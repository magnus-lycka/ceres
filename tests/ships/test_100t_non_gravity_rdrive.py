"""
100-ton, Streamlined, Non-Gravity, R-Drive runabout.

TL 8, no power plant. Derived from a published stat block.

Key design points:
- Non-gravity hull (–50% hull cost)
- Heat Shielding (MCr0.1/ton)
- R-Drive Thrust 4 (no Power required)
- Low Automation (–20% of hull-config + R-drive basis)
- Small Bridge

Total cost MCr13.36, Maintenance Cr1,113/month.
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.automation import LowAutomation
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, RDrive4
from ceres.make.ship.sensors import SensorsSection
from ceres.make.ship.software import Library, Manoeuvre
from ceres.make.ship.storage import FuelSection, ReactionFuel

_streamlined_non_gravity = hull.streamlined_hull.model_copy(update={'non_gravity': True})


def build_100t_non_gravity_rdrive():
    return ship.Ship(
        tl=8,
        displacement=100,
        ship_class='Non-Gravity Runabout',
        ship_type='Runabout',
        hull=hull.Hull(
            configuration=_streamlined_non_gravity,
            heat_shielding=True,
        ),
        drives=DriveSection(r_drive=RDrive4()),
        fuel=FuelSection(reaction_fuel=ReactionFuel(minutes=360)),
        command=CommandSection(bridge=Bridge(small=True)),
        automation=LowAutomation(),
        computer=ComputerSection(
            hardware=Computer5(),
            software=[Library(), Manoeuvre()],
        ),
        sensors=SensorsSection(),
    )


def _build():
    return build_100t_non_gravity_rdrive()


def test_build_succeeds():
    s = _build()
    assert s is not None


def test_hull_points():
    assert _build().hull_points == 40


def test_displacement():
    assert _build().displacement == 100


def test_hull_cost():
    # Streamlined (1.2×) × non-gravity (0.5×) × base: 50000 × 100 × 0.6 = 3 MCr
    assert _build().hull_cost == pytest.approx(3_000_000)


def test_heat_shielding_cost():
    # MCr0.1 per ton of hull = MCr10
    assert _build().hull.heat_shielding_cost(100) == pytest.approx(10_000_000)


def test_rdrive_tons():
    s = _build()
    assert s.drives is not None
    assert s.drives.r_drive is not None
    assert s.drives.r_drive.tons == pytest.approx(8.0)  # 100 × 0.08


def test_reaction_fuel_tons():
    s = _build()
    assert s.fuel is not None
    assert s.fuel.reaction_fuel is not None
    assert s.fuel.reaction_fuel.tons == pytest.approx(60.0)  # 6h × 10 t/h


def test_bridge_tons():
    s = _build()
    assert s.command is not None
    assert s.command.bridge is not None
    assert s.command.bridge.tons == pytest.approx(6.0)


def test_bridge_cost():
    s = _build()
    assert s.command is not None
    assert s.command.bridge is not None
    assert s.command.bridge.cost == pytest.approx(250_000)


def test_automation_cost():
    # Basis: hull-config cost (streamlined, no non-gravity) + R-drive = MCr6 + MCr1.6 = MCr7.6
    # Low automation: –20% × MCr7.6 = –MCr1.52
    s = _build()
    assert s.automation is not None
    assert s.automation.cost == pytest.approx(-1_520_000)


def test_computer_cost():
    s = _build()
    assert s.computer is not None
    assert s.computer.hardware.cost == pytest.approx(30_000)


def test_total_production_cost():
    # Hull: 3 + Heat Shielding: 10 + R-Drive: 1.6 + Bridge: 0.25
    # + Automation: –1.52 + Computer: 0.03 = MCr13.36
    s = _build()
    assert s.expenses.production_cost == pytest.approx(13_360_000, rel=1e-4)


def test_maintenance_cost():
    # production_cost / 12000 = 13_360_000 / 12_000 = 1113.33 → round = 1113
    s = _build()
    assert s.expenses.maintenance == pytest.approx(1113)


def test_cargo_tons():
    # Remaining space after R-drive (8) + fuel (60) + bridge (6) = 26 tons cargo
    s = _build()
    assert s.remaining_usable_tonnage() == pytest.approx(26.0)
