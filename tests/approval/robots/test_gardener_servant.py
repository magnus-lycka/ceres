"""Approval snapshot for the Gardener Servant robot.

Source: refs/robot/121_hiver.md
"""

import pytest

from ceres.make.robot import Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.brain import AdvancedBrain
from ceres.make.robot.options import (
    AgriculturalEquipment,
    AuditorySensor,
    Autobar,
    Autochef,
    DomesticCleaningEquipment,
    Medikit,
    OlfactorySensor,
    PrisSensor,
    StorageCompartment,
)
from ceres.make.robot.skills import Animals, Medic, RobotProfession, Steward
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_gardener_servant() -> Robot:
    """Note: Gardener Servant — endurance 129h (Ceres) vs 130h (source rounds 129.6 up).

    Source: refs/robot/121_hiver.md — Gardener Servant, SIZE_5 TL15 Walker.
    """
    return Robot(
        name='Gardener Servant',
        tl=15,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(speed_increase=1),
        brain=AdvancedBrain(
            brain_tl=15,
            int_upgrade=1,
            bandwidth=6,
            installed_skills=(
                Animals(veterinary=1),
                Medic(level=1),
                RobotProfession(cleaning=1),
                RobotProfession(gardening=1),
                Steward(level=1),
            ),
        ),
        manipulators=[Manipulator(), Manipulator(), Manipulator(), Manipulator()],
        legs=[Manipulator(), Manipulator()],
        options=[
            *default_suite(speak=False, hear=False, drone=True),
            AgriculturalEquipment(size='small'),
            AuditorySensor(quality='broad_spectrum'),
            Autobar(quality='enhanced'),
            Autochef(quality='enhanced'),
            DomesticCleaningEquipment(size='small'),
            Medikit(quality='enhanced'),
            OlfactorySensor(quality='advanced'),
            PrisSensor(),
            StorageCompartment(slots_count=3, storage_type='refrigerated'),
        ],
    )


@pytest.mark.approval
def test_gardener_servant(snapshot):
    snap = AnnotatedSnapshot(build_gardener_servant().build_spec().model_dump(mode='json'))
    snap.annotate(
        'endurance',
        'Ceres 129h (truncates 129.6h) vs source 130h (rounds up)',
    )
    snap.annotate(
        'cost',
        'Ceres ~Cr86,100 vs source Cr85,000 — gap ~Cr1,100 unresolved (possible source rounding)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
