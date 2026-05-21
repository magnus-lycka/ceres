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
new Ceres implementation separates final character state from the creation
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
pending input requirements, and any scheduled future effects. Projection state
can be cached for performance, but it is disposable. Rebuilding from the event
log must produce the same result.

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
  kind: ucp
  fulfills: "1.0"
  ucp: 7869A5

- id: 18
  kind: survive
  fulfills: "17.0"
  dice: [3, 5]
  applied_effects: ["12.0"]
```

Event kinds name the step or decision, not the effect (`ucp`, not `ucp_provided`;
`survive`, not `survival_rolled`). Representative kinds across character creation:
`character_started`, `ucp`, `homeworld`, `background_skills`, `career`,
`skill_table`, `skill`, `survive`, `mishap`, `term_event`, `life_event`,
`commission`, `advancement`, `aging`, and others as needed.

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
exists, the engine rejects unrelated character events. Examples:

- Choose a skill table.
- Choose a specialization for a gained skill.
- Roll or provide dice for an injury result.
- Decide whether to accept a commission.
- Choose whether to reenlist or muster out.

Other pending inputs are deferred. They exist in the projection but are not
available to fulfill until the engine reaches a matching phase. Examples:

- Choose a benefit when mustering out.
- Resolve a contact or enemy choice that the rules postpone.
- Enter a forced next career when the next career-choice step is reached.

Pending inputs are created during event replay. They are removed during replay
when a later valid event references their deterministic pending id through
`fulfills`.

The projection does not need a separate cursor field. The first blocking pending
input's `kind` tells any client what step the character is at. When there are no
blocking inputs, the engine can advance deterministically until external input is
needed or creation is complete.

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
class ScheduledEffect(BaseModel):
    trigger: str
    effect: dict
    source_event_id: str
    expires: str | None = None
    consume: bool = True
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
- a FastAPI app whose OpenAPI pages can exercise the same event and
  projection models

The CLI and FastAPI app are already working, both sharing the same
`SqliteCharacterBackend`. Neither gets special authority to mutate state outside
the event log.

The current projection includes enough context for a simple client to be usable:

```python
class PendingInput(BaseModel):
    id: str
    kind: str
    instruction: str
    blocking: bool = True

class CharacterProjection(BaseModel):
    character_id: int
    summary: CharacterSummary
    pending_inputs: list[PendingInput] = []
    scheduled_effects: list[ScheduledEffect] = []
```

There is no `cursor` field. The first blocking pending input's `kind` encodes
the current step. When there are no blocking inputs, creation either advances
deterministically or is complete.

`CharacterSummary` carries enough for every simple client to render:

```python
class CharacterSummary(BaseModel):
    name: str | None = None
    age: int = 0
    species: str = ''
    characteristics: dict[str, int] = {}
    current_career: str | None = None
    current_assignment: str | None = None
    rank: str | int | None = None
    term_count: int = 0
    skills: list[SkillSummary] = []
    problems: list[str] = []
```

## Session Persistence

Character creation is persisted in a single SQLite `characters` table. The event
log is stored as a JSON column (`events_json`) on the character row. This is
simple, avoids a separate events table, and still makes the event log the
authoritative source of truth.

```text
characters
  id            integer primary key
  sophont       text not null
  player        text not null
  name          text not null
  events_json   text not null default '[]'
```

Reading a character loads the full list of events as Pydantic objects. Writing
replaces the full JSON column with a new list. The store runs a dry replay before
persisting any new event, so an invalid event raises `ReplayError` without
touching the database.

Projected columns such as UCP are derivable from replaying the event log; the
event log is the truth.

## Event Models

Events are Pydantic models forming a discriminated union. The store assigns real
sequential IDs via `model_copy`; the `id` field defaults to `0` to indicate
"not yet assigned":

```python
class EventBase(BaseModel):
    id: int = 0  # assigned by store; 0 means unassigned
    fulfills: str | None = None

class CharacterStartedEvent(EventBase):
    kind: Literal['character_started'] = 'character_started'
    sophont: str
    player: str = 'NPC'
    name: str

class UcpEvent(EventBase):
    kind: Literal['ucp'] = 'ucp'
    ucp: str  # 6 hex digits, one per characteristic in UCP_STATS order

