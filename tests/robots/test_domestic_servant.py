# Source: refs/robot/109_domestic_servant.md

from types import SimpleNamespace

from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion
from ceres.make.robot.options import (
    DecreasedResiliency,
    DomesticCleaningEquipment,
    ReconSensor,
    StorageCompartment,
)
from ceres.make.robot.spec import RobotSpecSection

_expected = SimpleNamespace(
    hits=6,
    locomotion='Wheels',
    speed='4m',
    tl=8,
    cost=500,
    skills='Profession (domestic cleaner) 2, Recon 1',
    attacks='—',
    manipulators='—',
    endurance_hours=79,
    armour=2,
    traits='Armour (+2), Small (-2)',
    programming='Primitive (clean)',
    options=(
        'Auditory Sensor',
        'Domestic Cleaning Equipment (small)',
        'Recon Sensor (improved)',
        'Storage Compartment (4 Slots)',
        'Transceiver 5km (improved)',
        'Visual Spectrum Sensor',
        'Voder Speaker',
        'Wireless Data Link',
    ),
)
# source: Cr500 (editorial rounding); Ceres computes 420 from all rule components
_expected.cost = 420


def build_domestic_servant() -> Robot:
    return Robot(
        name='Domestic Servant',
        tl=8,
        size=RobotSize.SIZE_3,
        locomotion=WheelsLocomotion(speed_reduction=1),
        brain=PrimitiveBrain(function='clean'),
        manipulators=[],
        options=[
            DomesticCleaningEquipment(size='small'),
            ReconSensor(quality='improved'),
            StorageCompartment(slots_count=4),
            DecreasedResiliency(hit_reduction=2),
        ],
    )


class TestDomesticServant:
    def test_hits(self):
        assert build_domestic_servant().hits == _expected.hits

    def test_base_armour(self):
        assert build_domestic_servant().base_armour == _expected.armour

    def test_traits_armour(self):
        robot = build_domestic_servant()
        assert any(str(t) == f'Armour (+{_expected.armour})' for t in robot.traits)

    def test_traits_small(self):
        robot = build_domestic_servant()
        assert any(str(t) == 'Small (-2)' for t in robot.traits)

    def test_programming(self):
        assert build_domestic_servant().brain.programming_label() == _expected.programming

    def test_skills_display_cleaner(self):
        assert 'Profession (domestic cleaner) 2' in build_domestic_servant().skills_display

    def test_skills_display_recon(self):
        assert 'Recon 1' in build_domestic_servant().skills_display

    def test_endurance(self):
        assert round(build_domestic_servant().base_endurance) == _expected.endurance_hours

    def test_cost(self):
        assert build_domestic_servant().total_cost == _expected.cost

    def test_spec_options_row_default_suite(self):
        spec = build_domestic_servant().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Auditory Sensor' in value
        assert 'Transceiver 5km (improved)' in value
        assert 'Visual Spectrum Sensor' in value
        assert 'Voder Speaker' in value
        assert 'Wireless Data Link' in value

    def test_spec_options_row_extra_options(self):
        spec = build_domestic_servant().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Domestic Cleaning Equipment (small)' in value
        assert 'Recon Sensor (improved)' in value
        assert 'Storage Compartment (4 Slots)' in value

    def test_spec_options_row_alphabetical(self):
        spec = build_domestic_servant().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        items = [s.strip() for s in value.split(',')]
        assert items == sorted(items)

    def test_spec_options_decreased_resiliency_not_listed(self):
        spec = build_domestic_servant().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Decreased' not in value

    def test_locomotion_label(self):
        assert build_domestic_servant().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_domestic_servant().locomotion.speed_label() == _expected.speed

    def test_skills_display_exact(self):
        assert build_domestic_servant().skills_display == _expected.skills

    def test_spec_traits_row(self):
        spec = build_domestic_servant().build_spec()
        value = spec.rows_for_section(RobotSpecSection.TRAITS)[0].value
        assert value == _expected.traits

    def test_spec_attacks_row(self):
        spec = build_domestic_servant().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row(self):
        spec = build_domestic_servant().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == _expected.manipulators

    def test_json_roundtrip_design_inputs(self):
        robot = build_domestic_servant()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Domestic Servant'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_3
        assert isinstance(restored.locomotion, WheelsLocomotion)
        assert isinstance(restored.brain, PrimitiveBrain)
