// ship_spec.typ — Ship specification sheet.
// Data injected by Python as: #let report_data = (...)

#import "@preview/gentle-clues:1.2.0": info as gc-info, warning as gc-warning, error as gc-error

#let accent = rgb("#cc2036")
#let ink = rgb("#0d0d0d")
#let table-border = 0.6pt + ink
#let table-rule = 0.3pt + rgb("#b0a090")

#set page(paper: report_data.page_size, margin: (x: 15mm, top: 12mm, bottom: 12mm))
#set text(font: ("Arial Narrow", "Helvetica Neue Condensed", "Helvetica"), size: 10pt)
#set table(stroke: table-rule)

// One admonition per category, sorted error → warning → info.
#let render-grouped(notes, headless: false) = {
  for cat in ("error", "warning", "info") {
    let msgs = notes.filter(n => n.at("category") == cat).map(n => n.at("message"))
    if msgs.len() > 0 {
      let body = msgs.map(m => [#m]).join(linebreak())
      if cat == "error"   { gc-error(headless: headless)[#body] }
      else if cat == "warning" { gc-warning(headless: headless)[#body] }
      else { gc-info(headless: headless)[#body] }
    }
  }
}

// Render notes inline (after item text), inside table cells.
#let render-ship-notes(notes) = {
  if notes.len() > 0 { linebreak() }
  render-grouped(notes, headless: true)
}

// Render a standalone notes block.
#let render-notes-block(notes) = render-grouped(notes)

// ── Header ────────────────────────────────────────────────────────────────
#let meta-parts = report_data.meta_parts

#grid(
  columns: (1fr, auto),
  align: (left + horizon, right + horizon),
  text(size: 14pt, weight: "bold", fill: accent)[#report_data.title_upper],
  if meta-parts.len() > 0 {
    table(
      stroke: (x, _y) => if x > 0 { 0.4pt + ink } else { none },
      columns: range(meta-parts.len()).map(_ => auto),
      inset: (x: 8pt, y: 4pt),
      ..meta-parts.map(p => text(size: 12pt, weight: "bold")[#p])
    )
  } else { [] },
)
#v(3mm)

// ── Main spec table ───────────────────────────────────────────────────────
#block(stroke: table-border, inset: 0pt)[
  #table(
    columns: (0pt, 24mm, 1fr, 28mm, 32mm),
    fill: none,
    stroke: (_x, _y) => (right: table-rule, bottom: table-rule),
    table.header(
      [], [*Section*], [*Item*],
      table.cell(align: right)[*Tons*],
      table.cell(align: right)[*Price (Cr)*],
    ),
    ..report_data.sections.map(section => {
      let n = section.rows.len()
      section.rows.enumerate().map(((i, row)) => {
        let guard = if i == 0 {
          (table.cell(rowspan: n, breakable: false)[],)
        } else {
          ()
        }
        let sec-cell = if i == 0 {
          if n > 1 {
            (table.cell(rowspan: n)[*#section.label*],)
          } else {
            ([*#section.label*],)
          }
        } else {
          ()
        }
        let tons = if row.emphasize_tons and row.tons != "" {
          [*#row.tons*]
        } else {
          [#row.tons]
        }
        let notes = row.at("notes", default: ())
        let item-content = if notes.len() > 0 {
          [#row.item#render-ship-notes(notes)]
        } else {
          [#row.item]
        }
        guard + sec-cell + (
          item-content,
          table.cell(align: right)[#tons],
          table.cell(align: right)[#row.cost],
        )
      }).flatten()
    }).flatten()
  )
]

#if report_data.ship_notes.len() > 0 {
  v(3mm)
  render-notes-block(report_data.ship_notes)
}

#v(4mm)

// ── Crew and Power side by side ───────────────────────────────────────────
#grid(
  columns: (1fr, 1fr),
  gutter: 8mm,

  [
    #block(breakable: false, stroke: table-border, inset: 0pt)[
      #table(
        columns: (1fr, auto, auto),
        stroke: (_x, _y) => (bottom: table-rule),
        table.header(
          table.cell(colspan: 3, align: center)[#text(fill: ink, weight: "bold")[CREW]],
          [*Role*],
          table.cell(align: right)[*Salary*],
          table.cell(align: right)[*Total*],
        ),
        ..if report_data.crew.len() == 0 {
          (table.cell(colspan: 3)[Uncrewed],)
        } else {
          report_data.crew.map(c => (
            [#c.role],
            table.cell(align: right)[#c.salary],
            table.cell(align: right)[#c.total],
          )).flatten()
        }
      )
    ]
    #if report_data.crew_notes.len() > 0 {
      v(2mm)
      render-notes-block(report_data.crew_notes)
    }
  ],

  block(breakable: false, stroke: table-border, inset: 0pt)[
    #table(
      columns: (1fr, auto),
      stroke: (_x, _y) => (bottom: table-rule),
      table.header(
        table.cell(colspan: 2, align: center)[#text(fill: ink, weight: "bold")[POWER]],
      ),
      ..report_data.power.map(p => (
        if p.emphasize { ([*#p.label*],) } else { ([#p.label],) },
        table.cell(align: right)[#if p.emphasize { [*#p.value*] } else { [#p.value] }],
      )).flatten()
    )
  ],
)

#v(4mm)

// ── Costs ─────────────────────────────────────────────────────────────────
#block(breakable: false, stroke: table-border, inset: 0pt)[
  #table(
    columns: (1fr, auto),
    stroke: (_x, _y) => (bottom: table-rule),
    table.header(
      table.cell(colspan: 2, align: center)[#text(fill: ink, weight: "bold")[COSTS (Cr)]],
    ),
    ..report_data.expenses.map(e => (
      [#e.label],
      table.cell(align: right)[#e.amount],
    )).flatten()
  )
]
