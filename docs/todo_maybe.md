# List of potential things to do

Update todo items in this document as progress is made.
When todo items are done, please move them to docs/archive/done_todos.md

## Conditional NumberEntry visibility in input_specs

In [src/ceres/character/input_specs.py](../src/ceres/character/input_specs.py),
`NumberEntry` (and potentially other input types) has no way to express
conditions on its relevance. A common pattern is a `NumberEntry` that only
applies when a particular option was selected in a preceding `SelectEntry`.

Currently the form always treats `NumberEntry` as compulsory and the frontend
has no signal about whether a field is actually required given the current
selection state. This forces the user to fill in numbers that are irrelevant to
their actual choice.

Needed:

- A `condition` or `visible_when` mechanism on at least `NumberEntry` (and
  probably other spec types), expressing something like "this field is only
  relevant when field X has value Y"
- The frontend should use this to hide/show (or mark optional) entries that do
  not apply given current selections, rather than always rendering them as
  required

## Projection diff testing helper

Improve and document the `projection_diff` / DeepDiff-based test helper used in
character tests.

Current thought:

- keep it as a focused tool for complex state-transition tests where "nothing
  else changed" is part of the behaviour under test
- avoid turning it into broad snapshot testing or replacing simple domain
  assertions such as cash totals, skill levels, or pending presence
- make the helper less brittle before wider use, especially around volatile
  paths such as generated event IDs, pending IDs, list indexes, and serialized
  implementation details

Possible work:

- add coding-guideline notes explaining when to prefer `projection_diff` and
  when ordinary assertions or `CharacterDriver` tests are clearer
- provide a higher-level assertion helper that supports expected changes plus
  allowed volatile paths
- consider narrower helpers for summary-only or pending-only diffs
- look for more complex character state transitions where it would improve
  coverage of unexpected side effects

## Tighten character event typing

Several character-domain APIs still use broad `Any` annotations such as
`projection: Any`, `event: Any`, `form: Any`, `fulfilled_pending: Any`, and
some `career: Any`. These are mostly historical, and they make architectural
boundaries too soft.

Defer this until after the current pre-career effect migration. When picked up:

- introduce a small form-data protocol near `input_specs.py` and use it for
  `form_str`, `form_int`, and `PendingInputBase.event_from_form(...)`
- type character event handlers with `CharacterProjection`, `Event`, and
  `PendingInputBase | None`
- type `ChoiceBase.handle()` and `PendingInputBase.resolve()` with
  `CharacterProjection` and `Event`
- replace `career: Any` with `CareerData`, `type[CareerData]`, or a narrow
  protocol as appropriate
- avoid spending effort typing legacy `*Effect` classes; migrate or delete
  them instead
- consider a later scan test preventing new `projection: Any` / `form: Any`
  annotations in character-domain code, with temporary allowlists while the
  existing code is cleaned up

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

Implemented in `Scout.start_new_term()` and covered in
`tests/character/test_scout.py`: the check runs for first and subsequent terms,
offers relocation from qualifying worlds, requires it from non-qualifying
worlds, and preserves `birthworld` when the pending input is fulfilled.

Remaining before archiving:

- Align `target_constraints='world_with_scout_base'` with the RIC-006 contract
  name `world_with_imperial_scout_base`, or update RIC-006 deliberately.
- Align the required and optional reason text with RIC-006, or update RIC-006
  deliberately.

### Homeworld handling for other careers

See [docs/RULE_INTERPRETATIONS.md](docs/RULE_INTERPRETATIONS.md) — RIC-006.

Current status:

- **Implemented:** Psion offers a homeworld change at the start of each term
  when the current world has a non-X starport.
- **Still needed:** Agent, Army, Citizen, Drifter, Entertainer, Marines,
  Merchant, Navy, Noble, Rogue, Scholar, and Prisoner handling described in
  RIC-006.

## Character creation: known implementation gaps (rules not yet enforced)

- **Injury table 1D damage** — rows 1 and 2 reduce a physical characteristic by
  1D. The form and auto-fill paths should be verified to record the actual die
  result rather than always using 1.
- **Skill level cap** — skills may not exceed level 4 during creation; total
  skill levels may not exceed 3 × (INT + EDU).
