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
