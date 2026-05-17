# Source: user-supplied stat block (no refs/robot/xxx_hudson.md yet).
#
# SIZE_4 TL15: STR = 2×4−1 = 7, DEX = ceil(15/2)+1 = 9. Source: 2× (STR 7, DEX 9). ✓
# Endurance: Walker base 72h × TL15 multiplier 2.0 = 144h. ✓
# Armour: TL15 → band [15,17] → +4. ✓
#
# Brain bandwidth: int_upgrade=1 → 1 BW; three level-1 skill packages (Admin, Pilot,
# Steward) → 3 BW; total used = 4. Advanced TL12 base BW = 2; +2 upgrade (Cr5,000)
# required. bandwidth=4, remaining=0. ✓
#
# Default suite: Visual Spectrum Sensor, Auditory Sensor, Transceiver 5km (improved),
# Drone Interface — source omits Voder Speaker and Wireless Data Link.
#
# Refrigerated Storage: source lists "Refrigerated Storage (Slots)" without a slot
# count; interpreted as 1 slot, consuming the final available slot (remaining=0).
#
# SIZE_4 chassis name is 'Bwap' in Ceres (refs/robot/04_chassis.md); source says 'Goat'
# (different supplement or edition).

from types import SimpleNamespace

from ceres.make.robot import AdvancedBrain, Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.options import (
    Autochef,
    OlfactorySensor,
    StorageCompartment,
    StylistToolkit,
    VideoScreen,
)
from ceres.make.robot.skills import SkillPackage
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits

_expected = SimpleNamespace(
    hits=12,
    locomotion='Walker',
    speed='5m',
    tl=15,
    armour=4,
    traits='Armour (+4), ATV, Heightened Senses, Small (-1)',
    programming='Advanced (INT 9)',
    skills='Admin 2, Drive (All) 1, Flyer (All) 1, Pilot (Small Craft) 2, Steward 2',
    endurance_hours=144,
    attacks='—',
    manipulators='2× (STR 7 DEX 9)',
    available_slots=8,
    used_slots=8,
    remaining_slots=0,
)
# source: Cr43,000; Ceres: Cr43,300 (discrepancy Cr300 untraced — likely source rounding).
# BCC Cr8,000 + brain Cr27,200 (Advanced TL12 Cr10k + INT+1 Cr9k + BW+2 Cr5k + skills Cr3.2k)
# + OlfactorySensor Cr3,500 + Autochef Cr2,000 + StylistToolkit Cr2,000
# + Storage (1 slot refrigerated) Cr100 + VideoScreen (improved) Cr500.
_expected.cost = 43_300


def build_hudson() -> Robot:
    return Robot(
        name='Hudson',
        tl=15,
        size=RobotSize.SIZE_4,
        locomotion=WalkerLocomotion(),
        brain=AdvancedBrain(
            int_upgrade=1,
            bandwidth=4,
            installed_skills=(
                SkillPackage(name='Admin', level=1, bandwidth=1),
                SkillPackage(name='Drive (All)', level=0, bandwidth=0),
                SkillPackage(name='Flyer (All)', level=0, bandwidth=0),
                SkillPackage(name='Pilot (Small Craft)', level=1, bandwidth=1),
                SkillPackage(name='Steward', level=1, bandwidth=1),
            ),
        ),
        manipulators=[Manipulator(), Manipulator()],
        options=[
            *default_suite(see=True, hear=True, improved_transceiver=True, drone=True, speak=False, wireless=False),
            OlfactorySensor(quality='improved'),
            Autochef(quality='improved'),
            StylistToolkit(),
            StorageCompartment(slots_count=1, storage_type='refrigerated'),
            VideoScreen(quality='improved'),
        ],
    )


class TestHudson:
    def test_hits(self):
        assert build_hudson().hits == _expected.hits

    def test_base_armour(self):
        assert build_hudson().base_armour == _expected.armour

    def test_traits(self):
        assert format_traits(build_hudson().traits) == _expected.traits

    def test_programming(self):
        assert build_hudson().brain.programming_label() == _expected.programming

    def test_skills(self):
        assert build_hudson().skills_display == _expected.skills

    def test_endurance(self):
        assert int(build_hudson().base_endurance) == _expected.endurance_hours

    def test_cost(self):
        assert build_hudson().total_cost == _expected.cost

    def test_locomotion_label(self):
        assert build_hudson().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_hudson().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_hudson().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_hudson().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_hudson().remaining_slots == _expected.remaining_slots

    def test_spec_attacks_row(self):
        spec = build_hudson().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row(self):
        spec = build_hudson().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == _expected.manipulators

    def test_spec_options_has_autochef(self):
        spec = build_hudson().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Autochef (improved)' in value

    def test_spec_options_has_stylist_toolkit(self):
        spec = build_hudson().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Stylist Toolkit' in value

    def test_spec_options_has_olfactory(self):
        spec = build_hudson().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Olfactory Sensor (improved)' in value

    def test_spec_options_has_refrigerated_storage(self):
        spec = build_hudson().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Storage Compartment (1 Slots refrigerated)' in value

    def test_spec_options_has_video_screen(self):
        spec = build_hudson().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Video Screen (improved)' in value

    def test_spec_options_alphabetical(self):
        spec = build_hudson().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        items = [s.strip() for s in value.split(',')]
        assert items == sorted(items)

    def test_no_spare_slots_in_options(self):
        spec = build_hudson().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Spare Slots' not in value

    def test_json_roundtrip(self):
        robot = build_hudson()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Hudson'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_4
        assert isinstance(restored.locomotion, WalkerLocomotion)
        assert isinstance(restored.brain, AdvancedBrain)
        assert restored.brain.int_upgrade == 1
        assert restored.brain.bandwidth == 4
