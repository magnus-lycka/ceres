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

Many rules also create future obligations. An event might grant a modifier to a
later advancement roll, force or suggest the next career, create an unresolved
injury, require a later choice of contact or enemy, or change the next term's
available options. These behave like messages sent into the future, to be opened
when character creation reaches the relevant point.

**Scope** is the full *Traveller Core Rulebook* character creation process
as described in `docs/character-creation-rules.md`, excluding alien races
(Aslan/Vargr) and post-career improvement (training). This covers all 12 standard
careers plus the Prisoner special career.

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
- Do not model alien species (Aslan, Vargr) — no `refs/` material available.
- Do not model post-career improvement (training study periods).

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
`survive`, not `survival_rolled`). Current implemented kinds:
`character_started`, `ucp`, `background_skills`, `career`,
`survive`, `mishap`, `term_event`, `skill_choice`, `advancement`,
`reenlist`, `skill_table`, `characteristic_choice`, `connections_roll`,
`skill_roll`, `aging_roll`, `injury_table`, `life_event`, `life_event_unusual`,
`muster_out`, `aging_crisis`.

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

Current `ScheduledEffect` shape:

```python
class ScheduledEffect(BaseModel):
    trigger: str
    source_event_id: int
    effect: dict = Field(default_factory=dict)
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

The current projection models:

```python
class PendingInput(BaseModel):
    id: str
    kind: str
    instruction: str
    options: list[str] = []
    blocking: bool = True

class ScheduledEffect(BaseModel):
    trigger: str
    source_event_id: int
    effect: dict = {}
    expires: str | None = None
    consume: bool = True

class Connection(BaseModel):
    kind: Literal['contact', 'ally', 'rival', 'enemy']
    source: str = ''

class CharacterSummary(BaseModel):
    name: str | None = None
    age: int = 18
    species: str | None = None
    characteristics: dict[str, int] = {}
    current_career: str | None = None
    current_assignment: str | None = None
    rank: int | None = None
    term_count: int = 0
    skills: dict[str, int] = {}
    connections: list[Connection] = []
    problems: list[str] = []
    cash: int = 0
    benefits: list[str] = []
    muster_out_cash_count: int = 0
    dead: bool = False

class CharacterProjection(BaseModel):
    character_id: int
    summary: CharacterSummary
    pending_inputs: list[PendingInput] = []
    scheduled_effects: list[ScheduledEffect] = []
    pending_reenlist: bool | None = None
    muster_out_career: str | None = None
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

## Event Models

Events are Pydantic models forming a discriminated union. The store assigns real
sequential IDs via `model_copy`; the `id` field defaults to `0` to indicate
"not yet assigned".

See `src/ceres/character/events.py` for the current `AnyEvent` union covering
all implemented event kinds.

## Skill Model

`ceres.character.skills` is the canonical skill registry. Each skill is a
Pydantic class with a `type` literal identifier. Specialised skills have
individual `Level` fields. Languages are individual classes (`LanguageGalanglic`,
`LanguageVilani`, etc.) created via `_make_language()`, with a `Languages`
union variable and a `LanguageSkill` type alias. The `AnySkill` discriminated
union contains all skill classes.

`SkillInfo` (a `NamedTuple` of `type` and `specialities`) is used for listing
and display. `skill_list(union)` enumerates any skill union.

Once the character skill model is solid, `ceres.make.robot.skills`
(currently string-based SkillGrant/SkillPackage) and gear software Expert
packages should migrate to reference the canonical character skill classes.

## Rules Data

Career data is authored in YAML under `src/ceres/character/careers/`. Currently
Scout (`scout.yaml`) and Scholar (`scholar.yaml`) are implemented. The YAML
loader validates into `CareerData` Pydantic models at load time.

Career-specific unusual event handling is registered as Python handlers in
`scout.py` and `scholar.py` alongside their YAML data, via
`get_effect_handler()` and `get_skill_roll_handler()` from
`src/ceres/character/careers/loader.py`.

A new career requires:

- a YAML file with qualification, assignments, skill tables, ranks, events, mishaps, muster out
- optional Python module with handlers for unusual event effects
- tests covering the full term flow

## Testing Strategy

