# Architecture

## Core patterns

### Pydantic frozen models

All models use Pydantic `BaseModel` with `frozen = True`. Objects are immutable
after construction.

### Parts use plain numeric values

`ShipPart` stores `cost`, `power`, and `tons` as ordinary `float` fields.
Parts that derive their values override `compute_cost()`, `compute_power()`,
and `compute_tons()`. The base implementation simply returns the stored values.

### Two-phase construction: creation then binding

Parts are created as plain frozen models. `Ship.model_post_init()` then calls
`part.bind(ship)` on every installed part, which sets the owner, validates TL
requirements, and recalculates derived values. Ship-dependent logic lives in
`compute_*` methods and is only callable after binding.

### Derived data in model JSON

Derived values (`cost`, `power`, `tons`) are included in JSON so a serialized
model can be used directly for rendering. On deserialization, derived values
are recalculated by the model and override whatever the JSON contained — JSON
is a snapshot of current state, not the authoritative source.

### Tech level model

`ship.tl` is the ship TL. `part.minimum_tl` is the minimum TL required.
`part.effective_tl` is what the part uses for calculations — it defaults to
the ship TL, but subclasses may override this when a part represents a specific
technology variant rather than just a minimum availability threshold.
`FusionPlant` is the primary example: it always uses its own fixed TL, not the
ship's.

### Notes and validation

Errors, warnings, and informational messages are stored as `Note` objects on
the part or ship that detected the problem. `build_notes()` is called during
binding and produces static notes (e.g. sensor DM). Validation logic in
`model_post_init` adds dynamic notes (e.g. missing airlock, jump control
mismatch, negative cargo). Notes with category `ITEM` are special: they carry
the human-readable row label for the stat sheet.

### Hull

`HullConfiguration` defines hull properties (streamlining, cost modifier, hull
points modifier, usage factor, etc.). Seven predefined configurations exist as
module-level instances (`standard_hull`, `streamlined_hull`, `planetoid`, etc.)
and can be modified further with flags such as `reinforced`, `light`, and
`military`.

`Hull` combines a `HullConfiguration` with optional armour, optional stealth,
and optional surface options (`heat_shielding`, `radiation_shielding`, `reflec`).
Armour and stealth are discriminated unions keyed by their `description` fields
so the Python API remains natural while roundtrip serialization still resolves
the correct concrete type.

### Ship aggregation

`Ship` owns the full installed-part graph and aggregates ship-level values such
as power budget (available, load by category), production cost, sales price,
cargo, crew roles, and operating expenses. `markdown_table()` renders the
complete stat sheet as a Markdown table. These remain ship-level concerns rather
than cached part data.

### Armour

`Armour` extends `ShipPart` with derived cost and tonnage. Tonnage scales with
displacement and a per-type `_tonnage_consumed` constant; small ships (< 100 t)
get a size-factor multiplier. Each concrete armour type enforces its own
protection limits and minimum TL via `check_protection_limit()`.

### Weapons

`FixedFirmpoint` composes a `PulseLaser` value object. The laser carries
advantage flags (`very_high_yield`, `energy_efficient`) that affect cost and
power; the firmpoint applies mount-level modifiers on top. `DoubleTurret` is
a fixed-cost part with no configurable weapon.

### Software

`SoftwarePackage` is a separate hierarchy from `ShipPart` — software has no
tonnage or binding, only cost and bandwidth requirements. `Computer.can_run()`
checks bandwidth against the computer's processing rating; `Core` computers
have unlimited jump control bandwidth. A computer automatically includes
`Library`, `Manoeuvre/0`, and (from TL11) `Intellect` in its software list.
