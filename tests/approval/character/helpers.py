"""Approval test helpers for character creation.

CharacterSession drives character creation through pending.event_from_form(form),
which is the same path production routes.py / future CharacterService will use.
Tests pass form dicts; the pending input turns them into events. No handler types
or event IDs are referenced directly.
"""

from collections.abc import Mapping
import dataclasses
from typing import Any

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.skills import AnySkill
from ceres.character.domain.sophont import Sophont
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay

# Non-aligned human world: PSI testing is offered here (allegiance does not start with 'Im').
MOCK_PSI_WORLD = TravellerMapWorld.model_validate(
    {
        'Name': 'Psiworld',
        'Hex': '0101',
        'UWP': 'B786577-D',
        'PBG': '314',
        'Zone': '',
        'Bases': '',
        'Allegiance': 'Na',
        'Stellar': 'G2 V',
        'SS': 'A',
        'Ix': '{ 1 }',
        'Ex': '(C45+1)',
        'Cx': '[565D]',
        'Nobility': '',
        'Worlds': 5,
        'ResourceUnits': 100,
        'Subsector': 1,
        'Quadrant': 1,
        'WorldX': 0,
        'WorldY': 0,
        'Remarks': 'Ni',
        'LegacyBaseCode': '',
        'Sector': 'Test Sector',
        'SubsectorName': 'Test Subsector',
        'SectorAbbreviation': 'Test',
        'AllegianceName': 'Non-Aligned',
    }
)


class FormData(Mapping[str, str]):
    """Multi-value form mapping. Supports getlist() so event_from_form() can handle
    repeated keys (e.g. multiple background skills submitted as repeated 'skill' fields)."""

    def __init__(self, data: dict[str, str | list[str]]):
        self._data: dict[str, list[str]] = {k: (v if isinstance(v, list) else [v]) for k, v in data.items()}

    def __getitem__(self, key: str) -> str:
        values = self._data.get(key, [])
        if not values:
            raise KeyError(key)
        return values[0]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def getlist(self, key: str) -> list[str]:
        return self._data.get(key, [])


class CharacterSession:
    """Drives character creation the same way production code does.

    Each step: find the first pending input, call pending.event_from_form(form),
    append the resulting event. This is exactly what routes.py / CharacterService
    will do. Tests supply form dicts rather than constructing handler objects.
    """

    def __init__(self, character_id: int = 1) -> None:
        self._id = character_id
        self._events: list[Event] = []
        self._projection: CharacterProjection | None = None
        self._log: list[Any] = []

    @property
    def log(self) -> list[Any]:
        return self._log

    @property
    def projection(self) -> CharacterProjection:
        if self._projection is None:
            raise ValueError('No events — call start() first')
        return self._projection

    def _append(self, event: Event) -> CharacterSession:
        self._events.append(event)
        self._projection = replay(self._id, self._events)
        return self

    def start(
        self,
        sophont: Sophont,
        homeworld: TravellerMapWorld,
        *,
        name: str = 'Test',
        player: str = 'NPC',
    ) -> CharacterSession:
        from ceres.character.domain.character_start import CharacterStartedHandler

        self._log.append({'sophont': sophont.name, 'homeworld': homeworld.name, 'name': name})
        return self._append(
            Event(handler=CharacterStartedHandler(sophont=sophont, homeworld=homeworld, name=name, player=player))
        )

    def submit(self, form: Mapping[str, Any]) -> CharacterSession:
        """Submit form data for the first pending input."""
        pending = self.projection.pending_inputs[0]
        self._log.append([dataclasses.asdict(s) for s in pending.input_specs(self.projection)])
        self._log.append({k: form.getlist(k) for k in form} if isinstance(form, FormData) else dict(form))
        event = pending.event_from_form(form)
        return self._append(event)


# ── Form builders ─────────────────────────────────────────────────────────────


