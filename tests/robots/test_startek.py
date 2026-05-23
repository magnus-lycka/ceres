# Source: refs/robot/99_startek.md
#
# Phase 2 (resized standard manipulators): SIZE_3 third arm slot/cost on SIZE_5 robot. ✓
# Phase 3 (STR/DEX enhancement): str_bonus=3 on SIZE_5 arms, dex_bonus=4 on SIZE_3 arm. ✓
# Phase 4 (fuller build): Grav primary + Walker secondary, IncreasedArmour, Efficiency, protection,
#   Starship Engineer Toolkit (advanced), Weapon Mount (small). ✓
# Athletics (Strength): pkg level=0 (BW=0) + STR DM+2 (effective STR 12 from str_bonus=3) = 2. ✓
# Gun Combat: pkg level=0 (no speciality, BW=0) + DEX DM+0 (TL14 DEX=8) = 0. ✓ (source: "Gun Combat 0")
# Remaining BW: 5 − 1(int upgrade) − 3(Electronics/Engineer/Mechanic lvl1) = 1. ✓

from types import SimpleNamespace

from ceres.make.robot import GravLocomotion, Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.brain import VeryAdvancedBrain
from ceres.make.robot.options import (
    Efficiency,
    IncreasedArmour,
    Medikit,
    PrisSensor,
    RadiationEnvironmentProtection,
    SecondaryLocomotion,
    StarshipEngineeringToolkit,
    VacuumEnvironmentProtection,
    WeaponMount,
)
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits
from tests.robots import skill_packages as sp

# SIZE_5 TL14: STR = 2×5−1 = 9, DEX = ceil(14/2)+1 = 8
# SIZE_3 TL14: STR = 2×3−1 = 5, DEX = ceil(14/2)+1 = 8
# Source: 2× (STR 12 DEX 8) = SIZE_5 with str_bonus=3 (Phase 3)
#         1× (STR 5 DEX 12) = SIZE_3 with dex_bonus=4 (Phase 3)
# Phase 2 tests use no str/dex bonuses so stats differ from source — expected.


def build_partial_startek() -> Robot:
    """Partial StarTek using WalkerLocomotion (source: Grav+Walker).

    Omits str_bonus/dex_bonus (Phase 3) and unavailable options.
    Uses VeryAdvancedBrain TL14 with INT upgrade to 12.
    """
    return Robot(
        name='StarTek',
        tl=14,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(),
        brain=VeryAdvancedBrain(brain_tl=14, int_upgrade=1),
        manipulators=[
            Manipulator(),
            Manipulator(),
            Manipulator(size=RobotSize.SIZE_3),
        ],
    )


