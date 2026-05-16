"""Tests for the Manipulator class and Robot manipulator cost/slot effects.

Rules: refs/robot/09_manipulators.md
"""

from math import ceil

import pytest

from ceres.make.robot.chassis import RobotSize
from ceres.make.robot.manipulators import Manipulator


def make_robot(**kwargs):
    from typing import Any

    from ceres.make.robot import PrimitiveBrain, Robot, WheelsLocomotion

    defaults: dict[str, Any] = {
        'name': 'Test',
        'tl': 8,
        'size': RobotSize.SIZE_3,
        'locomotion': WheelsLocomotion(),
        'brain': PrimitiveBrain(),
    }
    defaults.update(kwargs)
    return Robot(**defaults)


class TestManipulatorStats:
    """STR and DEX formulas from refs/robot/09_manipulators.md."""

    def test_default_str_size4(self):
        # default STR = 2 × size − 1
        m = Manipulator()
        assert m.default_str(RobotSize.SIZE_4) == 2 * 4 - 1  # 7

    def test_default_str_size5(self):
        m = Manipulator()
        assert m.default_str(RobotSize.SIZE_5) == 2 * 5 - 1  # 9

    def test_default_dex_tl10(self):
        # default DEX = ceil(TL / 2) + 1
        m = Manipulator()
        assert m.default_dex(10) == ceil(10 / 2) + 1  # 6

    def test_default_dex_tl12(self):
        m = Manipulator()
        assert m.default_dex(12) == ceil(12 / 2) + 1  # 7

    def test_effective_str_no_bonus(self):
        m = Manipulator()
        assert m.effective_str(RobotSize.SIZE_4) == 7

    def test_effective_str_with_bonus(self):
        m = Manipulator(str_bonus=3)
        assert m.effective_str(RobotSize.SIZE_5) == 9 + 3  # 12

    def test_effective_dex_no_bonus(self):
        m = Manipulator()
        assert m.effective_dex(12) == 7

    def test_effective_dex_with_bonus(self):
        m = Manipulator(dex_bonus=4)
        assert m.effective_dex(10) == ceil(10 / 2) + 1 + 4  # 10

    def test_stat_label_size4_tl12(self):
        # Steward Droid: size 4, TL12 → STR 7, DEX 7
        m = Manipulator()
        assert m.stat_label(RobotSize.SIZE_4, 12) == '(STR 7 DEX 7)'

    def test_stat_label_size5_tl10(self):
        # STR = 9, DEX = 6
        m = Manipulator()
        assert m.stat_label(RobotSize.SIZE_5, 10) == '(STR 9 DEX 6)'

    def test_resolved_size_none_uses_robot_size(self):
        m = Manipulator()
        assert m.resolved_size(RobotSize.SIZE_5) == RobotSize.SIZE_5

    def test_resolved_size_explicit_overrides(self):
        m = Manipulator(size=RobotSize.SIZE_3)
        assert m.resolved_size(RobotSize.SIZE_5) == RobotSize.SIZE_3


