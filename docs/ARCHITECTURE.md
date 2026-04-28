# Architecture

## Core patterns

### Pydantic models

The core models are ordinary Pydantic `BaseModel` subclasses. In practice we
still treat them as design declarations plus derived values, but they are not
globally frozen.

### Parts use plain numeric values

`ShipPart` stores `cost`, `power`, and `tons` as ordinary `float` fields.
Parts that derive their values override `compute_cost()`, `compute_power()`,
and `compute_tons()`. The base implementation simply returns the stored values.

`tons` in Traveller ship design means **displacement tons** (`dTons`), not
metric mass. One displacement ton is a volume measure: the volume occupied by
one metric ton of liquid hydrogen, conventionally about 14 cubic metres. In
other words, Tycho's tonnage model is volumetric. A part's `tons` field answers
"how much ship displacement / internal volume does this consume or represent?",
not "how many kilograms does it weigh?".

As a house rule for cargo realism, we also assume that one displacement ton of
cargo space normally yields about one metric ton of practical net payload. This
is not a geometric truth about every possible cargo, but it keeps Traveller's
trade assumptions in a usable range and avoids treating `dTons` of cargo as if
they were magically much denser than the hydrogen-reference volume.

### Two-phase construction: creation then binding

Parts are created as plain Pydantic models. `Ship.model_post_init()` then calls
`part.bind(ship)` on every installed part, which sets the owner, validates TL
requirements, and recalculates derived values. Ship-dependent logic lives in
`compute_*` methods and is only callable after binding.

### JSON roundtripping

A complete ship design must serialize to JSON and deserialize back to a
functionally identical ship — same structure, same types, same field values.
This is a core feature: designs are stored, transferred between systems, and
loaded as templates. Serialized ships are also used for rendering (HTML, PDF)
without re-running Python-side business logic.

`tests/tycho/test_serialization.py` is the explicit guardian of this contract.
As the codebase evolves, that file must be kept current: any new field or
polymorphic type that matters to a ship's identity must have a roundtrip test.

The markdown rendering path is being phased out in favour of the HTML and PDF
transforms, which means JSON becomes the primary regression artefact. Future
feature tests should verify correctness through JSON comparison wherever
possible, integrating roundtrip verification into the feature test rather than
treating it as a separate concern.

Polymorphic fields use Pydantic discriminated unions so the correct concrete
type is resolved during deserialization. `armour` and `stealth` on `Hull` use
`description` as the discriminator. Any new polymorphic field must follow the
same pattern — add a `Literal` discriminator field to each subclass and annotate
the union with `Field(discriminator=...)`.

### Derived data in model JSON

Derived values (`cost`, `power`, `tons`) are included in JSON so a serialized
model can be used directly for rendering. On deserialization, derived values
are recalculated by the model and override whatever the JSON contained — JSON
is a snapshot of current state, not the authoritative source.

### Tech level model

The intended conceptual model is:

- `ship.tl`: the ship's TL
- `part.tl`: the part's own technology level / variant TL

In the common case, `part.tl` is also the required ship TL for installing that
part. However, those are still different ideas and should not be conflated in
the design.

Customisation grades such as `Early Prototype`, `Prototype`, `Budget`,
`Advanced`, `Very Advanced`, and `High Technology` do **not** change what part
the thing is. A TL12 fusion plant remains a TL12 fusion plant. A TL10 beam
laser remains a TL10 beam laser. Customisation instead changes how the part may
be used and with what consequences: altered ship-TL requirement, cost, tonnage,
power, fuel use, notes, and similar effects.

Some subsystems may also care about `ship.tl` separately from `part.tl`. The
most obvious example is sensors, where the installed sensor package has its own
TL floor but some capabilities or notes may still depend on the ship's TL.

The current code still uses names such as `minimum_tl` and `effective_tl` in
places, and that implementation vocabulary does not yet cleanly match the
conceptual model above. When refactoring TL-sensitive code, prefer explicit
ideas such as:

- part TL / variant TL
- ship TL
- required ship TL after customisation
- capability rules affected by ship TL

Ceres currently supports ship TL16 and lower. We cap `ship.tl` at 16 and do
not attempt to model TL17+ features for now.

### Notes and validation

Errors, warnings, and informational messages are stored as `Note` objects on
the part or ship that detected the problem. Intrinsic notes are created during
`model_post_init()` from `build_item()` and `build_notes()`. Context-dependent
validation adds later notes without clearing the earlier ones. This is
intentional: if something triggers duplicate or strange notes, that should be
visible instead of being masked by a note-reset step. Notes with category
`ITEM` are special: they carry the human-readable row label for the stat
sheet.

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
cargo, crew roles, and operating expenses. `build_spec()` produces the
structured `ShipSpec` used by the HTML/PDF/Typst renderers and JSON regression
artifacts. These remain ship-level concerns rather than cached part data.

The installed-part graph is now section-based rather than mostly flat:

- `hull`
- `drives`
- `power`
- `fuel`
- `command`
- `computer`
- `sensors`
- `weapons`
- `craft`
- `habitation`
- `systems`
- `cargo`

### Carried craft and external loads

