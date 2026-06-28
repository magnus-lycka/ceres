"""Approval snapshots for robot Typst/PDF rendering.

Two robots (Domestic Servant and Lab Control) are rendered to Typst source
and snapshotted. The page-size parameter is tracked via annotation.
PDF smoke tests (bytes start with %PDF) are in tests/unit/make/robot/test_report.py.
"""

import pytest

from ceres.make.robot.report import render_robot_spec_typst
from tests.approval.robot.e2e.test_domestic_servant import build_domestic_servant
from tests.approval.robot.e2e.test_lab_control_robot_basic import build_basic_lab_control_robot
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


@pytest.mark.approval
def test_domestic_servant_typst(snapshot):
    """Domestic Servant Typst source — default a4 page size."""
    spec = build_domestic_servant().build_spec()
    src = render_robot_spec_typst(spec)
    src_letter = render_robot_spec_typst(spec, page_size='us-letter')
    snap = AnnotatedSnapshot({'typst_source': src})
    snap.annotate('us_letter_page_size_in_source', str('"us-letter"' in src_letter))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_lab_control_robot_typst(snapshot):
    """Lab Control Robot Typst source — verifies a different robot renders without error."""
    spec = build_basic_lab_control_robot().build_spec()
    src = render_robot_spec_typst(spec)
    snap = AnnotatedSnapshot({'typst_source': src})
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
