# Plan: Remove `_tl` ClassVar / `_fill_tl_from_class_var` from CeresPart subclasses

## Context

`CeresPart.tl` is an instance field (Pydantic, serialised). For parts whose TL is a fixed class
property (armour, sensors, hull options, …) the codebase works around this with:

1. `ShipPart._tl: ClassVar[int] = 0` — a class-level constant
2. `ShipPart._fill_tl_from_class_var` — a `model_validator(mode='before')` that injects `tl=N`
   into the dict before Pydantic validation whenever `_tl > 0`

This is an unnecessary indirection. `FusionPlant` already shows the right pattern for parts whose
TL varies with a configuration parameter (output level): split into per-TL subclasses
(`FusionPlantTL8`, `FusionPlantTL12`, `FusionPlantTL15`), each with its own class constants. The
`_tl` mechanism on those subclasses is itself still the old pattern and should be replaced too.

**Goal:** Every `CeresPart` subclass should express its minimum available TL as a plain Pydantic
field default (`tl: int = N`), with no `_tl` ClassVar and no `_fill_tl_from_class_var` validator.
Parts whose TL depends on a runtime parameter (drive level) must first be split into per-level or
per-TL subclasses so TL can become a class-level constant.

Scope is deliberately limited to `CeresPart` subclasses. Other model hierarchies may have `_tl`
class vars for their own purposes, but they are not part of this cleanup unless they inherit from
`CeresPart`.

`Assembly.tl` (e.g. `Ship.tl`) remains a plain instance field — a ship is an instance, not a
subclass.

## Review comments

Overall direction looks good: replacing the pre-validation injection with ordinary field defaults
will make the model shape much easier to see. A few points should be corrected before implementation:

- Ship software has been split out after this plan was written, but `SoftwarePackage` is not a
  `CeresPart`/`ShipPart`. Leave `src/ceres/make/ship/software.py` and `src/ceres/gear/software.py`
  out of this refactor even though they still use `_tl` internally.
- `src/ceres/make/ship/weapons.py` has at least one fixed `_tl` user (`FixedMount`). If the goal is
  to delete `ShipPart._tl`, this file must be included in Part 1.
- Part 2 changes `MDrive`, `JDrive`, and `RDrive` from constructible classes into type aliases.
  That means calls like `MDrive.model_validate(...)` and `MDrive(level=2)` stop working. The tests
  already contain direct constructor and direct `model_validate` calls, so either the plan should
  update those to `MDrive2(...)` / `TypeAdapter(MDrive).validate_python(...)`, or keep a factory API
  for backwards compatibility.
- The discriminated drive union can deliberately drop support for old serialized data. Existing
  payloads with only `{"level": 2}` will no longer validate; tests and fixtures should be updated to
  the new discriminator-based shape.
- With per-level drive subclasses, invalid-level tests change shape. `MDrive(level=99)` currently
  creates an object with a domain note; the new API will usually fail during Pydantic validation or
  attribute construction. The plan should call out this behavioral change and update tests
  intentionally.
- For `RDrive`, consider whether per-level subclasses are worth the larger API churn. Unlike
  customisable drives, `RDrive` has only one extra boolean option and no discriminated sibling
  pattern today. Splitting it is consistent, but it is a lot of surface area for a simpler part.

Suggested implementation order:

1. First land the fixed-`_tl` cleanup across `ShipPart` subclasses, including `weapons.py`, while
   leaving dynamic `_fill_tl` validators in place.
2. Then do the drive split with explicit test and fixture updates for the new discriminator-based
   payload shape.

---

## Part 1 — Fixed-TL parts (mechanical, low risk)

These currently use `_tl: ClassVar[int] = N`. Change each to `tl: int = N` as a plain field
default. Remove the `_tl` line. The `_fill_tl_from_class_var` validator in `ShipPart` must be
deleted; it becomes dead code once all `_tl` usages are gone.

Only apply this to `CeresPart` subclasses. Do not chase `_tl` usages in non-part classes such as
software packages.

### Files and classes

**`src/ceres/make/ship/armour.py`**
Each armour subclass already has `_tl`. Change to field default with `exclude=True` (armour TL is
a class constant, no need to serialise it):
- `TitaniumSteelArmour`: `tl: int = Field(default=7, exclude=True)`
- `CrystalironArmour`: `tl: int = Field(default=10, exclude=True)`
- `BondedSuperdenseArmour`: `tl: int = Field(default=14, exclude=True)`
- `MolecularBondedArmour`: `tl: int = Field(default=16, exclude=True)`

