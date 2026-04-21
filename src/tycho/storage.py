import math

from pydantic import Field

from .base import CeresModel, Note, NoteCategory
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

    def bulkhead_label(self) -> str:
        return 'Operation Fuel'

    def compute_tons(self) -> float:
        total = self._raw_tons()
        return math.ceil(total * 100 - 1e-9) / 100

    def _raw_tons(self) -> float:
        power = getattr(self.ship, 'power', None)
        plant = None if power is None else power.fusion_plant
        if plant is None:
            self.error('Ship must have a FusionPlant to compute OperationFuel')
            return 0.0
        pp_tons = plant.tons
        monthly = 0.10 * pp_tons
        weekly = monthly / 4
        return weekly * self.weeks

    def bulkhead_protected_tonnage(self) -> float:
        return self._raw_tons()

    def compute_cost(self) -> float:
        return 0.0


class JumpFuel(ShipPart):
    parsecs: int

    def build_item(self) -> str | None:
        return f'Jump {self.parsecs}'

    @property
    def _jump_drive(self):
        drives = getattr(self.ship, 'drives', None)
        return None if drives is None else drives.j_drive

    def compute_tons(self) -> float:
        multiplier = 1.0
        jump_drive = self._jump_drive
        if jump_drive is not None and getattr(jump_drive, 'customisation', None) is not None:
            multiplier = jump_drive.customisation.fuel_multiplier
        return self.ship.displacement * 0.1 * self.parsecs * multiplier

    def compute_cost(self) -> float:
        return 0.0


class ReactionFuel(ShipPart):
    minutes: int

    def build_item(self) -> str | None:
        reaction_drive = self._reaction_drive if self._ship is not None else None
        if reaction_drive is not None and reaction_drive.high_burn_thruster:
            if self.minutes % 60 == 0:
                hours = self.minutes // 60
                unit = 'hour' if hours == 1 else 'hours'
                return f'{hours} {unit} Thruster'
        unit = 'minute' if self.minutes == 1 else 'minutes'
        return f'{self.minutes} {unit} of operation'

    @property
    def _reaction_drive(self):
        drives = getattr(self.ship, 'drives', None)
        return None if drives is None else drives.r_drive

    def _fuel_rate_per_hour(self) -> float:
        reaction_drive = self._reaction_drive
        if reaction_drive is None:
            self.error('Ship must have an RDrive to compute ReactionFuel')
            return 0.0
        if reaction_drive.level == 0:
            return 0.25
        return self.ship.displacement * 0.025 * reaction_drive.level

    def compute_tons(self) -> float:
        return self._fuel_rate_per_hour() * (self.minutes / 60)

    def compute_cost(self) -> float:
        return 0.0


class FuelProcessor(ShipPart):
    tons: float

    def build_item(self) -> str | None:
        return f'Fuel Processor ({self.tons * 20:g} tons/day)'

    def compute_cost(self) -> float:
        return self.tons * 50_000

    def compute_power(self) -> float:
        return self.tons


class FuelSection(CeresModel):
    jump_fuel: JumpFuel | None = None
    operation_fuel: OperationFuel | None = None
    reaction_fuel: ReactionFuel | None = None
    fuel_scoops: FuelScoops | None = None
    fuel_processor: FuelProcessor | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        for part in (self.jump_fuel, self.operation_fuel, self.reaction_fuel, self.fuel_scoops, self.fuel_processor):
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
        if self.reaction_fuel is not None:
            item = self.reaction_fuel.build_item()
            if item is not None:
                parts.append(item)
        if parts:
            total_fuel_tons = 0.0
            if self.jump_fuel is not None:
                total_fuel_tons += self.jump_fuel.tons
            if self.operation_fuel is not None:
                total_fuel_tons += self.operation_fuel.tons
            if self.reaction_fuel is not None:
                total_fuel_tons += self.reaction_fuel.tons
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
        return owner.remaining_usable_tonnage()

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
    @staticmethod
    def _format_stores_tons(tons: float) -> str:
        return f'{tons:.1f}'.rstrip('0').rstrip('.')

    cargo_holds: list[CargoHold] = Field(default_factory=list)

    @staticmethod
    def maximum_stores_tons(ship) -> float | None:
        if not ship.military:
            return None
        return ship.displacement / 100

    def cargo_tons(self, ship) -> float:
        if self.cargo_holds:
            return sum(cargo_hold.usable_tons(ship) for cargo_hold in self.cargo_holds)
        return ship.remaining_usable_tonnage()

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
            self._add_stores_notes(ship, spec)
            return
        cargo_tons = self.cargo_tons(ship)
        cargo_item = 'Cargo Hold'
        if abs(cargo_tons) < 0.005:
            cargo_item = 'Cargo (0.00 tons)'
        spec.add_row(
            SpecRow(
                section=SpecSection.CARGO,
                item=cargo_item,
                tons=cargo_tons or None,
            )
        )
        self._add_stores_notes(ship, spec)

    def _add_stores_notes(self, ship, spec: ShipSpec) -> None:
        maximum_stores_tons = self.maximum_stores_tons(ship)
        if maximum_stores_tons is None:
            return
        cargo_row = spec.rows_for_section(SpecSection.CARGO)[-1]
        formatted_tons = self._format_stores_tons(maximum_stores_tons)
        cargo_row.notes.append(
            Note(
                category=NoteCategory.INFO,
                message=f'{formatted_tons} tons needed per 100 days of stores and spares',
            )
        )
        if self.cargo_tons(ship) < maximum_stores_tons:
            cargo_row.notes.append(
                Note(
                    category=NoteCategory.WARNING,
                    message=f'Cargo is below recommended 100-day stores capacity of {formatted_tons} tons',
                )
            )

    @classmethod
    def cargo_tons_for_ship(cls, ship) -> float:
        cargo = ship.cargo if ship.cargo is not None else cls()
        return cargo.cargo_tons(ship)

    @classmethod
    def add_spec_rows_for_ship(cls, ship, spec: ShipSpec) -> None:
        cargo = ship.cargo if ship.cargo is not None else cls()
        cargo.add_spec_rows(ship, spec)
