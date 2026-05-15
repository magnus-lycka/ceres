# Plan: `ceres.make.robot`

## Purpose

Build a new `ceres.make.robot` package with the same overall ambition and
working style as `ceres.make.ship`: a declarative Python model for Traveller
robots that can calculate stat blocks, validate design consistency, round-trip
through JSON, and produce a structured spec for reporting.

The first version should be based on `refs/robot` and limited to ordinary Robot
Handbook robots in Size 1-8. Microbots, nanorobots, vehicle brains, ship's
brains, androids, biological robots, avatars, clones, and very large
vehicle-like robots are deferred to later phases.

Early test examples:

- `refs/robot/109_domestic_servant.md`
- Basic Lab Control Robot in the same file
- possibly `refs/robot/110_lab_control_robot_advanced.md` once the core model
  can handle Advanced brains, drone controllers, and multiple control options

## Similarities With `ceres.make.ship`

Robots fit the same broad architecture as ships:

- A `Robot` is an `Assembly`, just like `Ship`.
- Installed components are parts that are bound to their assembly before
  context-dependent rules are queried.
- Domain values are computed as properties, not cached fields mutated during
  binding.
- JSON should describe design input, not stored derived values such as `cost`,
  `hits`, `slots_used`, `traits`, or `speed`.
- Polymorphic choices should use Pydantic discriminated unions, as ship armour,
  stealth, drives, and weapons do. This includes `Locomotion` — each locomotion
  type (`NoneLocomotion`, `WheelsLocomotion`, `GravLocomotion`, …) is its own
  class with a `type` discriminator field.
- `notes` should be used for TL errors, slot overload, bandwidth overload, and
  similar design issues rather than raising hard exceptions.
- A built spec should be structured data for rendering and regression tests,
  not just text.

The most important existing patterns to reuse are:

- `src/ceres/shared.py`: `Assembly`, `CeresPart`, `NoteList`
- `src/ceres/make/ship/base.py`: minimal assembly interface for parts
- `src/ceres/make/ship/parts.py`: context mixin, binding, TL checks,
  serialization patterns
- `src/ceres/make/ship/spec.py`: dataclass row/spec model
- `tests/make/ship/test_serialization.py`: JSON round-trip as a contract

`docs/assemblies_and_parts.md` is especially relevant: robot parts should follow
the same principle of one real domain inheritance chain plus pure
context/capability mixins.

## Differences From Ships

Robots do not have displacement, a power budget, or crew in the same way ships
do. Their central resource model is instead:

- `size`: controls base slots, base hits, attack roll DM, equivalent spaces, and
  basic cost. Modelled as `RobotSize(IntEnum)` with values 1–8; table lookups
  use the enum value directly.
- `slots`: used by physical options, manipulators, armour, power packs, and some
  brain installations.
- `zero_slots`: options that normally consume no slots (i.e. `slots == 0`).
  Zero-slot and slotted options live in the same `options` list; parts declare
  `slots: int` as a property and capacity checks filter by value. Extra zero-slot
  options beyond the default suite are limited to `Size + TL`; the five default
  suite items are counted separately and do not consume that quota.
- `locomotion`: primary movement mode with TL, agility, traits, base endurance,
  and cost multiplier.
- `brain`: programming/control type, INT, bandwidth, skill DM, security/expert
  capabilities, and sometimes slot cost depending on robot size/TL.
- `skills`: software packages with TL, bandwidth, cost, and adjustment from INT,
  DEX, STR, or traits.
- `traits`: combined presentation surface from size, armour, locomotion,
  sensors, options, and brain/package rules.
- `endurance`: starts from locomotion and is modified by TL, efficiency, power
  packs, and some power options.

The robot model should therefore not be forced into `ShipPart` or `ShipSpec`.
It should share common base patterns but define its own concepts:
`RobotPartMixin`, `RobotSpec`, `RobotSpecRow`, and `RobotSection`.

## Initial Scope

Implement only ordinary robots following the main robot design sequence:

1. Chassis Size 1-8
2. Primary locomotion, including `None`, `Wheels`, `Tracks`, `Grav`, `Walker`,
   and the other table entries
3. Chassis options needed for the first examples:
   base armour, endurance TL modifier, decreased resiliency, spare slots
4. Default Suite and zero-slot options as data/presentation
5. Slotted options needed for Domestic Servant and Lab Control:
   domestic cleaning equipment, storage compartment, external power,
   robotic drone controller, basic/improved sensors/comms/display/voder
