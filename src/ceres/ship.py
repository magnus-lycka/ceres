from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from .armour import (
    Armour,
    TitaniumSteelArmour,
    CrystalironArmour,
    BondedSuperdenseArmour,
    MolecularBondedArmour,
)
from .base import ShipBase
from .bridge import Cockpit
from .computer import Computer
from .drives import MDrive, FusionPlantTL8, FusionPlantTL12, FusionPlantTL15, OperationFuel
from .parts import ShipPart, Power
from .sensors import CivilianGradeSensors
from .weapons import FixedFirmpoint


class Streamlined(Enum):
    YES = 1
    PARTIAL = 2
    NO = 3


class ShipDesignType(str, Enum):
    STANDARD = "STANDARD"
    CUSTOM = "CUSTOM"
    NEW = "NEW"

    @property
    def cost_multiplier(self) -> float:
        return {
            ShipDesignType.STANDARD: 0.9,
            ShipDesignType.CUSTOM: 1.0,
            ShipDesignType.NEW: 1.01,
        }[self]


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
    streamlined=Streamlined.YES, armour_volume_modifier=1.2, hull_cost_modifier=1.2
)

sphere = HullConfiguration(
    streamlined=Streamlined.PARTIAL, armour_volume_modifier=0.9, hull_cost_modifier=1.1
)

close_structure = HullConfiguration(
    streamlined=Streamlined.PARTIAL, armour_volume_modifier=1.5, hull_cost_modifier=0.8
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
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    minimum_tl: ClassVar[int] = 0
    description: ClassVar[str] = ""
    cost_per_ton: ClassVar[int] = 0
    tonnage: ClassVar[float] = 0
    sensors_dm: ClassVar[int] = 0
    power: Power = Power(value=0)

    def calculate_cost(self):
        return self.owner.displacement * self.cost_per_ton

    def calculate_tons(self):
        return self.owner.displacement * self.tonnage


class NoStealth(Stealth):
    minimum_tl = 0


class BasicStealth(Stealth):
    description = "Basic Stealth"
    minimum_tl = 7
    cost_per_ton = 40_000
    sensors_dm = -2
    tonnage = 0.02


class ImprovedStealth(Stealth):
    description = "Improved Stealth"
    minimum_tl = 10
    cost_per_ton = 100_000
    sensors_dm = -2


class EnhancedStealth(Stealth):
    description = "Enhanced Stealth"
    minimum_tl = 12
    cost_per_ton = 500_000
    sensors_dm = -4


class AdvancedStealth(Stealth):
    description = "Advanced Stealth"
    minimum_tl = 14
    cost_per_ton = 1_000_000
    sensors_dm = -6


class Hull(BaseModel):
    configuration: HullConfiguration
    # Armour — at most one type at a time
    titanium_steel_armour: TitaniumSteelArmour | None = None
    crystaliron_armour: CrystalironArmour | None = None
    bonded_superdense_armour: BondedSuperdenseArmour | None = None
    molecular_bonded_armour: MolecularBondedArmour | None = None
    # Stealth — at most one type at a time
    basic_stealth: BasicStealth | None = None
    improved_stealth: ImprovedStealth | None = None
    enhanced_stealth: EnhancedStealth | None = None
    advanced_stealth: AdvancedStealth | None = None
    # Hull surface options
    heat_shielding: bool = False
    radiation_shielding: bool = False
    reflec: bool = False

    @property
    def armour(self) -> Armour | None:
        for a in (
            self.titanium_steel_armour,
            self.crystaliron_armour,
            self.bonded_superdense_armour,
            self.molecular_bonded_armour,
        ):
            if a is not None:
                return a
        return None

    @property
    def stealth(self) -> Stealth | None:
        for s in (
            self.basic_stealth,
            self.improved_stealth,
            self.enhanced_stealth,
            self.advanced_stealth,
        ):
            if s is not None:
                return s
        return None

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
    civilian_sensors: CivilianGradeSensors | None = None
    fixed_firmpoints: list[FixedFirmpoint] = Field(default_factory=list)

    @property
    def armour_volume_modifier(self) -> float:
        return self.hull.configuration.armour_volume_modifier

    @property
    def hull_cost(self) -> float:
        return float(self.hull.configuration.cost(self.displacement))

    @property
    def design_cost(self) -> float:
        return self.hull_cost + sum(float(part.cost) for part in self._all_parts())

    @property
    def discount_cost(self) -> float:
        return self.design_cost * self.design_type.cost_multiplier

    def _all_parts(self) -> list[ShipPart]:
        parts = list(self.hull._all_parts())
        for part in (
            self.m_drive,
            self.fusion_plant,
            self.operation_fuel,
            self.cockpit,
            self.computer,
            self.civilian_sensors,
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
