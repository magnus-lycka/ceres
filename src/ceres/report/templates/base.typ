// base.typ — shared design tokens and helpers for ceres reports.
// Import in domain templates: #import "base.typ": accent, render-notes, ...

#import "@preview/gentle-clues:1.2.0": info as gc-info, warning as gc-warning, error as gc-error

#let accent = rgb("#cc2036")

// One admonition per category, sorted error → warning → info.
#let render-notes(notes) = {
  for cat in ("error", "warning", "info") {
    let msgs = notes.filter(n => n.at("category") == cat).map(n => n.at("message"))
    if msgs.len() > 0 {
      let body = msgs.map(m => [#m]).join(linebreak())
      if cat == "error"        { gc-error[#body] }
      else if cat == "warning" { gc-warning[#body] }
      else                     { gc-info[#body] }
    }
  }
}
