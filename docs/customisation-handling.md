# Plan: Customisation handling

## Problem

Customisation grades (Budget, Advanced, Very Advanced, High Technology, …) are
modelled as `CustomisationGrade` enum values and the machinery to apply them
lives in `CustomisableShipPart`.  However, the parts that actually use
customisation — `MDrive`, `_FusionPlant`, `Barbette`, `Bay`,
`PointDefenseBattery`, and `MountWeapon` — all bypass that machinery by
accepting individual boolean/int fields (`budget`, `increased_size`,
`size_reduction`, `very_high_yield`, `energy_efficient`) and computing grade and
modification list in `model_post_init`.

This produces several concrete bugs and design problems:

- `Bay(size_reduction=3)` emits `"Advanced - Size Reduction × 3"` — but 3
  advantage points is High Technology, not Advanced.  The label is derived from
  advantage count, so it is wrong whenever a modification contributes more than
  one point (e.g. `VeryHighYield.advantage = 2`, `OrbitalRange.disadvantage = 2`).
- The caller never states which grade they intend, so the model cannot validate
  that the caller is self-consistent.  Grade is computed as an output when it
  should be declared as an input.
- Each part assembles its own customisation notes through ad-hoc functions
  (`_weapon_customisation_note`, inline `build_notes` logic) with no shared format.
- `MountWeapon` is not a `ShipPart` and has its own parallel mechanism with no
  shared validation.

Root cause: customisation flows backwards — properties → grade — instead of
grade → validated properties.

## Current status

The migration has now moved past the halfway state that originally motivated
this document.

Implemented:

- `Modification` is the renamed old property object type
- the new `Customisation` grade hierarchy is in place
- `CustomisableShipPart` accepts `customisation: CustomisationUnion | None`
- `MDrive` and `_FusionPlant` now read customisation directly
- `Barbette`, `Bay`, and `PointDefenseBattery` now read customisation directly
- `MountWeapon` now has `customisation` too, rather than its own boolean flags
- tests and ship builders now declare grade first, then modifications

This means the bad backwards pattern is gone from current construction code.
We no longer accept or test for things like:

- `Bay(size_reduction=3)`
- `MDrive7(budget=True, increased_size=True)`
- `MountWeapon(very_high_yield=True, energy_efficient=True)`

Those have been replaced with the intended declarative form:

- `Bay(customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction))`
- `MDrive7(customisation=Budget(IncreasedSize))`
- `MountWeapon(customisation=HighTechnology(VeryHighYield, EnergyEfficient))`

---

## What can be customised

Only the components listed in the *Customising Ships* chapter of High Guard have
Advantages or Disadvantages.  Not all `ShipPart` subclasses are customisable.

From the reference rules, customisable items are:

- **Jump Drive** — size reduction, energy efficient, early jump, decreased fuel,
  stealth jump (Adv); energy inefficient, late jump, increased size (Dis)
- **Manoeuvre Drive** — energy efficient, size reduction (Adv); energy
  inefficient, limited range, increased size, orbital range (Dis)
- **Reaction Drive** — fuel efficient (Adv); fuel inefficient (Dis)
- **Power Plant** — increased power, size reduction (Adv); energy inefficient,
  increased size (Dis)
- **Weapons and screens** — per weapon mounted in a turret or as a barbette/bay/
  point-defence battery (Adv: accurate, easy to repair, energy efficient, high
  yield, very high yield, intense focus, long range, resilient, size reduction;
  Dis: energy inefficient, inaccurate, increased size)

Everything else — bridges, sensors, computers, staterooms, cargo holds, etc. —
is not customisable.

---

## Proposed model

### `Modification` — rename of current `Customisation`

The existing `Customisation` instances (`SizeReduction`, `IncreasedSize`,
`EnergyEfficient`, and domain-specific ones such as `VeryHighYield` or
`LimitedRange`) are frozen Pydantic models describing one property. Each
carries `.advantage` and `.disadvantage` point values — most contribute 1
point, but some contribute 2 (`VeryHighYield.advantage = 2`,
`OrbitalRange.disadvantage = 2`, `Accurate.advantage = 2`). They also carry
cost/ton/power multipliers and optional info notes.

Rename the class `Modification` and update all import sites.  Instance names and
behaviour are unchanged.

### `CustomisationGrade` — retained as JSON discriminator

`CustomisationGrade` remains a StrEnum.  After the migration its only job is to
act as the Pydantic discriminator on the `customisation` field, so that
`model_dump_json` / `model_validate_json` round-trips resolve the correct
concrete `Customisation` subclass.  All per-grade constants (cost multiplier, TL
delta, etc.) move to `ClassVar` attributes on the subclasses; the enum's property
methods are removed.

### New `Customisation` hierarchy

