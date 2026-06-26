"""Approval snapshot for the Beowulf Type A Free Trader.

Source: refs/tycho/Beowulf.md.

Purpose:
- provide a compact source-derived commercial baseline ship
- exercise standard TL12 Streamlined/J-1/M-1/Fusion-75 design rules
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crew import Astrogator, Engineer, Pilot, ShipCrew, Steward
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive1, MDrive1, PowerSection
from ceres.make.ship.habitation import HabitationSection, LowBerth, Stateroom
from ceres.make.ship.occupants import MiddlePassage
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import (
    CargoCrane,
    CargoHold,
    CargoSection,
    FuelProcessor,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import Airlock, CommonArea
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_beowulf() -> ship.Ship:
    """Build the Beowulf reference case from refs/tycho/Beowulf.md."""
    return ship.Ship(
        ship_class='Beowulf',
        ship_type='Type A Free Trader',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            armour=armour.CrystalironArmour(protection=2),
            airlocks=[Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive1(), j_drive=JDrive1()),
        power=PowerSection(plant=FusionPlantTL12(output=75)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=1),
            operation_fuel=OperationFuel(weeks=4),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(), software=[JumpControl(rating=1)]),
        sensors=SensorsSection(primary=CivilianSensors()),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            low_berths=[LowBerth()] * 20,
            common_area=CommonArea(tons=10.0),
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(crane=CargoCrane())]),
        crew=ShipCrew(roles=[Pilot(), Astrogator(), Engineer(), Steward()]),
        occupants=[MiddlePassage()] * 16,
    )


@pytest.mark.approval
def test_beowulf(snapshot):
    snap = AnnotatedSnapshot(build_beowulf().build_spec().model_dump(mode='json'))
    snap.annotate('fuel', 'Ceres gives op_fuel=1.0t per RIS-007 (1-ton minimum); ref shows 0.5t')
    snap.annotate(
        'life_support',
        'Ceres gives 30,000 (4 crew + 16 middle passengers); ref shows 31,000 (source inconsistency)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
