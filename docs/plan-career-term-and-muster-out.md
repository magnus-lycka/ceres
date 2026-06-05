# Career Term and Muster-Out Ownership Plan

## Status

Paused. This plan should not proceed until the career modules stop using the
`CAREER_DATA = XCareerData(...)` singleton/data-blob pattern. The career
subclasses themselves need to become the real owners of career rules first; see
the corresponding todo in `docs/todo_maybe.md`.

## Problem

The current character-creation state still stores several career lifecycle
facts in generic or summary-level places:

- `CharacterSummary.career_terms` records terms, but the term objects are too
  passive.
- `CharacterSummary.benefits` and `muster_out_cash_count` are summary-level
  mutable state, even though they are produced by muster-out.
- `CharacterProjection.scheduled_effects` stores muster-out roll additions,
  lost rolls, and benefit-roll DMs as opaque deferred effects.
- `events.py` decides too much about term transitions, assignment changes,
  rank/advancement, and muster-out.

The earlier `term_count` problem exposed the deeper issue: the system needs to
know which terms belong to the same career run. That is not just a muster-out
question. It also controls rank retention, whether assignment changes are
allowed after ejection, whether a new qualification roll is a career change or
an assignment change, and whether failure falls back to the old assignment or
to draft/Drifter. These rules cannot be inferred safely from career name alone.
Some assignment changes continue the same run; others close the current run and
start a new one. That rule belongs to the career module.

## Design Goal

Career modules should own the rules for their own career terms.

The generic lifecycle should know that a term transition is happening, but the
career should decide what the transition means:

- continue the same assignment
- change assignment while continuing the same career run
- change assignment and close the current career run
- switch career
- enter a forced career
- finish character creation

Replay should stay dumb. Events should eventually become messages. The term
object and career module should own the Traveller rules for the current career.

## Core Assignment-Change Scope

The Core rules divide assignment changes into two categories:

- **Assignment change within the same career run**: Army, Marines, Navy,
  Noble, Rogue, Scholar, and Scout.
  - The Traveller makes the qualification roll for the new assignment.
  - On success, the Traveller adopts the new assignment and retains rank.
  - On failure, the Traveller continues in the same career with the same
    assignment and suffers no penalty.
  - This is a continuing career run, so any run-scoped state continues.
- **Assignment change treated as a new career**: Agent, Citizen, Entertainer,
  and Merchant.
  - The Traveller may do this only when voluntarily leaving, not when ejected.
  - Benefit rolls are made normally before the new assignment starts.
  - A qualification roll is required to enter the new assignment.
  - On failure, the Traveller must enter the draft or become a Drifter.
  - On success, the career begins afresh with the new assignment and rank 0.

This plan should eventually encapsulate that whole distinction in the
career/term model. `events.py` should not encode this matrix with generic
conditionals.

## Target Model

### CareerTerm

`CareerTerm` should become a real domain object, with career-specific subclasses
where useful:

```python
class CareerTerm(BaseModel):
    career: Career
    assignment: str
    assignment_index: int
    commission: bool = False
    rank_after_term: int = 0
    muster_out: MusterOut

    def continues_career_run_from(self, previous: CareerTerm) -> bool:
        return self.career == previous.career
```

Career modules can override the continuity rule:

```python
class ScoutTerm(CareerTerm):
    def continues_career_run_from(self, previous: CareerTerm) -> bool:
        return isinstance(previous, ScoutTerm)


class AgentTerm(CareerTerm):
    def continues_career_run_from(self, previous: CareerTerm) -> bool:
        return (
            isinstance(previous, AgentTerm)
            and self.assignment_index == previous.assignment_index
        )
```

The exact Agent rule is an example, not a settled interpretation. The important
point is that each career module owns the decision.

### MusterOut

Start with a generic `MusterOut` model:

```python
class MusterOut(BaseModel):
    terms: int = 1
    cash_count: int = 0
    benefits: list[ItemBenefit] = Field(default_factory=list)
    extra_rolls: int = 0
    lost_rolls: int = 0
    benefit_roll_dms: list[BenefitRollDm] = Field(default_factory=list)
```

The object tracks the current career run, not the whole character. When a new
term continues the same run, the new term receives the previous `MusterOut`
state or a copied successor and increments `terms`. When the transition starts
a new career run, the new term receives a fresh `MusterOut(terms=1)`.

