from itertools import groupby
import os
import tempfile

from ceres.make.ship.base import Note, NoteCategory
from ceres.make.ship.ship import Ship
from ceres.make.ship.spec import ShipSpec, SpecRow
from ceres.make.ship.text import format_counted_label

from .ship_view import collapsed_main_rows

__all__ = ['render_ship_pdf', 'render_ship_spec_pdf', 'render_ship_spec_typst', 'render_ship_typst']


def render_ship_pdf(ship: Ship, *, page_size: str = 'a4') -> bytes:
    return render_ship_spec_pdf(ship.build_spec(), page_size=page_size)


def render_ship_typst(ship: Ship, *, page_size: str = 'a4') -> str:
    return render_ship_spec_typst(ship.build_spec(), page_size=page_size)


def render_ship_spec_typst(spec: ShipSpec, *, page_size: str = 'a4') -> str:
    return _build_typst_source(spec, page_size=page_size)


def render_ship_spec_pdf(spec: ShipSpec, *, page_size: str = 'a4') -> bytes:
    import typst

    source = _build_typst_source(spec, page_size=page_size)
    with tempfile.NamedTemporaryFile(suffix='.typ', mode='w', delete=False, encoding='utf-8') as f:
        f.write(source)
        tmp_path = f.name
    try:
        return typst.compile(tmp_path)
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _esc(text: str) -> str:
    return (
        text.replace('\\', '\\\\')
        .replace('[', '\\[')
        .replace(']', '\\]')
        .replace('#', '\\#')
        .replace('*', '\\*')
        .replace('_', '\\_')
    )


def _fmt_tons(v: float | None) -> str:
    if v is None or abs(v) < 0.005:
        return ''
    return f'{v:,.2f}'


def _render_notes(notes: list[Note]) -> str:
    parts = []
    for note in notes:
        if note.category is NoteCategory.ITEM:
            continue
        msg = _esc(note.message)
        if note.category is NoteCategory.WARNING:
            parts.append(f'#text(fill: rgb("#e07800"), style: "italic")[Warning: {msg}]')
        elif note.category is NoteCategory.ERROR:
            parts.append(f'#text(fill: rgb("#cc2036"), weight: "bold")[Error: {msg}]')
        else:
            parts.append(f'#text(style: "italic")[{msg}]')
    if not parts:
        return ''
    return '#linebreak()' + '#linebreak()'.join(parts)


def _fmt_cr_col(v: float | None) -> str:
    if v is None or abs(v) < 0.5:
        return ''
    return f'{round(v):,}'


def _fmt_expense(label: str, amount: float) -> str:
    if label in {'Production Cost', 'Sales Price New'}:
        return f'MCr {amount / 1_000_000:.3f}'.rstrip('0').rstrip('.')
    return f'Cr {round(amount):,}'


# ---------------------------------------------------------------------------
# Table content generators
# ---------------------------------------------------------------------------


def _main_rows(spec: ShipSpec) -> list[SpecRow]:
    return collapsed_main_rows(spec)


def _spec_table_rows(spec: ShipSpec) -> str:
    lines = []
    for section, rows in groupby(_main_rows(spec), key=lambda r: r.section):
        rows = list(rows)
        n = len(rows)
        guard = f'table.cell(rowspan: {n}, breakable: false)[]' if n > 1 else 'table.cell(breakable: false)[]'
        for i, row in enumerate(rows):
            sec = _esc(section.value) if i == 0 else ''
            item = _esc(format_counted_label(row.item, row.quantity))
            tons = _fmt_tons(row.tons)
            mcr = _fmt_cr_col(row.cost)
            bold_tons = f'*{tons}*' if row.emphasize_tons and tons else tons
            if i == 0 and n > 1:
                sec_cell = f'table.cell(rowspan: {n})[*{sec}*]'
            elif i == 0:
                sec_cell = f'[*{sec}*]'
            else:
                sec_cell = None

            row_cells = []
            if i == 0:
                row_cells.append(guard)
            if sec_cell is not None:
                row_cells.append(sec_cell)
            row_cells.append(f'[{item}{_render_notes(row.notes)}]')
            row_cells.append(f'table.cell(align: right)[{bold_tons}]')
            row_cells.append(f'table.cell(align: right)[{mcr}]')
            lines.append('    ' + ', '.join(row_cells) + ',')
    return '\n'.join(lines)


def _crew_rows(spec: ShipSpec) -> str:
    if not spec.crew:
        return '    table.cell(colspan: 3)[Uncrewed],'
    lines = []
    for c in spec.crew:
        role = _esc(format_counted_label(c.role, c.quantity))
        qty = c.quantity if c.quantity is not None else 1
        total = c.salary * qty
        lines.append(f'    [{role}], table.cell(align: right)[{c.salary:,}], table.cell(align: right)[{total:,}],')
    return '\n'.join(lines)


def _crew_notes_block(spec: ShipSpec) -> str:
    if not spec.crew_notes:
        return ''
    return '#v(2mm)\n' + _render_notes(spec.crew_notes).removeprefix('#linebreak()')


