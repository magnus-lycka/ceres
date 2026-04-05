from typing import ClassVar

from .parts import ShipPart


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