Remove `tl: int = Field(default=0, exclude=True)` from `Armour` base (it was there only to
shadow `CeresPart.tl` and prevent an alias mess that no longer exists).

**`src/ceres/make/ship/drives.py`** — `_FusionPlant` subclasses
- `FusionPlantTL8`: `tl: int = 8` (replaces `_tl = 8`)
- `FusionPlantTL12`: `tl: int = 12`
- `FusionPlantTL15`: `tl: int = 15`

Remove `_tl: ClassVar[int]` declaration from `_FusionPlant` base.

**`src/ceres/make/ship/hull.py`** — hull option/stealth subclasses
Find all `_tl = N` in hull option classes (BasicStealth etc.), replace with `tl: int = N`.

**`src/ceres/make/ship/sensors.py`** — sensor subclasses
All sensor classes (BasicSensors, CivilianSensors, CommercialSensors, …) use `_tl`. Replace
each with `tl: int = N`.

**`src/ceres/make/ship/systems.py`** — system subclasses with `_tl`
Replace `_tl` with `tl: int = N` on the affected classes.

**`src/ceres/make/ship/habitation.py`**
Replace `_tl` with `tl: int = N`.

**`src/ceres/make/ship/parts.py`**
- Delete `_tl: ClassVar[int] = 0` from `ShipPart`
- Delete `_fill_tl_from_class_var` model_validator from `ShipPart` entirely

---

## Part 2 — Drive subclassing (MDrive, JDrive, RDrive)

These use a per-class `_fill_tl` model_validator that reads TL from a `_specs` dict keyed by
`level`. Because TL depends on `level` (a runtime value), TL cannot be a class constant on a
single class.

**Pattern:** follow `FusionPlant`. For each drive type, create a private abstract base and one
concrete subclass per level. `level` moves from an instance field to a class constant
(`_level: ClassVar[int]`). The `_specs` dict and `_fill_tl` validator are removed. A plain
`tl: int = N` field default replaces them.

All existing computations that reference `self.level` use a `@property level` returning `_level`.

A `TypeAlias` named `MDrive` / `JDrive` / `RDrive` is created as the discriminated union of all
subclasses, so `DriveSection(m_drive=MDrive2(), j_drive=JDrive3())` remains readable.

### MDrive  (`src/ceres/make/ship/drives.py`)

Current: `MDrive(level: int)` with 12 levels and a `_specs` dict.
New: `_MDrive(CustomisableShipPart)` abstract base, 12 concrete subclasses:

| Class | level | tl | tons_percent |
|---|---|---|---|
| `MDrive0` | 0 | 9 | 0.005 |
| `MDrive1` | 1 | 9 | 0.01 |
| `MDrive2` | 2 | 10 | 0.02 |
| `MDrive3` | 3 | 10 | 0.03 |
| `MDrive4` | 4 | 11 | 0.04 |
| `MDrive5` | 5 | 11 | 0.05 |
| `MDrive6` | 6 | 12 | 0.06 |
| `MDrive7` | 7 | 13 | 0.07 |
| `MDrive8` | 8 | 14 | 0.08 |
| `MDrive9` | 9 | 15 | 0.09 |
| `MDrive10` | 10 | 16 | 0.10 |
| `MDrive11` | 11 | 17 | 0.11 |

Example subclass definition:
```python
class MDrive2(_MDrive):
    drive_type: Literal['mdrive_2'] = 'mdrive_2'
    tl: int = 10
    _level: ClassVar[int] = 2
    _tons_percent: ClassVar[float] = 0.02
```

`_MDrive` base defines all compute methods using `_level` and `_tons_percent` class vars.
`drive_type` is the Pydantic discriminator (same pattern as `FusionPlant.plant_type`).
`MDrive = Annotated[MDrive0 | MDrive1 | … | MDrive11, Field(discriminator='drive_type')]`

### JDrive  (`src/ceres/make/ship/drives.py`)

Each level maps to a unique TL. 9 subclasses:

