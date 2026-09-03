# Plan: `ceres.rounds` — round-by-round situation (combat) tracker

Status: **in progress**. The tracker is a **browser application in `web/`**,
built in Svelte with its rules in TypeScript beside it. The NiceGUI prototype
under `src/ceres/rounds/domain/` and `src/ceres/rounds/ui/` is superseded and
kept only until nothing wants it; see "Architecture decision" and "Progress so
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
- **Remain open to practical authoring workflows.** In-app editing, copying,
  and assistant-proposed bundles all operate on the same actor, party and
  situation concepts, and all pass through the application's own service. The
  plan does not require one of them to be the sole authoring method.

The model and its names should make these different concepts and lifetimes
obvious. Protocols, JSON schemas, repositories and UI widgets are means of
achieving these goals, not goals in themselves.

Rules reference: `refs/core/03_combat.md` (pages 73–96), plus
`characteristic_dm` from `refs/core/02_traveller_creation.md`.

Typical live Situation: under 20 actors, a handful of rounds. The reusable
Actor library may be much larger.

## Architecture decision: a browser application in Svelte

The tracker is a **static SvelteKit application in `web/`** — Svelte 5,
TypeScript, zod, `adapter-static`, `ssr = false` — with the Traveller rules
beside it as a pure TypeScript module under `src/lib/rules/`. There is no
server and no API: the browser holds the rules, the state and the store client.

The boundary worth having is **domain versus UI, not client versus server**. A
network hop is an expensive way to enforce a module boundary, especially
between two halves that always change together, and every usual reason to split
is absent here — one referee, no shared state, no trust boundary, no secrets,
no computation a browser cannot do. So `rules/` imports nothing from Svelte and
touches no DOM, exactly as the Python `domain/` package did; the difference is
that the discipline is now enforced deliberately rather than by the language
boundary. See [ARCHITECTURE.md](ARCHITECTURE.md) ("The browser front end") and
[WORKING_AGREEMENT.md](WORKING_AGREEMENT.md) for how that boundary is kept.

The one thing that would change this: an outside client needing to *play*
rather than author — applying damage, advancing rounds — which would put the
rules back where it can reach them.

### How this decision was reached

The UI question was first explored across three shapes: a REST/HTMX split like
`ceres.character.web`, a pure client-side page (vanilla JS / Svelte / Pyodide),
and a Python UI framework. **NiceGUI was chosen**, on the reasoning that this is
a local single-process application and that a separate network API would invent
work that did not exist. Client-side JavaScript was rejected for putting the
rules outside pytest and adding an npm toolchain to a repo that had none.
Streamlit (whole-script rerun), Gradio (ML demo I/O), Dash (callback ceremony),
Anvil (a platform dependency) and notebooks (poor to drive mid-fight) were
rejected on their own terms and remain so.

**Using the prototype overturned that choice.** The evidence the original
comparison did not have:

- The library screens want a real data grid. Arrow-key cell navigation is what
  makes a grid feel like a control rather than a styled table, and NiceGUI could
  only reach it by driving AG Grid from Python.
- That driving is blind. Grid event payloads are not what their own JavaScript
  suggests, and three bugs in a row came from guessing at them.
- It is also untestable. NiceGUI's in-process test user cannot see a single
  grid cell, and anything read back from the grid is a JavaScript round trip
  that times out in tests. The framework's testing advantage disappeared exactly
  where we leaned on it hardest.
- What was wanted next — chips inside a cell — meant writing JavaScript inside
  Python strings, with no types, no linting and no tests: the worst of both
  worlds rather than a compromise.

A spike built one screen — Parties, with the in-cell tag chips — in Svelte 5
over a native Svelte grid, to be judged by use. It succeeded, and the rules
moved to the browser with the UI. The cost the original comparison correctly
predicted was paid: the rules are no longer in pytest, and the repo now has an
npm toolchain. What was bought is a grid whose custom cells are ordinary
components, and component tests that run in a real browser and can see them.

**The framework choice remains reversible in the same way it always was.** The
rules and the entity schemas are framework-free modules with their own Node-run
test suite; the Svelte components are a view over them. Replacing the UI, or
the grid library under it, does not move the domain.

Dependencies: `svelte`, `@sveltejs/kit`, `zod`, `@svgrid/grid`, `idb-keyval`,
and `vitest` with a Playwright browser provider. `./pre-commit.sh` runs the web
gate — `eslint --fix`, `prettier --check`, `svelte-check`, `vitest`, `vite
build` — alongside the Python one.

## Module layout

