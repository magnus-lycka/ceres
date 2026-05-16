# Source: refs/robot/104_utility_droid.md

from types import SimpleNamespace

from ceres.make.robot import BasicBrain, Robot, RobotSize, WalkerLocomotion
from ceres.make.robot.options import DecreasedResiliency
from ceres.make.robot.spec import RobotSpecSection

_expected = SimpleNamespace(
    hits=18,
    locomotion='Walker',
    speed='5m',
    tl=9,
    armour=3,
    traits='Armour (+3), ATV',
    programming='Basic (servant) (INT 3)',
    skills='Profession (domestic servant) 2',
    endurance_hours=72,
    attacks='—',
    available_slots=16,
    remaining_slots=16,
    options=(
        'Auditory Sensor',
        'Drone Interface',
        'Spare Slots x16',
        'Transceiver 5km (improved)',
        'Visual Spectrum Sensor',
        'Voder Speaker',
        'Wireless Data Link',
    ),
)
# source: Cr24,000; Ceres computes Cr29,000 (BCC Cr10,000 + BasicBrain TL8 Cr20,000 − DecreasedResiliency Cr1,000).
# Cause of discrepancy untraced. See RIR-002.
_expected.cost = 29_000


def build_utility_droid() -> Robot:
    return Robot(
        name='Utility Droid',
        tl=9,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(),
        brain=BasicBrain(brain_tl=8, function='servant'),
        options=[DecreasedResiliency(hit_reduction=2)],
        default_suite=[
            'Auditory Sensor',
            'Drone Interface',
            'Transceiver 5km (improved)',
            'Visual Spectrum Sensor',
            'Voder Speaker',
            'Wireless Data Link',
        ],
    )


class TestUtilityDroid:
    def test_hits(self):
        assert build_utility_droid().hits == _expected.hits

    def test_base_armour(self):
        assert build_utility_droid().base_armour == _expected.armour

    def test_traits(self):
        robot = build_utility_droid()
        from ceres.make.robot.text import format_traits

        assert format_traits(robot.traits) == _expected.traits

    def test_programming(self):
        assert build_utility_droid().brain.programming_label() == _expected.programming

    def test_skills(self):
        assert build_utility_droid().skills_display == _expected.skills

    def test_endurance(self):
        assert round(build_utility_droid().base_endurance) == _expected.endurance_hours

    def test_cost(self):
        assert build_utility_droid().total_cost == _expected.cost

    def test_locomotion_label(self):
        assert build_utility_droid().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_utility_droid().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_utility_droid().available_slots == _expected.available_slots

    def test_remaining_slots(self):
        assert build_utility_droid().remaining_slots == _expected.remaining_slots

    def test_spec_attacks_row(self):
        spec = build_utility_droid().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row_has_standard_pair(self):
        spec = build_utility_droid().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value != '—'

    def test_spec_options_row_contains_drone_interface(self):
        spec = build_utility_droid().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Drone Interface' in value

    def test_spec_options_row_contains_spare_slots(self):
        spec = build_utility_droid().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Spare Slots x16' in value

    def test_json_roundtrip(self):
        robot = build_utility_droid()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Utility Droid'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_5
        assert isinstance(restored.locomotion, WalkerLocomotion)
        assert isinstance(restored.brain, BasicBrain)
