# Rule Interpretations

Ceres targets **Mongoose Traveller 2nd Edition (MgT2)**, latest versions of each rule book unless otherwise stated.

Where the *Core Rulebook* and *High Guard* conflict, High Guard takes precedence.

Material from earlier MgT2 printings (notably *High Guard* 2016) that was removed
or replaced in later editions is treated as out of scope. See RIS-008.

This document records deliberate rule interpretations, exclusions, and normalizations used in Ceres.

It is intentionally sparse to begin with. Entries should be added when we review
source-derived behaviour and need to distinguish between:

- supported behavior
- deliberately ignored source material
- deliberate interpretations
- unresolved TODOs

The goal is to document decisions that are intentional but not obvious from the
code alone, especially where published examples, third-party designs, or older
rules material differ from our implementation.

## Conventions

- Organise all rule interpretations in the sections listed below.
- Add new rule interpretations within their section in order with stable, ascending identifier numbers starting at 001.
- If a rule interpretation doesn't fit in an existing section, consult repo owner.

| Prefix | Section content       | Primary Ceres Module(s)         |
| ------ | --------------------- | ------------------------------- |
| RIS-   | Spacecraft            | make.ship                       |
| RIC-   | Characters and Combat | character, rounds, make.sophont |
| RIR-   | Robots                | make.robot                      |
| RIG-   | Gear                  | gear                            |
| RIV-   | Vehicles              | make.vehicle                    |
| RIW-   | Worlds                | worlds, make.world, make.sector |

## Rule Interpretations for spacecraft

### RIS-001 Stores And Spares Are Not Modelled As Reserved Design Tonnage

Ceres does not currently model stores and spares as a separate reserved tonnage
entry in ship designs.

Where source material gives recommended or expected stores/spares capacity, that
is treated as design guidance rather than a hard reduction in cargo capacity.
This may be surfaced as informational or warning output in the cargo section,
but it is not installed as a separate ship part.

### RIS-002 Passenger Baggage Is Not Modelled As A Separate Design Allocation

Ceres does not model passenger baggage/storage space as a separate line item in
the ship design.

The working interpretation is:

- Middle Passage or lower in stateroom accommodation keeps baggage within the
  passenger's room allocation.
- Low berths are assumed to include space for the passenger's permitted small
  personal effects.
- High Passage reduces practical cargo availability by 1 ton per passenger in
  operation, but this is not reserved as fixed design tonnage.

This means baggage does not appear as a dedicated installed component in the
spec. If we later add explicit expected passenger manifests by class, this may
instead drive informational output, validation, or cargo-availability warnings.

### RIS-003 Small Ships Do Not Require Separate Maintenance Crew

For crew-role calculation, Ceres follows the High Guard prose in
`refs/HG_CREW_ROLES.md` for separate maintenance staff on smaller ships.

The working interpretation is:

- commercial ships below 1,000 tons do not require a distinct `MAINTENANCE`
  role
- military ships below 500 tons do not require a distinct `MAINTENANCE` role
- once those thresholds are reached, separate maintenance crew scales by ship
  tonnage

On smaller ships, maintenance duties are assumed to be covered by engineering
staff rather than listed as a separate crew position.

### RIS-004 Steward Requirements Depend On Planned Passenger Manifest

Steward staffing is treated as an operational requirement driven by the planned
passenger manifest, not by theoretical maximum berth capacity.

In practice, this means Ceres only derives steward requirements from explicitly
modelled occupants, rather than assuming that every available middle berth or
low berth is occupied for crew-planning purposes.

The steward requirement is interpreted as required `Steward` skill levels, not
raw headcount:

- each High Passage passenger counts as 10 Middle Passage passengers
- required steward level is `ceil((middle + 10 * high) / 100)`
- Ceres does not assume routine recruitment above `Steward 3`

When more than 3 total steward levels are needed, Ceres splits the requirement
across multiple stewards rather than assuming a single higher-skill recruit.

### RIS-005 Retro- And Proto-Tech Pricing For Ship Computers

Ceres models retro- and proto-tech pricing for ship Computer and Core hardware
via a `retro_levels` or `proto_levels` field on each computer object.

**Retro-tech** (`retro_levels=N`, N ≥ 1): The computer is built at a lower
cost by using technology that has become routine N TL levels above the
computer's standard introduction TL. Cost is divided by 2ᴺ. The ship must be
at TL `computer.tl + N` or higher to apply this discount; if not, a TL error
is raised.

**Proto-tech** (`proto_levels=N`, N ∈ {1, 2}): The computer is built before
its standard introduction TL, at 10ᴺ times cost. The effective minimum ship TL
is reduced by N levels accordingly.

**Software TL cap (retro only)**: A retro-tech computer can only run software
whose required TL does not exceed `ship.tl − retro_levels`. Installing a
Computer/10 at retro-2 in a TL11 ship yields an effective software TL of 9.
Software that requires TL10 or higher will raise a TL error against that
computer, even though the ship is TL11. See RIS-012 for the rationale.

When a reference ship uses retro-computer pricing (`Retro*` rows in source
exports), document the `retro_levels` value in the relevant test case.

### RIS-006 Marines On Liners Can Represent Shipboard Security Staff

When a commercial passenger ship or liner source lists `Marines` in its crew
manifest, Ceres does not interpret that alone as proof that the vessel should
be modelled as a military craft.

The working interpretation is that such `Marines` can represent embarked
security personnel: guards, police, response teams, or similar shipboard
security staff attached to a commercial operation.

This affects how source-derived test cases should be read:

- explicit `Marine` roles may appear on commercial ships
- their presence does not, by itself, imply military crew rules or military
  ship classification
- where relevant, the source test case should document that interpretation

### RIS-007 Small Craft Operation Fuel Uses Rounded Tankage And Actual Endurance

Ceres treats `OperationFuel.weeks` as the minimum requested endurance, not
necessarily the exact endurance that will appear in the final design.

For operation-fuel tankage, Ceres uses this policy:

- ships under `100 dTons`: round fuel tankage up to `0.1 dTon`
- ships of `100 dTons` or more: round fuel tankage up to whole `dTons`

This is our interpretation of the *Small Craft Catalogue* wording that "it
makes sense for small craft to be able to use less than a ton of fuel for
their tiny power plants", rather than a direct restatement of the simpler Core
/ High Guard minimum-one-ton wording.

The consequences are:

- `OperationFuel.tons` is the actual allocated tankage
- the rendered spec text uses the actual endurance that tankage supports
- if rounding up yields additional full four-week periods, Ceres reports the
  longer endurance rather than hiding it

### RIS-008 Pre-2022 Rules Items Without Current-Edition Equivalents Are Not Modelled

Ceres follows *High Guard* (2022) as its rules baseline. Items — equipment,
software packages, ship options — that appeared in earlier MgT2 printings but
were removed or replaced in 2022 and have no equivalent in the current rules
set are simply not modelled.

This is not a statement that those items were invalid. It is a scope decision:
we do not add code or model entries for things that no longer exist in the
edition we target.

**Where a source ship uses such items**, document the exclusion or substitution
in the relevant TCS entry and omit or remap accordingly. For ship-specific
mappings, see `TEST_CASE_ASSEMBLIES.md`.

### RIS-009 DELETED

Miscategorised.

### RIS-010 Carried Craft — Displacement, Performance Sizing, and Crew

**Ship displacement**: A ship's displacement is its own internal hull volume
only. Craft on docking clamps are external to the hull and are not counted.
The cost of the hull, and cost of armour etc should not rise because something
is sometimes placed outside the hull.

**Drive and jump-fuel sizing**: High Guard states that when a craft occupies a
docking clamp, drives and jump fuel must be sized for the combined tonnage of
both vessels. This applies only to craft actually transported with the ship
during transit. Craft internally housed within the hull (full hangar, internal
docking space) are already within the hull volume and do not add to this figure.
A clamp that merely holds a craft at berth without transporting it likewise does
not affect drive sizing.

**Clamp type**: The docking clamp type (I–V) is determined by the craft's
shipping tonnage, not chosen independently.

**Clamp hardware tonnage**: The clamp fitting itself (Type I: 1 t, Type II: 5 t,
Type III: 10 t, Type IV: 20 t, Type V: 50 t) counts against hull capacity as an
internal fitting.

**Crew**: The crew rules distinguish craft the ship's crew is responsible for
from craft merely being transported (e.g. a jump shuttle being ferried, or an
empty clamp). Only craft under the host ship's care contribute to crew counts:

| Crew role   | What counts                                                                               |
| ----------- | ----------------------------------------------------------------------------------------- |
| Pilot       | +1 per carried spacecraft that requires its own pilot                                     |
| Engineer    | The craft's drive and power-plant tonnage adds to the total used to derive engineer count |
| Maintenance | The craft's tonnage adds to the total used to derive maintenance count                    |

