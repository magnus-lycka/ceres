"""Unit tests for make/robot/base.py — RobotBase assembly interface."""

from ceres.make.robot.base import RobotBase
from ceres.make.robot.chassis import RobotSize
from ceres.make.robot.locomotion import WalkerLocomotion


class TestRobotBase:
    def test_parts_of_type_returns_empty_list(self):
        base = RobotBase(tl=12, size=RobotSize.SIZE_3, locomotion=WalkerLocomotion())
        assert base.parts_of_type(object) == []

    def test_tl_stored(self):
        base = RobotBase(tl=14, size=RobotSize.SIZE_5, locomotion=WalkerLocomotion())
        assert base.tl == 14

    def test_size_stored(self):
        base = RobotBase(tl=12, size=RobotSize.SIZE_2, locomotion=WalkerLocomotion())
        assert base.size == RobotSize.SIZE_2
