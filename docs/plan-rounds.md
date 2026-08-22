# Plan: `ceres.rounds` — round-by-round situation (combat) tracker

Status: **in progress** — phases 1–3 complete; see "Phases 1–3 results".

Tracking issue: [#56](https://github.com/magnus-lycka/ceres/issues/56)

## Purpose and goals

A referee's bookkeeping aid for situations run in combat rounds. It tracks
*who is involved, whose turn it is, what round we are in, what each actor has
already done, and how hurt they are*. It does **not** resolve attacks: no to-hit
checks, no dice, no armour, no ranges and no weapons.

The product goals are:

- **Run a fight quickly and clearly.** At a glance the referee can see who may
  act, who cannot, what each actor last did, their reactions, conditions and
  injury. Recording the next event must take only a few deliberate actions.
- **Track combat, not every six-second activity.** The only recorded actor
  actions are Melee attack, Ranged attack, reactions and Done. Damage from
  falls, fire and similar hazards may come from Other. Movement, Minor actions
  and general activity are deliberately absent.
- **Keep a reusable actor library.** PCs, NPCs, animals and eventually robots
  can be found, inspected, copied, added, corrected and removed without being
  recreated for every fight. Creating several similar actors must not require
  repeating a captive form one actor at a time.
- **Preserve consequences between situations.** Injury and stun belong to the
  actor and survive removal from one Situation and use in another until healed
  or explicitly reset. Initiative, turn progress, local party assignment and
  tactical conditions belong to a Situation.
- **Make preparation reusable but non-binding.** A Party is a reusable group
  of actors. Adding it prepares a Situation quickly, after which the referee
  may change that Situation's composition and party assignments without
  changing the reusable Party.
- **Make correction safe and immediate.** Any entered fact can be corrected
  when the referee notices a mistake, while derived states such as stunned,
  unconscious and dead remain consistent with the underlying facts.
- **Do not lose an active fight.** Reloading or reconnecting must not discard
  work. Durable storage must also survive closing the browser or restarting the
  application.
- **Interoperate without coupling the applications together.** Actors may be
  derived from richer `ceres.character`, `ceres.make.robot` and future
  `ceres.make.animal` objects, but rounds must retain a sufficient validated
  representation to work independently. Those source systems must not depend
  on the rounds UI or its mutable combat state.
- **Remain open to practical authoring workflows.** In-app pages, validated
  local files, Python constructors, copying, LLM-generated data and possible
  future external tools all operate on the same actor, party and situation
  concepts. The plan does not require one of them to be the sole authoring
  method.

The model and its names should make these different concepts and lifetimes
obvious. Protocols, JSON schemas, repositories and UI widgets are means of
achieving these goals, not goals in themselves.

Rules reference: `refs/core/03_combat.md` (pages 73–96), plus
`characteristic_dm` from `refs/core/02_traveller_creation.md`.

Typical live Situation: under 20 actors, a handful of rounds. The reusable
Actor library may be much larger.

## Architecture decision: NiceGUI, single Python codebase

The UI question was explored across three shapes: a REST/HTMX split like
`ceres.character.web`, a pure client-side page (vanilla JS / Svelte / Pyodide),
and a Python UI framework. The chosen shape is a **Python UI framework —
NiceGUI**, because this remains a local, single-process application. Actor,
Party and Situation repositories are real application boundaries, but exposing
them through a separate network API would invent work that does not exist.

Why NiceGUI over the alternatives considered:

- **NiceGUI 3.16 — chosen.** Event-driven callbacks (`on_click` → application
  service → refresh) match both the live tracker and local library pages. Built
  on FastAPI/Starlette, which Ceres already depends on. Installs clean on 3.14
  (~20 transitive deps). Ships a pytest plugin (`nicegui.testing`) for
  in-process UI tests.
- *Streamlit* — rejected. The whole-script-rerun model fights a stateful turn
  tracker, per-row buttons need unique-key loops, and persistence is hand-rolled
  anyway. `st.data_editor` is its one genuine advantage here.
- *Gradio* — rejected. Built for ML demo I/O, not stateful tables with per-row
  actions.
- *Plotly Dash* — rejected. Input/Output/State callback ceremony is heavy, and
  per-row buttons need pattern-matching callbacks.
- *Anvil* — rejected. Adds a platform/runtime dependency for a local
  single-user tool.
- *Jupyter / Marimo* — rejected for the app itself. A notebook is a fine
  scratchpad but a poor thing to drive at the table mid-fight.
- *FastAPI + HTMX*, like `ceres.character.web` — rejected per the above: there
  is no backend worth the split.
- *Client-side JS* (Svelte, vanilla, or Pyodide) — rejected. Svelte and vanilla
  put the rules outside pytest and add an npm toolchain to a repo that has
  none; Pyodide keeps them in Python but pays ~8MB of wasm and a bundling step
  for no gain over a local Python process.

**The framework choice is deliberately reversible.** All rules and state live in
`ceres/rounds/domain/`, a pure-Python package that imports nothing from the UI
layer and nothing heavy from the rest of Ceres. The NiceGUI module is a thin
view over that domain. If NiceGUI disappoints, only the view is rewritten.

New dependency: `nicegui`. `deptry` and `pre-commit.sh` must stay green.

## Module layout

```text
src/ceres/rounds/
  domain/
    ids.py          — ActorId, PartyId, SituationId (never bare str)
    tracks.py       — DamageTrack base; CharacteristicTrack, HitsTrack
    damage.py       — DamageKind (lethal / stun) and damage application
    actor.py        — persistent Actor definition and health state
    sources.py      — read-only source protocols and extraction adapters
    party.py        — reusable Party definitions referencing ActorId values
    initiative.py   — InitiativeMode, initiative ordering and tie handling
    actions.py      — Melee/Ranged attacks and Dodge/Parry/Dive reactions
    situation.py    — memberships, local parties, round counter, turn pointer
    repository.py   — actor, party and situation repository protocols
  storage/
    json_store.py   — validated local JSON and durable temporal state
  ui/
    app.py          — ui.run entry point
    actors.py       — searchable actor library and occasional maintenance
    parties.py      — reusable party composition
    situations.py   — prepared situation composition
    table.py        — the live round table and correction controls

tests/unit/rounds/   — mirrors domain/, one test module per domain module
```

### Naming: Situation and Actor

The tracker is built for combat, but neither the group of involved actors nor
its lasting consequences cease to exist at the boundary of one encounter. The
aggregate is therefore a **`Situation`**, not an encounter or a combat, and the
thing taking a turn is an **`Actor`** — a word that covers PCs, NPCs, animals
and eventually robots without claiming all of them are characters. This naming
does not expand the tracked action vocabulary beyond combat actions.

### Persistent actors and situation membership

There is one persistent **Actor**, identified by `ActorId`. It contains two
different lifetimes of data:

- its definition: name, kind, source reference and default combat properties;
- its persistent health state: lethal damage, stun damage and duration, and
  dead or destroyed state derived from those values.

Current STR/DEX/END or Hits are derived from defaults and stored damage. A new
situation therefore does not heal an actor. Healing or resetting health is an
explicit actor operation.

A Situation does not create a second actor or copy actor state. It stores a
**membership** referencing `ActorId`, with only situation-local facts: local
party, party or individual initiative, pending/ready/acted state, reaction
modifiers, last action and tactical conditions such as prone. Removing a
membership leaves the persistent actor untouched.

A reusable **Party** is a named collection of ActorId values. Adding it to a
Situation copies its current composition and name into situation-local party
and membership records, while continuing to reference the same Actors. The
local composition may then diverge freely without changing the reusable Party.

Actor, Party and Situation authoring must be local-file-first and efficient for
batches of similar entries. The in-app editor remains a correction surface
during play, not the primary bulk-entry workflow.

### Rich source objects and the JSON boundary

`ceres.rounds` consumes projections of richer objects created by
`ceres.character`, `ceres.make.robot` and a future `ceres.make.animal`. It owns
read-only structural Protocols describing only what each extraction adapter
needs. The source packages need not import `ceres.rounds`; real source objects
must be checked for structural conformance by `ty`.

The Protocol is not itself the serialisation format. An adapter converts a
source object into a Pydantic Actor definition from a discriminated union such
as `CharacterActorDefinition | AnimalActorDefinition |
RobotActorDefinition`. These models are versioned, validate independently of
the source system, generate JSON Schema and serialise to JSON. A stored source
reference records provenance, while the projection is retained so rounds can
operate without the richer source being available. Refreshing a definition
from its source is explicit and must preserve or deliberately reconcile the
Actor's persistent health state.

Extraction creates or refreshes the Actor definition only. It does not import
initiative, prone, damage, stun or other temporal state from a source object.
A newly imported Actor starts with a separate healthy state; refreshing an
existing Actor preserves its state unless the user explicitly changes it.

Use one source Protocol per genuinely different source shape rather than one
artificial umbrella. The character protocol and adapter are in scope now;
robot and animal contracts are added only when their combat properties are
known.

### Composition over subclassing

What varies between actors is not their behaviour in the round — taking turns,
delaying and reacting are identical for everyone — but **how they absorb
damage**. So an `Actor` *has a* `DamageTrack`:

- `CharacteristicTrack` — STR/DEX/END, for Travellers and NPCs.
- `HitsTrack` — a single Hits score, for animals.

This avoids a behavioural `CharacterActor`/`CreatureActor` hierarchy. Robots
will have their own damage model once their combat rules are implemented; they
must not reuse animal semantics merely because both display Hits. `Actor`
delegates health rules to its track.

The track owns its own rules — `apply(damage, kind)`, `is_unconscious`,
`is_dead`, `action_dm` — and the UI asks the track rather than computing
anything from raw numbers.

`domain/` may import `ceres.character.domain.characteristics` (`Chars`,
`characteristic_dm`) — a leaf module with no dependencies beyond `enum`. The
characteristic DM table is shared Traveller arithmetic and must not be
duplicated here.

Per the typed-identifier rule, Parties and Situations reference actors by
`ActorId`, a frozen typed identifier rather than a bare string. Display names
need not be unique.

## Rules to encode

Each item cites the rule it comes from. Tests are derived from these, not from
the implementation.

### CharacteristicTrack — lethal damage (`03_combat.md:259-268`)

- Damage applies to END first.
- Excess past 0 END goes to STR **or** DEX, the target's choice. The domain
  takes the choice as a parameter; the UI supplies it from a per-actor
  preference, not a popup (see the UI section).
- When STR or DEX reaches 0 the actor is **unconscious**, and further damage
  goes to the remaining physical characteristic.
- All three physical characteristics at 0 → **dead**.
- Characteristic DMs are recalculated from current values and the impaired DM
  is used until healed (`03_combat.md:268`). STR/DEX/END DM are shown live.

### CharacteristicTrack — stun damage (`03_combat.md:366`)

- Stun damage is deducted from END **only**; it never spills into STR or DEX,
  and so can never kill.
- If END reaches 0, the target is **incapacitated for (damage − END) rounds**,
  where END is the value at the moment of the hit.
- The END loss remains after that countdown reaches zero. Further stun is
  measured against the remaining END, so every point of a later hit is excess
  when END is already zero.
- Stun damage heals completely with one hour of rest, unlike lethal damage.

#### Interpretation: one shared END score

Recorded as **RIC-011** (stun and lethal reduce one shared END score) and
**RIC-012** (stun can never complete a kill) in
`docs/RULE_INTERPRETATIONS.md`, with the reasoning and the source evidence.

What it means for the code: `CharacteristicTrack` keeps `lethal_end` and
`stun_end` as two buckets **for healing only** — stun points vanish after an
hour's rest, lethal ones do not. Every threshold uses the single derived value,
`END = max − lethal_end − stun_end`. No rule may branch on the buckets, except
death, which counts lethal damage alone.

### HitsTrack (`03_combat.md:604, 652-660`)

- All damage goes to Hits, not to characteristics.
- Hits 0 → **dead**.
- Hits ≤ 10% of starting Hits → **unconscious** (stated as optional; default on,
  with a per-situation toggle).
- Hits ≤ half starting Hits → **may be driven off** (referee's option; shown as
  a hint, never applied automatically).
- Hits reduced to −(starting Hits) or worse → **body destroyed**.
- Stun suppresses current Hits, but only down to half starting Hits. Damage
  beyond that floor determines the number of rounds of incapacitation.
- Lethal damage displaces stun already suppressing Hits, so stun never reduces
  the lethal damage needed to kill the animal.
- Stored stun and its countdown clear after one hour of rest.

### Initiative (`03_combat.md:28-48, 62, 81`)

- Initiative is the Effect of a DEX or INT check. **The referee types the value
  in; the app rolls nothing.**
- Order is highest first. Ties break on higher DEX. Still tied → the actors act
  simultaneously, shown as a tie group the referee can order by hand.
- `InitiativeMode.FIXED` (RAW: "Every Traveller retains the same Initiative
  score for every combat round", `:81`) or `InitiativeMode.PER_ROUND`, an
  explicitly requested house option that clears and re-prompts each round.
- A **party** may hold one shared initiative (`03_combat.md:36`), which its
  members inherit; order within a shared-initiative party is arbitrary and
  referee-orderable. Any individual may override with their own value. PC and
  NPC parties are the same kind of thing — either may be shared or individual.

*Ambush and Tactics — in scope after all.* An earlier draft ruled these out on
the grounds that they modify a check the app does not roll, so the referee's
typed value already contains them. That was wrong on both counts:

- The ambush ±6 applies to **round one only** (RIC-014), so the ordering differs
  between round one and round two. That is a state change the tracker must
  model, not a constant folded into a typed number. `InitiativeMode` needs a
  third case beyond FIXED and PER_ROUND: fixed, with a first-round adjustment
  that expires.
- Under *Battlefield Dev* (Mongoose, 2024) the whole basis changes: one
  nominated leader per side rolls **every round**, with **Tactics levels added
  as a DM to that check**. Tactics stops being a separate one-off Effect and
  becomes part of a per-round, per-side input.

*Battlefield Dev also validates the requested variant.* Per-round, per-side
shared initiative with arbitrary order inside the side is not a house rule — it
is Mongoose's own official alternative, which is exactly what `PER_ROUND` plus
shared party initiative implements. Its other three modules (opposed
Dodge/Parry with glancing blows, no ranged attacks in close combat, all-or-
nothing AP) are **not** adopted and would change `CharacteristicTrack` if they
ever were.

### The round and tracked combat actions (`03_combat.md:62-81, 117-192`)

- A round is six seconds. Elapsed time = rounds × 6s, which matters because
  unconsciousness recovery is checked per *minute* = every 10 rounds.
- The underlying rules grant one Significant + one Minor action, **or** three
  Minor actions. The app deliberately does not inventory that budget, movement,
  or other Minor actions. It records only Melee and Ranged attacks; **Done**
  means the referee has finished the actor's turn.
- Reactions are unlimited, but **each reaction costs DM−1 on the actor's next
  set of actions** (`:192`).
- Diving for cover forfeits the next set of actions entirely (`:208`).
- An actor may freely **delay** and act later in the turn (`:32`).
- The round ends once everyone has had the chance to act.

"Their next set of actions" is read as *the next unspent set* — a reaction
before the actor has acted penalises this round, one after penalises next round.
Recorded as **RIC-013**.

### Recovery (`03_combat.md:537-539, 366`)

- Stun incapacitation counts down automatically as rounds advance.
- An unconscious character may attempt an END check every minute (every 10
  rounds), with a cumulative DM+1 per previously failed check. The app tracks
  the cadence and the accumulated DM and prompts; the referee rolls and reports
  pass or fail.

### Roster changes

- Actor-library changes are independent of Party and Situation composition.
- Reusable Parties support add, copy, edit, archive, and bulk member changes.
- Adding a Party to a Situation copies its composition into local memberships.
- Actors may be added, removed or reassigned locally without changing the
  reusable Party.
- An actor added mid-situation receives local initiative/turn state, while its
  existing persistent health state is used unchanged.
- Withdrawing from a Situation removes only the membership.

## UI surfaces

Bulk authoring through captive modal forms was rejected after trying the
prototype. The application needs four ordinary pages:

- **Actors:** browse, search and filter the library; import, copy, archive and
  occasionally edit an actor. Batch creation remains file-, constructor- or
  importer-first.
- **Parties:** edit reusable Parties with searchable, multi-select actor
  addition and removal.
- **Situations:** prepare local parties and memberships; adding a reusable Party
  copies its current composition, after which it can be changed locally.
- **Run:** the live round table described below. Its per-row editor is for quick
  corrections during play, not primary data entry.

Python constructors, LLM-generated documents and future external adapters such
as Google Sheets all write the same validated models as the UI. No authoring
surface gets a separate domain representation.

**Table columns:** Name | Party | Ini | STR | DEX | END | Stun | React | Action
| Status. ("Ini", not "Init".)

**Cell formats.** Characteristics read `current/max:DM` — `5/8:-1`, `0/6:-3`,
`9/9:+1` — so the DM lives in the cell it belongs to rather than in one
meaningless "DM" column. Stun has the same `points(rounds)` meaning for every
actor: `4(11)` means four stun points currently suppress the damage-bearing
stat, with eleven rounds of incapacitation left. Stun suppresses character END
towards zero and animal Hits towards half their starting value.

Worked example, an actor at 888 who takes 4 lethal and then 15 stun:

| STR | DEX | END | Stun |
| --- | --- | --- | ---- |
| 8/8:0 | 8/8:0 | 0/8:-3 | 4(11) |

END absorbs 4 of the stun before hitting 0; the remaining 11 become rounds of
incapacitation. After an hour's rest those 4 points come back, the 4 lethal ones
do not.

**React** is its own column: −1 per Dodge or Parry, cleared after the actor's
next set of actions.

**Action** shows the last tracked combat action — `Melee X` or `Ranged Y`.
Movement and other Minor actions are not recorded. Damage often has no actor
source, so **Other** can injure a target for falls, fire, vacuum and similar
hazards without consuming anyone's turn.

**A combat dialog is wanted after all**, kept simple: X attacks Y (X may be
**Other**), Melee or Ranged for actor sources, optional reaction of Dodge / Dive
/ Parry, net damage in lethal and stun points, and whether to pull from STR or
DEX first. Dive greys the target out — it forfeits their next turn. Dodge and
Parry each add −1 to React. Dive also marks the target prone. Prone persists
across rounds as a removable **Prone** tag. Clicking the tag or its × clears it
without recording an action or introducing movement-action bookkeeping.

Every actor row also has **Edit** as a correction surface. Persistent health
corrections update the referenced Actor; initiative, turn state, reaction DM,
last action, waiting/forfeiture flags and prone update only its Situation
membership. Current and maximum characteristics or Hits, stun points and
duration remain editable through their underlying damage representation.
Statuses such as stunned, unconscious and dead remain derived, so the editor
cannot create a label that contradicts the stored damage.

**Round flow.** "New round" is an explicit command. Before or during a round,
Situation memberships and local party assignments may be changed. Initiative
is either inherited from the previous round or set now, individually or for a
whole local party in one operation. Then the actors with the highest Ini turn
**green** and may act, unless stunned or otherwise incapable. Acting turns them
**grey**; waiting leaves them green. The next Ini step then turns green as
well, joining everyone still waiting. Grey until the next round.

## Persistence and undo

The prototype keeps its active `Situation` in NiceGUI's tab-scoped memory. A GET
or page refresh in the same browser tab must reconnect to that object rather
than construct a new encounter. This deliberately volatile state is lost when
the tab closes or the server restarts.

Phase 5 replaces that temporary boundary with validated local storage under
`settings.data_dir() / 'rounds'`.

Actor definitions, reusable Parties and prepared Situations are versioned
Pydantic documents with a JSON representation and generated JSON Schema. The
repository layer loads all documents, provides browse/search/get/save/copy and
archive operations, and reports filename plus validation path without
partially applying invalid input. Manual JSON, Python constructors, LLM output
and source-system adapters all pass through the same validation boundary.

Application-owned temporal state is stored separately from authored
definitions:

- Actor state holds persistent injury and stun across Situations.
- Situation state holds local memberships, initiative, turns, reactions and
  tactical conditions.

All writes are atomic. A browser reload or server restart mid-fight loses
nothing. Editing an actor definition does not silently discard its temporal
state; reconciliation is an explicit validated operation.

Undo is a bounded stack of transaction snapshots. Because an attack mutates
both Situation state and the target Actor's persistent health, an undo entry
contains the Situation plus every Actor state touched by that mutation. This is
still small for the intended encounter sizes and is safer than inverse
operations.

## TDD phases

Each phase is red → green → refactor, tests first, `uvx ruff check --fix` after
each edit, `./pre-commit.sh` green before the phase is called done.

The aim is a clickable walking skeleton early, because the UI questions can only
be answered by using it.

1. ✅ **Damage tracks.** `CharacteristicTrack` cascade, unconscious, dead, live
   DMs, the shared-END stun ruling and its incapacitation countdown;
   `HitsTrack` thresholds. Pure domain, no situation yet.
2. ✅ **Situation and round flow.** Actors, parties, the explicit new-round
   command, initiative (inherit or set, individual or per party), and the
   green → grey turn state machine with waiting.
3. ✅ **Prototype UI.** The table and the combat dialog, on top of 1–2, good
   enough to run a fight at the table and find out what is wrong with it.
4. **Iterate on what the prototype teaches**, then fill in:
   - reaction carryover — DM−1 per Reaction against the next *unspent* set of
     actions (RIC-013), cleared once those actions are spent;
   - the combat-only action scope: Melee, Ranged, reactions, and Done; no
     movement or Minor-action budget tracking;
   - the stun countdown and the 10-round unconsciousness check cadence;
   - a third `InitiativeMode` beyond FIXED and PER_ROUND: **fixed with a
     first-round adjustment that expires**, for the ambush ±6 (RIC-014);
   - optionally the *Battlefield Dev* shape — one nominated leader per side
     rolling each round, with Tactics levels as a DM on that check.
5. **Persistent actor library and source boundary.** Refactor `Actor` into a
   validated definition plus persistent health state; add typed IDs, the
   character-source Protocol and adapter, versioned JSON models, and the local
   actor repository with browse/search/get/save/copy/archive operations.
6. **Reusable Parties and prepared Situations.** Persist Party definitions and
   Situation memberships; implement copy-on-add Party composition and the
   Actors, Parties and Situations pages with search and bulk selection.
7. **Durable live state and undo.** Persist Actor health and Situation-local
   round state independently, make mutations atomic across both, and add the
   bounded transaction snapshot stack.
8. **Docs.** Note the package in `docs/ARCHITECTURE.md`; mark this plan
   complete and move it to `docs/archive/`. The rule interpretations are already
   recorded — RIC-011 (stun and lethal share one END score), RIC-012 (stun can
   never complete a kill), RIC-013 (a reaction penalises the next unspent set of
   actions) and RIC-014 (the ambush DM applies to Initiative only, round one
   only).

Rule tests go through the `Situation` / `Actor` / `DamageTrack` public API.
Repository contract tests run against an in-memory backend and the local JSON
backend. UI tests use an application service rather than reaching into storage
or domain internals directly.

## Phases 1–3 results

Implemented: `ceres/rounds/domain/` (`tracks.py`, `damage.py`,
`actor.py`, `roster.py`, `situation.py`) and `ceres/rounds/ui/` (`app.py`,
`table.py`), with **81 tests** in `tests/unit/rounds/`. Run the prototype with
`uv run python -m ceres.rounds.ui.app` on port 8081.

**Phase 1 — damage tracks.** The lethal cascade, unconscious and dead, live
impaired DMs, stun on a shared END score with its countdown and one-hour rest,
and `HitsTrack`'s dead / unconscious / driven-off / destroyed thresholds with
cumulative stun. Mutation-checked: twelve deliberate breaks, twelve reds.

**Phase 2 — situation and round flow.** Parties with shared initiative,
individual override, DEX tie-break, the explicit new-round command, and the
pending → ready → acted state machine where waiting keeps an actor ready while
the next initiative step opens.

**Phase 3 — prototype UI.** The NiceGUI table plus an attack/damage dialog.

**Phase 4 — in progress.** Table use narrowed the action model: the tracker
records Melee and Ranged attacks and has an explicit Done operation, but does
not inventory movement, Minor actions, or the full action budget. **Other** is
a non-actor damage source for falls, fire, vacuum, and similar hazards.
Reaction penalties now attach to the current unfinished turn or carry to the
next one; Dive follows the same boundary and forfeits the appropriate turn.
It also records the lasting prone condition as a removable tag. Refreshing the
page preserves the tab's active situation, and every actor has a general editor
for correcting stored tracker facts without making derived statuses editable.
An in-memory Roster experiment separated availability from active membership,
but its modal authoring UI was rejected. The next phase replaces that
experiment with persistent Actors, reusable Parties, Situation memberships and
the full-page/file-first workflows above.

**Two defects found by writing the rules down rather than by testing.** The
combat handouts (`handouts/combat_cards.typ`) forced several rules to be pinned
that the code had left vague, and one of those — the ambush ±6 — invalidated a
scoping decision in this plan; see the Initiative section. The other, an actor
with stun points and all characteristics at zero being unkillable, was found by
the referee asking what that state meant in practice.

**Still unrun in a full game session.** Short interactive trials have already
driven the combat-only action scope, consistent stun display, row colouring,
refresh survival, prone tags and general correction editing described above.
Phase 4 remains open until the tracker has supported a real fight.

## Explicitly deferred

- **Per-round injury provenance.** Which round each point of injury arrived in
  matters, because first aid must be applied within one minute — ten rounds — so
  some of an actor's injury may already be past saving while the rest is still
  treatable. Worth tracking internally without displaying it. Postponed.
- **Actions spanning more than one round**, such as first aid or any extended
  action (`03_combat.md:180-186`). Postponed.
- **Fatigue** (`03_combat.md:402-410`) — referee deferred it.
- **Armour and Protection** — the referee enters damage after protection.
- **Dice** — no initiative or damage rolls.
- **Healing** beyond stun recovery — first aid, medical care, natural healing.
- **Robot combat rules and robot-source adapter** — robots have Hits but their
  own damage, stun, protection and critical-hit rules. Their discriminated
  Actor-definition variant and source Protocol are added only after those rules
  are read; they must not inherit animal `HitsTrack` semantics by convenience.
- **Animal source adapter** — reserved for a future `ceres.make.animal`; manual
  validated animal definitions remain supported meanwhile.
- **The Companion's optional rules** — Natural Resilience, Knockout Blow, Random
  First Blood, alternative initiative, disabling wounds
  (`refs/companion/13_combat.md`). Noted as existing; not implemented.
- **Ranges, movement, cover, weapons, attack resolution** — permanently out of
  scope for this package.
