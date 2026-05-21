# Plan: Character Creation

## Context

Ceres currently models ships and robots mostly as declarative assemblies: a user
provides a final set of parts, and Ceres computes tonnage, cost, power, notes,
warnings, errors, and report output.

Traveller character creation is a different kind of system. It is a progressive
process where rules, dice rolls, and player decisions interact over time. A
career term is not just data to total up; it is a state machine with steps such
as qualification, initial training, survival, mishaps, events, advancement,
rank rewards, aging, reenlistment, and mustering out.

Many rules also create future obligations. An event might grant a
modifier to a later advancement roll, force or suggest the next career, create
an unresolved injury, require a later choice of contact or enemy, or change the
next term's available options. These behave like messages sent into the future,
to be opened when character creation reaches the relevant point.

There is an older prototype at:

```text
/Users/magnuslycka/work/traveller/travchar
```

That project has useful examples of final character data and PDF output, but the
new Ceres implementation should separate final character state from the creation
engine more explicitly.

## Goals

- Model character creation as an auditable, step-by-step process.
- Support back-and-forth interaction between rules, dice rolls, and player
  decisions.
- Preserve enough information to explain how the character got each skill,
  benefit, injury, ally, enemy, rank, or career transition.
- Represent future effects such as "DM+1 on the next advancement roll" without
  hard-coding them into a single large procedural function.
- Allow career rule data to be authored in a shape that resembles the source
  material: career pages, assignment tables, skill tables, event tables, mishap
  tables, ranks, and benefits.
- Keep source-authored rules readable and reviewable.
- Make tests deterministic by scripting dice rolls and player decisions.
- Leave room for character skills to become the canonical skill model shared by
  robots and other assemblies later.

## Non-Goals

- Do not try to encode every exceptional Traveller rule as pure data.
- Do not require source-authored rule files to round-trip through Pydantic
  without formatting changes.
- Do not use frozen Pydantic models for the active creation process.
- Do not merge character creation state with the final character sheet model.
- Do not build a polished UI as part of the initial engine.
- Do not let an early CLI or web workbench bypass the same interaction protocol
  used by tests.

## Core Idea

Use three related concepts:

1. A final/reportable character model.
2. An event log containing every external input that changes the character.
3. A derived projection built by replaying the event log.

The final character is the thing we render as a PDF. It contains current
characteristics, skills, terms, equipment, contacts, finances, notes, and other
finished character data.

The event log is the authoritative creation history. User decisions, referee
decisions, dice rolls, manual corrections, and system-mediated input are all
recorded as events. Given the same repository code/rules context, the event log
must contain enough information to recreate an identical character, no more and
no less.

The projection is the current derived state: the current character draft, any
pending input requirements, any scheduled future effects, and any cursor-like
position the engine needs while replaying. Projection state can be cached for
performance, but it is disposable. Rebuilding from the event log must produce
the same result.

Every meaningful write path should create an event. Convenience commands such
as `create ucp 7869A5` are allowed, but they are wrappers around event creation,
not separate mutation paths.

## Event Log

Use the term **event log** for the authoritative creation history. Avoid using
"journal" as a second term in engine APIs. Reports may render the event log as a
human-readable journal, but code and tests should refer to event log entries.

The event log records external inputs to character creation. It should not log
derived state changes merely because the engine computed them. If event `Y`
deterministically changes three fields when replayed, the log needs `Y`, not
three extra "field changed" records.

Example entries:

```yaml
- id: 1
  kind: character_started
  sophont: Vilani
  player: NPC
  name: Boss

- id: 2
  kind: ucp_provided
  fulfills: 1.0
  ucp: 7869A5

- id: 18
  kind: survival_rolled
  fulfills: 17.0
  dice: [3, 5]
  applied_effects: [12.0]
```

The current creation state is rebuilt by reducing the event log. While replaying
the log, events can create pending inputs and scheduled effects. Later events
can fulfill a specific pending input, or the engine can automatically consume a
scheduled effect when its trigger matches.

Event identifiers are stable within a character log. Pending identifiers derived
from an event must also be deterministic so replay can match fulfillment events
to the same pending items every time. A simple starting policy is:

```text
<source-event-id>.<local-index>
```

For example, event `1` might create pending items `1.0` and `1.1`. If event `2`
fulfills `1.0`, then replay removes `1.0` from the projection when event `2` is
processed. Nothing separate needs to be logged for "pending item removed"; the
fulfillment event is the historical fact.

## Pending Inputs And Scheduled Effects

Traveller character creation often creates things that matter later. They should
be first-class derived projection state, not hidden flags scattered across
procedural code.