| Class | level | tl | tons_percent |
|---|---|---|---|
| `JDrive1` | 1 | 9 | 0.025 |
| `JDrive2` | 2 | 11 | 0.05 |
| `JDrive3` | 3 | 12 | 0.075 |
| `JDrive4` | 4 | 13 | 0.10 |
| `JDrive5` | 5 | 14 | 0.125 |
| `JDrive6` | 6 | 15 | 0.15 |
| `JDrive7` | 7 | 16 | 0.175 |
| `JDrive8` | 8 | 17 | 0.20 |
| `JDrive9` | 9 | 18 | 0.225 |

`parsecs` property returns `_level`. `JDrive` becomes the discriminated union TypeAlias.

### RDrive  (`src/ceres/make/ship/drives.py`)

17 levels, split per level (consistent with MDrive/JDrive):

| Class | level | tl | tons_percent |
|---|---|---|---|
| `RDrive0` | 0 | 7 | 0.01 |
| `RDrive1` | 1 | 7 | 0.02 |
| `RDrive2` | 2 | 7 | 0.04 |
| `RDrive3` | 3 | 7 | 0.06 |
| `RDrive4` | 4 | 8 | 0.08 |
| `RDrive5` | 5 | 8 | 0.10 |
| `RDrive6` | 6 | 8 | 0.12 |
| `RDrive7` | 7 | 9 | 0.14 |
| `RDrive8` | 8 | 9 | 0.16 |
| `RDrive9` | 9 | 9 | 0.18 |
| `RDrive10` | 10 | 10 | 0.20 |
| `RDrive11` | 11 | 10 | 0.22 |
| `RDrive12` | 12 | 10 | 0.24 |
| `RDrive13` | 13 | 11 | 0.26 |
| `RDrive14` | 14 | 11 | 0.28 |
| `RDrive15` | 15 | 11 | 0.30 |
| `RDrive16` | 16 | 12 | 0.32 |

`RDrive` becomes the discriminated union TypeAlias.

---

## Part 3 — ComputerPart  (`src/ceres/gear/computer.py`)  *(deferred)*

`ComputerPart.tl` varies by **(equipment_type × processing_level)**: `PortableComputer`
processing=0 is TL 7, but `Tablet` processing=0 is TL 8. For consistency with the drive
subclassing above, `ComputerPart` should also be split into per-combination subclasses
(`PortableComputerPart0`, `PortableComputerPart1`, …, `TabletPart0`, …), each with `tl` and
`processing` as class constants.

This requires reworking how `ComputerEquipment._resolve_processing` constructs its inner part, and
potentially how `ComputerBase` subclasses in `src/ceres/make/ship/computer.py` are defined.

**Deferred:** implement after the drive subclassing work (Part 2) is complete and stable, as a
separate task. Until then, `ComputerPart.tl` remains a plain instance field set at construction.

---

## Verification

```bash
uv run pytest                        # full quick suite must be green
uvx ruff check                       # no lint errors
uvx ty check                         # no type errors
```

The ship test cases in `tests/ships/` are the integration targets. After Part 2, update
all instantiation sites from `MDrive(level=N)` / `JDrive(level=N)` / `RDrive(level=N)` to
`MDriveN()` / `JDriveN()` / `RDriveN()`.

---

## Files modified summary

| File | Change |
|---|---|
| `src/ceres/make/ship/parts.py` | Delete `_tl` ClassVar and `_fill_tl_from_class_var` from `ShipPart` |
| `src/ceres/make/ship/armour.py` | `_tl` → `tl: int = Field(default=N, exclude=True)` on each subclass; remove `tl` override from `Armour` base |
| `src/ceres/make/ship/drives.py` | Split `MDrive`/`JDrive`/`RDrive` into per-level subclasses; `_tl` → `tl: int = N` on FusionPlant subclasses |
| `src/ceres/make/ship/hull.py` | `_tl` → `tl: int = N` on hull option subclasses |
| `src/ceres/make/ship/sensors.py` | `_tl` → `tl: int = N` on all sensor subclasses |
| `src/ceres/make/ship/systems.py` | `_tl` → `tl: int = N` |
| `src/ceres/make/ship/habitation.py` | `_tl` → `tl: int = N` |
| `tests/ships/*.py` | Update drive instantiation to new API (`MDrive(level=2)` → `MDrive2()`) |
