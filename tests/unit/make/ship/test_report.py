"""Unit tests for ship report rendering — smoke tests and formatting helpers."""

from typing import Any, cast

import pytest

from ceres.make.ship.report import (
    _build_context,
    _fmt_cr_col,
    _fmt_tons,
    render_ship_html,
    render_ship_pdf,
    render_ship_spec_html,
    render_ship_spec_pdf,
    render_ship_spec_typst,
    render_ship_typst,
)
from ceres.make.ship.ship import Ship
from ceres.make.ship.spec import CrewRow, ExpenseRow, ShipSpec, SpecRow, SpecSection
from ceres.shared import NoteList


def _note_list() -> NoteList:
    return NoteList().item('item note').info('info note').warning('warning note')


def _spec() -> ShipSpec:
    spec = ShipSpec(
        ship_class='Beowulf',
        ship_type='Free Trader',
        tl=12,
        hull_points=40,
        ship_notes=NoteList().info('ship note'),
        crew_notes=NoteList().warning('crew note'),
        crew=[
            CrewRow(role='Pilot', salary=6000),
            CrewRow(role='Engineer', salary=5000, quantity=2),
        ],
        expenses=[
            ExpenseRow(label='Production Cost', amount=36_500_000),
            ExpenseRow(label='Sales Price New', amount=43_800_000),
            ExpenseRow(label='Monthly Maintenance', amount=3_642.2),
        ],
    )
    spec.add_row(
        SpecRow(
            section=SpecSection.HULL,
            item='Hull',
            quantity=2,
            tons=200,
            cost=9_000_000,
            emphasize_tons=True,
            notes=_note_list(),
        )
    )
    spec.add_row(
        SpecRow(
            section=SpecSection.POWER,
            item='Fusion Power Plant',
            power=120,
            cost=5_000_000,
            emphasize_power=True,
        )
    )
    spec.add_row(SpecRow(section=SpecSection.POWER, item='Basic Ship Systems', power=-40))
    spec.add_row(SpecRow(section=SpecSection.COMMAND, item='Bridge', tons=20, power=-10, cost=500_000))
    return spec


class TestFormatHelpers:
    def test_fmt_tons_formats_with_two_decimal_places(self):
        assert _fmt_tons(9_000_000) == '9,000,000.00'

    def test_fmt_cr_col_formats_as_rounded_integer_with_commas(self):
        assert _fmt_cr_col(9_000_000_000) == '9,000,000,000'

    def test_fmt_tons_returns_empty_for_none(self):
        assert _fmt_tons(None) == ''

    def test_fmt_cr_col_returns_empty_for_none(self):
        assert _fmt_cr_col(None) == ''

    def test_fmt_tons_returns_empty_for_display_epsilon(self):
        assert _fmt_tons(0.004) == ''

    def test_fmt_cr_col_returns_empty_for_display_epsilon(self):
        assert _fmt_cr_col(0.4) == ''


