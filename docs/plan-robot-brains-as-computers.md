# Plan: Robot Brains As Computer-Based Program Runners

## Goal

Robot brains should use the same underlying computer/software model as other
Ceres assemblies. A robot brain is not a ship computer, but it is a computer-like
part that can run software and consume bandwidth. This should mirror the current
relationship between `ceres.gear.computer.ComputerPart` and ship computers:

- generic computer/software semantics live in `ceres.gear`
- assembly-specific installation rules live in `ceres.make.<assembly>`
- the same software package classes can be installed in ships, robots, vehicles,
  and later other assemblies when the rules allow it

The practical outcome is that robot skill packages, expert packages, Intellect,
Virtual Crew-style packages, and future robot-specific software should be handled
through one shared software-running interface rather than each assembly inventing
its own package list.

## Current State

Ship computers already follow the desired pattern:

- `ceres.gear.computer.ComputerPart` defines generic computer capability through
  `processing`, TL, and retro/proto fields.
- `ceres.make.ship.computer.ComputerBase` combines `ComputerPart` with
  `ShipPartMixin`.
- `ComputerSection` owns installed ship software, adds included software, and
  validates software against hardware and ship context.

Robot brains are currently separate:

- `ceres.make.robot.brain` has `PrimitiveBrain`, `BasicBrain`, `AdvancedBrain`,
  and `VeryAdvancedBrain`.
- Brain table rows are stored in private robot-specific tables.
- `AdvancedBrain.installed_skills` and `VeryAdvancedBrain.installed_skills` use
  robot-specific `SkillPackage`.
- Skill packages already track `bandwidth` and `cost`, but are not represented as
  shared `SoftwarePackage` instances.

`ceres.gear.software` already defines a `SoftwarePackage` ABC with `bandwidth`,
`tl`, `cost`, `description`, and `validate_on_computer`. This is the interface
that robot skill packages should satisfy.

### Known Bug: VeryAdvancedBrain Bandwidth Validation

`VeryAdvancedBrain._resolve_bandwidth` (`brain.py:322`) returns `data` instead of
the modified `d`. Bandwidth upgrades therefore have no effect for Very Advanced
brains. This should be fixed as the first step of Phase 2, or as a standalone fix
regardless of this plan's timeline.

## Design Direction

Introduce a robot brain hardware class that combines generic computer semantics
with robot installation semantics:

```python
class RobotBrainBase(ComputerPart, RobotPartMixin):
    brain_type: str
    brain_tl: int
    installed_software: tuple[RobotSoftware, ...] = ()
```

This should not inherit from `RobotPart`, for the same reason `ShipComputer`
should not inherit from `ShipPart`: it would create two real domain inheritance
chains rooted in `CeresPart`. The pattern should follow
`docs/assemblies_and_parts.md`.

The robot-specific layer should own:

- brain category: Primitive, Basic, Advanced, Very Advanced
- robot brain TL table values
- robot Slots calculation
- robot INT and skill DM
- robot-specific programming labels
- any robot-only limitations on what software can run

The shared computer/software layer should own:

- generic processing/bandwidth capacity concepts
- software package identity
- software TL, bandwidth, cost, and notes
- common validation hooks where possible

## Important Distinction

A robot brain is not merely a normal portable computer installed in a robot. The
Robot Handbook brain table has its own cost, INT, slot, skill DM, and capability
rules. The shared computer base should provide software-running semantics, not
erase the robot brain rules.

`ComputerPart` is a capability base. `RobotBrainBase` is the robot-specific
hardware. `SoftwarePackage` is the shared program/package surface.

## Note on Deduplication

`AdvancedBrain` and `VeryAdvancedBrain` currently share nearly identical
implementation. Factoring out a shared base before this refactor is an extra step
that would itself be replaced when the `ComputerPart` inheritance is introduced.
Go directly to the full refactor rather than deduplicating the existing classes
first.

## Proposed Model

### 1. Shared Program Interface

