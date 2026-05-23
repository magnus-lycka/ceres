# Completed todo items

Moved from `docs/todo_maybe.md` once fully implemented.

## Naming

Renamed `self.owner` → `self.ship` and `_owner` → `_ship` throughout `parts.py` and all subclasses.

## Software Singleton

Note that Software Packages are Singletons

If user e.g. lists JumpContrl/2 and then JumpControl/3,
they have (and pay for) JumpControl/3, and a warning that
redundant JumpControl/2 was added. Note the included
JumpControl SW in Core models. I assume that if your main
is a Core, and your spare is a (non Core) computer, it
can still run the Core supplied SW within the capacity of
its rating.

## Quantities

If we have 10 staterooms, it should say Staterooms ✕ 10.
The same is probably true for many other items. If it's
just one, it can just say Stateroom.

Current status:

- done for Staterooms
- done for Low Berths
- done for Probe Drones
- done for grouped spec rows such as Airlocks
- done for crew table rows

## Decentralize build_spec

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

## Implement armoured bulkhead

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

## Limit TL

Make a note in ARCHITECTURE.md that support is limited to TL16 and lower, and
stick to that when writing code. For now we cap ship TL to 16 and don't bother
to implement TL17+ features.

Current status:

- `ARCHITECTURE.md` now states the TL16 cap explicitly
- `Ship` now rejects `tl > 16`
- TL17+ features are intentionally out of scope for now

## Expense module

Break out expense code to its own module expense.py

## Combine propulsion and jump sections

Maybe it's better to combine jump and propulsion to a drives section?

## x vs ×

Counted labels now go through shared helpers in `ceres.make.ship.text`, so the display form is consistently `×`
instead of `x`, and repeated labels are collapsed in one place instead of being reimplemented separately.

## Large ship crew reduction cap

For displacement-based roles the crew reduction for large ships should not
result in more crew than the next bracket above would require.

Implemented by restructuring the bracket data into `_LARGE_SHIP_BRACKETS` and
adding `_next_crew_reduction_multiplier`. `_apply_large_ship_reduction` now
applies `min(result, ceil(count × next_multiplier))` for any ship in the
reduction zone, preventing a ship just below a bracket boundary from needing
more crew than one just above it. The cap is not applied to ships ≤ 5,000 dTons
(outside the large-ship reduction zone).

## Medic passenger count

The commercial medic rule is "1 per 120 crew **and** passengers." Previously
only crew count was used.

Added `_habitation_population` which sums stateroom `.occupancy`, low berth
count, and `cabin_space.passenger_capacity`. Both `_commercial_roles` and
`_military_roles` now use this as the population denominator when habitation is
present (covering crew and passengers sharing the same accommodation), falling
back to `len(roles)` for ships with no habitation such as small craft.

## Remove singular SystemsSection accessors

Removed `SystemsSection.first_internal_system_of_type` and singular convenience
properties such as `medical_bay`, `library`, `briefing_room`, `workshop`, and
`biosphere`. Repeated internal systems are now accessed through list-returning
properties such as `medical_bays`, `libraries`, `briefing_rooms`, `workshops`,
and `biospheres`, or through `internal_systems_of_type(...)`.

## Handle non-fusion power plants

Chemical and fission power plants are implemented in `power.py`, accepted by
`PowerSection`, covered by unit tests, and represented in operation-fuel tests.

Sterling fission plants are also implemented from the Spinward Extents rules,
including TL6/TL8/TL12 variants, lifespan, minimum size, no operation-fuel
tonnage, and warnings for direct jump-drive use.

## Reaction drives

R-drives are implemented alongside M-drives and J-drives, including high-burn
thruster notes and reference-ship coverage for the 90-ton non-gravity R-drive
case.

The remaining external-load performance policy has been kept in
`docs/todo_maybe.md` under "External-load drive performance".

## Initial hull modifications

Reinforced Hull and Light Hull are implemented as `HullConfiguration` options,
affecting hull cost and Hull points.

Armoured Bulkhead is implemented as a protected-part option plus explicit hull
component, with cost, tonnage, spec notes, and tests.

