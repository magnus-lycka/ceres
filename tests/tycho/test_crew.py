from pydantic import ValidationError
import pytest

from tycho import hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection
from tycho.crafts import AirRaft, CarriedCraft, CraftSection, InternalDockingSpace
from tycho.crew import (
    Astrogator,
    Engineer,
    Pilot,
    ShipCrew,
    Steward,
)
from tycho.drives import DriveSection, FusionPlantTL12, JDrive, MDrive, PowerSection
from tycho.habitation import HabitationSection, LowBerths, Staterooms
from tycho.sensors import SensorsSection, SensorStations
from tycho.weapons import Barbette, Bay, Turret, WeaponsSection


def grouped_role_counts(roles):
    return [(role.role, quantity) for role, quantity in roles.grouped_roles]


def grouped_role_salaries(roles):
    return [(role.role, quantity, role.monthly_salary) for role, quantity in roles.grouped_roles]


def test_crew_role_total_salary():
    role = Engineer()
    assert role.total_salary == 4_000


def test_crew_role_display_role_includes_skill_level_when_above_one():
    role = Steward(level=3)
    assert role.display_role == 'STEWARD-3'


def test_required_crew_for_small_non_jump_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
    )

    assert grouped_role_salaries(my_ship.crew) == [
        ('PILOT', 1, 6_000),
    ]


def test_required_crew_for_small_jump_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=10)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
    )

    assert grouped_role_salaries(my_ship.crew) == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
    ]


def test_gunner_added_for_each_turret_on_commercial_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive(2), j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        weapons=WeaponsSection(turrets=[Turret(size='double')]),
    )

    assert grouped_role_counts(my_ship.crew) == [
        ('PILOT', 1),
        ('ASTROGATOR', 1),
        ('ENGINEER', 1),
        ('GUNNER', 1),
    ]


def test_large_ship_reduces_engineering_and_other_scaling_roles():
    my_ship = ship.Ship(
        tl=12,
        displacement=10_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive(1), j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=490)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
    )

    assert grouped_role_counts(my_ship.crew) == [
        ('PILOT', 1),
        ('ASTROGATOR', 1),
        ('ENGINEER', 9),
        ('MAINTENANCE', 8),
        ('ADMINISTRATOR', 4),
        ('SENSOR OPERATOR', 1),
        ('OFFICER', 1),
    ]


def test_military_ship_uses_military_pilot_and_gunner_rules():
    my_ship = ship.Ship(
        tl=12,
        military=True,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive(2)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        weapons=WeaponsSection(turrets=[Turret(size='double'), Turret(size='double')]),
    )

    assert grouped_role_counts(my_ship.crew) == [
        ('CAPTAIN', 1),
        ('PILOT', 3),
        ('ENGINEER', 1),
        ('GUNNER', 4),
        ('SENSOR OPERATOR', 3),
        ('OFFICER', 1),
    ]


def test_commercial_ship_gets_extra_pilot_for_carried_small_craft():
    class ShipBoat(CarriedCraft):
        shipping_size: int = 10
        cost: float = 1_000_000.0

    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive(2), j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        craft=CraftSection(docking_space=InternalDockingSpace(craft=ShipBoat())),
    )

    assert ('PILOT', 2) in grouped_role_counts(my_ship.crew)


def test_air_raft_does_not_add_extra_pilot():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive(2), j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        craft=CraftSection(docking_space=InternalDockingSpace(craft=AirRaft())),
    )

    assert ('PILOT', 1) in grouped_role_counts(my_ship.crew)


def test_military_small_non_jump_craft_still_uses_single_pilot():
    my_ship = ship.Ship(
        tl=12,
        military=True,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive(2)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=8)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
    )

    assert grouped_role_counts(my_ship.crew) == [
        ('PILOT', 1),
    ]


def test_commercial_ship_gets_gunner_for_barbette():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive(2)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        weapons=WeaponsSection(barbettes=[Barbette(weapon='pulse_laser')]),
    )

    assert ('GUNNER', 1) in grouped_role_counts(my_ship.crew)


def test_military_ship_gets_gunners_for_bays():
    my_ship = ship.Ship(
        tl=12,
        military=True,
        displacement=2_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive(2)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=100)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        weapons=WeaponsSection(
            bays=[Bay(size='small', weapon='missile'), Bay(size='medium', weapon='missile')],
        ),
    )

    assert ('GUNNER', 3) in grouped_role_counts(my_ship.crew)


