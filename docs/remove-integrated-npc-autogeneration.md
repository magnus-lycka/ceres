# Plan: Remove all NPC auto-generation code

## Context

The `auto_event()` system was built into `PendingInputBase` and every `Pending*`
subclass to support bulk NPC generation. This violates a clean boundary: the
character engine should be a pure event-sourced system driven by external clients;
it must not contain logic for auto-piloting itself. The `AutoFillContext`,
`_roll2d`, `_pick_skill_auto`, and all 39 `auto_event()` implementations are
internal coupling that should not exist. The bulk NPC web UI and its supporting
infrastructure is the client that should be removed, leaving no trace.

## Files to delete entirely

- `src/ceres/character/web/bulk.py`
- `tests/character/test_bulk.py`
- `tests/character/test_replay_integrity.py`
- `src/ceres/character/web/templates/gallery_form.html`
- `src/ceres/character/web/templates/gallery.html`

## `src/ceres/character/state.py`

- Remove `AutoFillContext` dataclass (currently lines ~21-26)
- Remove `auto_event()` abstract method from `PendingInputBase` (currently
  lines ~40-42, including its docstring)
- Remove `_pick_skill_auto()` method from `CharacterProjection` (currently
  lines ~325-334)
- Remove `auto_event()` delegation method from `CharacterProjection` (currently
  lines ~336-337)
- Remove `AutoFillContext` from `__all__`
- Remove `import random` if it becomes unused (check: `random` is also used
  for `random.Random` type hints in `auto_event` signatures — confirm nothing
  else needs it after removal)

## `src/ceres/character/events.py`

- Remove `_roll2d()` helper (currently lines ~77-78; only ever called from
  `auto_event` implementations)
- Remove `AutoFillContext` from the `TYPE_CHECKING` import block
- Remove all 39 `auto_event()` method bodies from every `Pending*` class
  (keep `event_from_form()` and `input_specs()` — those are interactive UI,
  not auto-generation)
- Remove `AutoFillContext` from `__all__`

## `src/ceres/character/web/routes.py`

Three changes:

1. **Remove gallery routes**: Delete the four gallery route handlers and their
   helper:
   - `GET /gallery/assignments` (~line 281)
   - `GET /gallery/new` (~line 292)
   - `POST /gallery/generate` (~line 303)
   - `POST /gallery/pdf` (~line 331)

2. **Remove dead imports**: After deleting the gallery routes, the import of
   `_NPC_DEFAULT_HOMEWORLD` from `bulk.py` becomes dead (its only use in
   `routes.py` is line ~191 inside the gallery form route being deleted). Remove
   that import. Also remove the `bulk` module import entirely.
   `render_npc_gallery_pdf` is still used at line ~260 for single-character PDF
   — keep that import.

3. **No homeworld constant needed here**: `routes.py` line ~191 is inside the
   gallery route being deleted, so `routes.py` has no remaining use of the
   homeworld constant after removal.

## `src/ceres/character/app.py`

`app.py` imports `_NPC_DEFAULT_HOMEWORLD` from `bulk.py` (line 10) and uses it
at line 72 for the `create_character()` interactive endpoint. After deleting
`bulk.py`, inline the constant directly in `app.py` — rename to
`_DEFAULT_HOMEWORLD` and define it there. Do not re-export from routes.

## `src/ceres/character/web/templates/base.html`

Remove the "NPC Gallery" nav link that points to `/ui/gallery/new`.

## `tests/character/test_web.py`

Remove the two gallery route tests (they test endpoints being deleted):

- `test_gallery_form_renders` (~line 346) — tests `GET /ui/gallery/new`
- `test_gallery_generate_returns_specs` (~lines 352-367) — tests
  `POST /ui/gallery/generate`

## `tests/character/test_replay.py`

- Remove `generate_npc` and `CohortParams` imports (line ~34)
- Remove the single test that uses `generate_npc`:
  `test_replaying_three_term_persisted_log_rebuilds_identical_projection`
  (lines ~305-335).

  **Replay integrity coverage**: the removed test is coupled to the NPC
  autopilot path (`generate_npc`) and cannot survive without it. Replay
  correctness remains covered by the explicit scripted-event replay tests in
  the same file. No replacement is needed.

