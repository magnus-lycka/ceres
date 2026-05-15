"""90-ton, Streamlined, Non-Gravity, R-Drive runabout.

TL8, updated from the 100-ton non-gravity runabout note in
`refs/tycho/testcases.md`.
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.automation import LowAutomation
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, RDrive4, SolarPanelsTL8, SterlingFissionPlant
from ceres.make.ship.power import PowerSection
from ceres.make.ship.sensors import SensorsSection
from ceres.make.ship.software import Library, Manoeuvre
from ceres.make.ship.storage import FuelScoops, FuelSection, OperationFuel, ReactionFuel
from ceres.make.ship.systems import Airlock

_streamlined_non_gravity = hull.streamlined_hull.model_copy(update={'non_gravity': True})

_expected = SimpleNamespace(
    tl=8,
    displacement=90,
    hull_points=36,
    hull_cost_mcr=2.7,
    heat_shielding_cost_mcr=9.0,
    r_drive_tons=7.2,
    r_drive_cost_mcr=1.44,
    plant_tons=2.0,
    plant_cost_mcr=1.2,
    solar_tons=0.5,
    solar_cost_mcr=0.1,
    available_power=9.0,
    operation_fuel_tons=0.0,
    operation_fuel_item='15 Years of Operation',
    reaction_fuel_tons=54.0,
    bridge_tons=3.0,
    bridge_cost_mcr=0.25,
    airlock_tons=2.0,
    airlock_cost_mcr=0.2,
    automation_cost_mcr=-1.608,
    computer_cost_mcr=0.03,
    production_cost_mcr=13.312,
    maintenance_cr=1109,
    cargo_tons=21.3,
    power_basic=9,
    total_power=9.0,
    expected_errors=[],
    expected_warnings=[],
)


def build_90t_non_gravity_rdrive():
    return ship.Ship(
        tl=_expected.tl,
        displacement=_expected.displacement,
        ship_class='Non-Gravity Runabout',
        ship_type='Runabout',
        hull=hull.Hull(
            configuration=_streamlined_non_gravity,
            heat_shielding=True,
            airlocks=[Airlock()],
        ),
        drives=DriveSection(r_drive=RDrive4()),
        power=PowerSection(
            plant=SterlingFissionPlant(output=8),
            solar=[SolarPanelsTL8(tons=0.5)],
        ),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=52 * 15),
            reaction_fuel=ReactionFuel(minutes=360),
            fuel_scoops=FuelScoops(free=True),
        ),
        command=CommandSection(bridge=Bridge(small=True)),
        automation=LowAutomation(),
        computer=ComputerSection(
            hardware=Computer5(),
            software=[Library(), Manoeuvre()],
        ),
        sensors=SensorsSection(),
    )


def _build():
    return build_90t_non_gravity_rdrive()


def test_build_succeeds():
    s = _build()
    assert s is not None


def test_hull_points():
    assert _build().hull_points == _expected.hull_points


def test_displacement():
    assert _build().displacement == _expected.displacement


def test_hull_cost():
    assert _build().hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)


def test_heat_shielding_cost():
    assert _build().hull.heat_shielding_cost(_expected.displacement) == pytest.approx(
        _expected.heat_shielding_cost_mcr * 1_000_000
    )


def test_rdrive_tons_and_cost():
    s = _build()
    assert s.drives is not None
    assert s.drives.r_drive is not None
    assert s.drives.r_drive.tons == pytest.approx(_expected.r_drive_tons)
    assert s.drives.r_drive.cost == pytest.approx(_expected.r_drive_cost_mcr * 1_000_000)


def test_power_sources():
    s = _build()
    assert s.power is not None
    assert s.power.plant is not None
    assert s.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert s.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)
    assert s.power.solar[0].tons == pytest.approx(_expected.solar_tons)
    assert s.power.solar[0].cost == pytest.approx(_expected.solar_cost_mcr * 1_000_000)
    assert s.available_power == pytest.approx(_expected.available_power)


def test_operation_fuel_tons():
    s = _build()
    assert s.fuel is not None
    assert s.fuel.operation_fuel is not None
    assert s.fuel.operation_fuel.tons == pytest.approx(_expected.operation_fuel_tons)
    assert s.fuel.operation_fuel.build_item() == _expected.operation_fuel_item


def test_reaction_fuel_tons():
    s = _build()
    assert s.fuel is not None
    assert s.fuel.reaction_fuel is not None
    assert s.fuel.reaction_fuel.tons == pytest.approx(_expected.reaction_fuel_tons)


def test_bridge_tons():
    s = _build()
    assert s.command is not None
    assert s.command.bridge is not None
    assert s.command.bridge.tons == pytest.approx(_expected.bridge_tons)


def test_bridge_cost():
    s = _build()
    assert s.command is not None
    assert s.command.bridge is not None
    assert s.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)


def test_airlock():
    s = _build()
    assert s.hull.airlocks[0].tons == pytest.approx(_expected.airlock_tons)
    assert s.hull.airlocks[0].cost == pytest.approx(_expected.airlock_cost_mcr * 1_000_000)


def test_automation_cost():
    s = _build()
    assert s.automation is not None
    assert s.automation.cost == pytest.approx(_expected.automation_cost_mcr * 1_000_000)


def test_computer_cost():
    s = _build()
    assert s.computer is not None
    assert s.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)


def test_total_production_cost():
    s = _build()
    assert s.expenses.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000, rel=1e-4)


def test_maintenance_cost():
    s = _build()
    assert s.expenses.maintenance == pytest.approx(_expected.maintenance_cr)


def test_cargo_tons():
    s = _build()
    assert s.remaining_usable_tonnage() == pytest.approx(_expected.cargo_tons)


def test_basic_ship_power_load():
    s = _build()
    assert s.basic_hull_power_load == _expected.power_basic
    assert s.total_power_load == pytest.approx(_expected.total_power)
    assert s.notes.errors == _expected.expected_errors
    assert s.notes.warnings == _expected.expected_warnings
