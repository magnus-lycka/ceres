# Source: refs/robot/121_hiver.md
#
# Partial build: many options not yet implemented (Agricultural Equipment, Autobar enhanced,
# Autochef enhanced, Olfactory Sensor advanced, PRIS Sensor, Storage Compartment refrigerated).
# Tests focus on Phase 4 (walker leg manipulators).
#
# SIZE_5 TL15: default STR = 2×5−1 = 9, default DEX = ceil(15/2)+1 = 9
# Source: 4x (STR 9 DEX 9), 2x Manipulator legs (STR 9 DEX 9)

from ceres.make.robot import Manipulator, Robot, RobotSize, WalkerLocomotion
from ceres.make.robot.brain import AdvancedBrain
from ceres.make.robot.spec import RobotSpecSection


def build_gardener_servant() -> Robot:
    """Note: Partial Gardener Servant — manipulators and locomotion only.

    Omits options not yet implemented.
    Source: refs/robot/121_hiver.md — Gardener Servant, SIZE_5 TL15 Walker.
    4 arm manipulators + 2 leg manipulators, all SIZE_5.
    """
    return Robot(
        name='Gardener Servant',
        tl=15,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(),
        brain=AdvancedBrain(brain_tl=15),
        manipulators=[Manipulator(), Manipulator(), Manipulator(), Manipulator()],
        legs=[Manipulator(), Manipulator()],
        options=[],
    )


class TestGardenerServantManipulatorsPhase4:
    """Phase 4: walker leg manipulators on Gardener Servant.

    refs/robot/121_hiver.md — 4x (STR 9 DEX 9), 2x Manipulator legs (STR 9 DEX 9)
    """

    def test_leg_manipulators_count(self):
        robot = build_gardener_servant()
        assert len(robot._leg_manipulators) == 2

    def test_leg_manipulator_stats(self):
        # SIZE_5 TL15: STR = 9, DEX = ceil(15/2)+1 = 9
        robot = build_gardener_servant()
        m = robot._leg_manipulators[0]
        assert m.effective_str(RobotSize.SIZE_5) == 9
        assert m.effective_dex(15) == 9

    def test_leg_manipulator_cost(self):
        # Cr100 × 5 = Cr500 per leg manipulator
        robot = build_gardener_servant()
        assert robot._leg_manipulators[0].cost == 500.0

    def test_manipulator_cost_effect(self):
        # 4 arm manips: sum=4×500=2000; std=2×500=1000; arm net=+1000
        # 2 leg manips: +2×500=+1000
        # total = +2000
        robot = build_gardener_servant()
        assert robot._manipulator_cost_effect == 2000.0

    def test_manipulator_slot_effect(self):
        # SIZE_5 std_slots=2; 4 arm manips: 4×2=8; arm effect=8−4=+4
        # 2 leg manips: no slot cost (RIR-007); total = +4
        robot = build_gardener_servant()
        assert robot._manipulator_slot_effect == 4

    def test_spec_shows_arm_manipulators(self):
        robot = build_gardener_servant()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        value = rows[0].value
        assert '× 4' in value
        assert '(STR 9 DEX 9)' in value

    def test_spec_shows_leg_manipulators(self):
        # Source: 2x Manipulator legs (STR 9 DEX 9)
        robot = build_gardener_servant()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        value = rows[0].value
        assert 'Manipulator leg (STR 9 DEX 9) × 2' in value

    def test_spec_arms_and_legs_both_present(self):
        robot = build_gardener_servant()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        value = rows[0].value
        assert '(STR 9 DEX 9) × 4' in value
        assert 'Manipulator leg (STR 9 DEX 9) × 2' in value
