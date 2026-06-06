# List of potential things to do

Update todo items in this document as progress is made.
When todo items are done, please move them
to docs/archive/done_todos.md

## Google Sheet fuel mismatch

We should keep an eye out for any remaining Google Sheet / export-based fuel
discrepancies after the `OperationFuel` fix to follow the book rule of a
rounded-up, minimum-1-ton four-week baseline.

Rule for future work:

- do not add ship-specific code just to force a match when we do not yet
  understand the source of the discrepancy
- instead, document the mismatch in the reference test and sort out whether the
  sheet is rounding, using a different rule basis, or whether Ceres is missing
  a real rule distinction

## Scientists on lab ships / stations

We need an explicit policy for how to model scientists on laboratory ships and
stations.

Current uncertainty:

- a laboratory-heavy design like `Almeida-class Laboratory Station` strongly
  suggests that `scientist`-type personnel should somehow relate to
  `Laboratory`, `Stateroom`, and available working space
- the sheet-style crew manifests may also imply supporting personnel such as
  lab assistants, technicians, or additional administrators
- current Ceres crew rules do not yet decide whether these should be treated as
  required crew, optional mission staff, passengers, or something in between

For now:

- keep carrying explicit source crew when provided
- do not infer new scientist roles until we have decided on a rule-backed
  interpretation

## Modulars and effective displacement

We need an explicit policy for cases where the same ship has one displacement
as a design object but a different effective displacement in some operating
profiles.

References: `refs/hg/24_modular_hull.md`, `refs/hg/58_modular_cutter.md`,
`refs/hg/59_cutter_modules.md`, `refs/hg/70_system_defence_boat.md`

### Construction rules (from `24_modular_hull.md`)

The modular hull is a hull feature with explicit construction rules:

- Up to 75% of internal tonnage may be designated as modular (cannot include
  bridge, power plant, drives, structure, or armour options)
- Hull cost increases by the modular percentage: a 100-ton hull at MCr2 with
  30% modular space → hull cost MCr2 × 1.30 = MCr2.6
- Hardpoints/firmpoints are calculated separately for the main hull and any
  installed module, but the combined total cannot exceed what a non-modular
  ship of the same tonnage would have
- Modules are themselves small ship designs (own hull, systems, etc.) that
  snap into the reserved space

Confirmed in published designs: the 50-ton Modular Cutter has 30 tons (60%)
modular → MCr3 × 0.60 = MCr1.8 extra cost ✅. Capital ships in file 70 use
module bays of 5,800 and 10,400 tons.

### Displacement concern

Examples to sort out:

- modular cutters with and without installed modules
- large modular warships whose published thrust / jump assume a larger loaded
  displacement than the stripped hull line item
- docking clamps and other external carried craft
- jump shuttles, jump nets, and drop tanks

Some published designs clearly distinguish between the ship's own built
displacement and the larger displacement that drives must handle in a
particular carried/loaded state. Other calculations (maintenance, crew
analysis, structural build cost) may still want the design displacement.

Rule for future work:

- do not flatten all such cases into one single `displacement` concept
- be prepared to distinguish between at least:
  - design / structural displacement
  - effective in-flight displacement for performance
- support parameterized outputs where needed, e.g. `Thrust X / Jump Y while
  carrying Z dTons`

## External-load drive performance

Note:

- R-drives are implemented, including high-burn thruster notes.
- when we later add external carry systems such as docking clamps, tow cables, cargo nets, external cargo mounts, jump nets, jump shuttles, modular cutter handling or similar, they should not be treated like internal docking space
- external loads should affect effective displacement for drive-performance calculations
- this likely wants parameterized specs, e.g. performance at `+X dTons`

## Culture property etc

Ships are buit differently for different audiences.
This is partly the biology of different species, but also a matter of
culture and various practical things, e.g. human stock living in very
different worlds, from aquatic to free space to High G etc.

