"""The vehicle design object.

A vehicle is built from a type and a number of Spaces. Everything the design
states about itself is derived from those two, the Tech Level, and what gets
installed later.

Rules: refs/vehicle/03_vehicle_design.md, refs/vehicle/02_new_rules.md
"""

from math import ceil

from pydantic import field_validator

from ceres.shared import Assembly

from .size import VehicleSize
from .speed import SpeedBand
from .types import VehicleType

_STRUCTURE_PER_HULL = 10


class Vehicle(Assembly):
    """A vehicle design.

    Hull and Structure are both kept: modifiers apply to Hull, and Structure —
    what the stat block prints and play uses — is a tenth of the result,
    rounded up once at the end (RIV-001).
    """

    name: str
    vehicle_type: VehicleType
    spaces: int
    tl: int

    @field_validator('spaces')
    @classmethod
    def _at_least_one_space(cls, spaces: int) -> int:
        # Not a rule violation to note but an incoherent design: there is no
        # vehicle to size, cost or damage.
        if spaces < 1:
            raise ValueError(f'a vehicle needs at least one Space, got {spaces}')
        return spaces

    def model_post_init(self, __context) -> None:
        if self.tl < self.vehicle_type.tl:
            self.error(f'{self.vehicle_type.name} requires TL{self.vehicle_type.tl}, this design is TL{self.tl}')

    @property
    def size(self) -> VehicleSize:
        return VehicleSize.for_spaces(self.spaces)

    @property
    def hull(self) -> float:
        """Spaces times the type's rate. Never less than 1, whatever reduces it.

        Not rounded: the rules round once, at Structure (RIV-001). A type such as
        an airship at 0.2 per Space produces a genuinely fractional Hull.
        """
        return max(self.spaces * self.vehicle_type.hull_per_space, 1)

    @property
    def structure(self) -> int:
        """The damage threshold: one-tenth of Hull, rounded up."""
        return ceil(self.hull / _STRUCTURE_PER_HULL)

    @property
    def shipping_tons(self) -> float:
        """Displacement when carried as cargo by a ship."""
        return self.spaces * self.vehicle_type.shipping_per_space

    @property
    def cost(self) -> float:
        return self.spaces * self.vehicle_type.cost_per_space

    @property
    def agility(self) -> int:
        return self.vehicle_type.agility + self.size.agility_modifier

    @property
    def speed(self) -> SpeedBand:
        """Maximum Speed Band: the type's at this Tech Level, less the size penalty."""
        return self.vehicle_type.speed_at(self.tl).shifted(self.size.speed_band_modifier)

    @property
    def cruise_speed(self) -> SpeedBand:
        return self.speed.cruise

    @property
    def range_km(self) -> int | None:
        """Range in kilometres, or None where the type states none at this TL."""
        return self.vehicle_type.range_at(self.tl)

    @property
    def traits(self) -> tuple[str, ...]:
        return self.vehicle_type.traits + self.size.traits
