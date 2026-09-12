"""Core options: what a vehicle is fitted with, and what it can then do.

Rules: refs/vehicle/09_core_options.md
"""

from typing import Any

from ceres.make.vehicle.options import (
    AirLock,
    Autopilot,
    Bunk,
    CollisionProtection,
    ControlSystem,
    FireExtinguishers,
    Fresher,
    Galley,
    LifeSupport,
    NavigationSystem,
    SensorSystem,
    VacuumEnvironment,
    VehicleComputer,
    VehicleTransceiver,
)
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


class TestInstalledFittings:
    """refs/vehicle/13_internal_options.md — what each fitting costs and occupies."""

    def test_an_airlock_takes_two_spaces_each(self):
        vehicle = a_vehicle(options=[AirLock()])
        assert vehicle.available_spaces == 18
        assert vehicle.cost == 15_000 + 2_000

    def test_collision_protection_is_priced_per_space_protected(self):
        assert a_vehicle(options=[CollisionProtection(quality='improved', spaces_protected=16)]).cost == 15_000 + 16_000

    def test_life_support_covers_twenty_people_per_space(self):
        vehicle = a_vehicle(options=[LifeSupport(duration='short_term', people=8)])
        assert vehicle.available_spaces == 19
        assert vehicle.cost == 15_000 + 10_000

    def test_a_fresher_and_a_galley_are_priced_by_the_space_they_take(self):
        assert a_vehicle(options=[Fresher(quality='standard')]).cost == 15_000 + 1_500
        assert a_vehicle(options=[Galley(quality='mini')]).cost == 15_000 + 250

    def test_bunks_take_a_space_each(self):
        vehicle = a_vehicle(options=[Bunk(count=2)])
        assert vehicle.available_spaces == 18
        assert vehicle.cost == 15_000 + 400


class TestPricedByTheWholeVehicle:
    """Some options are priced by the size of the vehicle they fit out."""

    def test_vacuum_protection_scales_with_the_vehicle(self):
        assert a_vehicle(options=[VacuumEnvironment()]).cost == 15_000 + 40_000

    def test_fire_extinguishers_scale_with_the_vehicle(self):
        assert a_vehicle(options=[FireExtinguishers()]).cost == 15_000 + 400


class TestGearBackedOptions:
    """ADR-0002 — the item is gear; the vehicle rules price the installation."""

    def test_a_transceiver_is_a_gear_part(self):
        option = VehicleTransceiver(range_km=500)
        assert option.part.range_km == 500
        assert 'Transceiver' in option.part.description

    def test_transceiver_options_are_priced_by_the_vehicle_rules(self):
        option = VehicleTransceiver(range_km=500, satellite_uplink=True, tightbeam=True, encryption=True)
        assert option.cost(20) == 600 + 1_000 + 2_000 + 4_000

    def test_a_computer_is_a_gear_part(self):
        assert VehicleComputer(processing=1).part.processing == 1

    def test_a_computer_is_free_once_it_is_standard_equipment(self):
        # refs/vehicle/16_automation.md — Computer/1 is Cr500 at TL8, free at TL11+.
        assert a_vehicle(tl=8, options=[VehicleComputer(processing=1)]).cost == 15_000 + 500
        assert a_vehicle(tl=12, options=[VehicleComputer(processing=1)]).cost == 15_000

    def test_fire_extinguishers_carry_the_gear_part(self):
        assert FireExtinguishers().part.cost == 50


class TestTechStage:
    """refs/vehicle/08_options.md — Tech Level Stages. Transceivers and computers
    get cheaper as technology advances past their introduction.
    """

    def test_a_stage_names_itself_and_discounts_the_cost(self):
        # A 500km transceiver is Cr600 basic; superior is a twentieth of that.
        superior = VehicleTransceiver(range_km=500, stage='superior')
        assert superior.label == 'Transceiver (superior)'
        assert superior.cost(20) == 30

    def test_improved_halves_it(self):
        assert VehicleTransceiver(range_km=500, stage='improved').cost(20) == 300

    def test_basic_is_the_listed_price(self):
        assert VehicleTransceiver(range_km=500).cost(20) == 600

    def test_the_discount_applies_to_the_transceiver_not_its_options(self):
        # Options are priced in their own right, so only the set is discounted.
        superior = VehicleTransceiver(range_km=500, stage='superior', satellite_uplink=True)
        assert superior.cost(20) == 30 + 1_000
