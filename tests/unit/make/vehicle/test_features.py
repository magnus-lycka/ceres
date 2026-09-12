"""Features: specialisations of a type, and what they do to a design.

Rules: refs/vehicle/05_features.md
"""

from typing import Any

from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.speed import SpeedBand
from ceres.make.vehicle.traits import Trait
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs) -> Vehicle:
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))


class TestTraitsFromFeatures:
    def test_a_feature_grants_its_trait(self):
        assert Trait.ATV in a_vehicle(features=[Feature.ATV]).traits

    def test_a_feature_that_grants_nothing_adds_no_trait(self):
        # Fast changes performance but confers no trait of its own.
        assert a_vehicle(features=[Feature.FAST]).traits == ()


class TestPerformanceEffects:
    def test_fast_raises_the_speed_band(self):
        # A Heavy ground vehicle at TL12 is Fast less one band for size, so High;
        # the Fast feature returns the band it lost.
        assert a_vehicle(features=[Feature.FAST]).speed is SpeedBand.FAST

    def test_fast_halves_the_range(self):
        assert a_vehicle(features=[Feature.FAST]).range_km == 500

    def test_a_design_without_features_is_unchanged(self):
        assert a_vehicle().speed is SpeedBand.HIGH
        assert a_vehicle().range_km == 1000


class TestCost:
    """refs/vehicle/05_features.md — added Cost is a percentage of the base Cost,
    and several features are additive against that base rather than compounding.
    """

    def test_one_feature_adds_its_percentage_of_base(self):
        # ATV is +30% of base. 20 Spaces x Cr750 = Cr15,000.
        assert a_vehicle(features=[Feature.ATV]).cost == 15_000 * 1.30

    def test_features_add_against_the_base_not_each_other(self):
        # ATV +30% and Fast +100% give +130% of base, not 1.3 x 2.0.
        assert a_vehicle(features=[Feature.ATV, Feature.FAST]).cost == 15_000 * 2.30

    def test_a_feature_can_reduce_cost(self):
        # Open-Topped is -15% of base.
        vehicle = a_vehicle(vehicle_type=VehicleType.GRAV_VEHICLE, spaces=8, tl=8, features=[Feature.OPEN_TOPPED])
        assert vehicle.cost == 8 * 30_000 * 0.85


class TestLegality:
    def test_a_feature_its_type_does_not_allow_is_an_error(self):
        # Open-Topped applies to ground vehicles; Folding Wings does not, and ATV
        # is a ground-vehicle feature an airship cannot take.
        vehicle = a_vehicle(vehicle_type=VehicleType.AIRSHIP, spaces=128, tl=12, features=[Feature.ATV])
        assert any('ATV' in error for error in vehicle.notes.errors)

    def test_incompatible_features_are_an_error(self):
        # refs/vehicle/05_features.md — Slow is not compatible with Fast.
        vehicle = a_vehicle(features=[Feature.FAST, Feature.SLOW])
        errors = ' '.join(vehicle.notes.errors)
        assert 'Fast' in errors
        assert 'Slow' in errors

    def test_compatible_features_are_not_an_error(self):
        assert a_vehicle(features=[Feature.ATV, Feature.FAST]).notes.errors == []
