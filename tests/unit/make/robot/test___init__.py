"""Unit tests for robot __init__ — default_suite() function.

Rule sources:
  refs/robot/10_default_suite.md   (default suite items and substitution rules)
"""

import pytest

from ceres.make.robot import (
    PrimitiveBrain,
    Robot,
    RobotSize,
    WheelsLocomotion,
    default_suite,
)
from ceres.make.robot.options import (
    AuditorySensor,
    DroneInterface,
    RobotTransceiver,
    VideoScreen,
    VisualSpectrumSensor,
    VoderSpeaker,
    WirelessDataLink,
)
from ceres.make.robot.parts import RobotPartMixin

_UNSET = object()


def _robot(*, tl: int = 8, size: RobotSize = RobotSize.SIZE_3, options=_UNSET) -> Robot:
    kwargs: dict = {
        'name': 'T',
        'tl': tl,
        'size': size,
        'locomotion': WheelsLocomotion(),
        'brain': PrimitiveBrain(),
    }
    if options is not _UNSET:
        kwargs['options'] = options
    return Robot(**kwargs)


class TestDefaultSuiteFunction:
    """refs/robot/10_default_suite.md — five zero-cost zero-slot items."""

    def test_returns_five_items_by_default(self):
        assert len(default_suite()) == 5

    def test_all_items_are_robot_part_mixin(self):
        assert all(isinstance(i, RobotPartMixin) for i in default_suite())

    def test_all_items_have_zero_cost(self):
        assert all(i.cost == 0.0 for i in default_suite())

    def test_all_items_have_zero_slots(self):
        assert all(i.slots == 0 for i in default_suite())

    def test_default_contains_expected_types(self):
        items = default_suite()
        assert any(isinstance(i, VisualSpectrumSensor) for i in items)
        assert any(isinstance(i, VoderSpeaker) for i in items)
        assert any(isinstance(i, AuditorySensor) for i in items)
        assert any(isinstance(i, WirelessDataLink) for i in items)

    def test_default_transceiver_is_5km_improved(self):
        transceivers = [i for i in default_suite() if isinstance(i, RobotTransceiver)]
        assert len(transceivers) == 1
        assert transceivers[0].range_km == 5
        assert transceivers[0].quality == 'improved'
        assert transceivers[0].cost == 0.0

    def test_drone_flag_adds_drone_interface_removes_wireless(self):
        items = default_suite(wireless=False, drone=True)
        assert any(isinstance(i, DroneInterface) for i in items)
        assert not any(isinstance(i, WirelessDataLink) for i in items)

    def test_basic_transceiver_flag(self):
        transceivers = [
            i
            for i in default_suite(improved_transceiver=False, basic_transceiver=True)
            if isinstance(i, RobotTransceiver)
        ]
        assert len(transceivers) == 1
        assert transceivers[0].quality == 'basic'
        assert transceivers[0].cost == 0.0

    def test_screen_flag_adds_video_screen_basic(self):
        screens = [i for i in default_suite(see=False, screen=True) if isinstance(i, VideoScreen)]
        assert len(screens) == 1
        assert screens[0].quality == 'basic'
        assert screens[0].cost == 0.0

    def test_too_many_true_flags_raises(self):
        with pytest.raises(ValueError, match='at most 5'):
            default_suite(drone=True, basic_transceiver=True)

    def test_remove_all_returns_empty(self):
        assert default_suite(see=False, speak=False, hear=False, wireless=False, improved_transceiver=False) == []


class TestDefaultSuiteInRobot:
    def test_robot_default_options_matches_default_suite(self):
        robot = _robot()
        ds = default_suite()
        assert len(robot.options) == len(ds)
        assert all(type(a) is type(b) for a, b in zip(robot.options, ds, strict=True))

    def test_default_suite_does_not_count_toward_slot_usage(self):
        robot = _robot(size=RobotSize.SIZE_3, tl=8)
        assert robot.used_slots == 0

    def test_default_suite_cost_is_zero(self):
        assert _robot().total_cost == _robot(options=[]).total_cost
