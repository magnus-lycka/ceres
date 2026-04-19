from pydantic import ValidationError
import pytest

from tycho import hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer5, ComputerSection
from tycho.crafts import AirRaft, CarriedCraft, CraftSection, InternalDockingSpace
from tycho.crew import CrewRole, required_crew_roles
from tycho.drives import DriveSection, FusionPlantTL12, JumpDrive1, MDrive1, MDrive2, PowerSection
from tycho.habitation import HabitationSection, LowBerths, Staterooms
from tycho.sensors import SensorsSection, SensorStations
from tycho.weapons import Barbette, Bay, Turret, WeaponsSection


def test_crew_role_total_salary():
    role = CrewRole(role='ENGINEER', count=2, monthly_salary=4_000)
    assert role.total_salary == 8_000


def test_required_crew_roles_for_small_non_jump_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
    )

    assert [(role.role, role.count, role.monthly_salary) for role in required_crew_roles(my_ship)] == [
        ('PILOT', 1, 6_000),
    ]


def test_required_crew_roles_for_small_jump_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(jump_drive=JumpDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=10)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
    )

    assert [(role.role, role.count, role.monthly_salary) for role in required_crew_roles(my_ship)] == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
        ('MAINTENANCE', 1, 1_000),
    ]


def test_gunner_added_for_each_turret_on_commercial_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive2(), jump_drive=JumpDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        weapons=WeaponsSection(turrets=[Turret(size='double')]),
    )

    assert [(role.role, role.count) for role in required_crew_roles(my_ship)] == [
        ('PILOT', 1),
        ('ASTROGATOR', 1),
        ('ENGINEER', 1),
        ('MAINTENANCE', 1),
        ('GUNNER', 1),
    ]


def test_large_ship_reduces_engineering_and_other_scaling_roles():
    my_ship = ship.Ship(
        tl=12,
        displacement=10_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive1(), jump_drive=JumpDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=490)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
    )

    assert [(role.role, role.count) for role in required_crew_roles(my_ship)] == [
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
        drives=DriveSection(m_drive=MDrive2()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        weapons=WeaponsSection(turrets=[Turret(size='double'), Turret(size='double')]),
    )

    assert [(role.role, role.count) for role in required_crew_roles(my_ship)] == [
        ('CAPTAIN', 1),
        ('PILOT', 3),
        ('ENGINEER', 1),
        ('MAINTENANCE', 1),
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
        drives=DriveSection(m_drive=MDrive2(), jump_drive=JumpDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        craft=CraftSection(docking_space=InternalDockingSpace(craft=ShipBoat())),
    )

    assert ('PILOT', 2) in [(role.role, role.count) for role in required_crew_roles(my_ship)]


def test_air_raft_does_not_add_extra_pilot():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive2(), jump_drive=JumpDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        craft=CraftSection(docking_space=InternalDockingSpace(craft=AirRaft())),
    )

    assert ('PILOT', 1) in [(role.role, role.count) for role in required_crew_roles(my_ship)]


def test_military_small_non_jump_craft_still_uses_single_pilot():
    my_ship = ship.Ship(
        tl=12,
        military=True,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive2()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=8)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
    )

    assert [(role.role, role.count) for role in required_crew_roles(my_ship)] == [
        ('PILOT', 1),
    ]


def test_commercial_ship_gets_gunner_for_barbette():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive2()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=20)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        weapons=WeaponsSection(barbettes=[Barbette(weapon='pulse_laser')]),
    )

    assert ('GUNNER', 1) in [(role.role, role.count) for role in required_crew_roles(my_ship)]


def test_military_ship_gets_gunners_for_bays():
    my_ship = ship.Ship(
        tl=12,
        military=True,
        displacement=2_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive2()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=100)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        weapons=WeaponsSection(
            bays=[Bay(size='small', weapon='missile'), Bay(size='medium', weapon='missile')],
        ),
    )

    assert ('GUNNER', 3) in [(role.role, role.count) for role in required_crew_roles(my_ship)]


def test_sensor_stations_drive_sensor_operator_count():
    my_ship = ship.Ship(
        tl=13,
        military=True,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(sensor_stations=SensorStations(count=2)),
    )

    assert ('SENSOR OPERATOR', 3) in [(role.role, role.count) for role in required_crew_roles(my_ship)]


def test_explicit_crew_vector_overrides_rule_based_crew():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(jump_drive=JumpDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=10)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        crew_vector={'PILOT': 1, 'ENGINEER': 1},
    )

    assert [(role.role, role.count) for role in my_ship.crew_roles] == [
        ('PILOT', 1),
        ('ENGINEER', 1),
    ]


def test_understaffed_explicit_crew_vector_emits_warning():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(jump_drive=JumpDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=10)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        crew_vector={'PILOT': 1, 'ENGINEER': 1},
    )

    assert ('warning', 'ASTROGATOR below recommended count: 0 < 1') in [
        (note.category.value, note.message) for note in my_ship.notes
    ]
    assert ('warning', 'MAINTENANCE below recommended count: 0 < 1') in [
        (note.category.value, note.message) for note in my_ship.notes
    ]


def test_crew_vector_rejects_list_form():
    with pytest.raises(ValidationError):
        ship.Ship(
            tl=12,
            displacement=100,
            hull=hull.Hull(configuration=hull.streamlined_hull),
            crew_vector=[('PILOT', 2), ('ENGINEER', 1)],
        )


def test_default_middle_passengers_use_only_unused_staterooms():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=10)),
        crew_vector={'PILOT': 7},
    )

    assert my_ship.expenses.life_support == 29_000


def test_high_passage_uses_one_stateroom_each():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=4)),
        crew_vector={'PILOT': 2},
        passenger_vector={'high': 2, 'middle': 2},
    )

    assert my_ship.expenses.life_support == 10_000


def test_low_passage_uses_low_berths():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=1), low_berths=LowBerths(count=4)),
        crew_vector={'PILOT': 1},
        passenger_vector={'low': 3},
    )

    assert my_ship.expenses.life_support == 5_300