Career-specific `MusterOut` subclasses are not required at first. Add them only
if a career has genuinely distinct muster-out mechanics. The career-specific
part currently appears to be term continuity and the career's benefit/cash
table, both of which can live on the career term/career data.

### Term Construction

Starting a new term should look conceptually like this:

```python
previous = projection.summary.career_terms[-1] if projection.summary.career_terms else None
new_term = career.create_term(projection, assignment)

if previous and new_term.continues_career_run_from(previous):
    new_term.muster_out = previous.muster_out.next_term()
else:
    new_term.muster_out = career.create_muster_out()

projection.summary.career_terms.append(new_term)
```

Whether `next_term()` mutates, copies, or returns a new object should be chosen
deliberately. Copying is probably clearer for replay/debugging because each
term can show the state it inherited, but mutation may be simpler during the
first slice. Tests should pin down the intended behaviour before changing it.

## Summary Accessors

`CharacterSummary` may keep summary-level accessors for display/API use:

- `benefits` should aggregate benefits across all career terms.
- cash may remain summary-level for now, or eventually become aggregated from
  muster-out results.
- `muster_out_cash_count` should aggregate cash rolls across career terms if it
  enforces the global Traveller limit of three cash rolls.

These should be read-only in the long run. Replacement assignment such as
`summary.benefits = [...]` is invalid once benefits are an aggregate view.
During migration, old append-style writes may temporarily be redirected to the
current term's `muster_out`, but direct callers should move to explicit
`MusterOut` methods.

## Moving Logic Out of `events.py`

The following behaviour should move from `events.py` into term/muster-out
objects:

- determining whether an assignment change continues the current career run or
  starts a fresh career run
- enforcing that Agent/Citizen/Entertainer/Merchant assignment changes can only
  happen when leaving voluntarily, not after ejection
- retaining rank on same-run assignment changes
- resetting rank to 0 on assignment changes treated as new careers
- handling failed assignment-change qualification rolls according to the
  career category
- computing number of muster-out rolls
- adding or losing muster-out rolls
- tracking benefit-roll DMs
- asking whether to spend a benefit-roll DM
- enforcing the cash-roll limit
- adding item benefits
- deciding when muster-out is complete
- deciding which transition choices are valid at end of term

`events.py` should eventually say only:

1. This event happened.
2. Find the responsible current term/pending input.
3. Ask the term or pending input to apply the event.
4. Queue whatever pending input the responsible object returns.

## Relationship To Other Plans

This plan is a concrete slice of the broader todo "Replace `ScheduledEffect`
with domain-owned term state" in `docs/todo_maybe.md`.

It also supports
[`docs/plan-event-and-pending-input-rethink.md`](plan-event-and-pending-input-rethink.md):

- self-addressed pending inputs can route user choices to the current term
- career terms can own career-specific state and rule handling
- replay remains a mailman, not a Traveller rules engine
- events can shrink toward simple Pydantic message envelopes

## Migration Order

1. Add `MusterOut` to `CareerTerm`.
2. Move muster-out roll count into `MusterOut.terms`.
3. Add tests for:
   - continuing the same career/assignment
   - changing assignment that continues the same run
   - changing assignment that starts a new run
   - failed same-run assignment change keeps the old assignment without penalty
   - failed new-run assignment change falls to draft/Drifter
   - ejection prevents Agent/Citizen/Entertainer/Merchant assignment changes
   - leaving and later re-entering the same career
   - accumulated cash and benefits across multiple career runs
4. Move `MUSTER_OUT_ADD` and `MUSTER_OUT_REDUCE` scheduled effects into
   `MusterOut`.
5. Move `benefit_roll_dm` scheduled effects into `MusterOut`, including a
   user-facing pending choice for whether to spend the DM on a given benefit
   roll.
6. Replace `CharacterSummary.benefits` and `muster_out_cash_count` fields with
   aggregate properties.
7. Introduce career-specific `CareerTerm` subclasses where career rules need
   them.
8. Move end-of-term transition-choice logic out of `events.py` and into the
   current career term/career module.
9. Delete the remaining muster-out uses of `ScheduledEffect`.

## Testing Principle

Tests must expose known broken behaviour. If a transition is known to produce
the wrong number of muster-out rolls or preserve the wrong state, the test
should go red until the implementation is fixed. Do not route around the broken
path merely to keep the suite green.
