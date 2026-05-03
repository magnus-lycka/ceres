from collections.abc import Sequence
import math
from typing import Annotated, ClassVar, Literal

from pydantic import Field, TypeAdapter

from .base import CeresModel
from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection
from .systems import CommonArea, HotTub, SwimmingPool, Theatre, WetBar


class Stateroom(ShipPart):
    kind: Literal['standard'] = 'standard'
    label: ClassVar[str] = 'Stateroom'
    plural_label: ClassVar[str] = 'Staterooms'
    occupancy: ClassVar[int] = 2
    tons_per_room: ClassVar[float] = 4.0
    cost_per_room: ClassVar[float] = 500_000.0
    fixed_life_support_per_room: ClassVar[float] = 1_000.0
    variable_life_support_per_occupant: ClassVar[float] = 1_000.0

    def build_item(self) -> str | None:
        return self.label

    @property
    def fixed_life_support_cost(self) -> float:
        return self.fixed_life_support_per_room

    @property
    def variable_life_support_cost(self) -> float:
        return self.occupancy * self.variable_life_support_per_occupant

    @property
    def life_support_cost(self) -> float:
        return self.fixed_life_support_cost + self.variable_life_support_cost

    def compute_tons(self) -> float:
        return self.tons_per_room

    def compute_cost(self) -> float:
        return self.cost_per_room


class HighStateroom(Stateroom):
    kind: Literal['high'] = 'high'
    label: ClassVar[str] = 'High Stateroom'
    plural_label: ClassVar[str] = 'High Staterooms'
    tons_per_room: ClassVar[float] = 6.0
    cost_per_room: ClassVar[float] = 800_000.0


class LuxuryStateroom(Stateroom):
    kind: Literal['luxury'] = 'luxury'
    label: ClassVar[str] = 'Luxury Stateroom'
    plural_label: ClassVar[str] = 'Luxury Staterooms'
    tons_per_room: ClassVar[float] = 10.0
    cost_per_room: ClassVar[float] = 1_500_000.0
    fixed_life_support_per_room: ClassVar[float] = 3_000.0


StateroomUnion = Annotated[Stateroom | HighStateroom | LuxuryStateroom, Field(discriminator='kind')]
_stateroom_adapter: TypeAdapter[StateroomUnion] = TypeAdapter(StateroomUnion)


class LowBerth(ShipPart):
    label: ClassVar[str] = 'Low Berth'
    plural_label: ClassVar[str] = 'Low Berths'
    tons_per_berth: ClassVar[float] = 0.5
    cost_per_berth: ClassVar[float] = 50_000.0

    def build_item(self) -> str | None:
        return self.label

    def compute_tons(self) -> float:
        return self.tons_per_berth

    def compute_cost(self) -> float:
        return self.cost_per_berth

    def compute_power(self) -> float:
        habitation = getattr(self.assembly, 'habitation', None)
        if habitation is None:
            return 0.0
        siblings = habitation.low_berths
        index = next((i for i, sibling in enumerate(siblings) if sibling is self), -1)
        if index < 0:
            return 0.0
        return 1.0 if index % 10 == 0 else 0.0


class Brig(ShipPart):
    def build_item(self) -> str | None:
        return 'Brig'

    def compute_tons(self) -> float:
        return 4.0

    def compute_cost(self) -> float:
        return 250_000.0


class AdvancedEntertainmentSystem(ShipPart):
    _tl: ClassVar[int] = 5
    minimum_cost: ClassVar[float] = 100.0
    maximum_cost: ClassVar[float] = 10_000.0
    cost: float

    @classmethod
    def validate_cost(cls, value: float) -> float:
        if not (cls.minimum_cost <= value <= cls.maximum_cost):
            raise ValueError(
                f'Advanced Entertainment System cost must be between '
                f'{cls.minimum_cost:.0f} and {cls.maximum_cost:.0f} credits'
            )
        return value

    def build_item(self) -> str | None:
        return 'Advanced Entertainment System'

    def compute_tons(self) -> float:
        return 0.0

    def model_post_init(self, __context) -> None:
        object.__setattr__(self, 'cost', self.validate_cost(self.cost))
        super().model_post_init(__context)


class CabinSpace(ShipPart):
    tons_per_passenger: ClassVar[float] = 1.5
    life_support_per_ton: ClassVar[float] = 250.0

    def build_item(self) -> str | None:
        return 'Cabin Space'

    def compute_cost(self) -> float:
        return self.tons * 50_000.0

    @property
    def passenger_capacity(self) -> int:
        return math.floor(self.tons / self.tons_per_passenger)

    @property
    def fixed_life_support_cost(self) -> float:
        return self.tons * self.life_support_per_ton