The sophont names in [travellermap.com/t5ss/sophonts](https://travellermap.com/t5ss/sophonts) could be useful,
as well as 'other', 'independent' etc.

## Other distinctions

We already have military boolean. The Adventure class ships split them in:
Exploration, Merchant, Passenger, Working, Military, Travellers Be Like... (catch-all),
Aslan, Sword Worlds, and Vargr.
Smal crafts catalogue in: Commerical, Working, Fighters, Military, Luxury, Aslan,
Sword Worlds, Vargr, Zhodany
Traders & Gunboats in Aslan, Droyne, Hiver, Imperium, Independents, K'kree, Solomani,
Sword Worlds (everybody likes their ships), Vargr and Zhodani.
THere are obviously e.g. Bwap and Florian ships too.

But maybe markers like this are best done by allowing arbitrary free tags on ships?

## Blurbs, pics and plans

We want to be able to attach random, somewhat formatted text to be attached to ship
designs. We'd use markdown for that.

Eventually we'll also want to provide illustrations and floor plans/drwaings.

## Add other types of drives

Keep this as a parking lot for genuinely new drive families, not power systems.

Already implemented elsewhere:

- chemical and fission power plants
- Sterling fission power plants
- high-efficiency batteries
- R-drives

Candidates that still need rule/API work:

- source-specific drive families from non-HG books

## Primitive Hulls

Implement Spinward Extents primitive hulls.

Reference: `refs/spinext/59_arcturus.md`

Started in `src/ceres/make/ship/hull/spinext.py`:

- `hull` is now a package with `standard.py` and `spinext.py`
- `SpinExtPrimitiveHull` is separate from `non_gravity=True`
- base primitive hull cost, basic ship systems Power, Hull point reduction, and
  invalid-drive notes are implemented

Primitive hulls are not the same thing as existing High Guard `non_gravity`
hulls. They are a separate low-tech spacecraft construction model:

- no artificial gravity, lifter support, advanced environmental controls, or
  structural support for high-G manoeuvres
- cannot fit manoeuvre drives or jump drives ✅
- cannot support reaction thruster acceleration above Thrust 3 ✅
- cost Cr15000/ton and use basic ship systems Power equal to 1% of hull tonnage ✅
- -50% Hull points ✅
- may still use Reinforced/Light Hulls, hull configurations, special hulls,
  armour, and hull options
- primitive asteroid hulls cost Cr2000/ton and do not suffer reduced Hull
- TL5 primitive hulls cost double and cannot exceed Thrust 1
- hulls built at TL6 or lower double life support costs

Implementation notes:

- Keep primitive hulls separate from `non_gravity=True`; the source explicitly
  distinguishes non-gravity hulls that do not meet primitive limitations.
- Ship building should report operationally impossible specs as notes/errors.
  For example, a primitive hull with a jump drive, manoeuvre drive, or too much
  reaction/plasma thrust should be invalid.
- Life-support cost doubling probably belongs in habitation/life support cost
  calculations, not in the hull class alone.
- Solar distance/hot/cold/boiling/frozen-zone modifiers are operational context;
  record as notes unless Ceres later gains scenario-state modelling.

## Breakaway multi-section model

The current breakaway hull construction cost and tonnage support is complete
for a single `Ship` design. Future work should only reopen this area when Ceres
is ready to model multiple independently operating sections.

Open design questions:

- decide whether breakaway sections are modelled as a single `Ship` with a
  sub-structure, or as two separate `Ship` objects linked by a relation
- validate that each section has at least a bridge and a power plant once
  sections are explicit model objects
- drive/weapon combining while docked is likely out of scope until a
  multi-section model exists

## Spinning hull configurations (Double Hull, Hamster Cage)

Reference: `refs/hg/05_specialised_hull_types.md`

Allows artificial gravity through rotation instead of grav plates (relates to Non-Gravity Hull).
Both require dedicated spin machinery (0.1 tons per ton of spun section) and increase hull cost
per percent of spun hull. Hamster cage requires ring radius ≥15m.

Probably out of scope for `ceres.make.ship` unless Ceres later starts modelling
layout dimensions. Spin radius and comfort are runtime/layout concerns; see
RIS-021.

## Space stations as a build target

Reference: `refs/hg/27_space_stations.md`

Space stations use almost the same design sequence as ships but with a few differences:

- No streamlined config; most use dispersed structure.
- Manoeuvre drive with Thrust 0 (orbital correction) is 0.5% of hull tonnage at MCr2/ton.
- Power and crew rules differ slightly.
- Can include mineral refineries, manufacturing plants, and other industrial facilities.

Decide whether `Ship` should be extended or whether a separate `Station` class is warranted.

## Birthworld vs mutable homeworld during character creation

See [docs/plan-homeworld-changes.md](docs/plan-homeworld-changes.md).

Ceres should distinguish between:

- immutable `birthworld`
- mutable `homeworld` during character creation

Character creation should log homeworld-change triggers explicitly in the event
log, using only two trigger classes:

- forced change
- optional change

This includes discovering where such triggers should arise in the domain model:

- Life Events and career/pre-career event tables
- interstellar-career start or end-of-term relocation opportunities
- academy/career entry cases that may require relocation

Careers and pre-careers should be able to:

- trigger required or optional homeworld changes
- attach target-world constraints (for example Scout-base, naval-base, or
  assignment/TL-based requirements)

This work is intentionally limited to character creation. It does **not**
include:

- homeworld changes during play
- a new UI for picking the replacement world
- current-location tracking

### Scout career: homeworld trigger at term start (RIC-006)

See [docs/RULE_INTERPRETATIONS.md](docs/RULE_INTERPRETATIONS.md) — RIC-006.

The Scout career (IISS) requires the character to be based at a world with an
Imperial Scout Base (`S`) or Way Station (`W`) in `TravellerMapWorld.bases`.
This should fire at the start of **every** Scout term (first entry and all
re-enlistments).

**Logic:**

- If `'S' not in homeworld.bases and 'W' not in homeworld.bases`:
  emit `HomeworldChangeRequiredEvent` with `source_kind='career_entry'`,
  `source_career='Scout'`,
  `target_constraints='world_with_imperial_scout_base'`, and reason text from
  RIC-006.
- Otherwise (homeworld already qualifies):
  emit `HomeworldChangeOfferedEvent` with the same fields and the optional
  reason text from RIC-006.

**Where to hook it:** The trigger belongs in Scout career domain logic, not in
the web layer. The right hook point is at the beginning of each Scout term —
equivalent to where other per-term career logic fires (survival, events, etc.).

**Dependency:** Another session is reworking the event-handling internals.
Implement this only after that work lands, to avoid merge conflicts around
career term lifecycle hooks.

**Tests to write first:**

- A character with a Scout-base homeworld: `HomeworldChangeOfferedEvent` appears
  in the projection; `homeworld` is not mutated.
- A character with a non-Scout-base homeworld: `HomeworldChangeRequiredEvent`
  appears and is blocking; `homeworld` is not mutated.
- After `HomeworldChangedEvent` fulfils the pending: `homeworld` is updated,
  `birthworld` is unchanged.
- Re-enlistment into a second Scout term produces the same check again.

**Out of scope for this item:** Navy, Marines, Merchant, Noble, and other
careers (their RIC-006 entries are TBD). The UI for picking a replacement
world.

## Character creation: known implementation gaps (rules not yet enforced)

- **Injury table 1D damage** — rows 1 and 2 reduce a physical characteristic by
  1D. The form and auto-fill paths should be verified to record the actual die
  result rather than always using 1.
- **Skill level cap** — skills may not exceed level 4 during creation; total
  skill levels may not exceed 3 × (INT + EDU).
- **Benefit roll bonus at rank 5–6 and "any one Benefit roll" events** — neither
  is implemented; see RIC-004.
- **Generic Life Events table must match Core literally** — the generic
  `LifeEventEvent` / `LifeEventUnusualEvent` implementation in
  `ceres.character.events` should match the Traveller Core Rulebook Life Events
  table word-for-word in meaning and behavior, not merely approximate the same
  mechanics. Current known deviations include:
  - roll 8 Betrayal does not clearly implement "convert one Contact or Ally"
    before falling back to gaining a Rival or Enemy
  - roll 9 Travel does not currently model "You move to another world"
  - roll 12 Unusual Event is substantially altered from core
  This should be fixed from the rulebook text itself, with tests asserting the
  core outcomes rather than current implementation behavior.
- **PSI characteristic support** — add explicit support for the PSI
  characteristic in `ceres.character`. This is needed both generally for core
  psionics rules and specifically so Life Event unusual subtable roll 1
  (encountering a Psionic institute and testing Psionic Strength) can be
  implemented correctly.
- **Generic Pre-Career Events table must match Core literally** — the generic
  pre-career events in `ceres.character.precareers.loader` and
  `PreCareerEvent` handling in `ceres.character.events` should match the
  Traveller Core Rulebook Pre-Career Events table word-for-word in meaning and
  behavior, not merely approximate the same outcomes. Current known deviations
  include:
  - roll 2 psionic-group approach is only recorded as a manual note because PSI
    support is missing
  - roll 4 prank-gone-wrong is not implemented; SOC 8+, Rival/Enemy, and
    natural-2 -> Prisoner handling are all left manual
  - roll 8 political movement wrongly grants Ally + Enemy automatically instead
    of requiring SOC 8+ and only then becoming a leading figure
  - roll 10 tutor conflict drops the required 9+ skill roll and the possible
    skill increase, leaving only a Rival
  - roll 11 wartime draft is mostly a manual note instead of modeled flee /
    draft / SOC 9+ avoidance behavior
  - roll 7 depends on the generic Life Events table, which already has its own
    correctness todo above
  This should be fixed from the rulebook text itself, with tests asserting core
  table outcomes rather than current implementation behavior.
- **Muster-out benefits are string-key encoded** — career data currently writes
  benefits as string keys passed through `parse_benefit(...)`, e.g.
  `parse_benefit('ship_share')` or `parse_benefit(['soc_plus_1',
  'cybernetic_implant'])`. These should be proper benefit objects with typed
  semantics, not stringly-typed identifiers.
- **Medical debt** — unpaid injury costs should accumulate as debt when cash
  benefits are insufficient.
- **Pension** — Travellers leaving a qualifying career after 5+ terms earn an
  annual pension (not Scout, Rogue, Prisoner, or Drifter).
- **End-of-creation marker** — no pending inputs and no active career should
  produce a "complete" state recording final cash, pension, and medical debt.
- **Character-state changes should be visible in the event log** — important
  character changes such as gaining skills, basic training results, rank
  bonuses, characteristic changes, homeworld changes, and similar stateful
  outcomes should not be hidden as replay-only side effects. The event log
  should make it possible to see what actually happened to the character and in
  what order. In particular, first-term basic training is currently applied
  implicitly during career start instead of appearing as explicit logged events.

- **Skill/characteristic roll events should preserve raw roll and system-known
  DM state** — for rolls such as `SkillRollEvent`, Ceres should record enough
  information to distinguish the raw dice result from the computed modifiers
  known to the system. The current `modified_roll`-only shape leaves too much
  ambiguity in the event log and makes the UI guess at why a result happened.

## Character creation: draft, career switching, and assignment changes

- **Draft domain logic** — the draft mechanic should live in the event engine
  (career-owned `is_in_draft` / `is_draft_alternative` predicates, per RIC-003),
  not in the web package. Any draft logic currently in `ceres.character.web`
  violates the career encapsulation rule and must be moved into `events.py` /
  the career package.
- **Changing careers** — normal qualification roll for new career; failure →
  draft or Drifter; cannot return to a career in the term immediately following
  departure.
- **Assignment changes** — within Army/Marines/Navy/Nobility/Rogue/Scholar/Scout:
  qualification roll, failure = continue same assignment. Within
  Agent/Citizen/Entertainer/Merchant: treated as a new career with full muster
  out.

### CareerTerm narrative fields

`CareerTerm` should carry the narrative state from the term so background text
generators and the UI can describe what happened:

- `mishap: str | None = None` — the mishap description if the character was
  ejected; `None` means the term was completed normally
- `event: str | None = None` — the life event description for the term; only
  set when `mishap is None`
- `prison: str | None = None` — the prison-sending description if the character
  was sent to the Prisoner career during this term

These fields serve two purposes beyond narrative:

- A background text generator can read them directly without re-interpreting
  event IDs or replaying history
- `mishap is not None` on the last term of a career run is the signal that the
  character was ejected, which drives career re-entry restrictions (see below)

### Career re-entry restrictions

The Core Rulebook qualification section states (paraphrased):

> If you leave a career you cannot return to it in the next term. Exceptions:
> the draft (you can be drafted back into a career you left or were ejected
> from) and the Drifter career (always open). Assignment changes on page 20 add
> a further exception.

The page-20 exception is that Agent/Citizen/Entertainer/Merchant may leave
their current assignment and enter a different assignment in the same career,
treated as a new career, when leaving voluntarily. That is an explicit
exception; the restriction still applies to re-entering the same assignment.

Rules that need to be enforced in `start_career()`:

- **Ejected last term (mishap on last term of career run)**: cannot re-enter
  the same career the following term regardless of assignment. Exception: draft.
- **Voluntarily mustered out from an `allows_assignment_change=True` career**
  (Scout/Army/Marines/Navy/Noble/Rogue/Scholar): cannot re-enter that career
  the following term. Exception: draft.
- **Voluntarily mustered out from an `allows_assignment_change=False` career**
  (Agent/Citizen/Entertainer/Merchant): cannot re-enter the same assignment the
  following term, but may enter a different assignment in the same career (which
  starts a new career run). Exception: same-assignment re-entry via draft is
  allowed.

`MusterOut.used` (already added) prevents `continue_career_run_from()`
treating a post-muster re-entry as a run continuation.

What still needs to be implemented:

- `CharacterSummary` (or the projection) needs to track whether the most recent
  departure from each career was ejection or voluntary, so `start_career()` can
  enforce the correct restriction. Currently only `last_career` is recorded with
  no ejection flag. The simplest approach: a field
  `last_career_ejected: bool = False` set alongside `last_career` in
  `clear_current_career()` — `True` when exiting via mishap, `False` for
  voluntary muster-out.
- `start_career()` checks these restrictions before qualifying, raises
  `ReplayError` if violated (with a clear message). The draft bypass goes
  through a separate code path that skips the restriction check.

### Career transition choice model

When a term ends (or muster-out completes), the player's valid next choices
are not just "reenlist or leave." They include every available
career/assignment combination. These should be modelled as a first-class domain
concept rather than scattered across several pending-input types.

#### Pull-based discovery

A central coordinator (e.g. `collect_career_transitions(summary)`) broadcasts
to every registered career:

```text
"What assignments do you offer this character for their next term?"
```

Each career receives the full `CharacterSummary` and is solely responsible for
deciding what it offers and why. It returns a list of typed option objects —
possibly empty if it has nothing to offer. The coordinator collects all
responses into one flat list and hands it to the pending-input machinery.

This is a pull model, not a push model. The career owns all the logic: it
looks at whatever parts of the summary matter to it and filters accordingly.
A career might care about any combination of:

- whether the character was ejected from this career last term
- whether the character left voluntarily last term (blocking same-career/
  same-assignment re-entry)
- how many prior terms the character has in this career
- age (some careers have age limits)
- characteristics (qualification DM)
- homeworld (Scout requires a Scout/Way Station base — RIC-006)
- whether a forced next career is active (e.g. sent to Prisoner)
- whether the character is already in this career and which assignment
- whether `allows_assignment_change` applies

No external code should re-implement these concerns. The coordinator just
aggregates; the career decides.

#### Option shape

Each option carries:

- Target career and assignment
- Whether it requires muster-out from the current career first (e.g.
  `allows_assignment_change=False` assignment switches, or any career change)
- Qualification requirement (`CharCheck | None`, where `None` = auto-qualify)
- Pre-computed DM from current characteristics
- A human-readable label

The qualification target and DM are visible in the option so the player can
see what they need to roll before committing. The player should never have
to pick a career, then an assignment, only to find the combination is
unavailable.

#### Restrictions each career encodes

- **Current assignment**: `qualification=None` (automatic reenlist)
- **Other assignments in same career** (for `allows_assignment_change=True`
  careers): normal qualification roll for the new assignment
- **Other assignments in same career** (for `allows_assignment_change=False`
  careers): counts as a new career, marked `requires_muster_out=True`; blocked
  if ejected last term or if the character is re-entering the same assignment
- **Other careers**: all selectable careers that pass this career's own filter
- **Muster out / end career**: always available (unless currently in no career)
- **Draft**: always available; no roll (career randomised by draft table)
- **Drifter**: always available; no roll
- **Prison**: if `career.prison is not None`, the only option the career
  returns is the prison transition; no qualification roll; forced

#### End state

This unified list will eventually replace the current patchwork of
`PendingReenlist`, `PendingAssignmentChangeChoice`, and `PendingDraftChoice`
with a single `PendingCareerTransition` carrying structured
`CareerTransitionOption` objects.

The UI renders the flat list directly — one picker, all options visible at
once, qualification requirements and DMs shown alongside each choice.

## Character creation: eliminate remaining semantic strings

The career YAML migration removed string-based skill/characteristic fields from
career data. Several string-based patterns remain and should be eliminated in
follow-up work packages.

### Replace `PendingInputBase.options: list[str]` with typed option objects

`PendingInputBase` currently declares:

- `options: list[str] = Field(default_factory=list)`

This is far too weak to act as the contract between career/event logic and the
frontend/client. Pending inputs should carry proper typed option objects that
make the intended interaction explicit: labels, submitted values, semantic
meaning, and any structured payload should be part of the model instead of
being improvised from arbitrary strings.

This should become a real domain/API contract between:

- event/career/pre-career logic that creates pending inputs
- the UI/client that renders and fulfills them

The current stringly-typed foundation is one source of bugs such as empty or
ambiguous `career_decision` submissions and special-case rendering drift across
different pending-input kinds.

### Consolidate career-entry state into a `TermChoices` object

`CharacterProjection` now holds three flat fields for career-entry state:
`pending_qualification_dm`, `auto_qualify_careers`, and `forced_next_career`.
These could be gathered into a `TermChoices` domain object that also tracks
draft constraints and future career-availability rules. Not urgent — the flat
fields are clear enough for now.

### Make replay a dumb mailman; move lifecycle rules out of `Event.apply()`

`ceres.character.events` currently mixes several responsibilities that should
be separate:

- event schemas ("what message was sent")
- state mutation / Traveller rule handling
- pending-input definitions
- generic lifecycle orchestration

The important design goal is **not** to make `replay.py` smarter. Replay should
stay stupid too.

Replay's job should be limited to:

- read the ordered event log
- find the fulfilled pending input, if any
- hand the event and current projection to the responsible component
- enforce only generic sequencing/integrity rules independent of Traveller rules

In this picture:

- replay is the mailman
- events are envelopes
- domain modules decide what messages mean

There are two routing modes:

- **fulfilled-pending routing** — most continuation events are routed through
  the pending input they fulfil; the pending acts like a self-addressed
  envelope and identifies the responsible handler
- **root-event routing** — events that arrive without a fulfilled pending input
  (for example phase-start or term-root events) need a small registry from
  event kind to the lifecycle component that owns them

#### Lifecycle structure

The character lifecycle is not complex enough to need an overarching lifecycle
manager. It is just:

1. Start character (`CharacterStartedEvent` seeds the UCP pending input)
2. Select background skills
3. Cycle around terms (career events → term handling → new pending inputs)
4. Finish (near no-op)

Aging, mishap, life events, and injury all happen within terms. A plausible
ownership boundary is that `TermData` (or the career term handling module)
owns that logic, but this is still a proposed split, not a settled fact.

Under that proposed split, the only events that arrive without a fulfilled
pending input — `CareerEvent`, `MishapEvent`, `AgingEvent` — would use the
small root-event registry described above. Everything else would be routed via
the fulfilled pending.

#### DB schema change

Replace the current single-blob `character_events` column with two tables:

- `events(id INTEGER PK, character_id FK, payload JSONB)` — one row per event,
  `id` is the sequence number within the character's log
- `pending_inputs(event_id INTEGER, seq INTEGER, character_id FK, payload JSONB,
  PRIMARY KEY (event_id, seq))` — composite PK is exactly the identity used
  today as the dotted string `"event_id.seq"`, just stored as two integers

An event that fulfills a pending input stores `(fulfills_event_id, fulfills_seq)`
— two integer columns — instead of the current `fulfills: str` field.

The pending input table is still fully derived state: `(event_id, seq)` is
deterministic across replays because the event log is immutable and replay is
deterministic. The event log remains the source of truth. No authoritative
pending-input storage is required; the table can be rebuilt by replaying.

#### Decoupling events from pending inputs

The important idea is **identity-based decoupling**, not the schema change by
itself. If events and pending inputs reference each other only by `(int, int)`
identity — whether as two DB columns or as a tuple in the model layer —
neither class hierarchy needs to import the other at the Python level. Events
can become plain Pydantic models carrying a `fulfills` identity. Pending inputs
can become plain Pydantic models carrying their own `(event_id, seq)` identity.
The relationship is then expressed by stable identifiers instead of Python
type-level coupling.

#### What this would pay off

- `events.py` becomes much smaller and more declarative
- replay stays simple and auditable
- domain knowledge lives with the components responsible for that phase
- pending inputs can become their own module with a cleaner contract to the UI
- tests assert lifecycle behaviour at the responsible module boundary instead of
  inside `Event.apply()` blobs

#### Relationship to the self-addressed envelope plan

[docs/plan-event-and-pending-input-rethink.md](plan-event-and-pending-input-rethink.md)
is a good incremental first slice: it replaces stringly `PendingXxxChoice` /
`on_choice()` dispatch with self-addressed envelopes.

That plan still uses `Event.apply()` as transitional scaffolding for choice
dispatch. That is fine as an incremental move.

This todo describes the broader end state those changes are growing toward:

- self-addressed envelopes remain a good routing mechanism
- but event classes should eventually stop being little executors
- and the meaning of events should live with the lifecycle/domain component
  responsible for that phase

#### Migration slices

1. Introduce domain-owned handlers for one small event family while keeping
   replay dumb (careers are the natural first target via the fulfilled pending)
2. Move pending-input classes out of `events.py` using identity-based
   decoupling instead of import tricks
3. Delete `apply()` bodies incrementally
4. Remove dead transitional abstractions

### Replace remaining `CareerDispatchEffect` registry dispatch with effect subclasses

The `CareerHandlerBase` self-registration pattern is intentional and clean for
**single-phase handlers**: the string `type: Literal['citizen_mishap_4'] =
'citizen_mishap_4'` appears only in the class definition; dispatch to
`effect.handle()` is via `isinstance`, so there are no free-floating string
references that could drift.

The actual smell is **multi-phase handlers**, where the primary handler's
`handle()` method creates a `PendingCareerChoice(context='secondary_key')` or
`PendingCareerSkillRoll(context='secondary_key')` referencing another handler's
key as a bare string. Affected pairs (primary → secondary):

- `prisoner_mishap_3` → `prisoner_mishap_3_fight`
- `prisoner_event_3` → `prisoner_event_3_escape`
- `prisoner_event_9` → `prisoner_event_9_level_{1,2,3}` (f-string, not bare string)
- `prisoner_event_12` → `prisoner_event_12_heroism`
- `prisoner_event_7` → `prisoner_event_7_riot`
- `drifter_event_9` → `drifter_event_9_roll`
- `scholar_event_8` → `scholar_event_8_roll`
- `merchant_event_3` → `merchant_event_3_skill`
- `merchant_event_8` → `merchant_event_8_roll`
- `rogue_event_3` → `rogue_event_3_skill`
- `noble_event_8` → `noble_event_8_skill`
- `citizen_event_8` → `citizen_event_8_skill`
- `entertainer_event_8` → `entertainer_event_8_skill`
- `marines_mishap_4` → `marines_mishap_4_skill`
- `scout_event_9` (creates `PendingCareerSkillRoll(context='scout_event_9')`,
  self-referential — the same handler resolves the roll)

These cross-handler string references also appear in the corresponding tests
(`SkillRollEvent(context='scholar_event_8_roll', ...)`, etc.).

The minimal fix is to replace `context='secondary_key'` literals with
`SecondaryHandlerClass.type` in the primary handler's `handle()` method.
This eliminates the raw string references in production code while keeping
the overall pattern intact.

A fuller refactor would make pending inputs carry the handler class directly
rather than a string key, eliminating `get_career_handler(context: str)` and
the registry lookup entirely.

## Agent career tables: bring Ceres fully in line with Core

The `Agent` career is close to the Core Rulebook, but it still has a few
fidelity gaps in event/mishap text and handler behavior.

References:

- `refs/core/02_traveller_creation.md` (Agent mishaps/events)
- `src/ceres/character/careers/agent.py`

Known differences:

- **Mishap 5** — text matches Core, but the handler only records a manual note
  for the harmed Contact/Ally/family-member injury instead of actually
  resolving the "roll twice on the Injury table for them, taking the lower
  result" outcome in whatever NPC-facing form Ceres decides to support.
- **Event 8** — text matches Core, but the handler does not actually perform
  the immediate Rogue/Citizen Event or Mishap roll, nor the Specialist skill
  table roll on success; it only records a manual note.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Agent event 7 against Core.
- **Minor text drift** — Mishap 1, Mishap 6, and Event 7 omit some Core
  wording/page-reference detail. Once behavior is correct, decide whether these
  strings should match Core literally as part of the broader text-fidelity
  policy.

## Army career tables: bring Ceres fully in line with Core

The `Army` career has several places where the event/mishap text has been
shortened relative to the Core Rulebook, and a few places where handler
behavior does not fully match the rules.

References:

- `refs/core/02_traveller_creation.md` (Army mishaps/events)
- `src/ceres/character/careers/army.py`

Known differences:

- **Text drift across multiple rows** — Mishaps 1-6 and Events 3-11 are often
  substantially shortened compared with Core, even where the mechanical effect
  is mostly present. Review these strings against the rulebook and decide
  whether the project's text-fidelity policy means they should match Core
  literally.
- **Event 6** — text implies "Roll EDU 8+ to avoid injury; if you succeed, you
  gain one level in Gun Combat or Leadership". Ceres implements the success
  branch, but on failure it only records a manual note to roll on the Injury
  table instead of actually applying the injury outcome.
- **Event 11** — Core explicitly grants `Tactics (military) 1` or `DM+4` to the
  next advancement roll. Ceres currently offers generic `Tactics()` rather than
  clearly preserving the required `military` specialty.
- **Event 12** — Core says "You may gain a promotion or a commission
  automatically." Ceres currently uses `AutoAdvanceEffect()`, which performs
  automatic rank advancement but does not model the "or a commission"
  alternative.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Army event 7 against Core.

## Citizen career tables: bring Ceres fully in line with Core

The `Citizen` career has several substantial fidelity gaps in both event/mishap
text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Citizen mishaps/events)
- `src/ceres/character/careers/citizen.py`

