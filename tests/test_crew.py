from ceres import hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import Computer5, ComputerSection
from ceres.crew import CrewRole, required_crew_roles
from ceres.drives import DriveSection, FusionPlantTL12, JumpDrive1, MDrive1, MDrive2, PowerSection
from ceres.sensors import SensorsSection, SensorStations
from ceres.weapons import Barbette, Bay, Turret, WeaponsSection


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
        ('PILOT', 3),
        ('ENGINEER', 1),
        ('GUNNER', 4),
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