Tests build event logs and assert projections. Rolls and decisions are events,
not hidden callbacks.

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
- pending inputs at interaction boundaries
- scheduled effects are applied once or remain active as intended
- unusual event handlers emit typed effects rather than silent mutations
- unrelated events are rejected while blocking pending inputs exist
- same event log replays to the same projection every time

## Implementation Status

### Done

- **Core event/projection models** — `events.py`, `projection.py`,
  `replay.py`. Pure `replay()` function.
- **Store** — SQLite with JSON event log column; typed event round-trip;
  dry-replay validation before save.
- **FastAPI endpoints** — full CRUD for characters; `GET /characters/{id}/projection`;
  `POST /characters/{id}/events`.
- **CLI** — `create start`, `create ucp`, `create status`, `create event`,
  full character management commands.
- **Pre-career setup** — `CharacterStartedEvent` → UCP pending; `UcpEvent`
  → background skills pending (count = EDU DM + 3); `BackgroundSkillsEvent`
  → career choice pending.
- **Career loader** — YAML → `CareerData` Pydantic models; `CareerEvent`
  handles qualification roll with characteristic DM and `qualification`
  scheduled effects; initial basic training (all service skills at level 0)
  on first term.
- **Full term loop** — survive → event → advancement → reenlist/muster out.
  `SurviveEvent`, `TermEventEvent`, `AdvancementEvent`, `ReenlistEvent`.
- **Skill tables** — `SkillTableEvent` + `SkillChoiceEvent`; `SkillRollEvent`
  for career-specific skill checks. Advancement-DM scheduled effects consumed
  on advancement roll.
- **Mishap handling** — `MishapEvent` with typed effects: `decrease_characteristic_choice`,
  `gain_connections_rolled`, `skill_choice`, `injury` (normal/severe/from_table);
  career-registered handlers for unusual mishap effects.
- **Life Events table** — `LifeEventEvent` (all 12 entries) +
  `LifeEventUnusualEvent` (sub-table rolls 1–6).
- **Aging** — `AgingRollEvent` covering all rows of the Ageing table;
  `CharacteristicChoiceEvent` for aging choices; aging crisis path with
  `AgingCrisisEvent`; aging interleaved with reenlist/muster-out flow.
- **Injury table** — `InjuryTableEvent` for all 6 rows including
  "nearly killed" with two-step characteristic reduction.
- **Muster out** — `MusterOutEvent`; cash/benefits columns; cash limit
  (max 3 across all careers); benefit roll count = terms + rank ÷ 2
  (minus 1 for mishap loss); `muster_out_reduce` scheduled effects.
- **Connections and characteristic adjustments** — `ConnectionsRollEvent`,
  `CharacteristicChoiceEvent`.
- **Scout career** — full YAML + handlers (all events, mishaps, muster out).
- **Scholar career** — full YAML + handlers (all events, mishaps, muster out).
- **Language skills** — individual skill classes (`LanguageGalanglic` etc.)
  via `_make_language()` factory; `Languages` union; included in background
  skill options.

### Remaining Work

#### Correctness gaps in current implementation

These rules exist in the implemented flow but are not yet enforced:

- **Skill level cap** — skills may not exceed level 4 during creation; total
  skill levels may not exceed 3 × (INT + EDU). Add enforcement in `_grant_skill`
  and `_increment_skill`.
- **Subsequent basic training** — from term 2 onward (reenlisting or entering
  a new career), the Traveller picks any one Service Skill at level 0.
  Currently only first-term basic training is applied. Needs a `basic_training`
  pending input when entering a career for the second or later time.
- **Advancement forced exit** — if the advancement roll ≤ terms served in the
  career, the Traveller is forced to leave (muster out). Currently the
  reenlist choice is always offered.
- **Advancement natural 12** — a natural 12 forces the Traveller to stay in
  the career (reenlist=True, no choice). Currently treated as a normal success.
- **Benefit roll bonus at rank 5–6** — reaching rank 5 or 6 grants DM+1 to
  all Benefit rolls from that career. Not yet tracked in `_apply_muster_out_setup`.
- **Medical debt** — unpaid injury costs from `_apply_muster_out_benefit` should
  accumulate as debt when cash benefits are insufficient.
