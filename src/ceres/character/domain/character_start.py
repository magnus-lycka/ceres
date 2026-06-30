from collections.abc import Mapping
import re
from typing import Literal, cast

from pydantic import Field, TypeAdapter, field_serializer, field_validator

from ceres.adapters.travellermap import TravellerMapWorld, fetch_world
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import UCP_STATS, Chars, characteristic_dm
from ceres.character.domain.skills import (
    AnySkill,
    BackgroundSkill,
    _skill_classes,
)
from ceres.character.domain.sophont import SOPHONTS, Sophont, available_sophont_names, get_sophont
from ceres.character.input_specs import InputSpec, NumberEntry, Select, SelectWorld, form_int, form_str
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase, PendingInputBase
from ceres.shared import ehex_to_int

BACKGROUND_SKILLS: frozenset[type] = frozenset(_skill_classes(BackgroundSkill))

_CHOOSE_COUNT_RE = re.compile(r'Choose (\d+)')
_skill_adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)


def _background_skill_count(edu: int) -> int:
    return max(0, characteristic_dm(edu) + 3)


# ── New creation flow: CharacterCreated → HomeworldSelected → SophontSelected ──


class CharacterCreatedHandler(EventHandlerBase):
    kind: Literal['character_created'] = 'character_created'
    name: str
    player: str = 'NPC'

    def init_replay(self, character_id: int, event_id: int) -> CharacterProjection:
        projection = CharacterProjection(
            character_id=character_id,
            summary=CharacterSummary(name=self.name),
        )
        projection.pending_inputs.append(
            PendingHomeworldSelection(pending_id=(event_id, 0), instruction='Select homeworld')
        )
        return projection


class HomeworldSelectedHandler(EventHandlerBase):
    kind: Literal['homeworld_selected'] = 'homeworld_selected'
    homeworld: TravellerMapWorld

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        projection.summary.homeworld = self.homeworld
        projection.summary.birthworld = self.homeworld
        sophont_names = available_sophont_names(self.homeworld)
        projection.pending_inputs.append(
            PendingSophontSelection(
                pending_id=(event.id, 0),
                instruction='Select sophont',
                sophont_names=sophont_names,
            )
        )


class SophontSelectedHandler(EventHandlerBase):
    kind: Literal['sophont_selected'] = 'sophont_selected'
    sophont: Sophont

    @field_validator('sophont', mode='before')
    @classmethod
    def _coerce_sophont(cls, v: object) -> Sophont:
        if isinstance(v, Sophont):
            return v
        if isinstance(v, str):
            result = get_sophont(v)
            if result is None:
                raise ValueError(f'Unknown sophont: {v!r}')
            return result
        raise ValueError(f'Expected Sophont or sophont name, got {type(v).__name__}')

    @field_serializer('sophont')
    def _serialize_sophont(self, v: Sophont) -> str:
        return v.name

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        projection.summary.sophont = self.sophont
        stat_names = [s.value for s in self.sophont.ucp_stats]
        projection.pending_inputs.append(
            PendingUcp(pending_id=(event.id, 0), instruction='Provide characteristics (UCP)', stat_names=stat_names)
        )


# ── Creation Pending Types ─────────────────────────────────────────────────────


class PendingHomeworldSelection(PendingInputBase):
    kind: Literal['homeworld_selection'] = 'homeworld_selection'
    blocking: bool = True

    @property
    def template_fragment(self) -> str:
        return 'homeworld_change'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        sector = form_str(form, 'sector', '').strip()
        hex_code = form_str(form, 'hex_code', '').strip()
        if not sector or not hex_code:
            raise ValueError('Sector and hex code are required to select a homeworld')
        world = fetch_world(sector, hex_code)
        return Event(fulfills=self.pending_id, handler=HomeworldSelectedHandler(homeworld=world))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [SelectWorld(name='homeworld', label='Homeworld')]


class PendingSophontSelection(PendingInputBase):
    kind: Literal['sophont_selection'] = 'sophont_selection'
    blocking: bool = True
    sophont_names: list[str] = Field(default_factory=lambda: [s.name for s in SOPHONTS])

    @property
    def template_fragment(self) -> str:
        return 'sophont_select'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        name = form_str(form, 'sophont', '').strip()
        sophont = get_sophont(name)
        if sophont is None:
            raise ValueError(f'Unknown sophont: {name!r}')
        return Event(fulfills=self.pending_id, handler=SophontSelectedHandler(sophont=sophont))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(n, n) for n in self.sophont_names]
        return [Select(name='sophont', label='Sophont', options=options)]


