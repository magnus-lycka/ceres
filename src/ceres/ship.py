from enum import Enum, StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field

from .armour import (
    BondedSuperdenseArmour,
    CrystalironArmour,
    MolecularBondedArmour,
    TitaniumSteelArmour,
)
from .base import CeresModel, ShipBase
from .bridge import Bridge, Cockpit
from .computer import (
    Computer5,
    Computer10,
    Computer15,
    Computer20,
    Computer25,
    Computer30,
    Computer35,
    Core40,
    Core50,
    Core60,
    Core70,
    Core80,
    Core90,
    Core100,
    Intellect,
    JumpControl,
    JumpControl1,
    JumpControl2,
    JumpControl3,
    JumpControl4,
    JumpControl5,
    JumpControl6,
    Library,
    Manoeuvre,
    SoftwarePackage,
)
from .drives import (
    FuelProcessor,
    FusionPlantTL8,
    FusionPlantTL12,
    FusionPlantTL15,
    JumpDrive1,
    JumpDrive2,
    JumpDrive3,
    JumpDrive4,
    JumpDrive5,
    JumpDrive6,
    JumpFuel,
    MDrive0,
    MDrive1,
    MDrive2,
    MDrive3,
    MDrive4,
    MDrive5,
    MDrive6,
    MDrive7,
    MDrive8,
    MDrive9,
    MDrive10,
    MDrive11,
    OperationFuel,
)
from .habitation import Staterooms
from .parts import ShipPart
from .sensors import CivilianGradeSensors, MilitaryGradeSensors
from .systems import InternalDockingSpace, ProbeDrones, Workshop
from .weapons import DoubleTurret, FixedFirmpoint


class Streamlined(Enum):
    YES = 1
    PARTIAL = 2
    NO = 3


class ShipDesignType(StrEnum):
    STANDARD = 'STANDARD'
    CUSTOM = 'CUSTOM'
    NEW = 'NEW'

    @property
    def cost_multiplier(self) -> float:
        return {
            ShipDesignType.STANDARD: 0.9,
            ShipDesignType.CUSTOM: 1.0,
            ShipDesignType.NEW: 1.01,
        }[self]


class CrewRole(CeresModel):
    role: str
    count: int
    monthly_salary: int

    @property
    def total_salary(self) -> int:
        return self.count * self.monthly_salary


class HullConfiguration(CeresModel):
    streamlined: Streamlined
    armour_volume_modifier: float = 1
    hull_points_modifier: float = 1
    hull_cost_modifier: float = 1
    reinforced: bool = False
    light: bool = False
    military: bool = False
    non_gravity: bool = False
    double: bool = False
    hamster_cage: bool = False
    breakaway: bool = False
    protection: int = 0
    usage_factor: float = 1

    @property
    def effective_hull_cost_modifier(self) -> float:
        modifier = self.hull_cost_modifier
        if self.reinforced:
            modifier *= 1.5
        if self.light:
            modifier *= 0.75
        if self.military:
            modifier *= 1.25
        if self.non_gravity:
            modifier *= 0.5
        return modifier

    @property
    def effective_hull_points_modifier(self) -> float:
        modifier = self.hull_points_modifier
        if self.reinforced:
            modifier *= 1.1
        if self.light:
            modifier *= 0.9
        return modifier

    def cost(self, ton):
        return 50000 * ton * self.effective_hull_cost_modifier

    def points(self, ton):
        return (ton * self.effective_hull_points_modifier) // 2.5


standard_hull = HullConfiguration(streamlined=Streamlined.PARTIAL)

streamlined_hull = HullConfiguration(
    streamlined=Streamlined.YES,
    armour_volume_modifier=1.2,
    hull_cost_modifier=1.2,
)

sphere = HullConfiguration(
    streamlined=Streamlined.PARTIAL,
    armour_volume_modifier=0.9,
    hull_cost_modifier=1.1,
)

close_structure = HullConfiguration(
    streamlined=Streamlined.PARTIAL,
    armour_volume_modifier=1.5,
    hull_cost_modifier=0.8,
)

dispersed_structure = HullConfiguration(
    streamlined=Streamlined.NO,
    armour_volume_modifier=2,
    hull_points_modifier=0.9,
    hull_cost_modifier=0.5,
)