class TestManipulatorSlots:
    """Slot table from refs/robot/09_manipulators.md.

    Δsize = resolved_size − robot_size; slots = max(1, ceil(pct × base_slots))
    | Δ  | pct  |
    |+2  | 40%  |
    |+1  | 20%  |
    | 0  | 10%  |
    |-1  |  5%  |
    |-2  |  2%  |
    |≤-3 |  1%  |
    """

    def _bound_manip(self, robot_size: RobotSize, manip_size: RobotSize | None = None) -> Manipulator:
        robot = make_robot(size=robot_size)
        m = Manipulator(size=manip_size)
        m.bind(robot)
        return m

    def test_same_size_slots_size5(self):
        # Size 5 base_slots=16; delta=0 → ceil(0.10 × 16) = 2
        m = self._bound_manip(RobotSize.SIZE_5, RobotSize.SIZE_5)
        assert m.slots == 2

    def test_same_size_slots_size3(self):
        # Size 3 base_slots=4; delta=0 → ceil(0.10 × 4) = 1 (min 1)
        m = self._bound_manip(RobotSize.SIZE_3, RobotSize.SIZE_3)
        assert m.slots == 1

    def test_delta_plus1_slots_size5(self):
        # delta=+1 → ceil(0.20 × 16) = 4 (SIZE_6 manip on SIZE_5 robot)
        m = self._bound_manip(RobotSize.SIZE_5, RobotSize.SIZE_6)
        assert m.slots == ceil(0.20 * 16)  # 4

    def test_delta_plus2_slots_size5(self):
        # delta=+2 → ceil(0.40 × 16) = 7
        m = self._bound_manip(RobotSize.SIZE_5, RobotSize.SIZE_7)
        assert m.slots == ceil(0.40 * 16)  # 7

    def test_delta_minus1_slots_size5(self):
        # delta=-1 → ceil(0.05 × 16) = 1
        m = self._bound_manip(RobotSize.SIZE_5, RobotSize.SIZE_4)
        assert m.slots == ceil(0.05 * 16)  # 1

    def test_delta_minus2_slots_size5(self):
        # delta=-2 → ceil(0.02 × 16) = 1 (minimum 1)
        m = self._bound_manip(RobotSize.SIZE_5, RobotSize.SIZE_3)
        assert m.slots == max(1, ceil(0.02 * 16))  # 1

    def test_delta_minus3_slots_size5(self):
        # delta=-3 → ceil(0.01 × 16) = 1
        m = self._bound_manip(RobotSize.SIZE_5, RobotSize.SIZE_2)
        assert m.slots == max(1, ceil(0.01 * 16))  # 1

    def test_minimum_1_slot_enforced(self):
        # Any manipulator gets at least 1 slot
        m = self._bound_manip(RobotSize.SIZE_1, RobotSize.SIZE_1)
        assert m.slots >= 1


class TestManipulatorCost:
    """Manipulator cost = Cr100 × resolved_size (set during bind)."""

    def test_cost_same_size(self):
        robot = make_robot(size=RobotSize.SIZE_5)
        m = Manipulator()
        m.bind(robot)
        assert m.cost == 100.0 * 5

    def test_cost_explicit_size4(self):
        robot = make_robot(size=RobotSize.SIZE_5)
        m = Manipulator(size=RobotSize.SIZE_4)
        m.bind(robot)
        assert m.cost == 100.0 * 4

    def test_build_item_returns_none(self):
        robot = make_robot(size=RobotSize.SIZE_5)
        m = Manipulator()
        m.bind(robot)
        assert m.build_item() is None


class TestManipulatorEnhancementCost:
    """STR/DEX enhancement costs from refs/robot/09_manipulators.md.

    STR cost = Cr100 × resolved_size × str_bonus²
    DEX cost = Cr200 × resolved_size × dex_bonus²
    Both are added to the base manipulator cost (Cr100 × resolved_size).
    """

    def _bound(self, robot_size: RobotSize, tl: int = 10, **kwargs) -> Manipulator:
        robot = make_robot(size=robot_size, tl=tl)
        m = Manipulator(**kwargs)
        m.bind(robot)
        return m

    def test_str_bonus_cost_size5_bonus3(self):
        # Source: STR +3 on SIZE_5 → Cr4500 extra; total = 500 + 4500 = 5000
        m = self._bound(RobotSize.SIZE_5, str_bonus=3)
        assert m.cost == 100.0 * 5 + 100.0 * 5 * 3**2  # 5000

    def test_dex_bonus_cost_size3_bonus4(self):
        # Source: DEX +4 on SIZE_3 → Cr9600 extra; total = 300 + 9600 = 9900
        m = self._bound(RobotSize.SIZE_3, dex_bonus=4)
        assert m.cost == 100.0 * 3 + 200.0 * 3 * 4**2  # 9900

    def test_str_and_dex_combined(self):
        # STR +6, DEX +3 on SIZE_5 TL10: base=500, STR=18000, DEX=9000 → 27500
        m = self._bound(RobotSize.SIZE_5, str_bonus=6, dex_bonus=3)
        expected = 100.0 * 5 + 100.0 * 5 * 6**2 + 200.0 * 5 * 3**2
        assert m.cost == expected  # 27500

    def test_no_bonus_unchanged(self):
        # str_bonus=0, dex_bonus=0 → same as base cost
        m = self._bound(RobotSize.SIZE_5)
        assert m.cost == 100.0 * 5

    def test_str_bonus_at_max_allowed(self):
        # default_str for SIZE_5 = 9; str_bonus=9 is at the limit → no error
        # TL must be high enough that dex limit is not hit (dex_bonus=0 always fine)
        m = self._bound(RobotSize.SIZE_5, tl=12, str_bonus=9)
        assert m.cost == 100.0 * 5 + 100.0 * 5 * 9**2  # 41000

    def test_str_bonus_exceeds_max_raises(self):
        # str_bonus > default_str(SIZE_5)=9 is forbidden
        with pytest.raises(ValueError, match='str_bonus'):
            self._bound(RobotSize.SIZE_5, str_bonus=10)

    def test_dex_bonus_within_tl_limit(self):
        # SIZE_5, TL10: default_dex=6; TL+3=13; max dex_bonus = 13−6 = 7
        m = self._bound(RobotSize.SIZE_5, tl=10, dex_bonus=7)
        assert m.effective_dex(10) == 13  # exactly TL+3

    def test_dex_bonus_exceeds_tl_limit_raises(self):
        # TL10: effective_dex = 6 + 8 = 14 > 13 (TL+3) → forbidden
        with pytest.raises(ValueError, match='dex_bonus'):
            self._bound(RobotSize.SIZE_5, tl=10, dex_bonus=8)