- **Benefit roll bonus at rank 5–6 and "any one Benefit roll" events** — neither
  is implemented; see RIC-004.
- **Generic Pre-Career Events table must match Core literally** — the generic
  pre-career events in `ceres.character.domain.precareer.loader` and
  `PreCareerEventHandler` in
  `ceres.character.domain.precareer.precareer_events` should match the
  Traveller Core Rulebook Pre-Career Events table word-for-word in text and
  behavior. Current known deviations include:
  - roll 2 psionic-group approach is only recorded as a manual problem note;
    testing PSI and the resulting future Psion-career availability are not
    represented
  - roll 4 prank-gone-wrong is not implemented; SOC 8+, Rival/Enemy, and
    natural-2 -> Prisoner handling are all left manual
  - roll 8 political movement wrongly grants Ally + Enemy automatically instead
    of requiring SOC 8+ and only then becoming a leading figure
  - roll 10 tutor conflict drops the required 9+ skill roll and the possible
    skill increase, and grants the Rival unconditionally
  - roll 11 wartime draft always ends education and leaves the flee/draft
    decision as a manual note; it does not allow SOC 9+ to avoid the draft and
    proceed to graduation
  - roll 7 depends on the generic Life Events table, which already has its own
    correctness todo above
  - all `_PRECAREER_EVENTS` text is shortened rather than matching Core
  The current tests explicitly assert manual notes for rolls 2 and 4 and
  unconditional termination for roll 11. Replace those with tests of the Core
  outcomes, and make every Pre-Career Event entry match Core word for word.
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

IMPORTANT: Whatever is done in the scope of this todo has to consider the
overarching goal in todo "Character creation: eliminate remaining semantic
strings" to keep Traveller rules knowledge in pure domain modules such as the
career modules.

- **Draft domain logic** — the active draft flow now lives in
  `ceres.character.domain.career.entry` and career-owned `draft_assignments`;
  the web layer only renders typed pending input. Still verify the full flow
  against RIC-003 and replace remaining bespoke draft behavior, such as Drifter
  event 11, with the shared mechanism.
- **Changing careers** — normal qualification roll for new career; failure →
  draft or Drifter. Immediate re-entry restrictions are implemented and
  archived in `docs/archive/done_todos.md`.
- **Assignment changes** — within Army/Marines/Navy/Nobility/Rogue/Scholar/Scout:
  qualification roll, failure = continue same assignment. Within
  Agent/Citizen/Entertainer/Merchant: treated as a new career with full muster
  out.

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

### Consolidate career-entry state into a `TermChoices` object

`CharacterProjection` now holds three flat fields for career-entry state:
`pending_qualification_dm`, `auto_qualify_careers`, and `forced_next_career`.
These could be gathered into a `TermChoices` domain object that also tracks
draft constraints and future career-availability rules. Not urgent — the flat
fields are clear enough for now.

## University pre-career: bring Ceres fully in line with Core

University implements its basic skill choices and characteristic increases, but
its career-entry benefits are not represented with the restrictions required by
Core.

References:

- `refs/core/02_traveller_creation.md` (Pre-Career Education: University)
- `src/ceres/character/domain/precareer/university.py`
- `src/ceres/character/domain/precareer/loader.py`
- `tests/character/test_companion_precareers.py`

Known differences:

- **Animals skill choice** — Core permits Animals (training or veterinary).
  Ceres offers generic `Animals()`, which also exposes Animals (handling).
- **Qualification bonus** — Core grants `DM+1`, or `DM+2` with honours, only
  when qualifying for its listed careers. Ceres puts the bonus in the generic
  `pending_qualification_dm`, so it applies to whichever career is attempted
  next and is then consumed.
- **Commission opportunity** — Core permits a commission roll before the first
  term of a military career only when that military career is the first career
  chosen after university, with honours granting `DM+2`. Ceres records this as
  a manual problem note rather than representing the opportunity and its
  conditions.
- Replace tests of the manual commission note with tests of the actual
  restricted qualification and commission benefits.

## Military Academy pre-careers: bring Ceres fully in line with Core

Army, Marine, and Navy Academy share one implementation. Entry and basic direct
skill grants are present, but several graduation benefits remain manual or lose
their required lifetime.