Pressure Hull is implemented with 25% tonnage usage, ×10 hull cost, intrinsic
Armour 4, spec output, and tests.

Any remaining validation rules for incompatible hull combinations remain in
`docs/todo_maybe.md`.

## Verify that we do not collapse non-identical rows

Spec row grouping and report-row collapse already require matching item labels
and display notes. Added a regression test covering two different triple
turrets:

- two identical pulse-laser turrets may collapse to `Triple Turret × 2`
- a pulse-laser turret and a missile/sandcaster turret remain separate rows

The test covers both raw `ShipSpec` weapon rows and `collapsed_main_rows(...)`
used by reports.

## Massive ship Hull points

Very large ships now use the High Guard Hull point scaling:

- 25,000-99,999 tons: 1 Hull point per 2 tons
- 100,000+ tons: 1 Hull point per 1.5 tons

Existing configuration modifiers such as Reinforced Hull and Light Hull still
apply before the divisor.

## Non-gravity hull maximum size

Non-gravity hulls now report a ship error above the 500,000-ton maximum size.

The remaining spin-layout modelling question stays in `docs/todo_maybe.md`.

## Command Bridge

Command bridges are implemented as a separate `CommandBridge` internal system,
not as a variant of the ship-control bridge.

They add 40 tons, add MCr30 to bridge cost, require ship displacement greater
than 5,000 tons, and add a spec note for DM+1 to Tactics (naval) checks made
within the command bridge.

## Cargo handling equipment

Cargo handling equipment from High Guard is implemented in `storage.py` and
rendered in the Cargo section of ship specs.

Implemented parts:

- `CargoCrane`: tonnage = 2.5 + 0.5 per 150 tons or part thereof of cargo
  space; MCr1 per ton of crane; reduces usable cargo hold capacity.
- `CargoScoop`: 2 tons, MCr0.5, with operational notes for scooping floating
  cargo and failed Pilot checks.
- `CargoNet`: 5 tons, MCr1, with operational notes for tow drones and jump
  restrictions while deployed.
- `LoadingBeltTL7`: 1 ton, Cr3,000, replaces 10 loading crew.
- `LoadingBeltTL12`: 1 ton, Cr10,000, 1 Power, replaces 25 loading crew.

## External Cargo Mount

External cargo mounts are implemented in `storage.py` as
`ExternalCargoMount(capacity=...)`.

They cost Cr1,000 per ton of external cargo capacity, add no internal tonnage
or power load, cannot be installed on streamlined or dispersed-structure hulls,
and add notes that the ship is effectively unstreamlined while external cargo
is mounted.

External cargo mount capacity contributes to ship `performance_displacement`,
so drive and fuel calculations using the combined tonnage are updated.

## Jump Net

Jump nets are implemented in `storage.py` and rendered in the Cargo section of
ship specs.

Implemented variants:

- `InterplanetaryJumpNet(capacity=...)`: TL8, 1 ton per 100 tons of external
  cargo capacity or part thereof, MCr0.1 per ton of net, cannot perform jump
  while deployed.
- `InterstellarJumpNet(capacity=...)`: TL10, 1 ton per 100 tons of external
  cargo capacity or part thereof, MCr0.3 per ton of net.

Both variants add notes that the ship is effectively unstreamlined while the
jump net is deployed. Jump net capacity contributes to
`performance_displacement`, so drive and fuel calculations include the external
cargo tonnage.

## Accommodation additions

Accommodation/support options from the High Guard Spacecraft Options chapter
are implemented in `systems.py` and render in the ship spec as internal system
rows.

Implemented parts:

- `AccelerationBench`: 4 seats, 1 ton, Cr10,000, a lower-cost bench variant of
  `AccelerationSeat`.
- `MultiEnvironmentSpace(covered_tons=...)`: support equipment for unusual
  environmental conditions, adding 5% of the designated area's tonnage,
  MCr0.5 per equipment ton, and 1 Power per equipment ton.

## Vault

Vaults are implemented in `systems.py` as `Vault(tons=...)`.

They support the High Guard 4-40 ton size range, cost MCr0.5 per ton, add no
power load, and expose content-only protection values:

- `content_armour = min(10, tons)`
- `content_hull_points = tons // 5`