Known differences:

- **Mishap 4** — both text and behavior diverge sharply from Core. Core says
  co-operating gains `DM+2` to the next career qualification roll and refusing
  gains an `Ally`; Ceres instead shortens the text and models cooperate/resist
  as `Contact`/`Rival` plus different mishap-ejection handling.
- **Event 3** — Core requires a chosen skill gain, then an `8+` roll on that
  skill with `DM+2` to the next advancement roll on success or `DM-2` to the
  next Survival roll on failure. Ceres currently only gives the initial skill
  choice.
- **Event 6** — Core says `EDU 10+` grants any one skill of your choice at
  level 1. Ceres currently reuses the generic advanced-training helper, which
  instead increases an existing skill by one level.
- **Event 8** — this is a major rewrite in Ceres. Core gives a simple
  illegal-profit choice leading to `DM+1` to a Benefit roll plus `Streetwise
  1`, `Deception 1`, or a criminal `Contact`, or nothing if refused. Ceres
  instead adds a `Streetwise 8+` roll, an extra Benefit roll on success,
  ejection and a `Rival` on failure, and `DM+2` to next advancement on refusal.
- **Event 11** — Core grants an `Ally` and either `Diplomat 1` or `DM+4` to
  the next advancement roll. Ceres currently grants only the `Ally`.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Citizen event 7 against Core.
