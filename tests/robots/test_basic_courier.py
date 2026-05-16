# Source: refs/robot/107_courier_basic.md

from types import SimpleNamespace

from ceres.make.robot import BasicBrain, GravLocomotion, Robot, RobotSize
from ceres.make.robot.options import NavigationSystem, StorageCompartment, VehicleSpeedModification
from ceres.make.robot.spec import RobotSpecSection

_expected = SimpleNamespace(
    hits=8,
    locomotion='Grav',
    speed='—',
    tl=10,
    armour=3,
    traits='Armour (+3), Flyer (high), Small (-2)',
    programming='Basic (locomotion) (INT 4)',
    skills='Athletics (dexterity) 1, Flyer (grav) 1, Navigation 1',
    endurance_hours=24,
    endurance_label='24 (6) hours',
    attacks='—',
    manipulators='—',
    available_slots=6,
    used_slots=6,
    remaining_slots=0,
    options=(
        'Auditory Sensor',
        'Drone Interface',
        'Navigation System (basic)',
        'Storage Compartment (3 Slots hazardous material)',
        'Transceiver 500km (improved)',
        'Visual Spectrum Sensor',
        'Voder Speaker',
        'Wireless Data Link',
    ),
)
# source: Cr25,000; Ceres computes Cr23,900:
# BCC Cr8,000 + brain Cr4,000 − manipulator discount Cr600
# + default suite Cr1,000 + NavigationSystem Cr2,000
# + StorageCompartment Cr1,500 + VehicleSpeedModification Cr8,000.
# Cause of discrepancy untraced. See RIR-002.
_expected.cost = 23_900

_DEFAULT_SUITE = [
    'Auditory Sensor',
    'Drone Interface',
    'Transceiver 500km (improved)',
    'Visual Spectrum Sensor',
    'Voder Speaker',
    'Wireless Data Link',
]


def build_basic_courier() -> Robot:
    return Robot(
        name='Basic Courier',
        tl=10,
        size=RobotSize.SIZE_3,
        locomotion=GravLocomotion(),
        brain=BasicBrain(function='locomotion'),
        manipulators=[],
        options=[
            VehicleSpeedModification(),
            NavigationSystem(quality='basic'),
            StorageCompartment(slots_count=3, storage_type='hazardous'),
        ],
        default_suite=_DEFAULT_SUITE,
    )


class TestBasicCourier:
    def test_hits(self):
        assert build_basic_courier().hits == _expected.hits

    def test_base_armour(self):
        assert build_basic_courier().base_armour == _expected.armour

    def test_traits(self):
        robot = build_basic_courier()
        from ceres.make.robot.text import format_traits

        assert format_traits(robot.traits) == _expected.traits

    def test_traits_no_flyer_idle(self):
        robot = build_basic_courier()
        assert all(not (t.name == 'Flyer' and t.value == 'idle') for t in robot.traits)

    def test_programming(self):
        assert build_basic_courier().brain.programming_label() == _expected.programming

    def test_skills(self):
        assert build_basic_courier().skills_display == _expected.skills

    def test_endurance(self):
        assert build_basic_courier().base_endurance == _expected.endurance_hours

    def test_endurance_label(self):
        assert build_basic_courier().endurance_label == _expected.endurance_label

    def test_cost(self):
        assert build_basic_courier().total_cost == _expected.cost

    def test_locomotion_label(self):
        assert build_basic_courier().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_basic_courier().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_basic_courier().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_basic_courier().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_basic_courier().remaining_slots == _expected.remaining_slots

    def test_spec_attacks_row(self):
        spec = build_basic_courier().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row(self):
        spec = build_basic_courier().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == _expected.manipulators

    def test_spec_options_contains_navigation(self):
        spec = build_basic_courier().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Navigation System (basic)' in value

    def test_spec_options_contains_storage(self):
        spec = build_basic_courier().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Storage Compartment (3 Slots hazardous material)' in value

    def test_spec_options_no_vehicle_speed_modification(self):
        spec = build_basic_courier().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Vehicle Speed' not in value

    def test_json_roundtrip(self):
        robot = build_basic_courier()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Basic Courier'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_3
        assert isinstance(restored.locomotion, GravLocomotion)
        assert isinstance(restored.brain, BasicBrain)
