# Source: refs/robot/99_startek.md
#
# Phase 2 (resized standard manipulators): SIZE_3 third arm slot/cost on SIZE_5 robot. ✓
# Phase 3 (STR/DEX enhancement): str_bonus=3 on SIZE_5 arms, dex_bonus=4 on SIZE_3 arm. ✓
#
# Full robot build not attempted here: combined Grav+Walker locomotion not modeled,
# several options (Medikit, PRIS Sensor, Vacuum/Radiation Protection, Weapon Mount,
# Starship Engineer Toolkit) not yet implemented.

from ceres.make.robot import Manipulator, Robot, RobotSize, WalkerLocomotion
from ceres.make.robot.brain import VeryAdvancedBrain
from ceres.make.robot.spec import RobotSpecSection

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
        assert '2×' in value  # the two SIZE_5 arms are collapsed


def build_startek() -> Robot:
    """StarTek with STR/DEX enhancements.

    Two SIZE_5 arms with str_bonus=3 and one SIZE_3 arm with dex_bonus=4.
    Source: refs/robot/99_startek.md — Manipulators: 2× (STR 12 DEX 8), 1× (STR 5 DEX 12)
    Omits unavailable options (Medikit, PRIS Sensor, Vacuum/Radiation Protection,
    Weapon Mount, Starship Engineer Toolkit) and uses WalkerLocomotion (source: Grav+Walker).
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
        assert '2×' in value  # the two SIZE_5 arms are collapsed

    def test_stat_label_size3_arm(self):
        # SIZE_3 arm with dex_bonus=4: (STR 5 DEX 12)
        m = Manipulator(size=RobotSize.SIZE_3, dex_bonus=4)
        assert m.stat_label(RobotSize.SIZE_5, 14) == '(STR 5 DEX 12)'