def _crew_panel(spec: ShipSpec) -> str:
    return f"""
[
  #block(breakable: false, stroke: table-border, inset: 0pt)[
    #table(
      columns: (1fr, auto, auto),
      stroke: (_x, _y) => (bottom: table-rule),
      table.header(
        table.cell(colspan: 3, align: center)[#text(fill: ink, weight: "bold")[CREW]],
        [*Role*], table.cell(align: right)[*Salary*], table.cell(align: right)[*Total*],
      ),
{_crew_rows(spec)}
    )
  ]
{_crew_notes_block(spec)}
]
""".strip()


def _power_rows(spec: ShipSpec) -> str:
    sums: dict[str, float] = {}
    produces: set[str] = set()
    basic: float | None = None
    for r in spec.rows:
        if r.power is None:
            continue
        if r.item == 'Basic Ship Systems':
            basic = r.power
            continue
        key = _esc(r.section.value)
        sums[key] = sums.get(key, 0.0) + r.power
        if r.emphasize_power:
            produces.add(key)
    lines = []
    for section, total in sums.items():
        if section in produces:
            val = f'{abs(total):.2f}'
            lines.append(f'    [*{section}*], table.cell(align: right)[*{val}*],')
    if basic is not None:
        lines.append(f'    [Basic Ship Systems], table.cell(align: right)[{abs(basic):.2f}],')
    for section, total in sums.items():
        if section not in produces:
            val = f'{abs(total):.2f}'
            lines.append(f'    [{section}], table.cell(align: right)[{val}],')
    return '\n'.join(lines)


def _fmt_cr(amount: float) -> str:
    return f'{round(amount):,}'


def _costs_rows(spec: ShipSpec) -> str:
    return '\n'.join(
        f'    [{_esc(e.label)}], table.cell(align: right)[{_esc(_fmt_cr(e.amount))}],' for e in spec.expenses
    )


def _ship_notes_block(spec: ShipSpec) -> str:
    if not spec.ship_notes:
        return ''
    return '#v(3mm)\n' + _render_notes(spec.ship_notes).removeprefix('#linebreak()')


# ---------------------------------------------------------------------------
# Typst source builder
# ---------------------------------------------------------------------------


def _build_typst_source(spec: ShipSpec, *, page_size: str) -> str:
    title = _esc((spec.ship_class or spec.ship_type or 'Unnamed').upper())

    meta_parts = []
    if spec.ship_type:
        meta_parts.append(_esc(spec.ship_type))
    if spec.tl is not None:
        meta_parts.append(f'TL{spec.tl}')
    if spec.hull_points is not None:
        meta_parts.append(f'Hull {spec.hull_points:.0f}')

    if meta_parts:
        cols = ', '.join(['auto'] * len(meta_parts))
        cells = ', '.join(f'text(size: 12pt, weight: "bold")[{p}]' for p in meta_parts)
        meta_widget = (
            f'table(stroke: (x, y) => if x > 0 {{ 0.4pt + ink }} else {{ none }},'
            f' columns: ({cols},), inset: (x: 8pt, y: 4pt), {cells})'
        )
    else:
        meta_widget = '[]'

    return f"""
#set page(paper: "{page_size}", margin: (x: 15mm, top: 12mm, bottom: 12mm))
#set text(font: ("Arial Narrow", "Helvetica Neue Condensed", "Helvetica"), size: 10pt)

#let accent = rgb("#cc2036")
#let ink = rgb("#0d0d0d")
#let table-border = 0.6pt + ink
#let table-rule = 0.3pt + rgb("#b0a090")

#set table(stroke: table-rule)

#grid(
  columns: (1fr, auto),
  align: (left + horizon, right + horizon),
  text(size: 14pt, weight: "bold", fill: accent)[{title}],
  {meta_widget},
)
#v(3mm)

// ── Main spec table (full width) ──────────────────────────────────────────
// 0pt guard column keeps each section together across page breaks
#block(stroke: table-border, inset: 0pt)[
  #table(
    columns: (0pt, 24mm, 1fr, 28mm, 32mm),
    fill: none,
    stroke: (_x, _y) => (right: table-rule, bottom: table-rule),
    table.header(
      [], [*Section*], [*Item*], table.cell(align: right)[*Tons*], table.cell(align: right)[*Price (Cr)*],
    ),
{_spec_table_rows(spec)}
  )
]
{_ship_notes_block(spec)}

#v(4mm)

// ── Crew and Power side by side ───────────────────────────────────────────
#grid(
  columns: (1fr, 1fr),
  gutter: 8mm,

  {_crew_panel(spec)},

  block(breakable: false, stroke: table-border, inset: 0pt)[
    #table(
      columns: (1fr, auto),
      stroke: (_x, _y) => (bottom: table-rule),
      table.header(
        table.cell(colspan: 2, align: center)[#text(fill: ink, weight: "bold")[POWER]],
      ),
{_power_rows(spec)}
    )
  ],
)

#v(4mm)

// ── Costs (full width) ────────────────────────────────────────────────────
#block(breakable: false, stroke: table-border, inset: 0pt)[
  #table(
    columns: (1fr, auto),
    stroke: (_x, _y) => (bottom: table-rule),
    table.header(
      table.cell(colspan: 2, align: center)[#text(fill: ink, weight: "bold")[COSTS (Cr)]],
    ),
{_costs_rows(spec)}
  )
]
"""
