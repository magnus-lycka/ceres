"""The Vehicle Size table: which band a number of Spaces falls in, and what it costs.

Rules: refs/vehicle/03_vehicle_design.md — Vehicle Size
"""

import pytest

from ceres.make.vehicle.size import VehicleSize
from ceres.make.vehicle.traits import Trait


class TestBandForSpaces:
    """Size is read off the Spaces count: 1-3, 4-19, 20-199, 200-1999, 2000+."""

    @pytest.mark.parametrize(
        ('spaces', 'expected'),
        [
            (1, VehicleSize.SMALL),
            (3, VehicleSize.SMALL),
            (4, VehicleSize.LIGHT),
            (19, VehicleSize.LIGHT),
            (20, VehicleSize.HEAVY),
            (199, VehicleSize.HEAVY),
            (200, VehicleSize.HUGE),
            (1999, VehicleSize.HUGE),
            (2000, VehicleSize.MASSIVE),
            (100_000, VehicleSize.MASSIVE),
        ],
    )
    def test_band_boundaries(self, spaces, expected):
        assert VehicleSize.for_spaces(spaces) is expected

    def test_a_vehicle_must_have_at_least_one_space(self):
        with pytest.raises(ValueError, match='at least one Space'):
            VehicleSize.for_spaces(0)


class TestSizeEffects:
    """Each band modifies Speed Band, Agility and the volume armour occupies."""

    @pytest.mark.parametrize(
        ('size', 'speed_modifier', 'agility_modifier', 'armour_volume'),
        [
            (VehicleSize.SMALL, 0, 0, 4.0),
            (VehicleSize.LIGHT, 0, 0, 2.0),
            (VehicleSize.HEAVY, -1, -1, 1.0),
            (VehicleSize.HUGE, -1, -2, 0.5),
            (VehicleSize.MASSIVE, -1, -4, 0.5),
        ],
    )
    def test_modifiers(self, size, speed_modifier, agility_modifier, armour_volume):
        assert size.speed_band_modifier == speed_modifier
        assert size.agility_modifier == agility_modifier
        assert size.armour_volume == armour_volume

    @pytest.mark.parametrize('size', [VehicleSize.HUGE, VehicleSize.MASSIVE])
    def test_the_largest_vehicles_are_unresponsive(self, size):
        assert Trait.UNRESPONSIVE in size.traits

    @pytest.mark.parametrize('size', [VehicleSize.SMALL, VehicleSize.LIGHT, VehicleSize.HEAVY])
    def test_smaller_vehicles_have_no_size_trait(self, size):
        assert size.traits == ()
