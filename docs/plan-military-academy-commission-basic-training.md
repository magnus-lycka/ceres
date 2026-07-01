# Plan: Fix Basic Training Repetition (RIC-009, RIC-010, Career Re-entry)

## Goal

Three scenarios currently give basic training when they should not. The rule
interpretations are already recorded in `RULE_INTERPRETATIONS.md`. This plan
describes a TDD approach to drive out the fixes one scenario at a time.

## Scenarios

1. **RIC-009** — Military academy graduate entering the tied career should not
   receive basic training again (they already received service skills during the
   academy precareer).

2. **Career re-entry** — Re-entering a career that was previously served (e.g.
   Scout → Drifter → Scout) should not repeat basic training.

3. **RIC-010** — Switching assignment within Agent, Citizen, Entertainer, or
   Merchant should not trigger basic training for the new assignment.

## Design direction (confirmed, not yet implemented)

**Serialization verified.** `CareerData` instances already serialize via their
`kind` discriminator — `Army()` round-trips as `{"kind": "ARMY_CAREER"}` — so
`list[CareerData]` is a safe Pydantic field type.

**Tracking field.** Add `basic_training_received: list[CareerData]` to
`CharacterSummary` (the persisted state, not the transient
`CharacterProjection`). Membership is tested by `kind`:
`self.kind in [t.kind for t in summary.basic_training_received]`.

**`_apply_basic_training` on the `TermData` hierarchy.** `TermData` is the
common base of both `CareerData` and `PreCareerData`. Define
`_apply_basic_training` there returning `None` — meaning "no basic training
administered." Non-military-academy precareers inherit this no-op.

`MilitaryAcademyPreCareer` overrides it to administer the tied career's basic
training: grant the service skills (what `apply_entry` currently does inline)
and append `self.service_skills_from()` to
`projection.summary.basic_training_received`. The knowledge "Army Academy
provides Army's basic training" already lives in `service_skills_from` on the
academy class — it stays there, and `CareerData` learns nothing new.

`CareerData` overrides it with the simplified logic: if `self.kind` is already
in `basic_training_received`, return `None` (no training, fall through to
`_queue_skill_table_before_survival`); otherwise grant training (full or
limited, per current rules) and append `type(self)()` to the list.

**The bigger pattern.** Every `CareerData.start_new_term()` call currently does
exactly one of: `_apply_basic_training()` (branching on a `grant_all` bool) or
`_queue_skill_table_before_survival()`. This is one concept — the term-start
skill-granting opportunity — expressed as a `bool | None` plan object plus a
separate method rather than one explicit decision. With `basic_training_received`
driving the check inside `_apply_basic_training`, the `_basic_training_plan`
indirection may collapse. That refactor belongs after the tests are green.

These points are direction, not upfront commitments. Tests must be red before
any implementation begins.

## `is_continuation` goes away

`start_new_term` currently takes an `is_continuation: bool` flag that skips
basic training when True. This flag is entirely superseded by
`basic_training_received`: once `CareerData._apply_basic_training` checks
`self.kind in [t.kind for t in summary.basic_training_received]` and returns
`None` (skip) when found, all scenarios are covered. Remove the parameter from
`start_new_term`; update `SwitchAssignmentHandler` and `_start_new_career_term`
to stop passing it.

## Process: one scenario at a time

For each scenario:

1. Write a failing test using `CharacterDriver` in the appropriate test file.
2. Confirm it is red.
3. Make the minimal change to turn it green without breaking anything else.
4. Run the full suite.
5. Refactor if a cleaner pattern has emerged.

## Starting point: RIC-009

Test in `tests/unit/character/domain/precareer/test_military_academy.py`:
drive Army Academy graduation → Army career entry and assert no
`PendingInitialTrainingChoice` is produced; assert `PendingSkillTable` instead.

## Career re-entry

Test in `tests/unit/character/domain/career/test_scout.py`: drive Scout → one
term → muster out → Drifter → one term → muster out → re-enter Scout. Assert
no `PendingInitialTrainingChoice` on second Scout entry; assert
`PendingSkillTable` instead.

## RIC-010

Test in `tests/unit/character/domain/career/test_citizen.py`: drive Citizen
Worker → one term → muster out → re-enter Citizen Corporate. Assert no
`PendingInitialTrainingChoice` on re-entry; assert `PendingSkillTable` instead.
(Citizen does not use `switch_assignment`; direct re-entry with a different
assignment is the RIC-010 scenario. Under the new design this is fixed by the
same `basic_training_received` check — no special case needed.)

## Refactor step (after all three scenarios are green)

With `is_continuation` gone and `basic_training_received` driving all checks,
consider whether `_basic_training_plan` / `_queue_skill_table_before_survival`
should collapse into a single dispatch inside `_apply_basic_training`. Only do
this once behaviour is locked in by green tests.

## Notes

- Tests use `CharacterDriver` exclusively; use `isinstance` checks on pending
  types, not `kind` string comparisons.
- Expected assertions come from the rules and `RULE_INTERPRETATIONS.md`, not
  from the current implementation.
- If a fix for one scenario accidentally covers another, confirm with a test
  before claiming credit.
