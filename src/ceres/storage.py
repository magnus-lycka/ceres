import math

from pydantic import Field

from .base import CeresModel, Note
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


class OperationFuel(ShipPart):
    weeks: int

    def build_item(self) -> str | None:
        return f'Operation {self.weeks} weeks'

    def compute_tons(self) -> float:
        plant = getattr(self.owner, 'fusion_plant', None)
        if plant is None:
            self.error('Ship must have a FusionPlant to compute OperationFuel')
            return 0.0
        pp_tons = plant.tons
        monthly = 0.10 * pp_tons
        weekly = monthly / 4
        total = weekly * self.weeks
        return math.ceil(total * 100 - 1e-9) / 100

    def compute_cost(self) -> float:
        return 0.0


class JumpFuel(ShipPart):
    parsecs: int

    def build_item(self) -> str | None:
        return f'Jump {self.parsecs}'

    def compute_tons(self) -> float:
        return self.owner.displacement * 0.1 * self.parsecs

    def compute_cost(self) -> float:
        return 0.0


class FuelProcessor(ShipPart):
    tons: float

    def build_item(self) -> str | None:
        return f'Fuel Processor ({self.tons:g} tons/day)'

    def compute_cost(self) -> float:
        return self.tons * 50_000

    def compute_power(self) -> float:
        return self.tons


class FuelSection(CeresModel):
    jump_fuel: JumpFuel | None = None
    operation_fuel: OperationFuel | None = None
    fuel_scoops: FuelScoops | None = None
    fuel_processor: FuelProcessor | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        for part in (self.jump_fuel, self.operation_fuel, self.fuel_scoops, self.fuel_processor):
            if part is not None:
                parts.append(part)
        return parts


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


class CargoSection(CeresModel):
    cargo_holds: list[CargoHold] = Field(default_factory=list)
