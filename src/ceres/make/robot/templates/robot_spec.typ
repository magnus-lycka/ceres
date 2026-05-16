// robot_spec.typ — Robot specification sheet.
// Data injected by Python as: #let report_data = (...)

#import "@preview/gentle-clues:1.2.0": abstract as gc-abstract, info as gc-info, warning as gc-warning, error as gc-error

#let accent = rgb("#cc2036")
#let ink = rgb("#0d0d0d")
#let table-rule = 0.3pt + rgb("#b0a090")
#let label-bg = luma(242)

#set page(paper: report_data.page_size, margin: (x: 15mm, top: 12mm, bottom: 12mm))
#set text(font: ("Arial Narrow", "Helvetica Neue Condensed", "Helvetica"), size: 10pt)
#set table(stroke: table-rule)

#let render-grouped(notes, headless: false) = {
  for cat in ("error", "warning", "content", "info") {
    let msgs = notes.filter(n => n.at("category") == cat).map(n => n.at("message"))
    if msgs.len() > 0 {
      let body = msgs.map(m => [#m]).join(linebreak())
      if cat == "error"   { gc-error(headless: headless)[#body] }
      else if cat == "warning" { gc-warning(headless: headless)[#body] }
      else if cat == "content" { gc-abstract(headless: headless)[#body] }
      else { gc-info(headless: headless)[#body] }
    }
  }
}

#let render-row-notes(notes) = {
  if notes.len() > 0 {
    linebreak()
    text(size: 8.5pt)[
      #set block(spacing: 3pt)
      #render-grouped(notes, headless: true)
    ]
  }
}

// Header
#grid(
  columns: (1fr, auto),
  align: (left + horizon, right + horizon),
  text(size: 14pt, weight: "bold", fill: accent)[#report_data.name_upper],
  table(
    stroke: (x, _y) => if x > 0 { 0.4pt + ink } else { none },
    columns: (auto,),
    inset: (x: 8pt, y: 4pt),
    text(size: 12pt, weight: "bold")[TL #report_data.tl]
  ),
)
#v(3mm)

// Robot stats row (two-row multi-column table)
#{
  let rc = report_data.robot_columns
  if rc.len() > 0 {
    table(
      columns: rc.map(c => c.at(2) * 1fr),
      align: (col, _row) => if col == 0 { left } else { center },
      inset: (x: 6pt, y: 4pt),
      ..rc.map(c => table.cell(fill: label-bg)[*#c.at(0)*]),
      ..rc.map(c => [#c.at(1)]),
    )
    v(1mm)
  }
}

// Remaining spec rows
#table(
  columns: (auto, 1fr),
  inset: (x: 6pt, y: 4pt),
  ..for row in report_data.rows {
    (
      table.cell(fill: label-bg)[*#row.label*],
      [#row.value#render-row-notes(row.notes)],
    )
  }
)

// Detailed component breakdown
#{
  let secs = report_data.detail_sections
  if secs.len() > 0 {
    v(3mm)
    table(
      columns: (1fr, auto, auto, auto),
      inset: (x: 6pt, y: 4pt),
      ..{
        let cells = ()
        for sec in secs {
          cells = cells + (
            table.cell(fill: label-bg)[*#sec.title*],
            table.cell(fill: label-bg, align: center)[*#sec.col2_header*],
            table.cell(fill: label-bg, align: center)[*#sec.col3_header*],
            table.cell(fill: label-bg, align: right)[*Cost*],
          )
          for row in sec.rows {
            cells = cells + (
              [#row.name],
              table.cell(align: center)[#row.col2],
              table.cell(align: center)[#row.col3],
              table.cell(align: right)[#row.cost],
            )
          }
        }
        cells
      }
    )
  }
}

// Robot-level notes
#{
  let notes = report_data.robot_notes
  if notes.len() > 0 {
    v(3mm)
    render-grouped(notes)
  }
}