References:

- `refs/core/02_traveller_creation.md` (Pre-Career Education: Military Academy)
- `src/ceres/character/domain/precareer/military_academy.py`
- `src/ceres/character/domain/precareer/loader.py`
- `tests/character/test_military_academy_precareer.py`

Known differences:

- **Army Academy service skills** — the Army Service Skills table contains a
  Drive-or-Vacc-Suit choice. Ceres deliberately skips list entries when
  granting academy service skills, so the Traveller receives neither. The
  current test explicitly asserts that choice lists are skipped.
- **Three level-1 Service Skills** — successful graduation should allow the
  Traveller to select any three Service Skills and increase them to level 1
  when entering the tied military career. Ceres leaves this as a manual problem
  note.
- **Automatic entry lifetime** — successful graduation, and failed graduation
  on a roll above 2, permit automatic entry only if the tied military career is
  the first career attempted after the academy. `auto_qualify_careers` remains
  available after attempting another career.
- **Commission opportunity** — the first tied military career should offer a
  commission roll with `DM+2`, automatically passed with honours. Failed
  graduates who use automatic entry may not make that first-term commission
  roll. Ceres records these rules as manual problem notes.
- Replace the tests that assert manual notes and skipped list entries with
  tests of the represented Core outcomes.

## Colonial Upbringing pre-career: bring Ceres fully in line with Companion

Colonial Upbringing grants most of its immediate skills, but eligibility,
graduation choices, age, and career modifiers are incomplete.

References:

- `refs/companion/07_pre_career_options.md` (Colonial Upbringing)
- `src/ceres/character/domain/precareer/colonial_upbringing.py`
- `src/ceres/character/domain/precareer/loader.py`
- `tests/character/test_companion_precareers.py`

Known differences:

- **Entry eligibility** — entry is automatic only for a homeworld of TL8 or
  lower. Ceres stores this as an `entry_requirement` string but does not enforce
  it; Colonial Upbringing is available to every character.
- **Career modifiers** — Ceres does not represent `DM+1` to qualify for Rogue
  or Scout, `DM-2` to qualify for all other careers, or the lifelong `DM-1` to
  commission and promotion checks.
- **Graduation skill choices** — Companion first increases one level-0
  pre-career skill, then grants either two other listed skills at level 1 or one
  increase to any already-possessed skill. Ceres always queues three level-1
  choices from the listed skill pool, allowing repeated or otherwise invalid
  selections and omitting the alternative existing-skill increase.
- **Honours skill choice** — the additional honours increase should apply to a
  listed skill gained at level 0; Ceres offers the whole skill pool.
- **EDU and age** — the `-D3 EDU` result and starting age of `22+2D3` are only
  manual problem notes. The current tests explicitly assert those notes.

## Merchant Academy pre-careers: bring Ceres fully in line with Companion

The Business and Shipboard curricula correctly select their broad skill tables,
but the random service skill and career-entry benefits are not faithfully
represented.

References:

- `refs/companion/07_pre_career_options.md` (Merchant Academy)
- `src/ceres/character/domain/precareer/merchant_academy.py`
- `src/ceres/character/domain/precareer/loader.py`
- `tests/character/test_companion_precareers.py`

Known differences:

- **Random Service Skill** — Companion says to roll randomly on the Merchant
  Service Skills table for a level-1 skill. Ceres lets the user choose one.
- **Automatic career entry and rank** — graduates may enter the appropriate
  Merchant or Citizen branch automatically at rank 1, or rank 2 with honours,
  only when it is their first career after the academy. Ceres records this as a
  manual problem note.
- **Advancement bonus** — `DM+1`, or `DM+2` with honours, on all advancement
  checks in Merchant or Citizen is only a manual problem note.
- The current tests explicitly assert the manual rank and advancement notes;
  replace them with tests of the represented benefits and their restrictions.

## School of Hard Knocks pre-career: bring Ceres fully in line with Companion

School of Hard Knocks implements its immediate skills and characteristic
change, but eligibility and the first-career penalty are not enforced.

References:

- `refs/companion/07_pre_career_options.md` (School of Hard Knocks)
- `src/ceres/character/domain/precareer/school_of_hard_knocks.py`
- `src/ceres/character/domain/precareer/loader.py`
- `tests/character/test_companion_precareers.py`

