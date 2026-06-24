"""Approval snapshot for the Type-K Safari Ship.

Source: refs/hg/66_prospecting_buggy.md, page 173.

Purpose:
- provide a compact High Guard source snapshot with a named common-area space
- exercise generic part display labels on a real ship/gallery entry
- keep the source's distinction between ordinary common area and a labelled
  trophy lounge without introducing a dedicated TrophyLounge rule class
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import Astrogator, Engineer, Medic, Pilot, ShipCrew, Steward
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive1, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import (
    CargoHold,
    CargoSection,
    FuelProcessor,
    FuelScoops,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import CommonArea
from ceres.make.ship.weapons import DoubleTurret, WeaponsSection
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_safari_ship() -> ship.Ship:
    """Note: Incomplete Type-K Safari Ship slice; multi-environment systems and launch-carried ATV remain unmodeled."""
    return ship.Ship(
        ship_class='Type-K',
        ship_type='Safari Ship',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive1(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=105)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=4),
            fuel_scoops=FuelScoops(free=True),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(bis=True), software=[JumpControl(rating=2)]),
        sensors=SensorsSection(primary=CivilianSensors()),
        weapons=WeaponsSection(turrets=[DoubleTurret()]),
        craft=CraftSection(
            internal_housing=[
                InternalDockingSpace(craft=SpaceCraft.from_catalog('Launch')),
                InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft')),
            ]
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 11,
            common_area=CommonArea(tons=13),
            common_areas=[CommonArea(tons=7, display_label='Trophy Lounge')],
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=13.2)]),
        crew=ShipCrew(roles=[Pilot(), Astrogator(), Engineer(), Steward(), Medic()]),
    )


@pytest.mark.approval
def test_safari_ship(snapshot):
    snap = AnnotatedSnapshot(build_safari_ship().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