class TestRobotManipulatorCostEffect:
    """_manipulator_cost_effect = sum(m.cost) - 2 × std_cost, capped at -20% BCC."""

    def test_default_pair_no_net_cost(self):
        # Default [Manipulator(), Manipulator()] → net = 0
        robot = make_robot(size=RobotSize.SIZE_5)
        assert robot._manipulator_cost_effect == 0.0

    def test_one_standard_removed_gives_credit(self):
        # 1 removed: net = 500 − 2 × 500 = −500; BCC = 1600 (wheels ×2); cap = −320
        # SIZE_5 basic=1000, wheels multiplier=2 → BCC=2000; cap = −400
        # net = 500 − 1000 = −500; capped at −0.20 × 2000 = −400
        robot = make_robot(size=RobotSize.SIZE_5, manipulators=[Manipulator()])
        bcc = robot.base_chassis_cost  # 2000
        net = robot._manipulator_cost_effect
        assert net == max(500 - 2 * 500, -0.20 * bcc)

    def test_both_removed_capped_at_20pct(self):
        # 0 manipulators: net = 0 − 2 × std; must be capped at -20% BCC
        # SIZE_3 wheels: BCC = 400 × 2 = 800; std = 300; net = -600; cap = -160
        robot = make_robot(size=RobotSize.SIZE_3, manipulators=[])
        bcc = robot.base_chassis_cost  # 800
        assert robot._manipulator_cost_effect == pytest.approx(-0.20 * bcc)

    def test_additional_manipulator_costs_more(self):
        # Three SIZE_5 manipulators: 3×500 = 1500; std=1000; net=+500
        robot = make_robot(
            size=RobotSize.SIZE_5,
            manipulators=[Manipulator(), Manipulator(), Manipulator()],
        )
        assert robot._manipulator_cost_effect == pytest.approx(500.0)


class TestRobotManipulatorSlotEffect:
    """_manipulator_slot_effect = sum(m.slots) - 2 × std_slots."""

    def test_default_pair_no_net_slots(self):
        robot = make_robot(size=RobotSize.SIZE_5)
        assert robot._manipulator_slot_effect == 0

    def test_both_removed_frees_slots(self):
        # SIZE_5: base_slots=16; std_slots = max(1, ceil(0.1 × 16)) = 2
        # effect = 0 − 2×2 = −4 (negative means freed)
        robot = make_robot(size=RobotSize.SIZE_5, manipulators=[])
        assert robot._manipulator_slot_effect == -4

    def test_additional_manipulator_uses_slots(self):
        # SIZE_5, 3 default manips: 3×2 − 2×2 = +2
        robot = make_robot(
            size=RobotSize.SIZE_5,
            manipulators=[Manipulator(), Manipulator(), Manipulator()],
        )
        assert robot._manipulator_slot_effect == 2