**Reference note**: Google Sheet stat blocks sometimes embed the external
craft tonnage inside the clamp entry (e.g. showing 45 dTon for a Type II clamp
carrying a 40 dTon Pinnace). The rules are equally satisfied by treating the
hull as 360 dTon and sizing drives for 400 dTon combined; both produce the same
drive sizes and fuel requirements.

### RIS-011 Administrators And Commercial Sensor Operators Use Floor Division

The crew table states "1 per 2,000 tons" for administrators and "1 per 7,500
tons" for commercial sensor operators. The general rule says "whenever a crew
calculation results in a fraction, always round up," which would yield at least
1 of each role for any ship.

Ceres uses floor division for both roles (`displacement // 2_000` and
`displacement // 7_500`), so these roles are absent on ships below those
tonnage thresholds.

The rationale is that "1 per N tons" expresses a workload rate, not a minimum
staffing requirement. A ship of 1,000 tons does not carry half an administrator;
it carries none, because the role is not warranted at that scale. The explicit
"per full" qualifier on officers ("1 per full 20 crew") confirms the intended
reading for rate-based crew assignments. The general round-up rule is interpreted
as applying within a calculation once the rate has produced a non-zero quotient,
not as mandating at least one of every listed role on every ship.

This is consistent with RIS-003 (maintenance thresholds) and with the prose
context for small ships, where a single multi-skilled pilot covers many duties.

### RIS-012 Retro-Tech Ship Computers Cap The Effective Software TL

A retro-tech computer (`retro_levels=N`) is not simply a cheaper version of
the same hardware. It is hardware built to an older standard — one that was
current N TL levels ago. Such hardware cannot take advantage of software
advances that appeared after that older standard was current.

The working interpretation is:

- a ship at TL X installing a computer at retro level N operates that computer
  at effective TL `X − N`
- software whose required TL exceeds `X − N` cannot run on that computer, even
  though the ship itself is at TL X
- the ship still needs to be at TL `computer.standard_tl + N` to apply the
  retro discount (you need the higher TL to recognise that the older design is
  now routine)

**Example**: A TL14 ship installing a Computer/20 (standard TL12) at
`retro_levels=2` saves 75% on the hardware (÷4 cost), but the computer
operates at effective TL 12. Software requiring TL13 or TL14 cannot be loaded
onto that computer.

This is a capability trade-off, not just a pricing footnote. A ship designer
who wants TL14 software must use a standard or proto-tech computer — retro
pricing comes at the cost of software reach.

### RIS-013 Basic Ship Systems Power Is Rounded Up To The Nearest Integer

*High Guard* states that basic ship systems power equals 20% of total hull
tonnage (10% for non-gravity hulls). No rounding rule is given in the text.

The *Small Craft Catalogue* stat blocks consistently display integer power
values, and its 6-ton designs (e.g. Freight Handler Pod, Civilian Hopper)
show Basic Ship Systems = 2, which equals ceil(6 × 0.2) = ceil(1.2) = 2.

Ceres therefore applies ceiling rounding:

    basic_ship_systems_power = ceil(displacement × 0.2)

For non-gravity hulls, the 50% reduction is applied before rounding:

    basic_ship_systems_power = ceil(displacement × 0.2 × 0.5)

**Note on reference data**: The reference data for the Belt Racer
(6-ton light hull) shows Basic Ship Systems = 1. Since the official Small
Craft Catalogue sources consistently show 2 for a standard 6-ton hull, and
the reference data may use floor rather than ceil, the Belt Racer stat block deviation
is treated as a reference data difference, not evidence of a light-hull modifier.
The rules text on light hulls (refs/hg/05_specialised_hull_types.md) states
only cost and hull-point effects — no power modifier.

### RIS-014 Spinward Extents Sterling Fission

`refs/spinext/59_arcturus.md` defines Sterling fission power plants as sealed,
long-duration fission generators that require no external fuel but must be
replaced at the end of their lifespan. Ceres models the TL6, TL8, and TL12 rows
from that table, including the two-ton minimum size and the post-lifespan loss
of one Power per ton per additional year of use.

The same rules state that Sterling fission power plants cannot directly operate
jump drives, although they may charge batteries for jump-drive use. Ceres reports
this as a warning on a Sterling fission plant installed in a ship with a jump
drive.

This is a ship-building model only. Ceres assumes a newly installed, in-lifespan
plant unless a design explicitly asks for aged equipment; past-lifespan behaviour
is exposed as derived helper logic rather than included in normal build totals.
Once the lifespan is exhausted, the plant is not refuelled or reused: the whole
sealed package is replaced and the spent unit is radioactive waste.

### RIS-015 Stored Battery Power Is Not Continuous Generation

High-efficiency batteries are stored power, not continuous generation. Ceres
therefore includes their tonnage, cost, and Power capacity in the Power section,
but does not add battery capacity to `Ship.available_power`. A combat round or
scenario layer may choose how much stored power is discharged in that round.

### RIS-016 Armoury Recommendations Apply To Military Ships With Scale

High Guard describes armouries as secure weapons and equipment stores for ships
carrying large numbers of marines or soldiers. One ton of armoury is required
for every 25 crew members or five marines.

Ceres treats this as a recommendation for `military=True` ships only. Civilian
ships and ordinary small craft are assumed to rely on a normal ship's locker
unless an armoury is explicitly installed by the source design.

For military ships, Ceres derives the recommendation as:

    ceil(non_marine_requirement + marine_count / 5 - epsilon)

where:

    non_marine_requirement = max(0, non_marine_count - 12) / 25

This treats ordinary crew as a rounded-to-nearest 25-person equipment burden
with a small-ship offset: one- or two-person military craft do not receive a
foolish armoury warning when a ship's locker is adequate, while ships with a
meaningful military crew start receiving armoury recommendations around 13
non-marine crew. Marines contribute immediately because their equipment
requirement is the specific use case called out by the armoury rule. The small
epsilon prevents floating-point noise from turning exact boundary cases into an
extra armoury.

### RIS-017 Collapsible, Mountable, And Drop Tanks Are Operational Equipment

High Guard describes collapsible fuel tanks as flexible bladders stored in cargo
space, mountable tanks as cargo-space conversions that take weeks to add or
remove, and drop tanks as external tanks used and jettisoned around jump
operations. These all change the ship's usable cargo/displacement state
depending on whether they are installed, carried, full, empty, attached, or
jettisoned.

Ceres does not model these as static ship construction components. They are
treated as loose equipment and operational state, analogous to carrying spare
fuel containers in cargo space rather than permanently installing another fuel
system in the ship design.

Implications:

- `FuelSection` does not include collapsible fuel tanks, mountable tanks, or
  drop tanks.
- published references to these items should be handled as source notes or
  future cargo/equipment state, not as rows in the static ship spec.
- mountable-tank installation/removal time and cargo-space conversion are
  operational/campaign state rather than static construction state.
- drop-tank jump penalties, jettison survival, streamlining effects, and thrust
  recalculation while attached are operational rules outside the current
  ship-building model.

### RIS-018 Fuel Tank Compartments Count As Real Cargo Volume

High Guard states that fuel tank compartment tonnage is deducted from ship
fuel tankage rather than total hull tonnage. Ceres treats this as an official
or deceptive specification convention rather than the physical construction
model.

In Ceres, jump fuel and operation fuel requirements are calculated from the
actual fuel the ship must carry. A fuel tank compartment then consumes real
cargo volume in addition to that fuel, because the compartment occupies space
inside what is officially presented as fuel tankage but does not itself hold
fuel.

Implications:

- `FuelTankCompartment` is modelled in the Cargo section, not as extra usable
  fuel.
- it reports the High Guard detection and access notes.
- where a power plant fuel rate is available, it notes how much the hidden
  compartment would overstate official operation endurance without changing the
  ship's real operation fuel.

### RIS-019 Firmpoint Range Limits Are Operational Combat Scope

High Guard states that firmpoint-mounted weapons have limited targeting range
compared with hardpoint/turret installations.

Ceres treats this as an operational combat limitation, not a ship-construction
calculation. Firmpoint range limits therefore do not alter installed tonnage,
cost, Power, hardpoint/firmpoint capacity, or crew requirements in
`ceres.make.ship`.

The build model still applies construction-relevant firmpoint effects:

- firmpoints provide lower mount capacity than hardpoints
- fixed-mount weapons on firmpoints use the firmpoint Power reduction
- firmpoint missile racks carry four missiles rather than twelve where this is
  modelled as installed ammunition/storage

Detailed targeting range, attack eligibility, and combat range-band effects
belong in a future combat/operations model rather than the static ship spec.

