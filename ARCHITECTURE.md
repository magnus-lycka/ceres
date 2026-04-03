# Architecture

## Project Structure

```
src/ceres/
  parts.py    # Base classes: ShipPart, Cost, Power, Tons, TechLevel
  armour.py   # Armour types (TitaniumSteel, Crystaliron, BondedSuperdense, MolecularBonded)
  ship.py     # Ship, Hull, HullConfiguration, HullOptions, Stealth classes
tests/
  test_parts.py
  test_armour.py
  test_hulls.py
  test_ship.py
```

## Core Patterns

### Pydantic Frozen Models

All models use Pydantic `BaseModel` with `frozen = True`. Objects are immutable
after construction.

### Lazy-Evaluated Value Types

`Cost`, `Power`, `Tons` extend `FloatModel` - Pydantic models that wrap a
`float | None` value. They resolve lazily via `resolve()`:

- If an explicit `value` was provided, return it.
- Otherwise, call the owning `ShipPart`'s `calculate_cost()` / `calculate_power()` /
  `calculate_tons()`.

These types implement arithmetic and comparison operators so they can be used
directly in expressions (e.g. `part.cost == 50000`).

`TechLevel` follows the same pattern but wraps `int | None` and defaults to the
ship's TL if not set explicitly.

### Binding

Construction happens in two phases:

1. **Part creation** - `ShipPart.__init__` binds its value fields (`cost`, `power`,
   `tons`, `tl`) to itself so they can call back `calculate_*` methods.
2. **Ship binding** - `Ship.model_post_init` calls `part.bind(ship)` on every part.
   This sets the part's owner and eagerly evaluates all values to trigger validation
   (TL checks, protection limits, etc.).

### Owner Properties

`FloatModel`, `TechLevel`, and `ShipPart` each have a private `_owner` attribute
(initially `None`) and a public `owner` property that raises `RuntimeError` if
accessed before binding. This gives clean type narrowing without scattered asserts.

### Derived data in madel json

**TODO:**

Some of the data in the model, such as cost, power and displacement need for
parts is calculated by the model. It's still included in the json, since the
the json is used to create textual representations etc. Such data is simply
recalculated after import (on model validation?), regardless of json content.

What's written below is a misunderstanding of requirements, and needs to be
fixed/removed. We shouldn't have any _explicit_cost: ClassVar[bool] = False etc.


`ShipPart` subclasses control which fields are user-supplied vs computed using
class variables:

```python
_explicit_cost: ClassVar[bool] = False   # cost computed by calculate_cost()
_explicit_tons: ClassVar[bool] = False   # tons computed by calculate_tons()
_explicit_power: ClassVar[bool] = True   # power set explicitly
```

Model validators reject attempts to pass values for derived fields.

### Field Coercion

Pydantic `field_validator(mode="before")` methods on `ShipPart` coerce plain
values to wrapper types: `int` -> `TechLevel`, `float` -> `Cost`/`Power`/`Tons`.
This means parts can be created with `tl=12` instead of `tl=TechLevel(value=12)`.

Note: ty cannot see this coercion statically, so `invalid-argument-type` is
suppressed in tests via `pyproject.toml`.

### Hull System

`HullConfiguration` defines hull properties (streamlining, cost modifier, hull
points modifier, usage factor, etc.). Seven predefined configurations exist as
module-level instances (e.g. `standard_hull`, `streamlined_hull`, `planetoid`).

`Hull` combines a `HullConfiguration`, optional `Armour`, and `HullOptions`
(stealth, shielding). It registers its sub-parts into the ship's parts set.

### Armour Hierarchy

`Armour` extends `ShipPart` with derived cost and tons. Concrete types
(`TitaniumSteelArmour`, `CrystalironArmour`, etc.) define cost-per-ton,
tonnage-consumed, min TL, and protection limits via class variables and
`check_protection_limit()`. Small ships (< 100 tons) have size-factor multipliers
on armour tonnage.
