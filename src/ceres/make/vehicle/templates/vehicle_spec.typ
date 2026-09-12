// vehicle_spec.typ — Vehicle specification sheet.
// Laid out after the Vehicle Handbook catalogue entries: a heavy title with a
// rule beneath it, description prose on the left, the stat table on the right.
// Data injected by Python as: #let report_data = (...)

#import "@preview/gentle-clues:1.2.0": abstract as gc-abstract, info as gc-info, warning as gc-warning, error as gc-error

#let accent = rgb("#cc5533")
#let ink = rgb("#0d0d0d")
#let table-rule = 0.5pt + luma(140)
#let label-bg = luma(242)

#set page(paper: report_data.page_size, margin: (x: 15mm, top: 12mm, bottom: 12mm))
#set text(font: ("Arial Narrow", "Helvetica Neue Condensed", "Helvetica"), size: 10pt, fill: ink)
#set table(stroke: table-rule)

#let render-grouped(notes, headless: false) = {
  for cat in ("error", "warning", "content", "info") {
    let msgs = notes.filter(n => n.at("category") == cat).map(n => n.at("message"))
    if msgs.len() > 0 {
      let body = msgs.map(m => [#m]).join(linebreak())
      if cat == "error" { gc-error(headless: headless)[#body] }
      else if cat == "warning" { gc-warning(headless: headless)[#body] }
      else if cat == "content" { gc-abstract(headless: headless)[#body] }
      else { gc-info(headless: headless)[#body] }
    }
  }
}

// Title bar, as the catalogue prints it: name in heavy caps over a rule.
#text(size: 26pt, weight: "bold")[#report_data.name_upper]
#v(-6pt)
#line(length: 100%, stroke: 1.2pt + accent)
#v(2pt)

// Description left, stat table right.
#grid(
  columns: (1fr, 1.1fr),
  column-gutter: 10mm,
  [
    #if report_data.description != "" [
      #par(justify: false)[#report_data.description]
      #v(4pt)
    ]
    *TYPE:* #report_data.type_line
    #linebreak()
    *FEATURES AND TRAITS:* #report_data.features_and_traits
  ],
  [
    #table(
      columns: (auto, 1fr),
      inset: (x: 5pt, y: 3.5pt),
      ..report_data.stats.map(row => (
        table.cell(fill: label-bg)[*#row.at("label")*],
        [#row.at("value")],
      )).flatten(),
    )
  ],
)

#v(4pt)

// An artwork block, when the design supplies one.
#if report_data.image != none [
  #v(2pt)
  #align(center)[#image(report_data.image, width: 82%)]
  #v(4pt)
]

#if report_data.notes.len() > 0 [
  #v(4pt)
  #render-grouped(report_data.notes)
]
