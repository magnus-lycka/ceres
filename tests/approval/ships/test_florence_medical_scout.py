"""Approval snapshot for the Florence-class Medical Scout.

Source: Mongoose Traveller 2e (screenshot of official stat block).

Purpose:
- exercise a 400-ton standard hull with J-3/M-2/FusionTL12 configuration
- verify Military sensors + Life Scanner Analysis Suite
- verify Medical Bays x6, Laboratory, Briefing Room
- verify slow pinnace + air/raft x2 docking spaces
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer15, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import Astrogator, Captain, Engineer, Maintenance, Medic, Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive3, MDrive2, PowerSection
from ceres.make.ship.habitation import HabitationSection, LowBerth, Stateroom
from ceres.make.ship.sensors import LifeScannerAnalysisSuite, MilitarySensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import FuelProcessor, FuelScoops, FuelSection, JumpFuel, OperationFuel
from ceres.make.ship.systems import BriefingRoom, CommonArea, Laboratory, MedicalBay, SystemsSection
from ceres.make.ship.weapons import DoubleTurret, WeaponsSection
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_florence_medical_scout() -> ship.Ship:
    return ship.Ship(
        ship_class='Florence',
        ship_type='Medical Scout',
        military=False,
        tl=14,
        displacement=400,
        design_type=ship.ShipDesignType.CUSTOM,
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 2,
                Astrogator(),
                *[Engineer()] * 2,
                Maintenance(),
                *[Medic()] * 6,
            ]
        ),
        occupants=[],
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive3()),
        power=PowerSection(plant=FusionPlantTL12(output=300)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=3),
            operation_fuel=OperationFuel(weeks=12),
            fuel_scoops=FuelScoops(),
            fuel_processor=FuelProcessor(tons=3),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer15(), software=[JumpControl(rating=3)]),
        sensors=SensorsSection(primary=MilitarySensors(), life_scanner_analysis_suite=LifeScannerAnalysisSuite()),
        weapons=WeaponsSection(turrets=[DoubleTurret()]),
        craft=CraftSection(
            internal_housing=[
                InternalDockingSpace(craft=SpaceCraft.from_catalog('Slow Pinnace')),
                InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft')),
                InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft')),
            ],
        ),
        systems=SystemsSection(internal_systems=[*[MedicalBay() for _ in range(6)], Laboratory(), BriefingRoom()]),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 8,
            low_berths=[LowBerth()] * 20,
            common_area=CommonArea(tons=32),
        ),
    )


@pytest.mark.approval
def test_florence_medical_scout(snapshot):
    snap = AnnotatedSnapshot(build_florence_medical_scout().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
