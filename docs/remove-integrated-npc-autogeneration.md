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

Four changes:

1. **Move the homeworld constant**: `_NPC_DEFAULT_HOMEWORLD` is currently
   imported from `bulk.py` but is also used for interactive character creation
   (line ~191). After deleting `bulk.py`, define it locally in `routes.py`
   (rename to `_DEFAULT_HOMEWORLD` — it is no longer NPC-specific).

2. **Fix `app.py` import**: `app.py` also imports `_NPC_DEFAULT_HOMEWORLD`
   from `bulk.py`. Change to import `_DEFAULT_HOMEWORLD` from `routes.py`.

3. **Remove gallery routes**: Delete the four gallery route handlers and their
   helper:
   - `GET /gallery/assignments` (~line 281)
   - `GET /gallery/new` (~line 292)
   - `POST /gallery/generate` (~line 303)
   - `POST /gallery/pdf` (~line 331)

4. **Remove unused imports** that become dead: `render_npc_gallery_pdf` import
   stays if it is still used for single-character PDF (line ~260 uses it — keep).
   Remove only the bulk-module import.

## `src/ceres/character/web/templates/base.html`

Remove the "NPC Gallery" nav link that points to `/ui/gallery/new`.

## `tests/character/test_replay.py`

- Remove `generate_npc` and `CohortParams` imports (line ~34)
- Remove the single test that uses `generate_npc`:
  `test_replaying_three_term_persisted_log_rebuilds_identical_projection`
  (lines ~305-335). The replay integrity concept is covered by the
  scripted-event tests in the same file.

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

## Verification

```bash
uvx ruff check src/ tests/         # no imports of deleted symbols
uvx ty check src/ceres/character/  # no type errors
uv run pytest -q                   # all tests pass
```

Confirm zero remaining references:
```bash
grep -r "auto_event\|AutoFillContext\|_pick_skill_auto\|_roll2d\|generate_npc\|generate_cohort\|CohortParams\|bulk\.py\|gallery" \
  src/ceres/character/ tests/character/ \
  --include="*.py" --include="*.html"
```
