"""Unit tests for spec.py — RobotSpec row ordering and section filtering."""

from ceres.make.robot.spec import RobotSpec, RobotSpecRow, RobotSpecSection


def _make_spec() -> RobotSpec:
    spec = RobotSpec(name='Test', tl=8)
    spec.add_row(RobotSpecRow(section=RobotSpecSection.PROGRAMMING, label='Programming', value='Primitive'))
    spec.add_row(RobotSpecRow(section=RobotSpecSection.ROBOT, label='Robot', value='Hits 8'))
    spec.add_row(RobotSpecRow(section=RobotSpecSection.TRAITS, label='Traits', value='Small (-2)'))
    return spec


class TestRobotSpec:
    def test_rows_in_section_order(self):
        spec = _make_spec()
        sections = [r.section for r in spec.rows]
        assert sections.index(RobotSpecSection.ROBOT) < sections.index(RobotSpecSection.TRAITS)
        assert sections.index(RobotSpecSection.TRAITS) < sections.index(RobotSpecSection.PROGRAMMING)

    def test_rows_for_section_filters_correctly(self):
        spec = _make_spec()
        robot_rows = spec.rows_for_section(RobotSpecSection.ROBOT)
        assert len(robot_rows) == 1
        assert robot_rows[0].value == 'Hits 8'

    def test_rows_for_missing_section_empty(self):
        spec = _make_spec()
        assert spec.rows_for_section(RobotSpecSection.OPTIONS) == []
