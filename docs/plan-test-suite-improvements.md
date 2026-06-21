# Plan: Test Suite Improvements for ceres.character

## Core principle

**Test things in the right place.** Each class or module has one correct home
for its unit tests. Implementation details of a class belong in that class's
dedicated test file — not in some other test that happens to exercise the class
as a side effect.

When a test breaks because an internal of class X changed, but the observable
behaviour of the system that USES X didn't change, the test was in the wrong
place.

Applying this to the character domain:

| What is being tested | Correct test file |
| --- | --- |
| `ConnectionsRollHandler` inserts name pendings before existing pendings | `test_connection_events.py` |
| `GainSkillEffect.apply()` grants the right skill level | `test_career_data.py` |
| `GainConnectionsRolledEffect` d3 vs d6 option generation | `test_career_data.py` |
| Scout mishap 3 applies connections effects at all | `test_scout.py` (observable: connections are added) |
| Army mishap 3 applies a skill choice and an enemy | `test_army.py` (observable: can choose skill, enemy appears) |
| `PendingSkillChoice.input_specs()` builds the right form spec | `test_events_pending_inputs.py` or `test_input_specs.py` |
| `AdvancementHandler.apply()` queues reenlist after a successful roll | `test_events_pending_inputs.py` |

## Summary of findings

The test suite has good overall coverage (97% total) but has structural issues
from code reorganisation that the tests didn't fully follow. The improvements
fall into four categories: coverage gaps, abstraction-level violations,
structural/DRY issues, and low-value tests.

## Coverage gaps (meaningful ones)

| Module | Coverage | Issue |
| --- | --- | --- |
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

### `test_events_pending_inputs.py` — mixed responsibilities

This 1400+ line file mixes three different kinds of tests that belong in
separate files:

- **Career rule tests** that use `_projection(current_career=SCOUT)` or
  `_projection(current_career=ARMY)` to test a specific mishap or event outcome.
  These belong in the career test file for that career and should use
  `CharacterDriver` so they assert observable outcomes, not implementation
  details.
- **Event/pending mechanics tests** that verify `apply()`/`resolve()` machinery,
  `event_from_form` parsing, and form spec building. These are in the right
  file.
- **Connection event mechanics tests** that verify the ordering or content of
  pending inputs produced by connection handlers. These belong in
  `test_connection_events.py`.

When moving a test, the question to ask is: *whose implementation detail is
this testing?* A test that checks `PendingSkillChoice` appeared in the pending
list is testing the internals of `MishapHandler` and should be near
`MishapHandler`, not inside a Scout career test.

### Career rule tests using pending type names

CLAUDE.md requires career rule tests to use `CharacterDriver` and assert only
observable outcomes — "does the career end?", "was an enemy gained?", "can the
player choose a skill?". Checking `isinstance(p, PendingSkillChoice)` in a
career test directly names an implementation detail of the event layer.

Where `CharacterDriver` lacks a method to drive a scenario without naming a
pending type, add the method. Example: `choose_skill()` was added to let Army
mishap 3 tests assert that a skill was granted without importing
`PendingSkillChoice`.

## Structural and DRY issues

### `test_scout.py` — Event() constructor migration ✅ DONE

Migrated from raw `Event(fulfills=(x.id, 0), ...)` to
`_event(fulfills=_pending(x, 0), ...)` throughout. This is transitional; the
end state for career rule tests in `test_scout.py` is `CharacterDriver`.
Tests that are event or homeworld mechanics should be explicitly classified and
stay in (or move to) the appropriate mechanics file.

### Duplicated setup functions across files

Some test files define their own `_full_setup()` functions instead of using
`CharacterDriver`. `CharacterDriver` is the single point of contact for career
rule tests; private setup functions that build event lists belong only in files
that genuinely test event machinery.

### Missing dedicated test modules

- **`test_career_data.py`**: No dedicated unit tests for `career_data.py`
  effects (`GainSkillEffect`, `SkillChoiceEffect`, `GainConnectionsRolledEffect`,
  etc.). These effects are only tested indirectly through career integration
  tests. Direct unit tests would catch regressions in the effect machinery and
  remove the need to test effect internals from career tests.
- **`test_connection_events.py`**: Created with the connection-pending ordering
  test. Further connection event mechanics belong here.

## Low-value tests

### `test_career_class.py` (337 lines)

Mostly verifies structural properties: `isinstance(career, CareerData)`, names
match strings, assignments exist. These are documentation, not safety net.
Candidates for deletion or replacement with a single parametrised smoke test.

