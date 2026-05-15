"""Tests for robot brain types.

All values derived from refs/robot/33_brain.md (Robot Brains table).
"""

from pydantic import TypeAdapter
import pytest

from ceres.make.robot.brain import AdvancedBrain, BasicBrain, PrimitiveBrain, RobotBrainUnion
from ceres.make.robot.skills import SkillGrant


class TestPrimitiveBrainTable:
    """refs/robot/33_brain.md — Primitive rows."""

    @pytest.mark.parametrize(
        'brain_tl, expected_cost, expected_int, expected_bw, expected_dm',
        [
            (7, 10000.0, 1, 0, -2),
            (8, 100.0, 1, 0, -2),
            (9, 100.0, 1, 0, -2),  # TL9 falls back to TL8 entry
        ],
    )
    def test_primitive_table_values(self, brain_tl, expected_cost, expected_int, expected_bw, expected_dm):
        brain = PrimitiveBrain(brain_tl=brain_tl)
        assert brain.brain_cost == expected_cost
        assert brain.base_int == expected_int
        assert brain.bandwidth == expected_bw
        assert brain.skill_dm == expected_dm


class TestBasicBrainTable:
    """refs/robot/33_brain.md — Basic rows."""

    @pytest.mark.parametrize(
        'brain_tl, expected_cost, expected_int, expected_bw, expected_dm',
        [
            (8, 20000.0, 3, 1, -1),
            (9, 20000.0, 3, 1, -1),  # TL9 falls back to TL8 entry
            (10, 4000.0, 4, 1, -1),
            (11, 4000.0, 4, 1, -1),  # TL11 falls back to TL10 entry
        ],
    )
    def test_basic_table_values(self, brain_tl, expected_cost, expected_int, expected_bw, expected_dm):
        brain = BasicBrain(brain_tl=brain_tl)
        assert brain.brain_cost == expected_cost
        assert brain.base_int == expected_int
        assert brain.bandwidth == expected_bw
        assert brain.skill_dm == expected_dm


class TestAdvancedBrainTable:
    """refs/robot/33_brain.md — Advanced rows."""

    @pytest.mark.parametrize(
        'brain_tl, expected_cost, expected_int, expected_bw, expected_dm',
        [
            (10, 100000.0, 6, 2, 0),
            (11, 50000.0, 7, 2, 0),
            (12, 10000.0, 8, 2, 0),
            (13, 10000.0, 8, 2, 0),  # TL13 falls back to TL12 entry
        ],
    )
    def test_advanced_table_values(self, brain_tl, expected_cost, expected_int, expected_bw, expected_dm):
        brain = AdvancedBrain(brain_tl=brain_tl)
        assert brain.brain_cost == expected_cost
        assert brain.base_int == expected_int
        assert brain.bandwidth == expected_bw
        assert brain.skill_dm == expected_dm


class TestProgrammingLabels:
    def test_primitive_no_function(self):
        assert PrimitiveBrain().programming_label() == 'Primitive'

    def test_primitive_with_function(self):
        assert PrimitiveBrain(function='clean').programming_label() == 'Primitive (clean)'

    def test_primitive_alert(self):
        assert PrimitiveBrain(function='alert').programming_label() == 'Primitive (alert)'

    def test_basic_no_function(self):
        assert BasicBrain().programming_label() == 'Basic'

    def test_basic_with_function(self):
        assert BasicBrain(function='servant').programming_label() == 'Basic (servant)'

    def test_advanced_tl12_shows_int(self):
        assert AdvancedBrain(brain_tl=12).programming_label() == 'Advanced (INT 8)'

    def test_advanced_tl11_shows_int(self):
        assert AdvancedBrain(brain_tl=11).programming_label() == 'Advanced (INT 7)'

    def test_advanced_tl10_shows_int(self):
        assert AdvancedBrain(brain_tl=10).programming_label() == 'Advanced (INT 6)'


