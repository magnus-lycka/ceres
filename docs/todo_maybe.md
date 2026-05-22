# List of potential things to do

Update todo items in this document as progress is made.
When todo items are done, please move them
to docs/archive/done_todos.md

## Sort out weapons.py [doing]

All ships have hardpoint in proportion to displacement, except smallcraft which have firmpoints.

Fixed mounts, turrets, barbettes and bays can be mounted in hardpoints of firmpoints (not bays in firmpoints).

Some weapons are designed to be mounted either on fixed mounts or turrests, some on barbettes and some in bays.

Firmpoint mounting of weapons reduces/limits range and reduces power.

The code as written matches the rules structure poorly.

Current status:

- hardpoint / firmpoint capacity checks implemented
- small craft restriction to single turrets implemented
- turret API split into concrete classes such as `SingleTurret`, `DoubleTurret`, and `TripleTurret`
- `FixedMount` and turrets now share concrete mount weapon classes such as `PulseLaser` and `MissileRack`
- `Barbette`, `Bay`, `PointDefenseBattery`, and `MissileStorage` are modeled with concrete weapon-installation classes
- size-reduction weapon modifiers are modeled for barbettes, bays, and point defense batteries
- fixed mounts can carry multiple weapons in the model, with small-craft restrictions enforced

Still missing / unclear:

- firmpoint range limitations are not yet modeled, only power / capacity effects
- weapon families and mount compatibility are still incomplete
- broader weapon coverage is still incomplete (for example sandcasters and other mountable weapon families)

## DETERMINE CREW [doing]

Calculate crew needs. Means we need to have a way to determine if military or civilian ship,
or if we want civilian or military crew analysis.

Calculate crew by rules if not given. Warning, not error, given if stated crew seems understaffed.

Use new module crew.py as single source of truth for crew.

Structural status:

- `crew.py` now exists and `Ship` delegates there
- commercial rules implemented
- military rules implemented
- large ship crew reduction implemented, including bracket-boundary cap
- medic count uses habitation capacity (stateroom beds + low berths + cabin space) as population proxy
- remaining work is further rule expansion and validation, not structure

Remaining ideas:

- decide whether ship role inference should remain explicit (`military=True`) or become partly automatic

Automation crew effects have been split into a separate item below.

## Automation [todo]

Model ship automation levels and their effect on crew requirements.

Reference: `refs/companion/54_starship_automation.md`

The Traveller Companion defines six automation tiers — from Crew-Intensive
(−40% hull/drive cost, +100% crew) through High Automation (+100% cost, −40%
crew) — each with a cost modifier, a crew-requirement multiplier, and a task
DM. Standard Automation is the current implicit default.

The cost side affects hull plus drives/power-plant totals. The crew side applies
a percentage multiplier to the normal crew complement. Some roles are exempt
from reduction (e.g. a ship needing one astrogator still needs one astrogator
regardless of automation level). Task DMs apply to all shipboard checks.

Remaining work:

- add an `automation` field to `Ship` (or a hull/drives option) with the six
  tiers
- apply the cost modifier to hull and drive/plant costs
- apply the crew-requirement multiplier to reducible roles
- clarify which roles are immune to the reduction (pilot count for carried
  craft, astrogator, etc.)
- surface any task DM in spec notes

## Screens follow-up [doing]

The High Guard crew table requires gunners for screens:

- commercial: 1 gunner per screen
- military: 2 gunners per screen

Current status:

- Meson screens and nuclear dampers are modelled in `screens.py`.
- Screen gunners are counted in `_commercial_gunner_count` and `_military_gunner_count`.

Remaining work:

- broader source coverage for meson screens and mixed screen installations
- implement **Deflector Screens** (TL10, 5t, MCr5, 10 Power): reduces radiation/particle damage; the lowest-TL screen and most likely to appear in published designs
- implement **Energy Shields** (TL14, 50t, MCr60, 90 Power): reduces all energy weapon damage
- implement **Black Globe Generator** (TL15): absorbs all damage into a capacitor bank; legality note needed (not commercially available); already referenced in this section
- decide how to model capacitor bank, energy bleed, and overload mechanics for Black Globe (these are operational effects; the ship-building side is tonnage/cost/power)

