from ceres import hull, ship
from ceres.crew import CrewRole, required_crew_roles
from ceres.drives import DriveSection, JumpDrive1


def test_crew_role_total_salary():
    role = CrewRole(role='ENGINEER', count=2, monthly_salary=4_000)

    assert role.total_salary == 8_000


def test_required_crew_roles_for_small_jump_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(jump_drive=JumpDrive1()),
    )

    assert [(role.role, role.count, role.monthly_salary) for role in required_crew_roles(my_ship)] == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
    ]


def test_required_crew_roles_for_small_non_jump_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
    )

    assert [(role.role, role.count, role.monthly_salary) for role in required_crew_roles(my_ship)] == [
        ('PILOT', 1, 6_000),
    ]
