// computer_catalog.typ — Computer Equipment catalog for Central Supply Catalogue.
//
// Data injected by Python as: #let report_data = (...)
// Structure: report_data.(title, eyebrow, page_size, sections)
// Each section: (heading, headers, alignments, rows)
// Each row: (cells, notes) where notes are [{category, message}]

#import "base.typ": accent, render-notes

#set page(paper: report_data.at("page_size", default: "a4"), margin: (x: 20mm, y: 20mm))
#set text(font: "Linux Libertine", size: 10pt)
#set par(leading: 0.55em)

#align(center)[
  #text(size: 16pt, weight: "bold")[#report_data.title]
  #v(2pt)
  #text(size: 10pt, fill: rgb("#666666"))[#report_data.eyebrow]
]
#v(8mm)

#for section in report_data.sections {
  let headers = section.headers
  let alignments = section.alignments.map(a => if a == "right" { right } else { left })
  let n = headers.len()

  // First column expands if first alignment is left and last is right (item-style section);
  // otherwise last column expands (value-first section).
  let col-widths = if alignments.first() == left and alignments.last() == right {
    (1fr,) + range(n - 1).map(_ => auto)
  } else {
    range(n - 1).map(_ => auto) + (1fr,)
  }

  text(size: 11pt, weight: "semibold", fill: accent)[#section.heading]
  v(2pt)
  table(
    columns: col-widths,
    align: (x, _) => alignments.at(x),
    stroke: none,
    table.header(
      ..headers.map(h => table.cell(stroke: (bottom: 0.5pt + black))[#text(size: 8pt)[*#h*]])
    ),
    ..section.rows.map(row => {
      let cells = row.cells.map(c => [#c])
      let notes = row.at("notes", default: ())
      if notes.len() > 0 {
        cells + (
          table.cell(colspan: n, inset: (left: 1em, top: 0pt, bottom: 2pt))[
            #render-notes(notes)
          ],
        )
      } else {
        cells
      }
    }).flatten()
  )
  v(4mm)
}