class UcpHandler(EventHandlerBase):
    kind: Literal['ucp_event'] = 'ucp_event'
    ucp: str

    def _parse_characteristics(self, sophont: Sophont) -> dict[Chars, int]:
        ucp_stats = sophont.ucp_stats if isinstance(sophont, Sophont) else UCP_STATS
        if len(self.ucp) != len(ucp_stats):
            raise ReplayError(f'Invalid UCP: {self.ucp!r} — expected {len(ucp_stats)} hex digits')
        return {stat: ehex_to_int(digit) for stat, digit in zip(ucp_stats, self.ucp, strict=True)}

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        sophont = projection.summary.sophont
        if sophont is None:
            raise ReplayError('Cannot process UCP: sophont not yet selected')
        projection.summary.characteristics = self._parse_characteristics(sophont)
        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        count = _background_skill_count(edu)
        if count > 0:
            projection.pending_inputs.append(
                PendingBackgroundSkills(
                    pending_id=(event.id, 0),
                    instruction=f'Choose {count} background skill(s)',
                    options=cast(
                        list[AnySkill], sorted([cls() for cls in BACKGROUND_SKILLS], key=lambda s: type(s).name())
                    ),
                )
            )
        else:
            from ceres.character.domain.psionics import queue_initial_psi_test_if_available

            queue_initial_psi_test_if_available(projection, event.id)


class BackgroundSkillsHandler(EventHandlerBase):
    kind: Literal['background_skills'] = 'background_skills'
    skills: list[AnySkill]

    model_config = {'arbitrary_types_allowed': True}

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        from ceres.character.domain.psionics import queue_initial_psi_test_or_career_choice

        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        expected = _background_skill_count(edu)
        if len(self.skills) != expected:
            raise ReplayError(f'Expected {expected} background skill(s), got {len(self.skills)}')
        invalid = [s for s in self.skills if type(s) not in BACKGROUND_SKILLS]
        if invalid:
            raise ReplayError(f'Invalid background skill(s): {", ".join(sorted(type(s).__name__ for s in invalid))}')
        for skill in self.skills:
            projection.grant_skill(skill)
        queue_initial_psi_test_or_career_choice(projection, event.id)


class FinishCreationHandler(EventHandlerBase):
    kind: Literal['finish_career_creation'] = 'finish_career_creation'

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeOffered

        projection.pending_inputs = [
            p for p in projection.pending_inputs if not isinstance(p, PendingHomeworldChangeOffered)
        ]


# ── Character-start Pending Input Types ───────────────────────────────────────


class PendingUcp(PendingInputBase):
    kind: Literal['ucp_pending'] = 'ucp_pending'
    stat_names: list[str] = Field(default_factory=lambda: [s.value for s in UCP_STATS])

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        ucp = ''.join(f'{form_int(form, stat, 0):X}' for stat in self.stat_names)
        return Event(fulfills=self.pending_id, handler=UcpHandler(ucp=ucp))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name=stat, label=stat, min=1, max=15) for stat in self.stat_names]


class PendingBackgroundSkills(PendingInputBase):
    kind: Literal['background_skills'] = 'background_skills'
    options: list[AnySkill] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        get_list = getattr(form, 'getlist', None)
        raw: list[str] = get_list('skill') if callable(get_list) else ([form['skill']] if 'skill' in form else [])
        skills = [_skill_adapter.validate_json(j) for j in raw]
        return Event(fulfills=self.pending_id, handler=BackgroundSkillsHandler(skills=skills))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        m = _CHOOSE_COUNT_RE.search(self.instruction)
        count = int(m.group(1)) if m else 1
        options: list[tuple[str, str]] = []
        for skill in self.options:
            skill_cls = type(skill)
            empty = skill_cls()
            options.append((skill_cls.name(), _skill_adapter.dump_json(empty).decode()))
        return [Select(name='skill', label='Skills', options=options, min_select=count, max_select=count)]