- **Text drift across multiple rows** — Mishap 1, Mishap 5, Mishap 6, and
  Events 4, 5, 7, 9, 10, and 12 are shortened relative to Core even where the
  mechanical intent is closer. Review these strings against the project's
  text-fidelity policy after the behavioral gaps are fixed.

## Drifter career tables: bring Ceres fully in line with Core

The `Drifter` career has several meaningful fidelity gaps in both event/mishap
text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Drifter mishaps/events)
- `src/ceres/character/careers/drifter.py`

Known differences:

- **Mishap 5** — Core says an existing `Contact` or `Ally` betrays the
  Traveller and becomes a `Rival` or `Enemy`, with a fallback `Rival` or
  `Enemy` if none exist. Ceres currently shortens the text and always creates a
  new `Rival`, never converting an existing relationship and never producing an
  `Enemy`.
- **Event 6** — Core says to go to the Life Events table and have an
  **Unusual Event** specifically. Ceres currently routes to the generic Life
  Events flow instead.
- **Event 8** — Core says gain an `Enemy` only if you do not already have one,
  then roll `Melee 8+`, `Gun Combat 8+`, or `Stealth 8+` to avoid an injury
  roll. Ceres always adds an `Enemy`, omits `Stealth`, adds a skill-increase
  reward on success that Core does not specify, and leaves the injury outcome
  as a manual note on failure.
