# Plan: Gear-Backed Robot Physical Options

## Goal

Robot physical options that are ordinary equipment should be modelled first as
generic gear, then adapted into robot parts when installed in a robot.

For example, a robot option such as `Transceiver 50km (enhanced)` appears to be
the same kind of device as the transceivers in the Central Supply Catalogue. The
canonical rules for that item should therefore live in `ceres.gear.comm`, not in
`ceres.make.robot.options`.

The robot layer should answer robot-specific questions:

- how many robot slots the installed item uses
- whether the item is a default suite item (cost included in BCC)
- how the item is displayed in a robot build
- whether it grants robot-specific capabilities

The gear layer should answer item-specific questions:

- TL, cost, mass
- range, encryption, satellite uplink, computer options
- source rules and catalogue output

This follows the rule in `docs/assemblies_and_parts.md`: context-independent
properties belong on the generic part, and context-dependent installation
properties belong in assembly-specific mixins or wrappers.

## Default Suite As Part of Options

The five default suite items are not a separate field. They are `RobotPart`
instances in `Robot.options`, exactly like any other installed option:

```python
options: list[RobotPartMixin] = Field(
    default_factory=lambda: list(DefaultSuite())
)
```

`DefaultSuite()` returns the five standard items:

```python
[
    VisualSpectrumSensor(),
    VoderSpeaker(),
    AuditorySensor(),
    WirelessDataLink(),
    Transceiver(range_km=5, quality='improved'),
]
```

Each item produced by `DefaultSuite()` has `cost = 0.0` — its cost is included in
the base chassis cost per the Robot Handbook rules.

The `default_suite: list[str]` field is removed from `Robot`. The separate
`_DEFAULT_SUITE_FREE_ITEMS` frozenset, `_ZERO_SLOT_ITEM_COSTS` dict, and
`default_suite_item_cost()` function are also removed once the migration is
complete.

### Constructing Builds With Default Suite Items

```python
# Default build — five standard items included:
Robot(name='Worker', ...)

# Default suite plus additional options:
Robot(name='Worker', ..., options=DefaultSuite() + [StorageCompartment(slots_count=4)])

# Remove wireless data link, add drone interface instead:
Robot(name='Worker', ..., options=DefaultSuite(wireless=False, drone=True) + [...])
```

### `DefaultSuite` Helper

`DefaultSuite` is a plain helper that returns a list of zero-cost `RobotPart`
instances. It is not a domain object, a robot part, or a robot field — it only
exists to make construction convenient.

```python
def DefaultSuite(
    see: bool = True,               # Visual Spectrum Sensor
    speak: bool = True,             # Voder Speaker
    hear: bool = True,              # Auditory Sensor
    wireless: bool = True,          # Wireless Data Link
    improved_transceiver: bool = True,  # Transceiver 5km (improved)
    drone: bool = False,            # Drone Interface
    basic_transceiver: bool = False,    # Transceiver 5km (basic)
    screen: bool = False,           # Video Screen (basic)
) -> list[RobotPartMixin]:
    ...
```

At most 5 of the eight flags may be `True` (validation error otherwise). The
returned parts all have `cost = 0.0`.

The eight possible items correspond to the substitution options in
`refs/robot/10_default_suite.md`. None are paid upgrades at the `DefaultSuite`
level — paying for a better transceiver means adding it outside `DefaultSuite()`:

```python
options=DefaultSuite(improved_transceiver=False) + [RobotTransceiver(range_km=50)]
```

### Zero-Slot Quota

The zero-slot quota is `5 + size + TL`. The 5 accounts for the five default suite
items now living in options. No marker or special casing is needed — the formula
applies uniformly to every zero-slot item in the options list:

```python
zero_slot_count = sum(
    1 for o in self.options
    if isinstance(o, RobotPartMixin)
    and o.slots == 0
    and o.notes.item_message is not None
)
excess_zero_slots = max(0, zero_slot_count - (5 + int(self.size) + self.tl))
```

## Current State

`ceres.make.robot.options` currently uses string names for several physical
options and default-suite replacements. These strings are paired with
robot-specific cost tables such as `_ZERO_SLOT_ITEM_COSTS`. String-based
comparison is the source of fragility in default-suite handling.