Spec notes state that vault armour and Hull points protect contents only, not
the ship, and that contents can survive in vacuum for a limited time if the
ship is destroyed.

## Re-entry Capsule and Re-entry Pod

Re-entry capsules and pods are implemented in `systems.py` and render in ship
specs as internal system rows.

Implemented variants:

- `BasicReEntryCapsule`: TL8, 0.5 tons, Cr20,000, capacity 1.
- `AssaultReEntryCapsule`: TL10, 0.5 tons, Cr50,000, capacity 1,
  Protection +20, DM-2 to detect.
- `HighSurvivabilityReEntryCapsule`: TL14, 0.5 tons, MCr0.1, capacity 1,
  Protection +30, DM-4 to detect, DM-2 against attacks.
- `ReEntryPod`: TL9, 1 ton, MCr0.15, capacity 2, with notes for its gliding
  surface, computer guidance, and manual Flyer (wing) control.

## Stable

Stables are implemented in `habitation.py` as `Stable(tons=...)` and render in
the Habitation section of ship specs.

They cost Cr2,500 per ton, add no power load, require a minimum size of 10
tons, and add Cr250 per ton to life support facility costs. Capacity scales
from the High Guard baseline of 10 tons housing 20 human-sized or 10
cattle-sized creatures.

## Concealed Compartment

Concealed compartments are implemented in `storage.py` as
`ConcealedCompartment(tons=...)` and render in the Cargo section of ship specs.

They cost Cr20,000 per ton, add no power load, and validate the High Guard
limit of at most 5% of ship tonnage. Spec notes include DM-2 to Electronics
(sensors) checks and DM-4 to Investigate checks made to find the compartment.

## Booby-Trapped Airlock

Booby-trapped airlocks are implemented as an optional `booby_trap` sub-part on
`Airlock`.

Implemented variants:

- `BoobyTrapTL6`: MCr0.1, 3D damage/round.
- `BoobyTrapTL8`: MCr0.3, 5D damage/round.
- `BoobyTrapTL10`: MCr0.5, 6D damage/round.
- `BoobyTrapTL12`: MCr1, 8D damage/round.

The trap adds no tonnage, adds its cost even when the airlock itself is part of
the ship's free airlock allowance, validates its TL, and renders a damage note
in the ship spec. The actual combat effect is out of scope for ship building.

## Construction Deck

Construction decks are implemented in `systems.py` as `ConstructionDeck(tons=...)`
and render in ship specs as internal system rows.

They cost MCr0.5 per ton, require 1 Power per ton, and report that they can
build or repair ships up to half the construction deck tonnage at the carrying
ship's TL. Construction simulation is out of scope.

## Optional Label On Parts

Generic display labels are implemented on `CeresModel` through
`display_label: str | None`.

The base `build_item()` renders labelled instances as
`"<display label> (<description>)"`, so generic parts can represent published
design names such as `Trophy Lounge (Common Area)` without changing tonnage,
cost, power, validation, or grouping semantics.

## Common Area Extras

Additional High Guard common-area extras are implemented in `systems.py`:

- `Brewery(litres_per_week=...)`: TL10, 0.5 tons per 10 litres/week, MCr0.1 per
  ton.
- `GourmetKitchen(diners=...)`: 1 ton per diner, MCr0.2 per ton, with notes for
  Steward 2 and DM+1 when seeking high passengers.
- `ZeroGRoom(tons=...)`: any specified room size, Cr50,000 fixed cost for
  controls and safe-access portal.

## Companion Weapon Additions

Traveller Companion starship weapon additions are implemented in `weapons.py`.

Implemented parts:

- `PlasmaCarronade`: TL10, 4 hardpoints, 4 tons, MCr10, 35 Power, 12D, Weak.
- `FusionCarronade`: TL12, 4 hardpoints, 4 tons, MCr12, 45 Power, 16D,
  Radiation and Weak.
- `GeneralPurposeMassDriverBay(extra_launch_capacity=...)`: TL8, base 50 tons,
  MCr4, 10 Power, 1 hardpoint, with optional extra launch capacity.
