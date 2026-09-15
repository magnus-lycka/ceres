"""Core options: what a vehicle is fitted with, and what it can then do.

Rules: refs/vehicle/09_core_options.md
"""

from typing import Any

from ceres.make.vehicle.grades import Grade
from ceres.make.vehicle.options import (
    AirLock,
    Autopilot,
    Bunk,
    CollisionProtection,
    ControlSystem,
    FireExtinguishers,
    Fresher,
    FresherSize,
    Galley,
    GalleyKind,
    LifeSupport,
    LifeSupportDuration,
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
        assert a_vehicle(options=[ControlSystem(quality=Grade.IMPROVED)]).agility == 0

    def test_a_basic_control_system_grants_nothing(self):
        assert a_vehicle(options=[ControlSystem(quality=Grade.BASIC)]).agility == -1

    def test_a_primitive_control_system_costs_agility(self):
        assert a_vehicle(options=[ControlSystem(quality=Grade.PRIMITIVE)]).agility == -2

    def test_it_costs_what_the_table_says(self):
        assert a_vehicle(options=[ControlSystem(quality=Grade.IMPROVED)]).cost == 15_000 + 5_000


class TestAutopilot:
    def test_it_flies_at_the_listed_skill_level(self):
        assert a_vehicle(options=[Autopilot(quality=Grade.BASIC)]).autopilot_skill == 0
        assert a_vehicle(options=[Autopilot(quality=Grade.IMPROVED)]).autopilot_skill == 1

    def test_a_design_without_one_has_no_autopilot(self):
        assert a_vehicle().autopilot_skill is None


class TestNavigationSystem:
    def test_it_grants_its_navigation_dm(self):
        assert a_vehicle(options=[NavigationSystem(quality=Grade.IMPROVED)]).navigation_dm == 2
        assert a_vehicle(options=[NavigationSystem(quality=Grade.BASIC)]).navigation_dm == 1

    def test_a_design_without_one_has_no_navigation_dm(self):
        assert a_vehicle().navigation_dm is None


class TestSensorSystem:
    def test_it_grants_a_dm_and_a_range(self):
        vehicle = a_vehicle(options=[SensorSystem(quality=Grade.IMPROVED)])
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
                ControlSystem(quality=Grade.IMPROVED),
                Autopilot(quality=Grade.BASIC),
                NavigationSystem(quality=Grade.IMPROVED),
                SensorSystem(quality=Grade.IMPROVED),
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
                ControlSystem(quality=Grade.BASIC),
                Autopilot(quality=Grade.IMPROVED),
                NavigationSystem(quality=Grade.BASIC),
                SensorSystem(quality=Grade.BASIC),
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
        assert (
            a_vehicle(options=[CollisionProtection(quality=Grade.IMPROVED, spaces_protected=16)]).cost
            == 15_000 + 16_000
        )

    def test_life_support_covers_twenty_people_per_space(self):
        vehicle = a_vehicle(options=[LifeSupport(duration=LifeSupportDuration.SHORT_TERM, people=8)])
        assert vehicle.available_spaces == 19
        assert vehicle.cost == 15_000 + 10_000

    def test_a_fresher_and_a_galley_are_priced_by_the_space_they_take(self):
        assert a_vehicle(options=[Fresher(quality=FresherSize.STANDARD)]).cost == 15_000 + 1_500
        assert a_vehicle(options=[Galley(quality=GalleyKind.MINI)]).cost == 15_000 + 250

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


class TestComputer:
    def test_a_computer_is_a_gear_part(self):
        assert VehicleComputer(processing=1).part.processing == 1

    def test_a_computer_is_free_once_it_is_standard_equipment(self):
        # refs/vehicle/16_automation.md — Computer/1 is Cr500 at TL8, free at TL11+.
        assert a_vehicle(tl=8, options=[VehicleComputer(processing=1)]).cost == 15_000 + 500
        assert a_vehicle(tl=11, options=[VehicleComputer(processing=1)]).cost == 15_000
        assert a_vehicle(tl=12, options=[VehicleComputer(processing=1)]).cost == 15_000

    def test_it_gets_cheaper_by_tech_level_stage_until_then(self):
        # refs/vehicle/16_automation.md — computers "decrease in cost at higher
        # Tech Levels with an interval of one TL as indicated in the Tech Level
        # Stages table": a half one TL on, a quarter two TLs on.
        assert a_vehicle(tl=9, options=[VehicleComputer(processing=1)]).cost == 15_000 + 250
        assert a_vehicle(tl=10, options=[VehicleComputer(processing=1)]).cost == 15_000 + 125

    def test_the_stages_continue_while_a_computer_is_not_yet_free(self):
        # Computer/3 is Cr2000 at TL12 and free only at TL16, so it reaches the
        # tenth of advanced at TL15.
        assert a_vehicle(tl=13, options=[VehicleComputer(processing=3)]).cost == 15_000 + 1_000
        assert a_vehicle(tl=15, options=[VehicleComputer(processing=3)]).cost == 15_000 + 200


class TestFireExtinguishers:
    def test_they_carry_the_gear_part(self):
        assert FireExtinguishers().part.cost == 50


class TestTransceiver:
    """A vehicle's transceiver is the gear item, priced by the vehicle rules.

    ADR-0002: the part says what the item is; the Vehicle Handbook says what
    fitting one costs. RIV-011: that price is the Core Options table, discounted
    by the Tech Level Stage the design chooses — a 500km transceiver is Cr600,
    half at improved, a twentieth at superior.
    """

    def test_a_basic_transceiver_is_the_listed_price(self):
        vehicle = a_vehicle(options=[VehicleTransceiver(range_km=500)])
        assert vehicle.cost == 15_000 + 600
        assert [item.grade for item in vehicle.build_spec().equipment] == ['basic']

    def test_an_improved_transceiver_is_half(self):
        vehicle = a_vehicle(options=[VehicleTransceiver(range_km=500, stage=Grade.IMPROVED)])
        assert vehicle.cost == 15_000 + 300
        assert [item.grade for item in vehicle.build_spec().equipment] == ['improved']

    def test_a_superior_transceiver_is_a_twentieth(self):
        vehicle = a_vehicle(options=[VehicleTransceiver(range_km=500, stage=Grade.SUPERIOR)])
        assert vehicle.cost == 15_000 + 30
        assert [item.grade for item in vehicle.build_spec().equipment] == ['superior']

    def test_its_options_are_priced_in_their_own_right(self):
        # refs/vehicle/09_core_options.md — Transceiver Options. The stage
        # discounts the transceiver, not what is added to it.
        vehicle = a_vehicle(
            options=[
                VehicleTransceiver(
                    range_km=500, stage=Grade.SUPERIOR, satellite_uplink=True, tightbeam=True, encryption=True
                )
            ]
        )
        assert vehicle.cost == 15_000 + 30 + 1_000 + 2_000 + 4_000

    def test_it_installs_the_gear_part(self):
        vehicle = a_vehicle(tl=8, options=[VehicleTransceiver(range_km=500)])
        (transceiver,) = [option for option in vehicle.options if isinstance(option, VehicleTransceiver)]
        assert transceiver.transceiver_part.range_km == 500
        assert transceiver.transceiver_part.tl == 8
