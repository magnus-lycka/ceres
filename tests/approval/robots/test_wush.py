"""Approval snapshot for the Wush robot.

Source: user-supplied stat block — Wush, SIZE_2 TL15 Wheels ATV, PrimitiveBrain (clean).
Cost matches source exactly (Cr850).
"""

import pytest

from ceres.make.robot import Manipulator, PrimitiveBrain, Robot, RobotSize, WheelsAtvLocomotion, default_suite
from ceres.make.robot.options import DomesticCleaningEquipment, StorageCompartment
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_wush() -> Robot:
    """Source: user-supplied stat block — Wush, SIZE_2 TL15 Wheels ATV, PrimitiveBrain (clean)."""
    return Robot(
        name='Wush',
        tl=15,
        size=RobotSize.SIZE_2,
        locomotion=WheelsAtvLocomotion(),
        brain=PrimitiveBrain(function='clean'),
        manipulators=[Manipulator(), Manipulator()],
        options=[
            *default_suite(
                see=True,
                speak=True,
                hear=True,
                wireless=False,
                improved_transceiver=True,
                drone=True,
            ),
            DomesticCleaningEquipment(size='small'),
            StorageCompartment(slots_count=1),
        ],
    )


@pytest.mark.approval
def test_wush(snapshot):
    snap = AnnotatedSnapshot(build_wush().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
