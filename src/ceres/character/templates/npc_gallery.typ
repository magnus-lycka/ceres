// npc_gallery.typ — NPC stat blocks, 2-column page, one per slot, flowing across pages.
// Data injected by Python as: #let report_data = (...)

#let accent = rgb("#384a6b")
#let rule-color = 0.3pt + rgb("#b0a090")

#set page(paper: report_data.page_size, margin: (x: 10mm, top: 10mm, bottom: 10mm), columns: 2)
#set text(font: ("Arial Narrow", "Helvetica Neue Condensed", "Helvetica"), size: 9pt)

#let render-npc(npc) = block(breakable: false, width: 100%, below: 6mm)[
  #block(
    width: 100%,
    fill: accent,
    inset: (x: 6pt, y: 4pt),
  )[
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      text(size: 11pt, weight: "bold", fill: white)[#npc.name],
      text(size: 9pt, fill: white)[#npc.career_rank],
    )
  ]
  #v(0.8mm)
  #table(
    columns: (1fr, 1fr, auto),
    stroke: rule-color,
    inset: (x: 5pt, y: 3pt),
    [*Sophont:* #npc.sophont],
    [*UCP:* #npc.ucp],
    [*Age:* #npc.age],
    table.cell(colspan: 3)[*Skills:* #npc.skills],
    ..if npc.equipment.len() > 0 {
      (table.cell(colspan: 3)[*Equipment:* #npc.equipment.join(", ")],)
    },
    ..if npc.notes != none {
      (table.cell(colspan: 3)[*Notes:* #npc.notes],)
    },
  )
]

#for npc in report_data.npcs {
  render-npc(npc)
}
