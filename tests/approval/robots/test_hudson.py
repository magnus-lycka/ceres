"""Approval snapshot for the Hudson robot.

Source: user-supplied stat block — Hudson, SIZE_4 TL15 Walker.
"""

import pytest

from ceres.make.robot import AdvancedBrain, Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.options import (
    Autochef,
    OlfactorySensor,
    StorageCompartment,
    StylistToolkit,
    VideoScreen,
)
from ceres.make.robot.skills import Admin, Drive, Flyer, Pilot, Steward
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_hudson() -> Robot:
    return Robot(
        name='Hudson',
        tl=15,
        size=RobotSize.SIZE_4,
        locomotion=WalkerLocomotion(),
        brain=AdvancedBrain(
            int_upgrade=1,
            bandwidth=4,
            installed_skills=(
                Admin(level=1),
                Drive(),
                Flyer(),
                Pilot(small_craft=1),
                Steward(level=1),
            ),
        ),
        manipulators=[Manipulator(), Manipulator()],
        options=[
            *default_suite(see=True, hear=True, improved_transceiver=True, drone=True, speak=False, wireless=False),
            OlfactorySensor(quality='improved'),
            Autochef(quality='improved'),
            StylistToolkit(),
            StorageCompartment(slots_count=1, storage_type='refrigerated'),
            VideoScreen(quality='improved'),
        ],
    )


@pytest.mark.approval
def test_hudson(snapshot):
    snap = AnnotatedSnapshot(build_hudson().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr43,300 vs source Cr43,000 — Cr300 discrepancy untraced, likely source rounding',
    )
    snap.annotate(
        'skills',
        'Ceres shows implied-familiarity Pilot subspecialties (Capital Ships, Spacecraft) at level 1 '
        'from DEX DM+1 boost; source stat block omits these entries',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
