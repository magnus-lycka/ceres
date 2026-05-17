"""Tests for default_suite() function and default-suite option classes.

Rule sources:
  refs/robot/10_default_suite.md   (default suite items and substitution rules)
  refs/robot/14_encryption_module.md (RobotTransceiver and VideoScreen tables)
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
from ceres.make.robot.spec import RobotSpecSection

_UNSET = object()


def _robot(
    *,
    name: str = 'T',
    tl: int = 8,
    size: RobotSize = RobotSize.SIZE_3,
    locomotion=None,
    brain=None,
    options=_UNSET,
) -> Robot:
    kwargs: dict = {
        'name': name,
        'tl': tl,
        'size': size,
        'locomotion': locomotion if locomotion is not None else WheelsLocomotion(),
        'brain': brain if brain is not None else PrimitiveBrain(),
    }
    if options is not _UNSET:
        kwargs['options'] = options
    return Robot(**kwargs)


# ── default_suite() function ─────────────────────────────────────────────────


class TestDefaultSuiteFunction:
    """refs/robot/10_default_suite.md — five zero-cost zero-slot items."""

    def test_returns_five_items_by_default(self):
        items = default_suite()
        assert len(items) == 5

    def test_all_items_are_robot_part_mixin(self):
        for item in default_suite():
            assert isinstance(item, RobotPartMixin)

    def test_all_items_have_zero_cost(self):
        for item in default_suite():
            assert item.cost == 0.0

    def test_all_items_have_zero_slots(self):
        for item in default_suite():
            assert item.slots == 0

    def test_default_contains_visual_spectrum_sensor(self):
        assert any(isinstance(i, VisualSpectrumSensor) for i in default_suite())

    def test_default_contains_voder_speaker(self):
        assert any(isinstance(i, VoderSpeaker) for i in default_suite())

    def test_default_contains_auditory_sensor(self):
        assert any(isinstance(i, AuditorySensor) for i in default_suite())

    def test_default_contains_wireless_data_link(self):
        assert any(isinstance(i, WirelessDataLink) for i in default_suite())

    def test_default_contains_transceiver_5km_improved(self):
        transceivers = [i for i in default_suite() if isinstance(i, RobotTransceiver)]
        assert len(transceivers) == 1
        assert transceivers[0].range_km == 5
        assert transceivers[0].quality == 'improved'

    def test_transceiver_in_default_suite_is_zero_cost(self):
        transceivers = [i for i in default_suite() if isinstance(i, RobotTransceiver)]
        assert transceivers[0].cost == 0.0

    def test_drone_flag_adds_drone_interface(self):
        items = default_suite(wireless=False, drone=True)
        assert any(isinstance(i, DroneInterface) for i in items)
        assert not any(isinstance(i, WirelessDataLink) for i in items)

    def test_basic_transceiver_flag(self):
        items = default_suite(improved_transceiver=False, basic_transceiver=True)
        transceivers = [i for i in items if isinstance(i, RobotTransceiver)]
        assert len(transceivers) == 1
        assert transceivers[0].quality == 'basic'
        assert transceivers[0].cost == 0.0

    def test_screen_flag_adds_video_screen_basic(self):
        items = default_suite(see=False, screen=True)
        screens = [i for i in items if isinstance(i, VideoScreen)]
        assert len(screens) == 1
        assert screens[0].quality == 'basic'
        assert screens[0].cost == 0.0

    def test_too_many_true_flags_raises(self):
        with pytest.raises(ValueError, match='at most 5'):
            default_suite(drone=True, basic_transceiver=True)  # 7 flags True → error

    def test_exactly_five_true_flags_is_valid(self):
        # see, hear, wireless, drone, screen = 5 (speak=False, improved_transceiver=False)
        items = default_suite(speak=False, improved_transceiver=False, drone=True, screen=True)
        assert len(items) == 5

    def test_remove_all_returns_empty(self):
        items = default_suite(see=False, speak=False, hear=False, wireless=False, improved_transceiver=False)
        assert items == []


# ── Robot integration ────────────────────────────────────────────────────────


class TestDefaultSuiteInRobot:
    """Default suite items appear in options list and option row."""

    def test_robot_default_options_equals_default_suite(self):
        robot = _robot()
        ds = default_suite()
        assert len(robot.options) == len(ds)
        for opt_r, opt_ds in zip(robot.options, ds):
            assert type(opt_r) is type(opt_ds)

    def test_default_suite_items_have_zero_cost_in_robot(self):
        robot = _robot()
        for opt in robot.options:
            assert opt.cost == 0.0

    def test_default_suite_in_options_row(self):
        robot = _robot()
        spec = robot.build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Auditory Sensor' in value
        assert 'Visual Spectrum Sensor' in value
        assert 'Voder Speaker' in value
        assert 'Wireless Data Link' in value
        assert 'Transceiver 5km (improved)' in value

    def test_default_suite_does_not_count_toward_slot_usage(self):
        # SIZE_3 TL8: quota = 5 + 3 + 8 = 16; default suite = 5 zero-slot → excess = 0
        robot = _robot(size=RobotSize.SIZE_3, tl=8)
        assert robot.used_slots == 0
        assert robot.remaining_slots == robot.available_slots

    def test_default_suite_cost_is_zero(self):
        robot_with_suite = _robot()
        robot_without_suite = _robot(options=[])
        assert robot_with_suite.total_cost == robot_without_suite.total_cost

    def test_no_default_suite_section_in_detail(self):
        robot = _robot()
        spec = robot.build_spec()
        titles = [s.title for s in spec.detail_sections]
        assert 'Default Suite' not in titles

    def test_default_suite_items_in_options_detail_section(self):
        robot = _robot()
        spec = robot.build_spec()
        titles = [s.title for s in spec.detail_sections]
        assert 'Options' in titles
        opts_section = next(s for s in spec.detail_sections if s.title == 'Options')
        names = [r.name for r in opts_section.rows]
        assert 'Auditory Sensor' in names
        assert 'Visual Spectrum Sensor' in names

    def test_zero_slot_quota_includes_default_suite(self):
        # SIZE_1 TL8: quota = 5 + 1 + 8 = 14
        # With default suite (5) + 6 extra zero-slot → 11 total → excess = 0
        from ceres.make.robot import NoneLocomotion
        from ceres.make.robot.options import DroneInterface as DI

        robot = _robot(
            size=RobotSize.SIZE_1,
            tl=8,
            locomotion=NoneLocomotion(),
            options=[*default_suite(), DI(), DI(), DI(), DI(), DI(), DI()],
        )
        assert robot.used_slots == 0


# ── RobotTransceiver ─────────────────────────────────────────────────────────


class TestRobotTransceiver:
    """refs/robot/14_encryption_module.md — zero-slot robot transceiver table."""

    @pytest.mark.parametrize(
        'quality, range_km, expected_tl, expected_cost',
        [
            ('basic', 5, 7, 250.0),
            ('improved', 5, 8, 100.0),
            ('improved', 50, 8, 500.0),
            ('enhanced', 50, 10, 250.0),
            ('advanced', 50, 13, 100.0),
            ('improved', 500, 9, 1000.0),
            ('enhanced', 500, 11, 500.0),
            ('advanced', 500, 14, 250.0),
            ('improved', 5000, 9, 5000.0),
            ('enhanced', 5000, 12, 1000.0),
            ('advanced', 5000, 15, 500.0),
        ],
    )
    def test_table_values(self, quality, range_km, expected_tl, expected_cost):
        t = RobotTransceiver(range_km=range_km, quality=quality)
        assert t.tl == expected_tl
        assert t.cost == expected_cost

    def test_slots_is_zero(self):
        assert RobotTransceiver(range_km=5, quality='improved').slots == 0

    def test_item_label_small_range(self):
        robot = _robot()
        t = RobotTransceiver(range_km=5, quality='improved')
        t.bind(robot)
        assert t.notes.item_message == 'Transceiver 5km (improved)'

    def test_item_label_large_range_formatted(self):
        robot = _robot(tl=12)
        t = RobotTransceiver(range_km=5000, quality='enhanced')
        t.bind(robot)
        assert t.notes.item_message == 'Transceiver 5,000km (enhanced)'

    def test_paid_transceiver_cost_added_to_robot(self):
        robot_base = _robot(options=[])
        robot_with = _robot(options=[RobotTransceiver(range_km=500, quality='improved')])
        assert robot_with.total_cost == robot_base.total_cost + 1000.0

    def test_paid_transceiver_in_options_row(self):
        robot = _robot(options=[RobotTransceiver(range_km=500, quality='improved')])
        spec = robot.build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Transceiver 500km (improved)' in value

    def test_tl_check_error_if_robot_tl_too_low(self):
        # enhanced 50km requires TL10; robot at TL8 should produce error
        robot = _robot(tl=8, options=[RobotTransceiver(range_km=50, quality='enhanced')])
        errors = [n for n in robot.options[0].notes if n.category.value == 'error']
        assert errors

    def test_is_default_suite_true_forces_zero_cost(self):
        t = RobotTransceiver(range_km=500, quality='improved', is_default_suite=True)
        assert t.cost == 0.0
        assert t.tl == 9  # TL still set from table


# ── VideoScreen ───────────────────────────────────────────────────────────────


class TestVideoScreen:
    """refs/robot/14_encryption_module.md — Video Screen table."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_cost',
        [
            ('basic', 7, 200.0),
            ('improved', 8, 500.0),
            ('advanced', 10, 2000.0),
        ],
    )
    def test_table_values_outside_default_suite(self, quality, expected_tl, expected_cost):
        vs = VideoScreen(quality=quality)
        assert vs.tl == expected_tl
        assert vs.cost == expected_cost

    def test_is_default_suite_forces_zero_cost(self):
        vs = VideoScreen(quality='basic', is_default_suite=True)
        assert vs.cost == 0.0
        assert vs.tl == 7  # TL still from table

    def test_item_label(self):
        robot = _robot()
        vs = VideoScreen(quality='improved')
        vs.bind(robot)
        assert vs.notes.item_message == 'Video Screen (improved)'

    def test_paid_screen_cost_added_to_robot(self):
        robot_base = _robot(options=[])
        robot_with = _robot(options=[VideoScreen(quality='improved')])
        assert robot_with.total_cost == robot_base.total_cost + 500.0
