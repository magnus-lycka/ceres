# Plan: Fix Basic Training Repetition and Pending Input Ordering

## STATUS: COMPLETE

## Background

This plan began as a fix for three basic-training-repetition bugs (RIC-009,
RIC-010, career re-entry). During that work we changed `start_new_term` so that
survival is always pre-queued last. That architectural change — pre-queuing
survival — exposed a systemic bug: every other pending input added during a term
also needs to respect queue position. Phase 2 is the full application of the new
ordering principle throughout the codebase.

---

## Phase 1 — Basic Training Repetition (COMPLETE)

### Goal

Three scenarios give basic training when they should not:

1. **RIC-009** — Military Academy graduate entering the tied career should not
   receive basic training again.
2. **Career re-entry** — Re-entering a previously served career (Scout → Drifter
   → Scout) should not repeat basic training.
3. **RIC-010** — Switching assignment within Agent, Citizen, Entertainer, or
   Merchant should not trigger basic training for the new assignment.

### What was done

**`basic_training_received`** was added to `CharacterSummary` as a
`list[CareerData]` tracked by `kind`. Membership check:
`self.kind in [t.kind for t in summary.basic_training_received]`.

**`is_continuation`** parameter was removed from `start_new_term`.
`SwitchAssignmentHandler` and `_start_new_career_term` no longer pass it.
`_apply_basic_training` now checks `basic_training_received` instead.

**`start_new_term` ordering** was changed: training-related pending inputs
(initial training choice, skill-table, rank-bonus) are appended in order first;
survival is always appended last, using index `max(used, default=-1) + 1`. This
is the architectural change that Phase 2 builds on.

**`MilitaryAcademyPreCareer.apply_entry` — Phase 1 regression.** The correct
implementation calls `career._apply_basic_training()`, which creates
`PendingInitialTrainingChoice` for list entries like `[Drive(), VaccSuit()]`.
Phase 1 broke this: to stop Army Academy approval tests failing after the queue
ordering change, `apply_entry` was changed to iterate the table manually and
skip list entries entirely. This silenced the test failures but violated the
rules — the player should choose Drive or VaccSuit during Army Academy entry.

This regression must be fixed (with a failing test written first):

1. Write a unit test asserting that `PendingInitialTrainingChoice` is produced
   with Drive and VaccSuit as options during Army Academy entry — confirm red.
2. Restore `apply_entry` to call `career._apply_basic_training(projection,
   assignment, training.table_name, training.grant_all, event.id)` and return
   `pending_idx + (pending inputs added by that call)`.
3. Update the three Army Academy approval tests in `test_precareers.py` to
   submit `skill_form(Drive())` (or VaccSuit) before the event and graduation
   roll forms, then regenerate their snapshots.

**Nine failing approval tests** were fixed by swapping form submission order.
After the ordering change, `PendingRankBonusChoice` (rank 0 bonus) is at queue
position 0 before `PendingSurvive`, so `skill_form(...)` must be submitted
before `roll_form(...)` for the survival roll. Six approval snapshots were
regenerated with `--snapshot-update`.

---

## Phase 2 — Pending Input Ordering Throughout the Codebase (COMPLETE)

### Completed in Phase 2

All of the `append` → `insert(0, ...)` fixes in `career_data.py` entry classes
were applied: `_queue_injury()`, `CharacteristicLossChoiceEntry`,
`RolledConnectionsEntry`, `SkillChoiceEntry`, `RollMishapEntry`,
`LifeEventEntry`, `GainConnectionAndSkillChoiceEntry`,
`GainConnectionsAndSkillChoiceEntry` — all now use `insert(0, ...)`.

In `career_events.py`: `SkillTableHandler.apply()` no longer contains
`reenlist_queued` detection or survival-appending logic;
`PendingSkillTableChoice.reenlist_queued` was removed;
`PendingRankBonusChoice._continue()` now uses `insert(0, ...)` for
`PendingSkillTable` and calls `queue_reenlist_or_aging` with index 1.

The Phase 1 regression in `MilitaryAcademyPreCareer.apply_entry` was fixed:
it now calls `career._apply_basic_training()` and produces
`PendingInitialTrainingChoice` with Drive/VaccSuit options. The three Army
Academy approval tests were updated to submit `skill_form(Drive())` before the
event and graduation forms. A unit test in `test_military_academy.py` covers
this.

