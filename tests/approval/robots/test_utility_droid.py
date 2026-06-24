"""Approval snapshot for the Utility Droid robot.

Source: refs/robot/104_utility_droid.md
"""

import pytest

from ceres.make.robot import BasicBrain, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.options import DecreasedResiliency, DroneInterface
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_utility_droid() -> Robot:
    return Robot(
        name='Utility Droid',
        tl=9,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(),
        brain=BasicBrain(brain_tl=8, function='servant'),
        options=[
            *default_suite(),
            DroneInterface(),
            DecreasedResiliency(hit_reduction=2),
        ],
    )


@pytest.mark.approval
def test_utility_droid(snapshot):
    snap = AnnotatedSnapshot(build_utility_droid().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr29,000 vs source Cr24,000 — discrepancy untraced, see RIR-002; '
        'BCC Cr10,000 + BasicBrain TL8 Cr20,000 - DecreasedResiliency Cr1,000',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