```text
web/src/
  lib/
    schema/         — one zod definition per entity: the TypeScript types, the
                      runtime validation, and the published JSON Schema
      actor.ts      — Actor definition variants, ids, injury history
      party.ts      — standalone reusable Party
      situation.ts  — membership rows, round counter, turn state
      import.ts     — the id-free proposal bundle and its receipt
      tags.ts       — the tag vocabulary shared by actors and parties
    rules/          — the domain, as pure functions over plain data
      rounds/
        vitality.ts  — the lethal cascade, stun, unconscious, dead, live DMs
        health.ts    — how a track reads: current/max, DMs, stun points
        lifecycle.ts — joining, withdrawing, ending a situation
        situation.ts — initiative ordering, turn state, the round counter
        criticals.ts — severity from an attack's Effect
        library.ts   — questions asked of a roster
      ehex.ts        — the shared notation
    store/          — where entities live and how they travel
      files.ts      — the FileStore interface every backend implements
      idb.ts        — the local copy, in IndexedDB, with its change log
      github.ts     — the data repository, over the GitHub contents API
      sync.ts       — reconciliation, and what blocks it
      library.ts    — the only way in and out of stored entities
      session.svelte.ts — the app-wide session: sync timer, import results
    actors/ parties/ situations/ tags/ grid/
                    — Svelte components, one grid per entity kind
  routes/           — pages, thin: actors, parties, situation, sync
```

Tests sit beside what they test: `*.test.ts` runs in Node, `*.svelte.test.ts`
and `*.browser.test.ts` in Chromium.

Nothing above the rules reaches into storage and nothing below the components
knows about them: pages call `Library` and the rules modules, and the grids take
entities and report edits.

**Superseded:** `src/ceres/rounds/domain/` and `src/ceres/rounds/ui/` are the
NiceGUI prototype, kept for reference until nothing wants them.
`src/ceres/rounds/library/` is a Python reader of the same store layout — one
JSON file per entity under a directory named for its kind, plus
`counters.json` — and the two implementations must keep agreeing about it.

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
round an actor's incapacitation ends, and the round they fell unconscious. When
the Situation ends, those facts end with it (see Time and Situation
boundaries).

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
  rounds), with a cumulative DM+1 per previously failed check. **The app only
  says when a check is due.** It does not roll, and it records no outcome: a
  passed check is the referee clearing the Unconscious marker.
- Nothing therefore counts the failures. The row stores one fact — the round
  they went down — and both the cadence and the DM follow from it: a check that
  fell due while the marker still stood is a check that was failed, so the DM is
  `minutes down − 1`.
- Clearing the marker restores consciousness without healing anything, which is
  what the rule says. STR or DEX stays at 0 and the impaired DMs stand.
- Animals get no END check. The rule is a Traveller's, and `HitsTrack` has no
  END; the referee may still clear a beast's marker by their own ruling.
- All of this is round-relative, so it belongs to the Situation and dies with
  it.

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
- Actors support add, edit, copy ×N with numbered names, and delete.
- Reusable Parties support add, copy, edit, delete and bulk member changes.
- Adding a Party to a Situation copies its name and its members at that moment
  into new membership rows, and keeps no tie to the Party afterwards.
- Rows may be added, removed or reassigned to another party name without
  changing any reusable Party. The party name may also be cleared.
- An actor added mid-situation receives fresh situation-local state, while its
  existing persistent health state is used unchanged.
- Withdrawing from a Situation removes only the membership row.
- **Anything may be deleted, with no questions asked.** There is no archive
  flag and no referential guard: this is a single-user tool and the referee is
  an adult. Every reader instead copes with a stale reference — a membership
  row whose Actor is gone shows dashes in the columns it can no longer fill,
  and keeps the situation-local facts that were always its own.

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
| PCs | 4–6, rarely change | Typed once: a name and three numbers |
| A pack of identical creatures | 10 chickens, 5 wolves | Copy one actor ×N |
| Similar-but-distinct NPCs | 7 pirates, varying stats | Edit side by side |
| A one-off invented at the table | 1 | A small form — the form's real case |

**The Actors page is an editable table**, not a list of things opened one at a
time. Columns: name, kind, STR/DEX/END or Hits, tags, source, a read-only health
summary. Cells are edited in place; adding a row and tabbing across it
covers the one-off case without a dialog. Health details stay in the actor
editor, which owns the injury history, Clear stun and Reset health.

Four operations over the selection carry the batch cases:

- **Copy ×N** — select an actor, give a count, get N independent Actors named
  `Wolf 1 … Wolf 10`. Two clicks for the ten-chickens case, and the numbering is
  what keeps identically named rows apart.
- **Add to party** and **add to situation** — the table-time operation, one
  click from a multi-select.
