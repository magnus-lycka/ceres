# Plan: `ceres.rounds` — round-by-round situation (combat) tracker

Status: **in progress** — phases 1–3 complete, phase 4 open; see "Progress so
far".

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
  can be found, inspected, copied, added, corrected and retired without being
  recreated for every fight. Creating several similar actors must not require
  repeating a captive form one actor at a time.
- **Preserve consequences between situations.** Injury and stun belong to the
  actor and survive removal from one Situation and use in another until healed
  or explicitly reset. Initiative, turn progress, party assignment and tactical
  conditions belong to a Situation and never leave it.
- **Make preparation reusable but non-binding.** A Party is a reusable named
  set of actors. Adding it prepares a Situation quickly, after which the referee
  may change that Situation's composition and party assignments without
  changing the reusable Party — the import keeps no tie to its origin.
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
    tracks.py       — DamageTrack over injury history; Characteristic, Hits
    damage.py       — DamageKind (lethal / stun) and applied-injury entries
    actor.py        — Actor definition variants and persistent health state
    sources.py      — read-only source protocols and extraction adapters
    party.py        — standalone reusable Party: a name and a set of ActorIds
    initiative.py   — InitiativeMode, initiative ordering and tie handling
    actions.py      — Melee/Ranged attacks and Dodge/Parry/Dive reactions
    situation.py    — membership rows, round counter, turn pointer
    repository.py   — actor, party and situation repository protocols
  app/
    service.py      — the application service the UI and UI tests call
  storage/
    json_store.py   — the three JSON document kinds, written atomically
  ui/
    app.py          — ui.run entry point
    actors.py       — the roster grid and its selection operations
    parties.py      — reusable party composition
    situations.py   — situation composition
    table.py        — the live Run table and correction controls

