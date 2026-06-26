"""Approval snapshot for the Munin robot.

Source: user-supplied stat block — Munin, SIZE_1 TL15 Grav.
AgilityEnhancement(4) and Efficiency inferred (not in source options list).
"""

import pytest

from ceres.make.robot import GravLocomotion, Robot, RobotSize
from ceres.make.robot.brain import AdvancedBrain
from ceres.make.robot.options import (
    ActiveCamouflage,
    AgilityEnhancement,
    AvatarReceiver,
    CamouflageAudible,
    CamouflageOlfactory,
    Efficiency,
    EncryptionModule,
    EnvironmentProcessor,
    GeckoGrippers,
    InjectorNeedle,
    OlfactorySensor,
    ParasiticLink,
    PrisSensor,
    RobotTransceiver,
    VacuumEnvironmentProtection,
    VoderSpeaker,
    WirelessDataLink,
)
from ceres.make.robot.skills import Recon
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_munin() -> Robot:
    """Note: Partial Munin — cost gap Cr42,170 vs source Cr140,000 unresolved.

    AgilityEnhancement(4) and Efficiency inferred (not in source options list).
    GravLocomotion(speed_increase=2) inferred for 12m speed and 76h endurance.
    Stealth 4 from ActiveCamouflage hardware grant; Recon 1 from brain pkg + EnvironmentProcessor.
    Source: user-supplied stat block — Munin, SIZE_1 TL15 Grav.
    """
    return Robot(
        name='Munin',
        tl=15,
        size=RobotSize.SIZE_1,
        locomotion=GravLocomotion(speed_increase=2),
        manipulators=[],
        brain=AdvancedBrain(
            brain_tl=15,
            hardened=True,
            installed_skills=(Recon(level=1),),
        ),
        options=[
            AgilityEnhancement(level=4),
            Efficiency(),
            ActiveCamouflage(),
            AvatarReceiver(),
            CamouflageAudible(quality='advanced'),
            CamouflageOlfactory(quality='advanced'),
            EncryptionModule(),
            EnvironmentProcessor(),
            GeckoGrippers(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            OlfactorySensor(quality='advanced'),
            ParasiticLink(),
            PrisSensor(),
            RobotTransceiver(range_km=5000, quality='advanced'),
            VacuumEnvironmentProtection(),
            VoderSpeaker(quality='broad_spectrum'),
            WirelessDataLink(),
        ],
    )


@pytest.mark.approval
def test_munin(snapshot):
    snap = AnnotatedSnapshot(build_munin().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr97,630 vs source Cr140,000 — gap Cr42,170 unresolved; '
        'source likely omits AgilityEnhancement(4) and Efficiency from options list',
    )
    snap.annotate(
        'endurance',
        'Ceres 76h (truncates 76.8h) vs source 77h (rounds up)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
