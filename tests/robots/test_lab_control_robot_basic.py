# Source: refs/robot/109_domestic_servant.md
# Default suite substitutes Visual Spectrum Sensor → Video Screen (improved)
# and Transceiver 5km (improved) → Transceiver 500km (improved).

from types import SimpleNamespace

from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize
from ceres.make.robot.options import ExternalPower, RoboticDroneController
from ceres.make.robot.skills import SkillPackage
from ceres.make.robot.spec import RobotSpecSection

_expected = SimpleNamespace(
    hits=1,
    locomotion='None',
    speed='0m',
    tl=12,
    cost=12000,
    skills='Electronics (remote ops) 1, +1 Bandwidth available',
    attacks='—',
    manipulators='—',
    endurance_hours=324,
    armour=4,
    traits='Armour (+4), Small (-4)',
    programming='Advanced (INT 8)',
    options=(
        'Auditory Sensor',
        'External Power',
        'Robotic Drone Controller (basic)',
        'Transceiver 500km (improved)',
        'Video Screen (improved)',
        'Voder Speaker',
        'Wireless Data Link',
    ),
)

_DEFAULT_SUITE = [
    'Auditory Sensor',
    'Transceiver 500km (improved)',
    'Video Screen (improved)',
    'Voder Speaker',
    'Wireless Data Link',
]


def build_basic_lab_control_robot() -> Robot:
    return Robot(
        name='Basic Lab Control Robot',
        tl=12,
        size=RobotSize.SIZE_1,
        locomotion=NoneLocomotion(),
        brain=AdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Electronics (remote ops)', level=1, bandwidth=1),),
        ),
        manipulators=[],
        options=[
            ExternalPower(),
            RoboticDroneController(quality='basic'),
        ],
        default_suite=_DEFAULT_SUITE,
    )


class TestBasicLabControlRobot:
    def test_hits(self):
        assert build_basic_lab_control_robot().hits == _expected.hits

    def test_endurance(self):
        assert build_basic_lab_control_robot().base_endurance == _expected.endurance_hours

    def test_base_armour(self):
        assert build_basic_lab_control_robot().base_armour == _expected.armour

    def test_programming(self):
        assert build_basic_lab_control_robot().brain.programming_label() == _expected.programming

    def test_cost(self):
        assert build_basic_lab_control_robot().total_cost == _expected.cost

    def test_skills_electronics(self):
        assert 'Electronics (remote ops) 1' in build_basic_lab_control_robot().skills_display

    def test_skills_bandwidth(self):
        assert '+1 Bandwidth available' in build_basic_lab_control_robot().skills_display

    def test_traits_armour(self):
        robot = build_basic_lab_control_robot()
        assert any(str(t) == f'Armour (+{_expected.armour})' for t in robot.traits)

    def test_traits_small(self):
        robot = build_basic_lab_control_robot()
        assert any(str(t) == 'Small (-4)' for t in robot.traits)

    def test_spec_options_row_default_suite(self):
        spec = build_basic_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Auditory Sensor' in value
        assert 'Transceiver 500km (improved)' in value
        assert 'Video Screen (improved)' in value
        assert 'Voder Speaker' in value
        assert 'Wireless Data Link' in value

    def test_spec_options_row_extra_options(self):
        spec = build_basic_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'External Power' in value
        assert 'Robotic Drone Controller (basic)' in value

    def test_spec_options_row_alphabetical(self):
        spec = build_basic_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        items = [s.strip() for s in value.split(',')]
        assert items == sorted(items)

    def test_locomotion_label(self):
        assert build_basic_lab_control_robot().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_basic_lab_control_robot().locomotion.speed_label() == _expected.speed

    def test_skills_display_exact(self):
        assert build_basic_lab_control_robot().skills_display == _expected.skills

    def test_spec_traits_row(self):
        spec = build_basic_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.TRAITS)[0].value
        assert value == _expected.traits

    def test_spec_attacks_row(self):
        spec = build_basic_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row(self):
        spec = build_basic_lab_control_robot().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == _expected.manipulators

    def test_json_roundtrip_design_inputs(self):
        robot = build_basic_lab_control_robot()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Basic Lab Control Robot'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_1
        assert isinstance(restored.locomotion, NoneLocomotion)
        assert isinstance(restored.brain, AdvancedBrain)