### RIS-020 Turret And Fixed-Mount Compatibility Uses The High Guard Weapon Table

High Guard presents fixed mounts and turrets together and states that they use
the same type of weapons. Ceres therefore treats the weapons in the High Guard
Turret Weapons table as valid for both fixed mounts and turrets.

Ceres models the construction restrictions stated by the rules:

- one turret or fixed mount may be attached to each hardpoint
- fixed mounts may carry up to three weapons on ships
- small craft firmpoint fixed mounts may carry only one weapon
- turrets carry one, two, or three weapons according to turret type
- small craft may upgrade one firmpoint to a single turret

Ceres does not add extra construction-time compatibility restrictions beyond
those rules. Combat-use details such as only firing one weapon type from a
mixed turret in the same attack are operational rules outside the static ship
spec.

### RIS-021 Non-Gravity Hull Spin Layout Is Outside Ship Construction Scope

High Guard states that non-gravity hulls can use specific configurations that
allow the hull to spin in order to generate gravity if desired. Ceres models
the construction effects that are explicit and measurable in the ship design:

- 50% hull cost reduction
- basic ship systems Power reduced to half the normal requirement
- maximum displacement of 500,000 tons

Ceres does not model hull dimensions, spin radius, deck orientation, Coriolis
effects, comfort, or whether a particular layout is operationally useful as a
rotating habitat. Those are layout and runtime concerns, not static
construction costs. A non-gravity ship may therefore be a poor or inconvenient
operational design without being an invalid Ceres build.

## Rule Interpretations for characters and combat

### RIC-001 Science, Art, Profession, And Language Are Groups Of Distinct Broad Skills

The *Traveller Companion* (2024) defines **Science**, **Art**, and
**Profession** as groups of broad skills. Each broad skill is a distinct,
top-level skill with its own specialisations; it is not a speciality of a
generic parent skill. For example, Ceres models `Space Science (Planetology)`,
not `Science (Planetology)`, and does not model a generic `Science` skill.
**Language** follows the same model: each language is a distinct broad skill,
not a speciality of one generic `Language` skill. A level in one language
grants no level or familiarity in any other language.

The groups are:

| Generic name | Available broad skills                                                                             |
| ------------ | -------------------------------------------------------------------------------------------------- |
| Science      | Life Science, Physical Science, Robotic Science, Social Science, Space Science                     |
| Art          | Performing Art, Creative Art, Presentation Art                                                     |
| Profession   | Colonist, Freeloader, Hostile Environment, Spacer, Sport, and Worker Profession                    |
| Language     | One distinct skill per language, such as Language Galanglic, Language Bilanidin, or Language Zdetl |

This model applies wherever Ceres names a skill, not only during character
creation. Expert software names the concrete broad skill and its optional
specialisation, and older robot or source labels such as `Science (Planetology)`
are normalised to the corresponding concrete skill, `Space Science
(Planetology)`.

**Implications for character creation:**

The *Core Rulebook* (2022) career tables use the generic group names — for
example, “Gain Science 1” or a result of “Language” on a skill table. Such an
entry means that the player chooses one of the available broad skills in that
group; it never grants a flat skill or speciality named `Science`, `Art`,
`Profession`, or `Language`.

- Skill table entries that list "Science" (e.g. Scout advanced education row 5,
  Scholar service skill row 6) offer all five broad sciences as choices; the
  player picks one.
- Event or mishap text that says "increase Science by one level" (e.g. Scholar
  event 11, Scholar mishap 3) likewise means player chooses which broad science.
- Rank bonuses listed as "Science 1" or "Science 2" (e.g. Scholar / Field
  Researcher / Scientist rank 1 and 5) defer the grant until the player chooses
  the science.
- The Physician career has a separate rank table from Field Researcher /
  Scientist because the Core Rulebook lists different rank bonuses for it (rank 1
  = Medic 1 instead of Science 1).

This avoids hard-coding a particular broad skill or speciality where the source
only names the group.

### RIC-002 Colonial Upbringing Lasts Exactly 8 Years (Two Standard Terms)

The *Traveller Companion* (2024) states that a Colonial Upbringing Traveller
"is aged 22+2D3 years when entering their first career" and that graduation
"Increase END by +1, and decrease EDU by −D3."

The 22+2D3 formula produces a variable age of 24–28 and implies the Traveller
spends 6–10 years beyond the standard 18 in the precareer. Ceres normalises
this to exactly **two standard terms of 4 years each** (8 years total), giving
a fixed starting age of **26**.

The model mirrors the *Core Rulebook* Prisoner career mechanic: the first term
is the Colonial Upbringing precareer itself (entry, event, graduation); the
**second term is mandatory** — there is no career choice. The second term
applies the EDU −1D3 effect from the graduation benefits block. END +1 is
applied at graduation of the first term.

**Rationale:**

- The variable "22+2D3" is treated as flavour text describing the range a
  real colonial upbringing might last; a fixed 8-year / 2-term model is
  consistent with that range at its midpoint (22+2×2 = 26).
- Making the second term mandatory and explicit is the cleanest way to apply
  the EDU −1D3 roll as a discrete, trackable event in the event-sourced model.
- It keeps character age deterministic during creation, which simplifies
  ageing-roll scheduling.

**Consequences:**

- A Colonial Upbringing character always begins their first career at age 26.
- The EDU −1D3 roll is resolved during the mandatory second term, not at first
  graduation.
- The DM-2 on career entry and DM-1 on commission/promotion that the rules
  attach to Colonial Upbringing still apply throughout all subsequent careers.

### RIC-003 Draft Eligibility Is Career-Owned; Merchant Draft Is for a Specific Assignment

The *Core Rulebook* draft table names six careers (Navy, Army, Marines, Merchant,
Scout, Agent) in fixed order 1–6. This table is implicitly human-centric and
Imperium-specific. Different sophonts or cultures might draft into different
careers in different order.

E.g. Darrians also include pre-carrers in the draft, see `Aliens of Charted Space vol 3`.

Ceres interprets draft eligibility as a career-owned predicate:
`is_in_draft(character_summary) -> int`. The draft table is constructed at
runtime by collecting all careers that return > 1, in alphabetical order.
For the six standard core-rulebook draftable careers, all return 1 regardless
of input; all other careers return 0 by default. This would lead to a draft
table like this: 1 Agent, 2 Army, 3 Marine, 4 Merchant, 5 Navy, 6 Scout.
When we add Darrian support from `Aliens of Charted Space vol 3` people with
a homeworld in the Darrian Confederation will get a Draft Table looking like this:
1: Guard, 2: Military Academy, 3: Militia 4: Navy, 5: University, 6: University.
I.e. pre-career university will return 2 on is_in_draft(character_summary) if
Allegience of their homeworld is DaCf (Darrian Confederation).
Similarly, the Drifter alternative to the draft is declared as
`is_draft_alternative(character_summary) -> bool`. When a Traveller fails
qualification and wants to avoid the draft, any career returning `True` from
this predicate is offered as an alternative.

For **Merchant**, the draft is for the specific Merchant Marine assignment rather
than a free choice of assignment. The career expresses this as a `draft_assignment`
field alongside its `is_in_draft` declaration.

For five of the six draft careers (Navy, Army, Marines, Scout, Agent), any
assignment within the career may be chosen on entry via draft.

### RIC-004 Benefit Roll Bonus: Rank 5–6 Applies to All Rolls; "Any One Roll" Events Allow Post-Roll Choice

Two distinct sources can grant DM+1 to benefit rolls:

**Rank 5–6 DM+1**: Careers that grant DM+1 to all Benefit rolls at rank 5 or 6
apply this bonus unconditionally to every benefit roll from that career. The
player does not choose when to use it.

**"DM+1 to any one Benefit roll"** (e.g. Agent event 4): A scheduled effect
granting DM+1 to one specific benefit roll. Ceres interprets "any" as
post-roll: the player rolls the benefit die (1–6) and, if this effect is
active, is offered both the rolled result and the rolled result +1 as choices.
Selecting the higher result consumes the scheduled effect.

**Interaction**: If the character already has the rank 5–6 DM+1 (which applies
to all benefit rolls), a "any one roll" scheduled effect is redundant and is not
additionally applied. The effect is consumed without offering a separate choice.

### RIC-005 Skill Labels Use the Achieved Specialisation Only; Level-0 Grants Are Written Without Specialisation

When a character gains a skill from a career table or basic training, Ceres
represents the outcome as a single label of the form `Skill-N` or
`Skill (Specialisation)-N`.

**Specialised skills at level > 0**: Only the chosen specialisation is named.
`Gun Combat (Slug)-1` means Slug reached level 1 in this step; the other
specialisations (Archaic, Energy) are implicitly at whatever level they were
before (including zero). Writing them out would be `Gun Combat (Slug)-1,
Gun Combat (Archaic)-0, Gun Combat (Energy)-0`, but that is unnecessarily
verbose. Ceres uses the short form.

