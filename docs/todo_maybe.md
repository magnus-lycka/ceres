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

## Character creation: correctness gaps and remaining rules

### Known implementation gaps (rules not yet enforced)

- **Advancement forced-leave** — if the advancement roll ≤ terms served in the
  current career, the Traveller must leave. Needs a per-career term counter and
  the pre-DM raw roll on `AdvancementEvent`.
- **Advancement natural-12-stay** — a natural 12 on the advancement dice forces
  the Traveller to stay. Same preconditions as forced-leave above.
- **Aging row ≤ −6: mental reduction after crisis** — if an aging crisis fires,
  the mental characteristic −1 from that aging row is never applied to a
  character who survives the crisis.
- **Injury table 1D damage** — rows 1 and 2 reduce a physical characteristic by
  1D. The form and auto-fill paths should be verified to record the actual die
  result rather than always using 1.
- **Skill level cap** — skills may not exceed level 4 during creation; total
  skill levels may not exceed 3 × (INT + EDU).
- **Subsequent basic training** — from term 2 onward the Traveller picks one
  Service Skill at level 0 (not all service skills at 0 as in term 1).
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
  - roll 11 Crime does not currently offer the "lose one Benefit roll or take
    the Prisoner career in your next term" choice
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

### Draft, career switching, and assignment changes

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

## Character creation: eliminate remaining semantic strings

The career YAML migration removed string-based skill/characteristic fields from
career data. Several string-based patterns remain and should be eliminated in
follow-up work packages.

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

### Replace sophont string-name lookup with typed objects

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

    class Automation(ShipPart[Ship]):
        def _basis(self) -> float:
            return self.assembly.hull ...   # ty now knows assembly is Ship

Parts that genuinely work with any `ShipBase` stay as `ShipPart[ShipBase]`.
This is a non-trivial refactor because Pydantic generics interact with
discriminated unions, but it would let us replace all the defensive `getattr`
calls in `automation.py`, `storage.py`, `habitation.py`, and `power.py` with
direct attribute access.
