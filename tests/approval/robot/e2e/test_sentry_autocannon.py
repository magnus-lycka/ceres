"""Approval snapshot for the Sentry Autocannon robot.

Original Ceres design (not source-derived): a stationary autonomous weapon with
the sensors and programming needed to detect, identify, and engage targets.
"""

import pytest

from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize, default_suite
from ceres.make.robot.options import IncreasedArmour, PrisSensor, ReconSensor, ThermalSensor, WeaponMount
from ceres.make.robot.skills import HeavyWeapons, Tactics
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_sentry_autocannon() -> Robot:
    """Note: Original Ceres design, not from a published stat block.

    Ceres models the vehicle weapon mount but not the autocannon, ammunition,
    fire-control system, or autoloader as priced parts. The Cr62,300 robot price
    therefore excludes the Cr10,000 light autocannon and its Cr1,000 500-round
    magazine; approximate equipped cost is Cr73,300. No Locomotion means the
    emplacement cannot translate; the separate weapon servo still gives its
    turret full traverse.
    """
    return Robot(
        name='Sentry Autocannon',
        tl=12,
        size=RobotSize.SIZE_5,
        locomotion=NoneLocomotion(),
        brain=AdvancedBrain(
            brain_tl=12,
            hardened=True,
            installed_skills=(
                HeavyWeapons(vehicle=1),
                Tactics(military=1),
            ),
        ),
        base_manipulators=[],
        options=[
            IncreasedArmour(additional=24),
            *default_suite(speak=False, drone=True),
            ReconSensor(quality='advanced'),
            PrisSensor(),
            ThermalSensor(),
            WeaponMount(size='vehicle'),
        ],
        attacks=[
            'Light Autocannon (6D, Auto 3, 500 rounds; 360° turreted vehicle mount)',
        ],
    )


def test_sentry_autocannon_uses_every_spare_slot_for_armour() -> None:
    robot = build_sentry_autocannon()

    assert robot.remaining_slots == 0
    assert [(trait.name, trait.value) for trait in robot.traits if trait.name == 'Armour'] == [('Armour', '+28')]


def test_sentry_autocannon_mount_can_traverse() -> None:
    robot = build_sentry_autocannon()

    assert robot.attacks == ['Light Autocannon (6D, Auto 3, 500 rounds; 360° turreted vehicle mount)']


@pytest.mark.approval
def test_sentry_autocannon(snapshot):
    snap = AnnotatedSnapshot(build_sentry_autocannon().build_spec().model_dump(mode='json'))
    snap.annotate(
        'weapons',
        'The attack is free text: Ceres validates the vehicle mount but does not '
        'model or price the autocannon, ammunition, fire control, or autoloader',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