6. Brain types needed:
   Primitive, Basic, Advanced
7. Skill packages needed:
   Primitive (clean), Electronics (remote ops), Recon, and simple standard
   packages
8. Final stat block:
   Robot, Hits, Locomotion, Speed, TL, Cost, Skills, Attacks, Manipulators,
   Endurance, Traits, Programming, Options

Defer:

- weapons and attacks except for presentation values such as `none`/`-`
- the full manipulator rule model, beyond being able to declare `none` or a list
  of manipulators
- combat and critical hit rules
- hacking, sanity, backups, physical upgrades after purchase
- catalogs/PDF/HTML until stat blocks and JSON are stable

## Proposed Package Structure

```text
src/ceres/make/robot/
  __init__.py
  base.py          # RobotBase: tl, size, locomotion, parts_of_type()
  robot.py         # Robot aggregate, build_notes(), build_spec()
  spec.py          # RobotSpec, RobotSpecRow, RobotSection
  chassis.py       # RobotSize table, chassis modifiers, armour/endurance bits
  locomotion.py    # Locomotion discriminated union, speed/endurance/agility
  parts.py         # RobotPartMixin + RobotPart, slot/cost/TL helpers
  options.py       # zero-slot and slotted options used by first examples
  brain.py         # Primitive/Basic/Advanced brain models
  skills.py        # skill packages, adjusted skill display, bandwidth accounting
  text.py          # formatting helpers shared inside robot package
```

Unit-level test structure:

```text
tests/make/robot/
  test_chassis.py
  test_locomotion.py
  test_options.py
  test_brain.py
  test_skills.py
  test_robot.py
  test_serialization.py
```

Catalogue/example test structure should mirror `tests/ships` rather than
collecting every example in one large file:

```text
tests/robots/
  README.md
  __init__.py
  _output.py
  test_domestic_servant.py
  test_lab_control_robot_basic.py
  test_lab_control_robot_advanced.py
  test_gallery.py
  test_gallery_coverage.py
  generated_output/
    json/
    html/
    pdf/
    typst/
```

Each robot example file should own one or a very small family of related
reference robots. It should expose a `build_<name>()` function, just as the ship
example tests do. `test_gallery.py` should import and register those builders,
generate regression artifacts, and eventually exercise renderers once robot
rendering exists. `test_gallery_coverage.py` should enforce that every
`tests/robots/test_*.py` example file is imported by the gallery, excluding only
the gallery files themselves.

If `RobotPart` later needs to share concrete equipment with gear, vehicle, or
ship code, build it according to `assemblies_and_parts.md`: generic part plus a
pure robot mixin, not multiple inheritance from several domain models.

## Domain Model

### `Robot`

Proposed shape:

```python
class Robot(RobotBase):
    name: str
    tl: int
    size: RobotSize           # IntEnum, values 1–8
    locomotion: LocomotionUnion
    brain: RobotBrainUnion
    chassis_options: list[ChassisOption] = Field(default_factory=list)
    default_suite: list[DefaultSuiteItem] = Field(default_factory=default_suite_items)
    options: list[RobotOptionUnion] = Field(default_factory=list)
    manipulators: list[str] = Field(default_factory=list)
    attacks: list[str] = Field(default_factory=list)
```

`options` holds all extra options (both zero-slot and slotted) as a discriminated
union list. Zero-slot capacity and slot capacity are checked by filtering on
`option.slots == 0`. `manipulators` and `attacks` are plain string lists for
Phase 1–4; proper rule models can replace them when test cases require it.

Sections own their spec rows: `locomotion`, `brain`, and option parts each
implement `add_spec_rows(robot, spec)`. `Robot.build_spec()` delegates to these
rather than building a long flat method.

### Parts And Options

A robot part should expose:

- `slots: int`
- `zero_slot: bool` or `slots == 0`
- `cost: float`
- `tl: int`
- `traits: tuple[Trait, ...]` or a simple presentation model
- `skills: tuple[SkillGrant, ...]` where relevant
- `option_label`

As with ship parts, computed values should be properties. Example:

```python
class DomesticCleaningEquipment(RobotPart):
    size: Literal["small", "medium", "large"]

    @property
    def slots(self) -> int: ...

    @property
    def cost(self) -> float: ...
```

