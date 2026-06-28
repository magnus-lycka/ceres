"""Approval snapshots for ship Typst/PDF rendering.

The Suleiman and Dragon cover the two most distinct rendering scenarios:
Suleiman is a small ship with a sidebar and crew notes; Dragon exercises
multi-section weapons and armoured bulkhead notes.
PDF smoke tests (bytes start with %PDF) are in tests/unit/make/ship/test_report.py.
"""

import pytest

from ceres.make.ship.report import render_ship_spec_typst
from tests.approval.ship.e2e.test_dragon import build_dragon
from tests.approval.ship.e2e.test_suleiman import build_suleiman
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


@pytest.mark.approval
def test_suleiman_typst(snapshot):
    """Suleiman Typst source — default a4 page size."""
    spec = build_suleiman().build_spec()
    src = render_ship_spec_typst(spec)
    src_letter = render_ship_spec_typst(spec, page_size='us-letter')
    snap = AnnotatedSnapshot({'typst_source': src})
    snap.annotate('us_letter_page_size_in_source', str('"us-letter"' in src_letter))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_dragon_typst(snapshot):
    """Dragon Typst source — exercises bulkhead notes and multi-turret weapons."""
    spec = build_dragon().build_spec()
    src = render_ship_spec_typst(spec)
    snap = AnnotatedSnapshot({'typst_source': src})
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
