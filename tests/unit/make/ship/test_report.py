"""Unit tests for ship report rendering — smoke tests and formatting helpers."""

import pytest

from ceres.make.ship.report import _fmt_cr_col, _fmt_tons


class TestFormatHelpers:
    def test_fmt_tons_formats_with_two_decimal_places(self):
        assert _fmt_tons(9_000_000) == '9,000,000.00'

    def test_fmt_cr_col_formats_as_rounded_integer_with_commas(self):
        assert _fmt_cr_col(9_000_000_000) == '9,000,000,000'

    def test_fmt_tons_returns_empty_for_none(self):
        assert _fmt_tons(None) == ''

    def test_fmt_cr_col_returns_empty_for_none(self):
        assert _fmt_cr_col(None) == ''


@pytest.mark.slow
def test_render_ship_spec_pdf_returns_pdf_bytes():
    from ceres.make.ship.report import render_ship_spec_pdf
    from tests.approval.ship.e2e.test_suleiman import build_suleiman

    pdf = render_ship_spec_pdf(build_suleiman().build_spec())
    assert pdf[:4] == b'%PDF'


@pytest.mark.slow
def test_render_ship_pdf_returns_pdf_bytes():
    from ceres.make.ship.report import render_ship_pdf
    from tests.approval.ship.e2e.test_suleiman import build_suleiman

    pdf = render_ship_pdf(build_suleiman())
    assert pdf[:4] == b'%PDF'