- **Delete**.

Parties then need almost no page of their own: a list of Parties, with
membership set by selecting rows in the same grid. Situations use the same
selection plus the party import already described.

**The files remain a first-class entry point**, now via the data repository
rather than a local working copy: `actors/*.json` can be edited in the repo and
arrives on the next sync, with validation failures reported by path and JSON
path. Python constructors, LLM-generated documents and future external adapters
all write the same validated models — no authoring surface gets its own domain
representation, and none of them is a way around `Library`.

*Deliberately not added:* a template or archetype concept. An Actor is the
template and copy is the mechanism.

**The grid question is answered.** Whether an editable grid could be the primary
surface was the open risk here, and it is what the NiceGUI/AG Grid combination
failed at. The grids are now **SvGrid** components — one per entity kind, typed,
with cell navigation, in-place editing, multi-select and range paste. The
**paste box** this plan held in reserve for batch entry turned out to be
unnecessary: pasting TSV into a range is the same gesture without a second
surface. **Copy ×N** with automatic numbering is not built — there is a
Duplicate button that makes one copy at a time — and remains the wanted answer
for ten identical chickens.

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

**The injury history is shown as what each hit actually did**, oldest first:

| Rounds ago | Kind | STR | DEX | END |
| ---------- | ---- | --- | --- | --- |
| 12 | lethal | — | — | -6 |
| 5 | lethal | -4 | — | -3 |

That is the first-aid view: how much of the injury is still inside the
one-minute window and therefore treatable, what is already past saving, and
which wound is the urgent one. Kind is a column because a stun line and a wound
are not the same thing to a medic. Entries from previous fights read `earlier`
rather than a count of rounds.

**Triage is a view of its own, not something reached one actor at a time.**
Deciding whom to treat first is a question about everybody, so the Run page
switches between **Round** and **Injuries**: the same table of actors, but with
each actor's wounds listed beneath them — Name | Party | Rounds ago | Kind |
STR | DEX | END — and Done and Edit still to hand. An actor with several wounds
occupies several lines, which is most of the signal at a glance; an unhurt one
keeps a line reading `unhurt`, so absence is never ambiguous. Rows carry the
same green and grey as the round table, because acting from here must give the
same feedback. Animals show their Hits in the END column, as they do in the
round table; the per-actor view inside Edit, which need not be uniform, labels
that column Hits.

Ordering is the round table's own, not worst-first. Sorting by severity needs a
definition of severity — total points, most recent, or only what is still
treatable — and that is a decision to make after using this, not before.

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
across rounds as a removable **Prone** tag, cleared without recording an action
or introducing movement-action bookkeeping.

**Markers are cleared by their ×, never by clicking the label.** Prone,
Unconscious and anything like them state a fact the referee will want to read
several times before they retire it, and losing one to a stray click on the row
costs more than the extra precision costs. Because a marker sits on a row whose
background changes with turn state, each states its own colour rather than
inheriting the row's: a due END check is the one that shouts.

**Unconscious is a marker, not a status.** Damage puts it there; only the
referee takes it away, because that is what a passed END check means. Until
then it carries the reminder — `Unconscious`, then `Unconscious (END check)`
once a minute has passed, then `Unconscious (END check DM+2)` as the failed
checks pile up.

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

Entities live in **IndexedDB in the browser**, and are pushed to and pulled from
the data repository by an explicit sync. Edits land locally and immediately;
nothing waits for the network, and closing the tab or losing connectivity loses
no work. **Three kinds of document, one file each, and no separate state
store:**

```text
actors/<actor-id>.json          — definition and health
parties/<party-id>.json         — name and member ActorIds
situations/<situation-id>.json  — membership rows and round state
counters.json                   — the id allocator
imports/<bundle>.json           — what installing a proposal allocated
inbox/<bundle>.json             — proposals waiting to be installed
```

The same paths are what the repository holds, so a file store is the whole
storage abstraction: `IdbFileStore` locally, `GitHubRepository` remotely, and a
memory one for tests. Nothing above `Library` learns which it is talking to.

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
  the Situation's rows. Each write lands on its own; the pair is not one
  transaction. A crash in the gap leaves a fight that recorded an attack whose
  damage did not land, which the editor repairs. That is an acceptable trade
  for one local single-user app, and it is not corruption.
- **Health lives beside the definition, not inside it.** Editing a definition
  must not silently discard injuries; reconciliation between a changed
  definition and existing health is an explicit validated operation.

Documents are zod-defined models with generated JSON Schema, kept as plain files
rather than in a database because files diff, review and version-control
cleanly. `Library` offers list/get/save/copy/delete, reporting the path plus the
JSON path on failure and never partially applying invalid input.

