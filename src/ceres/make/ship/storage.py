import math
from typing import ClassVar

from pydantic import ConfigDict, Field

from ceres.shared import CeresModel, _Note

from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection


class _ZeroPowerStoragePart(ShipPart):
    power: ClassVar[float]

    @property
    def power(self) -> float:
        return 0.0


class _ExplicitTonsStoragePart(ShipPart):
    tons: ClassVar[float]
    base_tons: float = Field(0.0, alias='tons')
    model_config = ConfigDict(frozen=True, populate_by_name=True, serialize_by_alias=True)

    @property
    def tons(self) -> float:
        return self.base_tons


class FuelScoops(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    free: bool = False

    def build_item(self) -> str | None:
        return 'Fuel Scoops'

    def build_notes(self) -> list[_Note]:
        return []

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        return 0.0 if self.free else 1_000_000.0


class OperationFuel(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    weeks: int

    def build_item(self) -> str | None:
        return f'Operation {self.actual_weeks} weeks'

    def bind(self, assembly) -> None:
        super().bind(assembly)
        self.item(self.build_item() or f'Operation {self.weeks} weeks')

    def bulkhead_label(self) -> str:
        return 'Operation Fuel'

    @property
    def tons(self) -> float:
        total = self._raw_tons()
        if self.assembly.displacement < 100:
            increment = 0.1
        else:
            increment = 1.0
        return math.ceil(total / increment - 1e-9) * increment

    def _raw_tons(self) -> float:
        power = getattr(self.assembly, 'power', None)
        plant = None if power is None else power.fusion_plant
        if plant is None:
            self.error('Ship must have a FusionPlant to compute OperationFuel')
            return 0.0
        pp_tons = plant.tons
        return 0.10 * pp_tons * self.weeks / 4

    @property
    def actual_weeks(self) -> int:
        if self._assembly is None:
            return self.weeks
        power = getattr(self.assembly, 'power', None)
        plant = None if power is None else power.fusion_plant
        if plant is None:
            return self.weeks
        four_week_baseline = 0.10 * plant.tons
        if four_week_baseline <= 0:
            return self.weeks
        full_periods = math.floor((self.tons / four_week_baseline) + 1e-9)
        return max(self.weeks, 4 * full_periods)

    def bulkhead_protected_tonnage(self) -> float:
        return self._raw_tons()

    @property
    def cost(self) -> float:
        return 0.0


class JumpFuel(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    parsecs: int

    def build_item(self) -> str | None:
        if self._assembly is not None and self.assembly.performance_displacement > self.assembly.displacement:
            return f'J-{self.parsecs} ({self.assembly.performance_displacement:g}t)'
        return f'J-{self.parsecs}'

    @property
    def _jump_drive(self):
        drives = getattr(self.assembly, 'drives', None)
        return None if drives is None else drives.j_drive

    @property
    def tons(self) -> float:
        multiplier = 1.0
        jump_drive = self._jump_drive
        if jump_drive is not None and getattr(jump_drive, 'customisation', None) is not None:
            multiplier = jump_drive.customisation.fuel_multiplier
        return self.assembly.performance_displacement * 0.1 * self.parsecs * multiplier

    @property
    def cost(self) -> float:
        return 0.0


class ReactionFuel(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    minutes: int

    def build_item(self) -> str | None:
        reaction_drive = self._reaction_drive if self._assembly is not None else None
        if reaction_drive is not None and reaction_drive.high_burn_thruster:
            if self.minutes % 60 == 0:
                hours = self.minutes // 60
                unit = 'hour' if hours == 1 else 'hours'
                return f'{hours} {unit} Thruster'
        unit = 'minute' if self.minutes == 1 else 'minutes'
        return f'{self.minutes} {unit} of operation'

    @property
    def _reaction_drive(self):
        drives = getattr(self.assembly, 'drives', None)
        return None if drives is None else drives.r_drive

    def _fuel_rate_per_hour(self) -> float:
        reaction_drive = self._reaction_drive
        if reaction_drive is None:
            self.error('Ship must have an RDrive to compute ReactionFuel')
            return 0.0
        if reaction_drive.level == 0:
            return 0.25
        return self.assembly.performance_displacement * 0.025 * reaction_drive.level

    @property
    def tons(self) -> float:
        return self._fuel_rate_per_hour() * (self.minutes / 60)

    @property
    def cost(self) -> float:
        return 0.0


class FuelProcessor(_ExplicitTonsStoragePart):
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_item(self) -> str | None:
        return f'Fuel Processor ({self.tons * 20:g} tons/day)'

    @property
    def cost(self) -> float:
        return self.tons * 50_000

    @property
    def power(self) -> float:
        return self.tons


class FuelSection(CeresModel):
    # Fuel and cargo live in the same module on purpose: future rules are likely
    # to blur the line between them via fuel bladders, combined containers, and
    # other storage-like arrangements.
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
            parts.append(self.jump_fuel.build_item() or f'J-{self.jump_fuel.parsecs}')
        if self.operation_fuel is not None:
            unit = 'week' if self.operation_fuel.actual_weeks == 1 else 'weeks'
            parts.append(f'{self.operation_fuel.actual_weeks} {unit} of operation')
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


class CargoAirlock(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    size: float = 2.0

    def build_item(self) -> str | None:
        return f'Cargo Airlock ({self.size:g} tons)'

    @property
    def tons(self) -> float:
        return max(self.size, 2.0)

    @property
    def cost(self) -> float:
        return self.tons * 100_000.0


class FuelCargoContainer(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    capacity: float

    def build_item(self) -> str | None:
        return f'Fuel/Cargo Container ({self.capacity:g} tons)'

    @property
    def cargo_capacity(self) -> float:
        return self.capacity

    @property
    def tons(self) -> float:
        return math.ceil(self.capacity * 1.05)

    @property
    def cost(self) -> float:
        return self.capacity * 5_000.0


class CargoSection(CeresModel):
    @staticmethod
    def _format_stores_tons(tons: float) -> str:
        return f'{tons:.1f}'.rstrip('0').rstrip('.')

    cargo_holds: list[CargoHold] = Field(default_factory=list)
    cargo_airlocks: list[CargoAirlock] = Field(default_factory=list)
    fuel_cargo_containers: list[FuelCargoContainer] = Field(default_factory=list)

    def _all_parts(self) -> list[ShipPart]:
        return [*self.cargo_airlocks, *self.fuel_cargo_containers]

    @staticmethod
    def maximum_stores_tons(ship) -> float | None:
        if not ship.military:
            return None
        return ship.displacement / 100

    def cargo_tons(self, ship) -> float:
        container_capacity = sum(container.cargo_capacity for container in self.fuel_cargo_containers)
        if self.cargo_holds:
            return sum(cargo_hold.usable_tons(ship) for cargo_hold in self.cargo_holds) + container_capacity
        return ship.remaining_usable_tonnage() + container_capacity

    @staticmethod
    def residual_cargo_space(ship) -> float:
        return ship.remaining_usable_tonnage()

    def _add_residual_cargo_space_row(self, ship, spec: ShipSpec) -> None:
        spec.add_row(
            SpecRow(
                section=SpecSection.CARGO,
                item='Cargo Space',
                tons=self.residual_cargo_space(ship),
            )
        )

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for cargo_part in self._all_parts():
            spec.add_row(ship._spec_row_for_part(SpecSection.CARGO, cargo_part))
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
            self._add_residual_cargo_space_row(ship, spec)
            self._add_stores_notes(ship, spec)
            return
        if self._all_parts():
            self._add_residual_cargo_space_row(ship, spec)
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
        cargo_row.notes.info(f'{formatted_tons} tons needed per 100 days of stores and spares')
        if self.cargo_tons(ship) < maximum_stores_tons:
            cargo_row.notes.warning(f'Cargo is below recommended 100-day stores capacity of {formatted_tons} tons')

    @classmethod
    def cargo_tons_for_ship(cls, ship) -> float:
        cargo = ship.cargo if ship.cargo is not None else cls()
        return cargo.cargo_tons(ship)

    @classmethod
    def add_spec_rows_for_ship(cls, ship, spec: ShipSpec) -> None:
        cargo = ship.cargo if ship.cargo is not None else cls()
        cargo.add_spec_rows(ship, spec)