- `TorpedoInterceptorCluster`: TL10, 1 hardpoint, 1 ton, MCr1, 1 Power,
  one-shot system with four interceptors.
- `LargeHullcutterBay`: TL16, 5 hardpoints, 500 tons, MCr110, 100 Power, with
  Reductor noted as an operational combat effect.

Operational combat mechanics such as Weak, Reductor, and interceptor kill rolls
are represented as notes only.

## Pop-Up Mounting

Pop-up mounting is implemented on `FixedMount` and turrets through
`pop_up: bool = False`.

When enabled, it requires TL10, adds 1 ton and MCr1 to the mount, and renders a
note that the weapon system is concealed until deployed. Hardpoint/firmpoint
allocation remains the same as the underlying fixed mount or turret.

## Weapon Customisation Modifiers

Additional High Guard weapon customisation modifiers are implemented in
`weapons.py`:

- `Accurate`: 2 Advantages, note for DM+1 to attack rolls.
- `EasyToRepair`: 1 Advantage, note for DM+1 to repair attempts.
- `IntenseFocus`: 2 Advantages, note for AP+2, restricted to laser and
  particle weapons.
- `Resilient`: 1 Advantage, note for reducing weapon critical hit Severity by
  -1.
- `Inaccurate`: 1 Disadvantage, note for DM-1 to attack rolls.

They are wired into the existing customisation framework and allowed on weapon
parts that already support weapon customisation.

## Jump Drive Customisation Modifiers

Additional High Guard jump drive customisation modifiers are implemented in
`drives.py`:

- `EarlyJump`: 1 Advantage, note for jumping at the 90-diameter limit.
- `StealthJump`: 2 Advantages, note for reduced jump emergence radiation
  signature.
- `JumpEnergyInefficient`: 1 Disadvantage, +30% Power for jump drives.
- `LateJump`: 1 Disadvantage, note for requiring the 150-diameter limit before
  jumping.

## Weapon Model Refactor

The broad weapon model refactor is complete enough to close the original
`Sort out weapons.py` doing item.

Implemented structure:

- hardpoint/firmpoint capacity checks
- small craft restriction to single turrets
- concrete turret classes such as `SingleTurret`, `DoubleTurret`, and
  `TripleTurret`
- shared concrete mount weapon classes for fixed mounts and turrets
- concrete barbettes, bays, point-defence batteries, spinal mounts, and
  ammunition/storage parts
- size-reduction weapon modifiers for barbettes, bays, and point-defence
  batteries
- fixed mounts with multiple weapons and small-craft restrictions

Remaining coverage and policy questions were moved back to `todo_maybe.md` as
follow-up todo items rather than keeping the broad refactor open.

## Crew Calculation Structure

The broad crew-calculation structure is complete enough to close the original
`DETERMINE CREW` doing item.

Implemented structure:

- `crew.py` is the single source of truth for ship crew calculations
- `Ship` delegates crew analysis to `crew.py`
- commercial crew rules
- military crew rules
- large ship crew reduction, including bracket-boundary cap
- medic count uses habitation capacity as a population proxy

Remaining role-inference policy questions were moved back to `todo_maybe.md` as
follow-up todo items.

## Screens Follow-Up

The broad screens follow-up is complete enough to close the doing item.

Implemented screen support:

- `MesonScreen`
- `NuclearDamper`
- `DeflectorScreen`
- `EnergyShield`
- screen gunner counts in commercial and military crew analysis

Remaining Black Globe and source-coverage work was moved back to `todo_maybe.md`
as a focused todo item.

## Spinal Mount Follow-Up

The broad spinal mount follow-up is complete enough to close the doing item.

Implemented support:

- High Guard mass driver, meson, particle accelerator, and railgun spinal mounts
- TL improvement rows (`+1`, `+2`, `+3`)
- military gunner count for spinal weaponry
- mass driver spinal mount ammunition cargo helper
- railgun spinal mount extra rounds cargo helper

Remaining source-coverage work was moved back to `todo_maybe.md` as a focused
todo item.

## Military Hull Armour Cap

Military hull armour-cap handling is implemented.

Implemented support:

- `HullConfiguration.effective_hull_cost_modifier` applies the +25% military
  hull cost modifier.