`ceres.gear.software.SoftwarePackage` already exists as an ABC with the right
properties. Robot skill packages should satisfy this interface.

Existing ship software (`SoftwarePackage` subclasses) does not change.

### 2. Robot Brain Hardware

Refactor `_BrainBase` into a `ComputerPart` + `RobotPartMixin` base:

```python
class RobotBrainBase(ComputerPart, RobotPartMixin):
    brain_type: str
    brain_tl: int
    installed_software: tuple[RobotSoftware, ...] = ()
```

It should keep robot-brain properties:

- `base_int`
- `bandwidth`
- `skill_dm`
- `brain_cost`
- `hardware_cost`
- `remaining_bandwidth`
- `brain_slots(robot_tl, robot_size)`
- `programming_label()`

`ComputerPart.processing` maps to the Robot Handbook `Computer/X` value from the
brain table (`_BrainEntry.computer_x`). This value currently drives the slot
calculation; its role as a general computing power indicator is secondary.
`bandwidth` remains the robot-brain bandwidth from the Robot Handbook table, which
is not always equal to `processing`. Both concepts should remain named distinctly
so they are not confused.

### 3. Robot Skill Packages As Software

Convert `SkillPackage` into a `SoftwarePackage` subclass:

```python
class RobotSkillPackage(SoftwarePackage):
    name: str
    level: int
    bandwidth: int
```

It should preserve current rules:

- base cost comes from `refs/robot/35_skill_packages.md`
- cost at level N is `base * 10**N`
- installed package level is adjusted by brain skill DM when producing
  `SkillGrant`

`AdvancedBrain.installed_skills` and `VeryAdvancedBrain.installed_skills` become
`installed_software`, while `skill_grants` filters/derives skill grants from
software packages that grant robot skills.

### 4. Validation in `validate_on_computer`

`SoftwarePackage.validate_on_computer` takes a `ComputerPart` and currently
references `computer.assembly.tl` and `computer.retro_levels`. Robot brain
validation should not reuse this method directly — the context is different (no
retro levels in the same sense, different TL checks). Add a separate
`validate_on_brain(brain)` method, or override `validate_on_computer` in
`RobotSkillPackage` to apply robot-specific rules.

### 5. Included/Implicit Brain Programs

Primitive and Basic brains use named function packages such as `clean`, `alert`,
or `servant`. These should be represented carefully.

Short-term:

- keep `function` on Primitive/Basic brains
- keep `primitive_package_skills(function)` as the source of bundled skill grants
- expose bundled packages through an `included_software` or `included_programs`
  property if useful

Long-term:

- represent primitive/basic packages as software/package objects too, if the rule
  tables support a clean mapping
- avoid forcing all primitive package behaviour into generic software if the source
  treats them as fixed brain programming rather than installable programs

### 6. Robot Software Validation

Add validation equivalent in spirit to ship `ComputerSection.validate_software`,
but owned by the robot brain or robot assembly. Validation should cover:

- robot TL versus software TL
- brain bandwidth capacity
- per-package maximum bandwidth
- available total bandwidth
- whether Primitive/Basic brains may run arbitrary installable software
- whether Advanced or higher brains are required for standard skill packages
- future Avatar/receiver/controller rules that share software across brains

Do not immediately copy ship-specific rules such as Jump Control handling. Those
should remain ship-specific software rules.

### 7. Robot Assembly Integration

`Robot` should continue to expose a single `brain` field. The existing aggregation
points stay conceptually similar:

- total cost includes `brain.hardware_cost` plus installed software/package cost
- skill aggregation asks the brain for `skill_grants`
- detail/spec output lists brain hardware separately from installed packages
- remaining bandwidth is reported from the brain

Avoid adding a separate `ComputerSection` to robots unless rules later require
multiple brain/computer modules.

## Migration Plan

### Phase 1: Fix VeryAdvancedBrain Bug

