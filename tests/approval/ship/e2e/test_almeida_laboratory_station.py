"""Approval snapshot for Almeida-class Laboratory Station.

Source: refs/tycho/AlmeidaLaboratoryStation.txt.

Purpose:
- provide a source-derived dispersed-structure laboratory station case
- exercise small bridge, advanced sensors, advanced probe drones, bulk
  laboratories, and a large explicit administrative crew
"""

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
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


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


@pytest.mark.approval
def test_almeida_laboratory_station(snapshot):
    snap = AnnotatedSnapshot(build_almeida_laboratory_station().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
