# Plan: More Functional Ship Parts

## Status

Numeric ship-part properties are complete:

- `Stateroom`, `HighStateroom`, and `LuxuryStateroom` now compute `tons`,
  `cost`, and `power` through properties instead of cached Pydantic fields.
- `LowBerth` now computes `tons`, `cost`, and context-dependent `power` through
  properties.
- `Brig` now computes `tons`, `cost`, and `power` through properties.
- A second low-risk systems slice now computes `tons`, `cost`, and `power`
  through properties for `Workshop`, `Laboratory`, `LibraryFacility`,
  `BriefingRoom`, `Armoury`, `WetBar`, `MedicalBay`, `ProbeDrones`,
  `AdvancedProbeDrones`, `MiningDrones`, and `TrainingFacility`.
- A third systems slice now computes assembly-context values through properties
  for `Airlock`, `Aerofins`, and `RepairDrones`.
- A fourth systems slice now handles explicit-tonnage systems with a serialized
  design `tons` field and computed `cost`/`power` properties for `CommonArea`,
  `SwimmingPool`, `Theatre`, `CommercialZone`, and `Biosphere`; `HotTub` now
  computes all three numeric values from `users`.
- A fifth storage slice now computes `tons`, `cost`, and `power` through
  properties for `FuelScoops`, `CargoAirlock`, and `FuelCargoContainer`.
- A sixth storage slice now computes fuel values through properties for
  `OperationFuel`, `JumpFuel`, `ReactionFuel`, and `FuelProcessor`.
- A seventh habitation slice now handles `AdvancedEntertainmentSystem` and
  `CabinSpace` with explicit design fields plus computed companion values.
- An eighth command slice now computes `Cockpit` and `Bridge` values through
  properties.
- A ninth computer slice now computes ship computer hardware values through
  properties.
- A tenth craft slice now computes craft housing values through properties.
- An eleventh armour slice now computes hull armour values through properties.
- A twelfth hull slice now computes stealth and armoured bulkhead values through
  properties.
- A thirteenth sensors slice now computes sensor package and add-on values
  through properties.
- A fourteenth drives slice now computes reaction drives, manoeuvre drives,
  jump drives, fusion plants, and emergency power systems through properties.
- A fifteenth weapons slice now computes weapon mounts, storage, barbettes,
  bays, and point defense batteries through properties.
- The shared `ShipPart` refresh machinery has been removed; binding now supplies
  assembly context and note/bulkhead setup without mutating cached numeric
  fields.
- Stale numeric inputs for computed values are ignored. Computed-only values are
  not serialized as stored fields; explicit design `tons` remains serialized as
  `tons`.

All ship-part numeric values are now either explicit design fields on simple
parts or properties on converted part families. The remaining follow-up area is
notes: note production still uses the existing reporting surface and has not
yet been converted into fully query-like derived output.

## Motivation

The current `ShipPart` model has two overlapping interfaces for the same
concepts:

- consumers read `part.tons`, `part.cost`, and `part.power`
- subclasses override `compute_tons()`, `compute_cost()`, and `compute_power()`
- `bind()` calls `refresh_derived_values()` to copy the computed values back
  into the public fields

That gives consumers the pleasant API we want, but it also creates a strange
life cycle: parts are frozen Pydantic models, then `bind()` uses
`object.__setattr__` to mutate derived fields after the part has been installed
in a ship.

The deeper issue is that we are mixing two styles:

- a mostly immutable design model, where parts are definitions installed in a
  ship
- an imperative finalisation step, where binding mutates those definitions with
  cached results and accumulated notes

The goal is to move toward a more functional model: keep the design state small
and stable, then compute derived facts from the current object graph when they
are requested. In other words, values should be outputs of functions over the
ship and its parts, not hidden state that appears because earlier code called
methods in the right order.

We want the object model to match the domain model more closely:

- a `Ship` owns parts
- each part carries its own build logic
- the ship can ask installed parts for their tonnage, cost, power, and notes
  without knowing each part's internal rules
- the ship evaluates a manually supplied design; it does not solve or optimise
  the design automatically

## Desired Shape

Keep `assembly` on installed parts. It is useful and matches how we think about
the model: a part knows which ship it belongs to once it is installed.

