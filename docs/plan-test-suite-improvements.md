# Plan: Test Suite Improvements for ceres.character

## Purpose

This plan supports [plan-career-entry-outcomes.md](plan-career-entry-outcomes.md).

The old version of this plan treated `career_data.py` effect classes as a
stable unit-test target. That is no longer the right destination. The new model
will replace generic `CareerEventEntry` / `MishapEntry` rows with typed entry
outcomes, and many `*Effect` classes should disappear.

The test-suite work should therefore be split into three categories:

1. **Before the entry-outcome refactor:** improve the safety net and remove
   misleading tests that would fight the refactor.
2. **During the refactor:** write TDD tests for projection verbs and typed entry
   classes as they are introduced.
3. **After the refactor:** prune transitional tests and broad structural tests
   that no longer add value.

## Core Principle

**Test things in the right place.** Each class or module has one correct home
for its tests. Implementation details of class X belong in tests for class X,
not in a career rule test that happens to exercise X as a side effect.

Applying this to the character domain:

| What is being tested | Correct home |
| --- | --- |
| `ConnectionsRollHandler` inserts name pendings before existing pendings | `test_connection_events.py` |
| Projection state operation, e.g. `decrease_characteristic()` | `test_character_projection.py` or equivalent focused state test |
| Shared typed entry, e.g. `AdvancementDmEntry` | `test_career_data.py` while entries live in `career_data.py` |
| Scout mishap 3 observable outcome | `test_scout.py` via `CharacterDriver` |
| Army mishap 3 observable outcome | `test_army.py` via `CharacterDriver` |
| `PendingSkillChoice.input_specs()` | `test_events_pending_inputs.py` or `test_input_specs.py` |
| `AdvancementHandler.apply()` event/pending mechanics | `test_events_pending_inputs.py` |

Career rule tests should not name pending types, event IDs, fulfillment order,
or concrete event classes. If a career rule test needs to drive a pending input,
add a `CharacterDriver` method.

## Current State

### Completed

- `test_scout.py` raw `Event(fulfills=(x.id, N), ...)` construction was migrated
  to `_event(fulfills=_pending(x, N), ...)`.
- Several misclassified tests were removed from `test_events_pending_inputs.py`:
  connection ordering moved to `test_connection_events.py`, and Army mishap 3
  moved to `test_army.py`.
- `CharacterDriver.choose_skill()` was added so career tests can resolve a
  skill-choice pending without importing `PendingSkillChoice`.
- The `TermEventHandler` tests were decoupled from real Scout/Army career
  tables by using small fake careers in `test_events_pending_inputs.py`.
- `test_career_data.py` was created with focused tests for current effect
  `apply()` behavior. It currently covers the direct-mutation effect classes:
  `GainSkillEffect`, characteristic decrease, connection gain effects,
  advancement/qualification/benefit DMs, parole threshold changes,
  auto-qualification, and benefit forfeiture.

### Current Implementation Audit

The current implementation already matches several of this plan's prerequisites:

- `tests/character/test_connection_events.py` exists and owns connection
  pending-ordering mechanics.
- `CharacterDriver.choose_skill()` exists and resolves `PendingSkillChoice`
  without exposing that pending type to career tests.
- `tests/character/test_events_pending_inputs.py` still has many
  `_projection(current_career=...)` uses. Many are legitimate event/pending
  mechanics tests, such as commission, reenlistment, advancement, assignment
  switching, prisoner advancement, and pending-choice resolution. These should
  be classified carefully; do not move them merely because a real career appears
  in the fixture.

### Important Reclassification

`test_career_data.py` effect tests are **transitional**. They are useful only as
a safety net while behavior is moved from effect wrappers into projection verbs
and typed entry classes.

They should not be treated as proof that `GainSkillEffect`,
`AdvancementDmEffect`, `BenefitDmEffect`, and similar classes are good
long-term abstractions.

## Before `plan-career-entry-outcomes.md`

Do these before starting the entry-outcome refactor. The goal is to reduce
noise, preserve behavior, and make failures point at the right layer.

### 1. Finish Misclassified Test Extraction

