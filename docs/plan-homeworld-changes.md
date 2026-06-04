# Plan: Homeworld Changes During Character Creation

## Summary

Ceres currently stores a single `homeworld` on the character summary and in the
start event. That field is doing two jobs at once:

- the world where the character was born
- the character's current homeworld during character creation

We want to split those concepts while keeping this work tightly scoped to the
character creation tool.

## Scope

In scope:

- select a starting world during character creation
- treat that starting world as the character's immutable `birthworld`
- keep a mutable `homeworld` in the character summary during character creation
- record all homeworld-change situations in the event log
- expose both `birthworld` and `homeworld` in character summary/display
- discover where in life events, pre-careers, and careers homeworld-change
  triggers should occur
- allow careers to trigger mandatory or optional homeworld changes during
  character creation
- allow careers to define constraints on valid target worlds for those changes

Out of scope:

- homeworld changes during play
- any new UI mechanism for selecting a replacement homeworld
- general tracking of current physical location

## Concepts

The character summary should distinguish between:

- `birthworld`: the world selected when the character is created; never changes
- `homeworld`: the character's current homeworld during character creation; may
  change

At character start:

- `birthworld = selected world`
- `homeworld = selected world`

## Triggers

There are only two trigger kinds worth modelling here.

### Forced Change

The event text says or strongly implies that the character must leave the
current homeworld or is no longer based there.

Examples:

- generic Life Event 9: `You move to another world.`
- Citizen mishap 5: `...forcing you to leave the planet.`

Effect for this phase:

- append a dedicated event to the log recording that a homeworld change is
  required
- add a blocking pending input to the projection so the character cannot
  progress until the change is resolved
- do **not** silently mutate `summary.homeworld`
- when the trigger comes from a career or pre-career, record enough metadata to
  say what kind of target world is required

### Optional Change

The event text suggests that changing homeworld is plausible, but not required.

Effect for this phase:

- append a dedicated event to the log recording that a homeworld change was
  offered
- add a non-blocking pending input to the projection surfacing the opportunity
- do **not** silently mutate `summary.homeworld`
- when the trigger comes from a career or pre-career, record enough metadata to
  say what kind of target world is allowed

## Trigger Discovery

This plan is not just about storing homeworld changes honestly. It must also
identify where the rules or strong setting logic suggest these triggers belong.

There are three main sources:

- generic Life Events
- career and mishap tables
- career/pre-career structure itself, especially entry and end-of-term
  transitions

### Event-driven triggers

These come directly from event text.

Examples already identified:

- generic Life Event 9: `You move to another world.` → forced change
- Citizen mishap 5: `...forcing you to leave the planet.` → forced change

Further audits should classify other event text as either:

- forced change
- optional change
- not a homeworld trigger

### Career-structure triggers

Some careers are interstellar enough that a homeworld-change opportunity may
need to occur even without a specific event entry.

Examples to evaluate:

- Navy, Marines, Scout:
  - possibly mandatory relocation at career start if the current homeworld does
    not meet service-base requirements
  - possibly optional relocation at the end of each term to a world with an
    appropriate base
- Merchant, Noble:
  - likely optional relocation opportunities at the end of terms
- Citizen:
  - assignment-specific constraints such as `Corporate` preferring sufficiently
    high-TL worlds and `Colonist` plausibly preferring lower-tech frontier
    worlds
- Military Academy / Navy Academy / Marine Academy:
  - possibly mandatory relocation when joining the academy or tied service if
    an academy/service world requirement is adopted

This should be handled explicitly as part of character-creation flow, not as an
accidental side effect buried in the web UI.

## Target-World Constraints

Careers and some assignments may need to approve which worlds are valid targets
for a relocation.

Examples:

- Scout:
  - only worlds with a Scout base or way station
- Navy:
  - only worlds with an appropriate naval base presence
- Marines:
  - likely worlds with an appropriate naval base presence
- Citizen / Corporate:
  - possibly require current or target homeworld TL to be high enough