## Spinal mount follow-up [doing]

Mass driver, meson, particle accelerator, and railgun spinal mounts are
modelled from the High Guard spinal mount table. Military gunner count includes
spinal weaponry at 1 gunner per 100 tons before existing large-ship crew
reductions. TL improvement rows (`+1`, `+2`, `+3`) are modelled, and the
High Guard Valiant light cruiser now provides source coverage for a TL15
Meson spinal mount.

Remaining work:

- decide whether railgun and mass-driver ammunition should be represented as
  separate storage parts
- add broader source test coverage for non-meson spinal mount TL improvements
  and other spinal mount families

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

## Military Hull armour cap [todo]

Military hulls (+25% hull cost) allow up to double the normal maximum armour
rating. For example, bonded superdense on a non-military hull caps at the ship's
TL; a military hull doubles that cap. Military hulls are restricted to capital
ships (>5,000 tons) and stack with reinforced hull.

Reference: `refs/hg/05_specialised_hull_types.md`

Current status:

- +25% cost modifier is implemented in `HullConfiguration.effective_hull_cost_modifier`
- capital-ship restriction is not validated
- double armour cap is not enforced in armour validation

Remaining work:

- add a validation error when `military=True` is set on a ship ≤5,000 tons
- enforce the double-cap rule in armour validation (compare installed protection
  against 2× the normal TL-derived maximum when `military=True`)

## Non-Gravity Hull

Basic hulls include artificial gravity, using grav plates to ensure a normal gravitational environment for the comfort and convenience of the crew. Hulls can be built cheaper without artificial grav plating, using specific configurations that allow the hull to constantly spin in order to generate gravity if desired. Non-gravity hulls reduce hull cost by 50% but are limited to a maximum size of 500,000 tons due to structural limitations. Base Power Requirements for non-gravity hulls are half that of other hull types. See Power Requirements on page 17 for more information.

Current status:

- hull cost reduction implemented
- basic hull power reduction implemented
- 500,000-ton maximum size reported as a ship error

Remaining work:

- decide how to model spin-capable layouts separately from the generic `non_gravity=True` flag

