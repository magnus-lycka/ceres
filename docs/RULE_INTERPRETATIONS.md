# Rule Interpretations

Ceres targets **Mongoose Traveller 2nd Edition (MgT2)**. The specific editions
in scope are:

| Book | Edition |
| ---- | ------- |
| *Core Rulebook* | 2022 (2026 revision) |
| *High Guard* | 2022 (2026 revision) |
| *Central Supply Catalogue* | 2023 (2024 revision) |
| *Traveller Companion* | 2024 |

Where the *Core Rulebook* and *High Guard* conflict, High Guard takes
precedence.

Material from earlier MgT2 printings (notably *High Guard* 2016) that was
removed or replaced in later editions is treated as out of scope. See RIS-008.

This document records deliberate rule interpretations, exclusions, and
normalizations used in Ceres.

It is intentionally sparse to begin with. Entries should be added when we
review source-derived ship test cases and need to distinguish between:

- supported behavior
- deliberately ignored source material
- deliberate interpretations
- unresolved TODOs

The goal is to document decisions that are intentional but not obvious from the
code alone, especially where published examples, third-party designs, or older
rules material differ from our implementation.

## Conventions

- Use stable identifiers like `RIS-001`.
- Prefer documenting cross-cutting decisions here.
- Keep ship-specific source notes in the relevant test file unless the decision
  applies more broadly.
- Do not restate code that is already clear unless the reason for the behavior
  would otherwise be ambiguous.

## Entries

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

### RIS-009 Broad Skills From The Traveller Companion Are Treated As Distinct Skills

The *Traveller Companion* (2024) introduced **broad skills**: what earlier
editions called specialities of a single `Science` skill are now fully
independent skills — `Space Science`, `Life Science`, `Physical Science`,
`Social Science`, `Robotic Science` — each with their own specialities. The same applies to `Art` and `Profession`.

Ceres follows this model. `Space Science` is a distinct skill,
with `Space Science (Planetology)`  as a speciality.
The old single `Science` skill with a `(Planetology)` speciality is not modelled.

This is analogous with the Language skill family. Each Language skill,
Language Galanglic, Language Zdatl etc are entirely separate skills.

In practice this affects `Expert` software packages: the skill string passed
to `Expert(N, skill='Space Science (Planetology)')` names a broad skill, not
a flat speciality. The software table in `ceres.gear.software` lists broad
science skills (and their specialities) as top-level entries accordingly.

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

| Crew role | What counts |
| --- | --- |
| Pilot | +1 per carried spacecraft that requires its own pilot |
| Engineer | The craft's drive and power-plant tonnage adds to the total used to derive engineer count |
| Maintenance | The craft's tonnage adds to the total used to derive maintenance count |

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

**Note on third-party tools**: The Tycho tool export for the Belt Racer
(6-ton light hull) shows Basic Ship Systems = 1. Since the official Small
Craft Catalogue sources consistently show 2 for a standard 6-ton hull, and
Tycho may use floor rather than ceil, the Belt Racer stat block deviation
is treated as a Tycho tool difference, not evidence of a light-hull modifier.
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

## Robot Interpretations

### RIR-001 Manipulator Cost Credit — 20% BCC Cap Applied to Combined Net

The rule (*Robot Handbook*, p.25) states: "Removing a manipulator lowers the cost of the robot by Cr100 multiplied by the size of the robot but no more than 20% of the Base Chassis Cost."

Ceres applies a single combined cap across all manipulator credit sources (removal and downsize). The net manipulator cost effect is:

    net = sum(m.cost for m in manipulators) − 2 × std_cost
    net = max(net, −0.20 × BCC)

A negative `net` is a credit. The 20% cap limits the total credit from all manipulator changes combined, not per manipulator. For a Size 3 Wheels robot (BCC = Cr800), the cap is Cr160 regardless of how many manipulators are removed or downsized.

This interpretation changes the Domestic Servant total from Cr420 (uncapped, former implementation) to Cr860 (capped). The source sheet that informed the original expected cost used an uncapped formula; Ceres now follows the explicit rule text.

The same cap applies to resized standard manipulators: if both are downsized the combined credit is still bounded at 20% of BCC.