```python
class Customisation(CeresModel):
    """Base class for a declared customisation grade + its modifications."""
    grade: CustomisationGrade          # Literal in each subclass; acts as discriminator
    modifications: tuple[Modification, ...]
    model_config = {'frozen': True}

    # Each subclass defines these ClassVars:
    #   _required_advantages:    ClassVar[int]
    #   _required_disadvantages: ClassVar[int]
    #   _cost_multiplier:        ClassVar[float]
    #   _tons_multiplier:        ClassVar[float]
    #   _tl_delta:               ClassVar[int]
    #   _display_name:           ClassVar[str]

    def __init__(self, *modifications: Modification, **kwargs):
        super().__init__(modifications=modifications, **kwargs)

    def model_post_init(self, __context):
        # Validation via self.error(), not raise:
        total_adv = sum(m.advantage for m in self.modifications)
        total_dis = sum(m.disadvantage for m in self.modifications)
        if total_adv != self._required_advantages or total_dis != self._required_disadvantages:
            self.error(
                f'{self.__class__.__name__} requires '
                f'{self._required_advantages} advantage point(s) and '
                f'{self._required_disadvantages} disadvantage point(s), '
                f'got {total_adv} and {total_dis}'
            )

    @property
    def note_text(self) -> str:
        """e.g. 'High Technology: Size Reduction × 3, Energy Efficient'"""
        counts: dict[str, int] = {}
        for m in self.modifications:
            counts[m.name] = counts.get(m.name, 0) + 1
        parts = [f'{name} × {n}' if n > 1 else name for name, n in counts.items()]
        return f'{self._display_name}: {", ".join(parts)}'


class EarlyPrototype(Customisation):
    grade: Literal[CustomisationGrade.EARLY_PROTOTYPE] = CustomisationGrade.EARLY_PROTOTYPE
    _required_advantages    = 0;  _required_disadvantages = 2
    _cost_multiplier        = 11.0;  _tons_multiplier = 2.0
    _tl_delta               = -2;  _display_name = 'Early Prototype'

# … Prototype, Budget, Advanced, VeryAdvanced, HighTechnology follow the same pattern
```

The union type on parts that accept customisation:

```python
CustomisationUnion = Annotated[
    EarlyPrototype | Prototype | Budget | Advanced | VeryAdvanced | HighTechnology,
    Field(discriminator='grade'),
]
```

### `CustomisableShipPart` — simplified, not removed

`CustomisableShipPart` is kept as the thin base for the `ShipPart` subclasses
that support customisation.  After the migration its only responsibilities are:

- Declare `customisation: CustomisationUnion | None = None`
- Declare `allowed_modifications: ClassVar[frozenset[str]] = frozenset()`,
  overridden in each subclass with the names of permitted `Modification` instances
- Override `build_notes()` to append `Note(INFO, customisation.note_text)` when
  customisation is set (after `super().build_notes()`)
- Override `group_key` to include grade and modification names so parts with
  different customisations are not collapsed into the same spec row
- Validate on `bind()` that every modification in `customisation.modifications`
  is in `allowed_modifications`, emitting an error note if not

All existing multiplier-computation methods and `validate_customisations` are
deleted; that logic now lives in `Customisation` itself.

`MountWeapon` is a `CeresModel`, not a `ShipPart`.  It receives the same
`customisation` field and `allowed_modifications` directly, without inheriting
from `CustomisableShipPart`.

### API before / after

```python
# before
Bay(size='small', weapon='missile', size_reduction=3, armoured_bulkhead=True)
MDrive7(budget=True, increased_size=True, armoured_bulkhead=True)
FusionPlantTL12(output=482, budget=True, increased_size=True)
Barbette(weapon='particle', very_high_yield=True)
PointDefenseBattery(kind='laser', rating=2, energy_efficient=True)
MountWeapon(weapon='pulse_laser', very_high_yield=True, energy_efficient=True)

# after
Bay(size='small', weapon='missile', armoured_bulkhead=True,
    customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction))
MDrive7(armoured_bulkhead=True,
    customisation=Budget(IncreasedSize))
FusionPlantTL12(output=482,
    customisation=Budget(IncreasedSize))
Barbette(weapon='particle',
    customisation=VeryAdvanced(VeryHighYield))
PointDefenseBattery(kind='laser', rating=2,
    customisation=Advanced(EnergyEfficient))
MountWeapon(weapon='pulse_laser',
    customisation=HighTechnology(VeryHighYield, EnergyEfficient))
```

A triple turret can have three independently-customised weapons:

```python
Turret(size='triple', weapons=[
    MountWeapon(weapon='pulse_laser', customisation=Advanced(EnergyEfficient)),
    MountWeapon(weapon='beam_laser'),
    MountWeapon(weapon='sandcaster', customisation=Budget(IncreasedSize)),
])
```

### Note format

All customisation notes use the form `"{Grade}: {Mod}, {Mod} × N"`.

