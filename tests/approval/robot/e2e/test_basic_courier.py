"""Approval snapshot for the Basic Courier robot.

Source: refs/robot/107_courier_basic.md
"""

import pytest

from ceres.make.robot import BasicBrain, GravLocomotion, Robot, RobotSize, default_suite
from ceres.make.robot.options import (
    NavigationSystem,
    RobotTransceiver,
    StorageCompartment,
    VehicleSpeedModification,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_basic_courier() -> Robot:
    return Robot(
        name='Basic Courier',
        tl=10,
        size=RobotSize.SIZE_3,
        locomotion=GravLocomotion(),
        brain=BasicBrain(function='locomotion'),
        manipulators=[],
        options=[
            *default_suite(improved_transceiver=False, drone=True),
            RobotTransceiver(range_km=500, quality='improved'),
            VehicleSpeedModification(),
            NavigationSystem(quality='basic'),
            StorageCompartment(slots_count=3, storage_type='hazardous'),
        ],
    )


@pytest.mark.approval
def test_basic_courier(snapshot):
    snap = AnnotatedSnapshot(build_basic_courier().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr23,900 vs source Cr25,000 — discrepancy untraced, see RIR-002',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