**Level-0 grants**: When basic training or a similar rule grants a skill at
level 0, the entire skill is added to the sheet without choosing a
specialisation. Even where the source table names a specialisation — e.g.
"Pilot (small craft)" in Drifter/Scavenger basic training — a level-0 grant
means only "you now have this skill on your sheet". The result is written
`Pilot-0`, not `Pilot (Small Craft)-0`.

### RIC-006 Homeworld Requirements and Options for Pre-careers and Careers

The *Core Rulebook* does not state explicitly that a Traveller must reside on a
world with a specific installation in order to serve a career term. However,
the nature of certain services implies it: a Scout is assigned to and operates
from a Scout installation, and a term of service begins with the character
reporting to one.

Ceres models this as a **start-of-term homeworld trigger**. At the beginning
of every career term (both the first and all subsequent re-enlistment terms),
a career may inspect the character's current homeworld and raise either a
required or optional homeworld change. **No end-of-term trigger is modelled**:
when a term ends, the character is free; it is the start of the *next* term —
the act of entering service again — that creates the requirement or option.

#### General trigger kinds at term start

- **Required change**: current homeworld does not meet the career's base
  requirement. The character must relocate to a qualifying world before the
  term can proceed.
- **Optional change**: current homeworld already qualifies, but the career
  offers the opportunity to relocate to another qualifying world. The character
  may decline and stay put.

Both raise the appropriate homeworld-change event (required or offered) with
`source_kind='career_entry'` and set `target_constraints` to describe which
worlds are valid targets.

#### Scout: Imperial Scout Base (S) or Way Station (W)

*Core Rulebook*, trade chapter: "**Scout (S):** A scout base offers refined
fuel and supplies to scout ships." "**Way Station (W):** A large Imperial
Interstellar Scout Service installation dedicated to the x-boat communication
network and servicing scout ships."

Scouts serve from and are supplied by these installations. A term of Scout
service therefore requires the character to be based at a world that carries
at least one of these facilities.

**Base-code check**: `'S' in world.bases or 'W' in world.bases`

(`TravellerMapWorld.bases` is a string of concatenated single-character codes,
e.g. `'NW'` for a world with a Naval base and a Way Station.)

**At the start of each Scout term:**

- If the current homeworld **does not** contain `S` or `W`: raise
  `HomeworldChangeRequiredEvent` with
  `target_constraints='world_with_imperial_scout_base'`.
  The character cannot proceed until relocated.

- If the current homeworld **does** contain `S` or `W`: raise
  `HomeworldChangeOfferedEvent` with the same `target_constraints`.
  Scouts move around; the option to relocate to a different Scout installation
  is always present even when the existing homeworld qualifies.

**Reason text (required)**: `"Scout service requires a homeworld with an
Imperial Scout Base (S) or Way Station (W)."`

**Reason text (optional)**: `"Scout service: you may relocate to another
world with an Imperial Scout Base (S) or Way Station (W)."`

**Allegiance**: The `S` and `W` codes identify Imperial Scout Service
facilities. A non-Imperial Scout career (e.g. Zhodani, Darrian) would need
its own base-code set and this rule would not apply; that is TBD.

#### Agent: Corporate and Intelligence if Starport

Law Enforcement stays put. Corporate and Intelligence get
HomeworldChangeOfferedEvent at term start if Starport A-D.
No world constraints.

#### Army: Stay put

No offers about homeworld change while serving in planetary army.

#### Citizen

Corporate: Changing Homeworld allowed every term if starport
Worker: Changing to Industrial (remark In) Homeworld allowed every term if starport
Colonist: Must move to Agricultural or Garden world (remark: Ag, Ga)

#### Drifter: Dependent on assignment

Barbarian: No change of Homeworld

Wanderer: Changing Homeworld required every term

Scavenger: Changing Homeworld allowed every term if starport

#### Entertainer

Changing Homeworld allowed every term if starport

#### Marine: Imperial Navy Base (N) or Navy Depot (D)

Same as Scout service, but Navy Base (N) or Navy Depot (D)

#### Merchant

Changing Homeworld allowed every term if starport

#### Navy: Imperial Navy Base (N) or Navy Depot (D)

Same as Scout service, but Navy Base (N) or Navy Depot (D)

#### Noble

Changing Homeworld allowed every term

#### Rogue

Changing Homeworld allowed every term if starport

#### Scholar

Changing Homeworld allowed every term if starport

#### Prisoner: Can escape and be transferred

Success with Event 3, escape implies forced homeworld change if starport
Event 7 - 4, tranferred, escape implies forced homeworld change if starport

#### Psion

Changing Homeworld allowed every term if starport (I.e. starport class not X)

### RIC-007 Career Rank Titles Persist Until Replaced

A blank title at a career rank means that rank grants no new title. It does not
remove the title earned at an earlier rank.

Ceres therefore displays the latest non-empty title at or below the Traveller's
current rank on the applicable assignment or officer rank table. For example,
an Adept with the titles `Initiate` at rank 1, `Acolyte` at rank 3, and `Master`
at rank 6 remains an `Initiate` at rank 2 and an `Acolyte` at ranks 4 and 5.

This interpretation affects title presentation only. Rank bonuses and other
effects still apply solely at the exact rank where they are listed.

### RIC-008 Individual Psionic Powers Are Out Of Scope For ceres.character

`ceres.character` models the Psion career and the PSI characteristic (including
the initial PSI test, talent selection, and PSI strength). It does not model the
individual powers within each talent — their PSI costs, range, duration, checks,
or PSI recovery rules.

Psionic powers are operational gameplay mechanics that belong in a future
play/encounter model, not in the character-creation domain.

### RIC-009 No basic training repeated for matching career after military academy

Military academy means that the character does the basic training before the
first career term. If corresponding career is conducted after mailitary academy,
e.g. Marine Career after Marine Academy, the character will select a skill table
for a skill roll before survival on the first term, as if it wasn't the first term.

### RIC-010 No basic training repeated after assignment switch

New assignments in the Agent, Citizen, Entertainer and Merchant careers are considered
to be new careers, but not with regards to Basic Training. If you e.g. switch from
Citizen Worker career to Citizen Corporate career, you don't get basic training again.

### RIC-011 Stun And Lethal Damage Reduce One Shared END Score

The rules do not say whether a character softened up by a stunner is easier to
knock out with lethal damage, or whether prior injury makes someone easier to
stun. Community discussion offers no consensus and barely addresses it, because
almost all of it predates the 2022 Update, which replaced the old stun rule (an
END check at DM− equal to the damage, failure meaning unconsciousness) with the
END-reduction rule now printed at `refs/core/03_combat.md:366`.

Ceres rules that there is **one END score**, reduced by both kinds of damage.
A character with END 7 who has taken 5 stun points needs 9 more lethal points to
fall unconscious, not 14; a character with END 6 who has taken 4 lethal points is
stunned by 5 further stun points rather than needing a fresh 6.

Reasons:

- Both rules reduce the same *characteristic*, not a pool: "Damage is initially
  applied to a target's END" (`:264`) against "Damage is only deducted from END"
  (`:366`).
- A baton round applies half of one attack's damage as Stun
  (`refs/vehicle/21_specialised_ammunition.md:35`), so both kinds are expected on
  one character at once, with no separate bookkeeping supplied.
- Where the authors mean a separate accumulating total they say so: the animal
  stun rule reads "a *cumulative* amount of damage equal to half of its Hits"
  (`:604`). That word is absent from the character rule.
- The Companion's optional Knockout Blow treats END as one running score reduced
  "from its starting value to 0" (`refs/companion/13_combat.md:71`).

`CharacteristicTrack` therefore keeps lethal and stun END damage in two buckets
**for healing only** — stun points are cleared by an hour of rest (`:366`),
lethal ones are not. Every threshold uses the single derived value.

The incapacitation countdown is separate from the stun damage that suppresses
END. When the countdown reaches zero, the END loss remains until one hour of
rest. A later stun hit is measured against that reduced END; if END is already
zero, every point of the new hit is excess and incapacitates for the same number
of rounds. A hit that merely reduces END to exactly zero has zero excess and
therefore causes zero rounds of incapacitation. If another hit lands during an
existing countdown, its newly calculated duration replaces the remaining
duration only when it is longer; durations do not add together.

### RIC-012 Stun Damage Can Never Complete A Kill

Following RIC-011, an actor may reach 0 in all three physical characteristics
while part of the END loss is stun damage. The Core Rulebook says a Traveller
with all three physical characteristics at 0 has been killed (`:266`), but it
also says Stun weapons "deal non-lethal damage, incapacitating a living target
rather than killing it" (`:366`).