planetoid = HullConfiguration(
    streamlined=Streamlined.NO,
    hull_points_modifier=1.25,
    hull_cost_modifier=0.08,
    usage_factor=0.8,
    protection=2,
)

buffered_planetoid = HullConfiguration(
    streamlined=Streamlined.NO,
    hull_points_modifier=1.5,
    hull_cost_modifier=0.08,
    usage_factor=0.65,
    protection=4,
)


class Stealth(ShipPart):
    minimum_tl: ClassVar[int] = 0
    description: str
    cost_per_ton: ClassVar[int] = 0
    tonnage: ClassVar[float] = 0
    sensors_dm: ClassVar[int] = 0
    power: float = 0.0

    def compute_cost(self):
        return self.owner.displacement * self.cost_per_ton

    def compute_tons(self):
        return self.owner.displacement * self.tonnage


class BasicStealth(Stealth):
    description: Literal['Basic Stealth'] = 'Basic Stealth'
    minimum_tl = 7
    cost_per_ton = 40_000
    sensors_dm = -2
    tonnage = 0.02


class ImprovedStealth(Stealth):
    description: Literal['Improved Stealth'] = 'Improved Stealth'
    minimum_tl = 10
    cost_per_ton = 100_000
    sensors_dm = -2


class EnhancedStealth(Stealth):
    description: Literal['Enhanced Stealth'] = 'Enhanced Stealth'
    minimum_tl = 12
    cost_per_ton = 500_000
    sensors_dm = -4


class AdvancedStealth(Stealth):
    description: Literal['Advanced Stealth'] = 'Advanced Stealth'
    minimum_tl = 14
    cost_per_ton = 1_000_000
    sensors_dm = -6


HullArmour = Annotated[
    TitaniumSteelArmour | CrystalironArmour | BondedSuperdenseArmour | MolecularBondedArmour,
    Field(discriminator='description'),
]

HullStealth = Annotated[
    BasicStealth | ImprovedStealth | EnhancedStealth | AdvancedStealth,
    Field(discriminator='description'),
]

ShipMDrive = Annotated[
    MDrive0
    | MDrive1
    | MDrive2
    | MDrive3
    | MDrive4
    | MDrive5
    | MDrive6
    | MDrive7
    | MDrive8
    | MDrive9
    | MDrive10
    | MDrive11,
    Field(discriminator='rating'),
]

ShipJumpDrive = Annotated[
    JumpDrive1 | JumpDrive2 | JumpDrive3 | JumpDrive4 | JumpDrive5 | JumpDrive6,
    Field(discriminator='rating'),
]

ShipComputer = Annotated[
    Computer5
    | Computer10
    | Computer15
    | Computer20
    | Computer25
    | Computer30
    | Computer35
    | Core40
    | Core50
    | Core60
    | Core70
    | Core80
    | Core90
    | Core100,
    Field(discriminator='description'),
]

ShipSoftware = Annotated[
    Library
    | Manoeuvre
    | Intellect
    | JumpControl1
    | JumpControl2
    | JumpControl3
    | JumpControl4
    | JumpControl5
    | JumpControl6,
    Field(discriminator='description'),
]


class Hull(CeresModel):
    configuration: HullConfiguration
    armour: HullArmour | None = None
    stealth: HullStealth | None = None
    # Hull surface options
    heat_shielding: bool = False
    radiation_shielding: bool = False
    reflec: bool = False

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        if (a := self.armour) is not None:
            parts.append(a)
        if (s := self.stealth) is not None:
            parts.append(s)
        return parts


