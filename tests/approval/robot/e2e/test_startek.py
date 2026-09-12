"""Approval snapshot for the StarTek robot.

Source: refs/robot/99_startek.md — SIZE_5 TL14, Grav+Walker.
Manipulators: 2× (STR 12 DEX 8), 1× (STR 5 DEX 12).
"""

import pytest

from ceres.make.robot import GravLocomotion, Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.brain import VeryAdvancedBrain
from ceres.make.robot.options import (
    Efficiency,
    IncreasedArmour,
    Medikit,
    PrisSensor,
    RadiationEnvironmentProtection,
    SecondaryLocomotion,
    StarshipEngineeringToolkit,
    VacuumEnvironmentProtection,
    WeaponMount,
)
from ceres.make.robot.skills import Athletics, Electronics, Engineer, Explosives, GunCombat, Mechanic, Medic
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_startek() -> Robot:
    """Source: refs/robot/99_startek.md — SIZE_5 TL14, Grav+Walker.

    Athletics (Strength): pkg level=0 (BW=0) + STR DM+2 = 2 (effective STR 12 from str_bonus=3).
    Gun Combat: pkg level=0 no speciality (BW=0) + DEX DM+0 = 0 (source: 'Gun Combat 0').
    """
    return Robot(
        name='StarTek',
        tl=14,
        size=RobotSize.SIZE_5,
        locomotion=GravLocomotion(),
        brain=VeryAdvancedBrain(
            brain_tl=14,
            int_upgrade=1,
            installed_skills=(
                Athletics(strength=0),
                Electronics(level=1),
                Engineer(level=1),
                Explosives(),
                GunCombat(),
                Mechanic(level=1),
                Medic(),
            ),
        ),
        base_manipulators=[
            Manipulator(str_bonus=3),
            Manipulator(str_bonus=3),
        ],
        additional_manipulators=[
            Manipulator(size=RobotSize.SIZE_3, dex_bonus=4),
        ],
        options=[
            IncreasedArmour(additional=6),
            Efficiency(),
            SecondaryLocomotion(locomotion=WalkerLocomotion()),
            RadiationEnvironmentProtection(),
            VacuumEnvironmentProtection(),
            PrisSensor(),
            Medikit(quality='enhanced'),
            StarshipEngineeringToolkit(quality='advanced'),
            WeaponMount(size='small'),
            *default_suite(),
        ],
    )


@pytest.mark.approval
def test_startek(snapshot):
    snap = AnnotatedSnapshot(build_startek().build_spec().model_dump(mode='json'))
    snap.annotate(
        'skills',
        "Gun Combat reads 2/0 where the published sheet shows 'Gun Combat 0'. "
        'Deliberate (RIR-013): the handbook text for this very robot says the stunner '
        "is installed in the Size 3 manipulator 'to take advantage of the small "
        "manipulator's DEX DM+2', which the printed skill line omits. Readings are "
        'ordered highest first and position names no particular arm, so the published '
        'figure is the 0 — what the DEX 8 base arms give.',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
