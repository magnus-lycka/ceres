"""Approval snapshot for the Gonzales robot.

Source: user-supplied stat block — Gonzales, SIZE_4 TL15 Wheels ATV.
"""

import pytest

from ceres.make.robot import BasicBrain, Manipulator, Robot, RobotSize, WheelsAtvLocomotion, default_suite
from ceres.make.robot.options import (
    AgilityEnhancement,
    AuditorySensor,
    CamouflageAudible,
    CamouflageOlfactory,
    CamouflageVisual,
    Efficiency,
    IncreasedArmour,
    NavigationSystem,
    PrisSensor,
    RobotTransceiver,
    StorageCompartment,
    VehicleSpeedModification,
    VoderSpeaker,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_gonzales() -> Robot:
    """Note: Partial Gonzales — cost gap Cr2,500 vs source Cr27,000 unresolved.

    Source: user-supplied stat block — Gonzales, SIZE_4 TL15 Wheels ATV.
    """
    return Robot(
        name='Gonzales',
        tl=15,
        size=RobotSize.SIZE_4,
        locomotion=WheelsAtvLocomotion(),
        brain=BasicBrain(function='locomotion'),
        manipulators=[Manipulator(size=RobotSize.SIZE_3), Manipulator(size=RobotSize.SIZE_3)],
        options=[
            IncreasedArmour(additional=4),
            AgilityEnhancement(level=2),
            Efficiency(),
            PrisSensor(),
            AuditorySensor(quality='broad_spectrum'),
            VoderSpeaker(quality='broad_spectrum'),
            *default_suite(
                drone=True,
                see=False,
                hear=False,
                speak=False,
                wireless=False,
                improved_transceiver=False,
            ),
            CamouflageVisual(quality='enhanced'),
            CamouflageAudible(quality='advanced'),
            CamouflageOlfactory(quality='advanced'),
            NavigationSystem(quality='basic'),
            StorageCompartment(slots_count=4),
            VehicleSpeedModification(),
            RobotTransceiver(range_km=5000, quality='advanced'),
        ],
    )


@pytest.mark.approval
def test_gonzales(snapshot):
    snap = AnnotatedSnapshot(build_gonzales().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres Cr24,500 vs source Cr27,000 — gap Cr2,500 unresolved',
    )
    snap.annotate(
        'slots',
        'IncreasedArmour(+4) takes 1 slot → used=9 vs available=8 (slot overload); source shows 0 remaining',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