class Ship(ShipBase):
    design_type: ShipDesignType = ShipDesignType.CUSTOM
    hull: Hull
    m_drive: ShipMDrive | None = None
    jump_drive: ShipJumpDrive | None = None
    fusion_plant: FusionPlantTL8 | FusionPlantTL12 | FusionPlantTL15 | None = None
    jump_fuel: JumpFuel | None = None
    operation_fuel: OperationFuel | None = None
    fuel_processor: FuelProcessor | None = None
    bridge: Bridge | None = None
    cockpit: Cockpit | None = None
    computer: ShipComputer | None = None
    software: list[ShipSoftware] = Field(default_factory=list)
    sensors: CivilianGradeSensors | MilitaryGradeSensors | None = None
    docking_space: InternalDockingSpace | None = None
    staterooms: Staterooms | None = None
    probe_drones: ProbeDrones | None = None
    workshop: Workshop | None = None
    turrets: list[DoubleTurret] = Field(default_factory=list)
    fixed_firmpoints: list[FixedFirmpoint] = Field(default_factory=list)

    @property
    def armour_volume_modifier(self) -> float:
        return self.hull.configuration.armour_volume_modifier

    @property
    def hull_cost(self) -> float:
        return float(self.hull.configuration.cost(self.displacement))

    @property
    def available_power(self) -> float:
        if self.fusion_plant is None:
            return 0.0
        return float(self.fusion_plant.output)

    @property
    def basic_power_load(self) -> float:
        if self.bridge is not None:
            return 20.0
        if self.hull.configuration.non_gravity:
            return 0.5
        return 1.0

    @property
    def basic_hull_power_load(self) -> float:
        return self.basic_power_load

    @property
    def maneuver_power_load(self) -> float:
        if self.m_drive is None:
            return 0.0
        return self.m_drive.power

    @property
    def sensor_power_load(self) -> float:
        if self.sensors is None:
            return 0.0
        return self.sensors.power

    @property
    def jump_power_load(self) -> float:
        if self.jump_drive is None:
            return 0.0
        return self.jump_drive.power

    @property
    def fuel_power_load(self) -> float:
        if self.fuel_processor is None:
            return 0.0
        return self.fuel_processor.power

    @property
    def weapon_power_load(self) -> float:
        return sum(part.power for part in self.fixed_firmpoints) + sum(part.power for part in self.turrets)

    @property
    def non_drive_power_load(self) -> float:
        return sum(part.power for part in self._all_parts() if part is not self.m_drive and part is not self.jump_drive)

    @property
    def total_power_load(self) -> float:
        return self.basic_power_load + max(self.maneuver_power_load, self.jump_power_load) + self.non_drive_power_load

    @property
    def power_margin(self) -> float:
        return self.available_power - self.total_power_load

    @property
    def production_cost(self) -> float:
        craft_cost = 0.0
        if self.docking_space is not None:
            craft_cost += self.docking_space.craft.cost
        return (
            self.hull_cost
            + sum(part.cost for part in self._all_parts())
            + sum(package.cost for package in self.software_packages)
            + craft_cost
        )

    @property
    def sales_price_new(self) -> float:
        return self.production_cost * self.design_type.cost_multiplier

    @property
    def crew_roles(self) -> list[CrewRole]:
        if self.displacement <= 100 and self.jump_drive is not None:
            return [
                CrewRole(role='PILOT', count=1, monthly_salary=6_000),
                CrewRole(role='ASTROGATOR', count=1, monthly_salary=5_000),
                CrewRole(role='ENGINEER', count=1, monthly_salary=4_000),
            ]
        # Small craft without jump drives typically operate with a single pilot.
        if self.displacement <= 100:
            return [CrewRole(role='PILOT', count=1, monthly_salary=6_000)]
        return []

    @property
    def total_crew(self) -> int:
        return sum(role.count for role in self.crew_roles)

    @property
    def crew_salary_cost(self) -> float:
        return float(sum(role.total_salary for role in self.crew_roles))

    @property
    def mortgage_cost(self) -> float:
        return round(self.sales_price_new / 240, 2)

    @property
    def maintenance_cost(self) -> float:
        return float(round(self.sales_price_new / 12_000))

    @property
    def life_support_cost(self) -> float:
        if self.cockpit is not None:
            return 0.0
        if self.staterooms is not None:
            return self.staterooms.life_support_cost
        return 0.0

    @property
    def fuel_cost(self) -> float:
        if self.jump_fuel is None:
            return 0.0
        fuel_cost_per_ton = 100 if self.fuel_processor is not None else 500
        return float(self.jump_fuel.tons * 2 * fuel_cost_per_ton)

    @property
    def software_packages(self) -> list[SoftwarePackage]:
        if self.computer is None:
            return []
        return [*self.computer.included_software, *self.software]

    @property
    def total_expenses(self) -> float:
        return self.mortgage_cost + self.maintenance_cost + self.life_support_cost + self.crew_salary_cost

    @property
    def total_income(self) -> float:
        return 0.0

    @property
    def total_loss(self) -> float:
        return self.total_income - self.total_expenses

    def _all_parts(self) -> list[ShipPart]:
        parts = list(self.hull._all_parts())
        for part in (
            self.m_drive,
            self.jump_drive,
            self.fusion_plant,
            self.jump_fuel,
            self.operation_fuel,
            self.fuel_processor,
            self.bridge,
            self.cockpit,
            self.computer,
            self.sensors,
            self.docking_space,
            self.staterooms,
            self.probe_drones,
            self.workshop,
        ):
            if part is not None:
                parts.append(part)
        parts.extend(self.turrets)
        parts.extend(self.fixed_firmpoints)
        return parts

    def parts_of_type(self, part_cls: type) -> list[ShipPart]:
        return [part for part in self._all_parts() if isinstance(part, part_cls)]

    def markdown_table(self) -> str:
        def add_row(item: str, details: str, tons: float | None, cost: float | None, power: float | None) -> str:
            tons_text = '' if tons is None else f'{tons:.2f}'
            cost_text = '' if cost is None else f'{cost:.2f}'
            power_text = '' if power is None else f'{power:.2f}'
            return f'| {item} | {details} | {tons_text} | {cost_text} | {power_text} |'

        lines = [
            '| Item | Details | Tons | Cost | Power |',
            '| --- | --- | ---: | ---: | ---: |',
            add_row(
                'Hull',
                f'{self.hull.configuration.streamlined.name.title()} hull',
                self.displacement,
                self.hull_cost,
                None,
            ),
        ]
        if self.hull.armour is not None:
            lines.append(
                add_row(
                    'Armour',
                    self.hull.armour.description,
                    self.hull.armour.tons,
                    self.hull.armour.cost,
                    self.hull.armour.power,
                ),
            )
        if self.hull.stealth is not None:
            lines.append(
                add_row(
                    'Stealth',
                    self.hull.stealth.description,
                    self.hull.stealth.tons,
                    self.hull.stealth.cost,
                    self.hull.stealth.power,
                ),
            )
        for part in self._all_parts():
            if part in self.hull._all_parts():
                continue
            details = getattr(part, 'description', part.__class__.__name__)
            lines.append(add_row(part.__class__.__name__, details, part.tons, part.cost, part.power))
        for package in self.software_packages:
            lines.append(add_row('Software', package.description, 0.0, package.cost, 0.0))
        lines.extend(
            [
                add_row('Cargo', 'Remaining capacity', self.cargo, 0.0, 0.0),
                add_row('Production Cost', 'Total', None, self.production_cost, None),
                add_row('Sales Price New', 'Total', None, self.sales_price_new, None),
                add_row('Available Power', 'Total', None, None, self.available_power),
                add_row('Total Power Load', 'Total', None, None, self.total_power_load),
            ],
        )
        return '\n'.join(lines)

    @property
    def cargo(self):
        cargo = self.displacement * self.hull.configuration.usage_factor
        for part in self._all_parts():
            cargo -= part.tons
        return cargo

    @property
    def self_sealing(self):
        return self.tl >= 9

    def model_post_init(self, __context: Any) -> None:
        self.clear_notes()
        for part in self._all_parts():
            part.bind(self)
        if self.software and self.computer is None:
            self.error('Ship software requires a computer')
        for package in self.software_packages:
            if self.tl < package.minimum_tl:
                package.error(f'{package.description} requires TL{package.minimum_tl}')
            if self.computer is not None and not self.computer.can_run(package):
                package.error(f'{self.computer.description} cannot run {package.description}')
        if self.jump_drive is not None:
            if self.computer is None:
                self.jump_drive.error(
                    f'JumpDrive{self.jump_drive.rating} requires Jump Control/{self.jump_drive.rating}',
                )
            elif not any(
                isinstance(package, JumpControl) and package.rating >= self.jump_drive.rating
                for package in self.software_packages
            ):
                self.jump_drive.error(
                    f'JumpDrive{self.jump_drive.rating} requires Jump Control/{self.jump_drive.rating}',
                )
        if self.cargo < 0:
            self.error(f'Cargo is negative by {-self.cargo:.2f} tons')