- ships with `military=True` on hull configuration emit an error at
  displacement <= 5,000 tons.
- armour validation doubles the normal TL-derived armour cap for military
  hulls and reports a military-hull-specific error when exceeded.

## Cockpit Options

Dual cockpit and ejector seat options are implemented on `Cockpit`.

Implemented support:

- `dual: bool = False` adds space for a second crew member, +2.5 tons, and
  Cr15,000.
- `ejector_seat: bool = False` adds Cr5,000 per cockpit seat.
- cockpit display labels describe dual and ejector-seat variants.
- unit tests cover standard, holographic, dual, ejector-seat, and combined
  cockpit values.

## Emergency Low Berth

Emergency low berths are implemented in `habitation.py`.

Implemented support:

- `EmergencyLowBerth` consumes 1 ton, costs MCr1, requires 1 Power, and holds
  four occupants.
- emergency low berths are included in `HabitationSection`.
- occupant capacity is included in habitation capacity calculations.
- unit tests cover cost, tonnage, power, capacity, and section integration.

## Grav Screen

Grav screens are implemented in `systems.py`.

Implemented support:

- `GravScreen` is TL12.
- tonnage is one ton per 200 tons of hull displacement, rounded up.
- cost is MCr1 per ton.
- power requirement is 2 Power per ton.
- notes record the operational densitometer-blocking effect.
- unit tests cover scaling by ship displacement.

## Detachable Bridge

Detachable bridges are implemented on `Bridge`.

Implemented support:

- `detachable: bool = False` adds 20% to bridge tonnage.
- detachable bridges add 50% to bridge cost, combining with small and
  holographic bridge modifiers.
- bridge labels identify detachable standard, small, and holographic variants.
- minimum detachable bridge sizes are validated by displacement band:
  15 tons up to 200 tons displacement, 30 tons up to 1,000 tons, 50 tons up to
  2,000 tons, and 80 tons above 2,000 tons.
- unit tests cover tonnage, cost, item labels, and minimum-size validation.

## Gravity Well Generator

Gravity well generators are implemented in `systems.py`.

Implemented support:

- `GravityWellGenerator` is TL16.
- tonnage is 100 tons.
- cost is MCr120.
- power requirement is 500 Power.
- notes record that the artificial-gravity-well effect is tactical and out of
  scope for ship construction.
- the part is included in `AnyInternalSystem` for serialization and system
  section use.
- unit tests cover values, notes, stale numeric input handling, and computed
  property serialization.

## Launch Tube And Recovery Deck

Launch tubes and recovery decks are implemented in `crafts.py`.

Implemented support:

- `LaunchTube(largest_craft_tons=...)` is TL9.
- `RecoveryDeck(largest_craft_tons=...)` models the recovery counterpart.
- both consume tonnage equal to 10 times the largest craft they support.
- both cost MCr0.5 per ton and require 1 Power per ton.
- notes record the construction-relevant operational limits: launch tubes do
  not replace docking space/full hangars, and recovery decks are open to vacuum
  and not full hangars.
- both parts are included in `InternalCraftHousing` for serialization and craft
  section use.
- unit tests cover values, notes, TL validation, power, stale numeric input
  handling, and computed property serialization.

## Jump Filter

Jump filters are implemented in `systems.py`.

Implemented support:

- `JumpFilter` is TL14.
- tonnage is 0 tons.
- cost is MCr5.
- power requirement is 1 Power.
- bandwidth is exposed as a property with value 5; ship spec rows do not yet
  have a bandwidth column.
- notes record the construction-relevant operational effect while keeping
  detailed jump-disruption mechanics out of scope.
- the part is included in `AnyInternalSystem` for serialization and system
  section use.
- unit tests cover values, notes, TL validation, spec row output, stale numeric
  input handling, and computed property serialization.

## Psion Stateroom

Psion staterooms are implemented in `habitation.py`.

Implemented support:

- `PsionStateroom` is TL12.
- tonnage is 4 tons, matching a normal stateroom.
- cost is MCr2.
- the room is otherwise modelled as a normal stateroom, including occupancy,
  residence provision, and life-support facility cost.
