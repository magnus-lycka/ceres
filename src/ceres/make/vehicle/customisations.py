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

from ceres.shared import CeresModel

_FUSION_PLUS_SPACE_FRACTION = 0.10
_SPEED_STEP_SPACE_FRACTION = 0.10
_FUEL_STEP_SPACE_FRACTION = 0.10


class _Customisation(CeresModel):
    """What every customisation can be asked, whether or not it answers."""

    def spaces_delta(self, spaces: int) -> int:
        """Spaces freed (positive) or consumed (negative) on a vehicle this big."""
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

    def cost(self, spaces: int) -> float:
        """Cost in credits that is not a fraction of the vehicle's base."""
        return 0.0


class FusionPlusPlant(_Customisation):
    """A compact fusion plant, refuelled from water, that greatly extends range."""

    kind: Literal['FUSION_PLUS'] = 'FUSION_PLUS'
    quality: Literal['basic'] = 'basic'

    def plant_spaces(self, spaces: int) -> int:
        """A tenth of the vehicle, and never less than one Space."""
        return max(ceil(spaces * _FUSION_PLUS_SPACE_FRACTION), 1)

    def spaces_delta(self, spaces: int) -> int:
        return -self.plant_spaces(spaces)

    @property
    def range_multiplier(self) -> float:
        return 5.0

    def cost(self, spaces: int) -> float:
        return self.plant_spaces(spaces) * 15_000


class SlowerSpeed(_Customisation):
    """A smaller engine: a Speed Band given up for Spaces and a cheaper vehicle."""

    kind: Literal['SLOWER'] = 'SLOWER'
    steps: int = 1

    def spaces_delta(self, spaces: int) -> int:
        return floor(spaces * _SPEED_STEP_SPACE_FRACTION) * self.steps

    @property
    def speed_bands(self) -> int:
        return -self.steps

    @property
    def added_cost(self) -> float:
        return -0.10 * self.steps


class IncreasedEfficiency(_Customisation):
    """A more efficient engine: more range for more money, at no cost in Spaces."""

    kind: Literal['INCREASED_EFFICIENCY'] = 'INCREASED_EFFICIENCY'
    steps: int = 1

    @property
    def range_fraction(self) -> float:
        return 0.50 * self.steps

    @property
    def added_cost(self) -> float:
        return 0.25 * self.steps


class IncreasedFuel(_Customisation):
    """Larger tanks: more range for Spaces, at no change in Cost."""

    kind: Literal['INCREASED_FUEL'] = 'INCREASED_FUEL'
    steps: int = 1

    def spaces_delta(self, spaces: int) -> int:
        return -ceil(spaces * _FUEL_STEP_SPACE_FRACTION) * self.steps

    @property
    def range_fraction(self) -> float:
        return 0.25 * self.steps


class DecreasedFuel(_Customisation):
    """Smaller tanks: range given up for Spaces, at no change in Cost."""

    kind: Literal['DECREASED_FUEL'] = 'DECREASED_FUEL'
    steps: int = 1

    def spaces_delta(self, spaces: int) -> int:
        return floor(spaces * _FUEL_STEP_SPACE_FRACTION) * self.steps

    @property
    def range_fraction(self) -> float:
        return -0.25 * self.steps


CustomisationUnion = Annotated[
    FusionPlusPlant | SlowerSpeed | IncreasedEfficiency | IncreasedFuel | DecreasedFuel,
    Field(discriminator='kind'),
]
