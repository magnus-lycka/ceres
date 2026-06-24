"""Approval snapshot for the Freight Handler Pod.

Source: Small Craft Catalogue (official publication).

Purpose:
- exercise 6-ton close-structure hull with Fission plant and small-craft systems
- confirm Basic Ship Systems power = 2 per RIS-013 (ceil(6 * 0.2) = 2)
- confirm TowCable and GrapplingArm tonnage and cost
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Cockpit, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FissionPlant, MDrive1, PowerSection
from ceres.make.ship.storage import FuelSection, OperationFuel
from ceres.make.ship.systems import GrapplingArm, SystemsSection, TowCable
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_freight_handler_pod() -> ship.Ship:
    return ship.Ship(
        ship_class='Freight Handler Pod',
        ship_type='Freight Handler',
        tl=9,
        displacement=6,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(configuration=hull.close_structure),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FissionPlant(output=4)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=1)),
        command=CommandSection(cockpit=Cockpit()),
        computer=ComputerSection(hardware=Computer5()),
        systems=SystemsSection(
            internal_systems=[TowCable(), GrapplingArm()],
        ),
    )


@pytest.mark.approval
def test_freight_handler_pod(snapshot):
    snap = AnnotatedSnapshot(build_freight_handler_pod().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cargo',
        'Stat block shows 1.5t; Ceres gives 1.78t (0.28t discrepancy — possibly a standard small-craft '
        'overhead in the SCC design tool not modelled by Ceres)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
