import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import (
    DriveSection,
    FusionPlantTL8,
    FusionPlantTL12,
    JDrive2,
    MDrive1,
    MDrive2,
    PowerSection,
)
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.storage import FuelProcessor, FuelSection, JumpFuel, OperationFuel


def build_small_jump_ship() -> ship.Ship:
    return ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=60)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(bis=True)),
        habitation=HabitationSection(staterooms=[Stateroom()] * 4),
    )


def test_production_cost_matches_ship_property():
    my_ship = build_small_jump_ship()

    assert my_ship.expenses.production_cost == pytest.approx(my_ship.production_cost)


def test_operating_expense_components_match_ship_helpers():
    my_ship = build_small_jump_ship()

    assert my_ship.expenses.mortgage == pytest.approx(my_ship.expenses.mortgage)
    assert my_ship.expenses.maintenance == pytest.approx(my_ship.expenses.maintenance)
    assert my_ship.expenses.life_support == pytest.approx(
        my_ship.expenses.life_support_facilities + my_ship.expenses.life_support_people
    )
    assert my_ship.expenses.fuel == pytest.approx(my_ship.expenses.fuel)


def test_ship_expenses_object_exposes_rows_and_total():
    my_ship = build_small_jump_ship()

    assert [row.label for row in my_ship.expenses.rows] == [
        'Production Cost',
        'Sales Price New',
        'Mortgage',
        'Maintenance',
        'Life Support Facilities',
        'Life Support People',
        'Fuel',
        'Crew Salaries',
        'Total Expenses',
    ]
    assert my_ship.expenses.total == pytest.approx(my_ship.expenses.rows[-1].amount)


def test_expense_rows_include_expected_labels():
    my_ship = build_small_jump_ship()

    assert [row.label for row in my_ship.expenses.rows] == [
        'Production Cost',
        'Sales Price New',
        'Mortgage',
        'Maintenance',
        'Life Support Facilities',
        'Life Support People',
        'Fuel',
        'Crew Salaries',
        'Total Expenses',
    ]


def test_operation_fuel_contributes_monthly_unrefined_cost():
    my_ship = ship.Ship(
        tl=9,
        displacement=200,
        hull=hull.Hull(configuration=hull.close_structure.model_copy(update={'light': True})),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FusionPlantTL8(output=80)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=12)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=[Stateroom()]),
    )
    assert my_ship.expenses.fuel == pytest.approx(100.0)


def test_operation_fuel_cost_is_zero_with_scoops_and_no_jump_drive():
    my_ship = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FusionPlantTL12(output=80)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=[Stateroom()]),
    )
    assert my_ship.expenses.fuel == pytest.approx(0.0)


def test_jump_and_operation_fuel_use_unrefined_price_with_processor():
    my_ship = build_small_jump_ship()

    assert my_ship.fuel is not None
    assert my_ship.fuel.fuel_scoops is not None
    assert my_ship.fuel.fuel_processor is not None
    assert my_ship.expenses.fuel == pytest.approx(4_066.6666666667)


def test_jump_drive_still_requires_refined_fuel_without_processor():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=60)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=12),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(bis=True)),
        habitation=HabitationSection(staterooms=[Stateroom()] * 4),
    )

    assert my_ship.fuel is not None
    assert my_ship.fuel.fuel_scoops is not None
    assert my_ship.fuel.fuel_processor is None
    assert my_ship.expenses.fuel == pytest.approx(20_333.3333333333)