*To use this and still get artificial gravity the ship must be able to spin. It could be a torus, a cylinder or something like a capsule connected to a counterweight with a wire (of course it could be two capsules acting as counterweights to each other, but you might have heavy stuff, like power plant, where you don't need full gravity). Either way, the spin radius must be big enough to make this more good than bad. One can of course settle for less than 1G gravity, but there are several well known issues. Both torus and capsule with counterweight would -- I think be dispersed structure. A cyliner, wgich could be a standard structure, would have to be huge, and either a lot of wasted space or most areas wouls have much less gravity. With rotation, there are several issues, which all get worse with less radius (which also means faster rotation): Things fall in tangential direction, not at all same as perceived down. Coriolis effects are stronger. Rapid spin makes people dizzy etc. All of this will place a lower bound on reasonable radius. Of course, working in Zero-G with penaltiess is an option.*

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

## Split big files

     632 src/ceres/make/ship/drives.py

Separate into drives and powerplants

    1215 src/ceres/make/ship/weapons.py

Split up the big weapons file

## Add other types of drives

Keep this as a parking lot for genuinely new drive families, not power systems.

Already implemented elsewhere:

- chemical and fission power plants
- Sterling fission power plants
- high-efficiency batteries
- R-drives

Candidates that still need rule/API work:

- plasma drives (tracked separately below)
- source-specific drive families from non-HG books

## Solar Energy Systems

Settle the source split and complete solar energy support.

Reference: `refs/hg/25_solar_energy_systems.md`
Related comparison: `docs/solar-energy-systems-comparison.md`

Four tiers (Basic TL6 through Advanced TL12) for both solar coating and solar panels.
Rules include:

- Solar coating only works on standard/sphere configurations; reduced 50% on close-structure/dispersed;
  not available on streamlined (atmospheric stress).
- Solar panels are deployed (cannot accelerate while deployed), measured in tons = units.
- Coatings increase hull repair cost ×2.

Some solar panel/coating support exists in code, but the source identity and
API still need cleanup before extending it further.

Spinward Extents (`refs/spinext/59_arcturus.md`) adds another solar technology
family: TL6/TL8/TL12 solar panels, hull coatings, and solar sails with different
tables and constraints. Decide whether Ceres should support only High Guard,
only Spinward Extents, or both as separate variants such as `HGSolarPanel` and
`SpinExtSolarPanel`. Do not merge them until the API and source identity are
clear.

Open questions:

- SpinExt solar coating works in increments of 10 tons of displacement covered;
  decide whether the API should take `covered_tons`, require multiples of 10, or
  expose another representation.
- SpinExt solar sails use "Thrust per %" based on the percentage of ship tonnage
  dedicated to sails; decide rounding, display, and whether sails belong with
  drives or power/auxiliary systems.
- HG solar sail is a drive accessory (5% hull tonnage, MCr0.2/ton, effective Thrust 0,
  prevents jump while deployed); SpinExt sails are scalable and can double as panels.
  These must remain distinct classes — see `docs/solar-energy-systems-comparison.md`
  for the detailed comparison. Placement decision (drives vs power vs auxiliary) is
  tracked in `docs/plan-source-specific-ship-rules.md`.

## Primitive Hulls

Implement Spinward Extents primitive hulls.

Reference: `refs/spinext/59_arcturus.md`

Primitive hulls are not the same thing as existing High Guard `non_gravity`
hulls. They are a separate low-tech spacecraft construction model:

- no artificial gravity, lifter support, advanced environmental controls, or
  structural support for high-G manoeuvres
- cannot fit manoeuvre drives or jump drives
- cannot support reaction thruster acceleration above Thrust 3
- cost Cr15000/ton and use basic ship systems Power equal to 1% of hull tonnage
- -50% Hull points
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

## Concealed Manoeuvre Drive [todo]

Reference: `refs/hg/23_spacecraft_options.md`

A concealed manoeuvre drive is hidden behind bulkheads for stealth. It adds +25% to the
m-drive's tonnage and cost, and halves effective Thrust (rounding down). The drive must be
within 3 metres of the accelerating surface; removing the outer bulkhead does not improve
performance.

Not currently modelled; no existing todo. Implement as a flag or wrapper on the existing
`_MDrive` hierarchy, similar to how `high_burn_thruster` is a flag on reaction drives.

## Plasma Drives

Implement Spinward Extents plasma drives.

Reference: `refs/spinext/59_arcturus.md`

Rules summary:

- available at TL8
- uses standard liquid hydrogen fuel
- tonnage is 20% of hull tonnage per Thrust
- cost is MCr0.4 per ton
- each ton of plasma drive requires 1 Power
- fuel use is 1% per Thrust per hour
- does not require or benefit from a gravity field, so it works in deep space

Open questions:

- The source says plasma drives may use primitive and advanced modifications.
  Decide whether this maps to existing Ceres customisation grades/modifiers or
  needs a plasma-drive-specific modification set.
- The listed modifications are Energy Efficient, Fuel Efficient, Size Reduction,
  Energy Inefficient, Increased Size, and Fuel Inefficient. Their percentages do
  not exactly match every existing drive customisation, so avoid guessing.
- Planetary-operation rules are out of scope for ship building, but invalid
  build specs should still produce notes/errors where the design itself violates
  construction limits.

## Fuel System Variants [todo]

References: `refs/hg/23_spacecraft_options.md`, `refs/hg/25_solar_energy_systems.md`

Several standard fuel tank options from HG Spacecraft Options are not yet modelled:

- **Collapsible Fuel Tank** (fuel bladder): consumes 1% of its full tonnage when empty, Cr500/ton.
  Cannot be pumped directly to jump drive; must complete a jump first.
- **Mountable Tank**: converts cargo space to fuel; Cr1000/ton. Takes 4 weeks to add/remove.
- **Metal Hydride Storage** (TL9): replaces liquid-H₂ tanks; twice the space, MCr0.2/ton; reduces
  fuel-leak severity.
- **Drop Tank**: external fuel tank jettisoned before jump. Mount fitting consumes 0.4% of tank
  tonnage, MCr0.5/ton; tank itself Cr25000/ton. Imposes DM penalty on Engineer (J-drive) jump
  check and prevents streamlining.
- **Ramscoops**: passive hydrogen collector; 1% of hull + 5 tons (minimum 10 tons), MCr0.25/ton;
  collects 5 tons hydrogen/week/ton ramscoop; no fuel processor needed; prevents streamlining.
- **Fuel Tank Compartment**: fuel tanks concealed inside cargo or other space. Inflicts DM-4 to
  sensor checks and DM-6 to Investigate checks to detect. Cr4,000/ton; tonnage deducted from
  fuel allocation, not from hull tonnage directly.

Remaining work:

- decide which variants are worth implementing first (mountable tanks and collapsible tanks are
  likely most common in published designs)
- implement as `ShipPart` subclasses in `storage.py` or a new `fuel.py` subsection

## Collectors [todo]

Reference: `refs/hg/34_exotic_technology.md`

An alternative to standard jump fuel tanks. A collector array gathers interstellar hydrogen using
field projectors and stores it for jump use, eliminating dependence on fuel refineries or gas giant
skimming. TL14.

Tonnage formula: (1% of hull tonnage × jump rating) + 5 tons. Cost: MCr0.5/ton.

Not yet implemented; no existing todo. Implement as a `ShipPart` in `storage.py` or a new section of
`power.py`; wire into fuel accounting so the ship can jump without dedicated fuel tanks when collectors
provide sufficient capacity.

## Fuel Refinery

Implement the on-board fuel refinery as a ship component.

Reference: `refs/hg/28_fuel_refinery.md`

Three TL tiers (7, 10, 13) with different output rates, power draw, crew requirements, and MCr/ton costs.
A fuel refinery allows processing of unrefined fuel into refined fuel. Also adds an operator crew role.

## Screens

Implement screens (Meson Screen, Nuclear Damper, Black Globe Generator) as ship components.

Reference: `refs/hg/22_screens.md`

Currently screens are referenced in two crew-count todos but do not exist as ship parts.
Once added to `weapons.py` or a dedicated `screens.py`, wire them into:

- hardpoint/firmpoint allocation (screens occupy turret hardpoints)
- power accounting
- `_commercial_gunner_count` / `_military_gunner_count` (see existing todos)

Black Globe Generator is TL15+, not commercially available — needs a legality note.

## Hull modifications (remaining validation)

Complete the remaining specialised hull modification work.

References: `refs/hg/05_specialised_hull_types.md` and `refs/hg/23_spacecraft_options.md`

Already implemented:

- **Reinforced Hull** — +50% hull cost, +10% hull points
- **Light Hull** — −25% hull cost, −10% hull points
- **Armoured Bulkhead** — 10% of protected item's tonnage, MCr0.2/ton, with protected-area notes
- **Pressure Hull** — 25% of total tonnage, ×10 hull cost, intrinsic Armour +4

(Military Hull already tracked separately above.)

Remaining work:

- validate incompatible hull combinations if any source rule requires it
- implement `reflec: bool` cost on `Hull`: MCr0.1 per ton of hull, +3 armour protection against
  lasers; validate that reflec and stealth are not combined on the same hull

## Adjustable Hull [todo]

Reference: `refs/hg/23_spacecraft_options.md`

An adjustable hull changes its outline to mimic any other ship of the same tonnage, hull
configuration, and options. All weapons on an adjustable hull get pop-up mountings at no extra
cost.

Two TL tiers:

| TL | Tons        | Cost            |
|----|-------------|-----------------|
| 12 | +5% of hull | +10% base hull  |
| 15 | +1% of hull | +100% base hull |

Not currently modelled. This is a specialist/military option; decide whether it belongs in
`hull.py` as a flag or as a `HullOption` subpart.

## Detachable Bridge [todo]

Reference: `refs/hg/23_spacecraft_options.md`

A detachable bridge can be ejected in emergencies. It has two weeks of life support and battery
power, and basic manoeuvring (effective Thrust 0). Adds +50% to bridge cost and +20% to bridge
tonnage. Minimum sizes by ship displacement:

| Ship Size          | Min Bridge Size |
|--------------------|-----------------|
| ≤200 tons          | 15 tons         |
| 201–1,000 tons     | 30 tons         |
| 1,001–2,000 tons   | 50 tons         |
| >2,000 tons        | 80 tons         |

Not currently modelled. Implement as `detachable: bool = False` on `Bridge`.

## Cockpit options (Dual Cockpit, Ejector Seat) [todo]

Reference: `refs/hg/09_step_5_install_bridge.md`

A **dual cockpit** provides space for an additional crew member (sensor operator or gunner).
It consumes 2.5 tons and costs Cr15,000.

An **ejector seat** can be added to any cockpit at Cr5,000 per seat (no additional tonnage).

Neither option is currently modelled. Cockpits have `holographic: bool` but no dual or ejector-seat fields.

Remaining work:

- add `dual: bool = False` to `Cockpit`; add 2.5 tons and Cr15,000 when set
- add `ejector_seat: bool = False` to `Cockpit`; add Cr5,000 when set

## Emergency Low Berth [todo]

Reference: `refs/hg/13_step_11_install_staterooms.md`

An emergency low berth holds up to 4 people in dire circumstances. It consumes 1 ton, costs
MCr1, and requires 1 Power. Regular low berths are already modelled in `habitation.py`; the
emergency variant is absent.

Remaining work:

- add `EmergencyLowBerth` to `habitation.py` (1t, MCr1, 1 Power, occupant capacity 4)
- wire it into `HabitationSection` alongside `low_berths`
- include occupant capacity in crew/passenger capacity calculations

## Breakaway Hulls [todo]

A ship can be designed to separate into two or more independently operating
sections. Each section must have its own bridge and power plant; drives, weapons,
and screens are optional per section but combined while docked. The separation
mechanism consumes 2% of the combined hull tonnage at MCr2/ton. Hull points
of each section are proportional to the total.

Reference: `refs/hg/05_specialised_hull_types.md`

Current status:

- `breakaway: bool` field exists on `HullConfiguration` but has no effect on
  cost, tonnage, or validation

Remaining work:

- decide whether breakaway sections are modelled as a single `Ship` with a
  sub-structure, or as two separate `Ship` objects linked by a relation
- implement the 2% tonnage + MCr2/ton cost for the separation mechanism
- validate that each section has at least a bridge and a power plant
- drive/weapon combining while docked is likely out of scope until a
  multi-section model exists

## Spinning hull configurations (Double Hull, Hamster Cage)

Reference: `refs/hg/05_specialised_hull_types.md`

Allows artificial gravity through rotation instead of grav plates (relates to Non-Gravity Hull).
Both require dedicated spin machinery (0.1 tons per ton of spun section) and increase hull cost
per percent of spun hull. Hamster cage requires ring radius ≥15m.

Probably out of scope until Non-Gravity Hull and the spin-radius calculation have a clear policy.

## Launch Tube and Recovery Deck [todo]

Reference: `refs/hg/26_drones.md`

**Launch Tube** (TL9): launches up to 10 craft per space-combat round. Consumes tonnage equal to
10× the size of the largest craft it must launch. MCr0.5/ton, 1 Power/ton. Each craft using it
still needs its own docking space or full hangar.

**Recovery Deck**: counterpart to launch tube — recovers up to 10 craft per round. Consumes 10×
the size of the largest craft it must recover. MCr0.5/ton, 1 Power/ton. Open to vacuum; cannot
function as a full hangar.

Not yet implemented; no existing todo. Good candidates for `crafts.py` alongside `FullHangar`
and `InternalDockingSpace`.

## Grav Screen [todo]

Reference: `refs/hg/26_drones.md`

Blocks densitometers (returns error codes). Presence of grav screen is itself obvious to sensor
operators. TL12, 1 ton per 200 tons of hull, MCr1/ton, 2 Power/ton.

Not yet implemented; no existing todo. Implement in `systems.py` as a `ShipPart`.

## Gravity Well Generator [todo]

Reference: `refs/hg/34_exotic_technology.md`

Creates an artificial gravity well that affects nearby vessels (tactical effect). TL16, 100 tons,
MCr120, 500 Power.

Not yet implemented; no existing todo. Implement in `systems.py`. The ship-building side is
tonnage/cost/power; combat effects are out of scope.

## Jump Filter [todo]

Reference: `refs/hg/35_jump_filters_and_psionics.md`

Prevents ships from jumping into the equipped vessel's surrounding space by detecting jump drive
initiation and disrupting emergence. TL14, no tonnage, 5 bandwidth, 1 Power, MCr5.

Not yet implemented; no existing todo. Implement in `computer.py` (software/hardware hybrid) or
`systems.py`. No tonnage required, so it is unusual — decide whether to model it as a software
package (like `JumpControl`) or as a zero-ton hardware system.

## Psionic Technology [todo]

Reference: `refs/hg/35_jump_filters_and_psionics.md`

Three ship components enabling psionic operation or defence. None currently implemented:

- **Psion Stateroom** (TL12, 4t, MCr2): enhanced stateroom for psionic crew; includes psionic
  shielding and amplification equipment. Good candidate for `habitation.py` alongside `HighStateroom`.
- **Psionic Shielding — Interior** (TL12, 0.25t per shielded room, MCr0.1 per room): blocks
  telepathic intrusion into a specific room. Implement as an option on staterooms/compartments or
  as a standalone part in `systems.py`.
- **Psionic Shielding — Exterior** (TL16): shields the entire ship's hull against psionic detection
  and intrusion; different tonnage/cost formula. Implement in `systems.py`.

Psionic Capacitor (TL18) is out of scope.

## Concealed Compartment [todo]

Reference: `refs/hg/26_drones.md`

Hidden space shielded against sensors. Up to 5% of ship tonnage. Inflicts DM-2 to Electronics
(sensors) and DM-4 to Investigate checks. Cr20,000/ton.

Not yet implemented; no existing todo. Appears in published scout and free trader designs.
Implement in `systems.py`; note that the tonnage is deducted from cargo or other space.

## Booby-Trapped Airlock [todo]

Reference: `refs/hg/26_drones.md`

Lethal defensive equipment fitted to any existing airlock. Four TL tiers (TL6–TL12), no extra
tonnage.

| TL | Cost   | Damage/Round |
|----|--------|--------------|
| 6  | MCr0.1 | 3D           |
| 8  | MCr0.3 | 5D           |
| 10 | MCr0.5 | 6D           |
| 12 | MCr1   | 8D           |

Not yet implemented; no existing todo. Implement as an optional flag or sub-part on `Airlock`
in `systems.py`. Damage is relevant for ship spec notes; the actual combat mechanic is out of
scope for ship building.

## Construction Deck [todo]

Reference: `refs/hg/26_drones.md`

A mobile shipyard capable of building and repairing ships whose tonnage is at most half the
construction deck's own tonnage. MCr0.5/ton, 1 Power/ton. Appears on very large civilian
vessels and some megacorporate ships.

Not yet implemented; no existing todo. Implement in `systems.py`. Ship-building capability
note is relevant; the actual construction simulation is out of scope.

## Optional label on parts [todo]

Published designs often give bespoke names to generic components — a yacht's common area appears
as "Studio + Trophy Lounge", a scout ship's cabin space as "Owner's Cabin". These are not distinct
part types; they are named instances of existing parts.

Consider adding an optional `label: str | None = None` field broadly — possibly to all `ShipPart`,
or even all `CeresPart` — so the spec sheet can render "Studio + Trophy Lounge (Common Area)"
rather than just "Common Area". The label would be purely cosmetic: no effect on tonnage, cost,
power, validation, or grouping unless explicitly decided otherwise.

Remaining work:

- decide the right level: `ShipPart`, `CeresPart`, or per-class
- add the field and thread it through the spec context / Typst template so it renders correctly

## Common Area Extras: Brewery, Gourmet Kitchen, Zero-G Room [todo]

Reference: `refs/hg/26_drones.md`

Three common-area extras that appear alongside the already-implemented Hot Tub, Swimming Pool,
Theatre, and Wet Bar, but are not yet modelled:

- **Brewery / Distillery** (TL10, 0.5t per 10 litres/week, MCr0.1/ton)
- **Gourmet Kitchen** (1t per diner, MCr0.2/ton; requires Steward 2, DM+1 when seeking high
  passengers)
- **Zero-G Room** (any size; Cr50,000 for controls and safe-access portal, no tonnage stated)

Not yet implemented. Implement in `systems.py` alongside the existing common-area parts.

## Carronade [todo]

Reference: `refs/companion/56_starship_weaponry.md`

A short-ranged plasma weapon occupying 4 hardpoints. Two variants:

| Weapon           | TL | Power | Damage | Cost  | Tons | Traits          |
|------------------|----|-------|--------|-------|------|-----------------|
| Plasma Carronade | 10 | 35    | 12D    | MCr10 | 4    | Weak            |
| Fusion Carronade | 12 | 45    | 16D    | MCr12 | 4    | Radiation, Weak |

The **Weak** trait doubles the target's armour score against damage — devastating against
unarmoured ships, weak against armoured ones. The Carronade consumes 4 hardpoints, which is
unusual — no existing Ceres mount type spans multiple hardpoints. Decide whether this is modelled
as a fixed mount occupying 4 hardpoints, or as a special mount class.

## General-Purpose Mass Driver Bay [todo]

Reference: `refs/companion/56_starship_weaponry.md`

A low-powered mass driver primarily used for launching ore or cargo to remote destinations
(mining ships), secondarily for orbital bombardment or mine/satellite deployment. TL8, 50 tons
(small bay), 10 Power, 4D damage, MCr4. Suffers DM-4 to attack rolls against manoeuvring
targets. Additional launch capacity: 2 tons per extra ton, Cr75,000/ton, 3 Power/ton.

Not the same as the High Guard orbital-strike mass driver. Implement as a separate bay class in
`weapons.py`.

## Torpedo-Interceptor Cluster [todo]

Reference: `refs/companion/56_starship_weaponry.md`

A one-shot point-defence hardpoint fitting (not a turret). A cluster of 4 interceptors occupies
1 hardpoint, 1 ton, MCr1, 1 Power. Fired at the last instant before missile/torpedo impact;
each interceptor kills one incoming missile on 6+ or torpedo on 8+ (2D roll). Must be replaced
dockside after firing.

Not yet modelled. The one-shot nature and per-interceptor kill probability are operational
effects; the ship-building side is tonnage, cost, power, and hardpoint allocation.

## Hullcutter Bay (TL16) [todo]

Reference: `refs/companion/56_starship_weaponry.md`

A beam of exotic particles that degrades armour as it damages. The **Reductor** trait reduces
the target's armour by -1 for each damage die rolled (applied before damage). Three sizes:

| Weapon               | TL | Power | Damage | Cost   | Tons |
|----------------------|----|-------|--------|--------|------|
| Large Hullcutter Bay | 16 | 100   | 12D    | MCr110 | 500  |

(Small at TL18 and Medium at TL17 are out of scope.)

Not yet modelled. Implement as `LargeHullcutterBay` in `weapons.py`. The Reductor trait is an
operational combat effect; only tonnage/cost/power need to be modelled for ship building.

## Pop-Up Mounting [todo]

Reference: `refs/hg/16_turrets_and_fixed_mounts.md`

A pop-up mounting conceals a turret or fixed mount in a pod or recess. A ship with all weapons
in pop-up mounts appears unarmed to external sensor scans. TL10, adds +1 ton and MCr1 to any
turret or fixed mount.

Not yet implemented; no existing todo.

Remaining work:

- add `pop_up: bool = False` to `_Turret` and `FixedMount`; add 1 ton and MCr1 when set
- wire a note into the weapon description indicating the mount is concealed

## Hardened Systems — General Investigation [todo]

References: `refs/hg/10_step_6_install_computer.md`, `refs/hg/26_drones.md`,
`refs/hg/17_particle_beam.md`, `refs/hg/43_fleet_evaluation.md`

`Computer` already supports `/fib` (+50% cost, ion immunity). The broader rule from HG is:

> Any system that draws power from the power plant can be Hardened to render it immune to Ion weapons. A Hardened system has its cost increased by +50%.

This implies every powered `ShipPart` could carry a `hardened: bool` flag. The fleet combat trait
"Hardened" (from `43_fleet_evaluation.md`) requires ≥75% of powered systems to be Hardened.

Before implementing, investigate:

- Which published ship designs include hardened non-computer systems? How common is this in practice?
- Is this a per-part flag, a hull-level option, or something else?
- How does the 75%-threshold fleet trait interact with the per-part model?
- Does radiation shielding's "treats the bridge as if Hardened" need to be modelled separately, or is it purely an operational note?

## Incomplete Customisation Advantages and Disadvantages [todo]

Reference: `refs/hg/29_customising_ships.md`

The customisation framework (EarlyPrototype through HighTechnology grades, `CustomisableShipPart`)
is in place and used on drives, jump drives, power plants, screens, and weapons. EnergyEfficient,
SizeReduction, LongRange, HighYield, VeryHighYield are already coded.

The following specific modifications from HG are not yet implemented:

**Weapons:**

- Accurate (DM+1 to attack, 2 Advantages)
- Easy to Repair (DM+1 repair attempts, 1 Advantage)
- Intense Focus (AP+2, lasers and particle only, 2 Advantages)
- Resilient (critical hit Severity -1, 1 Advantage)
- Inaccurate (DM-1 attacks, 1 Disadvantage)

**Jump Drive:**

- Decreased Fuel (-5% fuel, 1 Advantage)
- Early Jump (90-diameter limit, 1 Advantage)
- Stealth Jump (reduced emergence radiation signature, 2 Advantages)
- Energy Inefficient (+30% Power, 1 Disadvantage)
- Late Jump (150-diameter limit, 1 Disadvantage)

**Reaction Drive:**

- Fuel Efficient (-20% fuel, 1 Advantage)
- Fuel Inefficient (+25% fuel, 1 Disadvantage)

**Power Plant:**

- Increased Power (+10% output, 2 Advantages)

**Manoeuvre Drive:**

- Limited Range (within 100-diameter limit only, 2 Disadvantages)
- Orbital Range (within Short range of a planet only, 2 Disadvantages)

Decide which to prioritise based on occurrence in published ship designs.

## Portable Computer Options and Specialised Computer Variants

Tracked as code TODOs in `src/ceres/gear/computer.py` but not yet implemented.

Portable options: Camera, Comms, Data Display/Recorder, Data Wafer, Physical User Interface (all TL8+
or TL13).

Specialised variants:

- Intelligent Interface (TL8, ×5 cost of standard computer)
- Intellect (TL9, ×10 cost of standard computer)

## Additional sensor suites

Reference: `refs/hg/26_drones.md` (sensors section, pages 54–63)

Several sensor modules listed in HG are not yet modelled:

- Countermeasures Suite
- Deep Penetration Scanners
- Distributed Array / Extended Array / Extension Net
- Life Scanner
- Mail Distribution Array
- Mineral Detection Suite
- Rapid-Deployment Extended Arrays
- Shallow Penetration Suite
- Signal Processing System

## External attachment systems

Reference: `refs/hg/26_drones.md` (external systems section)

Only `DockingClamp` is currently in `crafts.py`. Still missing:

- Breaching Tube
- Forced Linkage Apparatus
- Holographic Hull

Implemented: `GrapplingArm`, `TowCable` (in `systems.py`).

External loads from grappling/tow should feed into effective displacement for drive performance
(related to the Modulars and effective displacement item above).

## Space stations as a build target

Reference: `refs/hg/27_space_stations.md`

Space stations use almost the same design sequence as ships but with a few differences:

- No streamlined config; most use dispersed structure.
- Manoeuvre drive with Thrust 0 (orbital correction) is 0.5% of hull tonnage at MCr2/ton.
- Power and crew rules differ slightly.
- Can include mineral refineries, manufacturing plants, and other industrial facilities.

Decide whether `Ship` should be extended or whether a separate `Station` class is warranted.

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