There are at least two broad categories.

### Pending Inputs

A pending input is something the engine needs from outside itself. It is not a
presentation-layer prompt and should not imply `input()` or a specific UI. It is
a rule-state requirement with a machine-readable input shape and a
human-readable instruction.

Some pending inputs are immediate and blocking. While any active blocking input
exists, the engine should reject unrelated character events. Examples:

- Choose a skill table.
- Choose a specialization for a gained skill.
- Roll or provide dice for an injury result.
- Decide whether to accept a commission.
- Choose whether to reenlist or muster out.

Other pending inputs are deferred. They exist in the projection but are not
available to fulfill until the engine reaches a matching phase or cursor state.
Examples:

- Choose a benefit when mustering out.
- Resolve a contact or enemy choice that the rules postpone.
- Enter a forced next career when the next career-choice step is reached.

Pending inputs are created during event replay. They are removed during replay
when a later valid event references their deterministic pending id through
`fulfills`.

### Scheduled Effects

A scheduled effect is a future hook that the engine can usually consume without
user input.

Examples:

- DM+1 on the next advancement roll.
- Must enter Prisoner next term.
- Gain a contact when mustering out.
- Resolve an injury before continuing.
- Gain DM+1 to survival rolls while staying in this career.

Represent these as scheduled effects or deferred inputs depending on whether
they need outside input when they become active. A next-roll modifier is a
scheduled effect. A future choice of benefit is a deferred pending input.

An illustrative shape:

```python
class ScheduledEffect(CeresModel):
    trigger: Trigger
    effect: Effect
    source_event_id: str
    expires: Expiry | None = None
    consume: bool = True
```

Example YAML-like shape:

```yaml
type: effect.scheduled
trigger: next_advancement_roll
consume: true
effect:
  type: roll_modifier
  value: 1
  reason: Impressed a superior officer
```

When the state machine reaches a matching trigger, it applies or offers the
effect and logs that application:

```yaml
- type: scheduled_effect.applied
  trigger: next_advancement_roll
  source: term.1.event.8
  effect:
    type: roll_modifier
    value: 1
```

Some effects are one-shot and consumed. Others remain active while a condition
holds, such as "while in this career".

## Interaction Model

The interaction model is part of the engine design, not a later presentation
detail. Character creation should be driven through a client/server-like
request/response protocol, but that protocol is event-based rather than
prompt-based.

1. The client asks for the current character projection, including pending
   inputs and scheduled effects.
2. The client creates an event. If the event fulfills a pending input, it
   references that pending id.
3. The engine validates the event against the current projection, appends it to
   the event log, replays or updates the projection, and returns the new
   projection.

The engine should not push information directly to clients, call `input()`, roll
hidden dice, or require UI callbacks. A pure request/response model should be
enough for character creation, because progress occurs when the player, referee,
scripted test, or random roller supplies the next event.

Useful early clients:

- scripted tests that append deterministic events
- a CLI runner that lists current pending inputs and creates events
- a small FastAPI app whose OpenAPI pages can exercise the same event and
  projection models

The CLI may be the most ergonomic early manual workbench, while FastAPI/OpenAPI
is useful for inspecting schemas and making sure the protocol is clean. Both
should talk to the same session API. Neither should get special authority to
mutate state outside the event log.

The current projection should include enough context for a simple client
to be usable:

```python
class CharacterProjection(CeresModel):
    character_id: int
    character_summary: CharacterSummary
    cursor: StepId
    pending_inputs: list[PendingInput] = []
    scheduled_effects: list[ScheduledEffect] = []
```

This is deliberately not a polished UI design. It is a protocol that lets tests,
CLI tools, FastAPI, and later richer interfaces validate the same behaviour.

`CharacterSummary` should be small enough for every simple client to render:

```python
class CharacterSummary(CeresModel):
    name: str | None
    age: int
    species: str
    characteristics: dict[str, int]
    current_career: str | None
    current_assignment: str | None
    rank: str | int | None
    term_count: int
    skills: list[SkillSummary]
    problems: list[str] = []
```

## Session Persistence

Session persistence is an early design decision, not an implementation detail to
defer. The event-based request/response model only works if a character creation
can survive between calls.

Initial implementation should persist character creation as an event log plus
small metadata. SQLite is a good early default because it gives us ordinary
application storage and in-memory tests:

```text
characters
  id
  sophont
  player
  name

character_events
  id
  character_id
  kind
  fulfills
  payload_json
```

An in-memory cache or projected columns may exist for speed, but they must be
rebuildable from the stored event log. The event log is the truth; database
columns such as current UCP are projections or conveniences.

