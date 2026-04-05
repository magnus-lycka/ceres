from enum import Enum, StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field

from .armour import (
    BondedSuperdenseArmour,
    CrystalironArmour,
    MolecularBondedArmour,
    TitaniumSteelArmour,
)
from .base import CeresModel, NoteCategory, ShipBase
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
from .sensors import BasicSensors, CivilianSensors, MilitarySensors
from .systems import Aerofins, Airlock, CommonArea, FuelScoops, InternalDockingSpace, ProbeDrones, Workshop
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
    description: str = 'Standard Hull'
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

    def build_item(self) -> str | None:
        return self.description


standard_hull = HullConfiguration(description='Standard Hull', streamlined=Streamlined.PARTIAL)

streamlined_hull = HullConfiguration(
    description='Streamlined Hull',
    streamlined=Streamlined.YES,
    armour_volume_modifier=1.2,
    hull_cost_modifier=1.2,
)

sphere = HullConfiguration(
    description='Sphere Hull',
    streamlined=Streamlined.PARTIAL,
    armour_volume_modifier=0.9,
    hull_cost_modifier=1.1,
)

close_structure = HullConfiguration(
    description='Close Structure Hull',
    streamlined=Streamlined.PARTIAL,
    armour_volume_modifier=1.5,
    hull_cost_modifier=0.8,
)

dispersed_structure = HullConfiguration(
    description='Dispersed Structure Hull',
    streamlined=Streamlined.NO,
    armour_volume_modifier=2,
    hull_points_modifier=0.9,
    hull_cost_modifier=0.5,
)

planetoid = HullConfiguration(
    description='Planetoid Hull',
    streamlined=Streamlined.NO,
    hull_points_modifier=1.25,
    hull_cost_modifier=0.08,
    usage_factor=0.8,
    protection=2,
)

