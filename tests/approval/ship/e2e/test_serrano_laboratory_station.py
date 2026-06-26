"""Approval snapshot for the Serrano-class Laboratory Station.

Source: refs/tycho/SerranoLaboratoryStation.txt.

Purpose:
- provide a smaller source-derived dispersed-structure laboratory station case
- exercise the same laboratory-station model family as Almeida at TL12
"""

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
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


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


@pytest.mark.approval
def test_serrano_laboratory_station(snapshot):
    snap = AnnotatedSnapshot(build_serrano_laboratory_station().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cargo',
        'Ceres gives 2t cargo; ref sheet shows 1t — unresolved 1t discrepancy',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