## State Machine

The state machine should be explicit, but not monolithic.

Character creation begins before the first career term. The state machine needs
pre-career phases for characteristic generation, species/background setup,
homeworld and education skills, and any rules that affect the first career
choice.

High-level phases:

```text
setup.characteristics
setup.species
setup.background
setup.education
career.choice
career.qualification
term.*
mustering_out.*
finalize
```

A normal career term after qualification might flow like:

```text
term.start
term.skill_or_initial_training
term.survival
term.mishap_or_event
term.event
term.advancement
term.rank_rewards
term.aging_if_needed
term.reenlist_or_muster
term.complete
```

Aging deserves its own step family, not only a placeholder. It involves age
brackets, characteristic rolls and DMs, possible medical treatment costs, and
interactions with anagathics.

Mustering out also deserves a distinct phase. It can involve multiple benefit
rolls, cash versus material choices, career-specific benefit tables, retirement
pay, pensions, gratuities, and deferred obligations from previous events.

At each step, the engine should:

1. Rebuild or update projection state from the event log.
2. Add any pending inputs or scheduled effects created by the current event.
3. Validate any fulfillment reference on the current event.
4. Remove fulfilled pending inputs from the projection.
5. Activate deferred pending inputs whose availability now matches.
6. Apply and consume scheduled effects whose trigger matches.
7. Advance deterministic state until external input is needed or creation is
   complete.

This avoids one huge function while still making the lifecycle easy to inspect.

## Effects

Most rules should produce typed effects. The session applies effects and logs
the result. Useful initial effect types include:

- `gain_skill`
- `increase_characteristic`
- `decrease_characteristic`
- `gain_rank`
- `gain_benefit_roll`
- `gain_contact`
- `gain_ally`
- `gain_enemy`
- `gain_rival`
- `add_note`
- `add_debt`
- `add_asset`
- `injury`
- `end_career`
- `end_character_creation`
- `force_next_career`
- `schedule_effect`
- `roll_modifier`

`roll_modifier` is one concrete effect type. A `ScheduledEffect` can wrap a
`roll_modifier` effect for future use, but the two concepts should stay
separate: scheduling describes when an effect applies; the effect describes what
happens.

Some source events are too unusual to model cleanly as simple data. For those,
rule data should be allowed to name a registered handler:

```yaml
effect:
  type: handler
  handler: core.unusual_event.psionics
```

The handler string must resolve through a registry at rules-load time, not by
ad-hoc importing at runtime:

```python
@character_rule_handler("core.unusual_event.psionics")
def handle_psionics(context: HandlerContext) -> list[Effect]:
    ...
```

This keeps source YAML stable while still letting tests and type checks catch
missing or renamed handlers before a character reaches the event in play.
Handlers should still emit typed effects and event log entries. They should not
silently mutate state.

## Rules Data

Career data should be authored to resemble the source material.

Example shape:

```yaml
name: Navy
source: Core

qualification:
  characteristic: INT
  target: 6

assignments:
  - name: Line/Crew
    survival:
      characteristic: INT
      target: 5
    advancement:
      characteristic: EDU
      target: 7
    skill_tables:
      personal_development: [...]
      service_skills: [...]
      specialist: [...]

ranks:
  - rank: 0
    title: Crewman
  - rank: 1
    title: Able Spacehand
    effects:
      - type: gain_skill
        skill: Mechanic
        level: 1

events:
  2:
    text: Disaster!
    effects:
      - type: handler
        handler: core.navy.disaster

mishaps:
  1:
    text: Severely injured.
    effects:
      - type: injury
        severity: severe
      - type: end_career
```

The authored data should be validated into normalized Pydantic models at load
time. The normalized model does not need to look exactly like the source file.

## Plug-In Rule Domains

Character creation needs several kinds of rule plug-ins. They do not all have
the same shape.

### Skills

Skills are mostly data, closer to gear or weapons. They need stable identifiers,
display names, optional specialties, defaulting rules, and improvement logic.
They should become the canonical skill model used by characters and eventually
by robots.

### Characteristics

Characteristics should be registry-driven rather than hard-coded to a fixed
six-stat model. A default human-like registry can define:

```yaml
STR: { label: Strength }
DEX: { label: Dexterity }
END: { label: Endurance }
INT: { label: Intellect }
EDU: { label: Education }
SOC: { label: Social Standing }
```

Some species and Alien modules may replace, reinterpret, or add to the default
characteristic set. Do not hard-code examples until the relevant Alien module
rules are available in `refs/`.

