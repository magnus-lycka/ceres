"""The vehicle design object.

A vehicle is built from a type and a number of Spaces. Everything the design
states about itself is derived from those two, the Tech Level, and what gets
installed later.

Rules: refs/vehicle/03_vehicle_design.md, refs/vehicle/02_new_rules.md
"""

from math import ceil
from typing import Any

from pydantic import Field, field_validator

from ceres.shared import Assembly

from .features import Feature
from .size import VehicleSize
from .speed import SpeedBand
from .traits import Trait
from .types import VehicleType

_HULL_PER_STRUCTURE = 10


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
    features: list[Feature] = Field(default_factory=list)

    @field_validator('spaces')
    @classmethod
    def _sizeable(cls, spaces: int) -> int:
        # Too few Spaces is not a rule violation to note but an incoherent
        # design: there is no vehicle to size, cost or damage. VehicleSize owns
        # what a workable Spaces count is, so ask it rather than repeat it.
        VehicleSize.for_spaces(spaces)
        return spaces

    def model_post_init(self, __context: Any) -> None:
        if self.tl < self.vehicle_type.tl:
            self.error(f'{self.vehicle_type.value} requires TL{self.vehicle_type.tl}, this design is TL{self.tl}')
        self._check_features()

    def _check_features(self) -> None:
        for feature in self.features:
            if not feature.allowed_on(self.vehicle_type):
                self.error(f'{self.vehicle_type.value} cannot take the {feature.value} feature')
            if self.tl < feature.tl:
                self.error(f'the {feature.value} feature requires TL{feature.tl}, this design is TL{self.tl}')
        for index, feature in enumerate(self.features):
            for other in self.features[index + 1 :]:
                if feature.conflicts_with(other):
                    self.error(f'the {feature.value} and {other.value} features are not compatible')

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
        return ceil(self.hull / _HULL_PER_STRUCTURE)

    @property
    def shipping_tons(self) -> float:
        """Shipping tonnage: what this occupies as cargo, or in a hangar."""
        return self.spaces * self.vehicle_type.shipping_per_space

    @property
    def base_cost(self) -> float:
        """Spaces times the type's rate, before features."""
        return self.spaces * self.vehicle_type.cost_per_space

    @property
    def cost(self) -> float:
        """Base Cost plus each feature's share of it.

        Feature percentages are added against the base rather than compounding,
        as refs/vehicle/05_features.md states under Multiple Features.
        """
        return self.base_cost * (1 + sum(feature.added_cost for feature in self.features))

    @property
    def agility(self) -> int:
        """Type and size and features.

        Not the design's final Agility: the Control System option contributes
        too, so this is incomplete until options are modelled (RIV-007).
        """
        return (
            self.vehicle_type.agility + self.size.agility_modifier + sum(feature.agility for feature in self.features)
        )

    @property
    def speed(self) -> SpeedBand:
        """Maximum Speed Band: the type's at this Tech Level, less the size penalty."""
        bands = self.size.speed_band_modifier + sum(feature.speed_bands for feature in self.features)
        return self.vehicle_type.speed_at(self.tl).shifted(bands)

    @property
    def cruise_speed(self) -> SpeedBand:
        return self.speed.cruise

    @property
    def range_km(self) -> int | None:
        """Range in kilometres, or None where the type states none at this TL."""
        base = self.vehicle_type.range_at(self.tl)
        if base is None:
            return None
        for feature in self.features:
            base *= feature.range_multiplier
        return round(base)

    @property
    def traits(self) -> tuple[Trait, ...]:
        from_features = tuple(trait for feature in self.features for trait in feature.traits)
        return self.vehicle_type.traits + self.size.traits + from_features