class TestRobotAvailableSlots:
    """Freed manipulator slots are added to available_slots."""

    def test_default_pair_no_change(self):
        # SIZE_3, wheels: base=4; default pair → no change
        robot = make_robot(size=RobotSize.SIZE_3, manipulators=[Manipulator(), Manipulator()])
        assert robot.available_slots == 4

    def test_both_removed_adds_freed_slots(self):
        # SIZE_5, wheels: base=16; std_slots=2; both removed → +4 → 20
        robot = make_robot(size=RobotSize.SIZE_5, manipulators=[])
        assert robot.available_slots == 16 + 4

    def test_one_removed_adds_one_std_slot(self):
        # SIZE_5: std_slots=2; one removed → +2 → 18
        robot = make_robot(size=RobotSize.SIZE_5, manipulators=[Manipulator()])
        assert robot.available_slots == 16 + 2


class TestRobotUsedSlots:
    """Additional manipulators beyond the default pair consume used_slots."""

    def test_third_manipulator_uses_slots(self):
        # SIZE_5: extra manip at same size → slots=2; effect=+2
        robot_default = make_robot(size=RobotSize.SIZE_5)
        robot_extra = make_robot(
            size=RobotSize.SIZE_5,
            manipulators=[Manipulator(), Manipulator(), Manipulator()],
        )
        assert robot_extra.used_slots == robot_default.used_slots + 2


class TestRobotTotalCost:
    """Total cost reflects _manipulator_cost_effect."""

    def test_default_pair_no_cost_change(self):
        robot_explicit = make_robot(manipulators=[Manipulator(), Manipulator()])
        robot_default = make_robot()
        assert robot_explicit.total_cost == robot_default.total_cost

    def test_additional_manipulator_adds_cost(self):
        # SIZE_3 TL8; extra SIZE_3 manip costs Cr300
        robot_default = make_robot(size=RobotSize.SIZE_3)
        robot_extra = make_robot(
            size=RobotSize.SIZE_3,
            manipulators=[Manipulator(), Manipulator(), Manipulator()],
        )
        assert robot_extra.total_cost == robot_default.total_cost + 300.0


