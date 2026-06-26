"""Approval snapshot for the Mimer robot.

Source: user-supplied stat block — Mimer, SIZE_1 TL15 None locomotion.
"""

import pytest

from ceres.make.robot import (
    NoneLocomotion,
    Robot,
    RobotSize,
    SelfAwareBrain,
    UniversalTranslator,
    default_suite,
)
from ceres.make.robot.options import (
    AvatarController,
    CamouflageAudible,
    CamouflageVisual,
    EncryptionModule,
    EnvironmentProcessor,
    InjectorNeedle,
    ParasiticLink,
    PrisSensor,
    SelfMaintenanceEnhancement,
    SwarmController,
    VacuumEnvironmentProtection,
)
from ceres.make.robot.skills import (
    Admin,
    Advocate,
    Broker,
    Electronics,
    Engineer,
    Flyer,
    Investigate,
    LanguageVilani,
    Mechanic,
    Medic,
    Navigation,
    Recon,
    RoboticScience,
    Stealth,
    Steward,
    Tactics,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_mimer() -> Robot:
    return Robot(
        name='Mimer',
        tl=15,
        size=RobotSize.SIZE_1,
        locomotion=NoneLocomotion(),
        brain=SelfAwareBrain(
            hardened=True,
            bandwidth=20,
            installed_software=(UniversalTranslator(),),
            installed_skills=(
                Recon(level=2),
                Stealth(level=1),
                Investigate(level=2),
                Electronics(),
                Broker(level=3),
                Admin(level=1),
                Advocate(level=1),
                Engineer(),
                Mechanic(),
                Medic(level=2),
                Steward(),
                RoboticScience(robotics=2),
                LanguageVilani(),
                Tactics(),
                Flyer(),
                Navigation(),
            ),
        ),
        manipulators=[],
        options=[
            *default_suite(),
            AvatarController(quality='enhanced'),
            SwarmController(quality='advanced'),
            CamouflageAudible(quality='advanced'),
            CamouflageVisual(quality='advanced'),
            EncryptionModule(),
            EnvironmentProcessor(),
            *[InjectorNeedle() for _ in range(7)],
            ParasiticLink(),
            PrisSensor(),
            SelfMaintenanceEnhancement(quality='improved'),
            VacuumEnvironmentProtection(),
        ],
    )


@pytest.mark.approval
def test_mimer(snapshot):
    snap = AnnotatedSnapshot(build_mimer().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
