# Plan: Ship section sub-objects

## Problem

`Ship` currently has ~25 flat fields. Adding new components keeps growing the
flat list indefinitely. There is no natural grouping at the Python level, so
both the construction API and `_all_parts()` are getting hard to scan.

The spec already has a well-defined section taxonomy:

```
Hull · Jump · Propulsion · Power · Fuel · Command · Computer
Sensors · Weapons · Craft · Habitation · Systems · Cargo
```

`Hull` already works as a sub-object. The goal is to apply the same pattern to
every section.

---

## Proposed structure

Each section becomes a frozen Pydantic sub-object that groups its parts, owns
its `_all_parts()` method, and mirrors the matching Python module (where one
exists).

| `Ship` field     | Class             | Module        | Contains |
|-----------------|-------------------|---------------|----------|
| `ship.hull`     | `Hull`            | `ship.py`     | configuration, armour, stealth, airlocks, aerofins, surface options |
| `ship.jump`     | `JumpSection`     | `drives.py`   | jump_drive, jump_fuel |
| `ship.propulsion` | `PropulsionSection` | `drives.py` | m_drive |
| `ship.power`    | `PowerSection`    | `drives.py`   | fusion_plant, operation_fuel, fuel_processor |
| `ship.fuel`     | `FuelSection`     | `drives.py`   | jump_fuel, fuel_scoops, fuel_processor *(see note)* |
| `ship.command`  | `CommandSection`  | `bridge.py`   | bridge or cockpit |
| `ship.computer` | `ComputerSection` | `computer.py` | computer hardware + software list |
| `ship.sensors`  | `SensorsSection`  | `sensors.py`  | primary sensors + countermeasures |
| `ship.weapons`  | `WeaponsSection`  | `weapons.py`  | turrets, fixed_firmpoints, missile_storage |
| `ship.craft`    | `CraftSection`    | `crafts.py`   | docking_space (+ carried craft) |
| `ship.habitation` | `HabitationSection` | `habitation.py` | staterooms, low_berths, common_area |
| `ship.systems`  | `SystemsSection`  | `systems.py`  | medical_bay, workshop, probe_drones, repair_drones |
| `ship.cargo`    | `CargoSection`    | `systems.py`  | cargo_holds |

> **Fuel boundary note:** Jump fuel is conceptually tied to the jump drive but
> appears in the Fuel spec section. Operation fuel and the fuel processor are
> tied to the power plant. The simplest rule: fuel volumes and their processor
> live in `FuelSection`; the jump drive and m-drive live in their own sections
> without owning fuel directly.

---

## Design rules

- Every section class is a frozen Pydantic model (same as `Hull` today).
- Every section class has a `_all_parts() -> list[ShipPart]` method that
  returns its parts in spec-display order.
- Sections that are always present (`hull`, `cargo`) are non-optional.
  Sections that may be absent are `Optional` and default to `None`.
- Where a section exactly maps to an existing module, the section class lives
  in that module (e.g. `WeaponsSection` in `weapons.py`, `ComputerSection` in
  `computer.py`).
- `Ship._all_parts()` becomes a simple concatenation of each section's
  `_all_parts()`.
- `build_spec()` iterates the same list and delegates per-section rendering
  to the section (or keeps the current logic — the primary gain is API
  organisation, not rendering refactor).

---

## Migration steps

1. **Move airlocks and aerofins into `Hull`.** They already belong to the hull
   section conceptually. `Hull._all_parts()` already exists; just extend it.

2. **Create `WeaponsSection`** in `weapons.py`:
   ```python
   class WeaponsSection(CeresModel):
       turrets: list[ShipTurret] = Field(default_factory=list)
       fixed_firmpoints: list[FixedFirmpoint] = Field(default_factory=list)
       missile_storage: MissileStorage | None = None
   ```
   Change `Ship.turrets`, `Ship.fixed_firmpoints`, `Ship.missile_storage` →
   `Ship.weapons: WeaponsSection | None = None`.

3. **Create `SensorsSection`** in `sensors.py`:
   ```python
   class SensorsSection(CeresModel):
       primary: ShipSensors = Field(default_factory=BasicSensors)
       countermeasures: CountermeasuresSuite | None = None
   ```
   Change `Ship.sensors` + `Ship.countermeasures` → `Ship.sensors: SensorsSection`.

4. **Create `ComputerSection`** in `computer.py`:
   ```python
   class ComputerSection(CeresModel):
       hardware: ShipComputer | None = None
       software: list[ShipSoftware] = Field(default_factory=list)
   ```
   Change `Ship.computer` + `Ship.software` → `Ship.computer: ComputerSection | None = None`.

5. **Create `HabitationSection`** in `habitation.py`:
   ```python
   class HabitationSection(CeresModel):
       staterooms: Staterooms | None = None
       low_berths: LowBerths | None = None
       common_area: CommonArea | None = None
   ```

6. **Create `SystemsSection`** in `systems.py`:
   ```python
   class SystemsSection(CeresModel):
       medical_bay: MedicalBay | None = None
       workshop: Workshop | None = None
       probe_drones: ProbeDrones | None = None
       repair_drones: RepairDrones | None = None
   ```

7. **Create `FuelSection`** in `drives.py`:
   ```python
   class FuelSection(CeresModel):
       jump_fuel: JumpFuel | None = None
       operation_fuel: OperationFuel | None = None
       scoops: FuelScoops | None = None
       processor: FuelProcessor | None = None
   ```

8. **Create `CommandSection`** in `bridge.py`:
   ```python
   class CommandSection(CeresModel):
       bridge: Bridge | None = None
       cockpit: Cockpit | None = None
   ```

9. **Create `JumpSection`** and **`PropulsionSection`** in `drives.py` (or keep
   drive fields flat — these sections each contain only one required part, so
   the gain is smaller. Defer until it feels necessary).

10. Update `build_spec()` to call each section's `_all_parts()`.

11. Update all tests. The construction API changes, so `build_suleiman()` etc.
    will need updating.

---

## Compatibility considerations

- Serialization: JSON keys change (e.g. `ship.sensors` becomes a nested object
  instead of a bare sensor instance). A migration pass or version bump is needed
  if serialized JSON is persisted anywhere.
- Existing tests that build `Ship(sensors=MilitarySensors(), ...)` will need
  to become `Ship(sensors=SensorsSection(primary=MilitarySensors()), ...)`.
  Consider a convenience shorthand or accept the verbosity as clearer intent.

---

## What to do first

The highest-value, lowest-risk first step is **`WeaponsSection`** — it has the
most fields currently on `Ship` and maps cleanly to `weapons.py` with no
ambiguity about what belongs there. Do this, verify tests pass, then continue
section by section.
