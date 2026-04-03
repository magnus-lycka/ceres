from enum import Enum, StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, Field

from .armour import (
    BondedSuperdenseArmour,
    CrystalironArmour,
    MolecularBondedArmour,
    TitaniumSteelArmour,
)
from .base import ShipBase
from .bridge import Cockpit
from .computer import Computer
from .drives import FusionPlantTL8, FusionPlantTL12, FusionPlantTL15, MDrive, OperationFuel
from .parts import ShipPart
from .sensors import CivilianGradeSensors
from .weapons import FixedFirmpoint


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


class CrewRole(BaseModel):
    role: str
    count: int
    monthly_salary: int

    @property
    def total_salary(self) -> int:
        return self.count * self.monthly_salary


class SoftwarePackage(BaseModel):
    name: str
    tons: float = 0.0
    cost: float = 0.0


class HullConfiguration(BaseModel):
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


class Hull(BaseModel):
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
    m_drive: MDrive | None = None
    fusion_plant: FusionPlantTL8 | FusionPlantTL12 | FusionPlantTL15 | None = None
    operation_fuel: OperationFuel | None = None
    cockpit: Cockpit | None = None
    computer: Computer | None = None
    sensors: CivilianGradeSensors | None = None
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
    def weapon_power_load(self) -> float:
        return sum(part.power for part in self.fixed_firmpoints)

    @property
    def total_power_load(self) -> float:
        return self.basic_power_load + sum(part.power for part in self._all_parts())

    @property
    def battle_power_load(self) -> float:
        return self.total_power_load - self.sensor_power_load

    @property
    def maximum_power_load(self) -> float:
        return self.total_power_load

    @property
    def power_margin(self) -> float:
        return self.available_power - self.total_power_load

    @property
    def design_cost(self) -> float:
        return self.hull_cost + sum(part.cost for part in self._all_parts())

    @property
    def discount_cost(self) -> float:
        return self.design_cost * self.design_type.cost_multiplier

    @property
    def crew_roles(self) -> list[CrewRole]:
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
        return round(self.discount_cost / 240, 2)

    @property
    def maintenance_cost(self) -> float:
        return float(round(self.discount_cost / 12_000))

    @property
    def life_support_cost(self) -> float:
        if self.cockpit is not None:
            return 0.0
        return 0.0

    @property
    def software_packages(self) -> list[SoftwarePackage]:
        if self.computer is None:
            return []
        return [
            SoftwarePackage(name='Library'),
            SoftwarePackage(name='Maneuver/0'),
            SoftwarePackage(name='Intellect'),
        ]

    @property
    def has_fuel_scoops(self) -> bool:
        return self.hull.configuration.streamlined is Streamlined.YES

    @property
    def fuel_scoop_cost(self) -> float:
        if self.has_fuel_scoops:
            return 0.0
        return 1_000_000.0

    @property
    def fuel_scoop_tons(self) -> float:
        return 0.0

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
            self.fusion_plant,
            self.operation_fuel,
            self.cockpit,
            self.computer,
            self.sensors,
        ):
            if part is not None:
                parts.append(part)
        parts.extend(self.fixed_firmpoints)
        return parts

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
        for part in self._all_parts():
            part.bind(self)
