"""Approval snapshot for ship HTML rendering.

Uses the Suleiman scout/courier as the primary representative design.
The snapshot captures the full HTML output; structural assertions (grid layout,
section headers, power/cost tables, theme toggle) are implicit in the snapshot —
any template change that removes or renames a key element will fail the test.
"""

import pytest

from ceres.report import render_ship_spec_html
from tests.approval.ship.e2e.test_suleiman import build_suleiman
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


@pytest.mark.approval
def test_suleiman_html(snapshot):
    """Full HTML output for the Suleiman — light theme (default)."""
    spec = build_suleiman().build_spec()
    html = render_ship_spec_html(spec)
    snap = AnnotatedSnapshot({'html': html})
    snap.annotate('dark_theme_supported', str('<body class="theme-dark">' in render_ship_spec_html(spec, theme='dark')))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)