class TestManipulatorSpecDisplay:
    """Spec row shows STR/DEX stats for each manipulator."""

    def test_default_pair_shows_str_dex(self):
        from ceres.make.robot.spec import RobotSpecSection

        # SIZE_3, TL8: STR = 2×3-1=5, DEX = ceil(8/2)+1=5
        robot = make_robot(size=RobotSize.SIZE_3, tl=8)
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        assert '(STR 5 DEX 5)' in rows[0].value

    def test_default_pair_collapsed_with_2x(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot(size=RobotSize.SIZE_3, tl=8)
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        assert rows[0].value.startswith('2×')

    def test_no_manipulators_shows_dash(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot(manipulators=[])
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        assert rows[0].value == '—'

    def test_three_distinct_manipulators_listed_separately(self):
        from ceres.make.robot.spec import RobotSpecSection

        # Two identical + one smaller → not collapsible
        robot = make_robot(
            size=RobotSize.SIZE_5,
            tl=10,
            manipulators=[Manipulator(), Manipulator(), Manipulator(size=RobotSize.SIZE_3)],
        )
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        value = rows[0].value
        # SIZE_5 TL10: STR=9 DEX=6; SIZE_3 TL10: STR=5 DEX=6
        assert '(STR 9 DEX 6)' in value
        assert '(STR 5 DEX 6)' in value

    def test_steward_droid_smoke(self):
        """Steward Droid: TL12, SIZE_4 walker. refs/robot/101_steward_droid.md"""
        from ceres.make.robot import Robot, WalkerLocomotion
        from ceres.make.robot.brain import BasicBrain
        from ceres.make.robot.spec import RobotSpecSection

        robot = Robot(
            name='Steward Droid',
            tl=12,
            size=RobotSize.SIZE_4,
            locomotion=WalkerLocomotion(),
            brain=BasicBrain(function='servant'),
        )
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        # SIZE_4 TL12: STR = 2×4−1=7; DEX = ceil(12/2)+1=7
        assert '2×' in rows[0].value
        assert '(STR 7 DEX 7)' in rows[0].value


class TestWalkerLegManipulators:
    """Walker leg manipulator rules from refs/robot/09_manipulators.md."""

    def test_leg_manipulator_cost_is_robot_size_times_100(self):
        # SIZE_5 robot: Cr100 × 5 = Cr500 per leg manipulator
        from ceres.make.robot import WalkerLocomotion

        robot = make_robot(
            size=RobotSize.SIZE_5,
            locomotion=WalkerLocomotion(),
            legs=[Manipulator()],
        )
        assert len(robot._leg_manipulators) == 1
        assert robot._leg_manipulators[0].cost == 500.0

    def test_leg_manipulator_slots_equal_same_size_arm(self):
        # SIZE_5: delta=0 → ceil(0.10 × 16) = 2
        from ceres.make.robot import WalkerLocomotion

        robot = make_robot(
            size=RobotSize.SIZE_5,
            locomotion=WalkerLocomotion(),
            legs=[Manipulator()],
        )
        assert robot._leg_manipulators[0].slots == 2

    def test_cost_effect_includes_one_leg_manipulator(self):
        # Default pair (net=0) + 1 leg manip at SIZE_5 = +500
        from ceres.make.robot import WalkerLocomotion

        robot = make_robot(
            size=RobotSize.SIZE_5,
            locomotion=WalkerLocomotion(),
            legs=[Manipulator()],
        )
        assert robot._manipulator_cost_effect == 500.0

    def test_cost_effect_includes_two_leg_manipulators(self):
        # Default pair (net=0) + 2 leg manips at SIZE_5 = +1000
        from ceres.make.robot import WalkerLocomotion

        robot = make_robot(
            size=RobotSize.SIZE_5,
            locomotion=WalkerLocomotion(),
            legs=[Manipulator(), Manipulator()],
        )
        assert robot._manipulator_cost_effect == 1000.0

    def test_slot_effect_includes_leg_manipulators(self):
        # SIZE_5: arm effect=0, leg manip=+2 → total +2
        from ceres.make.robot import WalkerLocomotion

        robot = make_robot(
            size=RobotSize.SIZE_5,
            locomotion=WalkerLocomotion(),
            legs=[Manipulator()],
        )
        assert robot._manipulator_slot_effect == 2

    def test_legs_ignored_for_non_walker(self):
        # legs on a non-walker robot have no effect
        robot = make_robot(legs=[Manipulator()])  # WheelsLocomotion by default
        assert robot._leg_manipulators == []
        assert robot._manipulator_cost_effect == 0.0

    def test_display_includes_leg_manipulator(self):
        # SIZE_3 TL8: STR=5, DEX=5; 1 leg manip should appear in display
        from ceres.make.robot import WalkerLocomotion
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot(
            size=RobotSize.SIZE_3,
            tl=8,
            locomotion=WalkerLocomotion(),
            legs=[Manipulator()],
        )
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        value = rows[0].value
        assert 'Manipulator leg' in value
        assert '(STR 5 DEX 5)' in value

    def test_display_collapses_identical_leg_manipulators(self):
        # 2 identical leg manips → "2× Manipulator leg (STR N DEX M)"
        from ceres.make.robot import WalkerLocomotion
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot(
            size=RobotSize.SIZE_3,
            tl=8,
            locomotion=WalkerLocomotion(),
            legs=[Manipulator(), Manipulator()],
        )
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        assert '2× Manipulator leg' in rows[0].value

    def test_robot_legs_round_trip(self):
        # Robot with leg manipulators must survive JSON round-trip
        from ceres.make.robot import Robot, WalkerLocomotion
        from ceres.make.robot.manipulators import Leg

        robot = make_robot(
            locomotion=WalkerLocomotion(),
            legs=[Leg(), Manipulator(str_bonus=2)],
        )
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert len(restored.legs) == 2
        assert isinstance(restored.legs[0], Leg)
        assert isinstance(restored.legs[1], Manipulator)
        assert restored.legs[1].str_bonus == 2