Examples:
- `Budget(IncreasedSize)` → `"Budget: Increased Size"`
- `Advanced(SizeReduction)` → `"Advanced: Size Reduction"`
- `HighTechnology(SizeReduction, SizeReduction, SizeReduction)` → `"High Technology: Size Reduction × 3"`
- `HighTechnology(VeryHighYield, EnergyEfficient)` → `"High Technology: Very High Yield, Energy Efficient"`

This replaces `_weapon_customisation_note()` and all inline note-building in
`drives.py`.

---

## Migration steps (TDD order)

This section started as a forward plan.  It now functions mostly as a record of
the migration order and a checklist for cleanup.  Steps 1–6 are complete; Step
7 remains.

### Step 1 — Rename `Customisation` → `Modification` [done]

Completed.

### Step 2 — Define `Customisation` hierarchy in `parts.py` [done]

Write tests first (`tests/make/ship/test_customisation.py` or similar):

- `Advanced(SizeReduction)` is valid; `.note_text` → `'Advanced: Size Reduction'`.
- `HighTechnology(SizeReduction, SizeReduction, SizeReduction)` is valid;
  `.note_text` → `'High Technology: Size Reduction × 3'`.
- `HighTechnology(VeryHighYield, EnergyEfficient)` is valid because
  `VeryHighYield.advantage = 2` + `EnergyEfficient.advantage = 1` = 3;
  `.note_text` → `'High Technology: Very High Yield, Energy Efficient'`.
- `Advanced(SizeReduction, SizeReduction)` has an error note (2 points ≠ 1 required).
- `Budget(SizeReduction)` has an error note (advantage ≠ 0, disadvantage ≠ 1).
- Each subclass has the correct `_cost_multiplier`, `_tl_delta`, `_tons_multiplier`.
- A `Customisation` instance roundtrips through `model_dump_json` /
  `model_validate_json` and resolves the same concrete subclass.

Completed.

### Step 3 — Simplify `CustomisableShipPart` [done]

Write tests using a minimal concrete subclass:

- Part with `customisation=None` behaves identically to `ShipPart`.
- `build_notes()` appends the customisation note when set.
- `group_key` differs between parts with different customisations.
- `bind()` emits an error when a modification is not in `allowed_modifications`.

Completed. `CustomisableShipPart` now exposes the thin interface described
above.  The old backwards construction API is gone from the tests and current
part construction code.

### Step 4 — Migrate `MDrive` and `_FusionPlant` [done]

Write failing tests using the new API first.  Then:

Completed.

### Step 5 — Migrate `Barbette`, `Bay`, `PointDefenseBattery` [done]

Same pattern as Step 4.

Completed.

### Step 6 — Migrate `MountWeapon` [done]

Completed.

### Step 7 — Remove `CustomisationGrade` property methods; keep enum values [done]

Done.  The old `CustomisationGrade` property helpers are removed.  The enum
values (`ADVANCED`, `BUDGET`, …) remain permanently as the discriminator keys in
JSON.

The old `grade_for_advantages` and `grade_for_disadvantages` helpers are also
gone.

---

## Affected files

| File | Change |
|------|--------|
| `src/ceres/make/ship/parts.py` | Rename `Customisation`→`Modification`; add new `Customisation` hierarchy; simplify `CustomisableShipPart`; strip old `CustomisationGrade` property methods |
| `src/ceres/make/ship/drives.py` | Remove per-field customisation in `MDrive`, `_FusionPlant` |
| `src/ceres/make/ship/weapons.py` | Remove per-field customisation in `Barbette`, `Bay`, `PDB`, `MountWeapon`; delete `_weapon_customisation_note` |
| `src/ceres/make/ship/sensors.py` | Import rename only |
| `tests/make/ship/test_customisation.py` | New file: unit tests for `Customisation` hierarchy |
| `tests/make/ship/test_drives.py` | New construction API; note text assertions |
| `tests/make/ship/test_weapons.py` | New construction API; note text assertions |
| `tests/make/ship/test_serialization.py` | Roundtrip tests for each customised part type |
| `tests/ships/test_dragon.py` | New construction API; note format `Grade: Mod` |
| `tests/ships/test_revised_dragon.py` | Same |
| `tests/ships/test_alt_dragon.py` | Same |
| `tests/ships/test_revised_beowulf.py` | Same |
| `tests/ships/test_ultralight_fighter.py` | Same |

---

## What does not change

- All `Modification` singletons keep their names, `.advantage`/`.disadvantage`
  values, and behaviour.
- All tonnage, cost, and TL arithmetic is identical; only the source of inputs
  changes.
- The spec/HTML/PDF rendering layer is unaffected except that note text strings
  change format (e.g. `"Advanced - Size Reduction × 3"` →
  `"High Technology: Size Reduction × 3"`).
