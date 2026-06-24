"""Approval snapshot for the Suleiman Scout/Courier.

Source: refs/tycho/Suleiman.md.

Purpose:
- provide a compact source-derived scout/courier baseline
- exercise standard TL12 Streamlined/J-2/M-2/Fusion-60 design rules
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive2, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import FuelProcessor, FuelSection, JumpFuel, OperationFuel
from ceres.make.ship.systems import Airlock, ProbeDrones, SystemsSection, Workshop
from ceres.make.ship.weapons import DoubleTurret, WeaponsSection
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_suleiman() -> ship.Ship:
    """Build the Suleiman reference case from refs/tycho/Suleiman.md."""
    return ship.Ship(
        ship_class='Suleiman',
        ship_type='Scout/Courier',
        tl=12,
        displacement=100,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            armour=armour.CrystalironArmour(protection=4),
            airlocks=[Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=60)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(bis=True), software=[JumpControl(rating=2)]),
        sensors=SensorsSection(primary=MilitarySensors()),
        weapons=WeaponsSection(turrets=[DoubleTurret()]),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))]),
        habitation=HabitationSection(staterooms=[Stateroom()] * 4),
        systems=SystemsSection(internal_systems=[Workshop()], drones=[ProbeDrones(count=10)]),
    )


@pytest.mark.approval
def test_suleiman(snapshot):
    snap = AnnotatedSnapshot(build_suleiman().build_spec().model_dump(mode='json'))
    snap.annotate(
        'fuel',
        'Ceres gives op_fuel=2.0t per RIS-007 (rounds up to whole dTon for ≥100t ships); ref shows 1.20t',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
