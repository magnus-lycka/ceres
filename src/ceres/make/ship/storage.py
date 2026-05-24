import math
from typing import Annotated, ClassVar, Literal

from pydantic import ConfigDict, Field

from ceres.shared import CeresModel, NoteList, _Note

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
    description: Literal['Fuel Scoops'] = 'Fuel Scoops'
    tons: ClassVar[float]
    cost: ClassVar[float]
    free: bool = False

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

    def item_description(self) -> str:
        if self.actual_weeks % 52 == 0:
            years = self.actual_weeks // 52
            unit = 'Year' if years == 1 else 'Years'
            return f'{years} {unit} of Operation'
        return f'Operation {self.actual_weeks} weeks'

    def bind(self, assembly) -> None:
        super().bind(assembly)
        self.item(self.item_description())

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
        plant = None if power is None else power.plant
        if plant is None:
            self.error('Ship must have a power plant to compute OperationFuel')
            return 0.0
        return plant.fuel_for_weeks(self.weeks)

    @property
    def actual_weeks(self) -> int:
        if self._assembly is None:
            return self.weeks
        power = getattr(self.assembly, 'power', None)
        plant = None if power is None else power.plant
        if plant is None:
            return self.weeks
        period_baseline = plant.fuel_for_weeks(plant.fuel_period_weeks)
        if period_baseline <= 0:
            return self.weeks
        full_periods = math.floor((self.tons / period_baseline) + 1e-9)
        return max(self.weeks, plant.fuel_period_weeks * full_periods)

    def bulkhead_protected_tonnage(self) -> float:
        return self._raw_tons()

    @property
    def cost(self) -> float:
        return 0.0


