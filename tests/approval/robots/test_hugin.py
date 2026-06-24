"""Approval snapshot for the Hugin robot.

Source: user-supplied stat block — Hugin, SIZE_1 TL15 Grav VSM.
Partial build: Flyer(Grav) 4, Stealth 2, Navigation 1, Recon 1 from source not reproduced.
"""

import pytest

from ceres.make.robot import GravLocomotion, Robot, RobotSize
from ceres.make.robot.brain import AdvancedBrain
from ceres.make.robot.options import (
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
    SolarCoating,
    VacuumEnvironmentProtection,
    VehicleSpeedModification,
    VoderSpeaker,
    WirelessDataLink,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_hugin() -> Robot:
    """Note: Partial Hugin — cost gap Cr45,090 vs source Cr130,000 unresolved.

    AgilityEnhancement(4) and Efficiency inferred (not in source options list).
    Flyer(Grav) 4 skill from source not reproduced: brain pkg at level 4 costs Cr1M (not viable).
    Stealth 2 from source not reproduced: origin unexplained from listed options.
    Navigation 1 and Recon 1 from source not reproduced (no NavigationSystem in source options).
    Source: user-supplied stat block — Hugin, SIZE_1 TL15 Grav VSM.
    """
    return Robot(
        name='Hugin',
        tl=15,
        size=RobotSize.SIZE_1,
        locomotion=GravLocomotion(),
        manipulators=[],
        brain=AdvancedBrain(
            brain_tl=15,
            hardened=True,
        ),
        options=[
            AgilityEnhancement(level=4),
            Efficiency(),
            VehicleSpeedModification(),
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
            OlfactorySensor(quality='advanced'),
            ParasiticLink(),
            PrisSensor(),
            SolarCoating(quality='advanced'),
            RobotTransceiver(range_km=5000, quality='advanced'),
            VacuumEnvironmentProtection(),
            VoderSpeaker(quality='broad_spectrum'),
            WirelessDataLink(),
        ],
    )


@pytest.mark.approval
def test_hugin(snapshot):
    snap = AnnotatedSnapshot(build_hugin().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr84,710 vs source Cr130,000 — gap Cr45,090 unresolved (partial build)',
    )
    snap.annotate(
        'skills',
        'Source shows Flyer(Grav) 4, Stealth 2, Navigation 1, Recon 1 — '
        'not reproduced: Flyer(Grav) 4 would require Cr1M brain pkg; '
        'Stealth 2 and Navigation 1 origins unexplained from source options list',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
