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
- whether it is part of the robot default suite
- whether replacing a default-suite item changes cost
- how the item is displayed in a robot build
- whether it grants robot-specific capabilities

The gear layer should answer item-specific questions:

- TL
- cost
- mass
- range
- options such as encryption, satellite uplink, and integrated computers
- source rules and catalog/report output

This follows the rule in `docs/assemblies_and_parts.md`: context-independent
properties belong on the generic part, and context-dependent installation
properties belong in assembly-specific mixins or wrappers.

## Current State

`ceres.make.robot.options` currently uses string names for several physical
options and default-suite replacements. The current tables include names such
as:

- `Transceiver 5km (basic)`
- `Transceiver 5km (improved)`
- `Transceiver 50km (enhanced)`
- `Transceiver 500km (improved)`
- `Transceiver 5,000km (advanced)`
- `Video Screen (basic)`
- `Video Screen (improved)`
- `Video Screen (advanced)`

These strings are paired with robot-specific cost tables such as
`_ZERO_SLOT_ITEM_COSTS`, and default-suite free items are also represented as
strings. This makes the robot builder responsible for facts that should belong
to the generic equipment catalogue.

`ceres.gear.comm` exists, but currently only contains a few audio bug classes.
It is the natural home for Central Supply Catalogue communications equipment
such as transceivers.

`ceres.gear.computer` already has a catalogue-style implementation for computer
equipment. The same style should be used for communication gear, but
communication devices should not be placed in `gear.computer` merely because
some of them include computer functionality. They should be catalogued through
the gear catalogue/reporting machinery, while their domain rules live in
`gear.comm`.

## Source Mapping

The first implementation pass should identify each robot option that is really
generic equipment and map it to its source.

Likely Central Supply Catalogue items:

- Transceivers: `refs/csc/05_communications.md`
- Hardware encryption modules: `refs/csc/05_communications.md`
- Satellite uplinks: `refs/csc/05_communications.md`
- Computer functionality built into TL10+ transceivers:
  `refs/csc/05_communications.md` and `ceres.gear.computer`
- Video screens or data displays: probably CSC computer/interface equipment,
  but this needs source confirmation before implementation

Possibly generic gear, pending source confirmation:

- Wireless data link
- Drone interface
- Tightbeam communicator
- Laser designator
- External speaker/voder-style output devices
- Cameras, visual sensors, auditory sensors, and other sensor packages

Possibly robot-specific options:

- options whose cost or rules come only from Robot Handbook robot construction
- options whose physical equipment is abstracted by the robot rules rather than
  sold as normal gear
- options where the robot version has special slot, integration, or capability
  rules that are not equivalent to handheld or carried gear

Do not use test examples as rules sources. If a robot test case demonstrates a
device name but the rule source is not known, treat it as an input gap until the
source is found.

## Proposed Model

### Generic Gear

Add real communications equipment classes to `ceres.gear.comm`.

A first transceiver shape could look conceptually like:

```python
class Transceiver(Equipment):
    medium: Literal["radio", "laser", "meson"] = "radio"
    range_km: int
    encryption: EncryptionModule | None = None
    satellite_uplink: SatelliteUplink | None = None
    integrated_computer: PortableComputer | None = None
```

The class should derive TL, cost, and mass from CSC tables. It should not know
anything about robot slots or default-suite replacement rules.

If the CSC table is easier to maintain as specific named classes at first, that
is acceptable, but the public API should still expose the rules in equipment
terms rather than robot option strings.

### Robot Installation Layer

Robot-installed versions should combine the generic equipment class with
robot-installation semantics, following the context-mixin rule.

Possible shapes:

```python
class RobotTransceiver(Transceiver, RobotPartMixin):
    slots: int = 0
    replaces_default_suite_item: bool = False
```

or:

```python
class RobotInstalledEquipment(RobotPartMixin):
    equipment: Equipment
    slots: int
```

The inheritance approach is closer to the current `ComputerPart`/`ShipComputer`
pattern. The wrapper approach may be better if many gear items can be installed
unchanged and robot slots are purely installation metadata. The implementation
choice should be made after inventorying the robot option list.

In both cases, the robot layer should not duplicate transceiver cost/range/TL
tables.

### Default Suite

Replace string-based default-suite declarations with typed parts or typed
descriptors.

Current style:

```python
"Transceiver 5km (improved)"
```

Target style:

```python
RobotTransceiver(range_km=5, quality="improved")
```

or:

```python
DefaultSuiteItem(
    item=RobotTransceiver(range_km=5, quality="improved"),
    free=True,
)
```

Replacement logic should compare typed capabilities, not display strings. For
example, replacing a default 5km transceiver with a 500km transceiver should be
recognised as a transceiver replacement because both are transceiver parts, not
because two strings happen to share a prefix.

During migration, accept the old string names as input aliases so existing
robot examples can be updated gradually.

## Catalogue Direction

Computer gear currently has a structured catalogue/report path. Communication
gear should gain the same kind of treatment:

- add or extend gear catalogue support for `gear.comm`
- list transceiver table entries with TL, range, mass, and cost
- list options such as encryption and satellite uplink separately
- expose build item text from the gear object, not from robot option strings

This should be "catalogued like gear computer equipment", not classified as
computer equipment unless the item actually is a computer. TL10+ transceiver
computer functionality should reuse `ceres.gear.computer` where practical, but
the owning device remains a transceiver.

## Migration Plan

### Phase 1: Inventory And Source Map

- List every string option in `ceres.make.robot.options`.
- Mark each one as CSC gear, Robot Handbook-only, or unknown.
- Add notes for unknown items rather than guessing.
- Identify which default-suite items are free built-ins and which are paid
  replacement options.

### Phase 2: Implement Communication Gear

