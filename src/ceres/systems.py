from typing import ClassVar

from .base import Note, NoteCategory
from .parts import ShipPart


class Workshop(ShipPart):
    def build_item(self) -> str | None:
        return 'Workshop'

    def compute_tons(self) -> float:
        return 6.0

    def compute_cost(self) -> float:
        return 900_000.0


class CommonArea(ShipPart):
    tons: float

    def build_item(self) -> str | None:
        return 'Common Area'

    def compute_cost(self) -> float:
        return self.tons * 100_000.0


class MedicalBay(ShipPart):
    def build_item(self) -> str | None:
        return 'Medical Bay'

    def compute_tons(self) -> float:
        return 4.0

    def compute_cost(self) -> float:
        return 2_000_000.0

    def compute_power(self) -> float:
        return 1.0


class Airlock(ShipPart):
    size: float = 2.0

    def build_item(self) -> str | None:
        return 'Airlock'

    def am_i_for_free(self) -> bool:
        free_airlocks = self.owner.displacement // 100
        siblings = self.owner.parts_of_type(Airlock)
        try:
            index = siblings.index(self)
        except ValueError:
            return False
        return index < free_airlocks

    def compute_tons(self) -> float:
        if self.am_i_for_free():
            return 0.0
        return max(self.size, 2.0)

    def compute_cost(self) -> float:
        if self.am_i_for_free():
            return 0.0
        return self.compute_tons() * 100_000.0


class Aerofins(ShipPart):
    @property
    def atmospheric_pilot_dm(self) -> int:
        return 2

    def build_item(self) -> str | None:
        return 'Aerofins'

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='DM +2 to Pilot checks in atmosphere')]

    def compute_tons(self) -> float:
        return self.owner.displacement * 0.05

    def compute_cost(self) -> float:
        return self.compute_tons() * 100_000.0


class ProbeDrones(ShipPart):
    drones_per_ton: ClassVar[int] = 5
    cost_per_ton: ClassVar[float] = 500_000.0
    count: int

    def build_item(self) -> str | None:
        return f'{self.count} Probes'

    def compute_tons(self) -> float:
        return self.count / self.drones_per_ton

    def compute_cost(self) -> float:
        return (self.count / self.drones_per_ton) * self.cost_per_ton


class RepairDrones(ShipPart):
    """Repair drones: 1 ton per 100 tons of displacement, Cr200,000 per ton."""

    def build_item(self) -> str | None:
        return 'Repair Drones'

    def compute_tons(self) -> float:
        return self.owner.displacement / 100

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0