Ceres resolves the conflict in favour of the Stun trait: **death requires all
three physical characteristics to be reduced to 0 by lethal damage.** An actor
whose STR and DEX are gone and whose END is only zero because of a stunner is
unconscious and stunned, not dead, and recovers that END after an hour's rest.
Otherwise a stunner could finish someone off, which the trait explicitly rules
out.

In that state every characteristic reads zero, so the damage cascade has nowhere
left to put further lethal damage — yet stun may still be occupying END capacity
that lethal damage has never claimed. **Further lethal damage claims it**,
displacing the stun points one for one, and death follows once END's full
maximum has been lost to lethal damage. Without this, an actor with any stun
points and all three characteristics at zero could never be killed at all.

The invariant this preserves: stun changes *when an actor falls unconscious*,
but never *how much lethal damage it takes to kill them*. An actor with
STR 4/DEX 4/END 4 dies to 12 points of lethal damage whether or not they were
stunned first.

### RIC-013 A Reaction Penalises The Next Unspent Set Of Actions

Every Reaction costs DM−1 "on their next set of actions"
(`refs/core/03_combat.md:192`). Ceres reads "next" as *the next unspent set*: a
reaction taken before the actor has acted this round penalises this round's
actions, while one taken after they have acted penalises next round's. The
penalty attaches to the next unspent action set rather than always to the
following round.

### RIC-014 The Ambush DM Applies To Initiative Only, And Only In Round One

`refs/core/03_combat.md:44` states the ambush modifier in two sentences that are
not parallel:

> The side that is aware that combat is about to begin gains DM+6 to its
> **Initiative check** for the first round only. The side that is not aware it is
> about to be attacked suffers **DM-6** for the first round only.

The first names the check; the second does not. Read literally, the penalty might
apply to every check the ambushed side makes in the first round, not merely to
Initiative. No official clarification exists, and community sources are split —
most of them describing the older Mongoose system, in which prepared combatants
instead receive an automatic 12.

Ceres rules that **both modifiers apply to the Initiative check alone**, and
adjust the standing Initiative score for round one only; from round two both
sides revert to their unmodified scores.

Reasons:

- The paragraph's subject is established by the first sentence, and the second
  continues it by ellipsis. That is the plainest reading of the two together.
- A DM-6 on *every* check would remove the ambushed side from the round rather
  than disadvantage it. In a 2D system an Average (8+) task is impossible at
  DM-6 without a positive modifier, and a Traveller with +2 from skill and
  characteristic succeeds 2.8% of the time against 72.2% unmodified. Had that
  been intended, "may not act in the first round" would be the natural wording.
- Reading it this way also removes the apparent conflict with `:81` ("Every
  Traveller retains the same Initiative score for every combat round"): the
  score is rolled once and kept, and the ambush modifier is a round-one
  adjustment to it rather than a re-roll.

The consequence for `ceres.rounds` is that surprise is **not** a status carrying
a penalty to unrelated rolls. It is a one-round adjustment to initiative
ordering, and needs no per-actor DM of its own.

**Note:** *Traveller: Battlefield Dev* (Mongoose, 2024) replaces only the two
initiative paragraphs on p.73 and leaves this ambush text standing, so the
interpretation is required under either initiative system.

### RIC-015 Animal Stun Uses The Same Points-And-Overflow Model As Character Stun

The animal rule says that a Stun weapon incapacitates an animal when cumulative
stun damage reaches half its starting Hits (`refs/core/03_combat.md:604`), but
does not state a duration. Ceres normalises this to the character Stun rule so
that stun has one operational meaning for every living actor:

- Stun points suppress current Hits, but cannot take them below half starting
  Hits. For odd starting Hits, this floor is rounded down.
- Damage beyond that floor is overflow, and incapacitates the animal for the
  same number of rounds.
- A later stun hit is measured against the current Hits. If lethal injury has
  already reduced Hits to half or below, every stun point is overflow.
- When a countdown reaches zero, stored stun continues to suppress Hits. More
  stun then causes overflow immediately. A new countdown replaces the remaining
  countdown only if it is longer; durations do not add.
- One hour of rest clears both the stored stun and its countdown (`:366`).

Lethal damage and stun share the displayed Hits score down to the stun floor,
but stun must remain non-lethal. As lethal damage claims capacity currently
occupied by stun, it displaces those stun points one for one. Injury-based
unconsciousness, death, and destruction therefore still require lethal damage;
stun never reduces the amount needed to reach those states.

The table uses the same `X(Y)` notation for characters and animals: `X` is the
stun currently suppressing END or Hits, and `Y` is the remaining overflow
countdown.

## Rule Interpretations for robots

### RIR-001 Manipulator Cost Credit — 20% BCC Cap Applied to Combined Net

The rule (*Robot Handbook*, p.25) states: "Removing a manipulator lowers the cost of the robot by Cr100 multiplied by
the size of the robot but no more than 20% of the Base Chassis Cost."

Ceres applies a single combined cap across all manipulator credit sources (removal and downsize). The net manipulator
cost effect is:

    net = sum(m.cost for m in manipulators) − 2 × std_cost
    net = max(net, −0.20 × BCC)

A negative `net` is a credit. The 20% cap limits the total credit from all manipulator changes combined, not per
manipulator. For a Size 3 Wheels robot (BCC = Cr800), the cap is Cr160 regardless of how many manipulators are removed
or downsized.

This interpretation changes the Domestic Servant total from Cr420 (uncapped, former implementation) to Cr860 (capped).
The source sheet that informed the original expected cost used an uncapped formula; Ceres now follows the explicit rule
text.

The same cap applies to resized standard manipulators: if both are downsized the combined credit is still bounded at 20%
of BCC.

### RIR-002 Robot Costs Reported Without Editorial Rounding

The Robot Handbook presents final robot costs that are sometimes rounded to one or two significant figures. Ceres
reports the exact calculated cost from all rule components and does not apply editorial rounding.

Where a source stat block differs from the Ceres-computed total, the source value is recorded in the test file's
`_expected` SimpleNamespace and the Ceres value is set as an override immediately after, with a comment documenting the
discrepancy.

Known discrepancies following this pattern are recorded in the relevant test files. The Basic Lab Control Robot
discrepancy is additionally explained in RIR-003. The cause of other discrepancies has not been traced to a specific
rule or omission and is left as an open question in the test file comment.

### RIR-003 Skill Package Costs And Default Suite Substitution Costs Are Included In Total Cost

**Skill packages** (`refs/robot/35_skill_packages.md`): Standard skill packages installed in Advanced (or higher) brains
carry an explicit cost: base cost × 10^level, where base cost comes from the Standard Skill Packages table. These costs
are not included in the brain hardware cost and are added separately to the robot's total.

**Default suite substitutions** (`refs/robot/10_default_suite.md`): The five standard default suite items are included
in the Base Chassis Cost. Only three alternatives substitute at no additional cost: Drone Interface, Transceiver 5km
(basic), and Video Screen (basic). Any other zero-slot item installed as a default suite substitution adds its own cost
to the robot total.

The *Basic Lab Control Robot* source stat block (Cr12000) omits both the Electronics (remote ops) 1 skill package
(Cr1000) and the two non-free default suite substitutions (Transceiver 500km (improved) Cr1000, Video Screen (improved)
Cr500). The Ceres-computed total is Cr14500. See the `_expected.cost` override in
`tests/robots/test_lab_control_robot_basic.py`.

### RIR-004 Zero-Slot Option Quota: Default Suite Items Are Not Counted Against Size + TL

`refs/robot/11_zero_slot_options.md`: "In addition to the five Zero-Slot options of the robot's Default Suite, a robot
design can incorporate additional Zero-Slot options equal to its size plus its Tech Level. Beyond Default (5) + Size +
TL any additional Zero-Slot options require one Slot each."

The five default suite items are free and entirely separate from the Size + TL quota. A robot therefore has up to Size +
TL additional zero-slot options at no slot cost. Any further zero-slot options each consume one slot from the robot's
available slots pool.

Chassis modifications that happen to occupy no slots (e.g. Decreased Resiliency) are not counted against this quota;
only options that appear in the Options row of the stat block are counted.

### RIR-005 All Slot Calculations Use Ceiling Rounding

The Robot Handbook states "round up" for every fractional slot result. Ceres applies `math.ceil` in all slot
derivations:

- available slots from None locomotion (+25% of base slots)
- slots freed by removing a manipulator (10% of base slots per manipulator, minimum 1)
- additional manipulator slot requirement (percentage of base slots, minimum 1)
- vehicle speed modification slot requirement (25% of base slots)
- external power slot requirement (5% of base slots)

No slot calculation ever uses floor division or banker's rounding.

### RIR-006 Resized Standard Manipulator Slot Formula

The *Robot Handbook* (p.26) describes resizing a standard manipulator as "the equivalent of removing it and adding a
different sized manipulator," then refers to the Additional Manipulator Slots table for the slot requirement of the new
size.

Ceres computes the net slot effect as:

    new_slots = max(1, ceil(pct(Δsize) × base_slots))
    std_slots = max(1, ceil(0.10 × base_slots))
    delta = new_slots − std_slots

A smaller manipulator frees `|delta|` slots (negative delta); a larger one consumes them. This is consistent with the
"equivalent of removing and adding" language: you recover the standard slot budget and spend the new one.

Worked example — Size 3 arm on a Size 5 robot (base_slots = 16):

- std_slots = max(1, ceil(0.10 × 16)) = 2
- Δsize = 3 − 5 = −2 → pct = 2% → new_slots = max(1, ceil(0.02 × 16)) = 1
- delta = 1 − 2 = −1 → one slot freed

### RIR-007 Walker Leg-Manipulators: Cost Only, No Slots

The *Robot Handbook* (p.27) states: "A robot designed as a walker may enhance a leg to operate as a manipulator by
paying the base manipulator cost of a robot of its Size (Cr100 × Size per modified manipulator). … their size may not be
altered."

The rule mentions only cost, not slots. The size restriction is the counterpart to that: because the legs are not
resized or fully added as extra components, they carry no slot expenditure. Ceres therefore treats converting a walker's
default two legs into manipulators as costing Cr100 × robot_size each with no slot effect.

The eight-limbed example (p.27) — "keeping the two original manipulators, adding four manipulators and altering the two
default legs" — distinguishes *adding* (slots + cost) from *altering* (cost only). Extra limbs beyond the default two
legs, if any, would be modelled as entries in `Robot.manipulators` (full additional-manipulator rules apply).
`Robot.legs` covers only the default two converted legs.

### RIR-008 Basic (locomotion) Vehicle Skill: Type From Locomotion, Level From Agility

The *Robot Handbook* (p.69) states that `Basic (locomotion)` grants `Athletics (dexterity) X, Vehicle (type) X` where X
equals the robot's agility enhancement modification value, and skill 0 if no agility enhancement is installed.

Ceres interprets "agility enhancement modification value" as the robot's *effective agility*: the locomotion type's base
agility plus any `AgilityEnhancement` option level. This matches the published Basic Courier design (GravLocomotion base
agility 1, no explicit `AgilityEnhancement` → Flyer (grav) 1, Athletics (dexterity) 1 ✓) and the Gonzales design
(WheelsATV base agility 0, `AgilityEnhancement(2)` → Drive (wheel) 2, Athletics (dexterity) 2 ✓).

The vehicle skill type follows the locomotion type:

| Locomotion          | Vehicle skill        |
| ------------------- | -------------------- |
| Wheels / Wheels ATV | Drive (wheel)        |
| Tracks              | Drive (tracked)      |
| Grav                | Flyer (grav)         |
| Aeroplane           | Flyer (wing)         |
| VTOL                | Flyer (rotor)        |
| Aquatic             | Seafarer (personal)  |
| Hovercraft          | Drive (hovercraft)   |
| Thruster            | Pilot (small craft)  |
| Walker / None       | — (no vehicle skill) |

### RIR-009 Speed Label Convention

A robot's speed display depends on whether Vehicle Speed Modification is installed:

- **No VSM**: tactical speed in metres — `'{effective_speed + agility + speed_bonus}m'`, e.g. `'12m'`. Affected by
  Tactical Speed Enhancement and Tactical Speed Reduction (neither of which may be combined with VSM; see RIR-010).
- **VSM present**: both modes are shown as `'{tactical}m ({band})'`, e.g. `'10m (high)'` or `'6m (slow)'`. The tactical
  part is the same formula as above; the band comes from the Vehicle Speed Locomotion table
  (refs/robot/08_locomotion_modifications.md). The Locomotion column in the stat block also shows `'Grav (VSM)'` etc. to
  make the installation visible at a glance.
- **Thruster locomotion** (regardless of VSM): thrust expressed as `'{thrust_g:g}G'` (e.g. `'0.1G'`).

Every locomotion type that can carry VSM must declare `_vehicle_speed_band` matching the Vehicle Speed Locomotion table.

### RIR-010 Vehicle Speed Modification: Incompatibilities and Agility Enhancement

**Incompatibilities.** The *Robot Handbook* (p.53) explicitly states that Vehicle Speed Modification cannot be combined
with Tactical Speed Enhancement or Tactical Speed Reduction. These are direct rule prohibitions, not interpretations.

**Agility Enhancement with VSM.** The rules place no restriction on combining Agility Enhancement with VSM. A robot with
VSM can still move at its normal tactical speed (to conserve endurance, for instance), and Agility Enhancement increases
that tactical speed as normal. The enhancement also grants `Athletics (dexterity) N` unconditionally and raises the
robot's effective agility used in other calculations (e.g. the vehicle skill level from a `Basic (locomotion)` brain,
see RIR-008). What Agility Enhancement does *not* do is change the vehicle speed band — that is fixed by locomotion
type.

