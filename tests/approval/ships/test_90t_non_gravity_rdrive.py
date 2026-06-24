"""Approval snapshot for 90-ton, Streamlined, Non-Gravity, R-Drive runabout.

Source: TL8, updated from the 100-ton non-gravity runabout note in
`refs/tycho/testcases.md`.
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.automation import LowAutomation
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, RDrive4, SpinExtSolarPanelsTL8, SterlingFissionPlant
from ceres.make.ship.power import PowerSection
from ceres.make.ship.sensors import SensorsSection
from ceres.make.ship.software import Library, Manoeuvre
from ceres.make.ship.storage import FuelScoops, FuelSection, OperationFuel, ReactionFuel
from ceres.make.ship.systems import Airlock
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot

_streamlined_non_gravity = hull.streamlined_hull.model_copy(update={'non_gravity': True})


def build_90t_non_gravity_rdrive() -> ship.Ship:
    return ship.Ship(
        tl=8,
        displacement=90,
        ship_class='Non-Gravity Runabout',
        ship_type='Runabout',
        hull=hull.Hull(
            configuration=_streamlined_non_gravity,
            heat_shielding=True,
            airlocks=[Airlock()],
        ),
        drives=DriveSection(r_drive=RDrive4()),
        power=PowerSection(
            plant=SterlingFissionPlant(output=8),
            solar=[SpinExtSolarPanelsTL8(tons=0.5)],
        ),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=52 * 15),
            reaction_fuel=ReactionFuel(minutes=360),
            fuel_scoops=FuelScoops(free=True),
        ),
        command=CommandSection(bridge=Bridge(small=True)),
        automation=LowAutomation(),
        computer=ComputerSection(
            hardware=Computer5(),
            software=[Library(), Manoeuvre()],
        ),
        sensors=SensorsSection(),
    )


@pytest.mark.approval
def test_90t_non_gravity_rdrive(snapshot):
    snap = AnnotatedSnapshot(build_90t_non_gravity_rdrive().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
