import pytest

from ceres import hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import Computer5, ComputerSection
from ceres.drives import DriveSection, FusionPlantTL8, FusionPlantTL12, JumpDrive2, MDrive1, MDrive2, PowerSection
from ceres.expense import expense_rows, fuel_cost, life_support_cost, maintenance_cost, mortgage_cost, production_cost
from ceres.habitation import HabitationSection, Staterooms
from ceres.storage import FuelProcessor, FuelSection, JumpFuel, OperationFuel


def build_small_jump_ship() -> ship.Ship:
    return ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive2(), jump_drive=JumpDrive2()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=60)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(bis=True)),
        habitation=HabitationSection(staterooms=Staterooms(count=4)),
    )


def test_production_cost_matches_ship_property():
    my_ship = build_small_jump_ship()

    assert production_cost(my_ship) == pytest.approx(my_ship.production_cost)


def test_operating_expense_components_match_ship_helpers():
    my_ship = build_small_jump_ship()

    assert mortgage_cost(my_ship) == pytest.approx(my_ship._mortgage_cost())
    assert maintenance_cost(my_ship) == pytest.approx(my_ship._maintenance_cost())
    assert life_support_cost(my_ship) == pytest.approx(my_ship._life_support_cost())
    assert fuel_cost(my_ship) == pytest.approx(my_ship._fuel_cost())


def test_expense_rows_include_expected_labels():
    my_ship = build_small_jump_ship()

    assert [row.label for row in expense_rows(my_ship)] == [
        'Production Cost',
        'Sales Price New',
        'Mortgage',
        'Maintenance',
        'Life Support',
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
        power=PowerSection(fusion_plant=FusionPlantTL8(output=80)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=12)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=Staterooms(count=1)),
    )
    assert fuel_cost(my_ship) == pytest.approx(80.0)