class HabitationSection(CeresModel):
    staterooms: list[StateroomUnion] = Field(default_factory=list)
    low_berths: list[LowBerth] = Field(default_factory=list)
    brig: Brig | None = None
    cabin_space: CabinSpace | None = None
    common_area: CommonArea | None = None
    entertainment: AdvancedEntertainmentSystem | None = None
    swimming_pool: SwimmingPool | None = None
    hot_tubs: list[HotTub] = Field(default_factory=list)
    theatres: list[Theatre] = Field(default_factory=list)
    wet_bar: WetBar | None = None

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'staterooms', [room.model_copy() for room in self.staterooms])
        object.__setattr__(self, 'low_berths', [berth.model_copy() for berth in self.low_berths])

    def stateroom_count(self) -> int:
        return len(self.staterooms)

    def low_berth_count(self) -> int:
        return len(self.low_berths)

    def validate_common_area(self) -> None:
        if not self.staterooms:
            return
        recommended_common_area = sum(room.tons for room in self.staterooms) / 4
        actual_common_area = self.provided_common_area_tons()
        if actual_common_area < recommended_common_area:
            self.warning(f'Recommended common area is {recommended_common_area:.2f} tons')

    def provided_common_area_tons(self) -> float:
        return sum(part.tons for part in self._all_parts() if isinstance(part, CommonArea))

    def validate_passenger_capacity(self, ship) -> None:
        if ship.passenger_vector is None:
            return

        passenger_vector = self.passenger_vector(ship)
        high_passage = passenger_vector.get('high', 0)
        middle_passage = passenger_vector.get('middle', 0)
        low_passage = passenger_vector.get('low', 0)

        crew_staterooms = math.ceil(self.crew_count(ship) / 2)
        non_crew_staterooms = max(0, self.stateroom_count() - crew_staterooms)
        if high_passage > non_crew_staterooms:
            self.error(f'High passage exceeds available non-crew staterooms: {high_passage} > {non_crew_staterooms}')

        cabin_capacity = 0 if self.cabin_space is None else self.cabin_space.passenger_capacity
        available_middle_capacity = max(0, non_crew_staterooms - high_passage) * 2 + cabin_capacity
        if middle_passage > available_middle_capacity:
            self.error(
                f'Middle passage exceeds available non-crew beds: {middle_passage} > {available_middle_capacity}'
            )

        if low_passage > self.low_berth_count():
            self.error(f'Low passage exceeds available low berths: {low_passage} > {self.low_berth_count()}')

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = [*self.staterooms, *self.low_berths]
        for part in (
            self.brig,
            self.cabin_space,
            self.common_area,
            self.entertainment,
            self.swimming_pool,
            *self.hot_tubs,
            *self.theatres,
            self.wet_bar,
        ):
            if part is not None:
                parts.append(part)
        return parts

    def crew_count(self, ship) -> int:
        return ship.crew.count

    def passenger_vector(self, ship) -> dict[str, int]:
        if ship.passenger_vector is not None:
            return {str(kind).lower(): int(count) for kind, count in ship.passenger_vector.items()}
        return self.default_passenger_vector(ship)

    def default_passenger_vector(self, ship) -> dict[str, int]:
        if ship.military:
            return {}

        crew_staterooms = math.ceil(self.crew_count(ship) / 2)
        remaining_staterooms = max(0, self.stateroom_count() - crew_staterooms)
        cabin_capacity = 0 if self.cabin_space is None else self.cabin_space.passenger_capacity

        return {
            'middle': remaining_staterooms * 2 + cabin_capacity,
            'low': self.low_berth_count(),
        }

    def fixed_life_support_cost(self, ship) -> float:
        stateroom_life_support = sum(room.fixed_life_support_cost for room in self.staterooms)
        cabin_life_support = 0.0 if self.cabin_space is None else self.cabin_space.fixed_life_support_cost
        return stateroom_life_support + cabin_life_support

    def variable_life_support_cost(self, ship) -> float:
        passenger_vector = self.passenger_vector(ship)
        high_passage = passenger_vector.get('high', 0)
        middle_passage = passenger_vector.get('middle', 0)
        low_passage = passenger_vector.get('low', 0)
        return float((self.crew_count(ship) + high_passage + middle_passage + low_passage) * 1_000)

    def life_support_cost(self, ship) -> float:
        passenger_vector = self.passenger_vector(ship)
        low_passage = passenger_vector.get('low', 0)
        low_berth_life_support = low_passage * 100
        return self.fixed_life_support_cost(ship) + low_berth_life_support + self.variable_life_support_cost(ship)

    def _group_consecutive(self, parts: Sequence[ShipPart]) -> list[list[ShipPart]]:
        groups: list[list[ShipPart]] = []
        keys: list[str] = []
        for part in parts:
            key = part.group_key
            if groups and keys[-1] == key:
                groups[-1].append(part)
            else:
                groups.append([part])
                keys.append(key)
        return groups

    def _spec_row_for_group(self, ship, section: SpecSection, group: list[ShipPart]) -> SpecRow:
        exemplar = group[0]
        quantity = len(group)
        item = ship._item_text(exemplar, getattr(exemplar, 'description', exemplar.__class__.__name__))
        plural_label = getattr(exemplar, 'plural_label', None)
        if quantity > 1 and plural_label is not None:
            item = plural_label
        total_tons = sum(part.tons for part in group) or None
        total_cost = sum(part.cost for part in group) or None
        total_power = sum(part.power for part in group)
        seen: set[tuple] = set()
        notes = []
        for part in group:
            for note in ship._display_notes(part):
                key = (note.category, note.message)
                if key not in seen:
                    seen.add(key)
                    notes.append(note)
        return SpecRow(
            section=section,
            item=item,
            quantity=quantity if quantity > 1 else None,
            tons=total_tons,
            power=(-total_power) if total_power else None,
            cost=total_cost,
            notes=notes,
        )

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        habitation_parts = [
            *self.staterooms,
            *self.low_berths,
            *[
                part
                for part in [
                    self.cabin_space,
                    self.brig,
                    self.common_area,
                    self.entertainment,
                    self.swimming_pool,
                    *self.hot_tubs,
                    *self.theatres,
                    self.wet_bar,
                ]
                if part is not None
            ],
        ]
        for group in self._group_consecutive(habitation_parts):
            spec.add_row(self._spec_row_for_group(ship, SpecSection.HABITATION, group))
        habitation_rows = spec.rows_for_section(SpecSection.HABITATION)
        if habitation_rows:
            habitation_rows[-1].notes.extend(ship._display_notes(self))