- Add CSC transceiver table support to `ceres.gear.comm`.
- Add hardware encryption and satellite uplink options.
- Add tests in `tests/gear/test_comm.py` for CSC table values.
- Decide whether TL10+ integrated transceiver computers create actual
  `PortableComputer` parts or report a derived computer capability first.

### Phase 3: Add Gear Catalogue Output

- Extend the gear catalogue/report machinery so communication equipment can be
  catalogued with the same level of structure as computers.
- Keep communications in `gear.comm`; avoid moving them into `gear.computer`.
- Add tests that prove catalogue rows come from gear classes, not robot strings.

### Phase 4: Add Robot Adapters

- Add robot-installed communication equipment classes or wrappers.
- Preserve robot-specific slot handling.
- Preserve default-suite free-item behaviour.
- Update robot detail/spec output to render installed gear consistently.

### Phase 5: Migrate Default Suite

- Replace default-suite strings with typed gear-backed robot parts.
- Keep compatibility aliases for old string input while examples are migrated.
- Remove duplicated cost tables only after all current examples and tests use
  gear-backed parts.

### Phase 6: Expand Beyond Communications

- Repeat the same inventory/source-map process for video screens, sensors,
  speakers, drone interfaces, and other physical robot options.
- Add new generic gear modules only where they correspond to reusable equipment
  domains, such as `gear.sensor` or `gear.electronics`.
- Keep Robot Handbook-only construction abstractions in `make.robot`.

## Test Expectations

Gear tests should validate source table facts directly:

- transceiver TL, range, mass, and cost
- encryption module TL and cost
- satellite uplink mass/cost effects
- integrated computer behaviour once decided

Robot tests should validate robot integration:

- default suite includes the expected installed parts
- default-suite replacements charge the expected extra cost
- output text remains stable for existing robot examples
- serialization round-trips typed robot options
- unknown string options are rejected or converted through explicit aliases

Robot validation examples should continue to compare produced builds to
`_expected` values. Unit tests should carry the detailed rule assertions.

## Open Questions

- Which robot options are explicitly CSC equipment, and which are Robot
  Handbook-only abstractions?
- Do robot-installed gear items use gear mass directly, ignore mass because the
  robot rules use slots, or report both?
- Is `Video Screen` a computer/interface option, a generic electronics item, or
  a robot-specific construction option?
- Should `Wireless Data Link` and `Drone Interface` be generic communications
  gear, robot-specific interfaces, or software/control capabilities?
- Should TL10+ transceiver computer functionality be represented as an actual
  nested `PortableComputer`, a lightweight capability object, or just derived
  notes until software integration needs it?
- Is `comm.py` the final module name, or should it eventually become
  `communication.py`? The existing module name is `comm.py`, so new work should
  use it unless there is a deliberate rename.

## Weapons

Weapons installed in robots follow the same gear-backed pattern as communications
equipment: the weapon itself is CSC gear; the mount and fire control system are
robot-specific construction options.

### Prerequisite: `ceres.gear.weapons`

No robot weapon plan can be implemented before `ceres.gear.weapons` exists and is
populated with the relevant weapon tables from the Central Supply Catalogue and the
Robot Handbook. All facts about damage, range, magazine size, cost, and traits
belong to the gear layer. The robot layer only handles slot cost and installation
semantics.

**Reference**: `refs/robot/32_fire_extinguisher.md` (Weapon Mount, Fire Control
System tables). CSC weapon tables are not yet converted to refs.

### Robot-Specific Parts

These parts belong in `ceres.make.robot.options` because their rules are entirely
robot-specific — they have no CSC equivalent:

- **WeaponMount** (`small`/`medium`/`heavy`/`vehicle`): slot cost and minimum
  manipulator size per the Robot Handbook table; does not include the weapon cost.
- **WeaponMountAutoloader**: doubles mount slots, adds 10 magazines, costs 20 ×
  magazine cost; increases minimum manipulator size by +1.
- **FireControlSystem** (`basic`/`improved`/`enhanced`/`advanced`): 1 slot,
  Weapon Skill DM +1 to +4; tied to one weapon or linked mount set.

Each weapon requires its own mount. Up to four same-type mounts can be linked;
linked mounts share one fire control system and add +1 per damage die per extra
weapon on a hit.

### Stinger (robot-only edge case)

The Stinger (`refs/robot/17_stinger.md`) is a zero-slot melee weapon that is a
robot construction option, not CSC gear. It inflicts 1 point of damage with AP
equal to the robot's base armour. Multiple stingers may be installed (each a
separate zero-slot option); up to four can be clustered in a single attack. It does
not require `ceres.gear.weapons` to implement, but implementation should wait until
the attacks row model is established.

### Attacks Row

The robot spec currently hard-codes `attacks='—'` for all robots that have no
weapon mounts. A proper attacks row should:

1. Collect all installed WeaponMount parts.
2. Retrieve weapon damage/traits from the installed gear object.
3. Render the attacks string in the same format as the Robot Handbook stat blocks:
   e.g. `Gauss Rifles ×2 (linked: 4D+4, AP 5, Auto 3, Scope), 880 shots`.

The attacks model should be deferred until `ceres.gear.weapons` is in place and at
least one armed robot example has a known-good expected output.

### Non-Goals For Weapons

- Do not invent a `RobotWeapon` class that duplicates CSC weapon tables.
- Do not add WeaponMount or FireControlSystem until the gear-backed attacks row is
  designed.
- Do not model the Stinger before the attacks row model exists.

## Non-Goals For The First Pass

- Do not redesign the whole robot options system before transceivers are proven.
- Do not move communications equipment into `gear.computer`.
- Do not infer missing rules from existing test cases.
- Do not make every robot option generic gear if its source treats it as a
  robot-only construction abstraction.