Ceres reflects this correctly: `AgilityEnhancement.speed_bonus` contributes to the tactical portion of `speed_label`
regardless of VSM (see RIR-009), and the Athletics skill grant is always emitted.

### RIR-011 Robot Skill Package Characteristics May Follow Speciality Task

The *Robot Handbook* Standard Skill Packages table assigns one characteristic to
each skill row regardless of specialisation. Ceres uses that row characteristic as
the default, but allows a speciality to use a different characteristic when the
speciality's task clearly differs from the broad row's physical handling assumption.

Current robot skill package characteristic interpretations:

| Skill package          | Table row | Characteristic | Reason                                                   |
| ---------------------- | --------- | -------------- | -------------------------------------------------------- |
| Animals (handling)     | DEX       | DEX            | physical handling/riding animals                         |
| Animals (training)     | DEX       | INT            | instruction and behavioural judgement                    |
| Animals (veterinary)   | DEX       | INT            | robot equivalent of EDU-based diagnosis/treatment        |
| Gunner (turret)        | DEX       | DEX            | direct weapon operation                                  |
| Gunner (screen)        | DEX       | DEX            | direct defensive system operation                        |
| Gunner (ortillery)     | DEX       | INT            | indirect orbital fire-control work                       |
| Gunner (capital)       | DEX       | INT            | large-ship weapon system coordination                    |
| Pilot (small craft)    | DEX       | DEX            | direct piloting                                          |
| Pilot (spacecraft)     | DEX       | DEX            | direct piloting                                          |
| Pilot (capital ships)  | DEX       | INT            | large-ship command/system piloting, not manual dexterity |
| Seafarer (personal)    | DEX       | DEX            | direct craft handling                                    |
| Seafarer (sail)        | DEX       | DEX            | direct craft handling                                    |
| Seafarer (ocean ships) | DEX       | INT            | vessel systems/navigation command, not manual dexterity  |
| Seafarer (submarine)   | DEX       | INT            | vessel systems/navigation command, not manual dexterity  |

Robot brains do not model EDU for ordinary skill package DMs, so specialities
that would be EDU-based for sophonts are treated as INT-based robot tasks.

### RIR-012 Skill (All) is a pure display artifact, nothing you can buy

Robot Handbook says:

"Finally, for skills with many specialities, the Referee
may rule that selecting a given skill package four
times at a certain level provides a broad enough
exposure so that the skill can be in all specialities.
Optionally, extremely broad skills such as Science
may require eight packages for full coverage."

Ceres gives no such concessions. Robot specifications can
have listings like "Engineer (All) 2", but that's not because
anyone bought an all-package. No such thing exists. It's just
a compact way of writing that skill level including DM from
impacting characteristic happened to cause all specialisations
to land on the same level, in this case probably because it's
an INT 12 brain and an Engineer 0 package.

It is of course possible to buy as many specializations as
one wants for skills with specializations, but note that this
is rarely the case when we see e.g. "Electronics (All) 1" in
a robot spec, and skill package APIs for skills with
specialisations must explicitly list all awarded specialisations
as soon as level is above 0. I.e. Something like Pilot() could
award Pilot 0, but to get Pilot (All) 1 without INT and DEX DMs,
the API call must look something like
Pilot(small_craft=1, starships=1, capital_ships=1) with all awarded
specialisations given. Note that the cost and bandwidth requirement
for this is the same as for three entirely separate skills with
the same price and bandwith, e.g. Admin(level=1), Mechanics(level=1)
and Steward(level=1)

### RIR-013 Manipulator STR/DEX Athletics DM: General-Purpose Arms Only

