# Plan: Ship section sub-objects

## Problem

`Ship` currently has ~25 flat fields. Adding new components keeps growing the
flat list indefinitely. There is no natural grouping at the Python level, so
both the construction API and `_all_parts()` are getting hard to scan.

The spec has a well-defined section taxonomy. `Hull` already works as a
sub-object. The goal is to apply the same pattern to every section.

Current status note:

- The report/spec layer already has an explicit section taxonomy via
  `SpecSection` and `ShipSpec`.
- The remaining work in this plan is about making the Python-side `Ship`
  structure match the same reality more cleanly, so the implementation of the
  rules becomes easier to extend.

This plan is therefore about the Python construction model first, not about the
Markdown/PDF rendering layer. The spec layer already has a workable section
taxonomy; the remaining problem is that `Ship` itself is still too flat.

---

## Proposed structure

Each section becomes a frozen Pydantic sub-object that groups its parts, owns
its `_all_parts()` method, and mirrors the matching Python module.

| `Ship` field      | Class               | Module         | Contains                                               |
|-------------------|---------------------|----------------|--------------------------------------------------------|
| `ship.hull`       | `Hull`              | `ship.py`      | configuration, armour, stealth, airlocks, aerofins     |
| `ship.drives`     | `DriveSection`      | `drives.py`    | m_drive, jump_drive                                    |
| `ship.power`      | `PowerSection`      | `drives.py`    | fusion_plant                                           |
| `ship.fuel`       | `FuelSection`       | `storage.py`   | jump_fuel, operation_fuel, scoops, processor           |
| `ship.command`    | `CommandSection`    | `bridge.py`    | bridge or cockpit                                      |
| `ship.computer`   | `ComputerSection`   | `computer.py`  | hardware + software list                               |
| `ship.sensors`    | `SensorsSection`    | `sensors.py`   | primary sensors + countermeasures                      |
| `ship.weapons`    | `WeaponsSection`    | `weapons.py`   | turrets, fixed_firmpoints, missile_storage             |
| `ship.craft`      | `CraftSection`      | `crafts.py`    | docking_space (+ carried craft)                        |
| `ship.habitation` | `HabitationSection` | `habitation.py`| staterooms, low_berths, common_area                    |
| `ship.systems`    | `SystemsSection`    | `systems.py`   | medical_bay, workshop, probe_drones, repair_drones     |
| `ship.cargo`      | `CargoSection`      | `storage.py`   | cargo_holds                                            |

> **Jump + Propulsion merged:** The original plan had separate `JumpSection`
> and `PropulsionSection`. These are merged into `DriveSection` — both drives
> live together and the spec renders them in separate visual sections regardless.

> **Fuel boundary:** Jump fuel and operation fuel live in `FuelSection`
> alongside scoops and processor, but the section belongs in `storage.py`,
> not `drives.py`. The interfaces to jump drive and power plant are clear
> enough already; the likely future overlap is with storage/cargo concepts,
> not with drive hardware.

> **Storage direction:** Fuel and cargo should live next to each other in
> `storage.py`, since future rules are likely to involve shared storage logic:
> fuel bladders in cargo space, combined fuel/cargo containers, fuel tank
> compartments, and mountable tanks.

Working interpretation:

- the section objects are primarily for making `Ship` smaller and clearer
- the fact that they also line up with the report/spec sections is a benefit,
  not the primary reason for the refactor
- we should still prefer the section object only when it makes the Python API
  clearer
- `FuelSection` and `CargoSection` should be designed with future shared
  storage logic in mind

---

## Design rules

- Every section class is a frozen Pydantic model (same as `Hull` today).
- Every section class has `_all_parts() -> list[ShipPart]` returning parts in spec-display order.
- Sections that may be absent are `Optional` and default to `None`.
- Section classes live in the module matching their content.
- `Ship._all_parts()` becomes a simple concatenation of each section's `_all_parts()`.
- `ShipSpec` / `SpecSection` remain the place where report ordering is defined.
- A report section and a Python section object usually correspond, but the plan
  should not force a Python section object before it makes the construction API
  better.

---

## Migration steps

1. ✅ **Airlocks and aerofins into `Hull`.**
2. ✅ **`WeaponsSection`** in `weapons.py` — `Ship.weapons: WeaponsSection | None`.
3. ✅ **`SensorsSection`** in `sensors.py` — `Ship.sensors: SensorsSection` (always present, defaults to BasicSensors).
4. ✅ **`ComputerSection`** in `computer.py` — `Ship.computer: ComputerSection | None`.
5. ✅ **`HabitationSection`** in `habitation.py` — `staterooms`, `low_berths`, `common_area` → `Ship.habitation: HabitationSection | None`.
6. **`SystemsSection`** in `systems.py` — `medical_bay`, `workshop`, `probe_drones`, `repair_drones` → `Ship.systems: SystemsSection | None`.
   - Good candidate once more systems accumulate or when `_all_parts()`/construction starts to feel noisy there.
7. **`FuelSection`** in `storage.py` — `jump_fuel`, `operation_fuel`, `fuel_scoops`, `fuel_processor` → `Ship.fuel: FuelSection | None`.
   - Strong candidate because the parts already behave as one conceptual group.
   - Current code has an interim `FuelSection` in `drives.py`; the plan is to move that concept to `storage.py`.
8. **`CommandSection`** in `bridge.py` — `bridge`, `cockpit` → `Ship.command: CommandSection | None`.
   - Strong candidate because bridge/cockpit are mutually exclusive alternatives.
9. **`DriveSection`** in `drives.py` — `m_drive`, `jump_drive` → `Ship.drives: DriveSection | None`.
   - Required by this plan, but worth doing only when we can keep the API as clear as the current flat fields.
10. **`CargoSection`** in `storage.py` — `cargo_holds` → `Ship.cargo: CargoSection | None`.
   - Keep this close to `FuelSection`, since future rules are likely to blur the boundary between cargo and fuel storage.

Additional status note:

- `Hull` is not only started but already contains `armour`, `stealth`,
  `airlocks`, and `aerofins` as intended.
- On the report side, section ordering and section ownership are already much
  clearer than this migration list implies, because `ShipSpec`/`SpecSection`
  already drive the spec output.

Practical implication:

- steps 6–10 no longer block a clean report
- they are now about cleaning up the Python construction model so the rules are
  easier to implement and reason about

---

## Compatibility note

JSON keys change as fields become nested objects. No serialized JSON is
persisted outside tests, so this is not a concern in practice — tests are
updated in the same commit as each step.

Implementation note:

- when taking one migration step, do the matching JSON/test updates in the same
  commit
- avoid partial nesting where both the old flat field and the new section field
  coexist for long

---

## Weapons.py rework (separate, later)

The current weapons model maps poorly to the rules. This is a known limitation,
not something to fix during the section refactor. After the refactor is done,
`WeaponsSection` provides a clean boundary for a proper rewrite.

Rules model (for reference):

- Ships have **hardpoints** (1 per 100t displacement); smallcraft have **firmpoints**.
- Mounts: fixed mount, turret, barbette, bay — all fit in hardpoints.
  Firmpoints take fixed mounts and turrets only (no bays).
- Weapons are designed for specific mount types (most fit fixed or turret;
  barbettes and bays are their own category).
- Firmpoint mounting reduces effective range and power.
- The current `FixedFirmpoint` is really a firmpoint mount wrapping a
  `PulseLaser`. `DoubleTurret`/`TripleTurret` model turret mounts but don't
  enforce hardpoint limits or separate mount from weapon consistently.