class TestPrimitiveBrainSkillGrants:
    """refs/robot/35_skill_packages.md — Primitive package skill table."""

    def test_clean_gives_profession(self):
        brain = PrimitiveBrain(function='clean')
        assert SkillGrant('Profession (domestic cleaner)', 2) in brain.skill_grants

    def test_alert_gives_recon(self):
        brain = PrimitiveBrain(function='alert')
        assert SkillGrant('Recon', 0) in brain.skill_grants

    def test_no_function_gives_no_skills(self):
        assert PrimitiveBrain().skill_grants == ()


class TestAdvancedBrainInstalledSkills:
    """Advanced brain skill packages + bandwidth accounting."""

    def test_no_installed_skills(self):
        brain = AdvancedBrain(brain_tl=12)
        assert brain.skill_grants == ()
        assert brain.used_bandwidth == 0
        assert brain.remaining_bandwidth == 2

    def test_installed_skill_grant(self):
        from ceres.make.robot.skills import SkillPackage

        brain = AdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Electronics (remote ops)', level=1, bandwidth=1),),
        )
        assert SkillGrant('Electronics (remote ops)', 1) in brain.skill_grants

    def test_bandwidth_accounting(self):
        from ceres.make.robot.skills import SkillPackage

        brain = AdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Electronics (remote ops)', level=1, bandwidth=1),),
        )
        assert brain.used_bandwidth == 1
        assert brain.remaining_bandwidth == 1  # 2 - 1

    def test_remaining_bandwidth_none_on_primitive(self):
        assert PrimitiveBrain().remaining_bandwidth is None

    def test_remaining_bandwidth_none_on_basic(self):
        assert BasicBrain().remaining_bandwidth is None


class TestBrainTlField:
    def test_primitive_default_tl(self):
        assert PrimitiveBrain().brain_tl == 8

    def test_basic_default_tl(self):
        assert BasicBrain().brain_tl == 10

    def test_advanced_default_tl(self):
        assert AdvancedBrain().brain_tl == 12


class TestBrainDiscriminatedUnion:
    @pytest.mark.parametrize(
        'brain, expected_type',
        [
            (PrimitiveBrain(), 'PRIMITIVE'),
            (BasicBrain(), 'BASIC'),
            (AdvancedBrain(), 'ADVANCED'),
        ],
    )
    def test_roundtrip(self, brain, expected_type):
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert restored.type == expected_type

    def test_installed_skills_roundtrip(self):
        from ceres.make.robot.skills import SkillPackage

        brain = AdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Electronics (remote ops)', level=1, bandwidth=1),),
        )
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, AdvancedBrain)
        assert len(restored.installed_skills) == 1
        assert restored.installed_skills[0].name == 'Electronics (remote ops)'

    def test_function_field_roundtrip(self):
        brain = PrimitiveBrain(function='clean')
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, PrimitiveBrain)
        assert restored.function == 'clean'

    def test_discriminator_in_json(self):
        data = AdvancedBrain(brain_tl=11).model_dump()
        assert data['type'] == 'ADVANCED'
        assert data['brain_tl'] == 11


class TestBasicBrainSkillGrants:
    def test_no_function_gives_no_skills(self):
        assert BasicBrain().skill_grants == ()


class TestBrainBaseGuards:
    """_BrainBase raises NotImplementedError for all abstract properties."""

    def test_base_programming_label_raises(self):
        from ceres.make.robot.brain import _BrainBase

        with pytest.raises(NotImplementedError):
            _BrainBase.programming_label(PrimitiveBrain())

    @pytest.mark.parametrize('prop', ['base_int', 'bandwidth', 'brain_cost', 'skill_dm'])
    def test_base_property_raises(self, prop):
        from ceres.make.robot.brain import _BrainBase

        with pytest.raises(NotImplementedError):
            getattr(_BrainBase, prop).fget(PrimitiveBrain())