Keep `ShipPart` frozen if practical. Frozen parts help protect us from
accidental mutation while the ship aggregates displacement, fuel, power, cost,
crew needs, and cargo space.

Change `tons`, `cost`, and `power` from cached mutable fields into simple
properties:

```python
part.tons
part.cost
part.power
```

These remain the public API. The implementation can still use private helper
methods, but consumers should not need to call `compute_*`.

The ideal pattern is:

- construction records design choices
- binding supplies context (`assembly`)
- asking a question computes the answer from current state
- no frozen model is mutated just to cache a derived value

## Proposed Direction

### 1. Convert Public Values to Properties

Move the current refresh logic into properties:

```python
@property
def tons(self) -> float:
    return self.assembly.performance_displacement * self.tons_percent
```

The calculation should live directly in the property unless a class has a real
reason to factor out a helper. Do not replace `compute_tons()` with a parallel
private `_tons()` method that has the same content as the property. That would
keep the current overlap under a new name.

The base implementation must still support explicit values for simple custom
parts. One likely route is to store explicit inputs in internal fields such as
`base_tons`, `base_cost`, and `base_power`, or to keep declared fields with
clearer names and expose the public properties separately.

### 2. Remove Refresh-Derived-Values

Once public values are properties, remove:

- `_refresh_field()`
- `refresh_derived_values()`
- the `object.__setattr__` used to write derived `cost`, `power`, and `tons`
  during `bind()`

`bind()` should still provide assembly context, but it should not cache derived
numeric values back onto the part. If validation can be made query-like as well,
that is preferable, but numeric derived values are the first target.

### 3. Keep Ship Aggregation Dumb

The ship should keep doing simple aggregation:

```python
sum(part.tons for part in self._all_parts())
sum(part.cost for part in self._all_parts())
sum(part.power for part in self._all_parts())
```

Each part is responsible for making those properties correct in its installed
context.

### 4. Treat Notes as a Follow-Up

Notes have the same underlying problem as cached numeric values. Today many
notes are accumulated over time in a mutable list, then returned later. That
makes order and lifecycle matter: the result depends on which validation or
binding methods happened to append notes earlier.

The better model is that `part.notes` is a property that creates all relevant
notes for the part when called. Notes should be derived from the current part
and assembly state, not preserved as a historical append log from earlier
program execution.

Notes were deliberately left out of the numeric-property conversion. For now,
keep notes as the reporting surface. But the intended direction is to make note
production query-like in the same way as `tons`, `cost`, and `power`.

The longer-term functional shape would be:

```python
part.notes
```

returning a freshly built `NoteList` derived from the current design.

## Ordering Concerns

Ceres evaluates a supplied design rather than deriving a complete design from
requirements. That keeps the dependency graph manageable.

The expected flow remains:

1. Normalize obvious ship defaults, such as automatic airlocks and free fuel
   scoops.
2. Bind parts to the ship so they have assembly context.
3. Aggregate tonnage, cost, power, cargo space, fuel needs, and crew needs by
   asking parts and sections for their current values.
4. Let parts and sections report warnings/errors from current state.
5. The user reads the spec and adjusts the design manually.

This means we do not need to solve circular design choices such as “choose
staterooms from computed crew needs”. Crew warnings and remaining cargo are
outputs, not automatic inputs back into the design.

Still, we should watch for properties that depend on aggregate values which in
turn depend on the same property. Those are the cases that need explicit rules
or cached section-level calculations.

If a value must be cached for performance or to break a real cycle, the cache
should be explicit and local to that calculation. It should not be hidden as a
mutation of the part definition.

## Risks

- JSON should represent the ship definition, not cached derived values. If
  `cost`, `power`, and `tons` become properties, they should generally not be
  serialized as stored fields. Re-instantiating Python should recompute them
  from the design and assembly context.
- Pydantic field/property naming may require internal field names for explicit
  input values.
- Some tests intentionally assert recomputation from incorrect input values;
  those tests will need to move from “field was overwritten” to “stale derived
  input is ignored or rejected” or similar.
- Repeated shared instances such as `[Stateroom()] * 4` still need care. Frozen
  parts reduce the risk, but context-bearing parts can still share assembly or
  notes if reused.
- We may uncover real dependency cycles that were previously hidden by mutation
  order. Those cycles should be named and handled deliberately.

## First Candidate Slice

