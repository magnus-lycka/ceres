# Plan: Test Suite Restructuring

This plan documents work to be done after the initial test-structure checkin
that established `tests/unit/`, `tests/approval/`, and `tests/gallery/`.

See `DEVELOPMENT_AND_TESTING.md` for the current structure and conventions.

## 1. Mirror `src/ceres/` in `tests/unit/`

**Goal:** every module `src/ceres/a/b/c.py` has a corresponding
`tests/unit/a/b/test_c.py`. Finding the tests for a module should be
mechanical.

**Current state:** `tests/unit/` groups tests by broad domain
(`character/`, `make/`, `report/`, etc.) but the internal structure does not
closely follow the source tree. For example, `tests/unit/character/` contains
tests for modules in several different sub-packages of
`src/ceres/character/`.

**Work required:**

- Audit `src/ceres/` and list modules with no corresponding test file.
  (`tools/check_unit_coverage.sh` automates this.)
- Rename and move test files so paths mirror source paths.
- Update imports to match the new paths.
- Consult `docs/plan-test-suite-improvements.md` for guidance on which tests
  belong in mechanics files vs career-rule files vs entry-class files.

**Recent progress:**

- Pre-career unit test stubs that contained only `import ceres` were filled in:
  `test_university.py`, `test_colonial_upbringing.py`, `test_merchant_academy.py`,
  `test_psionic_community.py`, `test_school_of_hard_knocks.py`,
  `test_spacer_community.py`. Tests cover entry data, `apply_entry`,
  `apply_graduation` (including honours branches), and `is_available`.
- `test_prisoner_events.py` was filled in: covers `ParoleRollHandler`
  (threshold = roll+2, narrative), `PendingParoleRoll` (form parsing, input
  specs), and `set_forced_prison_career`.
- A large backlog of modules with 0% unit test coverage remains, primarily
  in `make/ship/`, `make/robot/`, `character/report.py`, and
  `character/web/`. Run `tools/check_unit_coverage.sh` for the current list.

## 2. More Usecase Tests

**Goal:** any scenario that involves serious interaction between several
modules, or where "nothing else changed" is a meaningful invariant, should
have a usecase approval test.

**Candidates to evaluate:**

- Other Scholar mishaps with multiple simultaneous effects (e.g. mishap 3
  openly/secretly, mishap 5 start-again).
- Complex events from other careers: Rogue, Entertainer, Psion events with
  branching multi-effect choices.
- Pre-careers and how they impact qualification, commission, and basic training
  for following careers.
- Any scenario currently tested with raw `projection_diff` assertions.

**Criterion:** if writing plain assertions requires more than five
`assert ...` lines to capture "the complete observable outcome", consider
a usecase snapshot instead.

## 3. More NPC Approval Tests

**Goal:** cover full character generation paths — pre-career through muster-out
— as end-to-end approval tests under `tests/approval/character/npcs/`.

**Candidates:**

- A character with a pre-career followed by one or more regular careers:
  verifies that pre-career skills, qualification DMs, commission eligibility,
  and basic training carry through correctly into subsequent careers.
- A character who fails qualification and enters the draft.

## 4. Convert Hardcoded Approval-Test Assertions to Snapshots

**Goal:** every file under `tests/approval/` uses the snapshot approach
(`AnnotatedSnapshot` + `AnnotatedJSONSnapshotExtension`), not hardcoded `assert`
statements. Hardcoded assertions in approval tests encode whatever the code
happens to produce; they do not protect against unintended side-effects and
they rot silently when behaviour changes.

**Pattern:** drive a scenario with `CharacterDriver` to the natural resolution
point; snapshot `d.projection.summary.model_dump(mode='json')`. Use
`snap.annotate(key, note)` to flag known discrepancies from source material.
Error paths use `pytest.raises` — they need no snapshot.

Files to convert (assertion count at time of audit):

| File | Asserts | Status |
| --- | --- | --- |
| `tests/approval/ships/test_weapons.py` | 303 | not started |
| `tests/approval/character/uc/test_events_pending_inputs.py` | 237 | not started |
| `tests/approval/character/uc/test_web.py` | 231 | not started |
| `tests/approval/ships/test_systems.py` | 211 | not started |
| `tests/approval/character/uc/test_careers.py` | 201 | not started |
| `tests/approval/character/uc/test_companion_precareers.py` | 131 | not started |
| `tests/approval/ships/test_serialization.py` | 126 | not started |
| `tests/approval/ships/test_hulls.py` | 80 | not started |
| `tests/approval/character/uc/test_precareers.py` | 71 | not started |
| `tests/approval/ships/test_ship_pdf.py` | 67 | not started |
| `tests/approval/character/uc/test_projection.py` | 58 | not started |
| `tests/approval/robots/test_default_suite.py` | 54 | not started |
| `tests/approval/character/uc/test_career_identity.py` | 52 | not started |
| `tests/approval/character/uc/test_aging.py` | 46 | **deleted** — covered by unit tests and UC/E2E snapshots. |
| `tests/approval/character/uc/test_career_class.py` | 35 | not started |
| `tests/approval/character/uc/test_military_and_draft.py` | 31 | not started |
| `tests/approval/ships/test_ship_html.py` | 32 | not started |
| `tests/approval/robots/test_robot_pdf.py` | 28 | not started |
| `tests/approval/robots/test_robot_skill_packages.py` | 27 | not started |
| `tests/approval/robots/test_serialization.py` | 17 | not started |
| `tests/approval/robots/test_customisation.py` | 23 | not started |
| `tests/approval/character/uc/test_character_summary.py` | 14 | not started |
| `tests/approval/robots/test_text_and_spec.py` | 12 | not started |
| `tests/approval/character/uc/test_career_term_narrative.py` | 9 | not started |
| `tests/approval/character/uc/test_common_career_handlers.py` | 8 | not started |
| `tests/approval/character/uc/test_web_worlds.py` | 7 | not started |
| `tests/approval/character/uc/test_settings.py` | 5 | not started |
| `tests/approval/character/uc/test_sophont.py` | 4 | not started |

Note: `test_events_pending_inputs.py` tests event/pending mechanics directly
(`apply()`, `event_from_form()`, `input_specs()`). Those are correct for that
abstraction level; structural and error-path checks (`pytest.raises`, `isinstance`)
may stay as plain assertions. Non-trivial state checks should still use snapshots.

## 5. Test Suite Profiling and Tuning

**Goal:** keep the default `uv run pytest` run under a target wall-clock time
(TBD; currently ~9 seconds for ~3700 tests).

**Work required:**

- Profile with `pytest-profiling` or `--durations=20` to find slow tests.
- Identify tests that should be `@pytest.mark.slow` but are not.
- Look for redundant setup: tests that replay long event chains from scratch
  where a shared fixture could cache the result.
- Evaluate whether `scope='module'` on some `CharacterDriver` fixtures would
  help without sacrificing test isolation.
