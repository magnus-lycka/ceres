"""Approval snapshot for the Boxy Ore Freighter."""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL8, MDrive1, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import BasicSensors, SensorsSection
from ceres.make.ship.storage import FuelSection, OperationFuel
from ceres.make.ship.systems import Airlock, CommonArea, SystemsSection, Workshop
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot

BOXY_HULL = hull.close_structure.model_copy(
    update={'light': True, 'description': 'Light Close Structure Hull'},
)


def build_boxy_ore_freighter() -> ship.Ship:
    return ship.Ship(
        ship_class='Boxy',
        ship_type='Ore Freighter',
        tl=9,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(configuration=BOXY_HULL, airlocks=[Airlock()]),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FusionPlantTL8(output=80)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=12)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        sensors=SensorsSection(primary=BasicSensors()),
        habitation=HabitationSection(staterooms=[Stateroom()], common_area=CommonArea(tons=1.0)),
        systems=SystemsSection(internal_systems=[Workshop()]),
    )


@pytest.mark.approval
def test_boxy_ore_freighter(snapshot):
    snap = AnnotatedSnapshot(build_boxy_ore_freighter().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