def ucp_form(
    ucp: str,
    stat_names: tuple[str, ...] = ('STR', 'DEX', 'END', 'INT', 'EDU', 'SOC'),
) -> dict[str, str]:
    """Build form data for PendingUcp from a UCP hex string (e.g. '778827')."""
    from ceres.shared import ehex_to_int

    return {stat: str(ehex_to_int(digit)) for stat, digit in zip(stat_names, ucp, strict=True)}


def background_skills_form(*skills: AnySkill) -> FormData:
    """Build multi-value form data for PendingBackgroundSkills."""
    return FormData({'skill': [s.model_dump_json() for s in skills]})


def skill_form(skill: AnySkill) -> dict[str, str]:
    """Build form data for a single skill choice (PendingPreCareerSkillChoice, etc.)."""
    return {'skill': skill.model_dump_json()}


def roll_form(roll: int) -> dict[str, str]:
    """Build form data for any roll-only pending (survive, event, graduation, PSI, etc.)."""
    return {'roll': str(roll)}


def precareer_entry_form(precareer_cls: type[PreCareerData], roll: int) -> dict[str, str]:
    """Build form data for PendingCareerChoice → precareer entry."""
    from ceres.character.domain.precareer.loader import precareer_of_type

    pc = precareer_of_type(precareer_cls)
    return {'kind': 'precareer_entry', 'precareer': pc.name, 'roll': str(roll)}


def career_entry_form(career: str, assignment: str, roll: int) -> dict[str, str]:
    """Build form data for PendingCareerChoice → career entry."""
    return {'career': career, 'assignment': assignment, 'roll': str(roll)}


def commission_form(attempt: bool, roll: int = 7) -> dict[str, str]:
    """Build form data for PendingCommissionChoice."""
    if attempt:
        return {'choice': 'attempt', 'roll': str(roll)}
    return {'choice': 'skip'}


def reenlist_form(reenlist: bool) -> dict[str, str]:
    """Build form data for PendingReenlist OR PendingAssignmentChangeChoice (muster out / stay).

    Dual-purpose: works for both pending types so callers don't need to check which appears first.
    """
    if reenlist:
        return {'choice': 'same', 'reenlist': 'true'}
    return {'choice': 'muster_out', 'reenlist': 'false'}


def skill_table_form(table: str, roll: int) -> dict[str, str]:
    """Build form data for PendingSkillTable (advancement skill table pick)."""
    return {'table': table, 'roll': str(roll)}


def muster_out_form(table: str, roll: int) -> dict[str, str]:
    """Build form data for PendingMusterOut."""
    return {'table': table, 'roll': str(roll)}


def choice_form(choice_cls: type) -> dict[str, str]:
    """Build form data for PendingChoices from a ChoiceBase subclass."""
    return {'choice': choice_cls().kind}


def connections_form(count: int) -> dict[str, str]:
    """Build form data for PendingConnectionsRoll."""
    return {'count': str(count)}


def connection_name_form(name: str = '', note: str = '') -> dict[str, str]:
    """Build form data for PendingConnectionName."""
    return {'name': name, 'note': note}


def double_injury_form(roll1: int, roll2: int) -> dict[str, str]:
    """Build form data for PendingDoubleInjuryRoll."""
    return {'roll1': str(roll1), 'roll2': str(roll2)}


def keep_homeworld_form() -> dict[str, str]:
    """Build form data for PendingHomeworldChangeOffered (keep current homeworld)."""
    return {'keep': '1'}


def draft_form(choice: str, *, roll: int | None = None, assignment: str | None = None) -> dict[str, str]:
    """Build form data for PendingDraftChoice.

    choice='draft' with roll=N: submit to draft table (1–6, selects the N-th career).
    choice='alternative' with optional assignment: take the draft alternative career.
    """
    form: dict[str, str] = {'choice': choice}
    if roll is not None:
        form['roll'] = str(roll)
    if assignment is not None:
        form['assignment'] = assignment
    return form


def draft_assignment_form(assignment: str) -> dict[str, str]:
    """Build form data for PendingDraftAssignmentChoice."""
    return {'assignment': assignment}
