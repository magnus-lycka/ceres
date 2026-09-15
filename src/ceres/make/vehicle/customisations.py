"""Customisations: major modifications to power, speed and range.

Unlike a feature, a customisation is parameterised and can be applied more than
once, and it changes how many Spaces the vehicle has to spend. Some consume
Spaces, some free them.

Only the customisations the current designs need are described.

Rules: refs/vehicle/06_customisation.md
"""

from math import ceil, floor
from typing import Annotated, Literal

from pydantic import Field

from .base import InstalledInVehicle
from .grades import Grade
from .spec import EquipmentSpec

_FUSION_PLUS_SPACE_FRACTION = 0.10
_FUSION_PLUS_POWER_PER_SPACE = 1
_SPEED_STEP_SPACE_FRACTION = 0.10
# refs: the official Vehicle Design Worksheet computes fuel capacity's effect
# on Range as 2.5 x the share of the vehicle given over to fuel (RIV-008).
_RANGE_PER_FUEL_SHARE = 2.5


class _Customisation(InstalledInVehicle):
    """What every customisation can be asked, whether or not it answers."""

    @property
    def equipment(self) -> EquipmentSpec | None:
        """This customisation as an item of equipment, or None if it is not one.

        Speed and fuel modifications change the vehicle rather than adding
        anything to it, so a catalogue entry never lists them.
        """
        return None

    @property
    def spaces_delta(self) -> int:
        """Spaces freed (positive) or consumed (negative) in its vehicle."""
        return 0

    @property
    def range_multiplier(self) -> float:
        """Applied to Range alongside features, before fuel percentages."""
        return 1.0

    @property
    def range_fraction(self) -> float:
        """Pooled with the other fuel percentages and applied last."""
        return 0.0

    @property
    def speed_bands(self) -> int:
        return 0

    @property
    def added_cost(self) -> float:
        """A fraction of the vehicle's base Cost."""
        return 0.0

    @property
    def cost(self) -> float:
        """Cost in credits that is not a fraction of the vehicle's base."""
        return 0.0


class FusionPlusPlant(_Customisation):
    """A compact fusion plant, refuelled from water, that greatly extends range."""

    kind: Literal['FUSION_PLUS'] = 'FUSION_PLUS'
    quality: Literal[Grade.BASIC] = Grade.BASIC

    @property
    def plant_spaces(self) -> int:
        """A tenth of the vehicle, and never less than one Space."""
        return max(ceil(self.vehicle.spaces * _FUSION_PLUS_SPACE_FRACTION), 1)

    @property
    def spaces_delta(self) -> int:
        return -self.plant_spaces

    @property
    def equipment(self) -> EquipmentSpec | None:
        return EquipmentSpec(name='Fusion+', grade=self.quality, power_points=self.power_points)

    @property
    def power_points(self) -> int:
        """One Power per Space of plant, for a basic Fusion+."""
        return self.plant_spaces * _FUSION_PLUS_POWER_PER_SPACE

    @property
    def range_multiplier(self) -> float:
        return 5.0

    @property
    def cost(self) -> float:
        return self.plant_spaces * 15_000


class SlowerSpeed(_Customisation):
    """A smaller engine: a Speed Band given up for Spaces and a cheaper vehicle."""

    kind: Literal['SLOWER'] = 'SLOWER'
    steps: int = 1

    @property
    def spaces_delta(self) -> int:
        return floor(self.vehicle.spaces * _SPEED_STEP_SPACE_FRACTION) * self.steps

    @property
    def speed_bands(self) -> int:
        return -self.steps

    @property
    def added_cost(self) -> float:
        return -0.10 * self.steps


class FuelEfficiency(_Customisation):
    """A more or less efficient engine: Range traded against Cost, not Spaces.

    Each positive step multiplies Range by a further half and each negative step
    takes away a quarter, so two steps double it. Available up to three times, as
    the Tech Level allows.
    """

    kind: Literal['FUEL_EFFICIENCY'] = 'FUEL_EFFICIENCY'
    steps: int = 1

    @property
    def range_fraction(self) -> float:
        return self.steps * (0.5 if self.steps > 0 else 0.25)

    @property
    def added_cost(self) -> float:
        return self.steps * (0.25 if self.steps > 0 else 0.10)


class FuelCapacity(_Customisation):
    """Bigger or smaller tanks, measured in the Spaces given over to fuel.

    Range changes by 2.5 times the share of the vehicle carried as fuel, which
    is why the rules quote a tenth of the vehicle as +25% Range. Fuel capacity is
    paid for in Spaces and never in money.
    """

    kind: Literal['FUEL_CAPACITY'] = 'FUEL_CAPACITY'
    spaces: int = 1

    @property
    def spaces_delta(self) -> int:
        return -self.spaces

    @property
    def range_fraction(self) -> float:
        return _RANGE_PER_FUEL_SHARE * self.spaces / self.vehicle.spaces


class AquaticDrive(_Customisation):
    """A secondary drive letting a land vehicle cross calm water.

    Its performance is that of an equivalent watercraft, one Speed Band and one
    Agility lower, with a tenth of the range.
    """

    kind: Literal['AQUATIC_DRIVE'] = 'AQUATIC_DRIVE'

    @property
    def equipment(self) -> EquipmentSpec | None:
        speed, distance = self.vehicle.aquatic_performance
        return EquipmentSpec(name='Aquatic Drive', speed=speed, range_km=round(distance))

    @property
    def drive_spaces(self) -> int:
        return max(ceil(self.vehicle.spaces * 0.05), 1)

    @property
    def spaces_delta(self) -> int:
        return -self.drive_spaces

    @property
    def cost(self) -> float:
        return 1_500 * self.vehicle.spaces


CustomisationUnion = Annotated[
    FusionPlusPlant | SlowerSpeed | FuelEfficiency | FuelCapacity | AquaticDrive,
    Field(discriminator='kind'),
]