`ceres.gear.comm` exists but currently only contains a few audio bug classes.
It is the natural home for Central Supply Catalogue communications equipment.

## Option Class Pattern

Robot-installed gear uses the `(GearClass, RobotPartMixin)` inheritance pattern,
consistent with how `ComputerPart` and `ShipComputer` relate:

```python
class RobotTransceiver(Transceiver, RobotPartMixin):
    slots: int = 0
    is_default_suite: bool = False
```

The gear class owns TL, cost, range, options (encryption, satellite uplink, etc.).
The robot mixin adds slot count and robot-specific installation metadata.

For options that have no current CSC equivalent, define them as plain `RobotPart`
classes in `ceres.make.robot.options`. If a CSC source is found later, the gear
class can be introduced and the existing class converted to the two-base pattern.
Do not invent a generic gear class without a confirmed source.

## Source Mapping

The first implementation pass must map each current string option and default-suite
item to its source.

Confirmed CSC items (implement via `gear.comm`):

- Transceivers: `refs/csc/05_communications.md`
- Hardware encryption modules: `refs/csc/05_communications.md`
- Satellite uplinks: `refs/csc/05_communications.md`
- Computer functionality in TL10+ transceivers: same source

Unknown source — mark as pending, define as `RobotPart` for now:

- Video Screen: likely CSC computer/interface equipment; confirm before implementing
- Wireless Data Link: may be generic comms or robot-specific interface
- Drone Interface: may be generic comms or robot-specific interface

Robot Handbook-only options (stay in `ceres.make.robot.options`):

- Options whose cost or rules appear only in the Robot Handbook construction tables
- Options where the robot version has special slot, integration, or capability
  rules not equivalent to handheld or carried gear

Do not use test examples as rule sources. If a robot test case names a device
but the rule source is not known, treat it as an input gap.

## Communication Gear in `ceres.gear.comm`

A first transceiver shape:

```python
class Transceiver(Equipment):
    medium: Literal['radio', 'laser', 'meson'] = 'radio'
    range_km: int
    quality: str = 'improved'
    encryption: EncryptionModule | None = None
    satellite_uplink: SatelliteUplink | None = None
    integrated_computer: PortableComputer | None = None
```

TL, cost, and mass derive from CSC tables. The class has no knowledge of robot
slots or default-suite rules.

If the CSC table is more easily maintained as specific named classes initially,
that is acceptable, but the public API should expose rules in equipment terms.

## Migration Plan

### Phase 1: Inventory and Source Map

- List every string in `_DEFAULT_SUITE_FREE_ITEMS`, `_ZERO_SLOT_ITEM_COSTS`, and
  `_DEFAULT_SUITE` in `robot.py`.
- Mark each as CSC gear, Robot Handbook-only, or unknown.
- Add a note for unknown items rather than guessing.

### Phase 2: Define `RobotPart` Classes for Default Suite Items

- Define typed `RobotPart` classes for all five default suite items and the three
  alternative substitutions (drone interface, basic transceiver, video screen),
  with `cost = 0.0` and `is_default_suite = True`.
- Implement `DefaultSuite()` using these classes.
- Change `Robot.options` default to `list(DefaultSuite())`.
- Remove `Robot.default_suite` field.
- Update `Robot.used_slots` to use the new quota formula.
- Update `Robot._raw_cost` (default suite cost is now embedded in each part).
- Update spec and detail rendering: default suite items appear in the Options row
  from the options list; no separate Default Suite section needed.
- Keep `_DEFAULT_SUITE_FREE_ITEMS` and `_ZERO_SLOT_ITEM_COSTS` as dead code until
  all existing tests are migrated; remove them in Phase 5.

### Phase 3: Implement Communication Gear

- Add CSC transceiver classes to `ceres.gear.comm`.
- Add hardware encryption and satellite uplink options.
- Add tests in `tests/gear/test_comm.py` for CSC table values.
- Decide whether TL10+ integrated transceiver computers create actual
  `PortableComputer` parts or just derived notes.