Rules should refer to characteristic identifiers. Validation should catch a
career or rule package that refers to a characteristic unavailable to the active
species/ruleset, unless that species/ruleset provides an explicit mapping or
interpretation.

### Species

Species are data plus hooks. They can affect the characteristic set, starting
values, aging rules, traits, career access, starting skills, and event handlers.
The exact shape should be designed after the relevant Alien module material has
been added to `refs/`. Species are more integrated than skills and should be
treated as rule packages.

### Careers

Careers are the most integrated plug-ins. A career package may include:

- source-like career data
- assignment tables
- skill tables
- qualification, survival, and advancement rules
- rank and benefit tables
- event and mishap tables
- optional Python handlers for unusual rules
- tests for career-specific messages and effects

New careers may require new message handlers. That is acceptable if the message
boundary remains explicit and tested. A custom handler may emit career-specific
pending inputs, but those inputs must still be ordinary Pydantic messages that
scripted tests, CLI commands, or UI clients can satisfy by creating events.

## Data Format

JSON round-trips cleanly with Pydantic, but is unpleasant for source-like rules.
YAML is easier to read and can look much more like career pages.

Recommended approach:

- Use YAML for hand-authored rule data.
- Use `ruamel.yaml` if comment/order preservation becomes important.
- Validate loaded YAML into Pydantic models.
- Validate handler references against the registered handler catalogue at load
  time.
- Do not expect Pydantic to rewrite source-authored YAML without losing
  formatting and comments.
- If normalized machine-readable output is useful, write generated JSON as a
  cache/debug artifact, not as the canonical source.

TOML with `tomlkit` is another option and round-trips comments well, but nested
career tables, event tables, and skill tables are likely to become less readable
than YAML.

Character instances can remain YAML if that is convenient for manual editing,
but creation history should be structured as an event log rather than compressed
into prose-only term notes.

## Testing Strategy

Tests should build event logs and assert projections. Rolls and decisions are
events, not hidden callbacks.

Example:

```python
events = [
    CharacterStarted(sophont="Vilani", player="NPC", name="Boss"),
    UcpProvided(fulfills="1.0", ucp="7869A5"),
    BirthLocationProvided(fulfills="1.1", location="TROJ2815"),
]

projection = replay(events)
```

Pending identifiers should be deterministic. Human-readable kinds are useful,
but tests should not depend on ambiguous names such as `term.1.skill_table` when
multiple careers, repeated terms, or event-specific choices can produce similar
pending inputs.

Tests should assert:

- final character state
- important event log entries
- pending inputs at interaction boundaries
- scheduled effects are applied once or remain active as intended
- unusual event handlers emit typed effects rather than silent mutations
- unrelated events are rejected while blocking pending inputs exist

The first tests should cover a very small career subset and one or two scripted
terms before expanding into broad source coverage.

## Proposed Implementation Slices

1. Define final character draft models and basic skill/characteristic models.
2. Define event log entry models.
3. Define pending input and scheduled effect projection models.
4. Implement deterministic pending ids from source event id plus local index.
5. Implement a minimal replay/projection reducer.
6. Persist event logs in SQLite and treat projected columns as rebuildable.
7. Add `GET` projection/obligations-style API endpoints.
8. Add generic event-creation API endpoints.
9. Make existing CLI convenience commands append events.
10. Add undo by deleting the last event and rebuilding projection.
11. Add handler registry and load-time handler validation.
12. Add pre-career setup events for UCP and birth location.
13. Add background skill pending inputs.
14. Add a minimal CLI workbench that uses the same event protocol.
15. Optionally add or expand FastAPI/OpenAPI endpoints for schema inspection.
16. Implement one small career with qualification and a normal term path.
17. Add initial training.
18. Add mishap and event tables.
19. Add advancement, rank rewards, and benefit rolls.
20. Add scheduled effects such as next-roll modifiers.
21. Add aging steps.
22. Add mustering-out steps.
23. Add handler escape hatches for unusual event rules.
24. Add a non-default species only after relevant Alien module rules are in `refs/`.
25. Build a simple report from final state plus event log.

## Open Questions

- Should final character YAML include the creation event log, or should event
  log files live next to character files?
- Should manually edited final character state be allowed to diverge from the
  event log?
- How close should authored career YAML stay to the visual layout of source
  tables?
- Should rule data live under `refs/` while incomplete, or under `src/ceres`
  once it becomes executable rules data?
- How soon should the character skill model replace or feed robot skill data?
- Should the first manual workbench be CLI only, or should FastAPI/OpenAPI be
  added at the same time to validate schemas?