- **Event 9** — Core's risky-adventure outcome table is materially different
  from Ceres. In particular, Ceres turns the successful outcome into an extra
  Benefit roll instead of `DM+4` to one Benefit roll, and changes the middle
  outcome bands.
- **Event 10** — Core says to increase any skill the Traveller already has by
  one level. Ceres currently uses `SkillChoiceEffect(options=[], level=1)`,
  which does not obviously implement this correctly and should be treated as a
  likely bug until verified/fixed.
- **Event 11** — Core says "Roll for the Draft next term." Ceres currently
  replaces this with a manual problem note and bespoke 1D service mapping
  instead of reusing whatever proper draft handling exists elsewhere.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Drifter event 7 against Core.
- **Text drift across multiple rows** — Mishap 1, Mishap 2, Event 3, Event 4,
  Event 5, Event 6, Event 7, Event 8, Event 9, Event 10, and Event 11 are all
  shortened relative to Core even where the mechanical intent is closer.
  Review these strings against the project's text-fidelity policy after the
  behavioral gaps are fixed.

## Entertainer career tables: bring Ceres fully in line with Core

The `Entertainer` career has several important fidelity gaps in both
event/mishap text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Entertainer mishaps/events)
- `src/ceres/character/careers/entertainer.py`

Known differences:

