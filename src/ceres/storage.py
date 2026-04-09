import math

from pydantic import Field

from .base import CeresModel, Note
from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection


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
        power = getattr(self.owner, 'power', None)
        plant = None if power is None else power.fusion_plant
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

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        parts: list[str] = []
        if self.jump_fuel is not None:
            parts.append(f'J-{self.jump_fuel.parsecs}')
        if self.operation_fuel is not None:
            unit = 'week' if self.operation_fuel.weeks == 1 else 'weeks'
            parts.append(f'{self.operation_fuel.weeks} {unit} of operation')
        if parts:
            total_fuel_tons = 0.0
            if self.jump_fuel is not None:
                total_fuel_tons += self.jump_fuel.tons
            if self.operation_fuel is not None:
                total_fuel_tons += self.operation_fuel.tons
            spec.add_row(
                SpecRow(
                    section=SpecSection.FUEL,
                    item=', '.join(parts),
                    tons=total_fuel_tons or None,
                )
            )
        for fuel_part in (self.fuel_scoops, self.fuel_processor):
            if fuel_part is not None:
                spec.add_row(ship._spec_row_for_part(SpecSection.FUEL, fuel_part))


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

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.cargo_holds:
            for cargo_hold in self.cargo_holds:
                spec.add_row(
                    SpecRow(
                        section=SpecSection.CARGO,
                        item=cargo_hold.build_item() or 'Cargo Hold',
                        tons=cargo_hold.usable_tons(ship) or None,
                    )
                )
                if cargo_hold.crane is not None:
                    spec.add_row(
                        SpecRow(
                            section=SpecSection.CARGO,
                            item=cargo_hold.crane.build_item() or 'Cargo Crane',
                            tons=cargo_hold.crane_tons(ship) or None,
                            cost=cargo_hold.crane_cost(ship) or None,
                        )
                    )
            return
        spec.add_row(
            SpecRow(
                section=SpecSection.CARGO,
                item='Cargo Hold',
                tons=ship.cargo_tons or None,
            )
        )

    @classmethod
    def add_spec_rows_for_ship(cls, ship, spec: ShipSpec) -> None:
        cargo = ship.cargo if ship.cargo is not None else cls()
        cargo.add_spec_rows(ship, spec)