## `tests/character/test_events_pending_inputs.py`

This file is 890 lines, 28 tests. Many tests check both `event_from_form()` and
`auto_event()` together. Surgical removal required:

- Remove `AutoFillContext` import and `_ctx()` helper (~lines 119, 136-137)
- Remove the one test that is exclusively about `auto_event`:
  `test_skill_choice_auto_events_fall_back_to_advancement_dm_when_no_skill_can_be_chosen`
  (~line 556)
- For each remaining test that calls `auto_event()` in addition to
  `event_from_form()`/`input_specs()`: remove the `auto_event` call and its
  assertion, keeping the `event_from_form` and `input_specs` assertions intact.
  Affected tests include (not exhaustive — check each):
  `test_pending_background_skills_builds_form_auto_event_and_specs`,
  `test_pending_career_choice_form_auto_event_and_specs`,
  `test_pending_draft_choices_build_expected_events_and_specs`,
  `test_roll_pending_inputs_build_events_and_number_specs`,
  `test_double_injury_pending_builds_two_roll_event_and_specs`,
  `test_decision_pending_inputs_build_events_and_specs`,
  `test_skill_choice_pending_inputs_parse_skills_and_advancement_dm`,
  `test_characteristic_benefit_life_and_connection_pending_inputs`,
  `test_career_and_precareer_specific_pending_inputs`
- Rename tests that currently say "form_auto_event_and_specs" to drop
  "auto_event" from the name where it was the primary subject.

## What to keep

- `src/ceres/character/report.py` — `render_npc_gallery_pdf` is used for
  single-character PDF rendering in `routes.py` (`character_pdf()` route at
  line ~260). Keep the function and its Typst template `npc_gallery.typ`.
- `tests/npcs/test_gallery.py` — tests `render_npc_gallery_pdf` as a renderer
  (passing a list of specs). It exercises the Typst/PDF pipeline, not
  auto-generation. Keep it.

## Pre-implementation check

Before removing `auto_event()` from `state.py` and `events.py`, confirm it has
no callers outside the now-deleted `bulk.py` and the test files being modified:

```bash
grep -r "auto_event\|AutoFillContext\|_pick_skill_auto\|_roll2d\|generate_npc\|generate_cohort\|CohortParams" \
  src/ tests/ --include="*.py" | grep -v "bulk\.py\|test_bulk\|test_replay_integrity"
```

All results should be in `state.py`, `events.py`, and the test files covered
by this plan. If anything unexpected appears, address it before proceeding.

## Verification

```bash
uvx ruff check src/ tests/         # no imports of deleted symbols
uvx ty check src/ceres/character/  # no type errors
uv run pytest -q                   # all tests pass
```

Confirm zero remaining references to deleted symbols. Three targeted greps:

**1. Deleted auto-generation symbols** — scope is `character/` only, so
`tests/npcs/test_gallery.py` (which imports `render_npc_gallery_pdf` from
`report.py`, not from the deleted module) is not in scope and cannot interfere:

```bash
grep -r "auto_event\|AutoFillContext\|_pick_skill_auto\|_roll2d\|generate_npc\|generate_cohort\|CohortParams" \
  src/ceres/character/ tests/character/ \
  --include="*.py" --include="*.html"
```

**2. Imports of the deleted `bulk` module** — `tests/npcs/test_gallery.py`
imports from `ceres.character.report`, not from `bulk`, so it will not appear:

```bash
grep -r "ceres\.character\.web\.bulk\|from.*web import bulk\|from.*web\.bulk" \
  src/ tests/ --include="*.py"
```

**3. Deleted route URLs and nav text**:

```bash
grep -r "gallery/new\|gallery/generate\|gallery/pdf\|gallery/assignments\|NPC Gallery" \
  src/ tests/ --include="*.py" --include="*.html"
```

All three greps should return no output.
