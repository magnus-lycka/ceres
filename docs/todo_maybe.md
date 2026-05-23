# List of potential things to do

Update todo items in this document as progress is made.
When todo items are done, please move them
to docs/archive/done_todos.md

## Weapon coverage follow-up [todo]

The core weapon model has been split into concrete fixed mounts, turrets, barbettes, bays,
spinal mounts, point-defence batteries, carronades, and ammunition/storage parts.

Remaining work is coverage and policy rather than the broad model refactor:

- firmpoint range limitations are not yet modelled, only power/capacity effects
- weapon families and mount compatibility are still incomplete
- broader weapon coverage is still incomplete for some mountable weapon families

## Crew role inference [todo]

Crew calculation is implemented in `crew.py` and `Ship` delegates to it for commercial and
military crew analysis.

Remaining policy question:

- decide whether ship role inference should remain explicit (`military=True`) or become partly
  automatic

Automation crew effects have been split into a separate item below.

## Screens source coverage and Black Globe [todo]

Meson screens, nuclear dampers, deflector screens, and energy shields are modelled in
`screens.py`. Screen gunners are counted in commercial and military crew analysis.

Remaining work:

- broader source coverage for meson screens and mixed screen installations
- implement **Black Globe Generator** (TL15): absorbs all damage into a capacitor bank; legality
  note needed (not commercially available)
- decide how to model capacitor bank, energy bleed, and overload mechanics for Black Globe

## Spinal mount source coverage [todo]

Mass driver, meson, particle accelerator, and railgun spinal mounts are modelled from the High
Guard spinal mount table, including TL improvement rows and ammunition cargo helpers for mass
driver and railgun spinal mounts.

Remaining work:

- add broader source test coverage for non-meson spinal mount TL improvements and other spinal
  mount families

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
- **Reflec** — MCr0.1 per ton of hull, +3 armour protection against lasers, incompatible with
  stealth

(Military Hull already tracked separately above.)

Remaining work:

- validate incompatible hull combinations if any source rule requires it

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
