# Plan: Test Suite Improvements for ceres.character

## Summary of findings

The test suite has good overall coverage (97% total) but has structural issues
from code reorganisation that the tests didn't fully follow. The improvements
fall into four categories: coverage gaps, abstraction-level violations,
structural/DRY issues, and low-value tests.

## Coverage gaps (meaningful ones)

| Module | Coverage | Issue |
|---|---|---|
| `character/report.py` | 21% | Typst/PDF rendering paths essentially untested |
| `character/domain/homeworld/homeworld_events.py` | 82% | `input_specs` branch paths at lines 66, 89–125 |
| `character/domain/life_events.py` | 87% | Several outcome paths at lines 216, 298–333 |
| `character/domain/psionics.py` | 88% | Gaps at 139–189, 219–232, 272–299, 363 |
| `character/mechanism/store.py` | 86% | Serialisation/deserialisation edge paths |
| `character/mechanism/pending_input.py` | 89% | Abstract base class branches |
| `character/web/routes.py` | 88% | Error/edge case routes |

`character/report.py` at 21% is the most concerning gap; it is probably
untestable in the unit suite (requires Typst installed) and should be either
explicitly marked as requiring a slow/integration test or covered by a
generated-output test with `--with-generated-output`.

## Abstraction-level violations

### `test_events_pending_inputs.py` (1464 lines) — main offender

CLAUDE.md requires strict separation:
- Career rule tests → `CharacterDriver`, live in career test files
- Event/pending mechanics tests → work with event/pending objects directly
- Form/web boundary tests → test `input_specs` and `event_from_form`

The file currently mixes all three. Examples of tests at the wrong level:

- `test_mishap_handler_gain_connections_effect_queues_two_connection_rolls` —
  career rule behaviour tested through the event machinery layer. Should be in a
  career test file using `CharacterDriver`.
- `test_connections_roll_handler_inserts_name_pending_before_other_pending` —
  similarly a career behaviour test.
- `FakeCareer` and `FakePrisonerCareer` stub classes — a design smell. Real
  careers should be usable directly; if they cannot be, the interface needs
  fixing.

The correct tests to leave in `test_events_pending_inputs.py`: anything testing
`apply()`/`resolve()` mechanics directly, `event_from_form` parsing, and
`input_specs` form building.

## Structural and DRY issues

### `test_scout.py` uses raw `Event(...)` construction

`test_scout.py` still builds events with `Event(fulfills=(started.id, 0), ...)`
directly rather than the `scripted_event`/`pending_id` helpers now in
`helpers.py`. It should be migrated for consistency with the other test files.

### Duplicated setup functions across files

Some test files define their own `_full_setup()` functions instead of importing
from `helpers.py` or using `CharacterDriver`. This is inconsistent and means
setup drift is not caught early.

### Missing dedicated test modules

- **`test_career_data.py`**: No dedicated unit tests for `career_data.py`
  effects (`GainSkillEffect`, `SkillChoiceEffect`, `GainConnectionsRolledEffect`,
  etc.). These are only tested indirectly through integration tests. Direct unit
  tests would catch regressions in the data model itself.
- **`test_connection_events.py`**: Connection event handling is scattered across
  `test_events_pending_inputs.py` with no dedicated file.

### `test_dice.py` — exists and is complete

Created as part of the `DiceRoll` implementation. Good model for future
dedicated module tests.

## Low-value tests

### `test_career_class.py` (337 lines)

Mostly verifies structural properties: `isinstance(career, CareerData)`, names
match strings, assignments exist. These assertions are essentially documenting
the data rather than guarding against behavioural regressions. They bring little
value as a safety net for bold refactoring.

Candidates for deletion or replacement with a single structural smoke test that
checks all careers load and have the expected shape, rather than per-career
repetition.

### Duplicate coverage in `TestCareerEntry` and per-career files

`test_careers.py` uses Scout Courier as the default test career for general
mechanics (survive, term_event, advancement). Career-specific Scout tests in
`test_scout.py` also use the same setup. There is some redundancy, though it is
not harmful.

## Recommended improvements (priority order)

### 1. Extract career-rule tests from `test_events_pending_inputs.py`

Move tests that verify career rule behaviour (connections effects, mishap
handler side effects) into the relevant career test files using `CharacterDriver`.
Leave only genuine event/pending mechanics and form boundary tests in
`test_events_pending_inputs.py`.

This directly addresses the abstraction-level violation and makes it obvious
which tests are affected when a career changes.

### 2. Add `test_career_data.py`

Unit tests for the effect data model:
- `GainSkillEffect.apply()` grants the skill at the right level
- `GainConnectionsRolledEffect` uses `DiceRoll` correctly
- `SkillChoiceEffect` with options produces a `PendingSkillChoice`
- Characteristic increase/decrease effects
- `BenefitDmEffect`, `AdvancementDmEffect` store the right DM

These are small, fast, and catch regressions in the shared effect machinery
that underlies every career.

### 3. Migrate `test_scout.py` to `scripted_event`/`pending_id` helpers

Straightforward consistency fix. The file is already using `Event()` with
`(started.id, 0)` chaining, which is the pattern the helpers were designed to
replace.

### 4. Address `character/report.py` coverage

Determine whether the Typst rendering can be exercised in the existing
`--with-generated-output` slow tests, or whether it needs explicit unit tests
for the template-context building (separating template rendering from context
construction).

### 5. Review `test_career_class.py` for pruning

Decide whether the structural assertions add enough value to justify their
maintenance cost, or whether a single parametrised smoke test covers the intent
more efficiently.

## Relationship to other plans

- `plan-approval-testing.md`: The complex multi-effect event tests (Scholar
  event 3) should eventually move to the approval test tier rather than inline
  `projection_diff` assertions. Do not spread `projection_diff` into the new
  tests being written during this improvement work — use targeted assertions or
  approval tests, not inline expected-dict diffs.
