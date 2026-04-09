import math
from typing import ClassVar

from .base import CeresModel, Note
from .parts import ShipPart
from .systems import CommonArea


class Staterooms(ShipPart):
    tons_per_stateroom: ClassVar[float] = 4.0
    cost_per_stateroom: ClassVar[float] = 500_000.0
    life_support_per_stateroom: ClassVar[float] = 1_000.0
    occupants_per_stateroom: ClassVar[int] = 2
    life_support_per_occupant: ClassVar[float] = 1_000.0

    count: int

    def compute_tons(self) -> float:
        return self.count * self.tons_per_stateroom

    def compute_cost(self) -> float:
        return self.count * self.cost_per_stateroom

    @property
    def occupancy(self) -> int:
        return self.count * self.occupants_per_stateroom

    @property
    def life_support_cost(self) -> float:
        return self.count * self.life_support_per_stateroom + self.occupancy * self.life_support_per_occupant


class LowBerths(ShipPart):
    tons_per_berth: ClassVar[float] = 0.5
    cost_per_berth: ClassVar[float] = 50_000.0

    count: int

    def build_item(self) -> str | None:
        return 'Low Berths'

    def compute_tons(self) -> float:
        return self.count * self.tons_per_berth

    def compute_cost(self) -> float:
        return self.count * self.cost_per_berth

    def compute_power(self) -> float:
        return float(math.ceil(self.count / 10))


class HabitationSection(CeresModel):
    staterooms: Staterooms | None = None
    low_berths: LowBerths | None = None
    common_area: CommonArea | None = None

    def build_notes(self) -> list[Note]:
        notes = super().build_notes()
        if self.staterooms is None:
            return notes
        recommended_common_area = self.staterooms.tons / 4
        actual_common_area = 0.0 if self.common_area is None else self.common_area.tons
        if actual_common_area < recommended_common_area:
            self.warning(f'Recommended common area is {recommended_common_area:.2f} tons')
        return notes

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        for part in (self.staterooms, self.low_berths, self.common_area):
            if part is not None:
                parts.append(part)
        return parts
