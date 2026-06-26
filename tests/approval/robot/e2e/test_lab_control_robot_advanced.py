"""Approval snapshot for the Advanced Lab Control Robot.

Source: refs/robot/110_lab_control_robot_advanced.md
"""

import pytest

from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize, default_suite
from ceres.make.robot.options import (
    AvatarController,
    ExternalPower,
    RoboticDroneController,
    RobotTransceiver,
    SwarmController,
    VideoScreen,
)
from ceres.make.robot.skills import Electronics, RoboticScience
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_advanced_lab_control_robot() -> Robot:
    return Robot(
        name='Advanced Lab Control Robot',
        tl=12,
        size=RobotSize.SIZE_3,
        locomotion=NoneLocomotion(),
        brain=AdvancedBrain(
            int_upgrade=1,
            bandwidth=4,
            installed_skills=(
                Electronics(remote_ops=2),
                RoboticScience(robotics=1),
            ),
        ),
        manipulators=[],
        options=[
            *default_suite(see=False, improved_transceiver=False),
            VideoScreen(quality='improved'),
            RobotTransceiver(range_km=5000, quality='enhanced'),
            ExternalPower(),
            RoboticDroneController(quality='advanced'),
            AvatarController(quality='basic'),
            SwarmController(quality='enhanced'),
        ],
    )


@pytest.mark.approval
def test_lab_control_robot_advanced(snapshot):
    snap = AnnotatedSnapshot(build_advanced_lab_control_robot().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr188,220 vs source Cr160,000 — 15% source discount untraced, see RIR-002; '
        'SIZE_3 NoneLocomotion removal credit capped at 20% BCC = -Cr80',
    )
    snap.annotate(
        'skills',
        'Ceres shows implied-familiarity Electronics and Robotic Science subspecialties at level 1 '
        '(raw 0 + INT DM+1 from int_upgrade=1); source stat block omits these entries',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
