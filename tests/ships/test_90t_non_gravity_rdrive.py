"""
90-ton, Streamlined, Non-Gravity, R-Drive runabout.

TL 8, updated from the 100-ton non-gravity runabout note in
refs/tycho/testcases.md.
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.automation import LowAutomation
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, ImprovedSolarPanels, RDrive4, SterlingFissionPlant
from ceres.make.ship.power import PowerSection
from ceres.make.ship.sensors import SensorsSection
from ceres.make.ship.software import Library, Manoeuvre
from ceres.make.ship.storage import FuelScoops, FuelSection, OperationFuel, ReactionFuel

_streamlined_non_gravity = hull.streamlined_hull.model_copy(update={'non_gravity': True})


def build_90t_non_gravity_rdrive():
    return ship.Ship(
        tl=8,
        displacement=90,
        ship_class='Non-Gravity Runabout',
        ship_type='Runabout',
        hull=hull.Hull(
            configuration=_streamlined_non_gravity,
            heat_shielding=True,
        ),
        drives=DriveSection(r_drive=RDrive4()),
        power=PowerSection(
            plant=SterlingFissionPlant(output=8),
            solar=[ImprovedSolarPanels(units=2)],
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
    assert _build().hull_points == 36


def test_displacement():
    assert _build().displacement == 90


def test_hull_cost():
    # Streamlined (1.2x) x non-gravity (0.5x) x base: 50000 x 90 x 0.6 = 2.7 MCr
    assert _build().hull_cost == pytest.approx(2_700_000)


def test_heat_shielding_cost():
    # MCr0.1 per ton of hull = MCr9
    assert _build().hull.heat_shielding_cost(90) == pytest.approx(9_000_000)


def test_rdrive_tons_and_cost():
    s = _build()
    assert s.drives is not None
    assert s.drives.r_drive is not None
    assert s.drives.r_drive.tons == pytest.approx(7.2)
    assert s.drives.r_drive.cost == pytest.approx(1_440_000)


def test_power_sources():
    s = _build()
    assert s.power is not None
    assert s.power.plant is not None
    assert s.power.plant.tons == pytest.approx(2.0)
    assert s.power.plant.cost == pytest.approx(1_200_000)
    assert s.power.solar[0].tons == pytest.approx(2.0)
    assert s.power.solar[0].cost == pytest.approx(400_000)
    assert s.available_power == pytest.approx(9.0)


def test_operation_fuel_tons():
    s = _build()
    assert s.fuel is not None
    assert s.fuel.operation_fuel is not None
    assert s.fuel.operation_fuel.tons == pytest.approx(0.0)
    assert s.fuel.operation_fuel.build_item() == '15 Years of Operation'


def test_reaction_fuel_tons():
    s = _build()
    assert s.fuel is not None
    assert s.fuel.reaction_fuel is not None
    assert s.fuel.reaction_fuel.tons == pytest.approx(54.0)


def test_bridge_tons():
    s = _build()
    assert s.command is not None
    assert s.command.bridge is not None
    assert s.command.bridge.tons == pytest.approx(3.0)


def test_bridge_cost():
    s = _build()
    assert s.command is not None
    assert s.command.bridge is not None
    assert s.command.bridge.cost == pytest.approx(250_000)


def test_automation_cost():
    # Basis: hull-config cost (streamlined, no non-gravity) + R-drive + plant = MCr5.4 + MCr1.44 + MCr1.2.
    s = _build()
    assert s.automation is not None
    assert s.automation.cost == pytest.approx(-1_608_000)


def test_computer_cost():
    s = _build()
    assert s.computer is not None
    assert s.computer.hardware.cost == pytest.approx(30_000)


def test_total_production_cost():
    s = _build()
    assert s.expenses.production_cost == pytest.approx(13_412_000, rel=1e-4)


def test_maintenance_cost():
    s = _build()
    assert s.expenses.maintenance == pytest.approx(1118)


def test_cargo_tons():
    s = _build()
    assert s.remaining_usable_tonnage() == pytest.approx(21.8)


def test_basic_ship_power_load():
    s = _build()
    assert s.basic_hull_power_load == 9
    assert s.total_power_load == pytest.approx(9.0)
