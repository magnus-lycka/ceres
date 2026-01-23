from enum import Enum

from pydantic import BaseModel

from .armour import Armour
from .parts import ShipPart


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

    @staticmethod
    def self_sealing(tl):
        return tl >= 9


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


class ArmourType(BaseModel):
    tl: int
    tonnage: float
    cost: int
    max_protection: int


class TitaniumSteel(ArmourType):
    pass


class Ship(BaseModel):
    tl: int
    displacement: int
    hull_configuration: HullConfiguration
    armour: Armour | None = None
    parts: list[ShipPart] = []

    @property
    def hull(self):
        return self.hull_configuration.points(self.displacement)

    @property
    def cargo(self):
        cargo = self.displacement * self.hull_configuration.usage_factor
        for part in self.parts:
            cargo -= part.tons
        return cargo

    @property
    def self_sealing(self):
        return self.tl >= 9

    def set_armour(self, kind: type[Armour], protection: int):
        ships_armour = kind(
            tl=self.tl, protection=protection, displacement=self.displacement
        )
        self.parts.append(ships_armour)