class TestStarTekManipulatorsPhase2:
    """Phase 2: SIZE_3 third arm on SIZE_5 robot.

    refs/robot/99_startek.md — Manipulators: 2× (STR 12 DEX 8), 1× (STR 5 DEX 12)
    The SIZE_3 arm is the key Phase 2 case: delta = 3−5 = −2 → 2% of 16 base slots = 1 slot.
    """

    def test_size3_arm_slots_on_size5_robot(self):
        # delta = −2 → pct = 2% → ceil(0.02 × 16) = 1
        robot = build_partial_startek()
        m = robot.manipulators[2]
        assert m.slots == 1

    def test_size3_arm_cost(self):
        # Cr100 × 3 = Cr300
        robot = build_partial_startek()
        m = robot.manipulators[2]
        assert m.cost == 300.0

    def test_size3_arm_stat_label_no_bonus(self):
        # Phase 2 only (no dex_bonus): STR = 5, DEX = ceil(14/2)+1 = 8
        # Source shows (STR 5 DEX 12) which requires dex_bonus=4 (Phase 3)
        m = Manipulator(size=RobotSize.SIZE_3)
        assert m.stat_label(RobotSize.SIZE_5, 14) == '(STR 5 DEX 8)'

    def test_manipulator_slot_effect(self):
        # SIZE_5 std_slots = max(1, ceil(0.10 × 16)) = 2
        # sum: 2+2+1 = 5; std: 2×2 = 4; effect = +1
        robot = build_partial_startek()
        assert robot._manipulator_slot_effect == 1

    def test_manipulator_cost_effect(self):
        # std_cost = Cr500; sum: 500+500+300 = 1300; net = +300
        robot = build_partial_startek()
        assert robot._manipulator_cost_effect == 300.0

    def test_manipulator_used_slots(self):
        # Default: no extra slots. With SIZE_3 arm: +1 used slot vs. default pair
        from ceres.make.robot import PrimitiveBrain

        default = Robot(
            name='X',
            tl=14,
            size=RobotSize.SIZE_5,
            locomotion=WalkerLocomotion(),
            brain=PrimitiveBrain(),
        )
        startek = build_partial_startek()
        # StarTek used_slots = default brain's slots + 1 extra manipulator slot
        assert startek.used_slots == default.used_slots + 1

    def test_spec_manipulators_shows_size3_stats(self):
        # Without bonuses: SIZE_5 → (STR 9 DEX 8), SIZE_3 → (STR 5 DEX 8)
        robot = build_partial_startek()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        value = rows[0].value
        assert '(STR 9 DEX 8)' in value
        assert '(STR 5 DEX 8)' in value
        assert '× 2' in value  # the two SIZE_5 arms are collapsed


def build_startek() -> Robot:
    """Note: Partial StarTek — omits unavailable options and uses WalkerLocomotion (source: Grav+Walker).

    Omits: Medikit, PRIS Sensor, Vacuum/Radiation Protection, Weapon Mount, Starship Engineer Toolkit.
    Source: refs/robot/99_startek.md — SIZE_5 TL14, Grav+Walker.
    Manipulators: 2× (STR 12 DEX 8), 1× (STR 5 DEX 12).
    """
    return Robot(
        name='StarTek',
        tl=14,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(),
        brain=VeryAdvancedBrain(brain_tl=14, int_upgrade=1),
        manipulators=[
            Manipulator(str_bonus=3),
            Manipulator(str_bonus=3),
            Manipulator(size=RobotSize.SIZE_3, dex_bonus=4),
        ],
    )


class TestStarTekManipulatorsPhase3:
    """Phase 3: STR/DEX enhancements on StarTek arms.

    refs/robot/99_startek.md — 2× (STR 12 DEX 8), 1× (STR 5 DEX 12)
    """

    def test_size5_arm_effective_str(self):
        # str_bonus=3; default_str=9; effective=12
        robot = build_startek()
        m = robot.manipulators[0]
        assert m.effective_str(RobotSize.SIZE_5) == 12

    def test_size3_arm_effective_dex(self):
        # dex_bonus=4; default_dex=8 (TL14); effective=12
        robot = build_startek()
        m = robot.manipulators[2]
        assert m.effective_dex(14) == 12

    def test_size5_arm_cost_includes_str_bonus(self):
        # base=500 + STR cost=100×5×9=4500 → 5000
        robot = build_startek()
        m = robot.manipulators[0]
        assert m.cost == 5000.0

    def test_size3_arm_cost_includes_dex_bonus(self):
        # base=300 + DEX cost=200×3×16=9600 → 9900
        robot = build_startek()
        m = robot.manipulators[2]
        assert m.cost == 9900.0

    def test_manipulator_cost_effect_with_bonuses(self):
        # sum = 5000+5000+9900=19900; std=2×500=1000; net=18900 (positive, no cap)
        robot = build_startek()
        assert robot._manipulator_cost_effect == 18900.0

    def test_spec_shows_correct_stats(self):
        # Source: 2× (STR 12 DEX 8), 1× (STR 5 DEX 12)
        robot = build_startek()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        value = rows[0].value
        assert '(STR 12 DEX 8)' in value
        assert '(STR 5 DEX 12)' in value
        assert '× 2' in value  # the two SIZE_5 arms are collapsed

    def test_stat_label_size3_arm(self):
        # SIZE_3 arm with dex_bonus=4: (STR 5 DEX 12)
        m = Manipulator(size=RobotSize.SIZE_3, dex_bonus=4)
        assert m.stat_label(RobotSize.SIZE_5, 14) == '(STR 5 DEX 12)'