## Completed work

### Priority 3 — Migrate `test_scout.py` ✅ DONE

All raw `Event(fulfills=(x.id, N), ...)` constructions replaced with
`_event(fulfills=_pending(x, N), ...)`.

### Priority 1 — Extract misclassified tests (partial) ✅

Four career-rule tests removed from `test_events_pending_inputs.py`:

- `test_mishap_handler_gain_connections_effect_queues_two_connection_rolls` —
  deleted; already covered by `test_mishap_3_creates_pending_for_contacts_roll`
  in `test_scout.py`.
- `test_mishap_handler_d3_connections_effect_uses_d3_options` — moved to
  `test_scout.py` as `test_mishap_3_enemy_roll_has_d3_options`.
- `test_connections_roll_handler_inserts_name_pending_before_other_pending` —
  reclassified as connection event mechanics and moved to
  `test_connection_events.py`.
- `test_mishap_handler_skill_choice_effect_queues_pending_skill_choice` —
  reclassified as Army career rule and moved to `test_army.py` as
  `TestArmyMishap3`, rewritten via `CharacterDriver.choose_skill()`.

`CharacterDriver.choose_skill()` added to `helpers.py` to let career rule tests
drive `PendingSkillChoice` resolution without naming the type.

### Priority 1 — TermEventHandler tests decoupled from real careers ✅

The four `TermEventHandler` effect tests used Scout/Army event tables to inject
effects, coupling them to those career implementations. Each is now decoupled:

- Added `_FakeEventCareer(CareerData)` — a minimal `CareerData` subclass with
  only the interface `TermEventHandler` needs (`events`, `name`,
  `available_tables`, `current_ranks`, `update_current_term_rank`). Not
  registered in `CareerData._registry` (no `type` ClassVar set).
- Added subclasses `_LifeEventCareer`, `_AutoAdvanceCareer`, `_MishapStayCareer`,
  `_SkillChoiceCareer` — each with a single event at roll 1 with the relevant
  effect.
- Added `_fake_career_projection(career_class)` helper that constructs a minimal
  projection using the fake career.
- All four tests now use `TermEventHandler(roll=1)` against the matching fake
  career, independent of Scout/Army event tables.

### `test_career_data.py` created ✅

29 focused unit tests for all `career_data.py` effect classes that have
`apply()` methods: `GainSkillEffect`, `DecreaseCharacteristicEffect`,
`GainContactEffect/AllyEffect/RivalEffect/EnemyEffect`, `AdvancementDmEffect`,
`QualificationDmEffect`, `BenefitDmEffect`, `ParoleThresholdChangeEffect`,
`AutoQualifyCareerEffect`, `LoseAllCareerBenefitsEffect`.

The mega-test `test_effect_apply_methods_and_skill_entries` was dissolved: its
effect `apply()` assertions moved to `test_career_data.py`; its
`_apply_skill_table_entry` assertion split into three focused tests in
`test_events_pending_inputs.py`.

## Remaining improvements (priority order)

### 1. Continue extracting misclassified tests from `test_events_pending_inputs.py`

Scan remaining tests that use `_projection(current_career=X)`. Any test
verifying a career-specific outcome by calling `.apply()` on a fabricated
projection belongs in the career test file. Move it, rewrite it to use
`CharacterDriver`, and assert observable outcomes.

Add `CharacterDriver` methods as needed rather than letting tests name pending
types.

### 3. Address `character/report.py` coverage

Determine whether the Typst rendering can be exercised in the existing
`--with-generated-output` slow tests, or whether it needs explicit unit tests
for the template-context building.

### 4. Review `test_career_class.py` for pruning

Decide whether the structural assertions add enough value or whether a single
parametrised smoke test covers the intent.

### 5. Migrate `test_scout.py` career-rule tests to `CharacterDriver`

The `_event`/`_pending` migration is transitional. Career rule tests should
eventually use `CharacterDriver` exclusively, matching the pattern already in
`test_army.py`. Homeworld and form mechanics tests may stay with the
lower-level approach in their appropriate mechanics files.

## Relationship to other plans

- `plan-approval-testing.md`: `projection_diff`/DeepDiff is valuable for
  complex state-transition tests where "nothing else changed" is part of the
  behaviour under test — aim it at approval-style tests for complex
  multi-effect events rather than spreading hand-written inline expected-dict
  diffs.
