from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from .armour import Armour
from .parts import ShipPart, Power, TechLevel


class Streamlined(Enum):
    YES = 1
    PARTIAL = 2
    NO = 3


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

    def cost(self, ton):
        return 50000 * ton * self.hull_cost_modifier

    def points(self, ton):
        return (ton * self.hull_points_modifier) // 2.5


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
    sensors_dm: ClassVar[int] = 0
    description: ClassVar[str] = ""
    cost_per_ton: ClassVar[int] = 0
    tonnage: ClassVar[int] = 0
    hull: int
    power: Power = Power(value=0)

    def calculate_cost(self):
        return self.hull * self.cost_per_ton

    def calculate_tons(self):
        return self.hull * self.tonnage


class NoStealth(Stealth):
    tl: TechLevel = TechLevel(value=0)
    hull: int = 0


class BasicStealth(Stealth):
    description = "Basic Stealth"
    tl: TechLevel = TechLevel(value=7)
    cost_per_ton = 40_000
    sensors_dm = -2
    tonnage = 0.02


class ImprovedStealth(Stealth):
    description = "Improved Stealth"
    tl: TechLevel = TechLevel(value=10)
    cost_per_ton = 100_000
    sensors_dm = -2


class EnhancedStealth(Stealth):
    description = "Enhanced Stealth"
    tl: TechLevel = TechLevel(value=12)
    cost_per_ton = 500_000
    sensors_dm = -4


class AdvancedStealth(Stealth):
    description = "Advanced Stealth"
    tl: TechLevel = TechLevel(value=14)
    cost_per_ton = 1_000_000
    sensors_dm = -6


class HullOptions(BaseModel):
    heat_shielding: bool = False
    radiation_shielding: bool = False
    reflec: bool = False
    stealth: Stealth = Field(default_factory=NoStealth)


class Hull(BaseModel):
    configuration: HullConfiguration
    armour: Armour | None = None
    options: HullOptions = Field(default_factory=HullOptions)

    def register_parts(self, container: set):
        if self.armour is not None:
            container.add(self.armour)
        container.add(self.options.stealth)


class Ship(BaseModel):
    tl: int
    displacement: int
    hull: Hull
    parts: set[ShipPart] = Field(default_factory=set)

    @property
    def cargo(self):
        cargo = self.displacement * self.hull.configuration.usage_factor
        for part in self.parts:
            cargo -= part.tons
        return cargo

    @property
    def self_sealing(self):
        return self.tl >= 9

    def model_post_init(self, __context: Any) -> None:
        self.hull.register_parts(self.parts)
        for part in self.parts:
            part.bind(self)
