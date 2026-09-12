"""Approval snapshot for the Marshal Mk II robot.

Original Ceres design (not source-derived): a TL12 law-enforcement walker built to
make arrests on its own authority and subdue resisting suspects without killing them.
"""

import pytest

from ceres.make.robot import Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.brain import AdvancedBrain
from ceres.make.robot.options import (
    AgilityEnhancement,
    EncryptionModule,
    FireExtinguisher,
    ForensicToolkit,
    IncreasedArmour,
    LightIntensifierSensor,
    Medikit,
    OlfactorySensor,
    PowerPack,
    ReconSensor,
    RobotTransceiver,
    StorageCompartment,
    ThermalSensor,
    VideoScreen,
    WeaponMount,
)
from ceres.make.robot.skills import Athletics, GunCombat, Investigate, Medic, Melee, Persuade, Tactics
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_marshal() -> Robot:
    """Note: Original Ceres design, not from a published stat block.

    TL12 riot and arrest walker. The hardened Advanced brain caps bandwidth at 6
    (base 2 plus the largest TL12 upgrade) and allows only two zero-bandwidth
    packages, which sets the whole skill list. One of those six points buys INT+1
    rather than a skill: at Cr9,000 it lifts every INT-based skill by one, which is
    a better return than any single package. Melee (unarmed) 1, Gun Combat (energy) 1,
    Investigate 0, Tactics (military) 1 and Persuade 0 take one point each, and
    Athletics (strength) and Medic fill the two zero-bandwidth places.

    Melee is bought at 1 rather than 2 because STR carries it: with STR 15 arms the
    effective reading is still 4, so the second level would buy one point for a whole
    bandwidth. That point goes to Investigate instead, which the INT upgrade lifts to
    an effective 1 for the price of a level-0 package.

    Gun Combat is held at 1 to pay for the INT upgrade: it is DEX-based and gains
    nothing from INT, so the trade buys levels in Tactics, Persuade and Medic at the
    cost of one level of marksmanship. Recon comes from the advanced Recon Sensor as
    hardware, so it costs no bandwidth — and, being a hardware grant, it is not
    raised by INT either.

    The marksmanship comes back from hardware instead. The robot carries a pair of
    Size 3 DEX 12 gun arms alongside its STR 15 general arms, so DEX skills read
    3/2 — DM+2 from the nimble arms, DM+1 from the general ones, highest first. Which
    applies to a given shot is a table decision, per refs/robot/09_manipulators.md and
    RIR-013, and the spec carries a note saying so; position names no particular arm.

    DEX 12 is the efficient point: enhancement costs Size × (increase)² × Cr200, so
    DEX 13 and 14 pay more for the same DM+2.
    The arms stay at their default STR 5, which is ample for a pistol and keeps them
    cheap; per RIR-013 they do not raise the general Athletics figures.

    The default suite trades its 5km transceiver for a Drone Interface, both being
    zero-slot items included in the base chassis cost (refs/robot/10_default_suite.md):
    the 50km transceiver already covers the radio, and remote override matters more.

    Both mounts are small, which per refs/robot/32_fire_extinguisher.md is the size a
    pistol-equivalent weapon needs and the minimum a Size 3 manipulator can carry
    while still lending its DEX modifier.

    The arrest itself is a grapple (refs/core/03_combat.md): an opposed Melee
    (unarmed) check whose winner may force a suspect prone or drag them three metres,
    which is the whole job. Melee may use STR or DEX at the attacker's choice, so it
    gets a row per characteristic: Melee (STR, Unarmed) 5/1 on the STR 15 general arms
    against the STR 5 gun arms, and Melee (DEX, Unarmed) 4/3 the other way round. The
    two characteristics rank the arms in opposite orders, which is exactly why the
    rows are not collapsed into one.

    The enhanced forensic toolkit is the TL12 grade, supporting scene work up to skill
    2. Toolkits cap rather than grant, so it is only worth its four slots alongside the
    Investigate package above — which is exactly the skill level the toolkit supports.

    Both mounted weapons are energy so one Gun Combat speciality covers the stunner
    and the lethal backup. Weapon fits are free text: Ceres models the mounts, their
    slot cost and the arms, but not the weapons — and deliberately not which arm
    holds which weapon, which is the Referee's call.

    One additional power pack doubles endurance to 216 hours, so a week-long patrol
    needs no recharge (refs/robot/07_chassis_options.md). It costs four slots, which a
    Size 6 chassis can afford, and grants Athletics (endurance) 1 as a side effect of
    the larger power system. Efficiency would buy the same endurance for no slots, but
    at 50% of Base Chassis Cost it is five times the price on a walker and grants no
    skill.
    """
    return Robot(
        name='Marshal Mk II',
        tl=12,
        size=RobotSize.SIZE_6,
        locomotion=WalkerLocomotion(),
        brain=AdvancedBrain(
            brain_tl=12,
            bandwidth=6,
            hardened=True,
            int_upgrade=1,
            installed_skills=(
                Melee(unarmed=1),
                GunCombat(energy=1),
                Investigate(),
                Tactics(military=1),
                Persuade(),
                Athletics(strength=0),
                Medic(),
            ),
        ),
        base_manipulators=[
            Manipulator(str_bonus=4, dex_bonus=2),
            Manipulator(str_bonus=4, dex_bonus=2),
        ],
        additional_manipulators=[
            Manipulator(size=RobotSize.SIZE_3, dex_bonus=5),
            Manipulator(size=RobotSize.SIZE_3, dex_bonus=5),
        ],
        options=[
            PowerPack(),
            # The 5km default-suite transceiver is superseded by the 50km one below, so
            # it is substituted for a free Drone Interface: an armed robot that arrests
            # on its own authority needs a way for a human to take control.
            *default_suite(improved_transceiver=False, drone=True),
            IncreasedArmour(additional=10),
            AgilityEnhancement(level=1),
            ReconSensor(quality='advanced'),
            LightIntensifierSensor(),
            ThermalSensor(),
            OlfactorySensor(quality='improved'),
            Medikit(quality='enhanced'),
            StorageCompartment(slots_count=4),
            RobotTransceiver(range_km=50),
            EncryptionModule(),
            FireExtinguisher(),
            ForensicToolkit(quality='enhanced'),
            VideoScreen(quality='improved'),
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
def test_marshal(snapshot):
    snap = AnnotatedSnapshot(build_marshal().build_spec().model_dump(mode='json'))
    snap.annotate(
        'weapons',
        'Attacks are free text — Ceres has no weapon catalogue, so mount size and '
        'slot cost are validated but the weapon stats are not',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