### Phase 4: Add Gear Catalogue Output

- Extend the gear catalogue machinery so communication equipment can be catalogued
  with the same structure as computers.
- Keep communications in `gear.comm`; do not move them into `gear.computer`.

### Phase 5: Add Robot Adapters for Communication Gear

- Replace the typed-but-simple `RobotTransceiver` from Phase 2 with the full
  `RobotTransceiver(Transceiver, RobotPartMixin)` class backed by CSC gear data.
- Remove the old string-based tables and helper functions.
- Update robot detail and spec output to render installed gear consistently.

### Phase 6: Expand Beyond Communications

- Apply the same inventory and source-map process to video screens, sensors,
  speakers, drone interfaces, and other physical robot options.
- Add new generic gear modules only where a confirmed CSC source exists.
- Keep Robot Handbook-only construction options in `make.robot`.

## Weapons

Weapons installed in robots follow the same gear-backed pattern: the weapon itself
is CSC gear; the mount and fire control system are robot-specific construction
options.

The weapons section is a separate, blocked initiative. No robot weapon
implementation is possible before `ceres.gear.weapons` exists.

### Prerequisite: `ceres.gear.weapons`

All facts about damage, range, magazine size, cost, and traits belong to the gear
layer. The robot layer only handles slot cost and installation semantics.

**Reference**: `refs/robot/32_fire_extinguisher.md` (Weapon Mount, Fire Control
System tables). CSC weapon tables are not yet converted to refs.

### Robot-Specific Parts

These parts belong in `ceres.make.robot.options` — their rules are entirely
robot-specific:

- **WeaponMount** (`small`/`medium`/`heavy`/`vehicle`): slot cost and minimum
  manipulator size per the Robot Handbook table; does not include weapon cost.
- **WeaponMountAutoloader**: doubles mount slots, adds 10 magazines, costs 20 ×
  magazine cost; increases minimum manipulator size by +1.
- **FireControlSystem** (`basic`/`improved`/`enhanced`/`advanced`): 1 slot,
  Weapon Skill DM +1 to +4; tied to one weapon or linked mount set.

### Attacks Row

The robot spec currently hard-codes `attacks='—'`. A proper attacks row should
collect all installed WeaponMount parts and render damage/traits from the gear
object. Defer until `ceres.gear.weapons` is in place and at least one armed robot
example has a known-good expected output.

### Stinger

The Stinger is a zero-slot melee weapon that is a robot construction option, not
CSC gear. It does not require `ceres.gear.weapons` but should wait until the
attacks row model is established.

## Test Expectations

Gear tests (`tests/gear/test_comm.py`):

- Transceiver TL, range, mass, and cost from CSC tables.
- Encryption module TL and cost.
- Satellite uplink mass/cost effects.

Robot tests:

- Default `options` equals `DefaultSuite()` content.
- `DefaultSuite()` validation rejects more than five True flags.
- Default suite items have `cost = 0.0` and `is_default_suite = True`.
- Default suite items do not count toward the zero-slot quota.
- Adding a paid transceiver outside `DefaultSuite()` charges the correct cost.
- Serialization round-trips typed options.
- Existing robot examples produce the same total cost and spec output.

## Open Questions

- Which robot options are explicitly CSC equipment and which are Robot
  Handbook-only abstractions?
- Is `Video Screen` a computer/interface option, a generic electronics item,
  or a robot-specific construction option?
- Should `Wireless Data Link` and `Drone Interface` be generic communications
  gear, robot-specific interfaces, or software/control capabilities?
- Should TL10+ transceiver computer functionality be a nested `PortableComputer`,
  a lightweight capability object, or derived notes until software integration
  needs it?
- Do robot-installed gear items report gear mass, ignore mass (robot rules use
  slots), or report both?

## Non-Goals For the First Pass

- Do not redesign the whole robot options system before the default suite
  migration is complete.
- Do not move communications equipment into `gear.computer`.
- Do not infer missing rules from existing test cases.
- Do not implement WeaponMount, FireControlSystem, or Stinger before
  `ceres.gear.weapons` exists and the attacks row model is designed.
