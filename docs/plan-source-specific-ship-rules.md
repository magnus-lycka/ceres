# Plan: Source-Specific Ship Rule Modules

## Context

Ceres currently keeps most ship construction rules in broad modules such as
`power.py`, `drives.py`, `systems.py`, and `weapons.py`. That worked while most
implemented rules came from the default Core/High Guard rule set.

Spinward Extents introduces source-specific ship construction rules such as:

- Sterling fission power plants
- Spinward Extents solar panels, coatings, and sails
- primitive hulls
- plasma drives

These rules sometimes overlap with High Guard concepts while using different
tables, constraints, and assumptions. We should preserve source identity in code
instead of quietly merging unlike technologies.

Core and High Guard remain the default rule set and should not be split into
separate files just for source purity. Source-specific supplements can be split
out when they would otherwise blur the default model.

## Goals

- Keep default Core/High Guard imports simple.
- Make Spinward Extents and later supplement-specific rules visibly separate.
- Avoid circular imports when source-specific classes need shared base classes.
- Preserve existing public imports where practical, such as:

  ```python
  from ceres.make.ship.power import FusionPlantTL12, PowerSection
  ```

- Keep Pydantic discriminated unions explicit and serializable.
- Allow more source modules later without turning `power.py` or `drives.py` into
  a long mixed-source catalogue.

## Non-Goals

- Do not split Core and High Guard into separate files.
- Do not introduce a plugin system.
- Do not replace discriminated unions with a registry until we actually need
  that larger refactor.
- Do not model operational scenario state such as current orbital band or
  deployed/retracted status as part of this refactor.

## Proposed Pattern

Convert large subsystem modules into packages only when they need source-specific
separation.

Example for power:

```text
src/ceres/make/ship/power/
  __init__.py
  base.py
  default.py
  spinext.py
  types.py
  section.py
```

Responsibilities:

- `base.py`
  - shared abstract/base classes and helper logic
  - imports only stable low-level ship infrastructure such as `parts.py`,
    `spec.py`, and shared note/text helpers
  - no imports from source-specific modules

- `default.py`
  - Core/High Guard/default concrete classes
  - examples: fission, chemical, fusion, antimatter, High Guard/default solar
    systems if/when we keep those as default
  - imports from `base.py`

- `spinext.py`
  - Spinward Extents concrete classes
  - examples: Sterling fission, SpinExt solar panels/coatings/sails
  - imports from `base.py`
  - does not import from `power.__init__`

- `types.py`
  - assembles Pydantic discriminated unions from default and source-specific
    concrete classes
  - examples: `AnyPowerPlant`, `AnySolarPowerSource`,
    `AnyHighEfficiencyBatteries`

- `section.py`
  - owns subsystem section models that need assembled union types
  - example: `PowerSection`
  - imports union types from `types.py`

- `__init__.py`
  - public compatibility facade
  - re-exports default classes, source-specific classes, union types, and
    section classes
  - keeps existing public imports working

Dependency direction:

```text
base.py
  ↑
default.py   spinext.py
  ↑          ↑
       types.py
          ↑
       section.py
          ↑
      __init__.py
```

The important rule is that source modules import bases, but base/default/source
modules do not import the assembled package facade.

## Drives Package Status

The drives module has been converted into a package as part of adding Spinward
Extents plasma drives. The current shape is intentionally smaller than the full
future package decomposition:

```text
src/ceres/make/ship/drives/
  __init__.py
  standard.py
  spinext.py
```

Default/Core/High Guard manoeuvre, jump, reaction, and default solar-sail
support remain together in `standard.py`. Spinward Extents plasma drives are in
`spinext.py`. The public import path remains `ceres.make.ship.drives`.

Solar-sail placement decision:

- High Guard `SolarSail` is in `drives.standard` because it is a drive
  accessory and does not generate Power.