### Traits

Start with a small value model:

```python
@dataclass(frozen=True)
class Trait:
    name: str
    value: int | str | None = None
```

The spec can format `Armour (+2)`, `Small (-2)`, `Flyer (high)`, and `ATV`.
Avoid modelling the whole Traveller trait system immediately.

### Skills

The first model needs to express:

- hard-coded package skills from Primitive/Basic brain packages
- standard skill packages for Advanced brains
- bandwidth consumed
- available bandwidth as a presentation row, such as `+1 Bandwidth available`
- adjusted skill level when INT DM should appear in the stat block: e.g.
  Electronics-0 + INT 9 (DM+1) is presented as `Electronics (Any) 1`. The
  spec always shows the adjusted level; the unadjusted level is design input.
- STR/DEX adjustments are deferred: they depend on which manipulator arm is
  acting, which varies by context. Do not attempt to model this until a
  concrete test case forces it.

The first test examples can keep this pragmatic:

- Domestic Servant gets `Profession (domestic cleaner) 2` from Primitive
  (clean) and `Recon 1` from the recon sensor/option according to the stat
  block. Options that grant skills carry `skills: tuple[SkillGrant, ...]`;
  `SkillSection` (or the Robot's skill aggregation) collects from brain + options.
- Basic Lab Control gets `Electronics (remote ops) 1, +1 Bandwidth available`.

As more examples are added, the skill packages can be normalized more strictly.

## First Test Cases

### Domestic Servant

From `refs/robot/109_domestic_servant.md`:

- TL 8
- likely Size 3: base hits 8, Small (-2), basic cost Cr400
- Wheels: base endurance 72h, cost multiplier x2
- Hits 6: base 8 with decreased resiliency -2
- Armour (+2): TL8 base protection
- Speed 4m: differs from default 5m and should be modelled explicitly or with a
  speed modification once the rule is identified
- Cost Cr500: likely rounded/discounted final cost, not a raw design sum
- Programming: Primitive (clean)
- Options:
  Auditory Sensor, Domestic Cleaning Equipment (small), Recon Sensor
  (improved), Storage Compartment (4 Slots), Transceiver 5km (improved),
  Visual Spectrum Sensor, Voder Speaker, Wireless Data Link

Early test goals:

- `robot.hits == 6`
- `robot.base_slots == 4`
- `robot.used_slots <= robot.available_slots`
- stat block contains cost `Cr500`, endurance `79 hours`, traits, and skills
  matching the source
- JSON round-trip preserves concrete types and design input

Note: cost/endurance/speed appear to include catalogue rounding or options not
yet identified. Do not add override fields to `Robot`; instead mark the
discrepancy with a `TODO` assertion in the test and record the open question in
`docs/RULE_INTERPRETATIONS.md`. Override fields become permanent technical debt
— rule derivation is always preferred.

### Basic Lab Control Robot

From the same file:

- TL 12
- likely Size 1: base hits 1, base slots 1, Small (-4), basic cost Cr100
- Locomotion None: 0m, base endurance 216h, +25% available slots rounded up
- TL12 endurance +50% -> 324h
- Armour (+4): TL12 base protection
- Programming: Advanced (INT 8)
- Skills: `Electronics (remote ops) 1, +1 Bandwidth available`
- Options:
  Auditory Sensor, External Power, Robotic Drone Controller (basic),
  Transceiver 500km (improved), Video Screen (improved), Voder Speaker,
  Wireless Data Link
- Cost Cr12000

Early test goals:

- `robot.hits == 1`
- `robot.available_slots == ceil(1 * 1.25) == 2` for locomotion None
- endurance `324 hours`
- programming label `Advanced (INT 8)`
- basic drone controller limits Remote Ops to 0 in notes or in adjusted control
  calculation, because the source text calls out that limit

## Phases

### Phase 1: Skeleton And Contracts

Scope: `Robot` can be instantiated with size + locomotion + brain (no options).
Size and locomotion tables are correct. JSON round-trip works.

- Create the package structure (all files, empty or stub).
- `RobotSize(IntEnum)` table: base_slots, base_hits, attack_dm, basic_cost.
- `RobotBase(Assembly)`: fields `tl`, `size`, `locomotion`; property
  `parts_of_type()`. Derived slot/hit properties live on `Robot`, not here.
- Locomotion discriminated union: `NoneLocomotion`, `WheelsLocomotion`, and
  at least one more needed for the first two examples. Each has `speed`,
  `base_endurance`, `cost_multiplier`, `agility`, `traits`, `slots_modifier`.
- `RobotPartMixin` (pure ABC): declares `slots: int`, `cost: float`, `tl: int`,
  `traits`, `skills`; `bind(robot)` + `check_tl()`.
- `RobotPart(CeresPart, RobotPartMixin)`: concrete base part.
- Minimal `Robot(RobotBase)` with the fields listed above.
- `available_slots`, `used_slots`, `base_hits`, `base_armour`, `base_endurance`.
- Write tests: size table lookups, locomotion table lookups, JSON round-trip for
  a minimal robot (size + locomotion + brain, no options).

### Phase 2: Brains And Skills For The First Examples

- Implement Primitive, Basic, and Advanced brain rows from `33_brain.md`.
- Implement a package model for Primitive (clean) and a small subset of standard
  skills.
- Implement bandwidth accounting and `+N Bandwidth available`.
- Write tests for the `Programming` row and skill row.

### Phase 3: Options For Domestic Servant And Basic Lab Control

- Implement default suite as a fixed list of zero-slot items (always present).
- Implement the options that appear in the first two stat blocks as `RobotPart`
  subclasses in `options.py`, each with a `type` discriminator field.
- Zero-slot capacity check: default suite items are free; extra zero-slot options
  (those in `Robot.options` with `slots == 0`) are limited to `Size + TL`.
  Document the interpretation (whether default suite counts or not) in
  `docs/RULE_INTERPRETATIONS.md` before implementing the check.
- Slot capacity check: sum of `option.slots` for all slotted options must not
  exceed `available_slots`. Include `None` locomotion +25% in available_slots.
- Options that grant skills expose `skills: tuple[SkillGrant, ...]`; Robot
  aggregates these with brain-package skills when building the skills row.
- Add `tests/robots/test_domestic_servant.py` and
  `tests/robots/test_lab_control_robot_basic.py` with builder functions and
  focused stat block assertions.

### Phase 4: Spec And Reportable Shape

- `Robot.build_spec()` should produce the exact rows shown by Robot Handbook.
- Group output into the standard rows:
  Robot, Skills, Attacks, Manipulators, Endurance, Traits, Programming,
  Options.
- Add a robot gallery following the ship gallery pattern:
  `tests/robots/test_gallery.py`, `tests/robots/test_gallery_coverage.py`, and
  `tests/robots/generated_output/`.
- Keep rendering simple at first. JSON/spec output is enough until robot
  HTML/PDF/Typst renderers exist; the gallery can grow those checks later.

### Phase 5: Broaden Ordinary Robots

Once the first two examples are stable:

- add Utility Droid / Labour Droid for humanoid walker + manipulators
- add Basic Courier for grav locomotion and flyer traits
- add AG300 for multiple manipulators, storage, and sensors
- add more brain packages and standard skill packages as needed

Each new example should pull rules into the model only when the rule is needed.
Avoid loading the whole Robot Handbook into tables before there are test cases
that use those entries.

## Design Decisions To Document Later

Add robot-specific RI notes to `docs/RULE_INTERPRETATIONS.md` when an
interpretation choice is required. Expected questions:

- Exactly how catalogue final cost has been rounded or discounted.
- Whether stat block endurance is always a pure rules calculation or sometimes
  catalogue-adjusted.
- How the Domestic Servant's 4m speed arises.
- How sensors grant skills versus brain packages.
- How drone controller maximum skill should affect a robot's displayed Remote
  Ops.
- Whether `None` locomotion +25% slots affects only available option slots, or
  also some per-base-slot costs. The rules say Base Slots does not increase for
  coatings and similar options.

## Completion Definition For The First Implementation

The first `ceres.make.robot` milestone is complete when:

- Domestic Servant and Basic Lab Control Robot can be built with Python objects.
- Their stat blocks match the source's main rows for hits, locomotion, speed,
  TL, cost, skills, attacks, manipulators, endurance, traits, programming, and
  options.
- Slot, TL, and bandwidth overloads produce notes.
- JSON round-trip preserves design input and concrete part types.
- Derived values are recomputed after load and are not written as cached input
  fields unless they are explicit catalogue overrides.
- Micro/nano/large robots are deliberately excluded and have no half-finished
  special cases in the main model.
