"""Reference ship case based on refs/SerranoLaboratoryStation.txt.

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
    Tycho's recommended minimum crew, producing informational notes rather than
    changing the manifest
"""

import pytest

from ceres.build.ship import hull, ship
from ceres.build.ship.bridge import Bridge, CommandSection
from ceres.build.ship.computer import Computer, ComputerSection
from ceres.build.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.build.ship.crew import Administrator, Engineer, Maintenance, Officer, Pilot, ShipCrew, Steward
from ceres.build.ship.drives import DriveSection, FusionPlantTL12, MDrive, PowerSection
from ceres.build.ship.habitation import HabitationSection, Stateroom
from ceres.build.ship.sensors import MilitarySensors, SensorsSection
from ceres.build.ship.storage import CargoHold, CargoSection, FuelSection, OperationFuel
from ceres.build.ship.systems import AdvancedProbeDrones, CommonArea, Laboratory, LibraryFacility, SystemsSection


def build_serrano_laboratory_station() -> ship.Ship:
    return ship.Ship(
        ship_class='Serrano-class',
        ship_type='Laboratory Station',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        passenger_vector={},
        hull=hull.Hull(configuration=hull.dispersed_structure),
        drives=DriveSection(m_drive=MDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=60)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=8)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer(10)),
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

    assert station.tl == 12
    assert station.displacement == 200
    assert station.hull_cost == pytest.approx(5_000_000.0)
    assert station.hull_points == pytest.approx(72.0)

    assert station.drives is not None
    assert station.drives.m_drive is not None
    assert station.drives.m_drive.tons == pytest.approx(2.0)
    assert station.drives.m_drive.cost == pytest.approx(4_000_000.0)
    assert station.drives.m_drive.power == pytest.approx(20.0)

    assert station.power is not None
    assert station.power.fusion_plant is not None
    assert station.power.fusion_plant.tons == pytest.approx(4.0)
    assert station.power.fusion_plant.cost == pytest.approx(4_000_000.0)
    assert station.available_power == pytest.approx(60.0)

    assert station.fuel is not None
    assert station.fuel.operation_fuel is not None
    assert station.fuel.operation_fuel.tons == pytest.approx(1.0)

    assert station.command is not None
    assert station.command.bridge is not None
    assert station.command.bridge.tons == pytest.approx(6.0)
    assert station.command.bridge.cost == pytest.approx(500_000.0)

    assert station.computer is not None
    assert station.computer.hardware is not None
    assert station.computer.hardware.cost == pytest.approx(160_000.0)
    assert [(package.description, package.cost) for package in station.computer.software_packages.values()] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
    ]

    assert station.sensors.primary.tons == pytest.approx(2.0)
    assert station.sensors.primary.cost == pytest.approx(4_100_000.0)
    assert station.sensors.primary.power == pytest.approx(2.0)

    assert station.craft is not None
    assert len(station.craft.internal_housing) == 1
    assert station.craft.internal_housing[0].tons == pytest.approx(5.0)
    assert station.craft.internal_housing[0].cost == pytest.approx(1_250_000.0)
    assert station.craft.internal_housing[0].craft.cost == pytest.approx(250_000.0)

    assert station.systems is not None
    assert len(station.systems.drones) == 1
    assert station.systems.drones[0].tons == pytest.approx(3.0)
    assert station.systems.drones[0].cost == pytest.approx(2_400_000.0)
    assert len(station.systems.laboratories) == 24
    assert sum(lab.tons for lab in station.systems.laboratories) == pytest.approx(96.0)
    assert sum(lab.cost for lab in station.systems.laboratories) == pytest.approx(24_000_000.0)
    assert station.systems.library is not None
    assert station.systems.library.tons == pytest.approx(4.0)
    assert station.systems.library.cost == pytest.approx(4_000_000.0)

    assert station.habitation is not None
    assert sum(room.tons for room in station.habitation.staterooms) == pytest.approx(60.0)
    assert sum(room.cost for room in station.habitation.staterooms) == pytest.approx(7_500_000.0)
    assert station.habitation.common_area is not None
    assert station.habitation.common_area.tons == pytest.approx(15.0)
    assert station.habitation.common_area.cost == pytest.approx(1_500_000.0)

    assert station.cargo is not None
    assert len(station.cargo.cargo_holds) == 1
    assert station.cargo.cargo_holds[0].usable_tons(station) == pytest.approx(2.0)
    assert CargoSection.cargo_tons_for_ship(station) == pytest.approx(2.0)

    assert station.available_power == pytest.approx(60.0)
    assert station.basic_hull_power_load == pytest.approx(40.0)
    assert station.maneuver_power_load == pytest.approx(20.0)
    assert station.sensor_power_load == pytest.approx(2.0)
    assert station.total_power_load == pytest.approx(62.0)

    assert station.production_cost == pytest.approx(58_660_000.0)
    assert station.sales_price_new == pytest.approx(52_794_000.0)
    assert station.expenses.maintenance == pytest.approx(4_400.0)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in station.crew.grouped_roles] == [
        ('PILOT', 1, 6_000),
        ('ENGINEER', 1, 4_000),
        ('MAINTENANCE', 1, 1_000),
        ('STEWARD', 1, 2_000),
        ('ADMINISTRATOR', 24, 1_500),
        ('OFFICER', 1, 5_000),
    ]

    assert ('info', 'ADMINISTRATOR above recommended count: 24 > 0') in [
        (note.category.value, note.message) for note in station.crew.notes
    ]
    assert ('info', 'MAINTENANCE above recommended count: 1 > 0') in [
        (note.category.value, note.message) for note in station.crew.notes
    ]
    assert ('info', 'OFFICER above recommended count: 1 > 0') in [
        (note.category.value, note.message) for note in station.crew.notes
    ]
    assert ('info', 'STEWARD above recommended count: 1 > 0') in [
        (note.category.value, note.message) for note in station.crew.notes
    ]


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
