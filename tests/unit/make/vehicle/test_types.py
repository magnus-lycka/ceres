"""Vehicle types: the baseline a design starts from, before size and features.

Rules: refs/vehicle/04_vehicle_types.md
"""

import pytest

from ceres.make.vehicle.speed import SpeedBand
from ceres.make.vehicle.types import GROUND_VEHICLE


class TestGroundVehicleBaseline:
    """refs/vehicle/04_vehicle_types.md — Ground Vehicle."""

    def test_baseline_values(self):
        assert GROUND_VEHICLE.name == 'Ground Vehicle'
        assert GROUND_VEHICLE.tl == 1
        assert GROUND_VEHICLE.agility == 0
        assert GROUND_VEHICLE.hull_per_space == 2
        assert GROUND_VEHICLE.shipping_per_space == 0.5
        assert GROUND_VEHICLE.cost_per_space == 750

    def test_it_has_no_baseline_traits(self):
        assert GROUND_VEHICLE.traits == ()


class TestPerformanceByTechLevel:
    """A type's Speed and Range improve as technology advances."""

    @pytest.mark.parametrize(
        ('tl', 'speed', 'km'),
        [
            (1, SpeedBand.IDLE, 0),
            (2, SpeedBand.IDLE, 0),
            (3, SpeedBand.IDLE, 50),
            (4, SpeedBand.VERY_SLOW, 100),
            (5, SpeedBand.SLOW, 300),
            (6, SpeedBand.SLOW, 300),
            (7, SpeedBand.MEDIUM, 500),
            (8, SpeedBand.MEDIUM, 500),
            (9, SpeedBand.HIGH, 800),
            (10, SpeedBand.HIGH, 800),
            (11, SpeedBand.FAST, 1000),
            (15, SpeedBand.FAST, 1000),
        ],
    )
    def test_speed_and_range(self, tl, speed, km):
        assert GROUND_VEHICLE.speed_at(tl) is speed
        assert GROUND_VEHICLE.range_at(tl) == km

    def test_below_its_tech_level_a_type_cannot_be_built(self):
        with pytest.raises(ValueError, match='TL1'):
            GROUND_VEHICLE.speed_at(0)


class TestAllowedFeatures:
    """A type names the features it can take; anything else is not buildable."""

    def test_a_ground_vehicle_can_be_an_atv(self):
        assert GROUND_VEHICLE.allows('ATV')

    def test_a_ground_vehicle_cannot_have_folding_wings(self):
        assert not GROUND_VEHICLE.allows('Folding Wings')
