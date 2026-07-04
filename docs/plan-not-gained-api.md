# Plan: Visible No-Ops and Silent-Drop Policy

## STATUS: NOT STARTED

## Background

Projection diffs record what changed. They do not record what was considered
and intentionally did not change. In character creation, many "nothing changed"
cases are meaningful:

- A basic training skill was already present from background skills.
- A rank benefit gives a skill the character already has at the same or higher level.
- A psionic talent skill is rolled, but the character does not have PSI.
- A tuple of alternatives shrinks to no available choices after filtering.

In all these cases the character builder and the test author need to know whether
a no-op was intentional. Currently the domain is silent about it.

### Empty Tuples vs Unhandled Values

An empty tuple can be a valid, deliberate outcome — "there are no applicable
choices left". The bug pattern is different: a non-empty value reaches a handler,
the handler does not know what to do with it, and the code silently drops it.

**Proposed policy:**

| Situation | Action |
|-----------|--------|
| Tuple/result filtered to empty after processing concrete entries | Record each rejected entry with `not_gained(entry)`, then no-op |
| Known non-empty entry that cannot improve the character | Call `projection.not_gained(entry)` |
| Non-empty entry with no valid handler in this context | Raise `ReplayError` |

This plan implements the `not_gained` API and applies the policy to all known
drop-without-recording sites.

---

## Step 1: Add `not_gained()` to `CharacterProjection`

**File:** `src/ceres/character/domain/character_state.py`

```python
def not_gained(self, entry: AnySkill | PsionicTalentSkillModels | Chars) -> None:
    self._not_gained.append(entry)
```

Where `_not_gained` is a private list (or tuple accumulator). Expose it as a
read-only property. The property name and type should be chosen to make the
intent clear in test assertions:

```python
@property
def not_gained_entries(self) -> tuple[AnySkill | PsionicTalentSkillModels | Chars, ...]:
    return tuple(self._not_gained)
```

The type parameter of `not_gained()` should cover all the **concrete,
player-facing** things that can be considered but not applied:

- `AnySkill` — a concrete skill instance, including psionic talent skills like
  `Telepathy()`
- `Chars` — a characteristic modifier

`not_gained()` records what the player would see, not the table encoding.
When a skill table entry is `Psi(talent=Telepathy())` and the character cannot
gain it, record `Telepathy()` — the concrete skill — not the `Psi(...)` wrapper.
The `Psi` wrapper is a table-layer encoding detail; `Telepathy()` is what the
player lost. `PsionicTalentSkillModels` already covers the talent skill types
that can appear in `AnySkill`; no separate `Psi` case is needed in the union.

**Test first:** Write a unit test confirming that `not_gained(Admin())` appends
the entry to `not_gained_entries` and that the property is read-only.

---

## Step 2: Fix `build_skill_select_options()` Parseable-Chars Issue

**File:** `src/ceres/character/domain/skill_events.py:39`

`build_skill_select_options()` can render `Chars` as select options, but the
form submit paths validate submitted values as skill, psi, or advancement-DM
choices only. If `Chars` can reach a pending-choice form, the submit path is
incomplete and will fail.

Decide: should `Chars` be reachable from skill-table choice forms, or should it
be handled upstream (before a choice form is created)?

If `Chars` **should** be selectable in a choice form:
- Extend `event_from_form()` for `PendingSkillTableChoice` to parse `Chars`
  option values.
- Add a test submitting a `Chars` option and confirming the characteristic is
  applied.

If `Chars` **should not** be selectable:
- Narrow the type in `build_skill_select_options()` to exclude `Chars`.
- `_skill_table_item_choices()` should not include `Chars` options, since
  characteristic gains are not player-choice — they are automatic.
- Add a test confirming that a `Chars` entry in a skill table is applied
  immediately (not added to choices).

The current behaviour in `_apply_skill_table_entry()` for `Chars` entries is:

```python
if isinstance(entry, Chars):
    projection.summary.apply_characteristic_change(entry, 1)
```

This is an immediate application (no choice). Confirm that `Chars` never ends up
in `_skill_table_item_choices()` and, if it does, remove it from that path.

---

## Step 3: Apply the Policy to Known Drop-Without-Recording Sites

Once `not_gained()` exists, audit the known silent-drop sites and apply the
policy:

1. **`_apply_skill_table_entry()` — `Psi` for character without PSI:**
   Call `projection.not_gained(entry)` (see also
   [plan-psionic-skill-table.md](plan-psionic-skill-table.md)).

2. **`_apply_skill_table_entry()` — `Chars` already at cap, or similar:**
   If a characteristic cannot be improved (e.g., already at max), call
   `projection.not_gained(entry)`.

3. **Basic training already-known-skill:**
   When a basic training entry is skipped because the character already has the
   skill at a sufficient level, call `projection.not_gained(entry)`.

4. **Rank bonus already-known-skill:**
   When a rank bonus skill is not applied because the character already has it at
   the required level, call `projection.not_gained(entry)`.

For each site: write a test asserting that `not_gained_entries` contains the
expected entry after the no-op, then apply the call.

---

## Step 4: Apply the `ReplayError` Policy to Unknown Entries

Any non-empty entry that reaches a handler branch with no matching `isinstance`
check should raise `ReplayError`. This prevents silent corruption from future
type changes or bad serialised data.

**Pattern:**
```python
else:
    raise ReplayError(f'Unhandled skill table entry: {entry!r}')
```

This is a defensive measure. It does not change behaviour for valid inputs.
Add after confirming that all legitimate types are handled.

---

## Relationship to Other Plans

- `not_gained()` is referenced as a TODO in
  [plan-psionic-skill-table.md](plan-psionic-skill-table.md). Implement
  `not_gained()` first so the psionic plan can use it immediately.
- The `Chars` parseable issue in Step 2 interacts with
  [plan-characteristic-type.md](plan-characteristic-type.md). If `Chars` becomes
  a richer type, the rendering and parsing logic may change. Consider doing Step
  2 after the characteristic type plan is resolved, or at least cross-checking.