The *Robot Handbook* (p.26) ties the recorded Athletics level to manipulator
characteristics:

"Increased DEX and STR values do not directly grant a skill equivalence of
Athletics (dexterity) or Athletics (strength) to the robot unless it has a skill
package of Athletics installed in its brain. If such a package is installed, even
at skill level zero, then DMs for high STR or DEX are applied to simulate that
skill level, although in situations where different manipulators have different
DMs, the Referee should determine whether a DM applies. Note that a robot with
DEX 15 manipulators and Athletics 0 would be considered to have Athletics
(dexterity) 3 for skill recording purposes…"

The rule defers the mixed-manipulator case to the Referee, and the handbook's own
StarTek example (p.26) shows how that call is expected to go: the third, Size 3
arm with DEX 12 "does not gain a general Athletics (dexterity) DM even if the
robot has an Athletics skill package because the Referee determines that the DEX
modifier is limited to the specific actions of the small arm."

The distinction Ceres draws is the one the rules draw, by **role** rather than size.
*Robot Handbook* p.25–26 names four kinds: **Base Manipulators** (the two included in
the Base Chassis Cost), **Altered Base Manipulators** (those two removed, resized or
with STR/DEX changed), **Additional Manipulators** (bought on top, costing Cr100 ×
their own size), and walker legs enhanced to act as manipulators.

The robot's *general* figure comes from its base manipulators, however they have been
altered:

    dex_for_dm = max(m.effective_dex for m in base_manipulators)
    str_for_dm = max(m.effective_str for m in base_manipulators)

An **additional** manipulator is bought for a purpose, so it does not replace the
general figure — that is what StarTek's delicate third arm demonstrates. Size does not
decide this: a Size 5 robot whose two base arms were resized to Size 4 genuinely has
STR 7 arms, and reporting the chassis default STR 9 would invent a capability it does
not have. The chassis value 2 × Size − 1 is the fallback for a robot with **no** base
manipulators, which is the case refs/robot/54_robots_as_travellers.md gives it for
("tasks such as smashing down a door").

STR and DEX are governed by one paragraph and are treated identically. Note that
this affects only the *recorded* Athletics level; per the same passage, the robot
does not receive an additional DM on top of that level when making Athletics
checks.

#### Two readings when manipulators differ in DEX

Discarding the additional arm entirely would lose real information: StarTek's
stunner genuinely does get DM+2 from the small arm, as the handbook's own text says
even though its printed skill line shows a bare `Gun Combat 0`. Since the rule hands
the choice of manipulator to the Referee, Ceres does not choose. It states **one
reading per distinct DM profile** — the base arms taken together, plus each additional
and leg manipulator that differs from them — **highest first**:

    Gun Combat (Energy) 3/2
    Gun Combat (Other) 2/1

The leading figure is the best the robot can manage, which is also the typical case —
a ranged weapon is normally mounted on the arm bought to aim it. Readings are
deduplicated, and where they all agree a single figure is shown, so robots with
uniform manipulators are unaffected.

Readings are collected into a set before ordering, so the result does not depend on
the order the arms were declared in, and a robot with three distinct profiles shows
three readings rather than losing the middle one.

Position deliberately carries no fixed meaning: the readings are ordered by value,
not by arm, so nothing may be inferred from which slot a figure occupies. A robot
with mixed manipulator DEX carries an informational note saying only that some skills
show several levels depending on the manipulator used and that the highest leads. The
manipulator row already lists the arms; pairing figures to arms is a table decision,
not a design-time fact.

Pairing happens before speciality compaction. Compacting each reading separately and
matching the results afterwards would misalign them, since the zero-level exclusion
can give the two readings different shapes — `Gun Combat 0` against
`Gun Combat (All) 2` for StarTek.

#### Skills that may use more than one characteristic

For nearly every skill one characteristic applies, but the melee attack in *Traveller*
core is `2D + Melee (appropriate speciality) + STR or DEX DM` — the attacker's choice —
and the grapple rules repeat it. Melee is the only such skill for a robot: the other
multi-characteristic checks in the core rules choose among INT, EDU and SOC, and the
*Robot Handbook* collapses all three to INT, since skill packages take "INT or DEX" DMs
and "the robot's effective SOC or EDU is considered equivalent to its INT".

Ceres does not resolve the choice by taking the better characteristic. It gives each
one its own row, labelled with the characteristic:

    Melee (STR, Unarmed) 5/1
    Melee (DEX, Unarmed) 4/3

Collapsing to a single best-of row would hide the two facts a table actually needs.
The choice is not always free — a Referee may rule that a particular task turns on
STR — and the characteristics rank the arms *differently*: above, STR favours the
strong general arms and DEX the nimble gun arms, so a best-of row would silently pick
a different arm depending on which characteristic won. Splitting states the whole
matrix and leaves both choices where the rules put them, with the table.

Rows are named `Skill (CHAR, Speciality)`, and the `(All)` and `(Other)` compaction
applies within each characteristic independently.

In the skills row a `(Other)` entry is placed after the named specialities of the same
skill rather than in alphabetical position, since it stands for the remainder and reads
as a trailing catch-all — `Melee (STR, Unarmed) 5/1, Melee (STR, Other) 3`, not the
reverse that alphabetical order would give.

Readings below zero are left out. A negative reading means the manipulator is worse
than useless for that task, and the alternatives are all bad: printing `2/-1` puts a
number that is not a skill level in a skill column, and clamping to `2/0` would claim
a trained competence the robot does not have. Where every reading of an entry is
negative the entry is omitted entirely. This loses nothing that matters, because
unlike a published stat block a Ceres design also lists the skill packages it actually
bought — the Skills section of the build shows `Melee (Unarmed) 2` whatever the
manipulators do to it, so the skills row is a convenience, not the record.

This notation is a display artifact in the same sense as `(All)` (RIR-012): nothing
in the design buys a "3/2", it is a statement that two DMs are available and the
choice is a table decision.

## Rule Interpretations for vehicles

### RIV-001 Vehicle Hull And Structure Are Both Modelled; Vehicle Hull Is Not Ship Hull

A vehicle has two related damage figures, and they are not the same number.
*Vehicle Handbook* p.10 states: "Vehicles have a Hull value based upon their size,
type and certain features. A vehicle's Structure score is one-tenth of its Hull
value, rounded up."

Hull is the intermediate value — Spaces times the type's Hull per Space, modified by
features and structural reinforcement, never less than 1. Structure is what the
catalogue stat block prints and what play uses as the damage threshold. Ceres models
both, since the modifiers apply to Hull and rounding to Structure happens once, last.

**Hull is not rounded.** The quoted sentence licenses exactly one rounding, at
Structure. Rounding Hull as well is an invented second step. No published design
distinguishes the two — every catalogue entry with a fractional Hull (Dracoflame
1.5, Palanquin 8.8, Sky Dirge 28.16, Paladin 224.4) yields the same Structure
either way — so this is settled by what the rule says rather than by example, and
a rounded Hull would be an unnoticed divergence waiting for the case that differs.

The derivation was checked against every catalogue design that prints both a Spaces
count and a Structure — 29 of them, spanning all the per-Space rates in use (Ground,
Grav, Watercraft and Walker at 2; Rotorcraft and Hovercraft at 0.5; Airship at 0.2;
Submersible at 3) and sizes from 2 Spaces to 20,000,000. All 29 agree. A
representative sample:

| Vehicle             | Type        | Spaces | Modifiers                 | Hull   | Structure |
| ------------------- | ----------- | ------ | ------------------------- | ------ | --------- |
| ATV                 | Ground      | 20     | —                         | 40     | 4         |
| Gecko               | Ground      | 9      | —                         | 18     | 2         |
| Gunskiff            | Grav        | 20     | Light Hull -25%           | 30     | 3         |
| Brutus              | Ground      | 80     | Reinforced Hull +10%      | 176    | 18        |
| G/Carrier           | Grav        | 20     | AFV +50%, Reinforced +10% | 66     | 7         |
| Paladin Grav Tank   | Grav        | 68     | AFV +50%, Reinforced +10% | 224.4  | 23        |
| Dracoflame          | Rotorcraft  | 3      | —                         | 1.5    | 1         |
| Sky Dirge           | Airship     | 128    | Reinforced Hull +10%      | 28.16  | 3         |
| Horizon Hover Ferry | Hovercraft  | 5,000  | Light Hull -25%           | 1,875  | 188       |
| Nautilus            | Submersible | 370    | —                         | 1,110  | 111       |

Note the *Core Rulebook* prints a single `HULL` figure for the same vehicles on a
different scale — its ATV shows Hull 60 where the Vehicle Handbook gives Hull 40 and
Structure 4. The Vehicle Handbook is the construction source and is internally
consistent; the Core figure is not reproduced.