`InjuryAndGainConnectionEntry.apply()` was refactored to delegate to
`_queue_injury()`, eliminating duplicated logic and ensuring `insert(0, ...)`
ordering. Covered by a unit test confirming the injury choice appears before
existing pending inputs.

`RolledConnectionsGroupEntry.apply()` still uses the `reversed()`+`insert(0,
...)` pattern, which scrambles pending IDs. This is now tracked as a separate
item in [plan-pending-input-queue-api.md](plan-pending-input-queue-api.md).

---

### The architectural principle

`CharacterSession.submit` always resolves `pending_inputs[0]` first. There are
exactly two valid strategies for adding a new pending input to the queue:

- **`append`** — the new item goes after everything already queued. Use this
  only for items that belong at the tail of the term flow: `PendingSurvive` (in
  `start_new_term`), `PendingReenlist`, `PendingMusterOut`, `PendingAgingRoll`.
- **`insert(0, ...)`** — the new item goes before everything already queued.
  Use this for any pending input that must be resolved before the current
  tail (survival, reenlist, muster-out). In practice, this is almost every
  pending input arising during event, mishap, or skill-table resolution.

Pre-queuing survival last in `start_new_term` is what makes this work: the
player resolves skill tables, rank bonuses, events, mishap consequences, and
connection rolls before ever reaching the survival roll — each new item is
inserted at position 0, in front of the pre-queued survival.

