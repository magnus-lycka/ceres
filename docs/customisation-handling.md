====================================================== FAILURES =======================================================
_______________________________________ test_render_ship_pdf_delegates_to_spec ________________________________________

suleiman_spec = ShipSpec(ship_class='Suleiman', ship_type='Scout/Courier', tl=12, hull_points=40.0, _sections={<SpecSection.HULL: 'Hul...ntity=None), CrewRow(role='GUNNER', salary=2000, quantity=None)], passengers=[PassengerRow(kind='MIDDLE', quantity=2)])

    def test_render_ship_pdf_delegates_to_spec(suleiman_spec):
        pdf_from_ship = render_ship_pdf(build_suleiman())
        pdf_from_spec = render_ship_spec_pdf(suleiman_spec)
>       assert pdf_from_ship == pdf_from_spec
E       AssertionError: assert b'%PDF-1.7\n%...n84595\n%%EOF' == b'%PDF-1.7\n%...n84595\n%%EOF'
E         
E         At index 83239 diff: b'3' != b'4'
E         Use -v to get more diff

tests/stuart/test_tycho_pdf.py:33: AssertionError
=================================================== tests coverage ====================================================
__________________________________ coverage: platform darwin, python 3.14.0-final-0 ___________________________________
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
`EnergyEfficient`, `VeryHighYield`, `LimitedRange`, …) are frozen Pydantic models
describing one property.  Each carries `.advantage` and `.disadvantage` point
values — most contribute 1 point, but some contribute 2 (`VeryHighYield.advantage
= 2`, `OrbitalRange.disadvantage = 2`, `Accurate.advantage = 2`).  They also
carry cost/ton/power multipliers and optional info notes.

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

Each step: write failing tests → implement → all tests green → next step.
The serialization tests in `tests/tycho/test_serialization.py` must remain green
throughout — new customised parts must get roundtrip tests added there before or
alongside their feature tests.

### Step 1 — Rename `Customisation` → `Modification`

- Rename the class in `parts.py`; update all imports in `drives.py`, `weapons.py`,
  `sensors.py`, and test files that import `Customisation`.
- `LimitedRange` in `drives.py`: update `Customisation(...)` → `Modification(...)`.
  Instance name unchanged.
- No behaviour changes; all tests stay green.

### Step 2 — Define `Customisation` hierarchy in `parts.py`

Write tests first (`tests/tycho/test_customisation.py` or similar):

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

Implement the six subclasses and shared validation.  `CustomisationGrade` keeps
its enum values but loses its property methods (removed incrementally as parts
migrate).

### Step 3 — Simplify `CustomisableShipPart`

Write tests using a minimal concrete subclass:

- Part with `customisation=None` behaves identically to `ShipPart`.
- `build_notes()` appends the customisation note when set.
- `group_key` differs between parts with different customisations.
- `bind()` emits an error when a modification is not in `allowed_modifications`.

Implement the thin interface.  The existing `customisation_grade`,
`customisations` tuple, multiplier methods, and `validate_customisations` are
removed.  This intentionally breaks `MDrive`, `_FusionPlant`, `Barbette`, `Bay`,
`PointDefenseBattery` — resolved in the next steps.

### Step 4 — Migrate `MDrive` and `_FusionPlant`

Write failing tests using the new API first.  Then:

- Remove `budget`, `increased_size`, `size_reduction` from both.
- Remove grade/customisation derivation from `model_post_init`.
- Update `compute_tons` / `compute_cost` to read from `self.customisation`
  (falling back to `1.0` when `None`).
- `build_notes()` drops hand-written note; the base class emits it automatically.
- Set `allowed_modifications` class vars.
- Update `test_drives.py` and all ship test files.
- Add roundtrip tests to `test_serialization.py` covering a ship with a
  customised drive and power plant.

### Step 5 — Migrate `Barbette`, `Bay`, `PointDefenseBattery`

Same pattern as Step 4.

- Remove individual customisation fields.
- Set `allowed_modifications` class vars.
- Delete `_weapon_customisation_note()`.
- Update `test_weapons.py` and all ship tests.
- Add roundtrip tests for customised barbettes, bays, and PDB.

### Step 6 — Migrate `MountWeapon`

- Remove `very_high_yield`, `energy_efficient`.
- Add `customisation: CustomisationUnion | None = None` and `allowed_modifications`.
- Remove `customisation_note()` method.
- Update `_mounted_weapon_notes()` and `FixedMount.build_notes()` to read
  `weapon.customisation.note_text` instead.
- Update `test_ultralight_fighter.py`, `test_weapons.py`, and
  `test_serialization.py`.

### Step 7 — Remove `CustomisationGrade` property methods; keep enum values

Once no code reads `CustomisationGrade.ADVANCED.base_cost_multiplier` etc.,
delete those property methods.  The enum values (`ADVANCED`, `BUDGET`, …) are
kept permanently — they are the discriminator keys in JSON.

Remove `grade_for_advantages` and `grade_for_disadvantages` helpers if nothing
uses them.

---

## Affected files

| File | Change |
|------|--------|
| `src/tycho/parts.py` | Rename `Customisation`→`Modification`; add new `Customisation` hierarchy; simplify `CustomisableShipPart`; strip `CustomisationGrade` property methods in Step 7 |
| `src/tycho/drives.py` | Remove per-field customisation in `MDrive`, `_FusionPlant` |
| `src/tycho/weapons.py` | Remove per-field customisation in `Barbette`, `Bay`, `PDB`, `MountWeapon`; delete `_weapon_customisation_note` |
| `src/tycho/sensors.py` | Import rename only |
| `tests/tycho/test_customisation.py` | New file: unit tests for `Customisation` hierarchy |
| `tests/tycho/test_drives.py` | New construction API; note text assertions |
| `tests/tycho/test_weapons.py` | New construction API; note text assertions |
| `tests/tycho/test_serialization.py` | Roundtrip tests for each customised part type |
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
