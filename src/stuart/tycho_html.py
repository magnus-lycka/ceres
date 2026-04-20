from html import escape

from tycho.base import NoteCategory
from tycho.ship import Ship
from tycho.spec import CrewRow, ExpenseRow, ShipSpec, SpecRow

from .html import ExpanseHtmlPage, StuartTheme, render_expanse_html_page

__all__ = ['render_ship_html', 'render_ship_spec_html']


def render_ship_html(ship: Ship, *, theme: StuartTheme = 'light') -> str:
    return render_ship_spec_html(ship.build_spec(), theme=theme)


def render_ship_spec_html(spec: ShipSpec, *, theme: StuartTheme = 'light') -> str:
    title = spec.ship_class or spec.ship_type or 'Unnamed'
    if spec.ship_class is not None and spec.ship_type is not None:
        title = spec.ship_class

    body_html = (
        '<div class="ship-sheet">'
        '<div class="ship-grid">'
        f'{_render_main_table(spec)}'
        '<aside class="ship-sidebar">'
        f'{_render_crew_card(spec.crew, spec.crew_notes)}'
        f'{_render_power_card(spec.rows)}'
        f'{_render_costs_card(spec.expenses)}'
        '</aside>'
        '</div>'
        '</div>'
    )

    return render_expanse_html_page(
        ExpanseHtmlPage(
            title=title,
            body_html=body_html,
            extra_head_html=f'<style>{_TYCHO_SPEC_CSS}</style>',
            banner_side_html=_render_banner_side(spec),
            theme=theme,
        )
    )


def _render_banner_side(spec: ShipSpec) -> str | None:
    meta_items: list[str] = []
    if spec.ship_type is not None:
        meta_items.append(escape(spec.ship_type))
    if spec.tl is not None:
        meta_items.append(f'TL{spec.tl}')
    if spec.hull_points is not None:
        meta_items.append(f'Hull {spec.hull_points:.0f}')
    if not meta_items:
        return None
    return f'<p class="banner-meta">{" | ".join(meta_items)}</p>'


def _render_main_table(spec: ShipSpec) -> str:
    main_rows = [row for row in spec.rows if not (row.power is not None and row.tons is None and row.cost is None)]
    section_rowspans = _section_rowspans(main_rows)
    last_section_index = max(section_rowspans) if section_rowspans else -1
    rows_html = ''.join(
        _render_main_row(row, section_rowspans.get(index), index == last_section_index)
        for index, row in enumerate(main_rows)
    )
    return (
        '<section class="main-panel">'
        '<table class="spec-table">'
        '<thead><tr><th>Section</th><th>Item</th><th class="num">Tons</th><th class="num">Cost (MCr)</th></tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
        f'{_render_ship_notes(spec)}'
        '</section>'
    )


def _render_ship_notes(spec: ShipSpec) -> str:
    if not spec.ship_notes:
        return ''
    note_items = ''.join(_render_note_item(note.message, note.category) for note in spec.ship_notes)
    return f'<ul class="item-notes ship-notes">{note_items}</ul>'


def _section_rowspans(rows: list[SpecRow]) -> dict[int, int]:
    rowspans: dict[int, int] = {}
    index = 0
    while index < len(rows):
        section = rows[index].section
        span = 1
        while index + span < len(rows) and rows[index + span].section == section:
            span += 1
        rowspans[index] = span
        index += span
    return rowspans


def _render_main_row(row: SpecRow, section_rowspan: int | None, is_last_section: bool = False) -> str:
    item = _render_item_cell(row)
    tons = _format_number(row.tons)
    cost = _format_mcr(row.cost)
    if row.emphasize_tons and tons:
        tons = f'<strong>{tons}</strong>'

    section_cell = ''
    if section_rowspan is not None:
        cls = 'section-cell last-section-cell' if is_last_section else 'section-cell'
        section_cell = (
            f'<th scope="rowgroup" class="{cls}" rowspan="{section_rowspan}">{escape(row.section.value)}</th>'
        )

    return (
        f'<tr>{section_cell}'
        f'<td class="item-cell">{item}</td>'
        f'<td class="num">{tons}</td>'
        f'<td class="num">{cost}</td></tr>'
    )


def _render_item_cell(row: SpecRow) -> str:
    item = escape(row.item if row.quantity is None else f'{row.item} × {row.quantity}')
    if not row.notes:
        return item

    note_items = ''.join(_render_note_item(note.message, note.category) for note in row.notes)
    return f'{item}<ul class="item-notes">{note_items}</ul>'


def _render_note_item(message: str, category: NoteCategory) -> str:
    if category is NoteCategory.INFO:
        rendered = escape(message)
    elif category is NoteCategory.WARNING:
        rendered = f'<strong>Warning:</strong> {escape(message)}'
    elif category is NoteCategory.ERROR:
        rendered = f'<strong>Error:</strong> {escape(message)}'
    else:
        rendered = escape(message)
    return f'<li class="note-{category.value}">{rendered}</li>'


def _render_crew_card(crew: list[CrewRow], crew_notes) -> str:
    rows = ''.join(f'<li>{escape(c.role if c.quantity is None else f"{c.role} × {c.quantity}")}</li>' for c in crew)
    if not rows:
        rows = '<li>Uncrewed</li>'
    notes_html = ''
    if crew_notes:
        note_items = ''.join(_render_note_item(note.message, note.category) for note in crew_notes)
        notes_html = f'<ul class="item-notes ship-notes">{note_items}</ul>'
    return f'{_render_card("Crew", f'<ul class="simple-list">{rows}</ul>')}{notes_html}'


