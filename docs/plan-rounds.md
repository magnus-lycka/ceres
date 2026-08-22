# Plan: `ceres.rounds` — round-by-round encounter tracker

Status: **in progress** — phases 1–3 complete; see "Phases 1–3 results".

Tracking issue: [#56](https://github.com/magnus-lycka/ceres/issues/56)

## Purpose

A referee's bookkeeping aid for combat and other round-by-round action. It
tracks *who is involved, whose turn it is, what round we are in, what each
combatant has already done, and how hurt they are*. It does **not** resolve
attacks: no to-hit checks, no dice, no armour, no ranges, no weapons.

Rules reference: `refs/core/03_combat.md` (pages 73–96), plus
`characteristic_dm` from `refs/core/02_traveller_creation.md`.

Typical size: under 20 combatants, a handful of rounds.

## Architecture decision: NiceGUI, single Python codebase

The UI question was explored across three shapes: a REST/HTMX split like
`ceres.character.web`, a pure client-side page (vanilla JS / Svelte / Pyodide),
and a Python UI framework. The chosen shape is a **Python UI framework —
NiceGUI**, because there is no meaningful backend to design here: the whole
application is an editable table with a few side effects, and splitting it
across a network boundary invents work that does not exist.

Why NiceGUI over the alternatives considered:

- **NiceGUI 3.16 — chosen.** Event-driven callbacks (`on_click` → mutate
  encounter → refresh) match a turn tracker directly. Real per-row buttons and
  dialogs with no key gymnastics. Built on FastAPI/Starlette, which Ceres
  already depends on. Installs clean on 3.14 (~20 transitive deps). Ships a
  pytest plugin (`nicegui.testing`) for in-process UI tests.
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
    ids.py          — ActorId, PartyId (typed identifiers, never bare str)
    tracks.py       — DamageTrack base; CharacteristicTrack, HitsTrack
    damage.py       — DamageKind (lethal / stun) and damage application
    actor.py        — Actor: name, party, initiative, turn state, damage track
    initiative.py   — InitiativeMode, initiative ordering and tie handling
    actions.py      — Melee/Ranged attacks and Dodge/Parry/Dive reactions
    situation.py    — Situation: roster, parties, round counter, turn pointer
    storage.py      — Situation <-> JSON, undo stack
  ui/
    app.py          — ui.run entry point
    table.py        — the actor table, which is the whole UI (see below)

tests/unit/rounds/   — mirrors domain/, one test module per domain module
```

### Naming: Situation and Actor

This package is not only about combat. It serves any situation run in rounds
with people taking turns: a firefight, an actual fire, patching a hull breach
before the compartment empties. So the aggregate is a **`Situation`**, not an
encounter or a combat, and the thing taking a turn is an **`Actor`** — a word
that covers PCs, NPCs and animals without claiming any of them is a combatant
or a character.

### Composition over subclassing

What varies between actors is not their behaviour in the round — taking turns,
delaying and reacting are identical for everyone — but **how they absorb
damage**. So an `Actor` *has a* `DamageTrack`:

- `CharacteristicTrack` — STR/DEX/END, for Travellers and NPCs.
- `HitsTrack` — a single Hits score, for animals.

This avoids a `CharacterActor`/`CreatureActor` split, and lets a robot (Hits,
but not an animal) later reuse `HitsTrack` without pretending to be a creature.
`Actor` needs no `isinstance` checks: it asks its track.

The track owns its own rules — `apply(damage, kind)`, `is_unconscious`,
`is_dead`, `action_dm` — and the UI asks the track rather than computing
anything from raw numbers.

`domain/` may import `ceres.character.domain.characteristics` (`Chars`,
`characteristic_dm`) — a leaf module with no dependencies beyond `enum`. The
characteristic DM table is shared Traveller arithmetic and must not be
duplicated here.

Per the typed-identifier rule, the domain holds `Actor` *objects* in the
situation; `ActorId` exists for the storage and UI boundary only, and is a
frozen dataclass, not a bare string.

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
- Stun damage heals completely with one hour of rest, unlike lethal damage.

#### Interpretation: stun and lethal damage share one END score

The rules never say whether a character softened up by a stunner is easier to
knock out with lethal damage, or vice versa. Searching the community turns up no
consensus and barely any discussion, for an identifiable reason: nearly all of
it predates the 2022 Update, which replaced the old stun rule (an END check at
DM− equal to damage, failure meaning unconsciousness) with the END-reduction
rule quoted above. Mongoose's own published clarifications address the STR/DEX
split but never stun.

**Ruling: one END score, reduced by both kinds of damage.** So a character with
END 7 who has taken 5 stun damage needs 9 more lethal points to fall
unconscious, not 14; and a character with END 6 who has taken 4 lethal points is
stunned by 2 further stun points, not 6. The supporting evidence:

- Both rules reduce the same *characteristic*, not a pool: "Damage is initially
  applied to a target's END" against "Damage is only deducted from END".
- A baton round applies half of a single attack's damage as Stun
  (`refs/vehicle/21_specialised_ammunition.md:35`), so the designers expect both
  kinds on one character at once — and supplied no separate-pool bookkeeping.
- Where the authors do mean a separate accumulating total, they say so: the
  animal stun rule reads "a *cumulative* amount of damage equal to half of its
  Hits" (`03_combat.md:604`). That word is absent from the character rule.
- The Companion's optional Knockout Blow rule treats END as one running score
  reduced "from its starting value to 0" (`refs/companion/13_combat.md:71`).

The consequence is deliberately harsh: softening a target with a stunner really
does make them easier to kill.

`CharacteristicTrack` therefore keeps `lethal_end` and `stun_end` as two
buckets **for healing only** — stun points vanish after an hour's rest, lethal
ones do not. Every threshold uses the single derived value,
`END = max − lethal_end − stun_end`. No rule may branch on the buckets.

### HitsTrack (`03_combat.md:604, 652-660`)

- All damage goes to Hits, not to characteristics.
- Hits 0 → **dead**.
- Hits ≤ 10% of starting Hits → **unconscious** (stated as optional; default on,
  with a per-situation toggle).
- Hits ≤ half starting Hits → **may be driven off** (referee's option; shown as
  a hint, never applied automatically).
- Hits reduced to −(starting Hits) or worse → **body destroyed**.
- A stun weapon incapacitates a creature once *cumulative* stun damage reaches
  half its Hits.

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

*Interpretation to record:* "their next set of actions" is read as *the next
unspent set*. A reaction taken before the actor has acted this round penalises
this round's actions; one taken after they have acted penalises next round's.
This is implemented as a penalty that attaches to the next unspent action set,
not as a flat "next round" rule.

### Recovery (`03_combat.md:537-539, 366`)

- Stun incapacitation counts down automatically as rounds advance.
- An unconscious character may attempt an END check every minute (every 10
  rounds), with a cumulative DM+1 per previously failed check. The app tracks
  the cadence and the accumulated DM and prompts; the referee rolls and reports
  pass or fail.

### Roster changes

- Actors may join mid-situation with an initiative value, flagged as to whether
  they act in the current round.
- Actors may withdraw or flee: removed from the turn order, retained in the log.

## The UI — to be settled by prototype, not by argument

The shape below is what to build first and then try at the table. It is not to
be refined further on paper.

**Table columns:** Name | Party | Ini | STR | DEX | END | Stun | React | Action
| Status. ("Ini", not "Init".)

**Cell formats.** Characteristics read `current/max:DM` — `5/8:-1`, `0/6:-3`,
`9/9:+1` — so the DM lives in the cell it belongs to rather than in one
meaningless "DM" column. Stun reads `points(rounds)` — `4(11)` is four stun
points currently suppressing END with eleven rounds of incapacitation left.

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
Parry each add −1 to React.

**Round flow.** "New round" is an explicit command. On a new round: actors may
be added to a party, and initiative is either inherited from the previous round
or set now, individually or for a whole party in one operation. Then the actors
with the highest Ini turn **green** and may act, unless stunned or otherwise
incapable. Acting turns them **grey**; waiting leaves them green. The next Ini
step then turns green as well, joining everyone still waiting. Grey until the
next round.

## Persistence and undo

`Situation` serialises to and from JSON on its own (`storage.py`), independent
of NiceGUI, so it is testable with `tmp_path`. Situations are stored under
`settings.data_dir() / 'rounds'`, one JSON file each, written after every
mutation. A browser reload or a restart mid-fight loses nothing.

Undo is a bounded stack of whole-situation snapshots taken before each mutation.
With under 20 actors a snapshot is trivial, and snapshot-undo is far simpler and
more reliable than inverse operations. Mis-entered damage is the single most
likely referee error, so undo is v1, not a nicety.

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
5. **Persistence and undo.** JSON round-trip, snapshot stack.
6. **Docs.** Note the package in `docs/ARCHITECTURE.md`; mark this plan
   complete and move it to `docs/archive/`. The rule interpretations are already
   recorded — RIC-011 (stun and lethal share one END score), RIC-012 (stun can
   never complete a kill), RIC-013 (a reaction penalises the next unspent set of
   actions) and RIC-014 (the ambush DM applies to Initiative only, round one
   only).

Rule tests go through the `Situation` / `Actor` / `DamageTrack` public API —
that *is* the domain API, so no separate driver is needed, unlike
`CharacterDriver` in `ceres.character`. If UI tests start reaching into domain
internals, that is the signal to add one.

## Phases 1–3 results

Landed and committed: `ceres/rounds/domain/` (`tracks.py`, `damage.py`,
`actor.py`, `situation.py`) and `ceres/rounds/ui/` (`app.py`, `table.py`), with
**55 tests** in `tests/unit/rounds/`. Run the prototype with
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

**Two defects found by writing the rules down rather than by testing.** The
combat handouts (`handouts/combat_cards.typ`) forced several rules to be pinned
that the code had left vague, and one of those — the ambush ±6 — invalidated a
scoping decision in this plan; see the Initiative section. The other, an actor
with stun points and all characteristics at zero being unkillable, was found by
the referee asking what that state meant in practice.

**Still unrun at the table.** Phase 4 is "iterate on what the prototype
teaches", and nobody has yet used it in a real fight. Its original action model
was sketched before there was anything to try; the combat-only scope above is
the first correction from reviewing the prototype.

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
- **Importing actors from the character store** — v1 actors are entered by hand.
  The model should make a later import path a matter of populating the same
  fields, nothing more.
- **Robots as actors** — robots have Hits and their own damage rules from the
  robot book; they will reuse `HitsTrack` only once those rules are read.
- **The Companion's optional rules** — Natural Resilience, Knockout Blow, Random
  First Blood, alternative initiative, disabling wounds
  (`refs/companion/13_combat.md`). Noted as existing; not implemented.
- **Ranges, movement, cover, weapons, attack resolution** — permanently out of
  scope for this package.
