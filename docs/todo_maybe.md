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

## Screens in gunner count [todo]

The High Guard crew table requires gunners for screens:

- commercial: 1 gunner per screen
- military: 2 gunners per screen

Screens are not yet modelled as a weapon-system component, so they cannot
be counted. Once screens are implemented in `weapons.py`, wire their count
into `_commercial_gunner_count` and `_military_gunner_count`.

## Spinal mounts in military gunner count [todo]

The military crew table requires 1 gunner per 100 tons of spinal mount
weaponry. Spinal mounts are not yet modelled. Once implemented, add a
`_spinal_mount_tonnage` helper and include `ceil(spinal_tons / 100)` in
`_military_gunner_count`.

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

Examples to sort out:

- modular cutters with and without installed modules
- large modular warships whose published thrust / jump assume a larger loaded
  displacement than the stripped hull line item
- docking clamps and other external carried craft
- jump shuttles, jump nets, and drop tanks

Current concern:

- some published designs clearly distinguish between the ship's own built
  displacement and the larger displacement that drives must handle in a
  particular carried / loaded state
- other calculations such as maintenance, much of crew analysis, and structural
  build cost may still want the ship's own design displacement rather than the
  loaded one

Rule for future work:

- do not flatten all such cases into one single `displacement` concept
- be prepared to distinguish between at least:
  - design / structural displacement
  - effective in-flight displacement for performance
- support parameterized outputs where needed, e.g. `Thrust X / Jump Y while
  carrying Z dTons`

## Reaction drives

Handle R-drives in additioin to M-drives and J-drives

Note:

- when we later add external carry systems such as docking clamps, tow cables, cargo nets, external cargo mounts, jump nets, jump shuttles, modular cutter handling or similar, they should not be treated like internal docking space
- external loads should affect effective displacement for drive-performance calculations
- this likely wants parameterized specs, e.g. performance at `+X dTons`

## Handle non-fusion power plants

Support Chemical and Fission drives.

## MASSIVE SHIPS

Very large ships require a lot more internal bracing to support their mass under acceleration but this has the effect of increasing their durability under fire. Ships of 25,000–99,999 tons have 1 Hull point for every 2 tons of hull. Ships of 100,000 tons or more have 1 Hull point for every 1.5 tons of hull.

## COMMAND BRIDGES

A command bridge adds 40 tons to an existing
bridge, can be used by any ship of more than 5,000
tons and adds an additional MCr30 to the cost of the
bridge. The command bridge grants DM+1 to all Tactics
(naval) checks made within it.

## Military Hull

By increasing the cost of a hull by +25%, a ship may install armour up to double its standard rating. For example, a non-military hull made of bonded superdense has a maximum armour value equal to the Tech Level of the ship, as described in the Hull Armour table on page 13. However, a ship with a military hull may add up to double that value in armour. Military hulls can only be applied to capital ships (greater than 5,000 tons) and can stack with the reinforced hull option.

## Non-Gravity Hull

Basic hulls include artificial gravity, using grav plates to ensure a normal gravitational environment for the comfort and convenience of the crew. Hulls can be built cheaper without artificial grav plating, using specific configurations that allow the hull to constantly spin in order to generate gravity if desired. Non-gravity hulls reduce hull cost by 50% but are limited to a maximum size of 500,000 tons due to structural limitations. Base Power Requirements for non-gravity hulls are half that of other hull types. See Power Requirements on page 17 for more information.

*To use this and still get artificial gravity the ship must be able to spin. It could be a torus, a cylinder or something like a capsule connected to a counterweight with a wire (of course it could be two capsules acting as counterweights to each other, but you might have heavy stuff, like power plant, where you don't need full gravity). Either way, the spin radius must be big enough to make this more good than bad. One can of course settle for less than 1G gravity, but there are several well known issues. Both torus and capsule with counterweight would -- I think be dispersed structure. A cyliner, wgich could be a standard structure, would have to be huge, and either a lot of wasted space or most areas wouls have much less gravity. With rotation, there are several issues, which all get worse with less radius (which also means faster rotation): Things fall in tangential direction, not at all same as perceived down. Coriolis effects are stronger. Rapid spin makes people dizzy etc. All of this will place a lower bound on reasonable radius. Of course, working in Zero-G with penaltiess is an option.*

## Culture property etc

Ships are buit differently for different audiences.
This is partly the biology of different species, but also a matter of
culture and various practical things, e.g. human stock living in very
different worlds, from aquatic to free space to High G etc.

The sophont names in https://travellermap.com/t5ss/sophonts could be useful,
and https://travellermap.com/t5ss/sophonts as well as 'other', 'independent' etc.

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

## Verify that we don't collapse things unless they are identical

If we for instance hace two triple turrets with all pulse lasers
we basically want to see

Triple Turret x 2
 - Weapon: Pulse Laser x 3

But on the other hand, if we have this:

Triple Turret
 - Weapon: Pulse Laser x 3
Triple Turret
 - Weapon: Missile x 2
 - Weapon: Sandcaster

 Then we can't compact it any more than we did.
 We can't make a Triple Turret x 2, since they are different.

## Split big files

     632 src/ceres/make/ship/drives.py

Separate into drives and powerplants

    1215 src/ceres/make/ship/weapons.py

Split up the big weapons file

## Add other types of drives

Add the lower TL power plants, fission, chemichal?
Are there things like batteries as well than should go here?
Solar panels and stuff?

## Solar Energy Systems

Implement solar panels and solar coatings as an alternative/supplemental power source.

Reference: `refs/hg/25_solar_energy_systems.md`

Four tiers (Basic TL6 through Advanced TL12) for both solar coating and solar panels.
Rules include:

- Solar coating only works on standard/sphere configurations; reduced 50% on close-structure/dispersed;
  not available on streamlined (atmospheric stress).
- Solar panels are deployed (cannot accelerate while deployed), measured in tons = units.
- Coatings increase hull repair cost ×2.

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

## Hull modifications (Reinforced, Light, Armoured Bulkhead, Pressure Hull)

Implement the specialised hull modification options.

References: `refs/hg/05_specialised_hull_types.md` and `refs/hg/23_spacecraft_options.md`

Missing hull type modifiers:

- **Reinforced Hull** — +50% hull cost, +10% hull points
- **Light Hull** — −25% hull cost, −10% hull points

(Military Hull already tracked separately above.)

Spacecraft structural options not yet modelled:

- **Armoured Bulkhead** — 10% of protected item's tonnage, MCr0.2/ton, reduces critical-hit
  severity by −1 for the protected area
- **Pressure Hull** — 25% of total tonnage, ×10 hull cost, intrinsic Armour +4, allows very
  deep gas-giant and ocean operations

## Spinning hull configurations (Double Hull, Hamster Cage)

Reference: `refs/hg/05_specialised_hull_types.md`

Allows artificial gravity through rotation instead of grav plates (relates to Non-Gravity Hull).
Both require dedicated spin machinery (0.1 tons per ton of spun section) and increase hull cost
per percent of spun hull. Hamster cage requires ring radius ≥15m.

Probably out of scope until Non-Gravity Hull and the spin-radius calculation have a clear policy.

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
- Grappling Arm
- Holographic Hull
- Tow Cable

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

## Get rid of silly singular properties

class SystemsSection(CeresModel):
...

    def first_internal_system_of_type(self, system_cls: type[_T]) -> _T | None:
        matches = self.internal_systems_of_type(system_cls)
        return None if not matches else matches[0]

This is just silly! Remove properties like SystemsSection.medical_bay since there can be >1.
