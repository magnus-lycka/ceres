# Plan: Pending Input Queue API

## STATUS: NOT STARTED

## Background

The current convention for queuing pending inputs in `CharacterProjection` is:

- `projection.pending_inputs.insert(0, pending)` — resolve this next (immediate)
- `projection.pending_inputs.append(pending)` — resolve this after existing queue (deferred)

This rule is simple and valuable, but raw list operations have two problems:

1. **Intent is implicit.** A reader must know the convention to understand
   whether `insert(0, ...)` or `append(...)` is correct at any given call site.
2. **Multi-input ordering is fragile.** When several pending inputs must be
   queued immediately and in caller order, callers must either iterate in reverse
   and insert each at 0, or use a slice assignment — both of which are easy to
   get wrong.

The grouped-connection-rolls bug (`RolledConnectionsGroupEntry.apply()`) is a
concrete example of the second problem: iterating `reversed(self.rolls)` and
inserting at 0 preserves visible order but scrambles `pending_idx` values.

This plan adds a small API that keeps the current mental model while removing
the fragile list operations.

---

## Step 1: Add `queue_immediate` and `queue_deferred` to `CharacterProjection`

**File:** `src/ceres/character/domain/character_state.py`

Add two methods to `CharacterProjection`:

```python
def queue_immediate(self, *pending_inputs: PendingInput) -> None:
    self._pending_inputs[:0] = pending_inputs

def queue_deferred(self, *pending_inputs: PendingInput) -> None:
    self._pending_inputs.extend(pending_inputs)
```

- `queue_immediate(first, second)` inserts both at the front in caller order:
  `first` resolves before `second`, and both resolve before anything already in
  the queue.
- `queue_deferred(first, second)` appends both in caller order: they resolve
  after anything already in the queue.

**Test first:** Write unit tests for both methods confirming that caller order is
preserved and that immediate inputs resolve before deferred inputs.

---

## Step 2: Make `pending_inputs` Private With a Read-Only Property

`pending_inputs` is currently a public list field. Once the queue methods exist,
direct mutation of the list is an antipattern that bypasses the convention.

**Changes:**
1. Rename `pending_inputs: list[PendingInput]` to `_pending_inputs: list[PendingInput]`
   (Pydantic private field or excluded field).
2. Add a read-only property `pending_inputs` that returns a view or copy so that
   callers outside the class can still inspect the queue.

```python
@property
def pending_inputs(self) -> tuple[PendingInput, ...]:
    return tuple(self._pending_inputs)
```

This breaks all direct mutation call sites (including `remove()`, `insert()`,
`append()`, slice assignment) and forces callers to use the new methods. The
compile-time signal from ty will identify every site that needs updating.

Note: `projection.pending_inputs[:] = [...]` patterns (including the
`remaining_grad` fix in `precareer_events.py`) will need a replacement. If
removing all pending inputs of a type is a recurring pattern, consider adding a
method like `projection.drop_pending(predicate)` or `projection.cancel_pending(type)`.

**Do this step after all call sites are migrated**, not before — otherwise ty
will report errors before they are fixed.

---

## Step 3: Replace All `insert(0, ...)` and `append(...)` Call Sites

Migrate every production call site to use the new methods. Use `uvx ruff check`
and `uvx ty check` as signals that migration is complete.

Patterns to replace:

| Old | New |
|-----|-----|
| `projection.pending_inputs.insert(0, p)` | `projection.queue_immediate(p)` |
| `projection.pending_inputs.append(p)` | `projection.queue_deferred(p)` |
| `projection.pending_inputs.insert(0, a); projection.pending_inputs.insert(0, b)` | `projection.queue_immediate(b, a)` (reverse order kept, or…) |
| `projection.pending_inputs[:0] = [a, b]` | `projection.queue_immediate(a, b)` |

The multi-input reverse-insert pattern above is a known source of bugs. The
`*args` form makes caller order unambiguous.

---

## Step 4: Fix Grouped Connection Rolls

**File:** `src/ceres/character/domain/career/career_data.py` —
`RolledConnectionsGroupEntry.apply()`

The current implementation:

```python
for roll in reversed(self.rolls):
    pending = PendingConnectionRoll(pending_id=(event.id, pending_idx), ...)
    projection.pending_inputs.insert(0, pending)
    pending_idx += 1
```

Iterating in reverse and inserting at 0 achieves the right visible order, but
the `pending_id` values are assigned in reverse, so the first visible pending
input gets the highest `pending_idx`. This is confusing in tests and traces.

After Step 1 and Step 3, rewrite to iterate in forward order and call
`queue_immediate` with all pending inputs at once:

```python
pending_inputs = [
    PendingConnectionRoll(pending_id=(event.id, pending_idx + i), ...)
    for i, roll in enumerate(self.rolls)
]
projection.queue_immediate(*pending_inputs)
pending_idx += len(self.rolls)
```

**Test:** The existing weakened test that checks set-like shape should be
strengthened to assert exact `pending_id` ordering matching caller order.

---

## Step 5: Handle Direct-Mutation Removal Patterns

Sites that currently mutate `pending_inputs` to remove items (like the
`remaining_grad` pattern) need a replacement once the list is private.

Options:
- `projection.cancel_pending(predicate)` — drops all items matching a predicate
- `projection.cancel_pending_of_type(SomeType)` — type-specific convenience

Evaluate how many distinct removal patterns exist before committing to a name.
The key constraint is that the caller should not need direct list access to
remove something it previously queued.

---

## Step 6: Update Documentation and Follow-Up Notes

Once the queue API is implemented and production call sites have migrated,
update docs that currently describe raw list mutation as the architectural rule.

Required updates:

- `docs/concepts/character-creation-architecture.md` — replace the current
  `append(item)` / `insert(0, item)` guidance with
  `projection.queue_deferred(...)` / `projection.queue_immediate(...)`. It may
  mention the underlying list implementation briefly, but the documented API
  should be the projection methods.
- `docs/todo_maybe.md` — remove or update the transitional note that says
  `insert(0, ...)` is the current implementation. Future todo items should tell
  implementers to use `queue_immediate(...)` for mid-flow pending inputs and
  `queue_deferred(...)` for tail-of-flow pending inputs.
- Any active plan that still instructs new work to call
  `projection.pending_inputs.insert(0, ...)` or `.append(...)` directly should
  be updated to use the queue API.

This step is part of completing the queue API. Do not archive this plan while
architecture or todo docs still teach direct `pending_inputs` mutation as the
normal pattern.
