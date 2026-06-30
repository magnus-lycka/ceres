from collections.abc import Mapping
from typing import Literal

from ceres.adapters.travellermap import TravellerMapWorld, fetch_world
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.input_specs import InfoText, InputSpec, form_str
from ceres.character.mechanism.event_base import Event, EventHandlerBase, PendingInputBase


class HomeworldChangeRequiredHandler(EventHandlerBase):
    kind: Literal['homeworld_change_required'] = 'homeworld_change_required'
    reason: str
    source_kind: str = ''
    source_career: str | None = None
    source_assignment: str | None = None
    target_constraints: str | None = None

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        projection.pending_inputs.append(
            PendingHomeworldChangeRequired(
                pending_id=(event.id, 0),
                instruction=self.reason,
                reason=self.reason,
                source_kind=self.source_kind,
                source_career=self.source_career,
                source_assignment=self.source_assignment,
                target_constraints=self.target_constraints,
            )
        )


class HomeworldChangeOfferedHandler(EventHandlerBase):
    kind: Literal['homeworld_change_offered'] = 'homeworld_change_offered'
    reason: str
    source_kind: str = ''
    source_career: str | None = None
    source_assignment: str | None = None
    target_constraints: str | None = None

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        projection.pending_inputs.append(
            PendingHomeworldChangeOffered(
                pending_id=(event.id, 0),
                instruction=self.reason,
                reason=self.reason,
                source_kind=self.source_kind,
                source_career=self.source_career,
                source_assignment=self.source_assignment,
                target_constraints=self.target_constraints,
            )
        )


class HomeworldChangedHandler(EventHandlerBase):
    kind: Literal['homeworld_changed'] = 'homeworld_changed'
    new_homeworld: TravellerMapWorld

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        projection.summary.homeworld = self.new_homeworld


class HomeworldChangeKeptHandler(EventHandlerBase):
    kind: Literal['homeworld_change_kept'] = 'homeworld_change_kept'

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        pass


# ── Homeworld Pending Input Types ─────────────────────────────────────────────


class PendingHomeworldChangeRequired(PendingInputBase):
    kind: Literal['homeworld_change_required'] = 'homeworld_change_required'
    blocking: bool = True
    reason: str
    source_kind: str = ''
    source_career: str | None = None
    source_assignment: str | None = None
    target_constraints: str | None = None

    @property
    def template_fragment(self) -> str:
        return 'homeworld_change'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        sector = form_str(form, 'sector', '').strip()
        hex_code = form_str(form, 'hex_code', '').strip()
        if not sector or not hex_code:
            raise ValueError('Sector and hex code are required to select a new homeworld')
        world = fetch_world(sector, hex_code)
        if self.target_constraints == 'world_with_scout_base' and 'S' not in world.bases and 'W' not in world.bases:
            raise ValueError(
                f'{world.name} ({world.sector} {world.hex}) has no Imperial Scout Base (S) or Way Station (W)'
            )
        return Event(fulfills=self.pending_id, handler=HomeworldChangedHandler(new_homeworld=world))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [InfoText(text=self.reason)]


class PendingHomeworldChangeOffered(PendingInputBase):
    kind: Literal['homeworld_change_offered'] = 'homeworld_change_offered'
    blocking: bool = False
    reason: str
    source_kind: str = ''
    source_career: str | None = None
    source_assignment: str | None = None
    target_constraints: str | None = None

    @property
    def template_fragment(self) -> str:
        return 'homeworld_change'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        if form_str(form, 'keep', '').strip() == '1':
            return Event(fulfills=self.pending_id, handler=HomeworldChangeKeptHandler())
        sector = form_str(form, 'sector', '').strip()
        hex_code = form_str(form, 'hex_code', '').strip()
        if not sector or not hex_code:
            raise ValueError('Sector and hex code are required to select a new homeworld')
        world = fetch_world(sector, hex_code)
        return Event(fulfills=self.pending_id, handler=HomeworldChangedHandler(new_homeworld=world))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [InfoText(text=self.reason)]
