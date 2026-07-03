# Plan: Code Quality Fixes

## STATUS: NOT STARTED

Small, self-contained fixes that can be implemented directly without structural
rethink. Each is covered by a specific test. Order of implementation does not
matter; they can be done in any sequence.

---

## Fix 1: Basic Training Still Checks `list` After Tuple Refactor

**File:** `src/ceres/character/domain/career/career_data.py:937`

When skill-table alternatives were changed from lists to tuples, one branch was
not updated:

```python
elif not isinstance(entry, (Chars, list)):
```

If a tuple alternative has no unknown choices left, it falls through to
`_apply_initial_training_entry(projection, type(entry))`, which is called with
`tuple` as the argument. This can append `tuple()` to `summary.skills`.

**Fix:**
```python
elif not isinstance(entry, (Chars, tuple)):
```

**Test first:** Write a test where a full-basic-training tuple alternative has
already been satisfied before training is applied. Confirm the test goes red on
the current code, green on the fix.

---

## Fix 2: Injury Severity Has No Impossible-State Guard

**File:** `src/ceres/character/domain/career/career_data.py` — `_queue_injury()`

`_queue_injury()` handles `"normal"`, `"severe"`, and `"from_table"`, but has no
final `else`. Unknown severity silently queues nothing.

**Fix:** Add a final `else` branch that raises `ReplayError`:

```python
else:
    raise ReplayError(f'Unknown injury severity: {severity!r}')
```

**Test first:** Write a test that calls `_queue_injury()` with an unknown
severity string and confirms `ReplayError` is raised.

---

## Fix 3: Service Catalogue Conflates Missing Character With Global Context

**File:** `src/ceres/character/service.py:67`

`available_careers()` and `available_precareers()` take an optional
`character_id`. When a `character_id` is provided but no projection is found,
they silently fall back to global context — the same result as calling with no
`character_id`. This hides bad caller state.

**Fix:** When `character_id` is provided but the projection is `None` (or the
summary is `None`), raise `ValueError` (or return an appropriate error response)
rather than silently treating it as a global context call. The two cases are
semantically different.

The same pattern applies to `available_sophonts()` if it has the same
conflation.

**Test first:** Write a test that calls `available_careers(character_id=9999)`
with a non-existent character and confirms that it raises rather than silently
returning the global catalogue.

---

## Fix 4: `remaining_grad` Horror in `PreCareerEventHandler`

**File:** `src/ceres/character/domain/precareer/precareer_events.py:166`

The current pattern builds a list copy then calls `remove()` in a loop:

```python
remaining_grad = [p for p in projection.pending_inputs if isinstance(p, PendingPreCareerGraduation)]
for p in remaining_grad:
    projection.pending_inputs.remove(p)
```

This is O(n²) and relies on `remove()` finding by equality. Replace with a
single in-place filter:

```python
projection.pending_inputs[:] = [
    p for p in projection.pending_inputs
    if not isinstance(p, PendingPreCareerGraduation)
]
```

This fix is mechanical and should not change observable behaviour. Check that
existing pre-career tests still pass after the change.

Note: once the pending input queue API (see
[plan-pending-input-queue-api.md](plan-pending-input-queue-api.md)) is
implemented, this direct mutation of `pending_inputs` will need to change too —
the list will become a private `_pending_inputs`. Consider batching the two
changes.

---

## Fix 5: Convert Empty List Literals to Tuples

Throughout the codebase, empty return values `[]` in skill-table and similar
contexts should be `()` to be consistent with the tuple-based alternatives that
were introduced. This is a cosmetic but hygiene change: it removes the implicit
claim that the result is mutable and keeps types uniform.

**Approach:** `grep` for `return \[\]` in `src/ceres/character/domain/career/`
and convert appropriate instances to `return ()`. Do not convert cases where the
caller genuinely expects a mutable list.

Audit the known consumer types:
- `_skill_table_item_choices()` — returns choices for a single entry
- `_apply_skill_table_entry()` — does not return, but related filtering logic

This is low risk. If `uvx ruff check` is clean afterwards, the change is done.
