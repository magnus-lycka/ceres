"""Core options: what a vehicle is fitted with, and what it can then do.

Rules: refs/vehicle/09_core_options.md
"""

from typing import Any

from ceres.make.vehicle.options import Autopilot, ControlSystem, NavigationSystem, SensorSystem
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs) -> Vehicle:
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))


class TestControlSystem:
    """refs/vehicle/09_core_options.md — Control Systems grant Agility (RIV-007)."""

    def test_an_improved_control_system_raises_agility(self):
        # A Heavy ground vehicle is Agility -1 before its controls.
        assert a_vehicle(options=[ControlSystem(quality='improved')]).agility == 0

    def test_a_basic_control_system_grants_nothing(self):
        assert a_vehicle(options=[ControlSystem(quality='basic')]).agility == -1

    def test_a_primitive_control_system_costs_agility(self):
        assert a_vehicle(options=[ControlSystem(quality='primitive')]).agility == -2

    def test_it_costs_what_the_table_says(self):
        assert a_vehicle(options=[ControlSystem(quality='improved')]).cost == 15_000 + 5_000


class TestAutopilot:
    def test_it_flies_at_the_listed_skill_level(self):
        assert a_vehicle(options=[Autopilot(quality='basic')]).autopilot_skill == 0
        assert a_vehicle(options=[Autopilot(quality='improved')]).autopilot_skill == 1

    def test_a_design_without_one_has_no_autopilot(self):
        assert a_vehicle().autopilot_skill is None


class TestNavigationSystem:
    def test_it_grants_its_navigation_dm(self):
        assert a_vehicle(options=[NavigationSystem(quality='improved')]).navigation_dm == 2
        assert a_vehicle(options=[NavigationSystem(quality='basic')]).navigation_dm == 1

    def test_a_design_without_one_has_no_navigation_dm(self):
        assert a_vehicle().navigation_dm is None


class TestSensorSystem:
    def test_it_grants_a_dm_and_a_range(self):
        vehicle = a_vehicle(options=[SensorSystem(quality='improved')])
        assert vehicle.sensors_dm == 1
        assert vehicle.sensors_range_km == 5

    def test_a_design_without_sensors_has_neither(self):
        assert a_vehicle().sensors_dm is None
        assert a_vehicle().sensors_range_km is None


class TestThePublishedDesigns:
    """Both catalogue entries print these figures in their equipment sub-table."""

    def test_the_atv(self):
        atv = a_vehicle(
            options=[
                ControlSystem(quality='improved'),
                Autopilot(quality='basic'),
                NavigationSystem(quality='improved'),
                SensorSystem(quality='improved'),
            ]
        )
        assert atv.agility == 0
        assert atv.autopilot_skill == 0
        assert atv.navigation_dm == 2
        assert atv.sensors_dm == 1
        assert atv.sensors_range_km == 5

    def test_the_air_raft(self):
        air_raft = Vehicle(
            name='Air/Raft',
            vehicle_type=VehicleType.GRAV_VEHICLE,
            spaces=8,
            tl=8,
            options=[
                ControlSystem(quality='basic'),
                Autopilot(quality='improved'),
                NavigationSystem(quality='basic'),
                SensorSystem(quality='basic'),
            ],
        )
        assert air_raft.agility == 1
        assert air_raft.autopilot_skill == 1
        assert air_raft.navigation_dm == 1
        assert air_raft.sensors_dm == 0
        assert air_raft.sensors_range_km == 1
