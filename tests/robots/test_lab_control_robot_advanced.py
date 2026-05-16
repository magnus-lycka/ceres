# Source: refs/robot/110_lab_control_robot_advanced.md

from types import SimpleNamespace

from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize
from ceres.make.robot.options import (
    AvatarController,
    ExternalPower,
    RoboticDroneController,
    SwarmController,
)
from ceres.make.robot.skills import SkillPackage
from ceres.make.robot.spec import RobotSpecSection

_expected = SimpleNamespace(
    hits=8,
    locomotion='None',
    speed='0m',
    tl=12,
    armour=4,
    traits='Armour (+4), Small (-2)',
    # source: "Advanced (INT 9)". Advanced TL12 has base INT 8; the robot uses
    # an INT upgrade to 9 per refs/robot/34_retrotech.md (1 BW, Cr9,000). ✓
    programming='Advanced (INT 9)',
    skills='Electronics (remote ops) 3, Science (robotics) 2',
    endurance_hours=324,
    attacks='—',
    manipulators='—',
    available_slots=7,
    used_slots=5,
    remaining_slots=2,
)
# source: Cr160,000; Ceres computes Cr187,700 (BW upgrade Cr5,000 included).
# 15% discount in source untraced. See RIR-002.
_expected.cost = 187_700

_DEFAULT_SUITE = [
    'Auditory Sensor',
    'Transceiver 5,000km (enhanced)',
    'Video Screen (improved)',
    'Voder Speaker',
    'Wireless Data Link',
]


def build_advanced_lab_control_robot() -> Robot:
    return Robot(
        name='Advanced Lab Control Robot',
        tl=12,
        size=RobotSize.SIZE_3,
        locomotion=NoneLocomotion(),
        brain=AdvancedBrain(
            int_upgrade=1,
            bandwidth=4,
            installed_skills=(
                SkillPackage(name='Electronics (remote ops)', level=2, bandwidth=2),
                SkillPackage(name='Science (robotics)', level=1, bandwidth=1),
            ),
        ),
        manipulators=[],
        options=[
            ExternalPower(),
            RoboticDroneController(quality='advanced'),
            AvatarController(quality='basic'),
            SwarmController(quality='enhanced'),
        ],
        default_suite=_DEFAULT_SUITE,
    )


class TestAdvancedLabControlRobot:
    def test_hits(self):
        assert build_advanced_lab_control_robot().hits == _expected.hits

    def test_base_armour(self):
        assert build_advanced_lab_control_robot().base_armour == _expected.armour

    def test_traits(self):
        robot = build_advanced_lab_control_robot()
        from ceres.make.robot.text import format_traits

        assert format_traits(robot.traits) == _expected.traits

    def test_programming(self):
        assert build_advanced_lab_control_robot().brain.programming_label() == _expected.programming

    def test_skills(self):
        assert build_advanced_lab_control_robot().skills_display == _expected.skills

    def test_endurance(self):
        assert build_advanced_lab_control_robot().base_endurance == _expected.endurance_hours

    def test_cost(self):
        assert build_advanced_lab_control_robot().total_cost == _expected.cost

    def test_locomotion_label(self):
        assert build_advanced_lab_control_robot().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_advanced_lab_control_robot().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_advanced_lab_control_robot().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_advanced_lab_control_robot().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_advanced_lab_control_robot().remaining_slots == _expected.remaining_slots

    def test_spec_attacks_row(self):
        spec = build_advanced_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row(self):
        spec = build_advanced_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == _expected.manipulators

    def test_spec_options_has_avatar_controller(self):
        spec = build_advanced_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Avatar Controller (basic)' in value

    def test_spec_options_has_swarm_controller(self):
        spec = build_advanced_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Swarm Controller (enhanced)' in value

    def test_spec_options_has_drone_controller(self):
        spec = build_advanced_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Robotic Drone Controller (advanced)' in value

    def test_json_roundtrip(self):
        robot = build_advanced_lab_control_robot()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Advanced Lab Control Robot'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_3
        assert isinstance(restored.locomotion, NoneLocomotion)
        assert isinstance(restored.brain, AdvancedBrain)
        assert restored.brain.int_upgrade == 1
