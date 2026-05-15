"""Reference ship case based on refs/tycho/SerranoLaboratoryStation.txt.

Purpose:
- provide a smaller source-derived dispersed-structure laboratory station case
- exercise the same laboratory-station model family as Almeida at TL12

Source handling for this test case:
- supported: hull, manoeuvre drive, power plant, bridge, computer, included
  software, military sensors, docking space, air/raft, advanced probe drones,
  laboratories, physical library, standard staterooms, common area, cargo
  space, production cost, discounted purchase price, maintenance cost, and
  operation fuel
- deliberate interpretation:
  - explicit crew is carried over from the source sheet and allowed to exceed
    Ceres' recommended minimum crew, producing informational notes rather than
    changing the manifest
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer10, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.make.ship.crew import Administrator, Engineer, Maintenance, Officer, Pilot, ShipCrew, Steward
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive1, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
from ceres.make.ship.storage import CargoHold, CargoSection, FuelSection, OperationFuel
from ceres.make.ship.systems import AdvancedProbeDrones, CommonArea, Laboratory, LibraryFacility, SystemsSection

_expected = SimpleNamespace(
    tl=12,
    displacement=200,
    hull_cost_mcr=5.0,  # 200t Dispersed Structure
    hull_points=72.0,
    m_drive_tons=2.0,
    m_drive_cost_mcr=4.0,
    m_drive_power=20.0,
    plant_tons=4.0,
    plant_cost_mcr=4.0,
    available_power=60.0,
    operation_fuel_tons=1.0,
    bridge_tons=6.0,
    bridge_cost_mcr=0.5,
    computer_cost_mcr=0.16,
    software_packages=[('Library', 0.0), ('Manoeuvre/0', 0.0), ('Intellect', 0.0)],
    sensors_tons=2.0,
    sensors_cost_mcr=4.1,
    sensors_power=2.0,
    docking_space_tons=5.0,
    docking_space_cost_mcr=1.25,
    air_raft_cost_mcr=0.25,
    probe_drones_tons=3.0,
    probe_drones_cost_mcr=2.4,
    lab_count=24,
    labs_total_tons=96.0,
    labs_total_cost_mcr=24.0,
    library_tons=4.0,
    library_cost_mcr=4.0,
    staterooms_count=15,
    staterooms_total_tons=60.0,
    staterooms_total_cost_mcr=7.5,
    common_area_tons=15.0,
    common_area_cost_mcr=1.5,
    cargo_tons=1.0,  # ref sheet; Ceres gives 2 — unresolved 1t discrepancy
    power_basic=40.0,
    power_maneuver=20.0,
    power_sensors=2.0,
    total_power=62.0,
    production_cost_mcr=58.66,
    sales_price_mcr=52.794,
    maintenance_cr=4_400.0,
    crew=[
        ('PILOT', 1, 6_000),
        ('ENGINEER', 1, 4_000),
        ('MAINTENANCE', 1, 1_000),
        ('STEWARD', 1, 2_000),
        ('ADMINISTRATOR', 24, 1_500),
        ('OFFICER', 1, 5_000),
    ],
)
# Ceres gives 2 tons cargo; ref sheet shows 1 — unresolved 1t discrepancy
_expected.cargo_tons = 2.0


def build_serrano_laboratory_station() -> ship.Ship:
    return ship.Ship(
        ship_class='Serrano-class',
        ship_type='Laboratory Station',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        occupants=[],
        hull=hull.Hull(configuration=hull.dispersed_structure),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FusionPlantTL12(output=60)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=8)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer10()),
        sensors=SensorsSection(primary=MilitarySensors()),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))]),
        systems=SystemsSection(
            drones=[AdvancedProbeDrones(count=15)],
            internal_systems=[*[Laboratory()] * 24, LibraryFacility()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 15,
            common_area=CommonArea(tons=15.0),
        ),
        cargo=CargoSection(cargo_holds=[CargoHold()]),
        crew=ShipCrew(
            roles=[
                Pilot(),
                Engineer(),
                Maintenance(),
                Steward(),
                *[Administrator()] * 24,
                Officer(),
            ]
        ),
    )


def test_serrano_laboratory_station_matches_reference_sheet():
    station = build_serrano_laboratory_station()

    assert station.tl == _expected.tl
    assert station.displacement == _expected.displacement
    assert station.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert station.hull_points == pytest.approx(_expected.hull_points)

    assert station.drives is not None
    assert station.drives.m_drive is not None
    assert station.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert station.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert station.drives.m_drive.power == pytest.approx(_expected.m_drive_power)

    assert station.power is not None
    assert station.power.plant is not None
    assert station.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert station.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)
    assert station.available_power == pytest.approx(_expected.available_power)

    assert station.fuel is not None
    assert station.fuel.operation_fuel is not None
    assert station.fuel.operation_fuel.tons == pytest.approx(_expected.operation_fuel_tons)

    assert station.command is not None
    assert station.command.bridge is not None
    assert station.command.bridge.tons == pytest.approx(_expected.bridge_tons)
    assert station.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)

    assert station.computer is not None
    assert station.computer.hardware is not None
    assert station.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)
    assert [(package.description, package.cost) for package in station.computer.software_packages] == (
        _expected.software_packages
    )

    assert station.sensors.primary.tons == pytest.approx(_expected.sensors_tons)
    assert station.sensors.primary.cost == pytest.approx(_expected.sensors_cost_mcr * 1_000_000)
    assert station.sensors.primary.power == pytest.approx(_expected.sensors_power)

    assert station.craft is not None
    assert len(station.craft.internal_housing) == 1
    assert station.craft.internal_housing[0].tons == pytest.approx(_expected.docking_space_tons)
    assert station.craft.internal_housing[0].cost == pytest.approx(_expected.docking_space_cost_mcr * 1_000_000)
    assert station.craft.internal_housing[0].craft.cost == pytest.approx(_expected.air_raft_cost_mcr * 1_000_000)

    assert station.systems is not None
    assert len(station.systems.drones) == 1
    assert station.systems.drones[0].tons == pytest.approx(_expected.probe_drones_tons)
    assert station.systems.drones[0].cost == pytest.approx(_expected.probe_drones_cost_mcr * 1_000_000)
    assert len(station.systems.laboratories) == _expected.lab_count
    assert sum(lab.tons for lab in station.systems.laboratories) == pytest.approx(_expected.labs_total_tons)
    assert sum(lab.cost for lab in station.systems.laboratories) == pytest.approx(
        _expected.labs_total_cost_mcr * 1_000_000
    )
    assert station.systems.library is not None
    assert station.systems.library.tons == pytest.approx(_expected.library_tons)
    assert station.systems.library.cost == pytest.approx(_expected.library_cost_mcr * 1_000_000)

    assert station.habitation is not None
    assert sum(room.tons for room in station.habitation.staterooms) == pytest.approx(_expected.staterooms_total_tons)
    assert sum(room.cost for room in station.habitation.staterooms) == pytest.approx(
        _expected.staterooms_total_cost_mcr * 1_000_000
    )
    assert station.habitation.common_area is not None
    assert station.habitation.common_area.tons == pytest.approx(_expected.common_area_tons)
    assert station.habitation.common_area.cost == pytest.approx(_expected.common_area_cost_mcr * 1_000_000)

    assert station.cargo is not None
    assert len(station.cargo.cargo_holds) == 1
    assert station.cargo.cargo_holds[0].usable_tons(station) == pytest.approx(_expected.cargo_tons)
    assert CargoSection.cargo_tons_for_ship(station) == pytest.approx(_expected.cargo_tons)

    assert station.available_power == pytest.approx(_expected.available_power)
    assert station.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert station.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert station.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert station.total_power_load == pytest.approx(_expected.total_power)

    assert station.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert station.sales_price_new == pytest.approx(_expected.sales_price_mcr * 1_000_000)
    assert station.expenses.maintenance == pytest.approx(_expected.maintenance_cr)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in station.crew.grouped_roles] == (
        _expected.crew
    )

    crew_infos = station.crew.notes.infos
    assert 'ADMINISTRATOR above recommended count: 24 > 0' in crew_infos
    assert 'MAINTENANCE above recommended count: 1 > 0' in crew_infos
    assert 'OFFICER above recommended count: 1 > 0' in crew_infos
    assert 'STEWARD above recommended count: 1 > 0' in crew_infos


def test_serrano_laboratory_station_spec_structure():
    station = build_serrano_laboratory_station()
    spec = station.build_spec()

    assert spec.row('Dispersed Structure Hull').section == 'Hull'
    assert spec.row('M-Drive 1').section == 'Propulsion'
    assert spec.row('Fusion (TL 12), Power 60').section == 'Power'
    assert spec.row('8 weeks of operation').section == 'Fuel'
    assert spec.row('Smaller Bridge').section == 'Command'
    assert spec.row('Computer/10').section == 'Computer'
    assert spec.row('Military Grade Sensors').section == 'Sensors'
    assert spec.row('Internal Docking Space: Air/Raft').section == 'Craft'
    assert spec.row('Air/Raft').section == 'Craft'
    assert spec.row('Advanced Probe Drones').section == 'Systems'
    assert spec.row('Advanced Probe Drones').quantity == 15
    assert spec.row('Laboratory').section == 'Systems'
    assert spec.row('Laboratory').quantity == 24
    assert spec.row('Library', section='Systems').section == 'Systems'
    assert spec.row('Staterooms').section == 'Habitation'
    assert spec.row('Staterooms').quantity == 15
    assert spec.row('Common Area').section == 'Habitation'
    assert spec.row('Cargo Hold').tons == pytest.approx(2.0)