type AnyEvent = Annotated[
    CharacterStartedEvent | UcpEvent,
    Field(discriminator='kind'),
]
```

The `TypeAdapter[AnyEvent]` is used for deserialization. New event kinds are
added here as character creation expands.

## Skill Model

`ceres.character.skills` is the canonical skill registry. `SkillInfo` carries
only `type` (the display name, e.g. `"Space Science"`) and `specialities` (a
tuple of strings). There is no separate `name` field; `type` is the identifier.

Once the character skill model is solid, `ceres.make.robot.skills`
(currently string-based SkillGrant/SkillPackage) and gear software Expert
packages should migrate to reference the canonical character skill classes.

## Testing Strategy

Tests build event logs and assert projections. Rolls and decisions are events,
not hidden callbacks.

Example:

```python
from ceres.character.events import CharacterStartedEvent, UcpEvent
from ceres.character.replay import replay

events = [
    CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Boss'),
    UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
]

projection = replay(character_id=1, events=events)
```

Pending identifiers are deterministic. Tests assert:

- final character state
- important event log entries
- pending inputs at interaction boundaries
- scheduled effects are applied once or remain active as intended
- unusual event handlers emit typed effects rather than silent mutations
- unrelated events are rejected while blocking pending inputs exist
- same event log replays to the same projection every time

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
`roll_modifier` for future use, but the two concepts stay separate: scheduling
describes when an effect applies; the effect describes what happens.

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

Example shape (first careers are Scout and Scholar from the Explorer edition):

```yaml
name: Scout
source: Explorer

qualification:
  characteristic: INT
  target: 5

assignments:
  - name: Courier
    survival:
      characteristic: END
      target: 7
    advancement:
      characteristic: EDU
      target: 9
    skill_tables:
      personal_development: [...]
      service_skills: [...]
      specialist: [...]

ranks:
  - rank: 0
    title: Scout
  - rank: 3
    title: Senior Scout
    effects:
      - type: gain_skill
        skill: Pilot
        level: 1

events:
  2:
    text: Disaster!
    effects:
      - type: handler
        handler: core.scout.disaster

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

Skills are mostly data, closer to gear or weapons. They need stable identifiers
(the `type` field), optional specialties, defaulting rules, and improvement
logic. They are the canonical skill model used by characters and eventually by
robots.

### Characteristics

Characteristics are currently hard-coded as the six-stat human model (`STR`,
`DEX`, `END`, `INT`, `EDU`, `SOC`) via the `Chars` StrEnum in
`ceres.character.characteristics`. `UCP_STATS` is a convenience tuple derived
from that enum.

A registry-driven model is a later concern. Do not hard-code species variants
until the relevant Alien module rules are available in `refs/`.

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
- Validate loaded YAML into Pydantic models.
- Validate handler references against the registered handler catalogue at load
  time.
- Do not expect Pydantic to rewrite source-authored YAML without losing
  formatting and comments.
- If normalized machine-readable output is useful, write generated JSON as a
  cache/debug artifact, not as the canonical source.

## Implementation Status

### Done

- **Slice 1** — Core event/projection models + pure `replay()` function.
  Event kinds: `character_started`, `ucp`. Tests in `tests/character/test_replay.py`.
- **Slice 2** — Store: JSON column event log, typed event round-trip, dry-replay
  validation before save.
- **Slice 3** — FastAPI endpoints: `GET /characters/{id}/projection`,
  `POST /characters/{id}/events`. Full CRUD for characters including
  `DELETE /characters/{id}`.
- **Slice 4** — CLI: `create start` shows pending inputs, `create ucp` posts
  `UcpEvent`, `create delete` command.

### Remaining Work

- **Slice 5** — Pre-career setup: `homeworld` and `background_skills` events.
  UCP → homeworld → background skill pending input sequence. Options depend on
  homeworld, so the pending input for background skills is deferred until
  homeworld is known.

- **Slice 6** — Handler registry + YAML career loader. `@character_rule_handler`
  decorator, validated YAML → Pydantic career models, handler references
  validated at load time.

- **Slice 7** — First careers: Scout and Scholar (Explorer edition). Both with
  qualification, one assignment each, full normal term path: skill/initial
  training → survival → event → advancement → rank rewards → reenlist/muster.
  Career data lives under `src/ceres/character/careers/`.

- **Slices 8+** — Aging, mustering out, mishaps, scheduled effects (next-roll
  modifiers), additional careers, species variants, PDF report.

### Verification

After each slice:

```bash
uv run pytest tests/character/
uvx ruff check src/ceres/character/
uvx ty check
```