class TestBuildContext:
    def test_title_prefers_ship_class(self):
        context = _build_context(_spec())

        assert context['title'] == 'Beowulf'
        assert context['title_upper'] == 'BEOWULF'

    def test_title_falls_back_to_ship_type_then_unnamed(self):
        assert _build_context(ShipSpec(ship_type='Scout'))['title'] == 'Scout'
        assert _build_context(ShipSpec())['title'] == 'Unnamed'

    def test_meta_parts_include_type_tl_and_hull_points(self):
        assert _build_context(_spec())['meta_parts'] == ['Free Trader', 'TL12', 'Hull 40']

    def test_sections_group_rows_and_format_values(self):
        context = _build_context(_spec())

        hull = context['sections'][0]
        assert hull['label'] == 'Hull'
        assert hull['rows'][0] == {
            'item': 'Hull × 2',
            'tons': '200.00',
            'cost': '9,000,000',
            'emphasize_tons': True,
            'notes': [
                {'category': 'info', 'message': 'info note'},
                {'category': 'warning', 'message': 'warning note'},
            ],
        }

    def test_notes_exclude_item_note_for_display(self):
        context = _build_context(_spec())

        assert context['ship_notes'] == [{'category': 'info', 'message': 'ship note'}]
        assert context['crew_notes'] == [{'category': 'warning', 'message': 'crew note'}]

    def test_crew_formats_quantity_salary_and_total(self):
        context = _build_context(_spec())

        assert context['crew'] == [
            {'role': 'Pilot', 'salary': '6,000', 'total': '6,000'},
            {'role': 'Engineer × 2', 'salary': '5,000', 'total': '10,000'},
        ]

    def test_power_lists_producers_basic_systems_then_consumers(self):
        context = _build_context(_spec())

        assert context['power'] == [
            {'label': 'Power', 'value': '120.00', 'emphasize': True},
            {'label': 'Basic Ship Systems', 'value': '40.00', 'emphasize': False},
            {'label': 'Command', 'value': '10.00', 'emphasize': False},
        ]

    def test_power_omits_empty_rows(self):
        spec = ShipSpec()
        spec.add_row(SpecRow(section=SpecSection.HULL, item='Hull'))

        assert _build_context(spec)['power'] == []

    def test_expenses_format_mcr_for_ship_costs_and_cr_for_other_costs(self):
        context = _build_context(_spec())

        assert context['expenses'] == [
            {'label': 'Production Cost', 'amount': 'MCr 36.5'},
            {'label': 'Sales Price New', 'amount': 'MCr 43.8'},
            {'label': 'Monthly Maintenance', 'amount': 'Cr 3,642'},
        ]

    def test_theme_page_size_and_note_are_passed_through(self):
        context = _build_context(_spec(), theme='dark', page_size='letter', note='draft')

        assert context['theme'] == 'dark'
        assert context['page_size'] == 'letter'
        assert context['note'] == 'draft'


class _FakeShip:
    def __init__(self, spec: ShipSpec):
        self.spec = spec

    def build_spec(self) -> ShipSpec:
        return self.spec


class TestRenderWrappers:
    def test_render_ship_spec_html_calls_report_renderer(self, monkeypatch):
        calls: list[tuple[str, dict[str, Any]]] = []

        def fake_render_html(template, context):
            calls.append((template.name, context))
            return '<html>ship</html>'

        monkeypatch.setattr('ceres.report.render.render_html', fake_render_html)

        html = render_ship_spec_html(_spec(), theme='dark')

        assert html == '<html>ship</html>'
        assert calls[0][0] == 'ship_spec.html.j2'
        assert calls[0][1]['theme'] == 'dark'

    def test_render_ship_html_builds_spec_before_rendering(self, monkeypatch):
        monkeypatch.setattr('ceres.report.render.render_html', lambda template, context: context['title'])

        assert render_ship_html(cast(Ship, _FakeShip(_spec()))) == 'Beowulf'

    def test_render_ship_spec_typst_calls_report_renderer(self, monkeypatch):
        calls: list[tuple[str, dict[str, Any]]] = []

        def fake_render_typst_source(template, context):
            calls.append((template.name, context))
            return '#set page'

        monkeypatch.setattr('ceres.report.render.render_typst_source', fake_render_typst_source)

        source = render_ship_spec_typst(_spec(), page_size='letter', note='draft')

        assert source == '#set page'
        assert calls[0][0] == 'ship_spec.typ'
        assert calls[0][1]['page_size'] == 'letter'
        assert calls[0][1]['note'] == 'draft'

    def test_render_ship_typst_builds_spec_before_rendering(self, monkeypatch):
        monkeypatch.setattr('ceres.report.render.render_typst_source', lambda template, context: context['title'])

        assert render_ship_typst(cast(Ship, _FakeShip(_spec()))) == 'Beowulf'

    def test_render_ship_spec_pdf_calls_report_renderer(self, monkeypatch):
        calls: list[tuple[str, dict[str, Any]]] = []

        def fake_render_pdf(template, context):
            calls.append((template.name, context))
            return b'%PDF fake'

        monkeypatch.setattr('ceres.report.render.render_pdf', fake_render_pdf)

        pdf = render_ship_spec_pdf(_spec(), page_size='a5', note='proof')

        assert pdf == b'%PDF fake'
        assert calls[0][0] == 'ship_spec.typ'
        assert calls[0][1]['page_size'] == 'a5'
        assert calls[0][1]['note'] == 'proof'

    def test_render_ship_pdf_builds_spec_before_rendering(self, monkeypatch):
        monkeypatch.setattr('ceres.report.render.render_pdf', lambda template, context: context['title'].encode())

        assert render_ship_pdf(cast(Ship, _FakeShip(_spec()))) == b'Beowulf'


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