buffered_planetoid = HullConfiguration(
    description='Buffered Planetoid Hull',
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

ShipSensors = Annotated[
    BasicSensors | CivilianSensors | MilitarySensors,
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

    def build_item(self) -> str | None:
        return self.configuration.build_item()

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        if (a := self.armour) is not None:
            parts.append(a)
        if (s := self.stealth) is not None:
            parts.append(s)
        return parts


class Ship(ShipBase):
    ship_class: str | None = None
    ship_type: str | None = None
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
    sensors: ShipSensors = Field(default_factory=BasicSensors)
    docking_space: InternalDockingSpace | None = None
    staterooms: Staterooms | None = None
    common_area: CommonArea | None = None
    airlocks: list[Airlock] = Field(default_factory=list)
    aerofins: Aerofins | None = None
    probe_drones: ProbeDrones | None = None
    workshop: Workshop | None = None
    fuel_scoops: FuelScoops | None = None
    turrets: list[DoubleTurret] = Field(default_factory=list)
    fixed_firmpoints: list[FixedFirmpoint] = Field(default_factory=list)

    @property
    def armour_volume_modifier(self) -> float:
        return self.hull.configuration.armour_volume_modifier

    @property
    def hull_cost(self) -> float:
        return float(self.hull.configuration.cost(self.displacement))

    @property
    def hull_points(self) -> float:
        return float(self.hull.configuration.points(self.displacement))

    @property
    def available_power(self) -> float:
        if self.fusion_plant is None:
            return 0.0
        return float(self.fusion_plant.output)

    @property
    def basic_hull_power_load(self) -> float:
        if self.bridge is not None:
            return 20.0
        if self.hull.configuration.non_gravity:
            return 0.5
        return 1.0

    @property
    def maneuver_power_load(self) -> float:
        if self.m_drive is None:
            return 0.0
        return self.m_drive.power

    @property
    def sensor_power_load(self) -> float:
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
    def total_power_load(self) -> float:
        non_drive_power_load = sum(
            part.power for part in self._all_parts() if part is not self.m_drive and part is not self.jump_drive
        )
        return self.basic_hull_power_load + max(self.maneuver_power_load, self.jump_power_load) + non_drive_power_load

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

    def _crew_salary_cost(self) -> float:
        return float(sum(role.total_salary for role in self.crew_roles))

    def _mortgage_cost(self) -> float:
        return round(self.sales_price_new / 240, 2)

    def _maintenance_cost(self) -> float:
        return float(round(self.sales_price_new / 12_000))

    def _life_support_cost(self) -> float:
        if self.cockpit is not None:
            return 0.0
        if self.staterooms is not None:
            return self.staterooms.life_support_cost
        return 0.0

    def _fuel_cost(self) -> float:
        if self.jump_fuel is None:
            return 0.0
        fuel_cost_per_ton = 100 if self.fuel_processor is not None else 500
        return float(self.jump_fuel.tons * 2 * fuel_cost_per_ton)

    def _total_expenses(self) -> float:
        return (
            self._mortgage_cost()
            + self._maintenance_cost()
            + self._life_support_cost()
            + self._crew_salary_cost()
            + self._fuel_cost()
        )

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
    def software_packages(self) -> list[SoftwarePackage]:
        if self.computer is None:
            return []
        return [*self.computer.included_software, *self.software]

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
            self.common_area,
            self.aerofins,
            self.probe_drones,
            self.workshop,
            self.fuel_scoops,
        ):
            if part is not None:
                parts.append(part)
        parts.extend(self.airlocks)
        parts.extend(self.turrets)
        parts.extend(self.fixed_firmpoints)
        return parts

    def parts_of_type(self, part_cls: type) -> list[ShipPart]:
        return [part for part in self._all_parts() if isinstance(part, part_cls)]

    def markdown_table(self) -> str:
        last_section = None
        crew_salary_cost = self._crew_salary_cost()
        mortgage_cost = self._mortgage_cost()
        maintenance_cost = self._maintenance_cost()
        life_support_cost = self._life_support_cost()
        fuel_cost = self._fuel_cost()
        total_expenses = self._total_expenses()

        def add_row(
            section: str,
            item: str,
            tons: float | None,
            power: float | None,
            cost: float | None,
            emphasize_tons: bool = False,
            emphasize_power: bool = False,
        ) -> str:
            nonlocal last_section
            tons_text = '' if tons is None or tons == 0 else f'{tons:.2f}'
            if emphasize_tons and tons_text:
                tons_text = f'**{tons_text}**'
            if power is None or power == 0:
                power_text = ''
            else:
                power_text = f'{abs(power):.2f}'
            if emphasize_power and power_text:
                power_text = f'**{power_text}**'
            cost_text = '' if cost is None or cost == 0 else f'{cost / 1000:.2f}'
            section_text = '' if section == last_section else section
            last_section = section
            return f'| {section_text} | {item} | {tons_text} | {power_text} | {cost_text} |'

        def add_cost_row(item: str, cost: float) -> str:
            return f'| {item} | {round(cost)} |'

        def add_crew_row(role: str, salary: float) -> str:
            return f'| {role} | {round(salary)} |'

        def item_text(obj, fallback: str) -> str:
            for note in obj.notes:
                if note.category is NoteCategory.ITEM:
                    return note.message
            return fallback

        def add_note_rows(notes: list) -> list[str]:
            rows: list[str] = []
            for note in notes:
                if note.category is NoteCategory.ITEM:
                    continue
                if note.category is NoteCategory.INFO:
                    message = f'• {note.message}'
                elif note.category is NoteCategory.ERROR:
                    message = f'**ERROR:** {note.message}'
                elif note.category is NoteCategory.WARNING:
                    message = f'*WARNING:* {note.message}'
                else:
                    message = note.message
                rows.append(f'|  | {message} |  |  |  |')
            return rows

        heading_bits: list[str] = []
        if self.ship_class is not None and self.ship_type is not None:
            heading_bits.append(f'*{self.ship_class}* {self.ship_type}')
        elif self.ship_class is not None:
            heading_bits.append(f'*{self.ship_class}*')
        elif self.ship_type is not None:
            heading_bits.append(self.ship_type)
        heading_bits.append(f'TL{self.tl}')
        heading_bits.append(f'Hull {self.hull_points:.0f}')
        heading = f'## {" | ".join(heading_bits)}'

        lines = [
            heading,
            '',
            '| Section | Item | Tons | Power | Cost (kCr) |',
            '| --- | --- | ---: | ---: | ---: |',
            add_row(
                'Hull',
                item_text(self.hull, 'Hull'),
                self.displacement,
                None,
                self.hull_cost,
                emphasize_tons=True,
            ),
            add_row('Hull', 'Basic Ship Systems', None, self.basic_hull_power_load, 0.0),
        ]
        if self.hull.armour is not None:
            armour_row = add_row(
                'Armour',
                item_text(self.hull.armour, self.hull.armour.description),
                self.hull.armour.tons,
                -self.hull.armour.power if self.hull.armour.power else None,
                self.hull.armour.cost,
            )
            lines.append(
                armour_row,
            )
            lines.extend(add_note_rows(self.hull.armour.notes))
        if self.hull.stealth is not None:
            stealth_row = add_row(
                'Hull',
                item_text(self.hull.stealth, self.hull.stealth.description),
                self.hull.stealth.tons,
                -self.hull.stealth.power if self.hull.stealth.power else None,
                self.hull.stealth.cost,
            )
            lines.append(
                stealth_row,
            )
            lines.extend(add_note_rows(self.hull.stealth.notes))
        for part in self._all_parts():
            if part in self.hull._all_parts():
                continue
            details = item_text(part, getattr(part, 'description', part.__class__.__name__))
            section = part.__class__.__name__
            if part is self.m_drive:
                section = 'M-Drive'
            elif part is self.jump_drive:
                section = 'J-Drive'
            elif part is self.fusion_plant:
                section = 'Power Plant'
            elif part is self.jump_fuel or part is self.operation_fuel:
                section = 'Fuel'
            elif part is self.bridge or part is self.cockpit:
                section = 'Bridge'
            elif part is self.computer:
                section = 'Computer'
            elif part is self.sensors:
                section = 'Sensors'
            elif part is self.docking_space:
                section = 'Craft'
            elif part is self.staterooms:
                section = 'Staterooms'
            elif (
                part is self.common_area
                or part is self.probe_drones
                or part is self.workshop
                or part is self.fuel_processor
                or part is self.aerofins
                or part is self.fuel_scoops
                or part in self.airlocks
            ):
                section = 'Systems'
            elif part in self.turrets or part in self.fixed_firmpoints:
                section = 'Weapons'
            power = None
            emphasize_power = False
            if part is self.fusion_plant:
                power = float(self.fusion_plant.output)
                emphasize_power = True
            elif part.power:
                power = -part.power
            lines.append(add_row(section, details, part.tons, power, part.cost, emphasize_power=emphasize_power))
            lines.extend(add_note_rows(part.notes))
            if part is self.docking_space:
                craft = self.docking_space.craft
                lines.append(add_row('Craft', craft.build_item() or craft.__class__.__name__, None, None, craft.cost))
        for package in self.software_packages:
            lines.append(add_row('Software', item_text(package, package.description), None, None, package.cost))
            lines.extend(add_note_rows(package.notes))
        lines.append(add_row('Cargo', 'Cargo Hold', self.cargo, None, 0.0))
        lines.extend(add_note_rows(self.notes))
        lines.extend(
            [
                '',
                '| Cost | Amount |',
                '| --- | ---: |',
                add_cost_row('Production Cost', self.production_cost),
                add_cost_row('Sales Price New', self.sales_price_new),
                add_cost_row('Mortgage', mortgage_cost),
                add_cost_row('Maintenance', maintenance_cost),
                add_cost_row('Life Support', life_support_cost),
                add_cost_row('Fuel', fuel_cost),
                add_cost_row('Crew Salaries', crew_salary_cost),
                add_cost_row('Total Expenses', total_expenses),
            ],
        )
        if self.crew_roles:
            lines.extend(
                [
                    '',
                    '| Crew | Salary |',
                    '| --- | ---: |',
                ],
            )
            for role in self.crew_roles:
                lines.append(add_crew_row(role.role, role.total_salary))
        return '\n'.join(lines)

    @property
    def cargo(self):
        cargo = self.displacement * self.hull.configuration.usage_factor
        for part in self._all_parts():
            cargo -= part.tons
        return cargo

    def model_post_init(self, __context: Any) -> None:
        if self.hull.configuration.streamlined == Streamlined.YES:
            object.__setattr__(self, 'fuel_scoops', FuelScoops(free=True))
        self.clear_notes()
        for part in self._all_parts():
            part.bind(self)
        if self.software and self.computer is None:
            for package in self.software:
                package.warning('Ship software requires a computer')
        for package in self.software_packages:
            if self.tl < package.minimum_tl:
                package.error(f'{package.description} requires TL{package.minimum_tl}')
            if self.computer is not None and not self.computer.can_run(package):
                package.error(f'{self.computer.description} cannot run {package.description}')
        jump_controls = [package for package in self.software_packages if isinstance(package, JumpControl)]
        highest_jump_control = max(jump_controls, key=lambda package: package.rating, default=None)
        if self.jump_drive is not None:
            if highest_jump_control is None:
                self.jump_drive.warning('No Jump Control software')
            elif highest_jump_control.rating < self.jump_drive.rating:
                self.jump_drive.warning(f'Limited to Jump {highest_jump_control.rating} by control software')
        if highest_jump_control is not None:
            if self.jump_drive is None:
                highest_jump_control.warning('No jump drive installed')
            elif highest_jump_control.rating > self.jump_drive.rating:
                highest_jump_control.warning(f'Limited to Jump {self.jump_drive.rating} by drive capacity')
        if self.cargo < 0:
            self.error(f'Cargo is negative by {-self.cargo:.2f} tons')
        if self.bridge is not None and not self.airlocks:
            self.error('No airlock installed')
        if self.staterooms is not None:
            recommended_common_area = self.staterooms.tons / 4
            actual_common_area = 0.0 if self.common_area is None else self.common_area.tons
            if actual_common_area < recommended_common_area:
                self.warning(f'Recommended common area is {recommended_common_area:.2f} tons')
