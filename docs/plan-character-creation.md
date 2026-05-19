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

Use two related models:

1. A final/reportable character model.
2. A mutable creation session driven by an event log.

The final character is the thing we render as a PDF. It contains current
characteristics, skills, terms, equipment, contacts, finances, notes, and other
finished character data.

The creation session is the process engine. It keeps a cursor into character
creation, records every roll and decision, tracks pending obligations, applies
scheduled effects, and produces the next requested input.

Conceptually:

```python
session = CharacterCreationSession(...)

while not session.done:
    request = session.advance(rules)
    if request is not None:
        # UI, test, or CLI supplies the requested roll or decision.
        session.resolve(request, answer)
```

`advance()` should continue automatically only while the next step is fully
determined by existing state and rules. When a roll or player choice is needed,
it returns a structured request instead of improvising.

The public session API should consistently use:

- `advance()` to progress until the next request, completion, or error.
- `resolve(request_id, answer)` to answer a pending request.

## Event Log

Use the term **event log** for the authoritative creation history. Avoid using
"journal" as a second term in engine APIs. Reports may render the event log as a
human-readable journal, but code and tests should refer to event log entries.

The event log records what happened, why it happened, and what effects were
applied.

Example entries:

```yaml
- type: decision.made
  step: term.2.skill
  prompt: choose_skill_table
  choice: Service Skills

- type: roll.resolved
  step: term.2.survival
  rule: "INT 5+"
  dice: [3, 5]
  modifiers:
    - value: 1
      reason: Decorated in previous event
      source: term.1.event
  total: 9
  outcome: success

- type: effect.applied
  step: term.2.survival
  effect:
    type: gain_skill
    skill: Vacc Suit
    level: 1
```

The current creation state can be rebuilt by reducing the event log. In
practice we can cache a mutable state object for performance, but the event log
should remain the authoritative explanation.

## Scheduled Effects

Traveller character creation often creates effects that apply later. These
should be first-class objects, not hidden flags scattered across procedural code.

Examples:

- DM+1 on the next advancement roll.
- Must enter Prisoner next term.
- Gain a contact when mustering out.
- Resolve an injury before continuing.
- Gain DM+1 to survival rolls while staying in this career.

Represent these as scheduled effects:

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

## Pending Obligations

Scheduled effects are not the same as pending obligations.

A scheduled effect is a future hook. A pending obligation is something that
blocks progress until resolved.

Examples of pending obligations:

- Choose a skill table.
- Choose a specialization for a gained skill.
- Decide whether to accept a commission.
- Resolve an injury.
- Pick an ally, contact, enemy, or rival.
- Choose whether to reenlist or muster out.

The engine should expose pending obligations as structured requests:

```python
class PendingDecision(CeresModel):
    request_id: str
    step: StepId
    prompt: str
    options: list[DecisionOption] = []
    free_text_allowed: bool = False
```

Rolls are also structured requests:

```python
class PendingRoll(CeresModel):
    request_id: str
    step: StepId
    dice: str
    target: int | None
    modifiers: list[RollModifier]
```

`target=None` means the roll is not pass/fail by itself. The result is still
logged and may be interpreted by a table or handler.

Tests can resolve these with scripted choices and dice. A CLI or future UI can
ask the user.

## Interaction Model

The interaction model is part of the engine design, not a later presentation
detail. Character creation should be driven through a client/server-like
request/response protocol:

1. The client asks the session to advance.
2. The session either advances internally and returns updated state, or returns
   one structured request that needs an answer.
3. The client submits an answer for that request.
4. The session validates the answer, logs it, applies resulting effects, and can
   be advanced again.

The engine should not push information directly to clients, call `input()`, roll
hidden dice, or require UI callbacks. A pure request/response model should be
enough for character creation, because the rules only need progress when the
player, referee, scripted test, or random roller supplies the next answer.

Useful early clients:

- scripted tests that answer requests deterministically
- a CLI runner that prints the current state and pending request, then accepts a
  JSON/YAML answer
- a small FastAPI app whose OpenAPI pages can exercise the same request and
  answer models

The CLI may be the most ergonomic early manual workbench, while FastAPI/OpenAPI
is useful for inspecting schemas and making sure the protocol is clean. Both
should talk to the same session API. Neither should get special authority to
mutate state outside the event log.

The response from `advance()` should include enough context for a simple client
to be usable:

```python
class AdvanceResponse(CeresModel):
    session_id: str
    character_summary: CharacterSummary
    cursor: StepId
    event_log_tail: list[EventLogEntry]
    pending: PendingDecision | PendingRoll | PendingText | None = None
    scheduled_preview: list[ScheduledEffect] = []
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
defer. The request/response model only works if a session can survive between
calls.

Initial implementation should persist sessions as serialized event logs plus
small metadata:

```text
data/characters/<session-id>/
  session.json
  event-log.jsonl
```

An in-memory cache may exist for speed, but it must be rebuildable from the
stored event log. This keeps CLI, FastAPI, and tests on the same model and makes
`session_id` meaningful.

The first implementation can use local files. A database can come later without
changing the session API if the repository interface is explicit.

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

1. Build the current state from the event log and cached state.
2. Apply scheduled effects whose trigger matches the current step.
3. Return any blocking pending obligation.
4. Return any required pending roll.
5. Apply deterministic rule effects.
6. Log the outcome.
7. Move to the next step.

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
pending requests, but those requests must still be ordinary Pydantic messages
that a scripted test, CLI, or UI can answer.

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

Tests should script both rolls and decisions.

Example:

```python
session = CharacterCreationSession(
    character=CharacterDraft(...),
    roller=ScriptedRoller([8, 7, 6]),
    decisions=ScriptedDecisions({
        "term:1:step:skill_table": "Service Skills",
        "term:1:step:reenlist": "continue",
    }),
)
```

Request identifiers should be generated by the engine and must be unique within
the event log. Human-readable step ids are useful, but tests should not depend
on ambiguous keys such as `term.1.skill_table` when multiple careers, repeated
terms, or event-specific choices can produce similar prompts.

Tests should assert:

- final character state
- important event log entries
- pending requests at interaction boundaries
- scheduled effects are applied once or remain active as intended
- unusual event handlers emit typed effects rather than silent mutations

The first tests should cover a very small career subset and one or two scripted
terms before expanding into broad source coverage.

## Proposed Implementation Slices

1. Define final character draft models and basic skill/characteristic models.
2. Define event log entry models.
3. Define pending request models for decisions and rolls.
4. Define scheduled effect and effect models.
5. Implement a minimal reducer/session that can apply effects and record them.
6. Decide and implement file-backed session persistence for event logs.
7. Implement `advance()`/`resolve()` request-response session methods.
8. Add scripted roller and scripted decision providers as the first client.
9. Add handler registry and load-time handler validation.
10. Add pre-career setup steps for characteristics and background.
11. Add a minimal CLI workbench that uses the same message protocol.
12. Optionally add a tiny FastAPI/OpenAPI workbench for schema inspection.
13. Implement one small career with qualification and a normal term path.
14. Add initial training.
15. Add mishap and event tables.
16. Add advancement, rank rewards, and benefit rolls.
17. Add scheduled effects such as next-roll modifiers.
18. Add aging steps.
19. Add mustering-out steps.
20. Add handler escape hatches for unusual event rules.
21. Add a non-default species only after relevant Alien module rules are in `refs/`.
22. Build a simple report from final state plus event log.

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
