// base.typ — shared design tokens and helpers for ceres reports.
// Import in domain templates: #import "base.typ": accent, render-notes, ...

#import "@preview/gentle-clues:1.2.0": abstract as gc-abstract, info as gc-info, warning as gc-warning, error as gc-error

#let accent = rgb("#cc2036")

// One admonition per category, sorted error → warning → content → info.
#let render-notes(notes) = {
  for cat in ("error", "warning", "content", "info") {
    let msgs = notes.filter(n => n.at("category") == cat).map(n => n.at("message"))
    if msgs.len() > 0 {
      let body = msgs.map(m => [#m]).join(linebreak())
      if cat == "error"        { gc-error[#body] }
      else if cat == "warning" { gc-warning[#body] }
      else if cat == "content" { gc-abstract[#body] }
      else                     { gc-info[#body] }
    }
  }
}
