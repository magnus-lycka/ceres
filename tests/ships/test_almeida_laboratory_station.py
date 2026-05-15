"""Reference ship case based on refs/tycho/AlmeidaLaboratoryStation.txt.

Purpose:
- provide a source-derived dispersed-structure laboratory station case
- exercise small bridge, advanced sensors, advanced probe drones, bulk
  laboratories, and a large explicit administrative crew

Source handling for this test case:
- supported: hull, manoeuvre drive, power plant, bridge, computer, included
  software, advanced sensors, docking space, air/raft, advanced probe drones,
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
from ceres.make.ship.sensors import AdvancedSensors, SensorsSection
from ceres.make.ship.storage import CargoHold, CargoSection, FuelSection, OperationFuel
from ceres.make.ship.systems import AdvancedProbeDrones, CommonArea, Laboratory, LibraryFacility, SystemsSection

_expected = SimpleNamespace(
    tl=15,
    displacement=400,
    hull_cost_mcr=10.0,  # 400t Dispersed Structure
    hull_points=144.0,
    m_drive_tons=4.0,
    m_drive_cost_mcr=8.0,
    m_drive_power=40.0,
    plant_tons=8.0,
    plant_cost_mcr=8.0,
    available_power=120.0,
    operation_fuel_tons=2.0,
    bridge_tons=10.0,
    bridge_cost_mcr=1.0,
    computer_cost_mcr=0.16,
    software_packages=[('Library', 0.0), ('Manoeuvre/0', 0.0), ('Intellect', 0.0)],
    sensors_tons=5.0,
    sensors_cost_mcr=5.3,
    sensors_power=6.0,
    docking_space_tons=5.0,
    docking_space_cost_mcr=1.25,
    air_raft_cost_mcr=0.25,
    probe_drones_tons=4.0,
    probe_drones_cost_mcr=3.2,
    lab_count=50,
    labs_total_tons=200.0,
    labs_total_cost_mcr=50.0,
    library_tons=4.0,
    library_cost_mcr=4.0,
    staterooms_count=29,
    staterooms_total_tons=116.0,
    staterooms_total_cost_mcr=14.5,
    common_area_tons=29.0,
    common_area_cost_mcr=2.9,
    cargo_tons=13.0,
    power_basic=80.0,
    power_maneuver=40.0,
    power_sensors=6.0,
    total_power=126.0,
    production_cost_mcr=108.56,
    sales_price_mcr=97.704,
    maintenance_cr=8_142.0,
    crew=[
        ('PILOT', 1, 6_000),
        ('ENGINEER', 1, 4_000),
        ('MAINTENANCE', 1, 1_000),
        ('STEWARD', 1, 2_000),
        ('ADMINISTRATOR', 50, 1_500),
        ('OFFICER', 2, 5_000),
    ],
)


def build_almeida_laboratory_station() -> ship.Ship:
    return ship.Ship(
        ship_class='Almeida-class',
        ship_type='Laboratory Station',
        tl=15,
        displacement=400,
        design_type=ship.ShipDesignType.STANDARD,
        occupants=[],
        hull=hull.Hull(configuration=hull.dispersed_structure),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FusionPlantTL12(output=120)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=8)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer10()),
        sensors=SensorsSection(primary=AdvancedSensors()),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))]),
        systems=SystemsSection(
            drones=[AdvancedProbeDrones(count=20)],
            internal_systems=[*[Laboratory()] * 50, LibraryFacility()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 29,
            common_area=CommonArea(tons=29.0),
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=13.0)]),
        crew=ShipCrew(
            roles=[
                Pilot(),
                Engineer(),
                Maintenance(),
                Steward(),
                *[Administrator()] * 50,
                *[Officer()] * 2,
            ]
        ),
    )


def test_almeida_laboratory_station_matches_reference_sheet():
    station = build_almeida_laboratory_station()

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
    assert 'MAINTENANCE above recommended count: 1 > 0' in crew_infos
    assert 'STEWARD above recommended count: 1 > 0' in crew_infos
    assert 'ADMINISTRATOR above recommended count: 50 > 0' in crew_infos
    assert 'OFFICER above recommended count: 2 > 0' in crew_infos


def test_almeida_laboratory_station_spec_structure():
    station = build_almeida_laboratory_station()
    spec = station.build_spec()

    assert spec.row('Dispersed Structure Hull').section == 'Hull'
    assert spec.row('M-Drive 1').section == 'Propulsion'
    assert spec.row('Fusion (TL 12), Power 120').section == 'Power'
    assert spec.row('8 weeks of operation').section == 'Fuel'
    assert spec.row('Smaller Bridge').section == 'Command'
    assert spec.row('Computer/10').section == 'Computer'
    assert spec.row('Advanced Sensors').section == 'Sensors'
    assert spec.row('Internal Docking Space: Air/Raft').section == 'Craft'
    assert spec.row('Air/Raft').section == 'Craft'
    assert spec.row('Advanced Probe Drones').section == 'Systems'
    assert spec.row('Advanced Probe Drones').quantity == 20
    assert spec.row('Laboratory').section == 'Systems'
    assert spec.row('Laboratory').quantity == 50
    assert spec.row('Library', section='Systems').section == 'Systems'
    assert spec.row('Staterooms').section == 'Habitation'
    assert spec.row('Staterooms').quantity == 29
    assert spec.row('Common Area').section == 'Habitation'
    assert spec.row('Cargo Hold').tons == pytest.approx(13.0)