### RIR-002 Robot Costs Reported Without Editorial Rounding

The Robot Handbook presents final robot costs that are sometimes rounded to one or two significant figures. Ceres reports the exact calculated cost from all rule components and does not apply editorial rounding.

Where a source stat block differs from the Ceres-computed total, the source value is recorded in the test file's `_expected` SimpleNamespace and the Ceres value is set as an override immediately after, with a comment documenting the discrepancy.

Known discrepancies following this pattern are recorded in the relevant test files. The Basic Lab Control Robot discrepancy is additionally explained in RIR-003. The cause of other discrepancies has not been traced to a specific rule or omission and is left as an open question in the test file comment.

### RIR-003 Skill Package Costs And Default Suite Substitution Costs Are Included In Total Cost

**Skill packages** (`refs/robot/35_skill_packages.md`): Standard skill packages installed in Advanced (or higher) brains carry an explicit cost: base cost × 10^level, where base cost comes from the Standard Skill Packages table. These costs are not included in the brain hardware cost and are added separately to the robot's total.

**Default suite substitutions** (`refs/robot/10_default_suite.md`): The five standard default suite items are included in the Base Chassis Cost. Only three alternatives substitute at no additional cost: Drone Interface, Transceiver 5km (basic), and Video Screen (basic). Any other zero-slot item installed as a default suite substitution adds its own cost to the robot total.

The *Basic Lab Control Robot* source stat block (Cr12000) omits both the Electronics (remote ops) 1 skill package (Cr1000) and the two non-free default suite substitutions (Transceiver 500km (improved) Cr1000, Video Screen (improved) Cr500). The Ceres-computed total is Cr14500. See the `_expected.cost` override in `tests/robots/test_lab_control_robot_basic.py`.

### RIR-004 Zero-Slot Option Quota: Default Suite Items Are Not Counted Against Size + TL

`refs/robot/11_zero_slot_options.md`: "In addition to the five Zero-Slot options of the robot's Default Suite, a robot design can incorporate additional Zero-Slot options equal to its size plus its Tech Level. Beyond Default (5) + Size + TL any additional Zero-Slot options require one Slot each."

The five default suite items are free and entirely separate from the Size + TL quota. A robot therefore has up to Size + TL additional zero-slot options at no slot cost. Any further zero-slot options each consume one slot from the robot's available slots pool.

Chassis modifications that happen to occupy no slots (e.g. Decreased Resiliency) are not counted against this quota; only options that appear in the Options row of the stat block are counted.

### RIR-005 All Slot Calculations Use Ceiling Rounding

The Robot Handbook states "round up" for every fractional slot result. Ceres applies `math.ceil` in all slot derivations:

- available slots from None locomotion (+25% of base slots)
- slots freed by removing a manipulator (10% of base slots per manipulator, minimum 1)
- additional manipulator slot requirement (percentage of base slots, minimum 1)
- vehicle speed modification slot requirement (25% of base slots)
- external power slot requirement (5% of base slots)

No slot calculation ever uses floor division or banker's rounding.

### RIR-006 Resized Standard Manipulator Slot Formula

The *Robot Handbook* (p.26) describes resizing a standard manipulator as "the equivalent of removing it and adding a different sized manipulator," then refers to the Additional Manipulator Slots table for the slot requirement of the new size.

Ceres computes the net slot effect as:

    new_slots = max(1, ceil(pct(Δsize) × base_slots))
    std_slots = max(1, ceil(0.10 × base_slots))
    delta = new_slots − std_slots

A smaller manipulator frees `|delta|` slots (negative delta); a larger one consumes them. This is consistent with the "equivalent of removing and adding" language: you recover the standard slot budget and spend the new one.

Worked example — Size 3 arm on a Size 5 robot (base_slots = 16):

- std_slots = max(1, ceil(0.10 × 16)) = 2
- Δsize = 3 − 5 = −2 → pct = 2% → new_slots = max(1, ceil(0.02 × 16)) = 1
- delta = 1 − 2 = −1 → one slot freed

### RIR-007 Walker Leg-Manipulators: Cost Only, No Slots