- Spinward Extents solar sails are also currently in `drives.standard` because
  they integrate with `DriveSection`; they may move to `drives.spinext` in a
  later cleanup if the source-specific package split is expanded.

## Migration Steps For Power

1. Create `src/ceres/make/ship/power/`.
2. Move shared bases into `power/base.py`.
3. Move current default/Core/High Guard classes into `power/default.py`.
4. Move Spinward Extents classes into `power/spinext.py`.
5. Move union definitions into `power/types.py`.
6. Move `PowerSection` into `power/section.py`.
7. Re-export the existing public API from `power/__init__.py`.
8. Run serialization tests before and after to ensure discriminator output is
   unchanged unless intentionally renamed.
9. Update imports only where internal modules benefit from clearer source
   paths. Do not churn all test imports just for neatness.

Compatibility concern:

Python cannot have both `power.py` and a `power/` package at the same import
path. The migration must rename/remove `power.py` in the same change that adds
the package directory.

## Future Drives Package Cleanup

The first migration slice is done. If the package grows further, continue with:

1. Move source-neutral bases into `drives/base.py`.
2. Rename `standard.py` to `default.py` if we want naming symmetry with other
   packages.
3. Move Spinward Extents solar sails from `standard.py` to `spinext.py` if the
   section and union wiring is split out.
4. Assemble drive unions in `drives/types.py`.
5. Move `DriveSection` to `drives/section.py`.
6. Keep re-exporting the current public API from `drives/__init__.py`.

## Pydantic Union Policy

Ceres currently relies on explicit discriminated unions. Keep that approach for
now.

Rules:

- Every concrete serializable part in a polymorphic field must appear in the
  appropriate union in `types.py`.
- Each source-specific class should use a discriminator value that preserves
  source identity when needed.
- Avoid ambiguous names where two sources define similar technologies with
  different rules.

Example:

```python
type AnyPowerPlant = Annotated[
    FusionPlantTL8
    | FusionPlantTL12
    | FissionPlant
    | SpinExtSterlingFissionPlantTL8,
    Field(discriminator='plant_type'),
]
```

The public class name can be shorter if the package/module makes source identity
clear, but serialized discriminator values should remain stable once shipped.

## Naming Guidance

Default/Core/High Guard rules get the plain names:

- `SolarPanels`
- `SolarCoating`
- `FusionPlantTL12`
- `MDrive4`

Supplement-specific rules should carry source identity when exposed alongside
default rules:

- `SpinExtSolarPanelsTL8`
- `SpinExtSterlingFissionPlantTL8`
- `SpinExtPlasmaDrive`
- `SpinExtPrimitiveHull`

If a class is imported from a source-specific module directly, shorter names may
be acceptable inside that module, but the package-level facade should avoid
ambiguity.

## Documentation Requirements

When adding a source-specific rules module:

- cite the local ref file in docs or tests
- add a `RULE_INTERPRETATIONS.md` entry only for actual interpretation choices
- use `todo_maybe.md` for unresolved design questions
- avoid encoding testcase-derived assumptions as rules

For solar systems specifically, keep
`docs/solar-energy-systems-comparison.md` updated until the HG/SpinExt modelling
choice is settled.

## Open Questions

- Should existing Spinward Extents classes be renamed to include `SpinExt` before
  the package split, or during it?
- Should `PowerSection` accept only default rules by default, with optional
  source-specific section variants, or should one assembled union include all
  supported published rules?
- If two supplements define incompatible versions of the same concept, do we
  keep adding source prefixes or introduce a higher-level ruleset selection?

## Recommended Next Step

Do not refactor all ship modules now. The next practical step is:

1. `hull` now follows the package structure with `standard.py` and `spinext.py`
   so Spinward Extents primitive hulls can stay separate from default hulls.
2. Consider converting `power.py` into the package structure above if solar or
   source-specific power support grows further.
3. Continue the drives package cleanup only when another source-specific drive
   change makes it worthwhile.
