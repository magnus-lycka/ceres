"""Approval snapshot for the Gothta Ambush Fighter."""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive6, PowerSection, RDrive4
from ceres.make.ship.habitation import CabinSpace, HabitationSection
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
from ceres.make.ship.software import FireControl
from ceres.make.ship.storage import FuelScoops, FuelSection, OperationFuel, ReactionFuel
from ceres.make.ship.systems import Aerofins
from ceres.make.ship.weapons import FixedMount, PulseLaser, WeaponsSection
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_gothta_ambush_fighter() -> ship.Ship:
    return ship.Ship(
        ship_class='Gothta',
        ship_type='Ambush Fighter',
        military=True,
        tl=12,
        displacement=20,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            pressure_hull=True,
            airlocks=[],
            aerofins=Aerofins(),
        ),
        drives=DriveSection(
            m_drive=MDrive6(),
            r_drive=RDrive4(high_burn_thruster=True),
        ),
        power=PowerSection(plant=FusionPlantTL12(output=30)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=2),
            reaction_fuel=ReactionFuel(minutes=60),
            fuel_scoops=FuelScoops(free=True),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(), software=[FireControl(rating=1)]),
        sensors=SensorsSection(primary=MilitarySensors()),
        weapons=WeaponsSection(
            fixed_mounts=[FixedMount(weapons=[PulseLaser()])],
        ),
        habitation=HabitationSection(cabin_space=CabinSpace(tons=1.5)),
    )


@pytest.mark.approval
def test_gothta_ambush_fighter(snapshot):
    snap = AnnotatedSnapshot(build_gothta_ambush_fighter().build_spec().model_dump(mode='json'))
    snap.annotate('error', 'No airlock installed — expected error for this design')
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
