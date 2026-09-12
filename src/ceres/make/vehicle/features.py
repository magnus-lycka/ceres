"""Features: specialisations of a vehicle type.

A feature is not a part and occupies no Spaces. It modifies what the vehicle
already is — its performance, its Cost, the traits it carries — and each is
restricted to the types that may take it.

Only the features the current designs need are described. The rest of the
chapter's table joins them as designs call for them.

Rules: refs/vehicle/05_features.md
"""

from dataclasses import dataclass
from enum import StrEnum

from .traits import Trait
from .types import VehicleType


@dataclass(frozen=True)
class _FeatureEntry:
    """One row of the Features chapter.

    `added_cost` is a fraction of the vehicle's *base* Cost. Several features on
    one vehicle add their fractions against that base rather than compounding,
    which the chapter states explicitly.
    """

    tl: int
    incompatible_with: frozenset[str] = frozenset()
    traits: tuple[Trait, ...] = ()
    speed_bands: int = 0
    range_multiplier: float = 1.0
    agility: int = 0
    added_cost: float = 0.0


class Feature(StrEnum):
    """A feature a design may take, if its type allows it.

    The member's value is the name the type tables use in their allowed-feature
    lists, so a type can be asked directly whether it permits a feature.
    """

    ATV = 'ATV'
    FAST = 'Fast'
    OPEN_TOPPED = 'Open-Topped'
    SLOW = 'Slow'

    @property
    def _entry(self) -> _FeatureEntry:
        return _FEATURES[self]

    @property
    def tl(self) -> int:
        return self._entry.tl

    @property
    def traits(self) -> tuple[Trait, ...]:
        return self._entry.traits

    @property
    def speed_bands(self) -> int:
        return self._entry.speed_bands

    @property
    def range_multiplier(self) -> float:
        return self._entry.range_multiplier

    @property
    def agility(self) -> int:
        return self._entry.agility

    @property
    def added_cost(self) -> float:
        """Fraction of the vehicle's base Cost this feature adds, or removes."""
        return self._entry.added_cost

    def conflicts_with(self, other: Feature) -> bool:
        return other.value in self._entry.incompatible_with

    def allowed_on(self, vehicle_type: VehicleType) -> bool:
        return vehicle_type.allows(self.value)


# refs/vehicle/05_features.md
_FEATURES: dict[Feature, _FeatureEntry] = {
    Feature.ATV: _FeatureEntry(
        tl=0,
        incompatible_with=frozenset({'Off-Roader', 'Rail Rider', 'Tracks'}),
        traits=(Trait.ATV,),
        added_cost=0.30,
    ),
    Feature.FAST: _FeatureEntry(
        tl=0,
        incompatible_with=frozenset({'Slow', 'Supersonic'}),
        speed_bands=1,
        range_multiplier=0.5,
        added_cost=1.00,
    ),
    Feature.OPEN_TOPPED: _FeatureEntry(
        tl=0,
        incompatible_with=frozenset({'AFV', 'Hypersonic', 'Open Frame', 'Supersonic'}),
        traits=(Trait.OPEN_TOPPED,),
        added_cost=-0.15,
    ),
    Feature.SLOW: _FeatureEntry(
        tl=0,
        incompatible_with=frozenset({'Fast'}),
        speed_bands=-1,
        range_multiplier=1.5,
        added_cost=-0.25,
    ),
}