- **Mishap 4** — Core says an existing `Contact` or `Ally` betrays the
  Traveller and becomes a `Rival` or `Enemy`, with a fallback `Rival` or
  `Enemy` if none exist. Ceres currently shortens the text and always applies
  `GainRivalEffect()`, never converting an existing relationship and never
  producing an `Enemy`.
- **Mishap 6** — Core grants `DM+2` to the next **qualification** roll for the
  next career. Ceres currently uses `AdvancementDmEffect(amount=2)`, which is
  the wrong domain entirely.
- **Event 4** — Core says gain **one of** `Carouse 1`, `Persuade 1`, `Steward
  1`, or a `Contact`. Ceres currently grants both a skill choice and a
  `Contact`.
- **Event 8** — this is a major rewrite in Ceres. Core says accepting gives an
  `Enemy`, then `Art or Persuade 8+`; on success gain one level in any skill
  already possessed; on failure still increase a skill and then roll on the
  Mishap table. Ceres instead uses `Art or Investigate 8+`, grants `DM+2` to
  advancement on success, and gives a powerful `Enemy` on failure.
- **Event 11** — Core says to go to the Life Events table and have an
  **Unusual Event** specifically. Ceres currently routes to the generic Life
  Events flow instead.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Entertainer event 7 against
  Core.
