"""Approval snapshot for robot default suite composition.

refs/robot/10_default_suite.md — five zero-cost zero-slot items included in every robot.
"""

import pytest

from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion, default_suite
from ceres.make.robot.options import DroneInterface
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def _robot(**kwargs) -> Robot:
    return Robot(name='T', tl=8, size=RobotSize.SIZE_3, locomotion=WheelsLocomotion(), brain=PrimitiveBrain(), **kwargs)


@pytest.mark.approval
def test_robot_spec_with_default_suite(snapshot):
    """Default suite items appear in spec options row; they add zero slots and zero cost."""
    robot = _robot()
    empty = _robot(options=[])
    snap = AnnotatedSnapshot(robot.build_spec().model_dump(mode='json'))
    snap.annotate('used_slots', str(robot.used_slots))
    snap.annotate('default_suite_cost_impact', str(robot.total_cost - empty.total_cost))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_robot_spec_with_drone_default_suite(snapshot):
    """Drone flag swaps WirelessDataLink for DroneInterface; zero cost and slot impact unchanged."""
    robot = _robot(options=default_suite(wireless=False, drone=True))
    empty = _robot(options=[])
    snap = AnnotatedSnapshot(robot.build_spec().model_dump(mode='json'))
    snap.annotate('used_slots', str(robot.used_slots))
    snap.annotate('default_suite_cost_impact', str(robot.total_cost - empty.total_cost))
    snap.annotate('has_drone_interface', str(any(isinstance(o, DroneInterface) for o in robot.options)))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
