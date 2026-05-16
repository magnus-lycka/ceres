"""Tests for robot brain types.

All values derived from refs/robot/33_brain.md (Robot Brains table).
"""

from pydantic import TypeAdapter, ValidationError
import pytest

from ceres.make.robot.brain import AdvancedBrain, BasicBrain, PrimitiveBrain, RobotBrainUnion, VeryAdvancedBrain
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
        assert BasicBrain().programming_label() == 'Basic (INT 4)'

    def test_basic_tl8_shows_int3(self):
        assert BasicBrain(brain_tl=8).programming_label() == 'Basic (INT 3)'

    def test_basic_with_function(self):
        assert BasicBrain(function='servant').programming_label() == 'Basic (servant) (INT 4)'

    def test_basic_tl8_with_function(self):
        assert BasicBrain(brain_tl=8, function='servant').programming_label() == 'Basic (servant) (INT 3)'

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


class TestAdvancedBrainBandwidthUpgrade:
    """Brain Bandwidth Upgrade validation — refs/robot/34_retrotech.md (RHB p.67-68).

    Advanced brain at TL12: base BW=2. Valid upgrades: +2 (TL10, Cr5,000),
    +3 (TL11, Cr10,000), +4 (TL12, Cr20,000).
    """

    def test_default_bandwidth_is_base(self):
        brain = AdvancedBrain(brain_tl=12)
        assert brain.bandwidth == 2

    def test_bandwidth_upgrade_plus2_accepted(self):
        brain = AdvancedBrain(brain_tl=10, bandwidth=4)
        assert brain.bandwidth == 4

    def test_bandwidth_upgrade_plus2_cost(self):
        brain = AdvancedBrain(brain_tl=10, bandwidth=4)
        assert brain.hardware_cost == 100_000.0 + 5_000.0  # base + BW upgrade

    def test_bandwidth_upgrade_plus4_at_tl12(self):
        brain = AdvancedBrain(brain_tl=12, bandwidth=6)
        assert brain.bandwidth == 6
        assert brain.hardware_cost == 10_000.0 + 20_000.0

    def test_bandwidth_upgrade_invalid_raises(self):
        with pytest.raises(ValidationError):
            AdvancedBrain(brain_tl=12, bandwidth=3)  # +1 is not a valid upgrade delta

    def test_bandwidth_upgrade_tl10_not_available_below_tl10(self):
        with pytest.raises(ValidationError):
            AdvancedBrain(brain_tl=9, bandwidth=4)  # TL9 Advanced brain can't get +2 upgrade

    def test_hardware_cost_excludes_skill_packages(self):
        from ceres.make.robot.skills import SkillPackage

        brain = AdvancedBrain(
            brain_tl=12,
            bandwidth=4,
            installed_skills=(SkillPackage(name='Electronics (remote ops)', level=1, bandwidth=1),),
        )
        assert brain.hardware_cost == 10_000.0 + 5_000.0

    def test_bandwidth_upgrade_serialises_to_json(self):
        from pydantic import TypeAdapter

        from ceres.make.robot.brain import RobotBrainUnion

        brain = AdvancedBrain(brain_tl=12, bandwidth=4)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, AdvancedBrain)
        assert restored.bandwidth == 4


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


class TestVeryAdvancedBrainTable:
    """refs/robot/33_brain.md — Very Advanced rows."""

    @pytest.mark.parametrize(
        'brain_tl, expected_cost, expected_int, expected_bw, expected_dm',
        [
            (12, 500_000.0, 9, 3, 1),
            (13, 500_000.0, 10, 4, 1),
            (14, 500_000.0, 11, 5, 1),
            (15, 500_000.0, 11, 5, 1),  # TL15 falls back to TL14 entry
        ],
    )
    def test_very_advanced_table_values(self, brain_tl, expected_cost, expected_int, expected_bw, expected_dm):
        brain = VeryAdvancedBrain(brain_tl=brain_tl)
        assert brain.brain_cost == expected_cost
        assert brain.base_int == expected_int
        assert brain.bandwidth == expected_bw
        assert brain.skill_dm == expected_dm

    def test_very_advanced_skill_dm_applies_to_grants(self):
        from ceres.make.robot.skills import SkillPackage

        # skill_dm=1 even without int_upgrade → package level 1 becomes grant level 2
        brain = VeryAdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Mechanic', level=1, bandwidth=1),),
        )
        assert SkillGrant('Mechanic', 2) in brain.skill_grants

    def test_very_advanced_programming_label(self):
        assert VeryAdvancedBrain(brain_tl=12).programming_label() == 'Very Advanced (INT 9)'

    def test_very_advanced_tl13_programming_label(self):
        assert VeryAdvancedBrain(brain_tl=13).programming_label() == 'Very Advanced (INT 10)'


class TestVeryAdvancedBrainBandwidthUpgrade:
    """Brain Bandwidth Upgrade for Very Advanced — refs/robot/34_retrotech.md.

    Very Advanced at TL12: base BW=3. Valid upgrades: +6 → BW 9 (Cr50,000),
    +8 → BW 11 (Cr100,000).
    """

    def test_default_bandwidth_is_base(self):
        assert VeryAdvancedBrain(brain_tl=12).bandwidth == 3

    def test_bandwidth_upgrade_plus6_accepted(self):
        brain = VeryAdvancedBrain(brain_tl=12, bandwidth=9)
        assert brain.bandwidth == 9
        assert brain.hardware_cost == 500_000.0 + 50_000.0

    def test_bandwidth_upgrade_plus8_accepted(self):
        brain = VeryAdvancedBrain(brain_tl=12, bandwidth=11)
        assert brain.bandwidth == 11
        assert brain.hardware_cost == 500_000.0 + 100_000.0

    def test_bandwidth_upgrade_invalid_raises(self):
        with pytest.raises(ValidationError):
            VeryAdvancedBrain(brain_tl=12, bandwidth=5)  # not a valid delta

    def test_bandwidth_upgrade_serialises(self):
        brain = VeryAdvancedBrain(brain_tl=12, bandwidth=9)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, VeryAdvancedBrain)
        assert restored.bandwidth == 9


