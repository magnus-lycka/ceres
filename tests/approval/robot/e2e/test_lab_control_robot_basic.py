"""Approval snapshot for the Basic Lab Control Robot.

Source: refs/robot/109_domestic_servant.md
Default suite substitutes Visual Spectrum Sensor → Video Screen (improved)
and Transceiver 5km (improved) → Transceiver 500km (improved).
"""

import pytest

from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize, default_suite
from ceres.make.robot.options import (
    ExternalPower,
    RoboticDroneController,
    RobotTransceiver,
    VideoScreen,
)
from ceres.make.robot.skills import Electronics
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_basic_lab_control_robot() -> Robot:
    return Robot(
        name='Basic Lab Control Robot',
        tl=12,
        size=RobotSize.SIZE_1,
        locomotion=NoneLocomotion(),
        brain=AdvancedBrain(
            brain_tl=12,
            installed_skills=(Electronics(remote_ops=1),),
        ),
        manipulators=[],
        options=[
            *default_suite(see=False, improved_transceiver=False),
            VideoScreen(quality='improved'),
            RobotTransceiver(range_km=500, quality='improved'),
            ExternalPower(),
            RoboticDroneController(quality='basic'),
        ],
    )


@pytest.mark.approval
def test_lab_control_robot_basic(snapshot):
    snap = AnnotatedSnapshot(build_basic_lab_control_robot().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr14,680 vs source Cr12,000 — source uses editorial simplification, '
        'omits skill package Cr1,000 and default suite substitution costs; '
        'SIZE_1 NoneLocomotion removal credit capped at 20% BCC = -Cr20',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
