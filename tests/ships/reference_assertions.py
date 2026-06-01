from types import SimpleNamespace

import pytest

from ceres.make.ship.crafts import FullHangar, InternalDockingSpace
from ceres.make.ship.ship import Ship
from ceres.make.ship.storage import CargoSection


def assert_laboratory_station_matches_reference(station: Ship, expected: SimpleNamespace) -> None:
    assert station.tl == expected.tl
    assert station.displacement == expected.displacement
    assert station.hull_cost == pytest.approx(expected.hull_cost_mcr * 1_000_000)
    assert station.hull_points == pytest.approx(expected.hull_points)

    assert station.drives is not None
    assert station.drives.m_drive is not None
    assert station.drives.m_drive.tons == pytest.approx(expected.m_drive_tons)
    assert station.drives.m_drive.cost == pytest.approx(expected.m_drive_cost_mcr * 1_000_000)
    assert station.drives.m_drive.power == pytest.approx(expected.m_drive_power)

    assert station.power is not None
    assert station.power.plant is not None
    assert station.power.plant.tons == pytest.approx(expected.plant_tons)
    assert station.power.plant.cost == pytest.approx(expected.plant_cost_mcr * 1_000_000)
    assert station.available_power == pytest.approx(expected.available_power)

    assert station.fuel is not None
    assert station.fuel.operation_fuel is not None
    assert station.fuel.operation_fuel.tons == pytest.approx(expected.operation_fuel_tons)

    assert station.command is not None
    assert station.command.bridge is not None
    assert station.command.bridge.tons == pytest.approx(expected.bridge_tons)
    assert station.command.bridge.cost == pytest.approx(expected.bridge_cost_mcr * 1_000_000)

    assert station.computer is not None
    assert station.computer.hardware is not None
    assert station.computer.hardware.cost == pytest.approx(expected.computer_cost_mcr * 1_000_000)
    assert [(package.description, package.cost) for package in station.computer.software_packages] == (
        expected.software_packages
    )

    assert station.sensors.primary.tons == pytest.approx(expected.sensors_tons)
    assert station.sensors.primary.cost == pytest.approx(expected.sensors_cost_mcr * 1_000_000)
    assert station.sensors.primary.power == pytest.approx(expected.sensors_power)

    assert station.craft is not None
    assert len(station.craft.internal_housing) == expected.docking_space_count
    craft_housing = station.craft.internal_housing[0]
    assert isinstance(craft_housing, FullHangar | InternalDockingSpace)
    assert craft_housing.tons == pytest.approx(expected.docking_space_tons)
    assert craft_housing.cost == pytest.approx(expected.docking_space_cost_mcr * 1_000_000)
    assert craft_housing.craft.cost == pytest.approx(expected.air_raft_cost_mcr * 1_000_000)

    assert station.systems is not None
    assert len(station.systems.drones) == expected.probe_drones_count
    assert station.systems.drones[0].tons == pytest.approx(expected.probe_drones_tons)
    assert station.systems.drones[0].cost == pytest.approx(expected.probe_drones_cost_mcr * 1_000_000)
    assert len(station.systems.laboratories) == expected.lab_count
    assert sum(lab.tons for lab in station.systems.laboratories) == pytest.approx(expected.labs_total_tons)
    assert sum(lab.cost for lab in station.systems.laboratories) == pytest.approx(
        expected.labs_total_cost_mcr * 1_000_000
    )
    assert station.systems.libraries[0] is not None
    assert station.systems.libraries[0].tons == pytest.approx(expected.library_tons)
    assert station.systems.libraries[0].cost == pytest.approx(expected.library_cost_mcr * 1_000_000)

    assert station.habitation is not None
    assert sum(room.tons for room in station.habitation.staterooms) == pytest.approx(expected.staterooms_total_tons)
    assert sum(room.cost for room in station.habitation.staterooms) == pytest.approx(
        expected.staterooms_total_cost_mcr * 1_000_000
    )
    assert station.habitation.common_area is not None
    assert station.habitation.common_area.tons == pytest.approx(expected.common_area_tons)
    assert station.habitation.common_area.cost == pytest.approx(expected.common_area_cost_mcr * 1_000_000)

    assert station.cargo is not None
    assert len(station.cargo.cargo_holds) == expected.cargo_hold_count
    assert station.cargo.cargo_holds[0].usable_tons(station) == pytest.approx(expected.cargo_tons)
    assert CargoSection.cargo_tons_for_ship(station) == pytest.approx(expected.cargo_tons)

    assert station.available_power == pytest.approx(expected.available_power)
    assert station.basic_hull_power_load == pytest.approx(expected.power_basic)
    assert station.maneuver_power_load == pytest.approx(expected.power_maneuver)
    assert station.sensor_power_load == pytest.approx(expected.power_sensors)
    assert station.total_power_load == pytest.approx(expected.total_power)

    assert station.production_cost == pytest.approx(expected.production_cost_mcr * 1_000_000)
    assert station.sales_price_new == pytest.approx(expected.sales_price_mcr * 1_000_000)
    assert station.expenses.maintenance == pytest.approx(expected.maintenance_cr)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in station.crew.grouped_roles] == (
        expected.crew
    )

    assert station.notes.errors == expected.expected_errors
    assert station.notes.warnings == expected.expected_warnings
    assert station.crew.notes.infos == expected.expected_crew_infos
    assert station.crew.notes.warnings == expected.expected_crew_warnings


def assert_laboratory_station_spec_matches_reference(spec, expected: SimpleNamespace) -> None:
    for item in expected.spec_rows:
        assert spec.row(item, section=expected.spec_rows[item]).section == expected.spec_rows[item]
    assert spec.row('Advanced Probe Drones').quantity == expected.probe_drones_quantity
    assert spec.row('Laboratory').quantity == expected.lab_count
    assert spec.row('Staterooms').quantity == expected.staterooms_count
    assert spec.row('Cargo Hold').tons == pytest.approx(expected.cargo_tons)
