# Character Code Findings

These notes collect observations from the recent career/pre-career and pending-input work. They are not a replacement for the implementation plans; they are a focused list of code smells, rule clarifications, and small abstractions that should make the next work easier to reason about.

## Review Findings From Recent Changes

### High: Basic Training Still Checks `list` After Tuple Refactor

`src/ceres/character/domain/career/career_data.py:937`

`CareerData._apply_basic_training()` was updated to use tuples for skill-table alternatives, but one branch still checks for `list`:

```python
elif not isinstance(entry, (Chars, list)):
```

In full basic training, if a tuple alternative has no unknown choices left, it falls through to `_apply_initial_training_entry(projection, type(entry))`, where `type(entry)` is `tuple`.

That can append `tuple()` to `summary.skills` or otherwise treat `tuple` as a skill class. This is a real regression from the list-to-tuple refactor.

Expected fix:

```python
elif not isinstance(entry, (Chars, tuple)):
```

This should be covered by a test where a full-basic-training tuple alternative has already been satisfied before training is applied.

### Medium: Grouped Connection Rolls Preserve Visible Order But Scramble Pending IDs

`src/ceres/character/domain/career/career_data.py:249`

`RolledConnectionsGroupEntry.apply()` currently loops through `reversed(self.rolls)` and inserts each pending input at index 0. That preserves visible resolution order, but the `pending_idx` values are assigned while iterating in reverse.

The result is that the first visible pending input can have a later logical meaning but an earlier/later id than expected. This makes tests and replay traces harder to reason about.

The test was weakened to assert a set-like shape rather than exact pending id/order. That hides the smell rather than resolving it.

Prefer an API such as `projection.queue_immediate(first, second)` that can insert a batch while preserving both visible order and pending-id assignment.

### Medium: Raw `insert(0, ...)` Is Correct But Too Easy To Misuse

The new queue convention is:

- `insert(0, pending)` means "resolve this immediately".
- `append(pending)` means "defer this".

That rule is simple and valuable, but raw list operations make intent implicit. They also require every caller that queues several inputs to remember reverse insertion or slice mechanics.

This is the broader cause behind the grouped-connection issue above.

Prefer projection-level methods:

```python
projection.queue_immediate(pending)
projection.queue_deferred(pending)
projection.queue_immediate(first, second)
```

The multi-item form should preserve caller order.

### Medium: Psionic Skill Table Entries Can Become Silent No-Ops

`src/ceres/character/domain/career/career_events.py:425`

`_apply_skill_table_entry()` increments a psionic talent only if psionics exists and the character already has the talent:

```python
elif isinstance(entry, Psi):
    psionics = projection.summary.psionics
    if psionics is not None and psionics.talent_level(type(entry.talent)) is not None:
        psionics.increment_talent(type(entry.talent))
```

If the character lacks psionics or lacks the talent, this silently does nothing.

For the Psion career, the character gets a chance to test talents before the first term. Later, if a psionic talent skill is rolled on the service skill table, they may test talents again with the cumulative talent-roll penalty. They can only gain skill level if they have the talent.

So this path should not silently vanish. Depending on context, it should either route to the talent-testing mechanic, record that the concrete talent skill was not gained, or raise `ReplayError` if the handler is being used in an invalid state.

There is no `Psi.TELEPATHY` domain value; `Telepathy()` is a skill.

### Medium: `PendingSkillTableChoice.on_psi_chosen()` Is Ambiguous

`src/ceres/character/domain/career/career_events.py:735`

`PendingSkillTableChoice.on_psi_chosen()` is currently a no-op. That may be correct if psionic talent training already applies the talent result before calling the hook and skill-table continuation is now pre-queued.

But the surrounding TODO/history makes this ambiguous. The code should either document why no continuation is needed, or the flow should be adjusted so choosing a psionic option visibly completes the skill-table choice.

### Medium: Injury Severity Has No Impossible-State Guard

`src/ceres/character/domain/career/career_data.py:108`

`_queue_injury()` handles `normal`, `severe`, and `from_table`, but has no final `else`.

The type is narrow, but replay code should still be defensive against bad persisted data, bad table data, or future refactors. Unknown severity should raise `ReplayError` instead of silently queueing nothing.

### Medium: Characteristic Options May Be Displayable But Not Parseable

`src/ceres/character/domain/skill_events.py:39`

`build_skill_select_options()` can now render `Chars` as select options:

```python
if isinstance(option, Chars):
    results.append((f'{option.value} +1', option.value))
```

But the related form paths still validate submitted values as skill, psi, or advancement-DM choices. If `Chars` can reach these pending-choice forms, the submit path is incomplete. If `Chars` should never reach them, the type should be narrowed so ty and readers see that.