- **Text drift across multiple rows** — Mishap 1, Mishap 3, Mishap 5, Mishap
  6, and Events 3, 4, 5, 6, 7, and 11 are shortened relative to Core even
  where the mechanical intent is closer. Review these strings against the
  project's text-fidelity policy after the behavioral gaps are fixed.

## Marines career tables: bring Ceres fully in line with Core

The `Marines` career has several substantial fidelity gaps in both
event/mishap text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Marines mishaps/events)
- `src/ceres/character/careers/marines.py`

Known differences:

- **Mishap 4** — both branches are rewritten in Ceres. Core says refusing
  ejects the Traveller, while accepting lets them stay but gain the lone
  survivor as an `Enemy`. Ceres instead gives a `Contact` on refusal and adds a
  `Deception or Persuade 8+` gate to staying after acceptance.
- **Event 5** — Core says `EDU 8+` grants any one skill of your choice at
  level 1. Ceres currently reuses the generic advanced-training helper, which
  instead increases an existing skill by one level.
- **Event 6** — Core says success grants `Tactics (military)` or `Leadership`,
  while failure causes injury and a loss of `1` point from any physical
  characteristic. Ceres currently uses generic `Tactics()`, leaves the injury
  outcome as a manual note, and does not apply the required characteristic
  loss.
- **Event 8** — Core explicitly grants `Electronics (comms) 1` as one option.
  Ceres currently uses generic `Electronics()`, losing the specialty.
- **Event 9** — Core says reporting the commander grants `DM+2` to the next
  advancement roll and an `Enemy`, while protecting them grants only an
  `Ally`. Ceres currently gives the `Ally` branch an extra `DM+1` advancement
  bonus that Core does not specify.
- **Event 12** — Core says "You may gain a promotion or a commission
  automatically." Ceres currently uses `AutoAdvanceEffect()`, which performs
  automatic rank advancement but does not model the "or a commission"
  alternative.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Marines event 7 against Core.
- **Text drift across multiple rows** — Mishap 1, Mishap 2, Mishap 3, Mishap
  5, Mishap 6, and Events 3, 4, 5, 6, 7, 8, 9, and 10 are shortened relative
  to Core even where the mechanical intent is closer. Review these strings
  against the project's text-fidelity policy after the behavioral gaps are
  fixed.

## Merchant career tables: bring Ceres fully in line with Core

The `Merchant` career has several important fidelity gaps in both event/mishap
text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Merchant mishaps/events)
- `src/ceres/character/careers/merchant.py`

Known differences:

- **Mishap 2** — text matches Core, but Ceres appears to implement only the
  `Rival` part and not the required "lose all Benefits from this career"
  consequence.
