# Plan: Psionic Skill Table Entries

## STATUS: PARTIALLY COMPLETE — Steps 1 and 4 done; Step 2 partially done; Step 3 pending

### What was completed

- **Step 1**: `on_psi_chosen` comment added.
- **Step 2 (partial)**: `_apply_skill_table_entry()` fixed for all three Psi
  cases (no PSI → `not_gained`, possessed → increment, has PSI but not talent →
  queue `PendingPsionicInstituteTraining`). However, `Psion.skill_table_option_is_available`
  returns `True` for Psi entries on service_skills (possessed and unlearned alike),
  which routes them through `PendingSkillTableChoice.on_psi_chosen` = `pass` —
  bypassing `_apply_skill_table_entry` entirely. The remaining fix: return `False`
  from `skill_table_option_is_available` for all Psi entries on service_skills.
  Tracked in `docs/todo_maybe.md`.
- **Step 4**: `todo_maybe.md` updated with correct current interpretation.

## Background

### The Rule

From `refs/core/10_psionics.md`, line 86:

> When rolling on the Service Skills table, if the Psion gains the skill for a
> talent they do not yet possess, they may attempt another roll to learn that
> talent.

This means: if a character rolls a psionic talent skill entry on the service
skill table and they do not already have that talent, they are not simply
out of luck — they get another roll to acquire the talent. That roll uses the
same talent-acquisition mechanic as the pre-career psionic institute, with the
cumulative talent-roll penalty applied.

### Current Code Behaviour

`_apply_skill_table_entry()` in `career_events.py` handles a `Psi` entry:

```python
elif isinstance(entry, Psi):
    psionics = projection.summary.psionics
    if psionics is not None and psionics.talent_level(type(entry.talent)) is not None:
        psionics.increment_talent(type(entry.talent))
```

If `psionics` is `None` (character has no psionic ability at all) or the
character does not yet have the specific talent, the code silently does nothing.

The silence is wrong for the case where the character has `psionics` (has gone
through the psionic institute) but does not yet have this particular talent. In
that case, the rule requires a talent acquisition attempt.

### Why `PendingSkillTableChoice.on_psi_chosen()` Is Correctly a No-Op

`_apply_promotion()` in `advancement.py` pre-queues both `PendingSkillTable`
and `queue_reenlist_or_aging()` before the skill table choice is resolved:

```
queue: [PendingSkillTable(0), PendingReenlist(1)]
```

When `PendingSkillTable` fires, if there are multiple choices it inserts
`PendingSkillTableChoice` at the front:

```
queue: [PendingSkillTableChoice(0,0), PendingReenlist(1)]
```

After `PendingSkillTableChoice` resolves (via `SkillChoiceHandler` or
`PsionicTalentTrainingHandler`), `PendingReenlist` is already in the queue —
no continuation is needed from within `on_psi_chosen`. The `pass` is intentional
and should be documented with a comment.

---

## Step 1: Document the No-Op With a Comment

**File:** `src/ceres/character/domain/career/career_events.py` —
`PendingSkillTableChoice.on_psi_chosen()`

Add a brief comment explaining that reenlist/aging is already in the queue before
this choice is resolved, so no continuation is needed:

```python
def on_psi_chosen(self) -> None:
    # Reenlist/aging is pre-queued by _apply_promotion() before the skill
    # table choice fires. No continuation needed here.
    pass
```

This is a one-line change and does not require a test.

---

## Step 2: Fix `_apply_skill_table_entry()` for Unowned Talents

**File:** `src/ceres/character/domain/career/career_events.py` —
`_apply_skill_table_entry()`

When a `Psi` entry reaches this function and the character:
- has `psionics` (has been through the psionic institute and has a PSI
  characteristic), AND
- does not yet have the specific talent

...the character should attempt to acquire the talent.

The talent acquisition attempt is already modelled by `PsionicTalentTrainingHandler`
(in `psionics.py`). Queueing a pending input that uses this handler for the
relevant talent is the right response.

When `psionics` is `None` entirely (character has never undergone psionic
testing), the entry is a no-op. Record this with `projection.not_gained(entry)`
once that API exists (see [plan-not-gained-api.md](plan-not-gained-api.md)).

**Fix outline:**

```python
elif isinstance(entry, Psi):
    psionics = projection.summary.psionics
    if psionics is None:
        # Character has no PSI characteristic; talent skill cannot be applied.
        # projection.not_gained(entry)  # TODO: once not_gained API exists
        return
    if psionics.talent_level(type(entry.talent)) is not None:
        psionics.increment_talent(type(entry.talent))
    else:
        # Character has PSI but not this talent; per core rules p.86, they
        # may attempt another roll to learn the talent.
        projection.queue_immediate(
            PendingPsionicTalentAcquisition(
                pending_id=...,
                instruction='Roll to acquire psionic talent',
                talent=type(entry.talent),
            )
        )
```

The exact pending type name and its handler need to be verified against the
existing psionic talent acquisition flow in `psionics.py`. The key is that the
same `PsionicTalentTrainingHandler` used in pre-career psionic testing should be
reused here, with the cumulative penalty applied from `psionics.talent_count`.

**Test first:** Write a test where a Psion character (has `psionics` but not
Telepathy) rolls Telepathy on the service skill table. Confirm that a talent
acquisition pending input is queued. Run red on the current code, green on the
fix.

---

## Step 3: Confirm `PendingInitialTrainingChoice.on_psi_chosen()` Is Also Correct

`PendingInitialTrainingChoice.on_psi_chosen()` is also a `pass`. Verify that
during basic training the next pending input in the queue (either another
training choice or the survive pending) is already present, making the no-op
correct. Add a comment if confirmed. If not correct, fix accordingly.

---

## Step 4: Reconcile `todo_maybe.md`

`docs/todo_maybe.md` currently describes
`PendingSkillTableChoice.on_psi_chosen()` as a bug because it is `pass` and says
it should increment the talent. This plan's analysis says the opposite: the
`pass` is intentional for continuation ordering, and the real bug is the
unowned-talent service-skill-table path.

When this plan is implemented:

- update the "Psion skill table: incomplete Psi talent handling" item in
  `docs/todo_maybe.md`;
- remove or rewrite the claim that `PendingSkillTableChoice.on_psi_chosen()`
  should increment the talent directly;
- point the todo at the implemented service-skill-table talent-acquisition
  behaviour, or move the todo to `docs/archive/done_todos.md` if fully
  resolved.

Do not archive this plan while `todo_maybe.md` still teaches the old
interpretation.

---

## Notes on Psionic Talent Skill Entries in Service Tables

A psionic talent skill entry in a service table is represented as `Psi(talent)`.
There is no `Psi.TELEPATHY` domain value. `Telepathy()` is a skill class and
`Psi(talent=Telepathy())` is how the table entry is encoded.

The `skill_table_option_is_available()` check for `Psi` entries determines
whether the entry appears as a selectable option in a multi-choice context.
In a single-entry context (no choice), the entry goes directly to
`_apply_skill_table_entry()`. The two paths need to handle the unowned-talent
case consistently.