- Citizen / Colonist:
  - may encourage or require relocation to a more primitive or frontier world

At this stage, we do not need UI support for filtering these worlds. We do need
the domain model to express the constraints so later UI work has something
truthful to implement.

## Domain Shape for Career-Owned Triggers

This likely wants a career-owned mechanism somewhat analogous to draft, where
the event engine asks career/pre-career logic whether a homeworld trigger
should be raised at certain lifecycle points.

Likely hook points:

- on entering a career
- on entering a pre-career / academy
- at end of term
- from specific event or mishap handlers

Possible API shape:

- a career/pre-career can emit a `required` or `optional` homeworld change
- it can attach target-world constraints
- it can explain *why* the change is being raised

The exact API can wait, but the plan should assume the responsibility belongs
with career/pre-career domain logic rather than the web layer.

## Event Log Design

Add explicit creation-time homeworld events rather than burying this state in
unrelated career or life-event handlers.

Likely event types:

- `HomeworldChangeRequiredEvent`
- `HomeworldChangeOfferedEvent`
- `HomeworldChangedEvent`

`HomeworldChangeRequiredEvent` and `HomeworldChangeOfferedEvent` carry
origin/context metadata:

- source kind (`life_event`, `career_entry`, `career_term_end`, `career_event`,
  `precareer_entry`, etc.)
- source career or pre-career if relevant
- assignment if relevant
- target-world constraints or a serializable selector description
- human-readable reason text

`HomeworldChangedEvent` is the fulfillment event: it carries the new world,
references the pending input via `fulfills`, and mutates `summary.homeworld`.
All three event types are part of this pass.

## Replay / Compatibility

No database migration should be needed.

Existing saved characters begin with:

- `CharacterStartedEvent(homeworld=...)`

Both fields are initialized in `replay()` (`src/ceres/character/replay.py`) when
constructing `CharacterSummary` from the first event:

- `summary.birthworld = first.homeworld`
- `summary.homeworld = first.homeworld`

This preserves compatibility with existing event logs.

## Summary / Display Behavior

Character summary should carry both fields:

- `birthworld`
- `homeworld`

Display policy:

- if they are the same, showing just the current homeworld may be enough in
  compact views
- if they differ, show both explicitly

## Initial Implementation Slice

1. Write tests: replay sets `birthworld = homeworld` for both fresh and old
   event logs
2. Add `birthworld` to `CharacterSummary`; initialize both fields in `replay()`
   (`src/ceres/character/replay.py`) when constructing `CharacterSummary` from
   `CharacterStartedEvent`
3. Update summary/sheet rendering to show both when relevant
4. Audit and classify the first set of creation-time triggers:
   - Life Event 9
   - Citizen mishap 5
   - obvious interstellar career-entry / term-end cases for Navy, Marines,
     Scout, Merchant, Noble, and Citizen assignments
5. Write tests: `HomeworldChangeRequiredEvent` creates a blocking pending input
   and does not mutate `summary.homeworld`; `HomeworldChangeOfferedEvent`
   creates a non-blocking pending input; `HomeworldChangedEvent` fulfills the
   pending input and updates `summary.homeworld`
6. Add:
   - `HomeworldChangeRequiredEvent`
   - `HomeworldChangeOfferedEvent`
   - `HomeworldChangedEvent`
7. Write tests: Life Event 9 produces `HomeworldChangeRequiredEvent`
8. Hook Life Event 9
9. Write tests: Citizen mishap 5 produces `HomeworldChangeRequiredEvent`
10. Hook Citizen mishap 5
11. Add a minimal career-owned trigger mechanism for start-of-career and
    end-of-term relocation opportunities, even if it initially supports only a
    very small subset of careers

## Explicit Non-Goal for This Pass

This pass should not implement the UI for selecting a replacement homeworld. The
full domain machinery — event types, pending inputs, and `HomeworldChangedEvent`
— is in scope. The web layer that lets a user pick a world and submit it is not.