tests/unit/rounds/   — mirrors domain/, one test module per domain module
```

The discriminated union of Actor definition variants lives in `actor.py`
alongside the health state it belongs to; `sources.py` holds only the read-only
Protocols and the adapters that produce those definitions. `roster.py`, the
phase-4 experiment, disappears when `party.py` and membership rows replace it.

Nothing above the domain reaches into it: `app/service.py` owns repository
wiring and is the only thing the NiceGUI pages — and the UI tests — call.

### Naming: Situation and Actor

The tracker is built for combat, but neither the group of involved actors nor
its lasting consequences cease to exist at the boundary of one encounter. The
aggregate is therefore a **`Situation`**, not an encounter or a combat, and the
thing taking a turn is an **`Actor`** — a word that covers PCs, NPCs, animals
and eventually robots without claiming all of them are characters. This naming
does not expand the tracked action vocabulary beyond combat actions.

### Actors, Parties and Situation membership

Three concepts with three different lifetimes. They are deliberately not
variants of one thing.

**Actor** — persistent, identified by `ActorId`. One Actor is one individual.
Ten chickens in a fight are ten Actors, not one Actor with a count, because
each of them gets hurt separately. Several Actors may be derived from the same
source object — one `ceres.make.animal` chicken, one robot design — so the
relation from a source object to Actors is one-to-many. Five identical fighting
dogs in a fight are five `ActorId`s. Within one Situation an Actor has **at most
one membership row**; across Situations it may appear in as many as it lives
through.

An Actor holds two kinds of data:

- its definition: name, kind, source reference, free-form tags and default
  combat properties;
- its persistent health: a **damage history** — an ordered list of what each
  injury actually did.

Tags are there to make a library findable — `wolves`, `session 12`, `pirates` —
and carry no rules meaning.

Each history entry records the **applied result, not the input**: the round it
landed in, whether it was lethal or stun, and the reduction it caused to each
characteristic — STR/DEX/END, or Hits. So an entry is `round 5: STR −4, END −3`,
not "7 damage, pull from STR". The allocation choice, the END-first cascade and
the order of several hits in one round are all resolved when the damage is
applied, and the stored fact is the outcome.

That is what makes the history worth keeping. Current values are the defaults
minus the sums, so nothing has to be replayed to know them. What replay would be
needed for — which injury is still inside the first-aid window — is exactly what
the table below shows directly, and correcting a mistake means editing the line
that was wrong rather than reverse-engineering a total.

Entries carry a round while the Situation they landed in is live, and are
stamped **"earlier"** once it ends: injuries from a previous fight are past the
first-aid window by definition, so their exact round has no remaining meaning
and they may be compacted per kind.

Nothing about a particular fight is stored on the Actor — not initiative, and
not the round-relative facts described under Situation membership below.

**Party** — standalone and reusable: a name and a set of `ActorId` values, plus
whatever descriptive parameters prove useful. The PC party, a wolf pack,
starport security, one named band of pirates. It exists to make preparation
quick and to be browsed and edited outside any fight. A Party holds no
initiative and no combat state whatsoever.

**Situation membership** — a Situation holds one row per participating Actor,
referencing it by `ActorId`. The row carries only situation-local facts: party
name, initiative, pending/ready/acted state, reaction modifiers, last action,
waiting and forfeiture flags, and tactical conditions such as prone. Removing a
row leaves the Actor and its injuries untouched.

**Anything counted in rounds lives on the row, not on the Actor**, because a
round number only means something inside the fight that is counting them: the
round an actor's incapacitation ends, the round they fell unconscious and how
many recovery checks they have failed. When the Situation ends, those facts end
with it (see Time and Situation boundaries).

The party of a member is a **plain editable name on that row** — not a
reference, and not a separate situation-party object. Rows can be reassigned to
another name, a side can be split by editing names, and the field may be left
empty for an actor who belongs to no side, such as an innocent bystander.
Collective operations, "set initiative 8 for Raiders", match on that name and
write the value into each matching row.

**Importing a Party is a copy that forgets its origin.** Adding a Party to a
Situation writes its name into the party column of one new row for each Actor
that is a member *at that moment*. No link to the Party survives the import.
Editing the Situation afterwards never touches the Party; editing the Party
afterwards never touches the Situation. Actors may equally be added to a
Situation one at a time, with or without a party name.

**Copying an Actor is a domain operation, not a UI trick.** Copy ×N produces N
independent Actors from one, with numbered names (`Wolf 1 … Wolf 10`) and no
health history, since a fresh copy has not been hurt yet. It is how identical
opponents are created, and it belongs beside the definition it copies rather
than in whatever page happens to call it. See Roster management for the surface.

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

The track owns its own rules — `apply(damage, kind, at=round)`,
`is_unconscious`, `is_dead`, `action_dm` — and the UI asks the track rather than
computing anything from raw numbers. `apply` is where the END-first cascade and
the STR-or-DEX choice are resolved; what it appends to the history is the
resolved per-characteristic reduction, so no query ever has to replay the rules
to know a current value.

`domain/` may import `ceres.character.domain.characteristics` (`Chars`,
`characteristic_dm`) — a leaf module with no dependencies beyond `enum`. The
characteristic DM table is shared Traveller arithmetic and must not be
duplicated here.

Per the typed-identifier rule, Parties and Situations reference actors by
`ActorId`, a frozen typed identifier rather than a bare string. Display names
need not be unique — ten chickens may all be called Chicken — so any surface
listing actors must be able to tell identically named rows apart.

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
  where END is the value at the moment of the hit. Held on the membership row as
  the round it ends, not as a counter someone has to decrement.
- The END loss remains after that countdown reaches zero. Further stun is
  measured against the remaining END, so every point of a later hit is excess
  when END is already zero.
- Stun damage heals completely with one hour of rest, unlike lethal damage. That
  rest happens between fights, so the app applies it as an explicit **Clear
  stun** rather than inferring it (see Time and Situation boundaries).

#### Interpretation: one shared END score

Recorded as **RIC-011** (stun and lethal reduce one shared END score) and
**RIC-012** (stun can never complete a kill) in
`docs/RULE_INTERPRETATIONS.md`, with the reasoning and the source evidence.

What it means for the code: `CharacteristicTrack` distinguishes lethal from stun
entries **for healing only** — Clear stun removes the stun ones, lethal ones
survive it. Every threshold uses the single derived value,
`END = max − lethal against END − stun`. No rule may branch on the kind, except
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
- Stun entries and the incapacitation they caused are removed by Clear stun,
  the referee's stand-in for an hour of rest.

### Initiative (`03_combat.md:28-48, 62, 81`)

- Initiative is the Effect of a DEX or INT check. **The referee types the value
  in; the app rolls nothing.**
- Order is highest first. Ties break on higher DEX. Still tied → the actors act
  simultaneously, shown as a tie group the referee can order by hand.
- `InitiativeMode.FIXED` (RAW: "Every Traveller retains the same Initiative
  score for every combat round", `:81`) or `InitiativeMode.PER_ROUND`, an
  explicitly requested house option that clears and re-prompts each round.
  Neither exists in code yet — the prototype behaves as FIXED, and the enum
  arrives with the third mode below.
- **Initiative belongs to the Situation and to nothing else.** It is rolled at
  the table for that fight and has no meaning outside it, so it is stored on the
  membership row — never on the Actor, and never on the reusable Party. It is
  not carried into a Situation and not carried out of one.
- A **side may share one initiative** (`03_combat.md:36`). That is an input
  convenience, not a shared object: entering a value for a party name writes it
  to every row carrying that name, after which any row may be edited on its own.
  Order within a group holding equal initiative is arbitrary and
  referee-orderable. PC and NPC sides are the same kind of thing.

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

- Stun incapacitation ends at a round stored on the membership row, so it
  expires as rounds pass rather than being counted down by anyone.
- An unconscious character may attempt an END check every minute (every 10
  rounds), with a cumulative DM+1 per previously failed check. The row stores
  the round unconsciousness began and the number of failed checks, so the next
  check is due at `began + 10 × (failures + 1)`. The app prompts; the referee
  rolls and reports pass or fail.
- Both are round-relative, so both belong to the Situation and end with it.

### Time and Situation boundaries

**The only clock is the round counter of the Situation being run, and exactly
one Situation is live at a time.** A new fight cannot begin before the previous
one is finished. That is what makes an unqualified round number unambiguous, in
the damage history and everywhere else.

A campaign clock was considered and rejected. So was tracking elapsed time or
rest between fights. Neither earns its keep: every rule that depends on time
runs inside one fight — incapacitation lasting a few tens of seconds, the
10-round unconsciousness cadence, the one-minute first-aid window — and a fight
that starts a minute after the last one *is* the same fight, still counting its
own rounds.

**What crosses a Situation boundary:** injuries, and the stun points that go
with them. They stay on the Actor until healed or cleared.

**What does not:** everything counted in rounds. Incapacitation, the
unconsciousness check cadence, initiative and turn state end with the fight they
belonged to. An actor still stunned or unconscious when the next Situation opens
is simply not in it — the referee leaves them out, or edits them.

**Stun recovery is a referee action, not a timer.** The rule is an hour of rest,
which happens between sessions rather than between rounds, so the app offers a
one-click **Clear stun** on an Actor and does not try to infer when an hour has
passed. Resetting health entirely is the same kind of operation. The rule is
documented in the tracker so the referee knows what they are applying, on the
same principle as entering damage after armour rather than modelling protection.

**Surviving entries are stamped "earlier" when a Situation ends.** A new fight
counts from round 1 again, and injuries carried into it are past the first-aid
window in any case.

*Long-term healing would bring a real clock back*, since natural healing counts
days. It is deferred, and the damage history survives such a change unaltered —
only the frame of reference for a stamp moves.

### Roster changes

- Actor-library changes are independent of Party and Situation composition.
- Actors support add, edit, copy ×N with numbered names, import, refresh from
  source, and archive.
- Reusable Parties support add, copy, edit, archive and bulk member changes.
- Adding a Party to a Situation copies its name and its members at that moment
  into new membership rows, and keeps no tie to the Party afterwards.
- Rows may be added, removed or reassigned to another party name without
  changing any reusable Party. The party name may also be cleared.
- An actor added mid-situation receives fresh situation-local state, while its
  existing persistent health state is used unchanged.
- Withdrawing from a Situation removes only the membership row.
- An Actor is **archived, not deleted**, while any Party or Situation still
  references its `ActorId`. Archived actors stay resolvable and are marked as
  archived wherever they appear, so an old Situation never loses a participant.

## UI surfaces

The **Run** page — the live round table described below, with a per-row editor
for quick corrections during play — is settled and built. Three more surfaces
are needed, for the actor library, reusable Parties and preparing a Situation.

### Roster management: the library is a grid

The captive modal form of the phase-4 prototype is fine for correcting one row
mid-fight and wrong for managing a library. That is a finding from using it, and
the reason is that roster management is **four different jobs** which no single
form serves:

| Job | Volume | Mechanism |
| --- | --- | --- |
| PCs | 4–6, rarely change | Import from `ceres.character`, refresh later |
| A pack of identical creatures | 10 chickens, 5 wolves | Copy one actor ×N |
| Similar-but-distinct NPCs | 7 pirates, varying stats | Edit side by side |
| A one-off invented at the table | 1 | A small form — the form's real case |

**The Actors page is an editable table**, not a list of things opened one at a
time. Columns: name, kind, STR/DEX/END or Hits, tags, source, a read-only health
summary, archived. Cells are edited in place; adding a row and tabbing across it
covers the one-off case without a dialog. Health details stay in the actor
editor, which owns the injury history, Clear stun and Reset health.

Four operations over the selection carry the batch cases:

- **Copy ×N** — select an actor, give a count, get N independent Actors named
  `Wolf 1 … Wolf 10`. Two clicks for the ten-chickens case, and the numbering is
  what keeps identically named rows apart.
- **Import** — from the character store; creates or refreshes definitions and
  never touches health.
- **Add to party** and **add to situation** — the table-time operation, one
  click from a multi-select.
- **Archive**.

Parties then need almost no page of their own: a list of Parties, with
membership set by selecting rows in the same grid. Situations use the same
selection plus the party import already described.

**The files remain a first-class entry point.** Editing `actors/*.json` in a
text editor and pressing Reload must work, with validation failures reported by
filename and JSON path. Python constructors, LLM-generated documents and future
external adapters all write the same validated models — no authoring surface
gets its own domain representation.

*Deliberately not added:* a template or archetype concept. An Actor is the
template and copy is the mechanism.

*Deferred until batch entry actually hurts:* a **paste box** taking TSV with a
header row, showing a validated preview with per-line errors before committing.
It is the natural path for a spreadsheet or generated document, and costs no new
syntax, but grid plus Copy ×N may well be enough. Adding it later changes no
model.

**One thing to verify first.** NiceGUI wraps AG Grid (`ui.aggrid`), which is
what makes an editable grid cheap — the single genuine advantage this plan
credited to Streamlit's `st.data_editor`. Whether its inline editing and
selection are pleasant enough to be the primary surface is worth a half-day
spike before phase 7 commits. If they are not, the fallback is the paste box and
files for batches with a per-row form for one-offs, which still meets the
twelve-animals test.

**Table columns:** Name | Party | Ini | STR | DEX | END | Stun | React | Action
| Status. ("Ini", not "Init".) Party is the row's own editable name and Ini its
own value; both are situation-local, and setting one initiative for a whole side
simply writes it into every row sharing that name.

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
incapacitation. Clear stun returns those 4 points; the 4 lethal ones stay.

**The injury history is shown per actor**, oldest first, as what each hit
actually did:

| Rounds ago | STR | DEX | END |
| ---------- | --- | --- | --- |
| 12 | – | – | −6 |
| 5 | −4 | – | −3 |

That is the first-aid view: it shows how much of the injury is still inside the
one-minute window and therefore treatable, what is already past saving, and
which wound is the urgent one. Entries from previous fights read `earlier`
rather than a count of rounds. Animals show a single Hits column instead.

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

Every actor row also has **Edit** as a correction surface, and with undo
deferred it is the only way to take a mistake back — it must therefore reach
every stored fact. Health corrections update the referenced Actor; party name,
initiative, turn state, reaction DM, last action, waiting and forfeiture flags,
prone and the round-relative recovery facts update only that Situation row.

Health is corrected by editing the injury history above — each line's
per-characteristic reductions, its kind and the round it landed — which is a
short list in any real fight, and by **Clear stun** and **Reset health** for the
wholesale cases. The editor never overwrites a current total, because a total
would then have to be reverse-engineered back into the lines that produced it.
Statuses such as stunned, unconscious and dead remain derived, so the editor
cannot create a label that contradicts the stored injuries.

**Round flow.** "New round" is an explicit command. Before or during a round,
membership rows and their party names may be changed. Initiative
is either inherited from the previous round or set now, individually or for
every row sharing a party name in one operation. Then the actors with the
highest Ini turn
**green** and may act, unless stunned or otherwise incapable. Acting turns them
**grey**; waiting leaves them green. The next Ini step then turns green as
well, joining everyone still waiting. Grey until the next round.

## Persistence

The prototype keeps its active `Situation` in NiceGUI's tab-scoped memory. A GET
or page refresh in the same browser tab must reconnect to that object rather
than construct a new encounter. This deliberately volatile state is lost when
the tab closes or the server restarts.

Phases 6–8 replace that temporary boundary with local storage under
`settings.data_dir() / 'rounds'`. **Three kinds of document, one file each, and
no separate state store:**

```text
rounds/
  actors/<actor-id>.json          — definition and health
  parties/<party-id>.json         — name and member ActorIds
  situations/<situation-id>.json  — membership rows and round state
```

An earlier draft split application-owned temporal state into a single
`state.json`, to make a mutation touching both a Situation and an Actor atomic.
That is dropped. A Situation document simply *is* the fight, prepared and then
played in place; an Actor document holds both what it is and how hurt it is.
The alternative bought one narrow guarantee at the cost of a second storage
concept, a prepared-versus-live copy step and a document nobody can read.

Consequences worth being explicit about:

- **There is no prepared-to-live transition.** Preparing a Situation is editing
  its rows before round 1; playing it edits the same rows. Reopening or
  refreshing loads the one document, so it is idempotent by construction.
- **A mutation may write two files** — an attack writes the target's health and
  the Situation's rows. Each write is atomic on its own (temp file plus
  rename), but the pair is not. A crash in the gap leaves a fight that recorded
  an attack whose damage did not land, which the editor repairs. That is an
  acceptable trade for one local single-user app, and it is not corruption.
- **Health lives beside the definition, not inside it.** Editing a definition
  must not silently discard injuries; reconciliation between a changed
  definition and existing health is an explicit validated operation.

Documents are versioned Pydantic models with generated JSON Schema. Plain files
rather than a database because the authoring workflows depend on it: a file can
be written by hand, generated by an LLM, produced by a Python constructor,
copied, diffed and kept in version control. The repository layer offers
browse/search/get/save/copy/archive, reporting filename plus JSON path on
failure and never partially applying invalid input. Manual JSON, Python
constructors, LLM output and source-system adapters all pass through that one
validation boundary.

A browser reload or a server restart mid-fight loses nothing.

### Undo — deferred

An earlier draft made a bounded snapshot stack part of v1, on the grounds that
mis-entered damage is the likeliest referee error. Correction turned out to
cover that case: every stored fact is reachable through the row editor and the
actor editor, and repairing a number is as fast as undoing it. Undo is
therefore postponed, and the row editor carries the burden instead. If
correction proves too slow at the table, the intended shape is a bounded stack
of transaction snapshots holding every document the transaction wrote.

## TDD phases

Each phase is red → green → refactor, tests first, `uvx ruff check --fix` after
each edit, `./pre-commit.sh` green before the phase is called done.

The aim is a clickable walking skeleton early, because the UI questions can only
be answered by using it. A phase is done when its behaviour can be exercised at
the table, not when it is finished for good: getting a feature into the
prototype early outranks landing it in its final shape, and phases 5–8 are
expected to revisit each other's work.

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
5. ✅ **Injury history.** The damage tracks became an ordered history of applied
   results — round, kind, and the reduction to each characteristic — stamped
   "earlier" once their Situation ends, with the per-actor first-aid view over
   it and Clear stun in the editor. Incapacitation moved onto the membership
   row as the round it ends. Every rule tested in phase 1 still holds.
6. **Persistent actor library and source boundary.** Refactor `Actor` into a
   validated definition plus its health; add typed IDs, the character-source
   Protocol and adapter, versioned JSON models, the application service, and
   the local actor repository with browse/search/get/save/copy/archive
   operations, plus Clear stun and Reset health.
7. **Parties, Situation membership, and the roster grid.** Persist standalone
   Parties and Situation membership rows; implement party import as a copy that
   forgets its origin and the editable party-name column with its collective
   initiative operation. Then build the Actors grid — inline editing, quick
   filter, multi-select — with Copy ×N, import, add-to-party, add-to-situation,
   archive, and Reload for files edited outside the app. Spike `ui.aggrid`
   first. The test is twelve similar animals or seven related NPCs created
   without filling in twelve or seven forms.
8. **Durable storage.** Persist actors, parties and situations as their three
   document kinds, each written atomically.
9. **Docs.** Note the package in `docs/ARCHITECTURE.md`; mark this plan
   complete and move it to `docs/archive/`. The rule interpretations are already
   recorded — RIC-011 (stun and lethal share one END score), RIC-012 (stun can
   never complete a kill), RIC-013 (a reaction penalises the next unspent set of
   actions) and RIC-014 (the ambush DM applies to Initiative only, round one
   only).

Rule tests go through the `Situation` / `Actor` / `DamageTrack` public API.
Repository contract tests run against an in-memory backend and the local JSON
backend. UI tests use an application service rather than reaching into storage
or domain internals directly.

## Progress so far

Implemented: `ceres/rounds/domain/` (`tracks.py`, `damage.py`,
`actor.py`, `roster.py`, `situation.py`) and `ceres/rounds/ui/` (`app.py`,
`table.py`), with **105 tests** in `tests/unit/rounds/`. Run the prototype with
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
but its modal authoring UI was rejected, and it kept initiative on its `Party`
object — which the model above rules out. Phases 6–8 replace that experiment
with persistent Actors, standalone Parties, Situation membership rows and the
full-page, file-first workflows above.

**Phase 5 — injury history.** `DamageTrack` is now generic in its injury type
and holds an ordered history instead of running totals: `apply()` resolves the
END-first cascade and the STR-or-DEX choice, records the reduction each hit
actually caused, and returns the rounds of incapacitation it inflicted rather
than counting them down itself. Every phase-1 rule test still passes, mostly
unchanged, and four deliberate breaks each produced a red. `Actor.take_damage`
stores incapacitation as the round it ends, `Situation.end()` stamps surviving
injuries as `earlier`, and `Actor.clear_stun` is the referee's hour of rest.
The editor gained the first-aid view — `Rounds ago | Kind | STR | DEX | END`,
or a single Hits column — and a Clear stun button.

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

- **First aid as a tracked action.** First aid happens inside a fight, often
  during combat, and the tracker supports it the way it supports everything
  else: Done for the medic and for the patient each round it takes, the injury
  history to see what is still inside the one-minute window, and the editor to
  record the result. It does not become a fifth action type, and the action
  vocabulary stays Melee, Ranged, reactions and Done.
- **Actions spanning more than one round** as a modelled concept
  (`03_combat.md:180-186`) — nothing tracks that an actor is partway through
  something. Postponed.
- **Fatigue** (`03_combat.md:402-410`) — referee deferred it.
- **Armour and Protection** — the referee enters damage after protection.
- **Dice** — no initiative or damage rolls.
- **Undo** — the row and actor editors cover correction instead; see the
  Persistence section for the shape it would take if that proves insufficient.
- **Healing as a rule the app applies** — first aid, medical care, natural
  healing. Clear stun and Reset health let the referee record the outcome;
  nothing computes it. Modelling natural healing would bring back the campaign
  clock, since it counts days.
- **A campaign clock, and any tracking of time or rest between fights.**
  Considered and rejected: see Time and Situation boundaries.
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
