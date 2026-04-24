import math
from typing import ClassVar, Literal

from pydantic import field_validator

from .base import CeresModel
from .parts import ShipPart
from .spec import ShipSpec, SpecSection
from .systems import CommonArea
from .text import optional_count


class Staterooms(ShipPart):
    kind: Literal['standard', 'high'] = 'standard'
    count: int
    _specs: ClassVar[dict[str, dict[str, float | int]]] = {
        'standard': dict(
            tons_per_stateroom=4.0,
            cost_per_stateroom=500_000.0,
            life_support_per_stateroom=1_000.0,
            occupants_per_stateroom=2,
            life_support_per_occupant=1_000.0,
        ),
        'high': dict(
            tons_per_stateroom=6.0,
            cost_per_stateroom=800_000.0,
            life_support_per_stateroom=1_000.0,
            occupants_per_stateroom=2,
            life_support_per_occupant=1_000.0,
        ),
    }

    def __init__(self, count: int | None = None, /, **data):
        if count is not None and 'count' not in data:
            data['count'] = count
        super().__init__(**data)

    @field_validator('kind')
    @classmethod
    def validate_kind(cls, value: str) -> str:
        if value not in cls._specs:
            allowed = ', '.join(sorted(cls._specs))
            raise ValueError(f'Unsupported Staterooms kind {value!r}; expected one of: {allowed}')
        return value

    @property
    def tons_per_stateroom(self) -> float:
        return float(self._specs[self.kind]['tons_per_stateroom'])

    @property
    def cost_per_stateroom(self) -> float:
        return float(self._specs[self.kind]['cost_per_stateroom'])

    @property
    def life_support_per_stateroom(self) -> float:
        return float(self._specs[self.kind]['life_support_per_stateroom'])

    @property
    def occupants_per_stateroom(self) -> int:
        return int(self._specs[self.kind]['occupants_per_stateroom'])

    @property
    def life_support_per_occupant(self) -> float:
        return float(self._specs[self.kind]['life_support_per_occupant'])

    @property
    def label(self) -> str:
        return 'Stateroom' if self.kind == 'standard' else 'High Stateroom'

    def compute_tons(self) -> float:
        return self.count * self.tons_per_stateroom

    def compute_cost(self) -> float:
        return self.count * self.cost_per_stateroom

    @property
    def occupancy(self) -> int:
        return self.count * self.occupants_per_stateroom

    @property
    def fixed_life_support_cost(self) -> float:
        return self.count * self.life_support_per_stateroom

    @property
    def variable_life_support_cost(self) -> float:
        return self.occupancy * self.life_support_per_occupant

    @property
    def life_support_cost(self) -> float:
        return self.fixed_life_support_cost + self.variable_life_support_cost


class LowBerths(ShipPart):
    tons_per_berth: ClassVar[float] = 0.5
    cost_per_berth: ClassVar[float] = 50_000.0

    count: int

    def __init__(self, count: int | None = None, /, **data):
        if count is not None and 'count' not in data:
            data['count'] = count
        super().__init__(**data)

    def compute_tons(self) -> float:
        return self.count * self.tons_per_berth

    def compute_cost(self) -> float:
        return self.count * self.cost_per_berth

    def compute_power(self) -> float:
        return float(math.ceil(self.count / 10))


class AdvancedEntertainmentSystem(ShipPart):
    minimum_tl: ClassVar[int] = 5
    minimum_cost: ClassVar[float] = 100.0
    maximum_cost: ClassVar[float] = 10_000.0
    cost: float

    def __init__(self, cost: float | None = None, /, **data):
        if cost is not None and 'cost' not in data:
            data['cost'] = cost
        super().__init__(**data)

    @field_validator('cost')
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