Internally carried craft use dedicated ship volume. For `Internal Docking Space`
or `Full Hangar`, the mothership pays the tonnage and cost of the docking /
hangar facility, while the carried craft itself contributes only its own cost
to the spec. The carried craft's own fuel, cargo, and other internal resources
are not added separately to the mothership spec.

For internal carriage, the facility's displacement already includes the carried
craft in volumetric terms. A `Full Hangar (95 tons)` has the same total
displacement whether it currently contains a `Passenger Shuttle` or stands
empty, because the shuttle fits inside that reserved internal volume. Likewise,
an `Air/Raft` occupying a `Docking Space (5 tons)` does not add another 4
displacement tons on top of the docking-space row; the craft fits within that
allocated internal space.

Externally carried craft or cargo are different. For systems such as docking
clamps, tow cables, cargo nets, external cargo mounts, jump nets, jump shuttles
and similar arrangements, the attached load must be treated as extra effective
displacement when assessing drives and other displacement-sensitive performance.
This is not yet modelled in code.

Docking clamps are therefore different from hangars or internal docking spaces:
the clamp itself has its own displacement, but a craft attached to it during
flight remains an additional external load whose displacement must still be
handled by the carrying ship.

When we later model crew effects from carried craft, a single
`engineering_tonnage` figure on the carried-craft data is likely sufficient for
Tycho's purposes. That value should be understood as the total drives-plus-power
engineering burden relevant to engineer staffing, not as a narrower physical
"drive mass" figure.

When we add these external-load systems, we will likely want some form of
parameterized spec output, so a design can state performance at one or more
extra carried displacements, such as “Thrust X / Jump Y while carrying Z dTons”.

Just as important, "relevant displacement" is not always the same for every
calculation. A design may have:

- a structural / design displacement used for hull, internal space budgeting,
  most maintenance, and the ship's own crew rules
- an effective in-flight displacement used for thrust, jump, fuel use, and
  other performance calculations while carrying external loads or certain
  detachable modules

This distinction matters for examples such as modular cutters, detachable
modules, docking clamps, jump shuttles, drop tanks, and jump nets. A ship can
be one size as a design object and another size for a specific flight profile.
Tycho should therefore avoid assuming that a single displacement value is
always correct for every rule.

### Armour

`Armour` extends `ShipPart` with derived cost and tonnage. Tonnage scales with
displacement and a per-type `_tonnage_consumed` constant; small ships (< 100 t)
get a size-factor multiplier. Each concrete armour type enforces its own
protection limits and minimum TL via `check_protection_limit()`.

### Weapons

`FixedMount` and the turret classes compose weapon value objects. Weapon models
carry their own cost/power characteristics while the mount applies mount-level
rules such as firmpoint reductions or turret mount overhead. `WeaponsSection`
owns capacity checks such as hardpoints versus firmpoints and the small-craft
restriction to single turrets.

### Software

`SoftwarePackage` is a separate hierarchy from `ShipPart` — software has no
tonnage or owner-binding. `Computer.can_run()` checks bandwidth against the
computer's processing rating; `Core` computers have unlimited jump control
bandwidth. A computer automatically includes `Library`, `Manoeuvre/0`, and
(from TL11) `Intellect` in its software list.

`ComputerSection` normalizes installed software as singleton families. For
packages such as `Jump Control`, `Evade`, `Fire Control`, and `Auto-Repair`,
only the highest installed rating counts for cost and capability. Lower
redundant entries are not kept as active packages; instead, the retained
package gets a warning note describing the redundancy.

Cross-checks between `JumpDrive` and `Jump Control` are initiated from
`Ship.model_post_init()` but owned by the relevant sections:

- `DriveSection` warns on the jump drive if control software is missing or too weak
- `ComputerSection` warns on jump control software if there is no jump drive or
  the drive rating is lower than the software rating

### Crew

`Ship.crew` is now a dedicated sub-object. It holds explicit crew input
(`roles`) and crew-specific notes, so crew-related messages do not have to be
stored at ship level and filtered back into the crew table later.

Crew rows in the spec represent rule-indicated positions / functions, not
necessarily unique individuals. A single sophont (or sometimes robot) may
fulfill more than one of these positions in practice.

Automation and equipment can impact crew needs, e.g. with Starhip Automation
(Traveller Companion.)

## Rules interpretations

Cross-cutting rule decisions, intentional deviations, and interpretation notes
should now be recorded in [RULE_INTERPRETATIONS.md](/Users/magnuslycka/work/ceres/docs/RULE_INTERPRETATIONS.md).
Keep this section focused on high-level policy and only repeat details here
when they are needed to understand the architecture.

Source-to-test-case normalization rules for external ship designs should be
recorded separately in [TEST_CASE_SHIPS.md](/Users/magnuslycka/work/ceres/docs/TEST_CASE_SHIPS.md).

We follow the latest versions of Mongoose Traveller 2nd Edition Core Rules and
High Guard. Where the two books conflict, **High Guard takes precedence**.

We have studied Mark F. Anderson's ship design tool output and other external
sources, but cross-cutting decisions such as unsupported drive cost reduction
labels and unsupported retro starship computer pricing should now be recorded
in `RULE_INTERPRETATIONS.md` rather than duplicated here.
