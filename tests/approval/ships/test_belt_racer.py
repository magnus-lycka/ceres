"""Approval snapshot for the Vargr Belt Racer.

Source: refs/belt_racer.

Purpose:
- provide a minimal reaction-drive racing craft reference case
- exercise close-structure light hulls, reaction fuel, cockpit command, and
  cockpit-style zero life-support costs
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Cockpit, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import (
    DriveSection,
    FusionPlantTL8,
    PowerSection,
    RDrive16,
)
from ceres.make.ship.storage import FuelSection, ReactionFuel
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot

BELT_RACER_HULL = hull.close_structure.model_copy(
    update={'light': True, 'description': 'Light Close Structure Hull'},
)


def build_belt_racer() -> ship.Ship:
    """Build the Belt Racer reference case from refs/belt_racer."""
    return ship.Ship(
        ship_class='Vargr Belt Racer',
        ship_type='Racer',
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=BELT_RACER_HULL),
        drives=DriveSection(r_drive=RDrive16()),
        power=PowerSection(plant=FusionPlantTL8(output=5)),
        fuel=FuelSection(reaction_fuel=ReactionFuel(minutes=52)),
        command=CommandSection(cockpit=Cockpit()),
        computer=ComputerSection(hardware=Computer5()),
    )


@pytest.mark.approval
def test_belt_racer(snapshot):
    snap = AnnotatedSnapshot(build_belt_racer().build_spec().model_dump(mode='json'))
    snap.annotate(
        'power_basic',
        'Ceres gives 2 (ceil(6 * 0.2) per RIS-013); Tycho stat block shows 1 (uses floor)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