Known differences:

- **Entry eligibility** — entry is automatic only for SOC 6 or lower. Ceres
  stores this as an `entry_requirement` string but makes the option available
  to every character.
- **First-career penalty** — `DM-2` on promotion and commission checks in the
  first career, ending only after voluntarily leaving it, is a manual problem
  note. The current tests explicitly assert that note.
- Graduation choices should also enforce the word "other", preventing the same
  entry choices from being selected again where Companion requires other
  listed skills.

## Spacer Community pre-career: bring Ceres fully in line with Companion

Spacer Community implements most immediate graduation rewards, but eligibility
and its narrowly scoped Merchant benefit are incorrect.

References:

- `refs/companion/07_pre_career_options.md` (Spacer Community)
- `src/ceres/character/domain/precareer/spacer_community.py`
- `src/ceres/character/domain/precareer/loader.py`
- `tests/character/test_companion_precareers.py`

Known differences:

- **Entry eligibility** — entry is automatic for a size-0 homeworld; otherwise
  it requires `INT 4+`, with `DM+1` for DEX 8+. Ceres stores this as an
  `entry_requirement` string and allows automatic entry for every character.
- **Merchant Free Trader bonus** — Companion grants `DM+1` to enlist,
  commission, and promotion checks specifically in Merchant (Free Trader).
  Ceres adds `pending_qualification_dm += 1`, which applies once to whichever
  career is attempted next, and records the rest as a manual problem note.
- Graduation choices should enforce "other" skills where Companion requires
  them, rather than allowing repeated selections from the same pool.

## Agent career tables: remaining blocked items

The `Agent` career now matches Core for all text and behavior that can be
implemented. The remaining items are blocked on other infrastructure work.

References:

- `refs/core/02_traveller_creation.md` (Agent mishaps/events)
- `src/ceres/character/domain/career/agent.py`
- `tests/character/test_agent.py`

Remaining differences (blocked):

- **Mishap 5** — Ceres asks whether a Contact, Ally, or family member was hurt,
  but each choice only adds a manual problem note. Decide on an NPC-facing
  injury representation, then replace the note with the represented outcome.
- **Event 8** — text matches Core, but the handler does not actually perform
  the immediate Rogue/Citizen Event or Mishap roll, nor the Specialist skill
  table roll on success; it only records a manual problem note. The current
  tests explicitly assert these manual notes and must be replaced with tests
  of the Core outcomes when cross-career table execution is implemented.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Agent event 7 against Core.

## Army career tables: remaining blocked items

Most Army career gaps have been fixed (mishap 1 choice, event 6 injury table,
event 11 Tactics (military) specialty, event 12 commission/promote choice,
all mishap/event text updated to match Core, page refs excluded).

Remaining blocked:

- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Army event 7 against Core.

## Citizen career tables: bring Ceres fully in line with Core

The `Citizen` career has several substantial fidelity gaps in both event/mishap
text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Citizen mishaps/events)
- `src/ceres/character/domain/career/citizen.py`
- `tests/character/test_citizen.py`

Known differences:

- **Mishap 4** — both text and behavior diverge sharply from Core. Core says
  co-operating gains `DM+2` to the next career qualification roll and refusing
  gains an `Ally`; Ceres instead shortens the text and models cooperate/resist
  as `Contact`/`Rival` plus different mishap-ejection handling.
- **Event 3** — Core requires a chosen skill gain, then an `8+` roll on that
  skill with `DM+2` to the next advancement roll on success or `DM-2` to the
  next Survival roll on failure. Ceres currently only gives the initial skill
  choice.
- **Event 8** — the reward choice is now represented, but accepting incorrectly
  grants an extra Benefit roll instead of `DM+1` to one Benefit roll. Refusing
  incorrectly grants `DM+2` to the next advancement roll, while Core says it
  gains nothing.
- **Event 11** — Core grants an `Ally` and either `Diplomat 1` or `DM+4` to
  the next advancement roll. Ceres currently grants only the `Ally`.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Citizen event 7 against Core.