def _render_power_card(rows: list[SpecRow]) -> str:
    emphasized_rows = [row for row in rows if row.power is not None and row.emphasize_power]
    other_rows = [row for row in rows if row.power is not None and not row.emphasize_power]
    power_rows = [*emphasized_rows, *other_rows]
    rendered_rows = ''.join(
        '<tr>'
        f'<td>{escape(row.item if row.quantity is None else f"{row.item} × {row.quantity}")}</td>'
        f'<td class="num{" power-positive" if row.emphasize_power else ""}">{_format_number(abs(row.power))}</td>'
        '</tr>'
        for row in power_rows
    )
    return _render_card(
        'Power',
        '<table class="mini-table"><thead><tr><th>Item</th><th class="num">Power</th></tr></thead>'
        f'<tbody>{rendered_rows}</tbody></table>',
    )


def _render_costs_card(expenses: list[ExpenseRow]) -> str:
    rendered_rows = ''.join(
        f'<tr><td>{escape(exp.label)}</td><td class="num">{_format_expense(exp)}</td></tr>' for exp in expenses
    )
    return _render_card(
        'Costs',
        '<table class="mini-table"><thead><tr><th>Item</th><th class="num">Amount</th></tr></thead>'
        f'<tbody>{rendered_rows}</tbody></table>',
    )


def _render_card(title: str, content_html: str) -> str:
    return (
        '<section class="sidebar-card">'
        f'<header class="sidebar-card-title">{escape(title)}</header>'
        f'<div class="sidebar-card-body">{content_html}</div>'
        '</section>'
    )


def _format_number(value: float | None) -> str:
    if value is None or abs(value) < 0.005:
        return ''
    return f'{value:.2f}'


def _format_mcr(value: float | None) -> str:
    if value is None or abs(value) < 0.5:
        return ''
    return f'{value / 1_000_000:.3f}'.rstrip('0').rstrip('.')


def _format_expense(expense: ExpenseRow) -> str:
    if expense.label in {'Production Cost', 'Sales Price New'}:
        return f'MCr {expense.amount / 1_000_000:.3f}'.rstrip('0').rstrip('.')
    return f'Cr {round(expense.amount):,}'


_TYCHO_SPEC_CSS = """
.ship-sheet {
  display: grid;
  gap: 18px;
}

.banner-meta {
  margin: 0;
  padding: 8px 14px;
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--ink);
  font-size: 1.1rem;
  font-weight: 700;
  white-space: nowrap;
  text-align: right;
}

.ship-grid {
  display: grid;
  grid-template-columns: minmax(0, 2.6fr) minmax(260px, 1fr);
  gap: 22px;
  align-items: start;
}

.main-panel {
  min-width: 0;
  padding: 10px;
  background: var(--surface);
  border: 1px solid var(--accent);
}

.spec-table,
.mini-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--accent);
}

.spec-table th,
.spec-table td,
.mini-table th,
.mini-table td {
  padding: 8px 10px;
  border: 1px solid var(--line);
  vertical-align: top;
}

.spec-table thead th,
.mini-table thead th {
  background: var(--surface);
  color: var(--ink);
  font-size: 1.1rem;
  letter-spacing: 0.03em;
}

.main-panel .spec-table {
  border: 0;
  background: transparent;
}

.main-panel .spec-table th,
.main-panel .spec-table td {
  border-left: 0;
  border-right: 0;
}

.main-panel .spec-table thead th {
  border-top: 0;
}

.main-panel .spec-table tbody tr:last-child td {
  border-bottom: 0;
}

.main-panel .spec-table .last-section-cell {
  border-bottom: 0;
}

.spec-table thead th:first-child,
.spec-table .section-cell {
  width: 19%;
}

.spec-table thead th:nth-child(2) {
  width: 53%;
}

.spec-table .num,
.mini-table .num {
  text-align: right;
  white-space: nowrap;
}

.power-positive {
  font-weight: 700;
}

.section-cell {
  text-align: left;
  font-weight: 700;
}

.item-cell {
  line-height: 1.2;
}

.item-notes {
  margin: 8px 0 0 18px;
  padding: 0;
  display: grid;
  gap: 4px;
  font-size: 0.94rem;
  color: var(--ink);
}

.item-notes .note-info {
  color: var(--ink);
}

.item-notes .note-warning {
  color: var(--warning);
  font-style: italic;
}

.item-notes .note-error {
  color: var(--error);
  font-weight: 700;
}

.ship-sidebar {
  display: grid;
  gap: 18px;
}

.sidebar-card {
  border: 1px solid var(--accent);
  background: var(--surface);
}

.sidebar-card-title {
  padding: 9px 14px 8px;
  background: transparent;
  color: var(--accent);
  border-bottom: 1px solid var(--accent);
  font-size: 1.35rem;
  line-height: 1;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  text-align: center;
  font-weight: 800;
}

.sidebar-card-body {
  padding: 10px;
}

.sidebar-card .mini-table {
  border: 0;
  background: transparent;
}

.sidebar-card .mini-table th,
.sidebar-card .mini-table td {
  border-left: 0;
  border-right: 0;
}

.sidebar-card .mini-table thead th {
  border-top: 0;
}

.sidebar-card .mini-table tbody tr:last-child td {
  border-bottom: 0;
}

.simple-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
  text-align: center;
  font-size: 1.2rem;
  color: var(--ink);
}

@media (max-width: 960px) {
  .ship-grid {
    grid-template-columns: 1fr;
  }
}
"""