class CabinSpace(ShipPart):
    tons: float
    tons_per_passenger: ClassVar[float] = 1.5
    life_support_per_ton: ClassVar[float] = 250.0

    def __init__(self, tons: float | None = None, /, **data):
        if tons is not None and 'tons' not in data:
            data['tons'] = tons
        super().__init__(**data)

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
    staterooms: Staterooms | None = None
    high_staterooms: Staterooms | None = None
    cabin_space: CabinSpace | None = None
    low_berths: LowBerths | None = None
    common_area: CommonArea | None = None
    entertainment: AdvancedEntertainmentSystem | None = None

    def _stateroom_groups(self) -> list[Staterooms]:
        groups: list[Staterooms] = []
        if self.staterooms is not None:
            groups.append(self.staterooms)
        if self.high_staterooms is not None:
            groups.append(self.high_staterooms)
        return groups

    def validate_common_area(self) -> None:
        stateroom_groups = self._stateroom_groups()
        if not stateroom_groups:
            return
        recommended_common_area = sum(group.tons for group in stateroom_groups) / 4
        actual_common_area = 0.0 if self.common_area is None else self.common_area.tons
        if actual_common_area < recommended_common_area:
            self.warning(f'Recommended common area is {recommended_common_area:.2f} tons')

    def validate_passenger_capacity(self, ship) -> None:
        if ship.passenger_vector is None:
            return

        passenger_vector = self.passenger_vector(ship)
        high_passage = passenger_vector.get('high', 0)
        middle_passage = passenger_vector.get('middle', 0)
        low_passage = passenger_vector.get('low', 0)

        stateroom_count = sum(group.count for group in self._stateroom_groups())
        crew_staterooms = math.ceil(self.crew_count(ship) / 2)
        non_crew_staterooms = max(0, stateroom_count - crew_staterooms)
        if high_passage > non_crew_staterooms:
            self.error(f'High passage exceeds available non-crew staterooms: {high_passage} > {non_crew_staterooms}')

        cabin_capacity = 0 if self.cabin_space is None else self.cabin_space.passenger_capacity
        available_middle_capacity = max(0, non_crew_staterooms - high_passage) * 2 + cabin_capacity
        if middle_passage > available_middle_capacity:
            self.error(
                f'Middle passage exceeds available non-crew beds: {middle_passage} > {available_middle_capacity}'
            )

        low_berth_count = 0 if self.low_berths is None else self.low_berths.count
        if low_passage > low_berth_count:
            self.error(f'Low passage exceeds available low berths: {low_passage} > {low_berth_count}')

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        for part in (
            *self._stateroom_groups(),
            self.cabin_space,
            self.low_berths,
            self.common_area,
            self.entertainment,
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

        stateroom_count = sum(group.count for group in self._stateroom_groups())
        low_berth_count = 0 if self.low_berths is None else self.low_berths.count
        cabin_capacity = 0 if self.cabin_space is None else self.cabin_space.passenger_capacity

        crew_staterooms = math.ceil(self.crew_count(ship) / 2)
        remaining_staterooms = max(0, stateroom_count - crew_staterooms)

        return {
            'middle': remaining_staterooms * 2 + cabin_capacity,
            'low': low_berth_count,
        }

    def fixed_life_support_cost(self, ship) -> float:
        stateroom_life_support = sum(group.fixed_life_support_cost for group in self._stateroom_groups())
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

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for staterooms in self._stateroom_groups():
            item = staterooms.label
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.HABITATION,
                    staterooms,
                    item=f'{item}s' if staterooms.count > 1 else item,
                )
            )
            spec.rows_for_section(SpecSection.HABITATION)[-1].quantity = optional_count(staterooms.count)
        if self.low_berths is not None:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.HABITATION,
                    self.low_berths,
                    item='Low Berths' if self.low_berths.count > 1 else 'Low Berth',
                )
            )
            spec.rows_for_section(SpecSection.HABITATION)[-1].quantity = optional_count(self.low_berths.count)
        habitation_parts = [
            part for part in [self.cabin_space, self.common_area, self.entertainment] if part is not None
        ]
        for habitation_part in habitation_parts:
            spec.add_row(ship._spec_row_for_part(SpecSection.HABITATION, habitation_part))
        habitation_rows = spec.rows_for_section(SpecSection.HABITATION)
        if habitation_rows:
            habitation_rows[-1].notes.extend(ship._display_notes(self))