- **Literal text drift** — Citizen mishap/event entry text is shortened across
  multiple rows and omits Core details. Make all Citizen mishap/event entry
  text match Core word for word, excluding page references (which are
  intentionally omitted).

## Drifter career tables: bring Ceres fully in line with Core

The `Drifter` career has several meaningful fidelity gaps in both event/mishap
text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Drifter mishaps/events)
- `src/ceres/character/domain/career/drifter.py`
- `tests/character/test_drifter.py`

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
  as a manual note on failure. The current tests explicitly assert that note.
- **Event 9** — Core's risky-adventure outcome table is materially different
  from Ceres. In particular, Ceres turns the successful outcome into an extra
  Benefit roll instead of `DM+4` to one Benefit roll, and changes the middle
  outcome bands.
- **Event 11** — Core says "Roll for the Draft next term." Ceres currently
  replaces this with a manual problem note and bespoke 1D service mapping
  instead of reusing whatever proper draft handling exists elsewhere.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Drifter event 7 against Core.
- **Literal text drift** — Drifter mishap/event entry text is shortened across
  most of the tables. Make all Drifter mishap/event entry text match Core word
  for word, excluding page references (which are intentionally omitted).

## Entertainer career tables: bring Ceres fully in line with Core

The `Entertainer` career has several important fidelity gaps in both
event/mishap text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Entertainer mishaps/events)
- `src/ceres/character/domain/career/entertainer.py`
- `tests/character/test_entertainer.py`

Known differences:

- **Mishap 4** — Core says an existing `Contact` or `Ally` betrays the
  Traveller and becomes a `Rival` or `Enemy`, with a fallback `Rival` or
  `Enemy` if none exist. Ceres currently shortens the text and always applies
  `GainRivalEffect()`, never converting an existing relationship and never
  producing an `Enemy`.
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
- **Literal text drift** — Entertainer mishap/event entry text is shortened
  across multiple rows. Make all Entertainer mishap/event entry text match Core
  word for word, excluding page references (which are intentionally omitted).

## Marines career tables: bring Ceres fully in line with Core

The `Marines` career has several substantial fidelity gaps in both
event/mishap text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Marines mishaps/events)
- `src/ceres/character/domain/career/marines.py`
- `tests/character/test_marines.py`

Known differences:

- **Mishap 4** — both branches are rewritten in Ceres. Core says refusing
  ejects the Traveller, while accepting lets them stay but gain the lone
  survivor as an `Enemy`. Ceres instead gives a `Contact` on refusal and adds a
  `Deception or Persuade 8+` gate to staying after acceptance.
- **Event 6** — Core says success grants `Tactics (military)` or `Leadership`,
  while failure causes injury and a loss of `1` point from any physical
  characteristic. Ceres currently uses generic `Tactics()`, leaves the injury
  outcome as a manual note, and does not apply the required characteristic
  loss. The current tests explicitly assert the manual note.
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
- **Literal text drift** — Marines mishap/event entry text is shortened across
  most of the tables. Make all Marines mishap/event entry text match Core word
  for word, excluding page references (which are intentionally omitted).

## Merchant career tables: bring Ceres fully in line with Core

The `Merchant` career has several important fidelity gaps in both event/mishap
text and handler behavior compared with the Core Rulebook.

References:

- `refs/core/02_traveller_creation.md` (Merchant mishaps/events)
- `src/ceres/character/domain/career/merchant.py`
- `tests/character/test_merchant.py`

Known differences:

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
  The current tests explicitly assert that manual note.
- **Event 11** — Core grants an `Ally` and either `Carouse 1` or `DM+4` to the
  next advancement roll. Ceres currently grants only the `Ally`.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Merchant event 7 against Core.
- **Literal text drift** — Merchant mishap/event entry text is shortened across
  multiple rows. Make all Merchant mishap/event entry text match Core word for
  word, excluding page references (which are intentionally omitted).

## Navy career tables: bring Ceres fully in line with Core

The `Navy` career has several remaining fidelity gaps in its mishap/event
handlers and skill specialties.

References:

- `refs/core/02_traveller_creation.md` (Navy mishaps/events)
- `src/ceres/character/domain/career/navy.py`
- `tests/character/test_navy.py`

Known differences:

- **Mishap 3** — several assignment-specific Core skill specialties are lost:
  Electronics (sensors), Pilot (small craft or spacecraft), and Tactics
  (naval) are represented by generic skill objects.
- **Mishap 4** — accepting responsibility should grant a free Skills and
  Training table roll before ejection. Ceres records a manual problem note
  instead, and the current tests explicitly assert that note.
- **Event 3** — Ceres grants the initial Gambler or Deception increase but
  omits the optional `Gambler 8+` wager that can gain or lose a Benefit roll.
- **Event 8** — Core grants one of Recon 1, Diplomat 1, Steward 1, or a
  Contact. Ceres grants both a skill choice and a Contact, and e.g. 1->2 for skill, not 1.
- **Event 11** — Core requires `Tactics (naval) 1` or `DM+4` to the next
  advancement roll. Ceres offers generic `Tactics()`.
- **Event 12** — Core grants automatic success on the next promotion or
  commission roll. Ceres applies `AutoAdvanceEffect()` immediately and does not
  represent the choice or its timing.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Navy event 7 against Core.
- **Literal text drift** — Navy mishap/event entry text is shortened across
  most of the tables. Make all Navy mishap/event entry text match Core word for
  word, excluding page references (which are intentionally omitted).

## Noble career tables: bring Ceres fully in line with Core

The `Noble` career has several major event-handler substitutions and unresolved
injury outcomes.

References:

- `refs/core/02_traveller_creation.md` (Noble mishaps/events)
- `src/ceres/character/domain/career/noble.py`
- `tests/character/test_noble.py`

Known differences:

- **Mishaps 3 and 5** — failed rolls leave the Injury-table result as a manual
  problem note. The current tests explicitly assert those notes instead of a
  represented injury outcome.
- **Event 3** — Core offers a choice to refuse a duel or accept it, followed by
  SOC effects, a blade-skill roll, and possible injury. Ceres only grants a
  skill choice and omits the duel entirely.
- **Event 4** — Core specifically offers Animals (handling); Ceres offers
  generic `Animals()`, losing the specialty.
- **Event 8** — Ceres substantially rewrites the conspiracy. Refusal gives a
  Rival instead of Core's Enemy; success gives an extra Benefit roll instead
  of a Deception/Persuade/Tactics/Carouse skill increase; and failure ejects
  the Traveller instead of rolling on the Mishap table as the conspiracy
  collapses.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Noble event 7 against Core.
- **Literal text drift** — Noble mishap/event entry text is shortened across
  most of the tables. Make all Noble mishap/event entry text match Core word
  for word, excluding page references (which are intentionally omitted).

## Prisoner career tables: bring Ceres fully in line with Core

The `Prisoner` career has a particularly large mismatch in its Event 7
subtable, plus several incomplete consequences elsewhere.

References:

- `refs/core/02_traveller_creation.md` (Prisoner mishaps/events)
- `src/ceres/character/domain/career/prisoner.py`
- `tests/character/test_prisoner.py`

Known differences:

- **Mishap 3** — submitting to the prison gang records the lost Benefit roll as
  a manual problem note instead of changing muster-out state.
- **Event 5** — Core permits Deception, Persuade, Melee, or Stealth after
  joining the gang. Ceres omits Deception. The `DM+1` to Survival rolls is only
  recorded as a manual problem note rather than enforced.
- **Event 7** — Ceres' entire 1D Prison Event subtable differs from Core. Core's
  rows are Riot, New Contact, New Rival, Transfer and reroll parole threshold,
  Good Behaviour reducing parole threshold by 2, and an attack resolved with
  Melee (unarmed) 8+. Ceres instead provides a different set of labels and
  effects, including Gang Attack, Visitation, and Parole Hearing.
- **Event 9** — lawyer cost should be `Cr1000 × level²`; Ceres uses Cr1000,
  Cr2000, and Cr3000 and records payment as manual notes. On success Core
  reduces parole threshold by `1D`, while Ceres reduces it by only 1.
- **Literal text drift** — Prisoner mishap/event entry text and the Event 7
  subtable text are substantially shortened or rewritten. Make all Prisoner
  mishap/event entry text match Core word for word, excluding page references
  (which are intentionally omitted).

## Rogue career tables: bring Ceres fully in line with Core

