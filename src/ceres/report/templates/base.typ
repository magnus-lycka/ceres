// base.typ — shared design tokens and helpers for ceres reports.
// Import in domain templates: #import "base.typ": accent, render-notes, ...

#let accent = rgb("#cc2036")
#let ink-soft = rgb("#666666")
#let warning-color = rgb("#e07800")
#let error-color = rgb("#cc2036")

// Render a list of note dicts [{category: str, message: str}] as inline content.
#let render-notes(notes) = {
  for note in notes {
    let msg = note.at("message")
    let cat = note.at("category")
    if cat == "info" {
      text(size: 8pt, fill: ink-soft, style: "italic")[#msg]
    } else if cat == "warning" {
      text(size: 8pt, fill: warning-color, style: "italic")[Warning: #msg]
    } else if cat == "error" {
      text(size: 8pt, fill: error-color, weight: "bold")[Error: #msg]
    }
    linebreak()
  }
}