# ── Phase 4: fuller build ─────────────────────────────────────────────────────
#
# GravLocomotion primary + SecondaryLocomotion(WalkerLocomotion) → ATV + Flyer (idle)
# IncreasedArmour(+6): TL12-14 band, SIZE_5 base_slots=16
#   slots = max(ceil(6×0.004×16)=ceil(0.384)=1, ceil(6/3)=2, 1) = 2; cost = 2×1500 = Cr3,000
# Efficiency: cost = 50% × Grav BCC = 0.5×20000 = Cr10,000; endurance ×2
# Endurance: 24 (grav) × 1.5 (TL14) × 2.0 (efficiency) = 72h ✓
# Brain: VeryAdvancedBrain TL14 int_upgrade=1 → INT 12, skill_dm = 1+1 = 2, bandwidth 5
#   remaining BW = 5 − 1(int upgrade) − 3(Electronics/Engineer/Mechanic lvl1) = 1. ✓
# Traits: Armour(+10), ATV, Flyer (idle), IR/UV Vision. Source ✓

_startek_fuller_expected = SimpleNamespace(
    hits=20,
    locomotion='Grav',
    speed='6m',
    tl=14,
    base_armour=4,
    traits='Armour (+10), ATV, Flyer (idle), IR/UV Vision',
    programming='Very Advanced (INT 12)',
    endurance_hours=72,
    remaining_bandwidth=1,  # 5 − 1(int upgrade) − 3(lvl1 skills) = 1. Source: +1 ✓
)


def build_startek_fuller() -> Robot:
    """Source: refs/robot/99_startek.md — SIZE_5 TL14, Grav+Walker.

    Athletics (Strength): pkg level=0 (BW=0) + STR DM+2 = 2 (effective STR 12 from str_bonus=3).
    Gun Combat: pkg level=0 no speciality (BW=0) + DEX DM+0 = 0 (source: 'Gun Combat 0').
    """
    return Robot(
        name='StarTek',
        tl=14,
        size=RobotSize.SIZE_5,
        locomotion=GravLocomotion(),
        brain=VeryAdvancedBrain(
            brain_tl=14,
            int_upgrade=1,
            installed_skills=(
                sp.athletics_strength(level=0, bandwidth=0),
                sp.electronics_all(level=1, bandwidth=1),
                sp.engineer_all(level=1, bandwidth=1),
                sp.explosives(level=0, bandwidth=0),
                sp.gun_combat(level=0, bandwidth=0),
                sp.mechanic(level=1, bandwidth=1),
                sp.medic(level=0, bandwidth=0),
            ),
        ),
        manipulators=[
            Manipulator(str_bonus=3),
            Manipulator(str_bonus=3),
            Manipulator(size=RobotSize.SIZE_3, dex_bonus=4),
        ],
        options=[
            IncreasedArmour(additional=6),
            Efficiency(),
            SecondaryLocomotion(locomotion=WalkerLocomotion()),
            RadiationEnvironmentProtection(),
            VacuumEnvironmentProtection(),
            PrisSensor(),
            Medikit(quality='enhanced'),
            StarshipEngineeringToolkit(quality='advanced'),
            WeaponMount(size='small'),
            *default_suite(),
        ],
    )