The `Rogue` career implements several of its branching events, but still loses
important specialties and leaves some outcomes unresolved.

References:

- `refs/core/02_traveller_creation.md` (Rogue mishaps/events)
- `src/ceres/character/domain/career/rogue.py`
- `tests/character/test_rogue.py`

Known differences:

- **Mishap 3** - Ceres makes an arbitrary decision concerning which friend becomes
  a rival, instead of letting the player decide.
- **Mishap 4** — Core specifies Pilot (small craft or spacecraft) and Athletics
  (dexterity); Ceres offers generic `Pilot()` and `Athletics()`.
- **Event 3** — on a failed defence Core also grants an Enemy, and hiring a
  lawyer grants that lawyer as a Contact. Ceres implements the other
  consequences but omits both relationships.
- **Event 6** — Core grants `DM+4` to advancement for backstabbing and an Ally
  for refusing. Ceres instead grants only `DM+2` plus an Enemy for
  backstabbing, and a Contact for refusing.
- **Event 9** — failure should resolve an Injury-table roll. Ceres records a
  manual problem note instead, and the current tests explicitly assert it.
- **Event 10** — Core allows the Traveller to wager a Benefit roll with
  `Gambler 8+`, gaining or losing a Benefit roll. Ceres only grants Gambler 1
  and omits the wager.
- **Event 11** — Core requires `Tactics (military) 1` or `DM+4` to the next
  advancement roll. Ceres offers generic `Tactics()`.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Rogue event 7 against Core.
- **Literal text drift** — Rogue mishap/event entry text is shortened across
  most of the tables. Make all Rogue mishap/event entry text match Core word
  for word, excluding page references (which are intentionally omitted).

## Scholar career tables: bring Ceres fully in line with Core

The `Scholar` career's more complicated events are largely represented, but its
injury handling and some skill specialties still differ from Core.

References:

- `refs/core/02_traveller_creation.md` (Scholar mishaps/events)
- `src/ceres/character/domain/career/scholar.py`
- `tests/character/test_scholar.py`

Known differences:

- **Mishap 2** — Core requires rolling twice on the Injury table and taking the
  higher result. Ceres applies a single generic Injury-table effect.
- **Mishap 4** — Core specifically offers Athletics (dexterity or endurance);
  Ceres offers generic `Athletics()`.
- **Mishap 5** — giving up should retain the current term's Benefit roll, while
  starting again should lose all Benefit rolls from the career. Ceres calls
  muster-out with the current term lost on give-up, while the start-again
  branch does not remove the career's Benefit rolls.
- **Event 8** — on success Core grants `DM+2` to a Benefit roll as well as a
  skill increase and an Enemy; on failure it grants an Enemy and loses one
  Benefit roll. Ceres omits the Benefit-roll modifier/loss in both branches.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Scholar event 7 against Core.
- **Literal text drift** — Scholar mishap/event entry text is shortened across
  most of the tables. Make all Scholar mishap/event entry text match Core word
  for word, excluding page references (which are intentionally omitted).

## Scout career tables: bring Ceres fully in line with Core

The `Scout` career implements most of its branching events, but several skill
choices lose the specialties or breadth required by Core.

References:

- `refs/core/02_traveller_creation.md` (Scout mishaps/events)
- `src/ceres/character/domain/career/scout.py`
- `tests/character/test_scout.py`

Known differences:

- **Event 3** — failure now prevents re-enlisting in Scouts at the end of the
  term. Success should grant only Electronics (sensors) 1, but Ceres grants
  level 1 in every Electronics specialty.
- **Event 4** — Core offers Animals (riding or training), Survival, Recon, or
  any Science at level 1. Ceres offers generic `Animals()` and only
  `SpaceScience()` rather than the full Science choice.
- **Event 6** — Core specifically offers Pilot (small craft) among the skill
  choices. Ceres offers generic `Pilot()`.
- **Event 7** — inherits the generic Life Events correctness gap; once the
  generic Life Events todo is fixed, re-check Scout event 7 against Core.
- **Literal text drift** — Scout mishap/event entry text is shortened across
  most of the tables. Make all Scout mishap/event entry text match Core word
  for word, excluding page references (which are intentionally omitted).

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
