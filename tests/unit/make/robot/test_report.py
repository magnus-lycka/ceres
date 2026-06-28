"""Unit tests for robot report rendering — smoke tests only."""

import pytest


@pytest.mark.slow
def test_render_robot_spec_pdf_returns_pdf_bytes():
    from ceres.make.robot.report import render_robot_spec_pdf
    from tests.approval.robot.e2e.test_domestic_servant import build_domestic_servant

    pdf = render_robot_spec_pdf(build_domestic_servant().build_spec())
    assert pdf[:4] == b'%PDF'


@pytest.mark.slow
def test_render_robot_pdf_returns_pdf_bytes():
    from ceres.make.robot.report import render_robot_pdf
    from tests.approval.robot.e2e.test_domestic_servant import build_domestic_servant

    pdf = render_robot_pdf(build_domestic_servant())
    assert pdf[:4] == b'%PDF'