class TestStarTekFuller:
    """Phase 4: fuller build — Grav+Walker, armour, protection, toolkit, weapon mount.

    refs/robot/99_startek.md — SIZE_5 TL14.
    """

    def test_hits(self):
        assert build_startek_fuller().hits == _startek_fuller_expected.hits

    def test_base_armour(self):
        assert build_startek_fuller().base_armour == _startek_fuller_expected.base_armour

    def test_traits(self):
        assert format_traits(build_startek_fuller().traits) == _startek_fuller_expected.traits

    def test_programming(self):
        assert build_startek_fuller().brain.programming_label() == _startek_fuller_expected.programming

    def test_endurance(self):
        assert int(build_startek_fuller().base_endurance) == _startek_fuller_expected.endurance_hours

    def test_locomotion_label(self):
        assert build_startek_fuller().locomotion.label() == _startek_fuller_expected.locomotion

    def test_speed_label(self):
        assert build_startek_fuller().speed_label == _startek_fuller_expected.speed

    def test_remaining_bandwidth(self):
        assert build_startek_fuller().brain.remaining_bandwidth == _startek_fuller_expected.remaining_bandwidth

    def test_skills_athletics_strength_2(self):
        # pkg 0 + STR DM+2 (effective STR 12 from str_bonus=3) = 2
        assert 'Athletics (Strength) 2' in build_startek_fuller().skills_display

    def test_skills_electronics_all_3(self):
        assert 'Electronics (All) 3' in build_startek_fuller().skills_display

    def test_skills_engineer_all_3(self):
        assert 'Engineer (All) 3' in build_startek_fuller().skills_display

    def test_skills_explosives_2(self):
        # pkg 0 + INT DM+2 = 2
        assert 'Explosives 2' in build_startek_fuller().skills_display

    def test_skills_mechanic_3(self):
        assert 'Mechanic 3' in build_startek_fuller().skills_display

    def test_skills_medic_2(self):
        # pkg 0 + INT DM+2 = 2
        assert 'Medic 2' in build_startek_fuller().skills_display

    def test_armour_trait_is_10(self):
        robot = build_startek_fuller()
        trait_names = [str(t) for t in robot.traits]
        assert 'Armour (+10)' in trait_names

    def test_atv_from_secondary_walker(self):
        robot = build_startek_fuller()
        trait_names = [t.name for t in robot.traits]
        assert 'ATV' in trait_names

    def test_flyer_idle_from_grav(self):
        robot = build_startek_fuller()
        trait_strs = [str(t) for t in robot.traits]
        assert 'Flyer (idle)' in trait_strs

    def test_pris_sensor_ir_uv_vision(self):
        robot = build_startek_fuller()
        trait_names = [t.name for t in robot.traits]
        assert 'IR/UV Vision' in trait_names

    def test_spec_options_has_vacuum_protection(self):
        spec = build_startek_fuller().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Vacuum Environment Protection' in value

    def test_spec_options_has_radiation_protection(self):
        spec = build_startek_fuller().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Radiation Environment Protection' in value

    def test_spec_options_has_medikit_enhanced(self):
        spec = build_startek_fuller().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Medikit (enhanced)' in value

    def test_spec_options_has_pris_sensor(self):
        spec = build_startek_fuller().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'PRIS Sensor' in value

    def test_spec_options_has_starship_toolkit(self):
        spec = build_startek_fuller().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Starship Engineer Toolkit (advanced)' in value

    def test_spec_options_has_weapon_mount_small(self):
        spec = build_startek_fuller().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Weapon Mount (small)' in value

    def test_skills_gun_combat_0(self):
        # pkg 0 (no speciality) + DEX DM+0 (TL14 DEX=8) = 0. Source: "Gun Combat 0"
        assert 'Gun Combat 0' in build_startek_fuller().skills_display

    def test_json_roundtrip(self):
        robot = build_startek_fuller()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'StarTek'
        assert restored.tl == _startek_fuller_expected.tl
        assert isinstance(restored.locomotion, GravLocomotion)
        assert isinstance(restored.brain, VeryAdvancedBrain)
        assert restored.brain.int_upgrade == 1
        assert len(restored.brain.installed_skills) == 7
