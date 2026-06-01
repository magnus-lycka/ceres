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
from tests.ships.reference_assertions import (
    assert_laboratory_station_matches_reference,
    assert_laboratory_station_spec_matches_reference,
)

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
    docking_space_count=1,
    docking_space_tons=5.0,
    docking_space_cost_mcr=1.25,
    air_raft_cost_mcr=0.25,
    probe_drones_count=1,
    probe_drones_quantity=20,
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
    cargo_hold_count=1,
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
    expected_errors=[],
    expected_warnings=[],
    expected_crew_infos=[
        'ADMINISTRATOR above recommended count: 50 > 0',
        'MAINTENANCE above recommended count: 1 > 0',
        'OFFICER above recommended count: 2 > 0',
        'STEWARD above recommended count: 1 > 0',
    ],
    expected_crew_warnings=[],
    spec_rows={
        'Dispersed Structure Hull': 'Hull',
        'M-Drive 1': 'Propulsion',
        'Fusion (TL 12), Power 120': 'Power',
        '8 weeks of operation': 'Fuel',
        'Smaller Bridge': 'Command',
        'Computer/10': 'Computer',
        'Advanced Sensors': 'Sensors',
        'Internal Docking Space: Air/Raft': 'Craft',
        'Air/Raft': 'Craft',
        'Advanced Probe Drones': 'Systems',
        'Laboratory': 'Systems',
        'Library': 'Systems',
        'Staterooms': 'Habitation',
        'Common Area': 'Habitation',
    },
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


@pytest.fixture(scope='module')
def almeida_laboratory_station():
    return build_almeida_laboratory_station()


@pytest.fixture(scope='module')
def almeida_laboratory_station_spec(almeida_laboratory_station):
    return almeida_laboratory_station.build_spec()


def test_almeida_laboratory_station_matches_reference_sheet(almeida_laboratory_station):
    assert_laboratory_station_matches_reference(almeida_laboratory_station, _expected)


def test_almeida_laboratory_station_spec_structure(almeida_laboratory_station_spec):
    assert_laboratory_station_spec_matches_reference(almeida_laboratory_station_spec, _expected)
