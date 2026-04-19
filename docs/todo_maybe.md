# List of potential things to do

## Naming

Should self.owner be self.ship instead?


## Software Singleton [done]

Note that Software Packages are Singletons

If user e.g. lists JumpContrl/2 and then JumpControl/3,
they have (and pay for) JumpControl/3, and a warning that
redundant JumpControl/2 was added. Note the included
JumpControl SW in Core models. I assume that if your main
is a Core, and your spare is a (non Core) computer, it
can still run the Core supplied SW within the capacity of
its rating.

## Quantities [done]

If we have 10 staterooms, it should say Staterooms ✕ 10.
The same is probably true for many other items. If it's
just one, it can just say Stateroom.

Current status:

- done for Staterooms
- done for Low Berths
- done for Probe Drones
- done for grouped spec rows such as Airlocks
- done for crew table rows

## Decentralize build_spec [done]

Move substantial parts of Ship.build_spec() out to the
sections that own the rows, such as storage, computer,
habitation and systems.

Current status:

- done for hull
- done for drives / power
- done for storage (fuel + cargo)
- done for command
- done for computer
- done for sensors
- done for habitation
- done for systems
- done for weapons
- done for craft

Note:

- expense / crew summary now live in `expense.py` and `crew.py`
- a couple of generic row-grouping helpers still remain in `Ship`, but the section-level decentralization itself is complete

## Implement armoured bulkhead [done]

Armoured bulkheads protect specific areas and
systems, such as the jump drive or fuel tanks, making
them much more resilient to damage.
Adding armoured bulkheads consumes an amount of
space equal to 10% of the tonnage of the protected
item. During space combat, the Severity of any critical
hit to the protected space is reduced by -1 (to a
minimum of Severity 1).

Option Cost
Armoured Bulkhead MCr0.2 per ton

Current status:

- `ArmouredBulkhead` implemented in `hull.py`
- cost and tonnage modeled
- protection target shown in spec notes
- treated as a ship-design/spec concern, not as combat simulation logic

## Limit TL [done]

Make a note in ARCHITECTURE.md that support is limited to TL16 and lower, and
stick to that when writing code. For now we cap ship TL to 16 and don't bother
to implement TL17+ features.

Current status:

- `ARCHITECTURE.md` now states the TL16 cap explicitly
- `Ship` now rejects `tl > 16`
- TL17+ features are intentionally out of scope for now

## Sort out weapons.py [doing]

All ships have hardpoint in proportion to displacement, except smallcraft which have firmpoints.

Fixed mounts, turrets, barbettes and bays can be mounted in hardpoints of firmpoints (not bays in firmpoints).

Some weapons are designed to be mounted either on fixed mounts or turrests, some on barbettes and some in bays.

Firmpoint mounting of weapons reduces/limits range and reduces power.

The code as written matches the rules structure poorly.

Current status:

- hardpoint / firmpoint capacity checks implemented
- small craft restriction to single turrets implemented
- turret API simplified to `Turret(size='single'|'double'|'triple', weapons=[...])`
- `FixedMount` and `Turret` now share the same `MountWeapon(...)` weapon model
- `Barbette`, `Bay`, `PointDefenseBattery`, and `MissileStorage` are modeled
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
- large ship crew reduction implemented
- remaining work is further rule expansion and validation, not structure

Remaining ideas:

- understaffing warning if explicitly stated crew is too small
- steward / passenger rules
- decide whether ship role inference should remain explicit (`military=True`) or become partly automatic
- model how automation can change crew needs.

## Expense module [done]

Break out expense code to its own module expense.py


### Large ships crew reduction

For ships of more than 5,000 tons, the
Referee can reduce the required crew by multiplying
the crew complement by the Crew Reduction Multipler
in the Crew Reduction table.

Crew reductions can only be applied to the following
roles: engineer, maintenance, gunner, administrators
and sensor operators. Calculate officers and medics
after reducing the other roles.

Crew Reduction
Ship Size Crew Reduction Multiplier
5,001–19,999 75%
20,000–49,999 67%
50,000–99,999 50%
100,000+ 33%

For the displacement based roles, maintenance &
sensor operators, make sure you don't need more than
a larger ship, i.e. min(crew_need(displacement), crew_need(next limit))

## Combine propulsion and jump sections [done]

Maybe it's better to combine jump and propulsion to a drives section?

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