**Naming.** `Hull` already means something else in Ceres: in `make.ship` it is a
*part*, with configuration, armour and cost. A vehicle's Hull is a bare quantity,
and not necessarily a whole one. The two are unrelated and must not be conflated
because they share a word — which matters because `make.ship` will eventually import
`make.vehicle` (see ADR-0001).

### RIV-002 Hull Modifiers Compound; They Are Not Summed Against The Base

The rules give AFV as "+50% Hull" and structural reinforcement as Reinforced Hull
"+10%" or Light Hull "-25%", without stating whether several such modifiers compound
or are summed against the base. Note this is the opposite of how feature *Cost*
percentages behave, which the Features chapter states explicitly are additive against
the base Cost.

Modifiers compound: base Hull, then feature modifiers, then structural reinforcement,
each applied to the value arrived at so far. This is derived from the published
designs, not interpreted. The **Paladin Laser Grav Tank** decides it — 68 Spaces of
Grav Vehicle at Hull 2 per Space, carrying both AFV and a Reinforced Hull:

- compounding: 136 x 1.5 x 1.1 = 224.4, Structure 23 — the printed value
- summed: 136 x (1 + 0.5 + 0.1) = 217.6, Structure 22

It is the only design in the catalogue that separates the two readings. Every other
entry carrying both an AFV and a reinforcement, such as the G/Carrier at 66 against
64, rounds to the same Structure either way. Checked across all 29 catalogue designs
that print a Structure, compounding matches 29 and summing 28.

This entry previously recorded the sequential reading as an unevidenced
interpretation on the strength of the G/Carrier alone. That was a generalisation from
a single non-discriminating design; the Paladin settles it.

### RIV-003 Armour `6 (18)` Notation Is Derived At Render Time

Catalogue armour tables print two numbers per face, for example the ATV's
`Forward 6 (18)`. The first is the face's Protection. The second is the protection
applied against small arms only, which the Armour chapter states is reduced by both
the armour and the Tech Level of the vehicle — the ATV is TL12, so 6 + 12 = 18.

The parenthesised figure is presentation, not design state. Ceres stores Protection
per face and derives the small-arms figure when rendering a spec. It is not a field
on the design and is not serialised.

The Tech Level bonus applies only while the face is not reduced below the base
Protection for the vehicle's Tech Level — the open-topped dorsal face being the
case where it is. A face in that state prints its Protection without the
parenthesised figure.

### RIV-004 Round-To-Nearest Means Half Up, Never Python's `round`

*Vehicle Handbook* p.27 sets the convention: "When rounding to the nearest value,
whether positive or negative, a remainder of exactly 0.5 always rounds up."

Python's built-in `round` does not do this. It rounds half to even — `round(4.5)` is
4 and `round(5.5)` is 6 — so it disagrees with the rules on exactly the values the
rule exists to settle. Vehicle design must not use it where the rules say round to
the nearest value; use an explicit half-up helper.

This applies only to round-to-nearest. The rules also call for rounding up (Structure
from Hull, armour Spaces, mounted weapons consuming a Space) and rounding down
(available Spaces on an airship's gas envelope, a submersible's hours submerged),
which are ordinary ceilings and floors and are unaffected.

### RIV-005 An Unstated Range Is Not A Range Of Zero

Several vehicle type tables leave the Range column blank for their earliest Tech
Levels — a TL1–2 ground vehicle and a TL0–2 watercraft print "—" rather than a
figure. The source makes no claim about how far such a vehicle travels; it simply
does not state one.

Ceres records this as an absent Range rather than a Range of zero kilometres. Zero
would be a positive claim the source does not make, and a false one: a TL1 cart
plainly travels. A design with no stated Range renders the column as "—", as the
catalogue does.

This is distinct from a genuine zero. A Structure has a Speed of Stopped and a
Range of 0, because it does not move at all.

### RIV-006 A Design Below Its Type's Tech Level Is Flagged, Not Refused

Each vehicle type states the Tech Level at which it becomes available, and its
performance table begins there. The rules do not say what a vehicle built below
that Tech Level does, because it is not a legal design.

Ceres records the violation as an error on the design and otherwise lets it
behave as though built at the type's own earliest Tech Level, so every property
stays answerable and the design can still be rendered and inspected. This follows
the project's general treatment of rule violations as notes on a design rather
than refusals to construct one: a designer is better served by seeing an illegal
design with its problem named than by an exception.

The clamp is a rendering convenience, not a claim that such a vehicle exists.

### RIV-007 Agility Is Not Final Until Options Are Installed

A vehicle's Agility is easy to mistake for a property of its type and size. It is
not. It is the sum of the type's baseline, the Size table's modifier, any
features that grant Agility, and the **Control System** option — which the Core
Options chapter gives as Primitive -1, Basic +0, Improved +1, Enhanced +2,
Advanced +3, Superior +4.

The published ATV is the clearest case. A Heavy Ground Vehicle derives Agility
+0 -1 = -1, where the catalogue prints +0. The difference is its Control System
(improved), worth +1. The Air/Raft carries Control System (basic) and so keeps
the +1 its type and size give it.

Checked across the catalogue designs that print an Agility, including the
Control System raises agreement from 10 of 29 to 20 of 29. The designs that
still differ are not explained by this rule and are left for investigation; they
are not evidence against it.

The consequence for the model is structural: Agility cannot be computed from the
vehicle's type, size and features alone, so nothing should present it as final
before options are installed.

Note also that any control system granting a positive Agility DM requires a
powered vehicle.

### RIV-008 Fuel Capacity Is Measured In Spaces, Efficiency In Steps

The Customisations chapter quotes fuel capacity as "+25% Range for -10% Spaces"
and fuel efficiency as "+50% Range" per application, which reads as though both
were step-wise. The official Vehicle Design Worksheet, distributed with the
book, computes them differently and more generally:

    Range = (base + 2.5 x fuel_spaces / vehicle_spaces x base) x efficiency

- **Fuel capacity** is stated as a number of Spaces, and its effect is 2.5 times
  the share of the vehicle given over to fuel. A tenth of the vehicle is
  therefore the +25% the book quotes — the two agree, but the worksheet allows
  any number of Spaces rather than only tenths. Fuel capacity appears nowhere in
  the worksheet's Cost pipeline: it is paid for in Spaces and never in money.
- **Fuel efficiency** is a step count. Each positive step multiplies Range by a
  further half and each negative step removes a quarter, so two steps double it.
  Its Cost is a fraction of the vehicle's base: 25%, 50% and 75% for one, two
  and three steps, and -10%, -20% and -30% going the other way.

Ceres follows the worksheet, because it reproduces the book's quoted figures
while also handling vehicles whose fuel is not a round tenth.

The worksheet confirms much else besides: the type and size tables, the range
ladders, cruise speed as one band down with Range x1.5 rounded, and the shape of
the Cost pipeline — a base Cost with every percentage taken against that base
and summed rather than compounded, absolute costs added on top, and total
reductions limited to 90% of base. It also prices some options by the size of
the whole vehicle rather than by any volume of their own, vacuum environment
protection and fire extinguishers among them.

The worksheet is not an answer key either. It disagrees with the book on the
Cost of a basic sensor system (Cr5,000 against Cr2,000) and on galley Costs, and
sizes life support as a flat 5% of the vehicle rather than one Space per twenty
people. Where the two differ and nothing else decides it, Ceres follows the book.

### RIV-009 Published Catalogue Designs Do Not Reliably Reconcile

Several designs in the Vehicle Catalogue cannot be reproduced from the
construction rules, and this is acknowledged by the book's own contributors
rather than being a matter of interpretation. On the publisher's forum, in the
Vehicle Catalogue 2026 Questions and Errata thread, Terry Mixon reports of the
Corporate Jet Transport that he "had to discount it by 60% to get the price
close" and "was unable to get the range. Not even close.", concluding "The
design is definitely broken". Others report being unable to "even remotely
create some vehicles in this catalogue, always coming out heavier and larger",
and the Invader Light Grav Tank is printed with wheeled-vehicle statistics.

Ceres has found the same for the two designs it reproduces. Every figure on the
ATV's and the Air/Raft's stat blocks derives from the rules except Cost, where
the ATV comes out well above its published Cr155,000 and the Air/Raft below its
Cr250,000. The Air/Raft's published 2,000km Range is reachable only by two steps
of fuel efficiency, which then adds half its base Cost again and puts it further
still from the published figure; the alternative, fuel capacity, would require
3.2 Spaces of a vehicle that has 8.

These are therefore recorded as source discrepancies on the affected designs
rather than reconciled. A design whose derived figures differ from its published
ones is annotated at the point of comparison, and the derivation is not adjusted
to match. No official errata exists at the time of writing.
