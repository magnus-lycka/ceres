"""Reference ship case: Civilian Hopper.

Source: Small Craft Catalogue (official publication).

Purpose:
- exercise 6-ton close-structure hull with Fission plant and acceleration seats
- confirm Basic Ship Systems power = 2 per RIS-013 (ceil(6 * 0.2) = 2)
- confirm AccelerationSeat and TowCable tonnage and cost

Source handling:
- supported: hull, m-drive, fission power plant, operation fuel, cockpit,
  computer, basic sensors, tow cable, acceleration seats, maintenance cost,
  purchase cost, and single-pilot crew
- design_type is CUSTOM (no multiplier)

Known deviations from stat block:
- power_basic: stat block shows 2; Ceres gives 2 per RIS-013 (agrees)
- cargo: stat block shows 2.5 tons; Ceres remaining_usable_tonnage gives
  2.78 tons (0.28 ton discrepancy). Same systematic gap as the Freight
  Handler Pod — root cause not identified. Cargo is not asserted against
  the stat block value.
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Cockpit, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FissionPlant, MDrive1, PowerSection
from ceres.make.ship.storage import FuelSection, OperationFuel
from ceres.make.ship.systems import AccelerationSeat, SystemsSection, TowCable

_expected = SimpleNamespace(
    tl=9,
    displacement=6,
    hull_cost_mcr=0.24,  # 6 * 50_000 * 0.8
    m_drive_tons=0.06,  # 6 * 0.01
    m_drive_cost_mcr=0.12,  # 0.06 * 2_000_000
    plant_tons=0.5,  # 4 / 8
    plant_cost_mcr=0.2,  # 0.5 * 400_000
    fuel_weeks=8,
    cockpit_tons=1.5,
    cockpit_cost_mcr=0.01,
    computer_cost_mcr=0.03,
    tow_cable_tons=0.06,  # 6 * 0.01
    tow_cable_count=1,
    tow_cable_cost_mcr=0.0003,  # 6 * 0.01 * 5_000
    acceleration_seat_count=2,
    acceleration_seat_tons=0.5,
    acceleration_seat_cost_mcr=0.03,  # Cr30_000
    available_power=4,
    power_basic=2,  # stat block; agrees with ceil(6 * 0.2) = 2, RIS-013
    power_maneuver=1,  # ceil(0.1 * 6 * 1) = 1
    power_sensors=0,
    total_power=3,  # 2 + 1 + 0
    expected_errors=[],
    expected_warnings=[],
)


def build_civilian_hopper() -> ship.Ship:
    return ship.Ship(
        ship_class='Civilian Hopper',
        ship_type='Hopper',
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
            internal_systems=[TowCable(), AccelerationSeat(), AccelerationSeat()],
        ),
    )


def _build() -> ship.Ship:
    return build_civilian_hopper()


def test_civilian_hopper_hull():
    hopper = _build()
    assert hopper.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)


def test_civilian_hopper_m_drive():
    hopper = _build()
    assert hopper.drives is not None
    assert hopper.drives.m_drive is not None
    assert hopper.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert hopper.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)


def test_civilian_hopper_fission_plant():
    hopper = _build()
    assert hopper.power is not None
    assert hopper.power.plant is not None
    assert hopper.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert hopper.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)


def test_civilian_hopper_tow_cable():
    hopper = _build()
    assert hopper.systems is not None
    tow_cables = [s for s in hopper.systems.internal_systems if isinstance(s, TowCable)]
    assert len(tow_cables) == _expected.tow_cable_count
    assert tow_cables[0].tons == pytest.approx(_expected.tow_cable_tons)
    assert tow_cables[0].cost == pytest.approx(_expected.tow_cable_cost_mcr * 1_000_000)


def test_civilian_hopper_acceleration_seats():
    hopper = _build()
    assert hopper.systems is not None
    seats = [s for s in hopper.systems.internal_systems if isinstance(s, AccelerationSeat)]
    assert len(seats) == _expected.acceleration_seat_count
    for seat in seats:
        assert seat.tons == pytest.approx(_expected.acceleration_seat_tons)
        assert seat.cost == pytest.approx(_expected.acceleration_seat_cost_mcr * 1_000_000)


def test_civilian_hopper_power():
    hopper = _build()
    assert hopper.available_power == pytest.approx(_expected.available_power)
    assert hopper.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert hopper.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert hopper.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert hopper.total_power_load == pytest.approx(_expected.total_power)
    assert hopper.notes.errors == _expected.expected_errors
    assert hopper.notes.warnings == _expected.expected_warnings
