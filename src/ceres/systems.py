import math
from typing import ClassVar

from .base import CeresModel, Note, NoteCategory
from .parts import ShipPart


class FuelScoops(ShipPart):
    free: bool = False

    def build_item(self) -> str | None:
        return 'Fuel Scoops'

    def build_notes(self) -> list[Note]:
        return []

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return 0.0 if self.free else 1_000_000.0


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


class CargoCrane(CeresModel):
    def build_item(self) -> str | None:
        return 'Cargo Crane'

    def tons_for_space(self, cargo_space: float) -> float:
        return 2.5 + 0.5 * math.ceil(cargo_space / 150)

    def cost_for_space(self, cargo_space: float) -> float:
        return self.tons_for_space(cargo_space) * 1_000_000.0


class CargoHold(CeresModel):
    tons: float | None = None
    crane: CargoCrane | None = None

    def build_item(self) -> str | None:
        return 'Cargo Hold'

    def total_tons(self, owner) -> float:
        if self.tons is not None:
            return self.tons
        return owner.cargo_space_for(self)

    def crane_tons(self, owner) -> float:
        if self.crane is None:
            return 0.0
        return self.crane.tons_for_space(self.total_tons(owner))

    def crane_cost(self, owner) -> float:
        if self.crane is None:
            return 0.0
        return self.crane.cost_for_space(self.total_tons(owner))

    def usable_tons(self, owner) -> float:
        return self.total_tons(owner) - self.crane_tons(owner)


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