### Medium: Service Catalogue Methods Conflate Missing Character With Global Context

`src/ceres/character/service.py:67`

The new `available_sophonts()`, `available_careers()`, and `available_precareers()` methods should distinguish between:

- no `character_id` supplied, meaning catalogue/global context is intended;
- explicit `character_id` supplied but no character/projection/summary found, meaning the caller probably has bad state.

The latter should not accidentally behave like the former without an explicit decision.

### Low: Service Migration Is Incremental, Not Complete

`CharacterService.available_*` is a useful direction, and `web/routes.py` starting to use it is good. But route code still reaches through the service into backend details in several places.

That is not a bug by itself. It is just worth documenting that this is partial migration, not a completed service boundary.

### Low: `SkillTableItem` Broadening Needs Follow-Through

The type alias moved toward `AnySkill | Psi | Chars`, and list alternatives became tuple alternatives. That direction is reasonable, but every consumer needs to be audited for:

- tuple alternatives;
- `Chars`;
- psionic skill/talent entries;
- empty-after-filtering results.

The high-severity basic-training regression is one example of a consumer that was not fully updated.

## Pending Input Queue Intent

The current queue rule is simple and useful:

- `insert(0, pending)` means "resolve this immediately, before already queued pending inputs".
- `append(pending)` means "defer this until after already queued pending inputs".

That simplicity is worth preserving. The problem is that raw list operations make intent implicit and make multi-input ordering easy to get wrong.

Prefer adding a small projection-level API:

```python
projection.queue_immediate(pending)
projection.queue_deferred(pending)
```

For multiple pending inputs, the API should preserve the order in which the caller passes them:

```python
projection.queue_immediate(first, second)
```

should resolve `first` before `second`, without every caller needing to remember reverse insertion or slice assignment.

This would keep the current mental model while making the code grep-able and reducing fragile `insert(0, ...)` / `reversed(...)` patterns.

## Valid No-Ops Should Be Visible

Projection diffs are good at showing what changed. They are weak at showing what was considered and intentionally did not change.

That matters in character creation because many "nothing changed" cases are meaningful:

- A basic training skill was already present from background skills.
- A rank benefit gives a skill the character already has at the same or higher level.
- A psionic talent skill is rolled, but the character does not have the talent.
- A tuple of alternatives shrinks to no available choices after filtering.

In these cases, an empty resulting tuple can be valid. The missing piece is a visible breadcrumb.

Prefer a small projection API such as:

```python
projection.not_gained(entry)
```

where `entry` is the concrete thing that was considered:

```python
AnySkill | PsionicTalentSkillModels | Chars
```

Examples of useful rendered messages:

- `Admin 0 not gained`
- `Telepathy not gained`
- `STR +1 not gained`
- `Vacc Suit 1 not gained`

Do not over-model the reason yet. It is enough to record that the entry was considered and rejected. The player can usually infer why, and tests can assert that the no-op was intentional.

## Empty Tuples Vs Unhandled Values

An empty tuple can be a valid way to say "there are no applicable choices left".

The bug pattern to avoid is different: a non-empty value reaches a handler, the handler does not know what to do with it, and the code silently drops it.

Suggested rule:

- Empty tuple/result: allowed explicit no-op, often after recording `not_gained(...)` for filtered entries.
- Known non-empty entry that cannot improve the character: call `projection.not_gained(entry)`.
- Non-empty entry with no valid handler in this context: raise `ReplayError`.

## Silent-Drop Policy

These are the rules suggested by the findings above.

### Empty Tuples

An empty tuple can be a valid way to say "there are no applicable choices left".

But we probably reached that empty tuple by considering concrete entries and determining that none can be gained. Those concrete entries should usually be recorded first with `projection.not_gained(...)`.

### Non-Empty Unknowns

A non-empty value that reaches a handler and has no valid interpretation in that context should raise `ReplayError`.

Do not silently treat "we do not know how to handle this" as "nothing happened".

### Known No-Improvement Results

If the code understands the entry but it cannot improve the character, record it:

```python
projection.not_gained(entry)
```

## Reporting Direction

The domain should not rely only on projection diffs for user-visible reporting.

Projection diffs answer:

> What changed?

The character creation flow also needs to answer:

> What was considered but did not change anything?

`projection.not_gained(...)` is a deliberately small first step. It avoids turning reporting into a second rules engine while still making no-op outcomes observable in tests and the UI.

Later, this could become part of a broader outcome/journal model, but that is not required before using the idea in career and pre-career handlers.
