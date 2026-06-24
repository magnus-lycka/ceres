"""Approval snapshot for the Domestic Servant robot.

Source: refs/robot/109_domestic_servant.md
"""

import pytest

from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion, default_suite
from ceres.make.robot.options import (
    DecreasedResiliency,
    DomesticCleaningEquipment,
    ReconSensor,
    StorageCompartment,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_domestic_servant() -> Robot:
    return Robot(
        name='Domestic Servant',
        tl=8,
        size=RobotSize.SIZE_3,
        locomotion=WheelsLocomotion(speed_reduction=1),
        brain=PrimitiveBrain(function='clean'),
        manipulators=[],
        options=[
            *default_suite(),
            DomesticCleaningEquipment(size='small'),
            ReconSensor(quality='improved'),
            StorageCompartment(slots_count=4),
            DecreasedResiliency(hit_reduction=2),
        ],
    )


@pytest.mark.approval
def test_domestic_servant(snapshot):
    snap = AnnotatedSnapshot(build_domestic_servant().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr860 vs source Cr500 — source uses editorial rounding; '
        'Ceres: BCC=Cr800, capped manipulator removal credit (20% BCC = -Cr160)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
