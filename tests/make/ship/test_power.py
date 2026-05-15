from pydantic import ValidationError
import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.drives import DriveSection, MDrive1
from ceres.make.ship.power import (
    AdvancedSolarCoating,
    AntimatterPlant,
    ChemicalPlant,
    EnhancedSolarCoating,
    FissionPlant,
    FusionPlantTL8,
    HighEfficiencyBatteriesTL10,
    HighEfficiencyBatteriesTL12,
    PowerSection,
    SolarPanelsTL6,
    SolarPanelsTL8,
    SolarPanelsTL12,
    SterlingFissionPlant,
    SterlingFissionPlantTL6,
    SterlingFissionPlantTL12,
)
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


# --- Other power plants ---


def test_tl8_sterling_fission_plant_tons_cost_and_lifespan():
    p = SterlingFissionPlant(output=8)
    assert p.tons == pytest.approx(2.0)
    assert p.cost == pytest.approx(1_200_000)
    assert p.lifespan_years == 15


def test_sterling_fission_plant_tl6_values():
    p = SterlingFissionPlantTL6(output=6)
    assert p.tons == pytest.approx(2.0)
    assert p.cost == pytest.approx(800_000)
    assert p.lifespan_years == 10


def test_sterling_fission_plant_tl12_values():
    p = SterlingFissionPlantTL12(output=12)
    assert p.tons == pytest.approx(2.0)
    assert p.cost == pytest.approx(1_600_000)
    assert p.lifespan_years == 20


def test_sterling_fission_plant_minimum_size():
    p = SterlingFissionPlant(output=4)
    assert p.tons == pytest.approx(2.0)
    assert p.cost == pytest.approx(1_200_000)


def test_sterling_fission_plant_has_no_operation_fuel():
    p = SterlingFissionPlant(output=8)
    assert p.fuel_for_weeks(52 * 15) == 0.0


def test_sterling_fission_plant_loses_power_after_lifespan():
    p = SterlingFissionPlant(output=8)
    assert p.power_per_ton_at_age(15) == 4
    assert p.power_per_ton_at_age(17) == 2
    assert p.output_at_age(17) == pytest.approx(4.0)


def test_sterling_fission_plant_build_item():
    p = SterlingFissionPlant(output=8)
    assert p.build_item() == 'Sterling Fission (TL 8), Power 8'


def test_sterling_fission_plant_warns_when_jump_drive_installed():
    from ceres.make.ship.drives import DriveSection, JDrive1

    my_ship = ship.Ship(
        tl=9,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(j_drive=JDrive1()),
        power=PowerSection(plant=SterlingFissionPlant(output=20)),
    )
    assert my_ship.power is not None
    assert my_ship.power.plant is not None
    assert 'Sterling fission power plants cannot directly operate jump drives' in my_ship.power.plant.notes.warnings


def test_antimatter_plant_tons_and_cost():
    p = AntimatterPlant(output=100)
    assert p.tons == pytest.approx(1.0)
    assert p.cost == pytest.approx(10_000_000)


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


# --- Solar energy systems ---


def test_tl8_solar_panels_tons_cost_and_output():
    panels = SolarPanelsTL8(tons=0.5)
    assert panels.tons == pytest.approx(0.5)
    assert panels.cost == pytest.approx(100_000)
    assert panels.output == pytest.approx(1.0)
    assert panels.power == 0.0
    assert panels.build_item() == 'Solar Panels (TL 8), Power 1'


def test_solar_panel_table_values():
    assert SolarPanelsTL6(tons=1).output == pytest.approx(1.0)
    assert SolarPanelsTL6(tons=1).cost == pytest.approx(100_000)
    assert SolarPanelsTL8(tons=1).output == pytest.approx(2.0)
    assert SolarPanelsTL8(tons=1).cost == pytest.approx(200_000)
    assert SolarPanelsTL12(tons=1).output == pytest.approx(3.0)
    assert SolarPanelsTL12(tons=1).cost == pytest.approx(400_000)


def test_solar_panels_minimum_size():
    with pytest.raises(ValidationError):
        SolarPanelsTL8(tons=0.49)


def test_solar_panel_notes_capture_deployment_and_use_limits():
    my_ship = ship.Ship(
        tl=8,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(solar=[SolarPanelsTL8(tons=0.5)]),
    )
    assert my_ship.power is not None
    panels = my_ship.power.solar[0]
    assert 'Ships cannot jump with solar panels deployed' in panels.notes.infos
    assert 'Ships cannot manoeuvre above Thrust 1 with solar panels deployed' in panels.notes.infos


def test_solar_coating_has_no_tonnage():
    coating = EnhancedSolarCoating(units=10)
    assert coating.tons == 0.0
    assert coating.cost == pytest.approx(3_000_000)
    assert coating.output == pytest.approx(1.0)


def test_solar_coating_close_structure_halves_output():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.close_structure),
        power=PowerSection(solar=[AdvancedSolarCoating(units=10)]),
    )
    assert my_ship.power is not None
    coating = my_ship.power.solar[0]
    assert coating.output == pytest.approx(1.0)


def test_solar_coating_rejects_streamlined_hulls():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        power=PowerSection(solar=[EnhancedSolarCoating(units=10)]),
    )
    assert my_ship.power is not None
    coating = my_ship.power.solar[0]
    assert 'Solar coating cannot be applied to streamlined hulls' in coating.notes.errors


def test_solar_coating_rejects_more_than_forty_percent_coverage():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(solar=[EnhancedSolarCoating(units=41)]),
    )
    assert my_ship.power is not None
    coating = my_ship.power.solar[0]
    assert 'Solar coating exceeds 40% hull coverage: 41 > 40' in coating.notes.errors


def test_power_section_output_sums_plant_and_solar():
    ps = PowerSection(plant=FissionPlant(output=8), solar=[SolarPanelsTL8(tons=0.5)])
    assert ps.output == pytest.approx(9.0)


def test_ship_available_power_includes_solar():
    s = ship.Ship(
        tl=8,
        displacement=90,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(plant=SterlingFissionPlant(output=8), solar=[SolarPanelsTL8(tons=0.5)]),
    )
    assert s.available_power == pytest.approx(9.0)


# --- High-efficiency batteries ---


def test_tl10_high_efficiency_batteries_tons_cost_and_power():
    batteries = HighEfficiencyBatteriesTL10(stored_power=40)
    assert batteries.tons == pytest.approx(1.0)
    assert batteries.cost == pytest.approx(100_000)
    assert batteries.power == 0.0
    assert batteries.build_item() == 'High-Efficiency Batteries (TL 10), Power 40'


def test_tl12_high_efficiency_batteries_tons_cost_and_power():
    batteries = HighEfficiencyBatteriesTL12(stored_power=180)
    assert batteries.tons == pytest.approx(3.0)
    assert batteries.cost == pytest.approx(600_000)
    assert batteries.power == 0.0
    assert batteries.build_item() == 'High-Efficiency Batteries (TL 12), Power 180'


def test_high_efficiency_batteries_do_not_increase_continuous_available_power():
    s = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(plant=FissionPlant(output=8), batteries=[HighEfficiencyBatteriesTL12(stored_power=60)]),
    )
    assert s.available_power == pytest.approx(8.0)


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


def test_operation_fuel_with_sterling_fission_plant_has_no_tonnage():
    my_ship = ship.Ship(
        tl=8,
        displacement=90,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(plant=SterlingFissionPlant(output=8)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=52 * 15)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.operation_fuel is not None
    assert my_ship.fuel.operation_fuel.tons == 0.0
    assert my_ship.fuel.operation_fuel.build_item() == '15 Years of Operation'
