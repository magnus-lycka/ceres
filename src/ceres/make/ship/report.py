"""Ship report rendering — domain logic for building context and calling the engine."""

from itertools import groupby
from pathlib import Path
from typing import Literal

from ceres.make.ship.base import NoteList, _Note
from ceres.make.ship.ship import Ship
from ceres.make.ship.spec import CrewRow, ExpenseRow, ShipSpec, SpecRow
from ceres.make.ship.text import format_counted_label
from ceres.make.ship.view import collapsed_main_rows

ReportTheme = Literal['light', 'dark']

__all__ = [
    'render_ship_html',
    'render_ship_pdf',
    'render_ship_spec_html',
    'render_ship_spec_pdf',
    'render_ship_spec_typst',
    'render_ship_typst',
]

_TEMPLATES = Path(__file__).parent / 'templates'


def render_ship_html(ship: Ship, *, theme: ReportTheme = 'light') -> str:
    return render_ship_spec_html(ship.build_spec(), theme=theme)


def render_ship_spec_html(spec: ShipSpec, *, theme: ReportTheme = 'light') -> str:
    from ceres.report.render import render_html

    return render_html(_TEMPLATES / 'ship_spec.html.j2', _build_context(spec, theme=theme))


def render_ship_typst(ship: Ship, *, page_size: str = 'a4') -> str:
    return render_ship_spec_typst(ship.build_spec(), page_size=page_size)


def render_ship_spec_typst(spec: ShipSpec, *, page_size: str = 'a4') -> str:
    from ceres.report.render import render_typst_source

    return render_typst_source(_TEMPLATES / 'ship_spec.typ', _build_context(spec, page_size=page_size))


def render_ship_pdf(ship: Ship, *, page_size: str = 'a4') -> bytes:
    return render_ship_spec_pdf(ship.build_spec(), page_size=page_size)


def render_ship_spec_pdf(spec: ShipSpec, *, page_size: str = 'a4') -> bytes:
    from ceres.report.render import render_pdf

    return render_pdf(_TEMPLATES / 'ship_spec.typ', _build_context(spec, page_size=page_size))


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------


def _build_context(spec: ShipSpec, *, theme: ReportTheme = 'light', page_size: str = 'a4') -> dict:
    meta_parts: list[str] = []
    if spec.ship_type:
        meta_parts.append(spec.ship_type)
    if spec.tl is not None:
        meta_parts.append(f'TL{spec.tl}')
    if spec.hull_points is not None:
        meta_parts.append(f'Hull {spec.hull_points:.0f}')

    title = spec.ship_class or spec.ship_type or 'Unnamed'
    return {
        'title': title,
        'title_upper': title.upper(),
        'meta_parts': meta_parts,
        'sections': _build_sections(collapsed_main_rows(spec)),
        'ship_notes': _notes_for_display(spec.ship_notes),
        'crew': _build_crew(spec.crew),
        'crew_notes': _notes_for_display(spec.crew_notes),
        'power': _build_power(spec.rows),
        'expenses': _build_expenses(spec.expenses),
        'theme': theme,
        'page_size': page_size,
    }


def _build_sections(rows: list[SpecRow]) -> list[dict]:
    result = []
    for section, section_rows in groupby(rows, key=lambda r: r.section):
        section_rows = list(section_rows)
        result.append(
            {
                'label': section.value,
                'rows': [
                    {
                        'item': format_counted_label(row.item, row.quantity),
                        'tons': _fmt_tons(row.tons),
                        'cost': _fmt_cr_col(row.cost),
                        'emphasize_tons': row.emphasize_tons,
                        'notes': _notes_for_display(row.notes),
                    }
                    for row in section_rows
                ],
            }
        )
    return result


def _build_power(rows: list[SpecRow]) -> list[dict]:
    sums: dict[str, float] = {}
    produces: set[str] = set()
    basic: float | None = None
    for r in rows:
        if r.power is None:
            continue
        if r.item == 'Basic Ship Systems':
            basic = r.power
            continue
        key = r.section.value
        sums[key] = sums.get(key, 0.0) + r.power
        if r.emphasize_power:
            produces.add(key)
    result = []
    for section, total in sums.items():
        if section in produces:
            result.append({'label': section, 'value': f'{abs(total):.2f}', 'emphasize': True})
    if basic is not None:
        result.append({'label': 'Basic Ship Systems', 'value': f'{abs(basic):.2f}', 'emphasize': False})
    for section, total in sums.items():
        if section not in produces:
            result.append({'label': section, 'value': f'{abs(total):.2f}', 'emphasize': False})
    return result


def _build_crew(crew: list[CrewRow]) -> list[dict]:
    result = []
    for c in crew:
        qty = c.quantity if c.quantity is not None else 1
        result.append(
            {
                'role': format_counted_label(c.role, c.quantity),
                'salary': f'{c.salary:,}',
                'total': f'{c.salary * qty:,}',
            }
        )
    return result


def _build_expenses(expenses: list[ExpenseRow]) -> list[dict]:
    result = []
    for e in expenses:
        if e.label in {'Production Cost', 'Sales Price New'}:
            amount = f'MCr {e.amount / 1_000_000:.3f}'.rstrip('0').rstrip('.')
        else:
            amount = f'Cr {round(e.amount):,}'
        result.append({'label': e.label, 'amount': amount})
    return result


def _notes_for_display(notes: list[_Note]) -> list[dict]:
    return NoteList(notes).detail_entries


def _fmt_tons(v: float | None) -> str:
    if v is None or abs(v) < 0.005:
        return ''
    return f'{v:,.2f}'


def _fmt_cr_col(v: float | None) -> str:
    if v is None or abs(v) < 0.5:
        return ''
    return f'{round(v):,}'