**Concrete symptom when this is wrong:** pre-career event 6 ("involved in a
tightly knit clique or group") currently appends `PendingConnectionsRoll` after
`PendingPreCareerGraduation`, so the player can only roll for connections *after*
graduation — in the wrong order. The same bug exists for every `append` call
inside a career or pre-career event handler.

### Code locations to fix

Everything below uses `append` where it should use `insert(0, ...)`.

#### `src/ceres/character/domain/career/career_data.py`

| Location | What to change |
|---|---|
| `_queue_injury()` — all three branches (~lines 117, 126, 135) | `append(PendingCharacteristicChoice / PendingInjuryTable)` → `insert(0, ...)` |
| `CharacteristicLossChoiceEntry.apply()` (~line 188) | `append(PendingCharacteristicChoice)` → `insert(0, ...)` |
| `RolledConnectionsEntry.apply()` (~line 221) | `append(PendingConnectionsRoll)` → `insert(0, ...)` |
| `RolledConnectionsGroupEntry.apply()` (~lines 244–253) | `append(PendingConnectionsRoll)` for each roll → `insert(0, ...)` (note: if multiple rolls, reverse-insert or build list and insert slice) |
| `SkillChoiceEntry.apply()` (~line 274) | `append(PendingSkillChoice)` → `insert(0, ...)` |
| `RollMishapEntry.apply()` (~line 307) | `append(PendingMishap)` → `insert(0, ...)` |
| `LifeEventEntry.apply()` (~line 324) | `append(PendingLifeEvent)` → `insert(0, ...)` |
| `GainConnectionAndSkillChoiceEntry.apply()` (~line 402) | `append(PendingSkillChoice)` → `insert(0, ...)` |
| `GainConnectionsAndSkillChoiceEntry.apply()` (~line 429) | `append(PendingSkillChoice)` → `insert(0, ...)` |

`InjuryEntry.apply()` delegates to `_queue_injury`, so fixing `_queue_injury`
covers it. `InjuryAndGainConnectionEntry` likewise; check whether it calls
`_queue_injury` or appends directly.

#### `src/ceres/character/domain/career/career_events.py`

| Location | What to change |
|---|---|
| `SkillTableHandler.apply()` (~lines 285–323): `reenlist_queued` detection and index-search insertion | Delete the `survival_already_queued` / `reenlist_queued` detection block. Delete the `next(...)` index search. Replace with `insert(0, new_pending)` unconditionally. |
| `SkillTableHandler.apply()` (~lines 320–323): survival appended when no choice needed | Delete these `append(_survive_pending(...))` calls — survival is pre-queued by `start_new_term`. |
| `PendingSkillTableChoice.reenlist_queued: bool` (~line 754) | Remove the field entirely (Alpha: no migration). |
| `PendingSkillTableChoice.on_skill_chosen()` (~lines 759–763) | Remove the `if ... not self.reenlist_queued: ... append(_survive_pending(...))` block. |
| `PendingSkillTableChoice.on_psi_chosen()` (~lines 765–768) | Same: remove survival-appending. |
| `PendingRankBonusChoice._continue()` (~line 794): `append(PendingSkillTable)` | Change to `insert(0, PendingSkillTable(...))` so the term skill table comes before survival. |

#### Pre-career event handlers

Pre-career events live in
`src/ceres/character/domain/precareer/precareer_events.py` and use
`PreCareerEventHandler` subclasses. Scan every `apply` method in that file
for `append`. In particular:

- `RolledConnectionsEntry` (or equivalent) in the pre-career event data must
  use `insert(0, ...)` to place connection rolls before graduation.
- `PreCareerEventHandler` for event 6 specifically queues connections AFTER
  `PendingPreCareerGraduation` — this is the known-broken case.

### Process: one location at a time (TDD)

For each fix location, using the three-step loop:

1. **Write a failing test** that exercises the broken ordering. Use
   `CharacterDriver` for career-rule tests (which pending the player sees and
   in what order). Reference `tests/unit/character/helpers.py`. For precareer
   ordering, use the approval test or a focused unit test.
2. **Confirm red.** The test must fail before touching production code.
3. **Make the minimal change** — swap `append` to `insert(0, ...)`, delete the
   now-unnecessary survivor-appending or index-search logic.
4. **Run `uv run pytest`** — confirm no regressions.
5. **Clean up**: if the fix eliminates `reenlist_queued` or other now-dead
   state, remove it (Alpha: no migration).

### Ordering for multiple inserts in one event

When a single event handler needs to queue two pending inputs and both must
happen before survival, insert them in reverse order so the first-to-resolve
ends up at index 0:

```python
projection.pending_inputs.insert(0, second_thing)  # goes to position 1 after next insert
projection.pending_inputs.insert(0, first_thing)  # at position 0 — resolved first
```

Or build a list and use `pending_inputs[0:0] = [first, second]`.

---

## Coordination with todo_maybe.md

Several items in `docs/todo_maybe.md` directly overlap with Phase 2 work. When
implementing a career-tables todo (Agent, Army, Citizen, Drifter, Entertainer,
Marines, Merchant, Navy, Noble, Prisoner, Rogue, Scholar, Scout), any new
pending input introduced for that career must use `insert(0, ...)` — not
`append`. Do not defer the ordering fix as a separate cleanup step; apply it
correctly from the start.

Specific `todo_maybe.md` items affected by Phase 2 ordering work:

- **"Generic Pre-Career Events table must match Core literally"** — pre-career
  event 6 is already broken by ordering. Events that trigger connections, life
  events, or skill rolls (e.g. 7, 9) may also be affected. Fix ordering before
  or alongside fixing pre-career event text/behavior.
- **Military Academy pre-career** — Phase 1 fixed RIC-009 (no repeated basic
  training). Remaining gaps (Drive/VaccSuit list entry choice, three-level-1
  service skills on graduation, commission DM lifetime) are separate from the
  ordering work but commission rolls will need `insert(0, ...)` if they add
  pending inputs.
- **All career-tables todos** — every pending input added when working through
  these must use `insert(0, ...)`. This is a gate condition: do not land a
  career-tables PR that uses `append` for mid-event pending inputs.

---

## Notes

- Tests use `CharacterDriver` exclusively for career-rule tests. Do not import
  `PendingSurvive`, `PendingRankBonusChoice`, or other event-layer types in
  career-rule tests.
- Expected assertions come from the rules and `RULE_INTERPRETATIONS.md`, not
  from the current implementation.
- `reenlist_queued` on `PendingSkillTableChoice` was an approximation of the
  new ordering invariant — it tried to detect whether survival was queued rather
  than guaranteeing position. Once Phase 2 is done, delete the field and all
  code that sets or reads it.
- Alpha policy: remove `reenlist_queued` from the Pydantic model without any
  migration or compatibility shim.
