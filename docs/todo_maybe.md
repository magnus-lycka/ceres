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

### Remove `skill_from_str` / `skill_class_by_name` from `events.py`

**Partial progress**: `PendingCareerSkillRoll`, `PendingSkillChoice`,
`PendingCareerSkillChoice`, and `PendingBackgroundSkills` now hold `AnySkill`
instances instead of strings. `_pick_skill_auto` handles typed instances
directly. All career event handlers and test assertions use typed skill objects.

Remaining string-based paths:

- `PendingInitialTrainingChoice`, `PendingSkillTableChoice`,
  `PendingRankBonusChoice` still inherit `options: list[str]` from
  `PendingInputBase` — because the career `SkillTable` entries and initial
  training lookups still use string names.
- `events.py:1508` — `skill_from_str(skill_name, 0)` in initial training apply
- `events.py:1884` — `skill_class_by_name(opt)` in `_build_skill_select_options`
  for the `str` branch
- `state.py:302` and `state.py:335` — `skill_class_by_name` in `skill_choices`
  and `_pick_skill_auto` for the `str` branch

Once the initial-training and skill-table paths migrate to typed `AnySkill`
entries, these call sites go away and both functions can be deleted.

### Remove `str` overload from `CharacterSummary.skill_level`

`state.py` exposes `skill_level(name: str | type[Skill])`. Remove the `str`
overload once no caller needs string-based lookup; the method should accept only
`type[Skill]`.

### Replace remaining `CareerDispatchEffect` registry dispatch with effect subclasses

The old `EFFECT_HANDLERS` dicts are gone, and raw
`CareerDispatchEffect(type='...')` entries have mostly been replaced with
`CareerHandlerBase` subclasses such as `AgentMishap2Handler`. The remaining
design smell is that these handlers still self-register under string `type`
keys and `events.py` still dispatches choice/skill-roll resolution through
`get_career_handler(context: str)`.

Replace `CareerDispatchEffect`/`CareerHandlerBase` with proper effect objects
that carry their own logic through an `apply(projection, ...)`-style interface.
The remaining context strings and handler registry should disappear; effects in
career data should be typed objects rather than string-dispatched handlers.

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
