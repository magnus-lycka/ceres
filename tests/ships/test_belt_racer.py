"""Reference ship case based on refs/belt_racer.

Purpose:
- provide a minimal reaction-drive racing craft reference case
- exercise close-structure light hulls, reaction fuel, cockpit command, and
  cockpit-style zero life-support costs
- keep one compact source-derived example that is currently in near-complete
  agreement with the reference sheet

Source handling for this test case:
- supported: hull, reaction drive, power plant, reaction fuel, cockpit,
  computer, basic sensors, software, maintenance cost, purchase cost, and
  single-pilot crew
- source limitation:
  - the source sheet does not provide a settled class name beyond `Vargr Belt
    Racer, class name ???`, so the test uses `Vargr Belt Racer` as the ship
    class
- deliberate deviations:
  - power_basic: Tycho stat block shows 1; Ceres gives 2 per RIS-013
    (ceil(6 * 0.2) = 2; Tycho appears to use floor)
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Cockpit, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import (
    DriveSection,
    FusionPlantTL8,
    PowerSection,
    RDrive16,
)
from ceres.make.ship.storage import CargoSection, FuelSection, ReactionFuel

_expected = SimpleNamespace(
    tl=12,
    displacement=6,
    hull_cost_mcr=0.18,
    r_drive_tons=1.92,
    r_drive_cost_mcr=0.384,
    plant_tons=0.5,
    plant_cost_mcr=0.25,
    fuel_label='52 minutes of operation',
    fuel_tons=2.08,
    cockpit_tons=1.5,
    cockpit_cost_mcr=0.01,
    computer_cost_mcr=0.03,
    available_power=5.0,
    power_basic=1,  # Tycho stat block
    power_maneuver=0.0,
    power_sensors=0,
    total_power=1,  # Tycho stat block
    cargo_tons=0.0,
    production_cost_mcr=0.854,
    maintenance_cr=71,
    crew=[('PILOT', 1, 6_000)],
    expected_errors=[],
    expected_warnings=[],
)
# Tycho tool uses floor; ceil(6 * 0.2) = 2 per RIS-013
_expected.power_basic = 2
_expected.total_power = 2

BELT_RACER_HULL = hull.close_structure.model_copy(
    update={'light': True, 'description': 'Light Close Structure Hull'},
)


def build_belt_racer() -> ship.Ship:
    """Build the Belt Racer reference case from refs/belt_racer."""
    return ship.Ship(
        ship_class='Vargr Belt Racer',
        ship_type='Racer',
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=BELT_RACER_HULL),
        drives=DriveSection(r_drive=RDrive16()),
        power=PowerSection(plant=FusionPlantTL8(output=5)),
        fuel=FuelSection(reaction_fuel=ReactionFuel(minutes=52)),
        command=CommandSection(cockpit=Cockpit()),
        computer=ComputerSection(hardware=Computer5()),
    )


def test_belt_racer_matches_current_r_drive_subset():
    racer = build_belt_racer()

    assert racer.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert racer.drives is not None
    assert racer.drives.r_drive is not None
    assert racer.drives.r_drive.tons == pytest.approx(_expected.r_drive_tons)
    assert racer.drives.r_drive.cost == pytest.approx(_expected.r_drive_cost_mcr * 1_000_000)

    assert racer.power is not None
    assert racer.power.plant is not None
    assert racer.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert racer.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)

    assert racer.fuel is not None
    assert racer.fuel.reaction_fuel is not None
    assert racer.fuel.reaction_fuel.build_item() == _expected.fuel_label
    assert racer.fuel.reaction_fuel.tons == pytest.approx(_expected.fuel_tons)

    assert racer.command is not None
    assert racer.command.cockpit is not None
    assert racer.command.cockpit.tons == pytest.approx(_expected.cockpit_tons)
    assert racer.command.cockpit.cost == pytest.approx(_expected.cockpit_cost_mcr * 1_000_000)

    assert racer.computer is not None
    assert racer.computer.hardware is not None
    assert racer.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)

    assert racer.available_power == pytest.approx(_expected.available_power)
    assert racer.basic_hull_power_load == _expected.power_basic
    assert racer.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert racer.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert racer.total_power_load == pytest.approx(_expected.total_power)
    assert CargoSection.cargo_tons_for_ship(racer) == pytest.approx(_expected.cargo_tons)
    assert racer.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert racer.sales_price_new == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert racer.expenses.maintenance == pytest.approx(_expected.maintenance_cr)
    assert racer.notes.errors == _expected.expected_errors
    assert racer.notes.warnings == _expected.expected_warnings
    assert [(role.role, quantity, role.monthly_salary) for role, quantity in racer.crew.grouped_roles] == _expected.crew


def test_belt_racer_has_no_errors():
    racer = build_belt_racer()
    assert racer.notes.errors == _expected.expected_errors
    assert racer.notes.warnings == _expected.expected_warnings
