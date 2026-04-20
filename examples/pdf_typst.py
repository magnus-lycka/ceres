"""Typst proof-of-concept: Ultralight Fighter on A5 (half A4).

Run with:
    uv run --with typst python examples/pdf_typst.py

Output: tests/ships/generated_output/pdf/ultralight_typst.pdf
"""

import sys
from itertools import groupby
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root / 'src'))
sys.path.insert(0, str(_root))

import typst

from tests.ships.test_ultralight_fighter import build_ultralight_fighter

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

spec = build_ultralight_fighter().build_spec()

main_rows = [
    r for r in spec.rows
    if not (r.power is not None and r.tons is None and r.cost is None)
]


def esc(text: str) -> str:
    """Escape Typst special characters."""
    return text.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]').replace('#', '\\#')


def fmt_tons(v: float | None) -> str:
    if v is None or abs(v) < 0.005:
        return ''
    return f'{v:.2f}'


def fmt_mcr(v: float | None) -> str:
    if v is None or abs(v) < 0.5:
        return ''
    return f'{v / 1_000_000:.3f}'.rstrip('0').rstrip('.')


def fmt_expense(label: str, amount: float) -> str:
    if label in {'Production Cost', 'Sales Price New'}:
        return f'MCr {amount / 1_000_000:.3f}'.rstrip('0').rstrip('.')
    return f'Cr {round(amount):,}'


# ---------------------------------------------------------------------------
# Build Typst source
# ---------------------------------------------------------------------------

def spec_table_rows() -> str:
    lines = []
    for section, rows in groupby(main_rows, key=lambda r: r.section):
        rows = list(rows)
        for i, row in enumerate(rows):
            sec  = esc(section.value) if i == 0 else ''
            item = esc(row.item if row.quantity is None else f'{row.item} \u00d7 {row.quantity}')
            tons = fmt_tons(row.tons)
            mcr  = fmt_mcr(row.cost)
            bold_tons = f'*{tons}*' if row.emphasize_tons and tons else tons
            # rowspan for section cell: Typst table supports rowspan
            if i == 0 and len(rows) > 1:
                sec_cell = f'table.cell(rowspan: {len(rows)})[*{sec}*]'
            elif i == 0:
                sec_cell = f'[*{sec}*]'
            else:
                sec_cell = None  # omit — consumed by rowspan

            row_cells = []
            if sec_cell is not None:
                row_cells.append(sec_cell)
            row_cells.append(f'[{item}]')
            row_cells.append(f'table.cell(align: right)[{bold_tons}]')
            row_cells.append(f'table.cell(align: right)[{mcr}]')
            lines.append('    ' + ', '.join(row_cells) + ',')
    return '\n'.join(lines)


def crew_rows() -> str:
    if not spec.crew:
        return '    [Uncrewed],'
    lines = []
    for c in spec.crew:
        label = esc(c.role if c.quantity is None else f'{c.role} \u00d7 {c.quantity}')
        lines.append(f'    table.cell(align: center)[{label}],')
    return '\n'.join(lines)


def power_rows() -> str:
    power = [r for r in spec.rows if r.power is not None]
    producers = [r for r in power if r.emphasize_power]
    consumers = [r for r in power if not r.emphasize_power]
    lines = []
    for r in producers + consumers:
        label = esc(r.item if r.quantity is None else f'{r.item} \u00d7 {r.quantity}')
        val   = f'{abs(r.power):.2f}'
        bold  = '*' if r.emphasize_power else ''
        lines.append(f'    [{bold}{label}{bold}], table.cell(align: right)[{bold}{val}{bold}],')
    return '\n'.join(lines)


def costs_rows() -> str:
    lines = []
    for e in spec.expenses:
        label = esc(e.label)
        val   = esc(fmt_expense(e.label, e.amount))
        lines.append(f'    [{label}], table.cell(align: right)[{val}],')
    return '\n'.join(lines)


title      = esc(spec.ship_class or spec.ship_type or 'Unnamed').upper()
meta_parts = []
if spec.ship_type:
    meta_parts.append(esc(spec.ship_type))
if spec.tl is not None:
    meta_parts.append(f'TL{spec.tl}')
if spec.hull_points is not None:
    meta_parts.append(f'Hull {spec.hull_points:.0f}')
meta = '  |  '.join(meta_parts)

source = f"""
#set page(paper: "a4", margin: (x: 15mm, top: 12mm, bottom: 12mm))
#set text(font: ("Arial Narrow", "Helvetica Neue Condensed", "Helvetica"), size: 7.5pt)
#set table(stroke: (x, y) => if y == 0 {{ 0.6pt + rgb("#cc2036") }} else {{ 0.3pt + rgb("#b0a090") }})

#let accent = rgb("#cc2036")
#let ink    = rgb("#0d0d0d")

// Banner
#text(size: 14pt, weight: "bold", fill: accent)[{title}]
#v(1mm)
#text(size: 7.5pt, fill: ink)[{meta}]
#v(3mm)

// Two-column layout
#grid(
  columns: (126mm, 1fr),
  gutter: 8mm,

  // ── Left: main spec table ──────────────────────────────────────────────
  table(
    columns: (16mm, 1fr, 14mm, 14mm),
    fill: (_, y) => if y == 0 {{ rgb("#fffdf5") }} else {{ none }},
    table.header(
      [*Section*], [*Item*], table.cell(align: right)[*Tons*], table.cell(align: right)[*MCr*],
    ),
{spec_table_rows()}
  ),

  // ── Right: sidebar cards ───────────────────────────────────────────────
  stack(
    spacing: 4mm,

    // Crew
    table(
      columns: (1fr,),
      table.header(table.cell(align: center)[#text(fill: accent, weight: "bold")[CREW]]),
{crew_rows()}
    ),

    // Power
    table(
      columns: (1fr, auto),
      table.header(
        table.cell(colspan: 2, align: center)[#text(fill: accent, weight: "bold")[POWER]],
      ),
{power_rows()}
    ),

    // Costs
    table(
      columns: (1fr, auto),
      table.header(
        table.cell(colspan: 2, align: center)[#text(fill: accent, weight: "bold")[COSTS]],
      ),
{costs_rows()}
    ),
  ),
)
"""

# ---------------------------------------------------------------------------
# Compile and write
# ---------------------------------------------------------------------------

import tempfile, os

out_dir = _root / 'tests' / 'ships' / 'generated_output' / 'pdf'
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / 'ultralight_typst.pdf'

with tempfile.NamedTemporaryFile(suffix='.typ', mode='w', delete=False) as f:
    f.write(source)
    tmp_path = f.name

try:
    pdf_bytes = typst.compile(tmp_path)
finally:
    os.unlink(tmp_path)

out_path.write_bytes(pdf_bytes)
print(f'Written: {out_path}')