- notes record the +50% PSI-regeneration effect for a psion occupant.
- the part is included in the stateroom union for serialization and habitation
  section use.
- unit tests cover values, notes, TL validation, residence/life-support
  integration, and JSON round-trip.

## Psionic Shielding

Psionic shielding is implemented in `systems.py`.

Implemented support:

- `PsionicShielding` is TL12.
- standard shielding consumes 1% of ship displacement.
- standard shielding costs MCr0.5 per ton.
- standard shielding consumes no Power.
- standard shielding notes report the size-dependent Clairvoyance and Telepathy
  effect: impenetrable below 100 tons, DM-4 up to 300 tons, DM-2 up to 500 tons,
  and no DM above 500 tons.
- `AdvancedPsionicShielding` is TL16.
- advanced shielding consumes no tonnage or Power.
- advanced shielding costs MCr1 per 100 tons, or part thereof, of ship
  displacement.
- both parts are included in `AnyInternalSystem` for serialization and system
  section use.
- unit tests cover values, notes, TL validation, stale numeric input handling,
  and computed property serialization.

Psionic Capacitor remains intentionally out of scope because Ceres currently
supports TL16 and lower.

## Power Plant Increased Power Customisation

The High Guard `Increased Power` customisation modifier is implemented for
power plants.

Implemented support:

- `IncreasedPower` is a 2-Advantage modification.
- power plants store the requested base output as the serialized `output`
  field and expose effective `.output` after customisation.
- `IncreasedPower` multiplies effective output by 1.10.
- plant tonnage remains based on base output, while customisation grade cost
  modifiers continue to apply normally.
- `PowerSection.output`, available ship power, and Power spec rows use the
  effective output.
- unit tests cover output, cost, tonnage, spec rows, notes, available power, and
  JSON/model round-trip.

## Reaction Drive Fuel Customisation

Reaction-drive fuel customisation modifiers are implemented.

Implemented support:

- `FuelEfficient` is a 1-Advantage modification and reduces reaction-fuel
  requirement by 20%.
- `FuelInefficient` is a 1-Disadvantage modification and increases
  reaction-fuel requirement by 25%.
- R-drives are now `CustomisableShipPart` instances and allow those
  reaction-drive fuel modifiers.
- `ReactionFuel` reads the installed R-drive customisation fuel multiplier.
- R-drive customisation notes are displayed alongside high-burn thruster notes
  where applicable.
- unit tests cover efficient and inefficient fuel calculations, notes, allowed
  modification handling, and JSON/model round-trip.

## Reflec Hull Option

The High Guard reflec hull option is implemented on `Hull`.

Implemented support:

- `Hull.reflec` adds a Hull spec row named `Reflec`.
- cost is MCr0.1 per ton of ship displacement.
- notes record +3 armour protection against lasers.
- reflec cost is included in production cost.
- ships with both reflec and stealth emit an error.
- unit tests cover cost, spec row output, production cost, and stealth
  incompatibility.

## Automation

Traveller Companion ship automation levels are implemented.

Implemented support:

- `Ship.automation` defaults to `StandardAutomation`.
- all six automation tiers are modelled: crew-intensive, low, standard,
  enhanced, advanced, and high.
- automation cost modifiers use the configured hull basis plus drives and power
  plant costs.
- the non-gravity hull discount is excluded from the automation cost basis.
- crew multipliers are applied to reducible crew roles.
- standard automation emits no spec row; non-standard automation emits a Hull
  spec row with any task DM notes.
- unit tests cover tier values, cost basis, spec row output, serialization, and
  non-gravity automation basis handling.

## Concealed Manoeuvre Drive

High Guard concealed manoeuvre drives are implemented on M-drive parts.

Implemented support:

- `MDrive*` parts accept `concealed=True`.
- concealed drives add +25% to M-drive tonnage and cost.
- effective Thrust is halved, rounding down, through `.effective_thrust`.
- power remains based on the installed drive rating because the option only
  changes tonnage, cost, and effective Thrust.
- notes record the effective Thrust, the 3-metre accelerating-surface placement
  rule, and that removing the outer bulkhead does not improve performance.
- unit tests cover values, notes, and JSON/model round-trip through the M-drive
  union.
