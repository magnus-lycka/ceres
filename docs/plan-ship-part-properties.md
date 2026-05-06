# Plan: More Functional Ship Parts

## Status

Draft plan. This describes a desired architecture cleanup, not current code.

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

Do not solve notes in the first numeric slice. For now, keep notes as the
reporting surface. But the intended direction is to make note production
query-like in the same way as `tons`, `cost`, and `power`.

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