Scan `test_events_pending_inputs.py` for tests that fabricate a projection with
`current_career=...` and then call a real career handler to assert a
career-specific outcome.

For each test:

- If it checks observable Traveller behavior, move it to the career-specific
  file and rewrite it through `CharacterDriver`.
- If it checks handler or pending-input mechanics, keep it in
  `test_events_pending_inputs.py` or move it to a more specific mechanics file.
- If it checks connection-event mechanics, move it to `test_connection_events.py`.

Add `CharacterDriver` methods instead of letting career tests import pending
types.

This work should happen before the entry-outcome refactor so that later changes
to `MishapHandler`, `TermEventHandler`, and entry classes do not create
misleading career-test failures.

Do not use `current_career=...` as a mechanical grep-and-move rule. It is only
a smell. Several mechanics tests need a real-ish career so the handler can
exercise generic event/pending machinery.

### 2. Convert Obvious Career Rule Tests to `CharacterDriver`

Do the easy, high-value conversions in career files, especially where tests
already read as "do career thing, observe result."

Good candidates:

- remaining Scout career-rule tests that are still event-chain based
- career tests that assert pending type names instead of driving the choice
- simple survival, mishap, skill-choice, and advancement flows

Do **not** convert tests that genuinely verify event mechanics, form parsing,
homeworld-change pending behavior, or pending ordering. Move or label those
instead.

### 3. Keep Transitional Effect Tests Focused

Keep `test_career_data.py` effect tests small and factual while effects still
exist. Their job is to pin current behavior before it moves.

Do not expand them into a large permanent test suite for the old effect model.
In particular, avoid adding broad tests that make `effects=[...]` look like the
desired future abstraction.

The existing `test_career_data.py` tests are enough for the direct-mutation
effects. New tests should usually target projection verbs or typed entries
instead of adding more coverage for soon-to-be-deleted effect wrappers.

### 4. Establish Snapshot/Approval Experiment

Try one complex state-delta test using the options in
[plan-approval-testing.md](plan-approval-testing.md):

- `inline-snapshot`
- Syrupy
- custom approval fixtures only if the library options fail

Use one existing `projection_diff` case such as Scholar event 3 accept. The
goal is to decide the test style before the entry-outcome refactor creates more
complex multi-effect migration tests.

## During `plan-career-entry-outcomes.md`

This is not separate cleanup. It is part of the TDD implementation of the
entry-outcome refactor.

### 1. Projection Verb Tests

When adding projection verbs, add focused tests first.

Examples:

- `decrease_characteristic()` lowers a characteristic and removes PSI/psionics
  when PSI reaches zero.
- `add_advancement_dm()` and `add_qualification_dm()` accumulate modifiers.
- `add_benefit_dm()` records the DM on the current muster-out record.
- `adjust_parole_threshold()` clamps to the valid range.
- `auto_qualify()` adds a career once.
- `forfeit_current_career_benefits()` affects only the current career's terms.
- `queue_skill_choice()` creates the expected pending input with stable
  `pending_idx`.
- `queue_connection_roll()` uses the dice roll options.

These tests should live near the state/event layer, not in career-specific
files.

### 2. Shared Entry Class Tests

As each shared entry class is introduced, test it directly before migrating
career rows to it.

Examples:

- `GainSkillEntry` grants the skill.
- `GainConnectionEntry` adds the connection with the entry text as origin.
- `GainSkillAndConnectionEntry` does both.
- `AdvancementDmEntry`, `QualificationDmEntry`, and `BenefitDmEntry` delegate to
  the projection verbs.
- `SkillChoiceEntry` queues the choice and returns the next pending index.
- `RolledConnectionsEntry` queues a roll with d3/d6 options.
- `LifeEventEntry`, `RollMishapEntry`, `InjuryEntry`, and `AutoAdvanceEntry`
  produce the same pending/control-flow behavior as the old effects.

These replace, rather than supplement forever, old effect tests.

### 3. Characterize Migrated Career Rows

For each migrated effect family, keep or add a small number of observable
career tests through `CharacterDriver`.

Example migrations:

