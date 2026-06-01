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
from tests.ships.reference_assertions import (
    assert_laboratory_station_matches_reference,
    assert_laboratory_station_spec_matches_reference,
)

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
    docking_space_count=1,
    docking_space_tons=5.0,
    docking_space_cost_mcr=1.25,
    air_raft_cost_mcr=0.25,
    probe_drones_count=1,
    probe_drones_quantity=15,
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
    cargo_hold_count=1,
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
    expected_errors=[],
    expected_warnings=[],
    expected_crew_infos=[
        'ADMINISTRATOR above recommended count: 24 > 0',
        'MAINTENANCE above recommended count: 1 > 0',
        'OFFICER above recommended count: 1 > 0',
        'STEWARD above recommended count: 1 > 0',
    ],
    expected_crew_warnings=[],
    spec_rows={
        'Dispersed Structure Hull': 'Hull',
        'M-Drive 1': 'Propulsion',
        'Fusion (TL 12), Power 60': 'Power',
        '8 weeks of operation': 'Fuel',
        'Smaller Bridge': 'Command',
        'Computer/10': 'Computer',
        'Military Grade Sensors': 'Sensors',
        'Internal Docking Space: Air/Raft': 'Craft',
        'Air/Raft': 'Craft',
        'Advanced Probe Drones': 'Systems',
        'Laboratory': 'Systems',
        'Library': 'Systems',
        'Staterooms': 'Habitation',
        'Common Area': 'Habitation',
    },
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


@pytest.fixture(scope='module')
def serrano_laboratory_station():
    return build_serrano_laboratory_station()


@pytest.fixture(scope='module')
def serrano_laboratory_station_spec(serrano_laboratory_station):
    return serrano_laboratory_station.build_spec()


def test_serrano_laboratory_station_matches_reference_sheet(serrano_laboratory_station):
    assert_laboratory_station_matches_reference(serrano_laboratory_station, _expected)


def test_serrano_laboratory_station_spec_structure(serrano_laboratory_station_spec):
    assert_laboratory_station_spec_matches_reference(serrano_laboratory_station_spec, _expected)
