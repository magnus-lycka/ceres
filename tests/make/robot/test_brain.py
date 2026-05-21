"""Tests for robot brain types.

All values derived from refs/robot/33_brain.md (Robot Brains table).
"""

from pydantic import TypeAdapter, ValidationError
import pytest

from ceres.make.robot.brain import (
    AdvancedBrain,
    BasicBrain,
    PrimitiveBrain,
    RobotBrainUnion,
    SelfAwareBrain,
    VeryAdvancedBrain,
)
from ceres.make.robot.skills import BrainSoftware, SkillGrant, SkillPackage


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
        assert PrimitiveBrain().programming_label() == 'Primitive (INT 1)'

    def test_primitive_with_function(self):
        assert PrimitiveBrain(function='clean').programming_label() == 'Primitive (clean) (INT 1)'

    def test_primitive_alert(self):
        assert PrimitiveBrain(function='alert').programming_label() == 'Primitive (alert) (INT 1)'

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

    def test_self_aware_default_tl(self):
        assert SelfAwareBrain().brain_tl == 15


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

    def test_self_aware_roundtrip(self):
        brain = SelfAwareBrain(hardened=True)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert restored.type == 'SELF_AWARE'
        assert isinstance(restored, SelfAwareBrain)
        assert restored.hardened is True


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


class TestVeryAdvancedBrainIntUpgrade:
    """INT upgrade for VeryAdvancedBrain — refs/robot/34_retrotech.md.

    Cost ×2 when the upgrade brings INT to 12 or above.
    TL12 base INT 9, TL13 base INT 10, TL14 base INT 11.
    """

    @pytest.mark.parametrize(
        'brain_tl, int_upgrade, expected_int, expected_cost',
        [
            # TL12 base INT 9: INT 9+1=10, 9+2=11 — below 12, no doubling
            (12, 1, 10, 10_000.0),  # 10×1000
            (12, 2, 11, 110_000.0),  # 10×11×1000
            # TL12 INT 9+3=12 — hits threshold, ×2
            (12, 3, 12, 2_640_000.0),  # 10×11×12×1000×2
            # TL13 base INT 10: INT 10+1=11 — below 12, no doubling
            (13, 1, 11, 11_000.0),  # 11×1000
            # TL13 INT 10+2=12 — hits threshold, ×2
            (13, 2, 12, 264_000.0),  # 11×12×1000×2
            (13, 3, 13, 3_432_000.0),  # 11×12×13×1000×2
            # TL14 base INT 11: INT 11+1=12 — immediately hits threshold
            (14, 1, 12, 24_000.0),  # 12×1000×2
            (14, 2, 13, 312_000.0),  # 12×13×1000×2
            (14, 3, 14, 4_368_000.0),  # 12×13×14×1000×2
        ],
    )
    def test_int_upgrade_cost(self, brain_tl, int_upgrade, expected_int, expected_cost):
        brain = VeryAdvancedBrain(brain_tl=brain_tl, int_upgrade=int_upgrade)
        assert brain.base_int == expected_int
        assert brain._int_upgrade_cost == expected_cost


