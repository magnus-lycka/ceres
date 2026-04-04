# Architecture

## Project Structure

```
src/ceres/
  base.py     # Shared ship base model
  parts.py    # Base class for installed ship parts
  armour.py   # Armour types (TitaniumSteel, Crystaliron, BondedSuperdense, MolecularBonded)
  sensors.py  # Sensor packages
  drives.py   # M-drive, fusion plants, operation fuel
  ship.py     # Ship, Hull, HullConfiguration, stealth classes, ship-level aggregates
tests/
  ships/      # Regression tests for complete ship designs
  test_parts.py
  test_armour.py
  test_drives.py
  test_hulls.py
  test_ship.py
```

## Core Patterns

### Pydantic Frozen Models

All models use Pydantic `BaseModel` with `frozen = True`. Objects are immutable
after construction.

### Parts Use Plain Numeric Values

`ShipPart` stores `cost`, `power`, and `tons` as ordinary `float` fields.
There are no wrapper value types for derived quantities.

Parts that derive their values override:

- `compute_cost()`
- `compute_power()`
- `compute_tons()`

The base `ShipPart` implementation simply returns the stored values unchanged.

### Binding

Construction happens in two phases:

1. **Part creation** - parts are created as plain frozen models.
2. **Ship binding** - `Ship.model_post_init()` calls `part.bind(ship)` on every
   installed part. This sets the part owner, validates TL requirements, and
   recalculates derived values such as cost, power, and tons.

### Owner Properties

`ShipPart` has a private `_owner` attribute and a public `owner` property that
raises `RuntimeError` if accessed before binding. This keeps ship-dependent logic
explicit and gives clean type narrowing without scattered asserts.

### Derived Data In Model JSON

Derived part data such as `cost`, `power`, and `tons` is included in JSON so the
serialized model can be used directly for rendering and reporting.

On import and validation, derived values are recalculated by the model and win
over whatever JSON happened to contain. JSON is therefore a serialization format
for the current state of the model, not the authoritative source for derived
part values.

### Tech Level Model

Tech levels are plain integers.

- `ship.tl` is the ship TL
- `part.minimum_tl` is the minimum TL required to install or use that part
- `part.ship_tl` is the owning ship's TL
- `part.effective_tl` is the TL the part uses for calculations

The default `ShipPart.effective_tl` is the ship TL, but subclasses may override
this when a part represents a specific technology variant rather than merely a
minimum availability threshold.

### Hull System

`HullConfiguration` defines hull properties (streamlining, cost modifier, hull
points modifier, usage factor, etc.). Seven predefined configurations exist as
module-level instances (e.g. `standard_hull`, `streamlined_hull`, `planetoid`).

`Hull` combines a `HullConfiguration`, optional armour, and optional stealth.
`armour` and `stealth` are represented as discriminated unions keyed by their
human-readable `description` fields, which are also included in JSON. This keeps
the Python API natural (`hull.armour`, `hull.stealth`) while still allowing
roundtrip serialization back to the correct concrete part type.

`Hull` exposes its installed sub-parts so `Ship` can bind and aggregate them.

### Ship Aggregation

`Ship` owns the full installed-part graph and is responsible for aggregating
ship-level values such as:

- `hull_cost`
- `production_cost`
- `sales_price_new`
- `crew_roles`
- `available_power`
- `basic_hull_power_load`
- `maneuver_power_load`
- `sensor_power_load`
- `weapon_power_load`
- `total_power_load`
- `cargo`
- `software_packages`
- `markdown_table()`

These remain ship-level properties rather than cached part data.

`Ship.sensors` is modeled as a ship-level installed part, similar to `Hull.armour`
and `Hull.stealth`, rather than encoding the specific sensor package name in the
attribute itself.

Some of these ship-level properties are still intentionally minimal and currently
exist to support regression-tested ship sheets such as the ultralight fighter.
For example, the crew model presently covers the small-craft case directly used
by that sheet, while presentation concerns are starting to move toward
`markdown_table()` instead of additional one-off report properties.

### Armour Hierarchy

`Armour` extends `ShipPart` with derived cost and tons. Concrete types
(`TitaniumSteelArmour`, `CrystalironArmour`, etc.) define cost-per-ton,
tonnage-consumed, min TL, and protection limits via class variables and
`check_protection_limit()`. Small ships (< 100 tons) have size-factor multipliers
on armour tonnage. Armour types also expose human-readable `description` values
used both for rendering and as discriminators during JSON roundtripping.