Start with a small, low-risk family:

- `Stateroom`
- `LowBerth`
- `Brig`

They cover fixed values and one context-dependent power calculation
(`LowBerth.compute_power()` depends on position in the habitation section).

Use that slice to settle naming, JSON behaviour, and test style before touching
drives, power plants, sensors, or weapons.

Current implementation note: this slice keeps the public names (`tons`, `cost`,
and `power`) as properties by declaring those names as `ClassVar` attributes on
the converted subclasses. That removes the inherited Pydantic fields for those
specific subclasses without forcing a base-class migration yet.

## Second Candidate Slice

The next completed slice is fixed and count-based systems:

- `Workshop`
- `Laboratory`
- `LibraryFacility`
- `BriefingRoom`
- `Armoury`
- `WetBar`
- `MedicalBay`
- `ProbeDrones`
- `AdvancedProbeDrones`
- `MiningDrones`
- `TrainingFacility`

These parts avoid explicit design fields named `tons`, `cost`, or `power`, so
they can follow the same subclass-level property pattern as the habitation
slice. They also share a small `_ZeroPowerSystemPart` base for converted systems
whose power draw is always zero.

## Third Candidate Slice

The next completed slice is context-dependent systems:

- `Airlock`
- `Aerofins`
- `RepairDrones`

These parts depend on the bound ship, but they still avoid explicit design
fields named `tons`, `cost`, or `power`. That makes them a good bridge between
fixed/count-based systems and the later explicit-tonnage migration.

`Airlock` keeps its current behaviour where free airlocks are computed from the
bound ship's displacement and installed airlock order. Because `tons` and
`cost` are now properties, free-vs-paid status is no longer copied into stored
fields during bind.

## Fourth Candidate Slice

The next completed slice is explicit-tonnage systems:

- `CommonArea`, `SwimmingPool`, `Theatre`, `CommercialZone`, and `Biosphere`
  now store the design tonnage in an internal `base_tons` field that validates
  and serializes as `tons`.
- `HotTub` now removes that inherited `base_tons` field and computes `tons`,
  `cost`, and `power` from `users`.

This confirms the naming pattern for parts where `tons` is a real design input
rather than a purely derived value: keep `part.tons` as the public property, use
an internal field for the design value, and serialize that field through the
external `tons` name.

## Fifth Candidate Slice

The next completed slice is storage parts with definition-derived values:

- `FuelScoops`
- `CargoAirlock`
- `FuelCargoContainer`

These parts do not use a serialized design `tons` field. `FuelScoops` computes
zero tonnage and free-vs-paid cost from its `free` flag. `CargoAirlock` computes
tonnage and cost from `size`. `FuelCargoContainer` computes installed tonnage
and cost from `capacity` while keeping `capacity` as the serialized design
input.

## Sixth Candidate Slice

The next completed slice is the remaining fuel storage parts:

- `OperationFuel`
- `JumpFuel`
- `ReactionFuel`
- `FuelProcessor`

`OperationFuel`, `JumpFuel`, and `ReactionFuel` are computed-only fuel entries:
their tonnage depends on the bound ship context, while cost and power are zero.
`FuelProcessor` uses the explicit-tonnage pattern: design `tons` remains
serialized as `tons`, while cost and power are computed from that value.

The existing note behaviour for missing plants/drives is intentionally left in
place for now, even though notes are still lifecycle-dependent. Notes remain a
follow-up concern after numeric values are moved to properties.

## Seventh Candidate Slice

The next completed slice is the remaining habitation parts:

- `AdvancedEntertainmentSystem`
- `CabinSpace`

`AdvancedEntertainmentSystem` uses the explicit-cost pattern: design `cost`
remains serialized as `cost`, while tonnage and power are computed as zero.
`CabinSpace` uses the explicit-tonnage pattern: design `tons` remains serialized
as `tons`, while cost and power are computed from that value.

## Eighth Candidate Slice

The next completed slice is command parts:

- `Cockpit`
- `Bridge`

`Cockpit` computes fixed tonnage, optional holographic cost, and zero power from
its design flags. `Bridge` computes context-dependent tonnage and cost from the
bound ship displacement plus `small`/`holographic` flags. Both are computed-only
numeric parts and no longer serialize `tons`, `cost`, or `power`.

## Ninth Candidate Slice