- **Mishap 5** — Core says the Traveller may take the `Rogue` career next term
  without a qualification roll. Ceres currently drops that rule entirely.
- **Mishap 6** — Core says bankruptcy still allows a Benefit roll for the term.
  Ceres currently has an unrelated injury mishap here instead, so this row
  appears to be outright wrong.
- **Event 3** — this is a substantial rewrite in Ceres. Core says refusing the
  smuggling job gains an `Enemy`; accepting and succeeding grants `Streetwise
  1` and an extra Benefit roll. Ceres instead gives a `Rival` on refusal, and
  on acceptance it omits the `Streetwise 1`, ejects the Traveller on failure,
  and adds an `Enemy`.
- **Event 5** — Core says to risk a chosen number of Benefit rolls, roll
  `Gambler 8+` or `Broker 8+`, then gain or lose Benefit rolls accordingly and
  gain one level in whichever skill was used. Ceres currently leaves the whole
  process as a manual problem note and does not automate the skill increase.
- **Event 11** — Core grants an `Ally` and either `Carouse 1` or `DM+4` to the
  next advancement roll. Ceres currently grants only the `Ally`.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Merchant event 7 against Core.
- **Text drift across multiple rows** — Mishap 1, Mishap 5, Event 3, Event 4,
  Event 5, Event 7, Event 8, Event 9, and Event 11 are shortened relative to
  Core even where the mechanical intent is closer. Review these strings against
  the project's text-fidelity policy after the behavioral gaps are fixed.

## Navy career tables: bring Ceres fully in line with Core

The `Navy` career still needs the same kind of strict Core-vs-Ceres audit that
has now been done for several other careers.

References:

- `refs/core/02_traveller_creation.md` (Navy mishaps/events)
- `src/ceres/character/careers/navy.py`

This needs a row-by-row comparison of `MishapEntry.text` / `CareerEventEntry.text`
and handler behavior against the Core Rulebook, with any text drift and
behavioral mismatches turned into concrete follow-up items.

## Noble career tables: bring Ceres fully in line with Core

The `Noble` career still needs the same kind of strict Core-vs-Ceres audit that
has now been done for several other careers.

References:

- `refs/core/02_traveller_creation.md` (Noble mishaps/events)
- `src/ceres/character/careers/noble.py`

This needs a row-by-row comparison of `MishapEntry.text` / `CareerEventEntry.text`
and handler behavior against the Core Rulebook, with any text drift and
behavioral mismatches turned into concrete follow-up items.

## Prisoner career tables: bring Ceres fully in line with Core

The `Prisoner` career still needs the same kind of strict Core-vs-Ceres audit
that has now been done for several other careers.

References:

- `refs/core/02_traveller_creation.md` (Prisoner mishaps/events)
- `src/ceres/character/careers/prisoner.py`

This needs a row-by-row comparison of `MishapEntry.text` / `CareerEventEntry.text`
and handler behavior against the Core Rulebook, with any text drift and
behavioral mismatches turned into concrete follow-up items.

## Rogue career tables: bring Ceres fully in line with Core

The `Rogue` career still needs the same kind of strict Core-vs-Ceres audit that
has now been done for several other careers.

References:

- `refs/core/02_traveller_creation.md` (Rogue mishaps/events)
- `src/ceres/character/careers/rogue.py`

This needs a row-by-row comparison of `MishapEntry.text` / `CareerEventEntry.text`
and handler behavior against the Core Rulebook, with any text drift and
behavioral mismatches turned into concrete follow-up items.

## Scholar career tables: bring Ceres fully in line with Core

The `Scholar` career still needs the same kind of strict Core-vs-Ceres audit
that has now been done for several other careers.

References:

- `refs/core/02_traveller_creation.md` (Scholar mishaps/events)
- `src/ceres/character/careers/scholar.py`

This needs a row-by-row comparison of `MishapEntry.text` / `CareerEventEntry.text`
and handler behavior against the Core Rulebook, with any text drift and
behavioral mismatches turned into concrete follow-up items.

## Scout career tables: bring Ceres fully in line with Core

The `Scout` career still needs the same kind of strict Core-vs-Ceres audit that
has now been done for several other careers.

References:

- `refs/core/02_traveller_creation.md` (Scout mishaps/events)
- `src/ceres/character/careers/scout.py`

This needs a row-by-row comparison of `MishapEntry.text` / `CareerEventEntry.text`
and handler behavior against the Core Rulebook, with any text drift and
behavioral mismatches turned into concrete follow-up items.

## Replace sophont string-name lookup with typed objects

`sophonts/__init__.py` finds sophonts by string name. Sophonts should be
referenced as typed objects or an enum rather than matched by string.

## Make ShipPart generic over assembly type

Currently `ShipPart.assembly` returns `ShipBase`, which only declares `tl` and
`displacement`. Parts that need to access `hull`, `drives`, `power`, etc. work
around this with `getattr(self.assembly, 'field', None)` — which silences the
type checker but defeats its guarantees: if a part is accidentally bound to the
wrong assembly type, the error is silent.

The proper fix is to make `ShipPart` generic over the assembly type, e.g.
`ShipPart[TAssembly: ShipBase]`, so that a part can declare exactly what it
needs:

```python
class Automation(ShipPart[Ship]):
    def _basis(self) -> float:
        return self.assembly.hull ...   # ty now knows assembly is Ship
```

Parts that genuinely work with any `ShipBase` stay as `ShipPart[ShipBase]`.
This is a non-trivial refactor because Pydantic generics interact with
discriminated unions, but it would let us replace all the defensive `getattr`
calls in `automation.py`, `storage.py`, `habitation.py`, and `power.py` with
direct attribute access.