The *Robot Handbook* (p.27) states: "A robot designed as a walker may enhance a leg to operate as a manipulator by paying the base manipulator cost of a robot of its Size (Cr100 × Size per modified manipulator). … their size may not be altered."

The rule mentions only cost, not slots. The size restriction is the counterpart to that: because the legs are not resized or fully added as extra components, they carry no slot expenditure. Ceres therefore treats converting a walker's default two legs into manipulators as costing Cr100 × robot_size each with no slot effect.

The eight-limbed example (p.27) — "keeping the two original manipulators, adding four manipulators and altering the two default legs" — distinguishes *adding* (slots + cost) from *altering* (cost only). Extra limbs beyond the default two legs, if any, would be modelled as entries in `Robot.manipulators` (full additional-manipulator rules apply). `Robot.legs` covers only the default two converted legs.

### RIR-008 Basic (locomotion) Vehicle Skill: Type From Locomotion, Level From Agility

The *Robot Handbook* (p.69) states that `Basic (locomotion)` grants `Athletics (dexterity) X, Vehicle (type) X` where X equals the robot's agility enhancement modification value, and skill 0 if no agility enhancement is installed.

Ceres interprets "agility enhancement modification value" as the robot's *effective agility*: the locomotion type's base agility plus any `AgilityEnhancement` option level. This matches the published Basic Courier design (GravLocomotion base agility 1, no explicit `AgilityEnhancement` → Flyer (grav) 1, Athletics (dexterity) 1 ✓) and the Gonzales design (WheelsATV base agility 0, `AgilityEnhancement(2)` → Drive (wheel) 2, Athletics (dexterity) 2 ✓).

The vehicle skill type follows the locomotion type:

| Locomotion | Vehicle skill |
| --- | --- |
| Wheels / Wheels ATV | Drive (wheel) |
| Tracks | Drive (tracked) |
| Grav | Flyer (grav) |
| Aeroplane | Flyer (wing) |
| VTOL | Flyer (rotor) |
| Aquatic | Seafarer (personal) |
| Hovercraft | Drive (hovercraft) |
| Thruster | Pilot (small craft) |
| Walker / None | — (no vehicle skill) |

### RIR-009 Speed Label Convention

A robot's speed display depends on whether Vehicle Speed Modification is installed:

- **No VSM**: tactical speed in metres — `'{effective_speed + agility + speed_bonus}m'`, e.g. `'12m'`. Affected by Tactical Speed Enhancement and Tactical Speed Reduction (neither of which may be combined with VSM; see RIR-010).
- **VSM present**: both modes are shown as `'{tactical}m ({band})'`, e.g. `'10m (high)'` or `'6m (slow)'`. The tactical part is the same formula as above; the band comes from the Vehicle Speed Locomotion table (refs/robot/08_locomotion_modifications.md). The Locomotion column in the stat block also shows `'Grav (VSM)'` etc. to make the installation visible at a glance.
- **Thruster locomotion** (regardless of VSM): thrust expressed as `'{thrust_g:g}G'` (e.g. `'0.1G'`).

Every locomotion type that can carry VSM must declare `_vehicle_speed_band` matching the Vehicle Speed Locomotion table.

### RIR-010 Vehicle Speed Modification: Incompatibilities and Agility Enhancement

**Incompatibilities.** The *Robot Handbook* (p.53) explicitly states that Vehicle Speed Modification cannot be combined with Tactical Speed Enhancement or Tactical Speed Reduction. These are direct rule prohibitions, not interpretations.

**Agility Enhancement with VSM.** The rules place no restriction on combining Agility Enhancement with VSM. A robot with VSM can still move at its normal tactical speed (to conserve endurance, for instance), and Agility Enhancement increases that tactical speed as normal. The enhancement also grants `Athletics (dexterity) N` unconditionally and raises the robot's effective agility used in other calculations (e.g. the vehicle skill level from a `Basic (locomotion)` brain, see RIR-008). What Agility Enhancement does *not* do is change the vehicle speed band — that is fixed by locomotion type.

Ceres reflects this correctly: `AgilityEnhancement.speed_bonus` contributes to the tactical portion of `speed_label` regardless of VSM (see RIR-009), and the Athletics skill grant is always emitted.