class TestAdvancedBrainIntUpgrade:
    """INT upgrade — refs/robot/34_retrotech.md.

    INT+n costs n(n+1)/2 BW and product(base_int+1 … base_int+n) × Cr1000.
    Advanced brain max INT = 8+3 = 11 < 12, so the ×2 threshold never applies.
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

    Rule: slots = 1 if robot_size < max(0, computer_x - (robot_tl - entry.tl)) else 0.
    Retrotech discount: each TL after the brain entry's introduction (entry.tl) shrinks
    the minimum-free size by one. brain_tl is the construction TL used to look up the
    entry; entry.tl is the entry's own introduction TL (may be lower).
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

    def test_advanced_tl15_in_tl15_size1_is_free(self):
        # brain_tl=15 → entry.tl=12 (TL12 Advanced entry, computer_x=2)
        # min_free = max(0, 2-(15-12)) = 0; size 1 is not < 0 → free
        assert AdvancedBrain(brain_tl=15).brain_slots(robot_tl=15, robot_size=1) == 0


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


# ─────────────────────────────────────────────────────────────────────────────
# SelfAwareBrain — refs/robot/33_brain.md (Self-Aware rows)
# ─────────────────────────────────────────────────────────────────────────────


class TestSelfAwareBrainTable:
    """refs/robot/33_brain.md — Self-Aware rows: TL15 BW 10 INT 12 MCr1 DM+2."""

    @pytest.mark.parametrize(
        'brain_tl, expected_bw, expected_int, expected_cost, expected_dm',
        [
            (15, 10, 12, 1_000_000.0, 2),
            (16, 15, 13, 1_000_000.0, 2),
            (17, 15, 13, 1_000_000.0, 2),  # TL17 falls back to TL16 entry
        ],
    )
    def test_table_values(self, brain_tl, expected_bw, expected_int, expected_cost, expected_dm):
        brain = SelfAwareBrain(brain_tl=brain_tl)
        assert brain.bandwidth == expected_bw
        assert brain.base_int == expected_int
        assert brain.brain_cost == expected_cost
        assert brain.skill_dm == expected_dm

    def test_remaining_bandwidth_defaults_to_full(self):
        assert SelfAwareBrain().remaining_bandwidth == 10

    def test_hardware_cost_equals_brain_cost_without_skills(self):
        brain = SelfAwareBrain()
        assert brain.hardware_cost == brain.brain_cost


class TestSelfAwareBrainProgrammingLabel:
    def test_tl15_label(self):
        assert SelfAwareBrain(brain_tl=15).programming_label() == 'Self-Aware (INT 12)'

    def test_tl16_label(self):
        assert SelfAwareBrain(brain_tl=16).programming_label() == 'Self-Aware (INT 13)'

    def test_int_upgrade_reflected_in_label(self):
        assert SelfAwareBrain(int_upgrade=1).programming_label() == 'Self-Aware (INT 13)'

    def test_int_upgrade2_reflected_in_label(self):
        assert SelfAwareBrain(int_upgrade=2).programming_label() == 'Self-Aware (INT 14)'


class TestSelfAwareBrainHardened:
    """refs/robot/34_retrotech.md — Hardening adds 50% to brain hardware cost and grants Hardened trait."""

    def test_not_hardened_by_default(self):
        assert SelfAwareBrain().hardened is False

    def test_brain_traits_empty_when_not_hardened(self):
        assert SelfAwareBrain().brain_traits == ()

    def test_brain_traits_has_hardened_when_hardened(self):
        traits = SelfAwareBrain(hardened=True).brain_traits
        assert len(traits) == 1
        assert traits[0].name == 'Hardened'

    def test_not_hardened_brain_cost_is_base(self):
        # TL15: MCr1 base cost
        assert SelfAwareBrain().brain_cost == 1_000_000.0

    def test_hardened_brain_cost_is_1_5x(self):
        # 1_000_000 × 1.5 = 1_500_000
        assert SelfAwareBrain(hardened=True).brain_cost == 1_500_000.0

    def test_hardened_hardware_cost_is_1_5x(self):
        assert SelfAwareBrain(hardened=True).hardware_cost == 1_500_000.0

    def test_not_hardened_hardware_cost_unchanged(self):
        assert SelfAwareBrain(hardened=False).hardware_cost == 1_000_000.0

    def test_hardened_with_bw_upgrade_both_costs_multiply(self):
        # BW delta=10 costs Cr500_000; hardened multiplies all hardware by 1.5
        # brain_cost = (1_000_000 + 500_000) × 1.5 = 2_250_000
        brain = SelfAwareBrain(bandwidth=20, hardened=True)
        assert brain.brain_cost == 2_250_000.0

    def test_not_hardened_with_bw_upgrade(self):
        brain = SelfAwareBrain(bandwidth=20, hardened=False)
        assert brain.brain_cost == 1_500_000.0  # 1_000_000 + 500_000

    def test_skills_cost_not_multiplied_by_hardening(self):
        # Skills are software and are not part of hardware_cost
        brain = SelfAwareBrain(
            hardened=True,
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        # Admin level 1 cost = 100 × 10 = 1000; not ×1.5
        assert brain.brain_cost == 1_500_000.0 + 1_000.0

    def test_hardened_serialises(self):
        brain = SelfAwareBrain(hardened=True)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, SelfAwareBrain)
        assert restored.hardened is True


class TestSelfAwareBrainBandwidthUpgrade:
    """refs/robot/33_brain.md — BW upgrades for Self-Aware at TL15.

    Base BW=10; valid deltas: +10 (Cr500K), +15 (MCr1), +20 (MCr2.5), +25 (MCr5).
    """

    def test_default_bandwidth_is_base(self):
        assert SelfAwareBrain().bandwidth == 10

    @pytest.mark.parametrize(
        'bw, expected_cost',
        [
            (20, 500_000.0),  # delta=10
            (25, 1_000_000.0),  # delta=15
            (30, 2_500_000.0),  # delta=20
            (35, 5_000_000.0),  # delta=25
        ],
    )
    def test_valid_bw_upgrade_accepted_and_costs(self, bw, expected_cost):
        brain = SelfAwareBrain(bandwidth=bw)
        assert brain.bandwidth == bw
        assert brain._bw_upgrade_cost == expected_cost

    def test_bw_upgrade_added_to_hardware_cost(self):
        brain = SelfAwareBrain(bandwidth=20)
        assert brain.hardware_cost == 1_000_000.0 + 500_000.0

    def test_bw_upgrade_adds_one_slot(self):
        brain = SelfAwareBrain(bandwidth=20)
        # SIZE_1, TL15: base brain_slots=1, BW upgrade adds +1 → 2 total
        assert brain.brain_slots(robot_tl=15, robot_size=1) == 2

    def test_invalid_bw_raises(self):
        with pytest.raises(ValidationError):
            SelfAwareBrain(bandwidth=11)  # +1 is not a valid delta

    def test_invalid_bw_below_tl_raises(self):
        # TL14 cannot have a Self-Aware brain at all, but testing boundary
        with pytest.raises(ValidationError):
            SelfAwareBrain(brain_tl=15, bandwidth=11)

    def test_bw_upgrade_serialises(self):
        brain = SelfAwareBrain(bandwidth=25)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, SelfAwareBrain)
        assert restored.bandwidth == 25

    def test_hardware_cost_excludes_skill_packages(self):
        brain = SelfAwareBrain(
            bandwidth=20,
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        # hardware_cost = base + BW upgrade; skill package cost not included
        assert brain.hardware_cost == 1_000_000.0 + 500_000.0


class TestSelfAwareBrainIntUpgrade:
    """INT upgrade for Self-Aware brain — refs/robot/34_retrotech.md.

    All Self-Aware INT upgrades are INT 12+, so upgrade cost is ×2.
    Formula: product(base_int+1 … base_int+n) × 1000 × 2.
    BW cost: n(n+1)/2.
    """

    @pytest.mark.parametrize(
        'int_upgrade, expected_base_int, expected_upgrade_cost, expected_bw_used',
        [
            (1, 13, 26_000.0, 1),  # 13×1000×2; 1×2/2=1 BW
            (2, 14, 364_000.0, 3),  # 13×14×1000×2; 2×3/2=3 BW
            (3, 15, 5_460_000.0, 6),  # 13×14×15×1000×2; 3×4/2=6 BW
        ],
    )
    def test_int_upgrade_cost_bw_and_new_int(
        self, int_upgrade, expected_base_int, expected_upgrade_cost, expected_bw_used
    ):
        brain = SelfAwareBrain(int_upgrade=int_upgrade)
        assert brain.base_int == expected_base_int
        assert brain._int_upgrade_cost == expected_upgrade_cost
        assert brain.used_bandwidth == expected_bw_used

    def test_int_upgrade_included_in_brain_cost(self):
        brain = SelfAwareBrain(int_upgrade=1)
        assert brain.brain_cost == 1_000_000.0 + 26_000.0

    def test_int_upgrade_included_in_hardware_cost(self):
        brain = SelfAwareBrain(int_upgrade=1)
        assert brain.hardware_cost == 1_000_000.0 + 26_000.0

    def test_int_upgrade_increases_skill_dm(self):
        # base skill_dm=2; int_upgrade=2 → skill_dm=4
        assert SelfAwareBrain(int_upgrade=2).skill_dm == 4

    def test_int_upgrade_applies_to_skill_grants(self):
        brain = SelfAwareBrain(
            int_upgrade=1,  # skill_dm=3
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        # level 1 + DM 3 = level 4
        assert SkillGrant('Admin', 4) in brain.skill_grants

    def test_int_upgrade_above_max_raises(self):
        with pytest.raises(ValidationError):
            SelfAwareBrain(int_upgrade=4)

    def test_int_upgrade_reflected_in_remaining_bandwidth(self):
        # INT+1 uses 1 BW; TL15 base BW=10 → 9 remaining
        assert SelfAwareBrain(int_upgrade=1).remaining_bandwidth == 9

    def test_int_upgrade_serialises(self):
        brain = SelfAwareBrain(int_upgrade=2)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, SelfAwareBrain)
        assert restored.int_upgrade == 2
        assert restored.base_int == 14


class TestSelfAwareBrainSkillsAndBandwidth:
    """Installed skills, skill_dm (+2 base), and bandwidth accounting."""

    def test_no_skills_empty_grants(self):
        assert SelfAwareBrain().skill_grants == ()

    def test_no_skills_remaining_bandwidth_is_full(self):
        assert SelfAwareBrain().remaining_bandwidth == 10

    def test_skill_dm_is_2_at_tl15(self):
        assert SelfAwareBrain().skill_dm == 2

    def test_installed_skill_grant_uses_dm(self):
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        # DM+2: level 1 + 2 = level 3
        assert SkillGrant('Admin', 3) in brain.skill_grants

    def test_level0_skill_with_dm2_grants_level2(self):
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Broker', level=0, bandwidth=1),),
        )
        assert SkillGrant('Broker', 2) in brain.skill_grants

    def test_bandwidth_accounting(self):
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=3),),
        )
        assert brain.used_bandwidth == 3
        assert brain.remaining_bandwidth == 7  # 10 - 3

    def test_multiple_skills_bw_summed(self):
        brain = SelfAwareBrain(
            installed_skills=(
                SkillPackage(name='Admin', level=1, bandwidth=1),
                SkillPackage(name='Advocate', level=1, bandwidth=1),
                SkillPackage(name='Broker', level=3, bandwidth=3),
            ),
        )
        assert brain.used_bandwidth == 5
        assert brain.remaining_bandwidth == 5

    def test_skill_cost_added_to_brain_cost(self):
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        # Admin level 1 cost = 100 × 10^1 = 1000
        assert brain.brain_cost == 1_000_000.0 + 1_000.0

    def test_skill_cost_not_in_hardware_cost(self):
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        assert brain.hardware_cost == 1_000_000.0

    def test_level0_specialty_grant_uses_all(self):
        # Level 0 package: speciality in name → "(All)" in grant (unspecialized)
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Electronics (Remote Ops)', level=0, bandwidth=0),),
        )
        assert SkillGrant('Electronics (All)', 2) in brain.skill_grants

    def test_level1_specialty_grant_preserved(self):
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Engineer (J-Drive)', level=1, bandwidth=1),),
        )
        assert SkillGrant('Engineer (J-Drive)', 3) in brain.skill_grants


class TestSelfAwareBrainSlots:
    """brain_slots() for Self-Aware brain — computer_x=10 at TL15.

    Rule: free if robot_size >= max(0, computer_x - (robot_tl - entry.tl)).
    A BW upgrade always adds +1 slot.
    """

    def test_tl15_brain_in_tl15_size1_costs_slot(self):
        # min_free = max(0, 10-0) = 10; size 1 < 10 → 1 slot
        assert SelfAwareBrain().brain_slots(robot_tl=15, robot_size=1) == 1

    def test_tl15_brain_in_tl15_size10_is_free(self):
        # size 10 is not < 10 → 0 slots
        assert SelfAwareBrain().brain_slots(robot_tl=15, robot_size=10) == 0

    def test_retrotech_robot_reduces_requirement(self):
        # TL25 robot, TL15 brain: min_free = max(0, 10-10) = 0; always free
        assert SelfAwareBrain().brain_slots(robot_tl=25, robot_size=1) == 0

    def test_tl16_robot_slightly_reduces_requirement(self):
        # TL16 robot, TL15 brain: min_free = max(0, 10-1) = 9
        # size 8 < 9 → still 1 slot
        assert SelfAwareBrain().brain_slots(robot_tl=16, robot_size=8) == 1

    def test_tl16_robot_size9_is_free(self):
        # min_free = 9; size 9 is not < 9 → free
        assert SelfAwareBrain().brain_slots(robot_tl=16, robot_size=9) == 0

    def test_bw_upgrade_adds_one_slot(self):
        brain = SelfAwareBrain(bandwidth=20)  # delta=10
        # base slots=1 + BW upgrade slot=1 = 2
        assert brain.brain_slots(robot_tl=15, robot_size=1) == 2

    def test_bw_upgrade_with_free_fit_still_adds_slot(self):
        brain = SelfAwareBrain(bandwidth=20)
        # retrotech free (0 base slots) + BW upgrade slot = 1
        assert brain.brain_slots(robot_tl=25, robot_size=1) == 1

    def test_no_bw_upgrade_no_extra_slot(self):
        brain = SelfAwareBrain()
        assert brain.brain_slots(robot_tl=15, robot_size=1) == 1  # only base slot


class TestSelfAwareBrainRoundtrip:
    """Full JSON serialisation/deserialisation for SelfAwareBrain."""

    def test_basic_roundtrip(self):
        brain = SelfAwareBrain(brain_tl=15)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, SelfAwareBrain)
        assert restored.brain_tl == 15

    def test_hardened_field_preserved(self):
        brain = SelfAwareBrain(hardened=True)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, SelfAwareBrain)
        assert restored.hardened is True

    def test_bandwidth_preserved(self):
        brain = SelfAwareBrain(bandwidth=20)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, SelfAwareBrain)
        assert restored.bandwidth == 20

    def test_installed_skills_preserved(self):
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, SelfAwareBrain)
        assert len(restored.installed_skills) == 1
        assert restored.installed_skills[0].name == 'Admin'

    def test_int_upgrade_preserved(self):
        brain = SelfAwareBrain(int_upgrade=2)
        adapter: TypeAdapter[RobotBrainUnion] = TypeAdapter(RobotBrainUnion)
        restored = adapter.validate_json(brain.model_dump_json())
        assert isinstance(restored, SelfAwareBrain)
        assert restored.int_upgrade == 2

    def test_type_discriminator_is_self_aware(self):
        data = SelfAwareBrain().model_dump()
        assert data['type'] == 'SELF_AWARE'


class TestSelfAwareBrainInRobot:
    """Integration: SelfAwareBrain properties visible at the Robot level."""

    def test_hardened_brain_adds_hardened_trait(self):
        from ceres.make.robot import NoneLocomotion, Robot, RobotSize

        robot = Robot(
            name='T',
            tl=15,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=SelfAwareBrain(hardened=True),
        )
        assert any(t.name == 'Hardened' for t in robot.traits)

    def test_not_hardened_brain_no_hardened_trait(self):
        from ceres.make.robot import NoneLocomotion, Robot, RobotSize

        robot = Robot(
            name='T',
            tl=15,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=SelfAwareBrain(hardened=False),
        )
        assert not any(t.name == 'Hardened' for t in robot.traits)

    def test_remaining_bandwidth_in_skills_display(self):
        from ceres.make.robot import NoneLocomotion, Robot, RobotSize

        robot = Robot(
            name='T',
            tl=15,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=SelfAwareBrain(),  # 10 BW, 0 used
        )
        assert '+10 Bandwidth available' in robot.skills_display

    def test_installed_skill_appears_in_skills_display_with_dm(self):
        from ceres.make.robot import NoneLocomotion, Robot, RobotSize

        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        robot = Robot(
            name='T',
            tl=15,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=brain,
        )
        # DM+2: Admin 1 + 2 = Admin 3
        assert 'Admin 3' in robot.skills_display


class TestSelfAwareBrainInstalledSoftware:
    """installed_software: BrainSoftware items consume bandwidth and add to brain_cost."""

    def test_installed_software_defaults_empty(self):
        assert SelfAwareBrain().installed_software == ()

    def test_software_bandwidth_subtracted_from_remaining(self):
        brain = SelfAwareBrain(
            installed_software=(BrainSoftware(name='Universal Translator', bandwidth=3, tl=12, cost=25000.0),),
        )
        # 10 base BW − 3 = 7
        assert brain.remaining_bandwidth == 7

    def test_software_bandwidth_added_to_used(self):
        brain = SelfAwareBrain(
            installed_software=(BrainSoftware(name='Universal Translator', bandwidth=3, tl=12, cost=25000.0),),
        )
        assert brain.used_bandwidth == 3

    def test_software_cost_added_to_brain_cost(self):
        brain = SelfAwareBrain(
            installed_software=(BrainSoftware(name='Universal Translator', bandwidth=3, tl=12, cost=25000.0),),
        )
        assert brain.brain_cost == 1_000_000.0 + 25_000.0

    def test_software_cost_not_in_hardware_cost(self):
        brain = SelfAwareBrain(
            installed_software=(BrainSoftware(name='Universal Translator', bandwidth=3, tl=12, cost=25000.0),),
        )
        assert brain.hardware_cost == 1_000_000.0

    def test_multiple_software_bandwidth_summed(self):
        brain = SelfAwareBrain(
            installed_software=(
                BrainSoftware(name='A', bandwidth=2, tl=12, cost=0.0),
                BrainSoftware(name='B', bandwidth=1, tl=12, cost=0.0),
            ),
        )
        assert brain.used_bandwidth == 3
        assert brain.remaining_bandwidth == 7

    def test_json_roundtrip_with_software(self):
        brain = SelfAwareBrain(
            installed_software=(BrainSoftware(name='Universal Translator', bandwidth=3, tl=12, cost=25000.0),),
        )
        restored = SelfAwareBrain.model_validate_json(brain.model_dump_json())
        assert len(restored.installed_software) == 1
        assert restored.installed_software[0].name == 'Universal Translator'


class TestAdvancedBrainSkillGrantsForRobot:
    """skill_grants_for_robot applies DEX DM for DEX skills, INT DM for others."""

    def test_int_skill_uses_int_dm(self):
        # Admin is INT: level 1 + INT DM 0 (AdvancedBrain TL12) = 1
        brain = AdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        grants = brain.skill_grants_for_robot(dex_dm=5)
        assert SkillGrant('Admin', 1) in grants  # INT DM=0, not dex_dm=5

    def test_dex_skill_uses_dex_dm(self):
        # Flyer is DEX: level 0 + dex_dm=1 = 1
        brain = AdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Flyer (Grav)', level=0, bandwidth=0),),
        )
        grants = brain.skill_grants_for_robot(dex_dm=1)
        assert SkillGrant('Flyer (All)', 1) in grants

    def test_dex_skill_does_not_use_int_dm(self):
        # Stealth level 1, INT DM=0 would give Stealth 1; DEX DM=2 gives Stealth 3
        brain = AdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Stealth', level=1, bandwidth=1),),
        )
        grants = brain.skill_grants_for_robot(dex_dm=2)
        assert SkillGrant('Stealth', 3) in grants  # level 1 + dex_dm 2 = 3

    def test_self_aware_brain_dex_skill_uses_dex_dm(self):
        # SelfAwareBrain INT DM=2; DEX DM=1 for TL15 robot
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Flyer (Grav)', level=0, bandwidth=0),),
        )
        grants = brain.skill_grants_for_robot(dex_dm=1)
        assert SkillGrant('Flyer (All)', 1) in grants  # level 0 + dex_dm 1 = 1

    def test_self_aware_brain_int_skill_uses_int_dm(self):
        # SelfAwareBrain INT DM=2; Admin uses INT
        brain = SelfAwareBrain(
            installed_skills=(SkillPackage(name='Admin', level=1, bandwidth=1),),
        )
        grants = brain.skill_grants_for_robot(dex_dm=1)
        assert SkillGrant('Admin', 3) in grants  # level 1 + INT DM 2 = 3