**The application owns its persistence, and nothing else writes to it.** Files
being readable is a convenience for inspection and history, not an interface.
Every writer — the UI, an importer, an assistant — goes through `Library`, so
validation, id allocation and every invariant apply once, in one place. An
earlier draft of this plan invited an LLM to write store files directly; that
was a backdoor around the boundary this section exists to draw.

A browser reload mid-fight loses nothing.

### Where the data lives: a private data repo

The durable store is a **private** repo — `magnus-lycka/ceres-data`, separate
from the public `magnus-lycka/ceres` code repo — reached over the GitHub
contents API rather than as a git working tree, because the application is a
page in a browser and has no filesystem to keep a clone in. Sync runs on a
timer, on demand, and when the page is being left.

This answers a requirement local storage alone cannot: next week's session may
be run from a different laptop, or the same one may have died. Point the app at
the repo, sync, and both the state and its history are there.

Git rather than a synced folder because history is a feature here, not a
side effect: the injury log already records what each hit did, and commits let
the referee see what the state actually was when someone recorded it wrongly.
It also reports a divergence instead of silently leaving a conflicted copy —
when both sides have moved, sync **blocks** rather than merging, because losing
a session's play to a clever automatic resolution would be worse than being
asked to sort it out.

The credential is a fine-grained personal access token scoped to that one repo
with `Contents: Read and write` and nothing else, entered in the app. The code
repo is public, so it carries neither the token nor the data repo's name.

The data repo is created directly rather than forked: a fork of a public repo
cannot be made private under any owner. It holds the store, an `inbox/`, and a
stub workflow that calls a reusable workflow living in this repo, so the import
logic stays in the codebase where it is reviewed and tested.

### Getting data in from outside: issues, not file writes

An assistant or person may propose new reusable library content — one Party
containing any supported kind of Actor — by filing an issue on the private data
repository. CI validates the proposal and writes only an id-free bundle under
`inbox/`; the application allocates ids and installs it during the next sync.

This is deliberately the whole outside interface for now. It needs no running
service, works from a machine that has never run Ceres, and leaves a reviewable
record. The bundle contract, GitHub workflow, replay-safe installation and the
narrow rule for pulling an inbox-only commit while local changes wait are
specified in [plan-library-import.md](plan-library-import.md).

### Undo — deferred

An earlier draft made a bounded snapshot stack part of v1, on the grounds that
mis-entered damage is the likeliest referee error. Correction turned out to
cover that case: every stored fact is reachable through the row editor and the
actor editor, and repairing a number is as fast as undoing it. Undo is
therefore postponed, and the row editor carries the burden instead. If
correction proves too slow at the table, the intended shape is a bounded stack
of transaction snapshots holding every document the transaction wrote.

## TDD phases

Each phase is red → green → refactor, tests first, `./pre-commit.sh` green
before the phase is called done.

The aim is a clickable walking skeleton early, because the UI questions can only
be answered by using it. A phase is done when its behaviour can be exercised at
the table, not when it is finished for good: getting a feature into the
prototype early outranks landing it in its final shape, and phases 5–8 are
expected to revisit each other's work.

**Phases 1–5 were done in Python and are being re-earned in TypeScript.** The
rules they settled did not change when the language did — the reasoning behind
each is still the record — but a ✅ below means "decided and tested in the
prototype", not "shipped in `web/`". What is built where is in "Progress so
far".

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
6. ✅ **Persistent Parties, Actors and Situations.** One zod definition per
   entity, one JSON file each behind a `Library` that does not leak its
   storage, plus the grids over them.
7. ✅ **Parties, Situation membership, and the roster grid.** Standalone
   Parties and Situation membership rows; party import as a copy that forgets
   its origin, and the editable party column with its collective initiative
   operation by range paste. The Actors grid has inline editing, keyboard cell
   navigation, multi-select, tags, paste and Duplicate. The twelve-animals test
   is met by pasting and duplicating one at a time; Copy ×N with automatic
   numbering is not built.
8. ✅ **Durable storage.** Actors, parties and situations in IndexedDB, synced
   to the private data repo over the GitHub contents API, with a change log,
   commit-based conflict detection, and a sync page that reports what is
   waiting and what is blocked.