The next completed slice is ship computer hardware:

- `Computer5` through `Computer35`
- `Core40` through `Core100`

The shared `ComputerBase` now computes zero tonnage, zero power, and cost from
the hardware base cost plus `bis`/`fib` flags. These hardware parts no longer
serialize `tons`, `cost`, or `power`; their design state is the discriminated
hardware kind plus options.

## Tenth Candidate Slice

The next completed slice is craft housing:

- `DockingClamp`
- `InternalDockingSpace`
- `FullHangar`

These parts compute their installed tonnage and cost from the clamp kind or
carried craft metadata. They draw zero power and no longer serialize `tons`,
`cost`, or `power`; the serialized design state is the clamp/housing type plus
the carried occupant metadata.

## Eleventh Candidate Slice

The next completed slice is hull armour:

- `TitaniumSteelArmour`
- `CrystalironArmour`
- `BondedSuperdenseArmour`
- `MolecularBondedArmour`

The shared `Armour` base now computes context-dependent tonnage from the bound
ship displacement, material tonnage factor, protection rating, size factor, and
hull armour volume modifier. Cost and zero power are properties as well.
Material armour parts no longer serialize `tons`, `cost`, or `power`; their
design state is material type and protection.

## Twelfth Candidate Slice

The next completed slice is remaining hull parts:

- `BasicStealth`, `ImprovedStealth`, `EnhancedStealth`, and `AdvancedStealth`
- `ArmouredBulkhead`

The shared `Stealth` base now computes context-dependent tonnage and cost from
the bound ship displacement plus stealth class factors, with zero power.
`ArmouredBulkhead` computes tonnage and cost from protected tonnage, also with
zero power. These parts no longer serialize `tons`, `cost`, or `power`.

## Thirteenth Candidate Slice

The next completed slice is sensors:

- primary packages from `BasicSensors` through `AdvancedSensors`
- `CountermeasuresSuite`
- `LifeScannerAnalysisSuite`
- `SensorStations`
- `EnhancedSignalProcessing`
- `ExtendedArrays`
- `RapidDeploymentExtendedArrays`

Primary sensor packages now share class-level base tonnage/cost/power values
and compute low-intercept cost multipliers as properties. Sensor add-ons compute
fixed, count-derived, or primary-suite-derived values through properties. These
parts no longer serialize `tons`, `cost`, or `power`; notes still keep their
existing bind-time rebuild behaviour for assembly-TL-dependent descriptions.

## Fourteenth Candidate Slice

The next completed slice is drives and power plants:

- reaction drives from `RDrive0` through `RDrive16`
- manoeuvre drives from `MDrive0` through `MDrive11`
- jump drives from `JDrive1` through `JDrive9`
- `FusionPlantTL8`, `FusionPlantTL12`, and `FusionPlantTL15`
- `EmergencyPowerSystem`

Drive and power values now compute from the bound ship displacement, performance
displacement, drive level, plant output, and installed customisation. These
parts no longer serialize `tons`, `cost`, or `power`; their serialized state is
the selected drive/plant type plus design options such as customisation,
high-burn thruster, and fusion output.

## Fifteenth Candidate Slice

The next completed slice is weapons:

- `FixedMount`
- turrets from `SingleTurret` through `QuadTurret`
- `MissileStorage` and `SandcasterCanisterStorage`
- barbettes from `BeamLaserBarbette` through `TorpedoBarbette`
- bay weapons from small through large variants
- point defense batteries from type I through type III laser and gauss variants

Weapon values now compute from mounted weapon lists, ammunition counts, base
mount data, base weapon data, and installed customisation. These parts no longer
serialize `tons`, `cost`, or `power`; their serialized state is the selected
weapon/mount type plus design options such as mounted weapons, count, and
customisation.

## Base Cleanup Slice

The shared numeric refresh lifecycle is now removed from `ShipPartMixin`:

- `compute_tons()`, `compute_cost()`, and `compute_power()` are gone
- `_refresh_field()` and `refresh_derived_values()` are gone
- `bind()` no longer writes computed numeric values back onto frozen parts

Simple `ShipPart` instances can still carry explicit numeric fields. Converted
families expose `tons`, `cost`, and `power` as properties, so ship aggregation
continues to use the same public API without depending on bind-time mutation.
