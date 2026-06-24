"""Approval snapshot for the Rhino robot.

Source: user-supplied stat block + detailed design-tool breakdown.
SIZE_8 Walker TL15 MCr6.8.
"""

import pytest

from ceres.make.robot import (
    Robot,
    RobotSize,
    SelfAwareBrain,
    WalkerLocomotion,
    default_suite,
)
from ceres.make.robot.manipulators import Manipulator
from ceres.make.robot.options import (
    BioscanneSensor,
    DensitometerSensor,
    EncryptionModule,
    EnvironmentProcessor,
    FabricationChamber,
    InjectorNeedle,
    MedicalChamber,
    Medikit,
    NeuralActivitySensor,
    OlfactorySensor,
    RoboticDroneController,
    ScientificToolkit,
    SolarCoating,
    StorageCompartment,
    SwarmController,
    VacuumEnvironmentProtection,
    VideoScreen,
)
from ceres.make.robot.skills import (
    Athletics,
    BrainSoftware,
    Electronics,
    Engineer,
    Investigate,
    LifeScience,
    Mechanic,
    Medic,
    Melee,
    PhysicalScience,
    Recon,
    RoboticScience,
    RobotProfession,
    SpacerProfession,
    Survival,
    Tactics,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_rhino() -> Robot:
    return Robot(
        name='Rhino',
        tl=15,
        size=RobotSize.SIZE_8,
        locomotion=WalkerLocomotion(),
        brain=SelfAwareBrain(
            hardened=True,
            bandwidth=18,
            installed_skills=(
                Athletics(strength=0),
                Athletics(dexterity=0),
                Medic(level=2),
                Investigate(level=2),
                LifeScience(biology=2),
                PhysicalScience(chemistry=2),
                RoboticScience(robotics=2),
                RobotProfession(fabricator=2),
                RobotProfession(robotics=2),
                Electronics(),
                Engineer(),
                Mechanic(),
                Tactics(),
                SpacerProfession(belter=0),
                Melee(),
                Recon(),
                Survival(),
            ),
            installed_software=(
                BrainSoftware(name='Fab Creator/3', bandwidth=3, tl=13, cost=20_000.0),
                BrainSoftware(name='Translator/0', bandwidth=0, tl=9, cost=50.0),
            ),
        ),
        manipulators=[
            Manipulator(),
            Manipulator(),
            Manipulator(size=RobotSize.SIZE_3, str_bonus=1, dex_bonus=6),
            Manipulator(size=RobotSize.SIZE_3, str_bonus=1, dex_bonus=6),
        ],
        options=[
            *default_suite(speak=False, hear=False, improved_transceiver=False, drone=True),
            BioscanneSensor(),
            DensitometerSensor(),
            EncryptionModule(),
            EnvironmentProcessor(),
            *[InjectorNeedle() for _ in range(8)],
            Medikit(quality='advanced'),
            MedicalChamber(
                slots_count=40,
                low_berth='improved',
                reanimation=True,
                species_specific=1,
            ),
            NeuralActivitySensor(),
            OlfactorySensor(quality='advanced'),
            RoboticDroneController(quality='advanced'),
            ScientificToolkit(quality='advanced'),
            SolarCoating(quality='advanced'),
            StorageCompartment(slots_count=8, storage_type='refrigerated'),
            SwarmController(quality='advanced'),
            VacuumEnvironmentProtection(),
            VideoScreen(quality='advanced'),
            FabricationChamber(quality='enhanced', slots_count=64),
        ],
    )


@pytest.mark.approval
def test_rhino(snapshot):
    snap = AnnotatedSnapshot(build_rhino().build_spec().model_dump(mode='json'))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
