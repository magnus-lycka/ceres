"""Approval snapshot for the Topper class Law Enforcement Walker.

Original Ceres design (not source-derived): a TL12 walker van that carries one
law-enforcement robot — a Marshal Mk II or a Deputy — and its prisoners across
terrain. Each robot has a Topper of its own.
"""

import pytest

from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.grades import Grade
from ceres.make.vehicle.options import Autopilot
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_topper() -> Vehicle:
    """Note: Original Ceres design, not from a published stat block.

    Six Spaces is the largest walker that ships in 3 tons (0.5 tons per Space), which
    is what a 3 x 4.5 m cargo lift takes. The robot fills the one crew Space; the
    Marshal Mk II is Size 6, larger than a human, so it needs the whole Space. It has
    no Drive skill, so an autopilot does the walking and the robot only says where to
    go; autopilots are fully capable only from TL9, and the advanced one gives skill 3.
    TL12 matches the robots and costs Cr5,000 more than TL9 for a speed band and
    three more points of Protection. One Space is cargo, kept for confiscated goods;
    the other four seat prisoners.

    Nothing else frees a Space. Less fuel was rejected: range is not traded for room.
    Slower gains 10% of Spaces rounded down, none on six. Open-Topped and Open Frame
    only cut Cost or add speed, and would let prisoners climb or jump out. Grid and
    beamed power gain Spaces, but tie the walker to infrastructure, and a walker is
    built for terrain.

    For the same reason the Topper is Multi-Legged: more than two legs, the number
    left open by the rules. For +100% of base Cost (Cr60,000) it gains Agility +1,
    DM+1 to operator checks in rough terrain, and can cross some impassible terrain
    at DM-2 rather than a two-legged walker's DM-4.

    Speed: Medium (100-200 kph), cruising Slow (50-100 kph). Anyone fleeing on foot
    is in the Idle band (1-20 kph), so the Topper always catches up.

    Prisoner capacity. Comfort Levels (refs/vehicle/02_new_rules.md, Crew and
    Passenger Comfort) are Comfort Points per occupant, one point per seat Space, and
    may be tracked for passengers apart from crew, so the robot's Space does not count.
    A level on the border between two takes the better one. With the four seat Spaces:

        Prisoners  Comfort Level  Comfort                Effect
        4          1.0            Basic Seating          DM-1 after 8 hours, then DM-1 per 8 hours
        5-7        0.8-0.57       Uncomfortable Seating  DM-1 after 4 hours, then DM-1 per 4 hours
        8          0.5            Uncomfortable Seating  (border, so the better level)
        9-16       0.44-0.25      Intolerable            DM-2 to all tasks at once, plus DM-2 per 4 hours

    Sixteen is the limit: 0.25, four people to a Space, is the rule's usual lower
    limit, 'Clown Seating', and the Topper does not go below it. For a prisoner van,
    an immediate DM-2 to every task is arguably a feature.

    Mass is the practical check the rules give: one Space is about 250 kg, so four
    Spaces hold roughly 1,000 kg of people, and sixteen adults are near or over that.

    Ceres models one Space per occupant only, so the stat block shows the four seated
    prisoners at Basic Seating; the crowded figures above are not derived by the code.
    """
    return Vehicle(
        name='Topper class Law Enforcement Walker',
        vehicle_type=VehicleType.WALKER,
        spaces=6,
        tl=12,
        crew=1,
        passengers=4,
        cargo_spaces=1,
        features=[Feature.MULTI_LEGGED],
        options=[Autopilot(quality=Grade.ADVANCED)],
    )


@pytest.mark.approval
class TestTopper:
    def test_it_is_a_legal_design(self):
        topper = build_topper()
        assert topper.notes.errors == []
        assert topper.notes.warnings == []

    def test_it_fits_the_cargo_lift(self):
        assert build_topper().shipping_tons <= 3

    def test_snapshot(self, snapshot):
        snap = AnnotatedSnapshot(build_topper().build_spec().model_dump(mode='json'))
        snap.annotate(
            'passengers',
            'Four prisoners at one Space each; crowded capacities down to Clown Seating are '
            'in the design notes, since Ceres models one Space per occupant',
        )
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