9. **The issue-driven library import channel
   ([#61](https://github.com/magnus-lycka/ceres/issues/61)).** Implement
   [plan-library-import.md](plan-library-import.md): the generic issue form,
   reusable validation workflow, `inbox/`, inbox-aware sync and replay-safe
   installation into the Actor and Party libraries. **Milestone 1 is done** —
   the bundle and receipt schemas, the replay-safe installer, and installation
   after a clean sync. Milestones 2 and 3 — the issue form, the validating
   workflow, inbox-only reconciliation and feedback on the issue — are not
   started, so a bundle reaches the inbox only by being committed by hand.
10. **Docs.** Note the package in `docs/ARCHITECTURE.md`; mark this plan
    complete and move it to `docs/archive/`. The rule interpretations are
    already recorded — RIC-011 (stun and lethal share one END score), RIC-012
    (stun can never complete a kill), RIC-013 (a reaction penalises the next
    unspent set of actions) and RIC-014 (the ambush DM applies to Initiative
    only, round one only).

Rule tests go through the `$lib/rules` functions and the schemas, in Node.
Store tests run against `MemoryFileStore`, with the IndexedDB and sync
behaviour tested in a real browser. Component tests render in Chromium and
assert what a referee can see and reach, not how a grid is configured.

## Progress so far

**The application is `web/`.** Run it with `npm run dev`; the pages are Actors,
Parties, Situation and Sync. Its suites are `npm test` — the `rules` project in
Node, the `components` project in Chromium.

Built there: the entity schemas with their generated JSON Schema; the rules
modules for vitality, health display, criticals, situation membership,
initiative and turn state, and the situation lifecycle; the Actors, Parties and
Situation grids with keyboard navigation, in-place editing, multi-select, tag
chips and range paste; a `Library` over a `FileStore`, with IndexedDB locally
and the private data repo over the GitHub contents API, a change log, sync with
commit-based conflict detection, and installation of inbox proposals after a
clean sync.

Not yet in `web/`: the combat dialog and applying damage, the injury and triage
views, the round-by-round markers, and the correction editors. Those rules are
settled — phases 1–5 below are their record — but they are not on a screen yet,
so **the browser app cannot yet run a fight**.

**The Python prototype**, `ceres/rounds/domain/` and `ceres/rounds/ui/`, still
runs with `uv run python -m ceres.rounds.ui.app` on port 8081, with **105
tests** in `tests/unit/rounds/`. It is superseded; it is kept because the
phase 4–5 behaviour above lives only there for now.
`ceres/rounds/library/` is a separate thing: a Python reader of the same store,
still current.

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

**Then three corrections from using it.** Reaching a pure read through an editor
is wrong when the medic wants to compare everyone, so triage became its own
**Injuries** view beside the round table. Tracking the END check's pass, fail
and accumulated DM was more than the app should own: it says when a check is
due, and clearing the marker is how the referee reports success — which leaves
one stored fact, the round they went down. And markers now clear only by their
×, in colours of their own, after a stray click lost one.

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

**The move to the browser.** The grid was what forced it — see "How this
decision was reached" — and the rewrite went library-first rather than
tracker-first, because the library screens were both the reason for the move
and the part with no working implementation to lose. So `web/` now has the
entity schemas, the Actors, Parties and Situation grids with tags and paste,
IndexedDB with a change log, and sync with the private data repo; the round
table's rules are ported (vitality, initiative, turn state, criticals,
lifecycle) but the play surfaces over them are not built yet.

**Phase 9, milestone 1 — proposals install themselves.** A bundle in `inbox/`
is validated against the same zod schema CI will use, installed as one
replay-safe operation that allocates ids and writes a receipt before the
entities, and the sync page reports what was imported and what could not be.
Interruption at any step resumes to exactly one result; a bundle that reappears
after being consumed installs nothing. What is missing is everything that puts
a file in the inbox: no issue form, no workflow, no repository automation.

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
- **Any synchronous AI interface** — an MCP server or HTTP API letting an
  assistant create or change entities on demand. The issue channel covers the
  one wanted workflow, needs nothing running, and works from a machine that has
  never been set up. Revisit only if preparation starts happening at the table.
- **Healing as a rule the app applies** — first aid, medical care, natural
  healing. Clear stun and Reset health let the referee record the outcome;
  nothing computes it. Modelling natural healing would bring back the campaign
  clock, since it counts days.
- **A campaign clock, and any tracking of time or rest between fights.**
  Considered and rejected: see Time and Situation boundaries.
- **Robot combat rules** — robots have Hits but their own damage, stun,
  protection and critical-hit rules. Their damage track waits until those rules
  are read; it must not inherit animal `HitsTrack` semantics by convenience.
- **The Companion's optional rules** — Natural Resilience, Knockout Blow, Random
  First Blood, alternative initiative, disabling wounds
  (`refs/companion/13_combat.md`). Noted as existing; not implemented.
- **Ranges, movement, cover, weapons, attack resolution** — permanently out of
  scope for this package.