def test_sensor_stations_drive_sensor_operator_count():
    my_ship = ship.Ship(
        tl=13,
        military=True,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(sensor_stations=SensorStations(count=2)),
    )

    assert ('SENSOR OPERATOR', 3) in grouped_role_counts(my_ship.crew)


def test_explicit_crew_input_overrides_rule_based_crew():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=10)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        crew=ShipCrew(roles=[Pilot(), Engineer()]),
    )

    assert grouped_role_counts(my_ship.crew) == [
        ('PILOT', 1),
        ('ENGINEER', 1),
    ]


def test_understaffed_explicit_crew_input_emits_warning():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=10)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        crew=ShipCrew(roles=[Pilot(), Engineer()]),
    )

    assert ('warning', 'ASTROGATOR below recommended count: 0 < 1') in [
        (note.category.value, note.message) for note in my_ship.crew.notes
    ]


def test_overstaffed_explicit_crew_input_emits_warning():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        crew=ShipCrew(roles=[Pilot(), Pilot()]),
    )

    assert ('info', 'PILOT above recommended count: 2 > 1') in [
        (note.category.value, note.message) for note in my_ship.crew.notes
    ]


def test_overstaffed_explicit_crew_input_warning_is_exposed_in_spec_crew_notes():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        crew=ShipCrew(roles=[Pilot(), Pilot()]),
    )

    spec = my_ship.build_spec()
    assert ('info', 'PILOT above recommended count: 2 > 1') in [
        (note.category.value, note.message) for note in spec.crew_notes
    ]


def test_explicit_crew_notes_are_not_stored_on_ship_level():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        crew=ShipCrew(roles=[Pilot(), Pilot()]),
    )

    assert my_ship.notes == []
    assert ('info', 'PILOT above recommended count: 2 > 1') in [
        (note.category.value, note.message) for note in my_ship.crew.notes
    ]


def test_small_commercial_ship_does_not_require_separate_maintenance_crew():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive(1), j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
    )

    assert ('MAINTENANCE', 1) not in grouped_role_counts(my_ship.crew)


def test_steward_added_for_middle_passenger_manifest():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive(1), j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        habitation=HabitationSection(staterooms=Staterooms(count=10)),
        passenger_vector={'middle': 16},
    )

    assert ('STEWARD', 1) in grouped_role_counts(my_ship.crew)


def test_steward_requirement_uses_skill_levels_for_large_middle_passenger_manifest():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive(1), j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=40)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        habitation=HabitationSection(staterooms=Staterooms(count=130)),
        passenger_vector={'middle': 250},
    )

    steward_roles = [role for role in my_ship.crew.recommended_roles if role.role == 'STEWARD']
    assert [(role.level, role.monthly_salary) for role in steward_roles] == [
        (3, 4_000),
    ]


def test_steward_requirement_caps_single_person_skill_at_three():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive(1), j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=40)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        habitation=HabitationSection(staterooms=Staterooms(count=210)),
        passenger_vector={'middle': 350},
    )

    steward_roles = [role for role in my_ship.crew.recommended_roles if role.role == 'STEWARD']
    assert [(role.level, role.monthly_salary) for role in steward_roles] == [
        (3, 4_000),
        (1, 2_000),
    ]


def test_explicit_crew_input_warns_when_steward_missing_for_passenger_manifest():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive(1), j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        habitation=HabitationSection(staterooms=Staterooms(count=10)),
        crew=ShipCrew(roles=[Pilot(), Astrogator(), Engineer()]),
        passenger_vector={'middle': 16},
    )

    assert ('warning', 'STEWARD below recommended count: 0 < 1') in [
        (note.category.value, note.message) for note in my_ship.crew.notes
    ]


def test_crew_input_rejects_list_form():
    with pytest.raises(ValidationError):
        ship.Ship(
            tl=12,
            displacement=100,
            hull=hull.Hull(configuration=hull.streamlined_hull),
            crew={'roles': [('PILOT', 2), ('ENGINEER', 1)]},
        )


def test_default_middle_passengers_use_only_unused_staterooms():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=10)),
        crew=ShipCrew(roles=[Pilot()] * 7),
    )

    assert my_ship.expenses.life_support == 29_000


def test_high_passage_uses_one_stateroom_each():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=4)),
        crew=ShipCrew(roles=[Pilot(), Pilot()]),
        passenger_vector={'high': 2, 'middle': 2},
    )

    assert my_ship.expenses.life_support == 10_000


def test_low_passage_uses_low_berths():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=1), low_berths=LowBerths(count=4)),
        crew=ShipCrew(roles=[Pilot()]),
        passenger_vector={'low': 3},
    )

    assert my_ship.expenses.life_support == 5_300
