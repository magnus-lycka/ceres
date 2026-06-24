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
- Rename and move test files so paths mirror source paths.
- Update imports to match the new paths.
- Consult `docs/plan-test-suite-improvements.md` for guidance on which tests
  belong in mechanics files vs career-rule files vs entry-class files.

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

## 4. Test Suite Profiling and Tuning

**Goal:** keep the default `uv run pytest` run under a target wall-clock time
(TBD; currently ~9 seconds for ~3700 tests).

**Work required:**
- Profile with `pytest-profiling` or `--durations=20` to find slow tests.
- Identify tests that should be `@pytest.mark.slow` but are not.
- Look for redundant setup: tests that replay long event chains from scratch
  where a shared fixture could cache the result.
- Evaluate whether `scope='module'` on some `CharacterDriver` fixtures would
  help without sacrificing test isolation.
