"""Approval snapshots for Robot JSON serialization.

Design inputs (name, tl, size, locomotion type, brain type) must survive a round-trip.
Derived values (base_armour, base_endurance, base_chassis_cost, traits, slot counts)
must NOT appear in the serialised JSON — their absence is captured by the snapshot;
their values are tracked via annotations.
"""

import pytest

from ceres.make.robot import (
    AdvancedBrain,
    NoneLocomotion,
    PrimitiveBrain,
    Robot,
    RobotSize,
    WheelsLocomotion,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


@pytest.mark.approval
def test_wheels_primitive_serialization(snapshot):
    """Minimal robot (SIZE_3, wheels, primitive brain) round-trips correctly."""
    robot = Robot(name='Test', tl=8, size=RobotSize.SIZE_3, locomotion=WheelsLocomotion(), brain=PrimitiveBrain())
    restored = Robot.model_validate(robot.model_dump())
    snap = AnnotatedSnapshot(robot.model_dump(mode='json'))
    snap.annotate('base_armour', str(robot.base_armour))
    snap.annotate('base_endurance_hours', str(round(robot.base_endurance, 2)))
    snap.annotate('base_chassis_cost', str(robot.base_chassis_cost))
    snap.annotate('available_slots', str(robot.available_slots))
    snap.annotate('round_trip_tl', str(restored.tl))
    snap.annotate('round_trip_locomotion', type(restored.locomotion).__name__)
    snap.annotate('round_trip_brain', type(restored.brain).__name__)
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_none_locomotion_advanced_brain_serialization(snapshot):
    """Stationary robot (SIZE_1, no locomotion, advanced brain) preserves discriminated unions."""
    robot = Robot(name='Lab', tl=12, size=RobotSize.SIZE_1, locomotion=NoneLocomotion(), brain=AdvancedBrain())
    restored = Robot.model_validate(robot.model_dump())
    snap = AnnotatedSnapshot(robot.model_dump(mode='json'))
    snap.annotate('base_armour', str(robot.base_armour))
    snap.annotate('round_trip_locomotion', type(restored.locomotion).__name__)
    snap.annotate('round_trip_brain', type(restored.brain).__name__)
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