Fix `VeryAdvancedBrain._resolve_bandwidth` to return `{**d, 'bandwidth': base}`
instead of `data`. Add a test proving bandwidth upgrades work for Very Advanced
brains. This can be done immediately, independently of the rest of this plan.

### Phase 2: Make Robot Brains ComputerPart-Based

- Refactor `_BrainBase` into a `ComputerPart` + `RobotPartMixin` compatible base.
- Map `_BrainEntry.computer_x` to `processing`.
- Preserve current public properties and serialization shape where reasonable.
- Keep existing class names: `PrimitiveBrain`, `BasicBrain`, `AdvancedBrain`,
  `VeryAdvancedBrain`.
- Cover both `AdvancedBrain` and `VeryAdvancedBrain` in this phase.

### Phase 3: Convert Installed Skills To Installed Software

- Introduce `RobotSkillPackage` as a `SoftwarePackage` subclass.
- Migrate `installed_skills` toward `installed_software`/`installed_packages`.
- Keep a compatibility alias for existing `installed_skills` inputs until tests
  and examples are updated.
- Update `skill_grants` to derive from installed robot skill software.

### Phase 4: Shared Software Use

- Allow selected shared `gear.software` packages on robot brains where rules
  support them.
- Start with `Expert`, because it is already context-independent and naturally
  related to robot skills.
- Decide whether `Intellect` is a generic software package, a robot brain
  capability, or both, based on the source rules.
- Keep ship-only packages ship-only. `JumpControl` should not become valid robot
  software merely because it shares the base type.

### Phase 5: Reporting And Serialization

- Update robot detail output to distinguish:
  - brain hardware
  - included/fixed programming
  - installed software/skill packages
  - bandwidth used/remaining
- Add serialization tests for robot brains with installed software.
- Confirm old robot reference tests still assert source-derived expected values.

## Test Strategy

Keep tests layered:

- `tests/make/robot/test_brain.py`: robot brain table values, slot behaviour,
  bandwidth, INT, skill DM, and robot-specific validation.
- `tests/make/robot/test_skills.py`: robot skill package cost, bandwidth, and
  skill grant mapping.
- `tests/gear/test_software.py`: context-independent software behaviour.
- `tests/make/ship/test_software.py`: ship-only software behaviour.
- `tests/robots/*`: source/reference validation only, using `_expected`.

Add focused regression tests for:

- `VeryAdvancedBrain` bandwidth upgrade works correctly (Phase 1)
- an Advanced brain running a robot skill package
- bandwidth overrun produces a robot brain note/error
- an old `installed_skills` input still round-trips during migration
- a shared `Expert` package can be installed once a policy is chosen
- ship software behaviour does not change

## Open Questions

- Should robot skill packages become generic `SoftwarePackage` directly, or
  should they be a robot-specific subclass?
- Which non-skill software packages are valid on robot brains?
- Is `ComputerPart.processing` the right generic name for the Robot Handbook
  `Computer/X` column, or should robot brains expose both `processing` and a
  separate `brain_computer_rating` for clarity?
- How should Primitive/Basic fixed functions be represented: installed software,
  included software, or fixed brain programming?
- How should brain bandwidth upgrades from `refs/robot/34_retrotech.md` combine
  with the shared software model?
- How should brain hardening (`/fib`) relate to ship computer `/fib`?

## Non-Goals For The First Refactor

- Do not implement avatar controller/receiver rules at the same time.
- Do not change ship computer API unless needed to extract a shared helper.
- Do not make every ship software package valid for robots by default.
- Do not rewrite all robot examples in one pass.

## Success Criteria

- Robot brains use the same computer/software base concepts as ship computers.
- Existing robot examples still pass with the same visible expected values.
- Installed robot skill packages are software-like objects with bandwidth, cost,
  TL, and notes.
- Shared software can be enabled per assembly context without duplicating the
  package model.
- The implementation follows the one-domain-chain plus pure-mixin rule from
  `docs/assemblies_and_parts.md`.
