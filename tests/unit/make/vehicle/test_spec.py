"""The spec a design projects for rendering.

The spec carries raw values; composing display strings such as 'High (Medium)'
is the report context's job, as it is for ships.
"""

from typing import Any

from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.options import Autopilot, NavigationSystem, SensorSystem, VehicleTransceiver
from ceres.make.vehicle.size import VehicleSize
from ceres.make.vehicle.speed import SpeedBand
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs) -> Vehicle:
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))


class TestTargetSize:
    """refs/vehicle/02_new_rules.md — Target Size. Finer than the size bands:
    Heavy splits at 100 Spaces and Huge at 1,000.
    """

    def test_the_published_designs(self):
        # ATV: 20 Spaces, DM+2. Air/Raft: 8 Spaces, DM+1.
        assert a_vehicle(spaces=20).target_size_dm == 2
        assert a_vehicle(spaces=8).target_size_dm == 1

    def test_the_band_boundaries(self):
        assert a_vehicle(spaces=3).target_size_dm == 0
        assert a_vehicle(spaces=99).target_size_dm == 2
        assert a_vehicle(spaces=100).target_size_dm == 3
        assert a_vehicle(spaces=999).target_size_dm == 4
        assert a_vehicle(spaces=1000).target_size_dm == 5
        assert a_vehicle(spaces=2000).target_size_dm == 6


class TestCruising:
    """refs/vehicle/02_new_rules.md — cruising speed is one band lower and
    increases Range by 50%.
    """

    def test_cruise_range_is_half_again(self):
        # The Air/Raft's 2,000 becomes 3,000; here 1,000 becomes 1,500.
        assert a_vehicle(spaces=6).cruise_range_km == 1500

    def test_a_design_with_no_range_has_no_cruise_range(self):
        assert a_vehicle(spaces=6, tl=2).cruise_range_km is None


class TestSpecCarriesRawValues:
    def test_the_headline_figures(self):
        spec = a_vehicle(features=[Feature.ATV, Feature.FAST]).build_spec()

        assert spec.name == 'Test'
        assert spec.tl == 12
        assert spec.structure == 4
        assert spec.shipping_tons == 10
        assert spec.cost == 34_500
        assert spec.speed is SpeedBand.FAST
        assert spec.cruise_speed is SpeedBand.HIGH
        assert spec.range_km == 500
        assert spec.skill == 'Drive (varies)'

    def test_it_describes_the_type(self):
        spec = a_vehicle().build_spec()

        assert spec.size is VehicleSize.HEAVY
        assert spec.vehicle_type is VehicleType.GROUND_VEHICLE
        assert spec.spaces == 20
        assert spec.target_size_dm == 2

    def test_features_and_traits_are_listed_together(self):
        # The catalogue prints one 'FEATURES AND TRAITS' line mixing both.
        spec = a_vehicle(features=[Feature.ATV, Feature.FAST]).build_spec()

        assert 'ATV' in spec.features_and_traits
        assert 'Fast' in spec.features_and_traits

    def test_a_design_with_neither_lists_nothing(self):
        assert a_vehicle(spaces=6, tl=7).build_spec().features_and_traits == []


class TestSpecCarriesWhatTheEquipmentConfers:
    """Numbers and flags, not the text the catalogue's small table prints."""

    def test_the_figures_the_fittings_confer(self):
        spec = a_vehicle(
            options=[
                Autopilot(quality='basic'),
                NavigationSystem(quality='improved'),
                SensorSystem(quality='improved'),
                VehicleTransceiver(range_km=500, satellite_uplink=True, tightbeam=True, encryption=True),
            ]
        ).build_spec()

        assert spec.autopilot_skill == 0
        assert spec.navigation_dm == 2
        assert spec.sensors_dm == 1
        assert spec.sensors_range_km == 5
        assert spec.communications is not None
        assert spec.communications.range_km == 500
        assert spec.communications.tightbeam
        assert spec.communications.satellite_uplink
        assert spec.communications.encryption

    def test_a_design_without_them_has_none(self):
        spec = a_vehicle().build_spec()

        assert spec.autopilot_skill is None
        assert spec.navigation_dm is None
        assert spec.sensors_dm is None
        assert spec.sensors_range_km is None
        assert spec.communications is None
