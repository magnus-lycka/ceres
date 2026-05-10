# Decision record: report rendering architecture

> This file records the key decisions made when building the report engine.
> The current design is described in full in [ARCHITECTURE.md](ARCHITECTURE.md)
> under "Reporting and rendering".

## What was built

`ceres.report` is a template execution engine. It has no domain knowledge —
domain packages own their templates and context builders and call the engine.
The engine provides `render_html`, `render_typst_source`, and `render_pdf`.

The scope grew from "add ship PDF output" to a general-purpose rendering
toolkit covering ship HTML, ship PDF, and the gear catalog.

## PDF library: Typst

**Decision**: use Typst (`typst-py` on PyPI) as the PDF engine.

Typst was evaluated through working proof-of-concept examples. It produces
visibly better typography than ReportLab and its layout DSL maps cleanly onto
tabular document layout. Key primitives used:

- `table.cell(rowspan: N, breakable: false)[]` — 0pt guard column keeps
  sections together across page breaks.
- `block(breakable: false)[...]` — keeps sidebar cards whole.

ReportLab handles pagination via `KeepTogether` + `BaseDocTemplate` + `Frame`
objects, but the API is verbose and has non-obvious sharp edges. The output
quality difference was the deciding factor.

The main risk of Typst is that the Python side generates a Typst source string,
so escaping bugs and template errors surface as Typst compiler errors rather
than Python tracebacks. This is managed by keeping the Python data-building
layer clean and the Typst template straightforward.

## HTML and PDF are independent pipelines

HTML and PDF are not the same layout adapted for two media. They are two
different products:

- **HTML**: interactive, responsive, works on a phone screen. Progressive
  disclosure, responsive layout.
- **PDF**: static, fixed paper size (A4 or Letter), designed for print.
  Fixed typography.

Both consume the same `ShipSpec` context dict but render it independently.