class TestAdvancedBrainIntUpgrade:
    """INT upgrade — refs/robot/34_retrotech.md.

    INT+n costs n(n+1)/2 BW and product(base_int+1 … base_int+n) × Cr1000.
    """

    @pytest.mark.parametrize(
        'int_upgrade, expected_int, expected_cost, expected_bw_used',
        [
            (1, 9, 9_000.0, 1),  # 9 × 1000; 1×2/2 = 1 BW
            (2, 10, 90_000.0, 3),  # 9×10 × 1000; 2×3/2 = 3 BW
            (3, 11, 990_000.0, 6),  # 9×10×11 × 1000; 3×4/2 = 6 BW
        ],
    )
    def test_int_upgrade_cost_and_bw(self, int_upgrade, expected_int, expected_cost, expected_bw_used):
        brain = AdvancedBrain(brain_tl=12, int_upgrade=int_upgrade)
        assert brain.base_int == expected_int
        assert brain._int_upgrade_cost == expected_cost
        assert brain.used_bandwidth == expected_bw_used

    def test_int_upgrade_increases_skill_dm(self):
        assert AdvancedBrain(brain_tl=12, int_upgrade=2).skill_dm == 2  # 0 base + 2

    def test_int_upgrade_applies_dm_to_skill_grants(self):
        from ceres.make.robot.skills import SkillPackage

        brain = AdvancedBrain(
            brain_tl=12,
            int_upgrade=1,
            installed_skills=(SkillPackage(name='Mechanic', level=1, bandwidth=1),),
        )
        assert SkillGrant('Mechanic', 2) in brain.skill_grants  # level 1 + DM 1

    def test_int_upgrade_included_in_hardware_cost(self):
        brain = AdvancedBrain(brain_tl=12, int_upgrade=1)
        assert brain.hardware_cost == 10_000.0 + 9_000.0

    def test_int_upgrade_not_in_remaining_bandwidth_if_bw_base_sufficient(self):
        # INT+1 uses 1 BW; Advanced TL12 base BW=2 → 1 remaining
        brain = AdvancedBrain(brain_tl=12, int_upgrade=1)
        assert brain.remaining_bandwidth == 1

    def test_int_upgrade_above_max_raises(self):
        with pytest.raises(ValidationError):
            AdvancedBrain(brain_tl=12, int_upgrade=4)

    def test_int_upgrade_programming_label(self):
        assert AdvancedBrain(brain_tl=12, int_upgrade=1).programming_label() == 'Advanced (INT 9)'

    def test_int_upgrade_serialises(self):
        brain = AdvancedBrain(brain_tl=12, int_upgrade=2)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, AdvancedBrain)
        assert restored.int_upgrade == 2
        assert restored.base_int == 10


class TestBrainSlots:
    """brain_slots() — slot cost when brain computer rating exceeds robot size.

    Rule: slots = 1 if robot_size < max(0, computer_x - (robot_tl - brain_tl)) else 0.
    Retrotech discount: higher robot TL reduces the effective computer requirement.
    """

    def test_advanced_tl12_in_tl12_size2_is_free(self):
        # computer_x=2, min_free=2; size 2 is not < 2 → free
        assert AdvancedBrain(brain_tl=12).brain_slots(robot_tl=12, robot_size=2) == 0

    def test_advanced_tl12_in_tl12_size1_costs_slot(self):
        # size 1 < min_free 2 → 1 slot
        assert AdvancedBrain(brain_tl=12).brain_slots(robot_tl=12, robot_size=1) == 1

    def test_advanced_tl10_in_tl12_always_free(self):
        # retrotech: robot TL 2 higher → min_free = max(0, 2-2) = 0
        assert AdvancedBrain(brain_tl=10).brain_slots(robot_tl=12, robot_size=1) == 0

    def test_very_advanced_tl12_in_tl12_size3_is_free(self):
        # computer_x=3, min_free=3; size 3 is not < 3 → free
        assert VeryAdvancedBrain(brain_tl=12).brain_slots(robot_tl=12, robot_size=3) == 0

    def test_very_advanced_tl12_in_tl12_size2_costs_slot(self):
        # size 2 < min_free 3 → 1 slot
        assert VeryAdvancedBrain(brain_tl=12).brain_slots(robot_tl=12, robot_size=2) == 1

    def test_primitive_tl8_always_free(self):
        # computer_x=0 → min_free=0 for any robot TL → never costs a slot
        assert PrimitiveBrain(brain_tl=8).brain_slots(robot_tl=8, robot_size=1) == 0

    def test_basic_tl10_in_tl10_size1_is_free(self):
        # computer_x=1, min_free=1; size 1 is not < 1 → free
        assert BasicBrain(brain_tl=10).brain_slots(robot_tl=10, robot_size=1) == 0


class TestBrainBaseGuards:
    """_BrainBase raises NotImplementedError for all abstract properties."""

    def test_base_programming_label_raises(self):
        from ceres.make.robot.brain import _BrainBase

        with pytest.raises(NotImplementedError):
            _BrainBase.programming_label(PrimitiveBrain())

    @pytest.mark.parametrize('prop', ['base_int', 'brain_cost', 'skill_dm'])
    def test_base_property_raises(self, prop):
        from ceres.make.robot.brain import _BrainBase

        with pytest.raises(NotImplementedError):
            getattr(_BrainBase, prop).fget(PrimitiveBrain())
