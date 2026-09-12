"""Approval snapshot for the Deputy robot.

Original Ceres design (not source-derived): the cheap patrol tier below the
Marshal Mk II — human-sized, non-lethal only, and no bandwidth to spare.
"""

import pytest

from ceres.make.robot import Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.brain import AdvancedBrain
from ceres.make.robot.options import (
    CuttingTorch,
    EncryptionModule,
    FireExtinguisher,
    IncreasedArmour,
    LightIntensifierSensor,
    Medikit,
    PowerPack,
    ReconSensor,
    StorageCompartment,
    WeaponMount,
)
from ceres.make.robot.skills import Athletics, GunCombat, Medic, Melee
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_deputy() -> Robot:
    """Note: Original Ceres design, not from a published stat block.

    TL12 foot-patrol unit, the cheap tier below the Marshal Mk II. It is armed the same
    way; what it lacks is judgement, aim and armour. Its Advanced brain
    is left at base bandwidth 2, which is the whole design constraint: one level in
    Melee (unarmed) and one in Gun Combat (energy) spend it, and Athletics (strength)
    and Medic take the two zero-bandwidth places. There is no room for Tactics or
    Persuade, so the Deputy detains and calls for a Marshal rather than deciding
    anything itself.

    It carries the same stunner and laser pistol as the Marshal, one to each of a
    second pair of Size 3 arms at DEX 9 — the same idea as the Marshal's gun arms but
    a cheaper DM+1 rather than DM+2, which is most of the difference between the tiers.
    Both weapons are energy, so the single Gun Combat (energy) package covers the pair.
    Weapon fits are free text: Ceres models the mounts and their slot cost, not the
    weapons in them.

    The fire extinguisher and improved cutting torch are standard kit for a unit that
    attends incidents rather than only fights: forcing entry, freeing people from
    wreckage, damping down what it finds. The improved torch is the best available at
    TL12, the advanced one needing TL13. Note the torch can be improvised as a melee
    weapon for 3D AP 4, so the 'nothing lethal' description holds only for what the
    Deputy is armed with, not for what it carries.

    One additional power pack doubles endurance to 216 hours, so a week-long patrol
    needs no recharge (refs/robot/07_chassis_options.md). It costs two of the Deputy's
    remaining slots, which is most of what it had left, and grants
    Athletics (endurance) 1 as a side effect of the larger power system.
    """
    return Robot(
        name='Deputy',
        tl=12,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(),
        brain=AdvancedBrain(
            brain_tl=12,
            hardened=True,
            installed_skills=(
                Melee(unarmed=1),
                GunCombat(energy=1),
                Athletics(strength=0),
                Medic(),
            ),
        ),
        base_manipulators=[
            Manipulator(),
            Manipulator(),
        ],
        additional_manipulators=[
            Manipulator(size=RobotSize.SIZE_3, dex_bonus=2),
            Manipulator(size=RobotSize.SIZE_3, dex_bonus=2),
        ],
        options=[
            PowerPack(),
            *default_suite(),
            CuttingTorch(quality='improved'),
            FireExtinguisher(),
            IncreasedArmour(additional=4),
            ReconSensor(quality='enhanced'),
            LightIntensifierSensor(),
            Medikit(quality='basic'),
            StorageCompartment(slots_count=2),
            EncryptionModule(),
            WeaponMount(size='small'),
            WeaponMount(size='small'),
        ],
        attacks=[
            'Stunner (small mount)',
            'Laser pistol (small mount)',
            'Grapple (opposed Melee (unarmed); 2 + Effect, ignores armour)',
        ],
    )


@pytest.mark.approval
def test_deputy(snapshot):
    snap = AnnotatedSnapshot(build_deputy().build_spec().model_dump(mode='json'))
    snap.annotate(
        'weapons',
        'Attacks are free text — Ceres has no weapon catalogue, so mount size and '
        'slot cost are validated but the weapon stats are not',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
