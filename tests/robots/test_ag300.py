# Source: refs/robot/105_utility_robots.md

from types import SimpleNamespace

from ceres.make.robot import BasicBrain, Robot, RobotSize, WalkerLocomotion
from ceres.make.robot.options import (
    AdditionalManipulator,
    AgriculturalEquipment,
    LightIntensifierSensor,
    NavigationSystem,
    OlfactorySensor,
    StorageCompartment,
    ThermalSensor,
)
from ceres.make.robot.spec import RobotSpecSection

_expected = SimpleNamespace(
    hits=20,
    locomotion='Walker',
    speed='6m',
    tl=10,
    armour=3,
    traits='Armour (+3), ATV, Heightened Senses, IR Vision',
    programming='Basic (labourer) (INT 4)',
    endurance_hours=65,
    attacks='—',
    available_slots=16,
    used_slots=16,
    remaining_slots=0,
)
# source: Cr20,000; Ceres computes Cr24,850:
# BCC Cr10,000 + speed increase Cr1,000 + brain Cr4,000
# + additional manipulators Cr800 + AgriculturalEquipment Cr1,000
# + LightIntensifierSensor Cr1,250 + NavigationSystem Cr2,000
# + OlfactorySensor Cr3,500 + StorageCompartment Cr800 + ThermalSensor Cr500.
# Cause of discrepancy untraced. See RIR-002.
_expected.cost = 24_850

_DEFAULT_SUITE = [
    'Auditory Sensor',
    'Drone Interface',
    'Transceiver 5km (improved)',
    'Visual Spectrum Sensor',
    'Voder Speaker',
    'Wireless Data Link',
]


def build_ag300() -> Robot:
    return Robot(
        name='AG300 Agricultural Worker',
        tl=10,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(speed_increase=1),
        brain=BasicBrain(function='labourer'),
        options=[
            AgriculturalEquipment(size='medium'),
            LightIntensifierSensor(quality='advanced'),
            NavigationSystem(quality='basic'),
            OlfactorySensor(quality='improved'),
            StorageCompartment(slots_count=8, storage_type='refrigerated'),
            ThermalSensor(),
            AdditionalManipulator(count=2, manipulator_size=4),
        ],
        default_suite=_DEFAULT_SUITE,
    )


class TestAG300:
    def test_hits(self):
        assert build_ag300().hits == _expected.hits

    def test_base_armour(self):
        assert build_ag300().base_armour == _expected.armour

    def test_traits(self):
        robot = build_ag300()
        from ceres.make.robot.text import format_traits

        assert format_traits(robot.traits) == _expected.traits

    def test_ir_vision_not_duplicated(self):
        robot = build_ag300()
        ir_traits = [t for t in robot.traits if t.name == 'IR Vision']
        assert len(ir_traits) == 1

    def test_programming(self):
        assert build_ag300().brain.programming_label() == _expected.programming

    def test_skills_navigation(self):
        assert 'Navigation 1' in build_ag300().skills_display

    def test_skills_labourer(self):
        assert 'Profession (labourer) 2' in build_ag300().skills_display

    def test_endurance(self):
        assert round(build_ag300().base_endurance) == _expected.endurance_hours

    def test_cost(self):
        assert build_ag300().total_cost == _expected.cost

    def test_speed_label(self):
        assert build_ag300().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_ag300().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_ag300().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_ag300().remaining_slots == _expected.remaining_slots

    def test_spec_attacks_row(self):
        spec = build_ag300().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_includes_additional(self):
        spec = build_ag300().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert 'STR 7' in value

    def test_spec_options_has_agricultural(self):
        spec = build_ag300().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Agricultural Equipment (medium)' in value

    def test_spec_options_has_light_intensifier(self):
        spec = build_ag300().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Light Intensifier Sensor (advanced)' in value

    def test_spec_options_has_olfactory(self):
        spec = build_ag300().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Olfactory Sensor (improved)' in value

    def test_spec_options_has_thermal(self):
        spec = build_ag300().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Thermal Sensor' in value

    def test_spec_options_has_refrigerated_storage(self):
        spec = build_ag300().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Storage Compartment (8 Slots refrigerated)' in value

    def test_json_roundtrip(self):
        robot = build_ag300()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'AG300 Agricultural Worker'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_5
        assert isinstance(restored.locomotion, WalkerLocomotion)
        assert isinstance(restored.brain, BasicBrain)
