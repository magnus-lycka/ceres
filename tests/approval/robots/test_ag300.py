"""Approval snapshot for the AG300 Agricultural Worker robot.

Source: refs/robot/105_utility_robots.md
"""

import pytest

from ceres.make.robot import BasicBrain, Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.options import (
    AgriculturalEquipment,
    DroneInterface,
    LightIntensifierSensor,
    NavigationSystem,
    OlfactorySensor,
    StorageCompartment,
    ThermalSensor,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_ag300() -> Robot:
    return Robot(
        name='AG300 Agricultural Worker',
        tl=10,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(speed_increase=1),
        brain=BasicBrain(function='labourer'),
        manipulators=[
            Manipulator(),
            Manipulator(),
            Manipulator(size=RobotSize.SIZE_4),
            Manipulator(size=RobotSize.SIZE_4),
        ],
        options=[
            *default_suite(),
            DroneInterface(),
            AgriculturalEquipment(size='medium'),
            LightIntensifierSensor(quality='advanced'),
            NavigationSystem(quality='basic'),
            OlfactorySensor(quality='improved'),
            StorageCompartment(slots_count=8, storage_type='refrigerated'),
            ThermalSensor(),
        ],
    )


@pytest.mark.approval
def test_ag300(snapshot):
    snap = AnnotatedSnapshot(build_ag300().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr24,850 vs source Cr20,000 — discrepancy untraced, see RIR-002',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
