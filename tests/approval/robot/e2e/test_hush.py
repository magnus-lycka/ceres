"""Approval snapshot for the Hush robot.

Source: user-supplied stat block — Hush, SIZE_2 TL15 Walker.
Partial build: speed and agility modifications not yet implemented.
"""

import pytest

from ceres.make.robot import BasicBrain, Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.options import (
    AuditorySensor,
    CamouflageAudible,
    CamouflageOlfactory,
    CamouflageVisual,
    GeckoGrippers,
    NavigationSystem,
    PrisSensor,
    RobotTransceiver,
    VoderSpeaker,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_hush() -> Robot:
    """Note: Partial Hush — speed and agility modifications not yet implemented.

    Speed shown as 5m (source: 10m) and endurance as 144h (source: 173h).
    Tactical Speed Reduction is incompatible with Agility Enhancement per rules;
    source combination cannot be reproduced.
    Source: user-supplied stat block — Hush, SIZE_2 TL15 Walker.
    """
    return Robot(
        name='Hush',
        tl=15,
        size=RobotSize.SIZE_2,
        locomotion=WalkerLocomotion(),
        brain=BasicBrain(function='recon'),
        manipulators=[Manipulator(), Manipulator()],
        options=[
            PrisSensor(),
            AuditorySensor(quality='broad_spectrum'),
            VoderSpeaker(quality='broad_spectrum'),
            *default_suite(
                drone=True,
                see=False,
                hear=False,
                speak=False,
                wireless=False,
                improved_transceiver=False,
            ),
            CamouflageVisual(quality='enhanced'),
            CamouflageAudible(quality='advanced'),
            CamouflageOlfactory(quality='advanced'),
            GeckoGrippers(),
            NavigationSystem(quality='basic'),
            RobotTransceiver(range_km=5000, quality='advanced'),
        ],
    )


@pytest.mark.approval
def test_hush(snapshot):
    snap = AnnotatedSnapshot(build_hush().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr12,700 vs source Cr17,000 — gap ~Cr4,300 from unimplemented speed/agility modifications',
    )
    snap.annotate(
        'speed',
        'Ceres 5m vs source 10m — speed_reduction=2 + AgilityEnhancement incompatible per rules; '
        'source combination cannot be reproduced',
    )
    snap.annotate(
        'endurance',
        'Ceres 144h vs source 173h — endurance boost from speed_reduction not applied '
        '(incompatible with AgilityEnhancement)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
