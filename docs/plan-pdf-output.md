# Plan: PDF output from Stuart

## Design principle

The HTML and PDF renderers are independent pipelines that share the same data
source (`ShipSpec`). They are not the same layout adapted for two media — they
are two different products with different goals:

- **HTML**: interactive, responsive, works on a phone screen. Compact display
  with pop-ups, progressive disclosure, responsive layout. Solve screen problems
  here.
- **PDF**: static, fixed paper size (A4 or Letter), designed for print and
  annotation. Fixed typography, room for added text and diagrams. Solve paper
  problems here.

These concerns should not be mixed. The PDF renderer reads `ShipSpec` directly
and builds its layout from scratch, the same way `ship_html.py` does — just
for a different target.

---

## Decisions

### 1. PDF library: Typst

**Decision**: use Typst (`typst-py` on PyPI) as the PDF engine.

Typst was evaluated through working proof-of-concept examples
(`examples/pdf_typst.py` and `examples/pdf_typst_dragon.py`). Typst produces
visibly better typography and its layout DSL is well-suited to tabular
document layout. Page-break control maps cleanly onto Typst primitives:

- **Section grouping** (break between sections, never within): 0pt guard column
  with `table.cell(rowspan: N, breakable: false)[]` per section group.
- **Sidebar cards** (keep each card whole, move to next page if needed):
  `block(breakable: false)[#table(...)]`.

ReportLab stays entirely in Python and handles pagination via `KeepTogether` +
`BaseDocTemplate` + `Frame` objects, but the API is verbose and has non-obvious
sharp edges (e.g. the outer-Table pagination trap). The output quality difference
is the deciding factor.

The main risk of Typst is that the Python side generates a Typst source string,
so escaping bugs and template errors surface as Typst compiler errors rather than
Python tracebacks. This is manageable as long as the Python data-building layer
is kept clean and the Typst template stays simple.

`typst-py` calls `typst.compile(path)` — it takes a file path, not a source
string. The implementation must write to a temporary file, compile, then delete
it.

### 2. Page format

Default to A4. Letter support can be added later as a parameter; the layout
geometry is the only thing that changes.

### 3. Dependency model

`typst` should be an optional extras group (`[pdf]`) so HTML-only users do not
pull in the Typst binary. The extras group is named `pdf`.

### 4. PDF layout

Two-column layout: main spec table on the left (~126mm), sidebar cards on the
right (~46mm), 8mm gutter. Sections flow continuously and never break
mid-section. Sidebar cards are kept whole. Banner (ship class, type, TL, hull
points) appears on page 1 only.

---

## Proposed API

```python
# ship_pdf.py (new module in the report package)
def render_ship_pdf(ship: Ship, *, page_size: str = 'a4') -> bytes: ...
def render_ship_spec_pdf(spec: ShipSpec, *, page_size: str = 'a4') -> bytes: ...
```

`page_size` is passed through to Typst's `#set page(paper: ...)` directive.
Typst uses lowercase names (`"a4"`, `"us-letter"`).

`ship_html.py` is not touched. The two renderers are siblings, not a hierarchy.

---

## HTML renderer: no changes needed for PDF

The HTML renderer should continue to evolve on its own terms — responsive
layout, phone-friendly display, interactive elements. None of that work should
be deferred or shaped by PDF requirements.