- `effects=[GainEnemyEffect(), GainSkillEffect(...)]`
  becomes a typed entry and is covered by a career test that observes the enemy
  and the granted skill.
- `effects=[AdvancementDmEffect(amount=2)]`
  becomes `AdvancementDmEntry` and is covered by a shared entry test plus one
  representative career flow if needed.

Avoid duplicating the same shared entry behavior across every career that uses
it.

Where an existing career test currently asserts a pending type, prefer to drive
the pending through `CharacterDriver` and assert the resulting skill,
connection, rank, career state, or benefit-roll state. Only mechanics tests
should inspect pending classes directly.

### 4. Migrate Transitional Effect Tests

As each old effect class disappears:

- delete its `test_career_data.py` tests
- ensure equivalent projection verb or entry class tests exist
- keep one observable career rule test only where the career behavior itself is
  meaningful

This keeps the test suite from preserving the old design by accident.

### 5. Use Snapshot/Approval Tests Sparingly

Use snapshot/approval style only when a row has several simultaneous effects and
"nothing else changed" is part of the invariant.

Good candidates:

- Scholar event 3 accept
- complex mishaps with multiple pending inputs, connections, skills, and
  benefit-roll changes

Single-effect entries should use ordinary assertions.

## After `plan-career-entry-outcomes.md`

Do these only after the old `effects=[...]` model and legacy support are gone.

### 1. Delete Old Effect Tests

Remove any tests whose only purpose was to verify deleted `*Effect.apply()`
methods.

The remaining tests should target:

- projection verbs
- typed entry classes
- event/pending mechanics
- observable career behavior

### 2. Revisit `test_career_class.py`

`test_career_class.py` mostly checks structural facts such as career names,
assignments, and `CareerData` instances. After the entry-outcome refactor,
replace broad repetitive assertions with a smaller smoke test if possible:

- all careers load
- all careers have six event rows and six mishap rows where applicable
- entries are typed `CareerTableEntry` / `MishapEntry` subclasses
- each entry can be inspected without importing string identifiers

### 3. Prune Fake-Career Tests

The fake careers added to decouple `TermEventHandler` tests are useful while the
handler interprets old effects. After handlers dispatch to typed entries, those
tests may become redundant or should be rewritten to test the handler/entry
contract directly.

### 4. Finish `test_scout.py` Classification

After the entry model settles, revisit `test_scout.py`:

- career-rule tests should use `CharacterDriver`
- homeworld and form/pending mechanics should move or stay clearly separated
- remaining `_event`/`_pending` helpers should exist only in mechanics tests

### 5. Coverage Gap Follow-Up

The coverage gaps below are not blockers for the entry-outcome refactor and
should wait unless they become directly relevant:

| Module | Issue |
| --- | --- |
| `character/report.py` | Typst/PDF rendering paths essentially untested |
| `character/domain/homeworld/homeworld_events.py` | `input_specs` branch paths |
| `character/domain/life_events.py` | several outcome paths |
| `character/domain/psionics.py` | psionics edge paths |
| `character/mechanism/store.py` | serialization/deserialization edge paths |
| `character/mechanism/pending_input.py` | abstract/base branch paths |
| `character/web/routes.py` | route error paths |

## Work That Should Not Be Done Now

- Do not create broad permanent tests for every current `*Effect` class.
- Do not force every career test through low-level event chains just because
  typed entries are not implemented yet.
- Do not delete `test_career_class.py` before the entry refactor gives us a
  better structural smoke test.
- Do not build custom approval tooling before trying `inline-snapshot` and
  Syrupy.
- Do not mix entry-class internals into career-rule tests.

## Success Criteria

Before the entry-outcome refactor:

- misclassified tests are reduced
- obvious career-rule tests use `CharacterDriver`
- transitional effect tests pin behavior without endorsing the old design

During the refactor:

- each new projection verb has focused tests
- each shared entry class has focused tests
- old effect tests disappear as replacement entry/projection tests appear

After the refactor:

- tests no longer preserve the old `effects=[...]` model
- career tests assert observable behavior only
- mechanics tests are in mechanics files
- complex multi-effect rows use the chosen snapshot/approval style where useful
