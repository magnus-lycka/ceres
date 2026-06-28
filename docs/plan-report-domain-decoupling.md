# Plan: Decouple ceres.report from domain packages

## Status: Not started

## Problem

`ceres.report` is architecturally intended to be a pure template engine with no
domain knowledge (CLAUDE.md: *"`ceres.report` is a template engine; it has no
domain knowledge. Domain packages own their Jinja2/Typst templates and context
builders."*). However, the dependency graph shows a cycle between `ceres.report`
and `ceres.make.robot`, and `ceres.make.ship` also feeds into `ceres.report`.

The cycle exists because `ceres.report` exposes domain-specific convenience
functions (`render_ship_html`, `render_ship_pdf`, `render_robot_pdf`, etc.)
which require it to import types and context builders from `ceres.make.ship` and
`ceres.make.robot`. Those packages simultaneously import `ceres.report` for
rendering infrastructure — creating the cycle.

## Intended dependency direction

```
ceres.make.ship   →  ceres.report   (uses rendering infrastructure)
ceres.make.robot  →  ceres.report   (uses rendering infrastructure)
ceres.report         (no domain imports)
```

## Fix

Move domain-specific render functions out of `ceres.report` and into their
respective domain packages:

- `render_ship_html`, `render_ship_typst`, `render_ship_pdf`,
  `render_ship_spec_html`, `render_ship_spec_pdf` → `ceres.make.ship`
- `render_robot_typst`, `render_robot_pdf` → `ceres.make.robot`
- Gear catalog render functions → `ceres.gear.catalog` (they already live
  there per CLAUDE.md; verify no stray imports remain in `ceres.report`)

After this change, `ceres.report` contains only generic rendering
infrastructure: Jinja2 and Typst engine wrappers, template loading, format
conversion. It imports nothing from `ceres.make.*` or `ceres.gear.*`.

## Impact on callers

CLAUDE.md documents the old import paths. Update them in docs and any
call sites:

```python
# Before
from ceres.report import render_ship_html, render_ship_pdf

# After
from ceres.make.ship import render_ship_html, render_ship_pdf
```

Since Ceres is alpha with one user and all call sites are in the test suite,
no compatibility shims are needed — just update the imports.

## Steps

1. Audit `ceres/report/` for all functions that import from `ceres.make.*` or
   `ceres.gear.*`.
2. Move each such function (and any helper it owns) to its domain package.
3. Update all import sites (tests, `__init__.py` re-exports, docs).
4. Verify `ceres.report` has no remaining domain imports.
5. Update CLAUDE.md examples to reflect the new import paths.
6. Run the full test suite.
