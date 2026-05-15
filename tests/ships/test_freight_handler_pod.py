"""Reference ship case: Freight Handler Pod.

Source: Small Craft Catalogue (official publication).

Purpose:
- exercise 6-ton close-structure hull with Fission plant and small-craft systems
- confirm Basic Ship Systems power = 2 per RIS-013 (ceil(6 * 0.2) = 2)
- confirm TowCable and GrapplingArm tonnage and cost

Source handling:
- supported: hull, m-drive, fission power plant, operation fuel, cockpit,
  computer, basic sensors, tow cable, grappling arm, maintenance cost,
  purchase cost, and single-pilot crew
- design_type is CUSTOM (no multiplier)

Known deviations from stat block:
- power_basic: stat block shows 2; Ceres gives 2 per RIS-013 (agrees)
- cargo: stat block shows 1.5 tons; Ceres remaining_usable_tonnage gives
  1.78 tons (0.28 ton discrepancy). Root cause not identified — possibly
  a standard small-craft overhead in the SCC design tool not modelled by
  Ceres. Cargo is not asserted against the stat block value.
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Cockpit, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FissionPlant, MDrive1, PowerSection
from ceres.make.ship.storage import FuelSection, OperationFuel
from ceres.make.ship.systems import GrapplingArm, SystemsSection, TowCable

_expected = SimpleNamespace(
    tl=9,
    displacement=6,
    hull_cost_mcr=0.24,  # 6 * 50_000 * 0.8
    m_drive_tons=0.06,  # 6 * 0.01
    m_drive_cost_mcr=0.12,  # 0.06 * 2_000_000
    plant_tons=0.5,  # 4 / 8
    plant_cost_mcr=0.2,  # 0.5 * 400_000
    fuel_weeks=1,
    cockpit_tons=1.5,
    cockpit_cost_mcr=0.01,
    computer_cost_mcr=0.03,
    tow_cable_tons=0.06,  # 6 * 0.01
    tow_cable_cost_mcr=0.0003,  # 6 * 0.01 * 5_000
    grappling_arm_tons=2.0,
    grappling_arm_cost_mcr=1.0,
    available_power=4,
    power_basic=2,  # stat block; agrees with ceil(6 * 0.2) = 2, RIS-013
    power_maneuver=1,  # ceil(0.1 * 6 * 1) = 1
    power_sensors=0,
    total_power=3,  # 2 + 1 + 0
    production_cost_mcr=1.6003,
    maintenance_cr=133,
)


def build_freight_handler_pod() -> ship.Ship:
    return ship.Ship(
        ship_class='Freight Handler Pod',
        ship_type='Freight Handler',
        tl=_expected.tl,
        displacement=_expected.displacement,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(configuration=hull.close_structure),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FissionPlant(output=4)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=_expected.fuel_weeks)),
        command=CommandSection(cockpit=Cockpit()),
        computer=ComputerSection(hardware=Computer5()),
        systems=SystemsSection(
            internal_systems=[TowCable(), GrapplingArm()],
        ),
    )


def _build() -> ship.Ship:
    return build_freight_handler_pod()


def test_freight_handler_pod_hull():
    pod = _build()
    assert pod.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)


def test_freight_handler_pod_m_drive():
    pod = _build()
    assert pod.drives is not None
    assert pod.drives.m_drive is not None
    assert pod.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert pod.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)


def test_freight_handler_pod_fission_plant():
    pod = _build()
    assert pod.power is not None
    assert pod.power.plant is not None
    assert pod.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert pod.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)


def test_freight_handler_pod_tow_cable():
    pod = _build()
    assert pod.systems is not None
    tow_cables = [s for s in pod.systems.internal_systems if isinstance(s, TowCable)]
    assert len(tow_cables) == 1
    assert tow_cables[0].tons == pytest.approx(_expected.tow_cable_tons)
    assert tow_cables[0].cost == pytest.approx(_expected.tow_cable_cost_mcr * 1_000_000)


def test_freight_handler_pod_grappling_arm():
    pod = _build()
    assert pod.systems is not None
    arms = [s for s in pod.systems.internal_systems if isinstance(s, GrapplingArm)]
    assert len(arms) == 1
    assert arms[0].tons == pytest.approx(_expected.grappling_arm_tons)
    assert arms[0].cost == pytest.approx(_expected.grappling_arm_cost_mcr * 1_000_000)


def test_freight_handler_pod_power():
    pod = _build()
    assert pod.available_power == pytest.approx(_expected.available_power)
    assert pod.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert pod.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert pod.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert pod.total_power_load == pytest.approx(_expected.total_power)


def test_freight_handler_pod_production_cost():
    pod = _build()
    assert pod.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)


def test_freight_handler_pod_maintenance():
    pod = _build()
    assert pod.expenses.maintenance == pytest.approx(_expected.maintenance_cr)


def test_freight_handler_pod_has_no_errors():
    pod = _build()
    assert not pod.notes.errors