class JumpFuel(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    parsecs: int

    def item_description(self) -> str:
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


class Collector(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    description: Literal['Collector'] = 'Collector'
    tl: Literal[14] = 14
    parsecs: int

    def item_description(self) -> str:
        return f'Collector (J-{self.parsecs})'

    @property
    def tons(self) -> float:
        return self.assembly.displacement * 0.01 * self.parsecs + 5

    @property
    def cost(self) -> float:
        return self.tons * 500_000.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Collects and stores interstellar hydrogen for jump fuel')
        return notes


class ReactionFuel(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    minutes: int

    def item_description(self) -> str:
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
            base_rate = 0.25
        else:
            base_rate = self.assembly.performance_displacement * 0.025 * reaction_drive.level
        multiplier = 1.0
        if getattr(reaction_drive, 'customisation', None) is not None:
            multiplier = reaction_drive.customisation.fuel_multiplier
        return base_rate * multiplier

    @property
    def tons(self) -> float:
        return self._fuel_rate_per_hour() * (self.minutes / 60)

    @property
    def cost(self) -> float:
        return 0.0


class FuelProcessor(_ExplicitTonsStoragePart):
    cost: ClassVar[float]
    power: ClassVar[float]

    def item_description(self) -> str:
        return f'Fuel Processor ({self.tons * 20:g} tons/day)'

    @property
    def cost(self) -> float:
        return self.tons * 50_000

    @property
    def power(self) -> float:
        return self.tons


class FuelRefinery(_ExplicitTonsStoragePart):
    cost: ClassVar[float]
    power: ClassVar[float]
    description: Literal['Fuel Refinery'] = 'Fuel Refinery'
    tl: Literal[7, 10, 13] = 7

    _output_per_ton: ClassVar[dict[int, float]] = {7: 10.0, 10: 12.0, 13: 15.0}
    _power_per_ton: ClassVar[dict[int, float]] = {7: 2.0, 10: 1.0, 13: 1.0}
    _crew_per_tons: ClassVar[dict[int, float]] = {7: 50.0, 10: 100.0, 13: 500.0}
    _cost_per_ton: ClassVar[dict[int, float]] = {7: 100_000.0, 10: 250_000.0, 13: 500_000.0}

    def item_description(self) -> str:
        return f'Fuel Refinery ({self.output_per_day:g} tons/day)'

    @property
    def output_per_day(self) -> float:
        return self.tons * self._output_per_ton[self.tl]

    @property
    def crew_requirement(self) -> float:
        return self.tons / self._crew_per_tons[self.tl]

    @property
    def cost(self) -> float:
        return self.tons * self._cost_per_ton[self.tl]

    @property
    def power(self) -> float:
        return self.tons * self._power_per_ton[self.tl]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info(f'Requires 1 crew per {self._crew_per_tons[self.tl]:g} tons')
        return notes


class Ramscoop(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    extra_tons: float = 0.0

    def item_description(self) -> str:
        return f'Ramscoop ({self.collection_per_week:g} tons/week)'

    @property
    def tons(self) -> float:
        return max(self.assembly.displacement * 0.01 + 5, 10) + self.extra_tons

    @property
    def collection_per_week(self) -> float:
        return self.tons * 5

    @property
    def cost(self) -> float:
        return self.tons * 250_000.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        hull = getattr(self.assembly, 'hull', None)
        if hull is not None:
            from .hull import Streamlined

            if hull.configuration.streamlined is Streamlined.YES:
                notes.error('Ramscoops prevent atmospheric re-entry and cannot be installed on streamlined hulls')
        notes.info('Collects 5 tons of hydrogen per week per ton of ramscoop')
        notes.info('Does not require fuel scoops or fuel processors')
        return notes


class MetalHydrideStorage(ShipPart):
    description: Literal['Metal Hydride Storage'] = 'Metal Hydride Storage'
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    tl: Literal[9] = 9

    @property
    def tons(self) -> float:
        return self._stored_fuel_tons()

    @property
    def cost(self) -> float:
        return self._metal_hydride_tankage_tons() * 200_000.0

    @property
    def power(self) -> float:
        return 0.0

    def _stored_fuel_tons(self) -> float:
        fuel = getattr(self.assembly, 'fuel', None)
        if fuel is None:
            return 0.0
        return fuel.raw_fuel_tons()

    def _metal_hydride_tankage_tons(self) -> float:
        return self._stored_fuel_tons() * 2

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        notes.info('Replaces normal liquid hydrogen fuel tankage; consumes twice the stored fuel volume')
        notes.info('Fuel leak loss reduced to 25% of indicated amount, minimum 1 ton')
        return notes


class FuelSection(CeresModel):
    # Fuel and cargo live in the same module on purpose: future rules are likely
    # to blur the line between them via fuel bladders, combined containers, and
    # other storage-like arrangements.
    jump_fuel: JumpFuel | None = None
    collector: Collector | None = None
    operation_fuel: OperationFuel | None = None
    reaction_fuel: ReactionFuel | None = None
    fuel_scoops: FuelScoops | None = None
    fuel_processor: FuelProcessor | None = None
    fuel_refinery: FuelRefinery | None = None
    ramscoop: Ramscoop | None = None
    metal_hydride_storage: MetalHydrideStorage | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        for part in (
            self.jump_fuel,
            self.collector,
            self.operation_fuel,
            self.reaction_fuel,
            self.fuel_scoops,
            self.fuel_processor,
            self.fuel_refinery,
            self.ramscoop,
            self.metal_hydride_storage,
        ):
            if part is not None:
                parts.append(part)
        return parts

    def raw_fuel_tons(self) -> float:
        total_fuel_tons = 0.0
        if self.jump_fuel is not None:
            total_fuel_tons += self.jump_fuel.tons
        if self.operation_fuel is not None:
            total_fuel_tons += self.operation_fuel.tons
        if self.reaction_fuel is not None:
            total_fuel_tons += self.reaction_fuel.tons
        return total_fuel_tons

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
            total_fuel_tons = self.raw_fuel_tons()
            fuel_cost = None
            notes = NoteList()
            if self.metal_hydride_storage is not None:
                total_fuel_tons *= 2
                fuel_cost = self.metal_hydride_storage.cost
                notes.extend(self.metal_hydride_storage.notes.details)
                parts.append('metal hydride storage')
            spec.add_row(
                SpecRow(
                    section=SpecSection.FUEL,
                    item=', '.join(parts),
                    tons=total_fuel_tons or None,
                    cost=fuel_cost,
                    notes=notes,
                )
            )
        for fuel_part in (self.collector, self.fuel_scoops, self.fuel_processor, self.fuel_refinery, self.ramscoop):
            if fuel_part is not None:
                spec.add_row(ship._spec_row_for_part(SpecSection.FUEL, fuel_part))


class CargoCrane(CeresModel):
    description: Literal['Cargo Crane'] = 'Cargo Crane'

    def tons_for_space(self, cargo_space: float) -> float:
        return 2.5 + 0.5 * math.ceil(cargo_space / 150)

    def cost_for_space(self, cargo_space: float) -> float:
        return self.tons_for_space(cargo_space) * 1_000_000.0


class _LoadingBelt(ShipPart):
    description: Literal['Loading Belt'] = 'Loading Belt'
    tons: ClassVar[float]
    _replaced_loading_crew: ClassVar[int]

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def replaced_loading_crew(self) -> int:
        return self._replaced_loading_crew

    def item_description(self) -> str:
        return f'Loading Belt (TL{self.tl})'


class LoadingBeltTL7(_LoadingBelt):
    loading_belt_type: Literal['LOADING_BELT_TL7'] = 'LOADING_BELT_TL7'
    tl: Literal[7] = 7
    cost: float = 3_000.0
    power: float = 0.0
    _replaced_loading_crew: ClassVar[int] = 10


class LoadingBeltTL12(_LoadingBelt):
    loading_belt_type: Literal['LOADING_BELT_TL12'] = 'LOADING_BELT_TL12'
    tl: Literal[12] = 12
    cost: float = 10_000.0
    power: float = 1.0
    _replaced_loading_crew: ClassVar[int] = 25


type LoadingBelt = Annotated[LoadingBeltTL7 | LoadingBeltTL12, Field(discriminator='loading_belt_type')]


class CargoScoop(_ZeroPowerStoragePart):
    description: Literal['Cargo Scoop'] = 'Cargo Scoop'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 2.0

    @property
    def cost(self) -> float:
        return 500_000.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Picks up floating cargo at one ton per round')
        notes.info('Pilot check required; ship takes damage equal to negative Effect on failure')
        return notes


class CargoNet(_ZeroPowerStoragePart):
    description: Literal['Cargo Net'] = 'Cargo Net'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 5.0

    @property
    def cost(self) -> float:
        return 1_000_000.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Tow drones extend a retrieval net')
        notes.info('Ship cannot jump while cargo net is deployed')
        return notes


class ConcealedCompartment(_ExplicitTonsStoragePart):
    description: Literal['Concealed Compartment'] = 'Concealed Compartment'
    cost: ClassVar[float]
    power: ClassVar[float]
    sensors_dm: ClassVar[int] = -2
    investigate_dm: ClassVar[int] = -4

    @property
    def cost(self) -> float:
        return self.tons * 20_000.0

    @property
    def power(self) -> float:
        return 0.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        if self._assembly is not None:
            maximum_tons = self.assembly.displacement * 0.05
            if self.tons > maximum_tons:
                notes.error(f'Concealed compartment exceeds 5% of ship tonnage: {self.tons:.1f} > {maximum_tons:.1f}')
        notes.info('Hidden space shielded against sensors')
        notes.info('DM-2 to Electronics (sensors) checks and DM-4 to Investigate checks')
        return notes


class FuelTankCompartment(_ExplicitTonsStoragePart):
    description: Literal['Fuel Tank Compartment'] = 'Fuel Tank Compartment'
    cost: ClassVar[float]
    power: ClassVar[float]
    sensors_dm: ClassVar[int] = -4
    investigate_dm: ClassVar[int] = -6

    @property
    def cost(self) -> float:
        return self.tons * 4_000.0

    @property
    def power(self) -> float:
        return 0.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Officially counts as fuel tankage; Ceres counts it as real cargo volume (RIS-018)')
        notes.info('Can only be accessed when fuel tank is at least three-quarters empty')
        notes.info('DM-4 to Electronics (sensors) checks and DM-6 to Investigate checks')
        extra_weeks = self._official_operation_weeks()
        if extra_weeks is not None:
            notes.info(f'Would overstate official operation endurance by {extra_weeks:g} weeks')
        return notes

    def _official_operation_weeks(self) -> float | None:
        if self._assembly is None:
            return None
        power = getattr(self.assembly, 'power', None)
        plant = None if power is None else power.plant
        if plant is None:
            return None
        period_fuel = plant.fuel_for_weeks(plant.fuel_period_weeks)
        if period_fuel <= 0:
            return None
        return self.tons / period_fuel * plant.fuel_period_weeks


class ExternalCargoMount(_ZeroPowerStoragePart):
    description: Literal['External Cargo Mount'] = 'External Cargo Mount'
    tons: ClassVar[float]
    cost: ClassVar[float]
    capacity: float

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        return self.capacity * 1_000.0

    @property
    def performance_displacement_contribution(self) -> float:
        return self.capacity

    def item_description(self) -> str:
        return f'External Cargo Mount ({self.capacity:g} tons)'

    def bind(self, assembly) -> None:
        super().bind(assembly)
        from .hull import Streamlined

        hull = self.assembly.hull
        if hull is None:
            return
        if hull.configuration.streamlined == Streamlined.YES:
            self.error('External cargo mount cannot be installed on streamlined hulls')
        if hull.configuration.description == 'Dispersed Structure Hull':
            self.error('External cargo mount cannot be installed on dispersed structure hulls')

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Ship is effectively unstreamlined while external cargo is mounted')
        return notes


class _JumpNet(_ZeroPowerStoragePart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    capacity: float
    cost_per_ton: ClassVar[float]
    _label: ClassVar[str]

    @property
    def tons(self) -> float:
        return math.ceil(self.capacity / 100)

    @property
    def cost(self) -> float:
        return self.tons * self.cost_per_ton

    @property
    def performance_displacement_contribution(self) -> float:
        return self.capacity

    def item_description(self) -> str:
        return f'{self._label} ({self.capacity:g} tons)'

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Ship is effectively unstreamlined while jump net is deployed')
        return notes


class InterplanetaryJumpNet(_JumpNet):
    jump_net_type: Literal['INTERPLANETARY_JUMP_NET'] = 'INTERPLANETARY_JUMP_NET'
    description: Literal['Interplanetary Jump Net'] = 'Interplanetary Jump Net'
    tl: Literal[8] = 8
    cost_per_ton: ClassVar[float] = 100_000.0
    _label: ClassVar[str] = 'Interplanetary Jump Net'

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        notes.info('Cannot perform jump while interplanetary jump net is deployed')
        return notes


class InterstellarJumpNet(_JumpNet):
    jump_net_type: Literal['INTERSTELLAR_JUMP_NET'] = 'INTERSTELLAR_JUMP_NET'
    description: Literal['Interstellar Jump Net'] = 'Interstellar Jump Net'
    tl: Literal[10] = 10
    cost_per_ton: ClassVar[float] = 300_000.0
    _label: ClassVar[str] = 'Interstellar Jump Net'


type JumpNet = Annotated[InterplanetaryJumpNet | InterstellarJumpNet, Field(discriminator='jump_net_type')]


class CargoHold(CeresModel):
    description: Literal['Cargo Hold'] = 'Cargo Hold'
    tons: float | None = None
    cost: float = 0.0
    crane: CargoCrane | None = None

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

    def item_description(self) -> str:
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

    def item_description(self) -> str:
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
    loading_belts: list[LoadingBelt] = Field(default_factory=list)
    cargo_scoops: list[CargoScoop] = Field(default_factory=list)
    cargo_nets: list[CargoNet] = Field(default_factory=list)
    concealed_compartments: list[ConcealedCompartment] = Field(default_factory=list)
    fuel_tank_compartments: list[FuelTankCompartment] = Field(default_factory=list)
    external_cargo_mounts: list[ExternalCargoMount] = Field(default_factory=list)
    jump_nets: list[JumpNet] = Field(default_factory=list)

    def _all_parts(self) -> list[ShipPart]:
        return [
            *self.cargo_airlocks,
            *self.fuel_cargo_containers,
            *self.loading_belts,
            *self.cargo_scoops,
            *self.cargo_nets,
            *self.concealed_compartments,
            *self.fuel_tank_compartments,
            *self.external_cargo_mounts,
            *self.jump_nets,
        ]

    @property
    def performance_displacement_contribution(self) -> float:
        return sum(mount.performance_displacement_contribution for mount in self.external_cargo_mounts) + sum(
            jump_net.performance_displacement_contribution for jump_net in self.jump_nets
        )

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
    def residual_cargo_hold_tons(ship) -> float:
        return ship.remaining_usable_tonnage()

    def _add_residual_cargo_hold_row(self, ship, spec: ShipSpec) -> None:
        residual_tons = self.residual_cargo_hold_tons(ship)
        if residual_tons < 0.005:
            return
        spec.add_row(
            SpecRow(
                section=SpecSection.CARGO,
                item='Cargo Hold',
                tons=residual_tons,
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
                        cost=cargo_hold.cost or None,
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
            if all(cargo_hold.tons is not None for cargo_hold in self.cargo_holds):
                self._add_residual_cargo_hold_row(ship, spec)
            self._add_stores_notes(ship, spec)
            return
        if self._all_parts():
            self._add_residual_cargo_hold_row(ship, spec)
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
