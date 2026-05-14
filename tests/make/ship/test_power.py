import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.drives import DriveSection, MDrive1
from ceres.make.ship.power import ChemicalPlant, FissionPlant, FusionPlantTL8, PowerSection
from ceres.make.ship.storage import FuelSection, OperationFuel

# --- FissionPlant ---


def test_fission_plant_tons():
    p = FissionPlant(output=80)
    assert p.tons == pytest.approx(10.0)  # 80 / 8


def test_fission_plant_cost():
    p = FissionPlant(output=80)
    assert p.cost == pytest.approx(4_000_000.0)  # 10 tons * MCr0.4/ton


def test_fission_plant_power_output_zero():
    p = FissionPlant(output=80)
    assert p.power == 0.0


def test_fission_plant_build_item():
    p = FissionPlant(output=80)
    p2 = FissionPlant(output=80, tl=7)
    assert p.build_item() == 'Fission Plant (TL 6), Power 80'
    assert p2.build_item() == 'Fission Plant (TL 7), Power 80'


def test_fission_plant_fuel_for_weeks_matches_fusion_rule():
    p = FissionPlant(output=80)
    # Same rule as fusion: 10% of plant tons per 4 weeks
    assert p.fuel_for_weeks(4) == pytest.approx(0.10 * p.tons)


def test_fission_plant_fuel_period_weeks():
    assert FissionPlant(output=80).fuel_period_weeks == 4


# --- ChemicalPlant ---


def test_chemical_plant_tons():
    p = ChemicalPlant(output=50)
    assert p.tons == pytest.approx(10.0)  # 50 / 5


def test_chemical_plant_cost():
    p = ChemicalPlant(output=50)
    assert p.cost == pytest.approx(2_500_000.0)  # 10 tons * MCr0.25/ton


def test_chemical_plant_power_output_zero():
    p = ChemicalPlant(output=50)
    assert p.power == 0.0


def test_chemical_plant_build_item():
    p = ChemicalPlant(output=50)
    assert p.build_item() == 'Chemical Plant (TL 7), Power 50'


def test_chemical_plant_fuel_for_weeks():
    p = ChemicalPlant(output=50)
    # 10 tons fuel per ton of plant per 2 weeks
    # plant is 10 tons, so for 2 weeks: 10 * 10 = 100 tons
    assert p.fuel_for_weeks(2) == pytest.approx(100.0)
    assert p.fuel_for_weeks(4) == pytest.approx(200.0)


def test_chemical_plant_fuel_period_weeks():
    assert ChemicalPlant(output=50).fuel_period_weeks == 2


def test_chemical_plant_fuel_much_higher_than_fusion():
    fusion = FusionPlantTL8(output=50)
    chemical = ChemicalPlant(output=50)
    # Chemical needs 10 tons/ton/2wks vs fusion 10%/ton/4wks
    assert chemical.fuel_for_weeks(4) > fusion.fuel_for_weeks(4) * 100


# --- PowerSection with non-fusion plants ---


def test_power_section_accepts_fission_plant():
    ps = PowerSection(plant=FissionPlant(output=40))
    assert ps.plant is not None
    assert ps.plant.output == 40


def test_power_section_accepts_chemical_plant():
    ps = PowerSection(plant=ChemicalPlant(output=20))
    assert ps.plant is not None
    assert ps.plant.output == 20


def test_ship_with_fission_plant():
    s = ship.Ship(
        tl=6,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FissionPlant(output=20)),
    )
    assert s.power is not None
    assert s.available_power == 20


# --- OperationFuel with non-fusion plant ---


def test_operation_fuel_with_fission_plant():
    my_ship = ship.Ship(
        tl=6,
        displacement=50,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(plant=FissionPlant(output=8)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=4)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.operation_fuel is not None
    plant = FissionPlant(output=8)
    # plant.tons = 1.0, fuel_for_weeks(4) = 0.10 * 1.0 = 0.10 tons (same rule as fusion)
    assert my_ship.fuel.operation_fuel.tons == pytest.approx(plant.fuel_for_weeks(4))


def test_operation_fuel_with_chemical_plant():
    my_ship = ship.Ship(
        tl=7,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(plant=ChemicalPlant(output=10)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=2)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.operation_fuel is not None
    plant = ChemicalPlant(output=10)
    # 2 weeks: 10 * plant_tons (2 tons) * 2 / 2 = 20 tons
    assert my_ship.fuel.operation_fuel.tons == pytest.approx(plant.fuel_for_weeks(2))


def test_operation_fuel_actual_weeks_chemical_rounds_to_two_week_periods():
    # Chemical baseline is 2-week periods, not 4-week
    plant = ChemicalPlant(output=10)
    # plant.tons = 2, baseline (2 weeks) = 10 * 2 * 2/2 = 20 tons
    # If we allocate exactly 1 baseline (20 tons), actual_weeks should be 2
    my_ship = ship.Ship(
        tl=7,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(plant=plant),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=2)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.operation_fuel is not None
    assert my_ship.fuel.operation_fuel.actual_weeks == 2
