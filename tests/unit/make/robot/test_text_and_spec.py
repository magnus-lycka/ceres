"""Tests for formatting helpers (text.py) and RobotSpec (spec.py)."""

from ceres.make.robot.chassis import Trait
from ceres.make.robot.spec import RobotSpec, RobotSpecRow, RobotSpecSection
from ceres.make.robot.text import format_credits, format_traits


class TestFormatTraits:
    def test_empty_list_returns_dash(self):
        assert format_traits([]) == '—'

    def test_single_trait(self):
        assert format_traits([Trait('ATV')]) == 'ATV'

    def test_multiple_traits(self):
        result = format_traits([Trait('Armour', '+2'), Trait('Small', -2)])
        assert result == 'Armour (+2), Small (-2)'


class TestFormatCredits:
    def test_hundreds(self):
        assert format_credits(400.0) == 'Cr400'

    def test_thousands(self):
        assert format_credits(12_000.0) == 'Cr12,000'

    def test_millions(self):
        assert format_credits(1_000_000.0) == 'MCr1'

    def test_fractional_millions(self):
        assert format_credits(2_500_000.0) == 'MCr2.5'


class TestRobotSpec:
    def _make_spec(self) -> RobotSpec:
        spec = RobotSpec(name='Test', tl=8)
        spec.add_row(RobotSpecRow(section=RobotSpecSection.PROGRAMMING, label='Programming', value='Primitive'))
        spec.add_row(RobotSpecRow(section=RobotSpecSection.ROBOT, label='Robot', value='Hits 8'))
        spec.add_row(RobotSpecRow(section=RobotSpecSection.TRAITS, label='Traits', value='Small (-2)'))
        return spec

    def test_rows_in_section_order(self):
        spec = self._make_spec()
        sections = [r.section for r in spec.rows]
        # ROBOT comes before TRAITS which comes before PROGRAMMING
        assert sections.index(RobotSpecSection.ROBOT) < sections.index(RobotSpecSection.TRAITS)
        assert sections.index(RobotSpecSection.TRAITS) < sections.index(RobotSpecSection.PROGRAMMING)

    def test_rows_for_section_filters_correctly(self):
        spec = self._make_spec()
        robot_rows = spec.rows_for_section(RobotSpecSection.ROBOT)
        assert len(robot_rows) == 1
        assert robot_rows[0].value == 'Hits 8'

    def test_rows_for_missing_section_empty(self):
        spec = self._make_spec()
        assert spec.rows_for_section(RobotSpecSection.OPTIONS) == []