- **Pension** — Travellers leaving a qualifying career (not Scout, Rogue, Prisoner,
  or Drifter) after 5+ terms earn an annual pension. Should be calculated and
  recorded at end of creation.
- **End-of-creation marker** — no pending inputs and no active career should
  transition the character to a "complete" state with a summary of final cash,
  pension, and medical debt.

#### Pre-career education (optional, available in terms 1–3)

- New event kinds: `university_entry`, `military_academy_entry`,
  `precareer_event`, `precareer_graduation`.
- University: EDU 6+ entry (with term-based DMs); pick one skill at level 0 and
  one at level 1 from the allowed list; EDU+1; graduation INT 6+; honours at 10+;
  graduation bonuses including qualification DMs and commission roll entitlement.
- Military Academy: service-branch-specific entry roll; gain all Service Skills
  at level 0; graduation INT 7+ with DMs; graduation bonuses including automatic
  entry and commission rights.
- Pre-career events table (12 entries) replaces the normal events roll.
- A new `commission_roll` pending input type arising from pre-career graduation.
- Career YAML: add `precareer_bonus_qualification_careers` and
  `precareer_commission_bonus` fields to careers that benefit from graduation.

#### Additional careers

The remaining 10 standard careers and 1 special career from the core rulebook.
Each requires a YAML file + optional Python handler module + tests.

| Career | Special notes |
| ------- | ------------- |
| Agent | Assignment-based qualification DM change (Intel/Corporate separate ranking table) |
| Army | Commission mechanic; officer rank table; aged-30 qualification penalty |
| Citizen | Assignment skill table used for basic training, not service skills |
| Drifter | Automatic qualification; assignment skill table for basic training |
| Entertainer | DEX or INT qualification |
| Marines | Commission mechanic; officer rank table; aged-30 qualification penalty |
| Merchant | "Free Trader" benefit requires special handling |
| Navy | Commission mechanic; officer rank table; aged-34 qualification penalty |
| Nobility | SOC 10+ automatic qualification |
| Rogue | — |
| Prisoner | Special career: Parole Threshold (starts 1D+2, max 12); leave only when advancement > threshold; mishaps do not eject; no anagathics |

#### Commission mechanic (Army, Navy, Marines)

- New event kind: `commission_roll` with `roll: int`.
- Qualification: SOC 8+ base; only allowed in first term unless SOC 9+;
  DM-1 per term after first.
- On success: enter officer rank table at rank 1; no advancement roll this term.
- On failure: normal advancement roll still allowed.
- Pre-career graduation entitlement: commission roll before first term with DM+2
  (automatic if graduated with honours from military academy).
- Career YAML: add `commission` check and `officer_ranks` table to military careers.

#### Draft, career switching, and assignment changes

- **Draft** — after qualification failure (once per lifetime unless stated
  otherwise); roll 1D on draft table: 1=Navy, 2=Army, 3=Marines, 4=Merchant
  (marine), 5=Scout, 6=Agent (law enforcement). New `draft_roll` event kind.
- **Changing careers** — normal qualification roll for the new career; failure
  → draft or Drifter. Tracked in projection; cannot return to a career in the
  term immediately after leaving it.
- **Changing assignments** — within Army/Marines/Navy/Nobility/Rogue/Scholar/Scout:
  qualification roll; failure = continue with same assignment, no penalty.
  Within Agent/Citizen/Entertainer/Merchant: treated as a new career with
  full muster out; new `assignment_change` event kind.

#### Connections Rule and Skill Packages

- **Connections Rule** — at any event, two Travellers may link their histories;
  both gain one free skill (max level 3, no Jack-of-all-Trades); max two
  connections per Traveller. This is a group-play mechanic. Event kind:
  `connection_skill`, referencing the other character.
- **Skill packages** — after all Travellers finish creation, one of eight
  packages is chosen collectively and skills distributed round-robin. This
  operates at the group level and may be out of scope for per-character
  modelling; consider a separate group session concept or a post-creation
  `skill_package` event kind.

### Verification

After each slice:

```bash
uv run pytest tests/character/
uvx ruff check src/ceres/character/
uvx ty check
```
