# Plan: Remove Career YAML Files

## Long-term goal

A long-term goal for the character subsystem is to eliminate all semantically
meaningful strings from the code. Strings are for communicating with the user —
display text, labels, descriptions. They are never used to identify or look up
skills, characteristics, careers, assignments, effects, or any other domain
concept. All such identification is done through Python objects: enums, class
references, instances, or typed attributes.

This work package moves a significant way toward that goal by replacing the YAML
files and the string-based skill/characteristic fields they required. It does
not get all the way there. The remaining work is described at the end of this
document.

---

## This work package: remove career YAML

Replace the 13 `*.yaml` career files with pure Python. Each career module
directly constructs a `CareerData` using real `AnySkill` instances and `Chars`
enum values instead of strings that need parsing. The result reads like the
rules pages.

Before:

```yaml
skill_tables:
  personal_development:
    1: STR
    2: DEX
    3: END
    4: Gambler
    5: Medic
    6: Melee
```

After:

```python
from ceres.character.skills import Gambler, Medic, Melee

personal_development=SkillTable([Chars.STR, Chars.DEX, Chars.END, Gambler(), Medic(), Melee()])
```

---

## Phase 1 — Data model changes (`career_data.py`)

### 1a. `CareerSkillTables` — replace `dict[str, SkillTable]`

Replace the open-ended `dict[str, SkillTable]` with a typed struct that names
every table position explicitly:

```python
class CareerSkillTables(CeresModel):
    personal_development: SkillTable
    service_skills: SkillTable
    advanced_education: SkillTable | None = None
    officer: SkillTable | None = None          # commissioned ranks only
    assignment1: SkillTable
    assignment2: SkillTable
    assignment3: SkillTable
```

`CareerData.skill_tables` changes from `dict[str, SkillTable]` to
`CareerSkillTables`. The assignment slots are positional because assignment
names vary across careers; the human-readable names live in `AssignmentData`.

### 1b. `SkillTable` entries — `AnySkill | Chars | list[AnySkill]`

A skill table is a list of six entries (index 0 = die roll 1):

```python
type SkillTableEntry = AnySkill | Chars | list[AnySkill]

class SkillTable(CeresModel):
    entries: list[SkillTableEntry]             # always length 6
    min_edu: int = 0                           # advanced_education gate
```

- `AnySkill` instance → gain that skill at the instance's level (default 0)
- `Chars` value → +1 to that characteristic
- `list[AnySkill]` → pick one from the list

Drop the existing `SkillTableEntry` model (which had separate `skill`,
`characteristic`, `choices`, and `level` fields and required string parsing).

### 1c. Effect fields — `AnySkill` instead of `str`

All effect models that currently store skill or characteristic names as strings
change to real objects:

| Model | Field | Before | After |
|---|---|---|---|
| `GainSkillEffect` | `skill` | `str` | `AnySkill` |
| `SkillChoiceEffect` | `choices` | `list[str]` | `list[AnySkill]` |
| `DecreaseCharacteristicEffect` | `characteristic` | `str` | `Chars` |
| `RankBonus` | `skill` | `str \| None` | `AnySkill \| None` |
| `RankBonus` | `characteristic` | `str \| None` | `Chars \| None` |
| `RankBonus` | `choices` | `list[str]` | `list[AnySkill]` |

Any downstream code that resolved these strings (e.g. `skill_from_str`) is
simplified to use the value directly.

---

## Phase 2 — Loader changes (`loader.py`)

Replace YAML-parsing with Python-module discovery:

1. Scan `careers/*.py`, skipping `__init__`, `loader`, `career_data`, `common`.
2. Import each module and read `CAREER_DATA: CareerData`.
3. Read `EFFECT_HANDLERS`, `SKILL_ROLL_HANDLERS`, `CHOICE_HANDLERS` as before —
   they continue to live alongside `CAREER_DATA` in the same file.
4. Delete `_load_career_file()`, all PyYAML imports, and the Pydantic
   `model_validator` logic that parsed strings into objects.

The public API of `load_careers()` and `selectable_careers()` is unchanged;
callers need no updates.

---

## Phase 3 — Migrate careers one at a time

Merge each `career.yaml` + `career.py` pair into a single `career.py` that
exports `CAREER_DATA`. Migrate in this order (simplest → most custom logic):

1. `army`
2. `navy`, `marines`, `scout`
3. `agent`, `merchant`, `citizen`
4. `entertainer`, `noble`, `rogue`, `drifter`
5. `scholar`
6. `prisoner` (last — `PrisonerCareerData` subclass, parole system)

Run `uv run pytest` after each career before moving on.

### Template for a migrated career module

```python
# army.py
from ceres.character.characteristics import Chars
from ceres.character.skills import (
    Athletics, GunCombat, Gambler, HeavyWeapons,
    Leadership, Medic, Melee, Recon, Stealth, Survival,
)
from ceres.character.careers.career_data import (
    AssignmentData, CareerData, CareerSkillTables, CharCheck,
    GainSkillEffect, MishapEntry, RankBonus, RankEntry, SkillTable,
    TermEventEntry,
)

CAREER_DATA = CareerData(
    name="Army",
    qualification=CharCheck(characteristic=Chars.END, target=5),
    skill_tables=CareerSkillTables(
        personal_development=SkillTable([
            Chars.STR, Chars.DEX, Chars.END, Gambler(), Medic(), Melee(),
        ]),
        service_skills=SkillTable([
            Athletics(), GunCombat(), Recon(), Melee(), HeavyWeapons(), Survival(),
        ]),
        advanced_education=SkillTable([...], min_edu=8),
        assignment1=SkillTable([...]),
        assignment2=SkillTable([...]),
        assignment3=SkillTable([...]),
    ),
    assignments=[
        AssignmentData(
            name="Support",
            survival=CharCheck(Chars.END, 5),
            advancement=CharCheck(Chars.EDU, 7),
        ),
        AssignmentData(
            name="Infantry",
            survival=CharCheck(Chars.STR, 6),
            advancement=CharCheck(Chars.EDU, 6),
        ),
        AssignmentData(
            name="Cavalry",
            survival=CharCheck(Chars.INT, 7),
            advancement=CharCheck(Chars.INT, 6),
        ),
    ],
    ranks={
        1: RankEntry(title="Lance Corporal", bonus=RankBonus(skill=GunCombat())),
        ...
    },
    events={
        2: TermEventEntry(text="...", effects=[...]),
        ...
    },
    mishaps={
        1: MishapEntry(text="...", effects=[...]),
        ...
    },
)

# Custom handlers (unchanged from current army.py, if any)
EFFECT_HANDLERS: dict = {}
```

---

## Phase 4 — Cleanup

- Delete all 13 `*.yaml` files.
- Remove PyYAML from `pyproject.toml` if it is not used outside careers.
- Remove remaining YAML-parsing helpers from `loader.py`.
- Run the full suite: `uv run pytest --all-tests`.

---

## Testing strategy

Existing tests in `tests/character/test_careers.py` exercise behaviour through
the `CareerData` API and should continue to pass without changes. The
`TestCoreCareerCoverage` class verifies loadability and will serve as the gate
for each migration step. No new test infrastructure is needed.

---

## What remains after this work package

The following semantic string uses are still present after the career YAML
migration is complete and need separate work packages to eliminate.

### Precareers still use string-based skill tables

`precareer_data.py` and the individual precareer modules (`colonial_upbringing`,
`military_academy`, `spacer_community`, etc.) call `skill_from_str()` and store
skill names as strings. These should be migrated the same way as careers:
replace YAML/string-based precareer tables with Python modules that carry
`AnySkill` instances directly.

### `skill_from_str` / `skill_class_by_name` remain in `events.py`

`events.py` calls `skill_from_str()` and `skill_class_by_name()` in many
places to resolve skill names carried on effect objects. Once all effect models
hold `AnySkill` instances (Phase 1 of this plan) and precareers are migrated,
these call sites go away and both functions can be deleted.

### `skill_level(name: str)` in `CharacterSummary`

`state.py` exposes `skill_level(name: str | type[Skill])`. The `str` overload
should be removed once no caller needs string-based lookup. The method should
accept only `type[Skill]`.

### Dispatch effects identified by string

Custom event and mishap effects such as `agent_mishap_2_choice` are currently
dispatched via string keys in `EFFECT_HANDLERS` dicts. The right end-state is
to replace `CareerDispatchEffect` with proper subclasses, each with an
`apply(projection, ...)` method. The effect objects themselves carry the logic,
removing the need for string-keyed dispatch tables entirely.

### Career and assignment identification by string in `CharacterSummary`

`CharacterSummary.current_career` and `current_assignment` are `str | None`.
They are used for two purposes: display (`f'Joined {after.current_career}'`)
and identity checks (`career.name == 'Prisoner'`). Display use is acceptable.
Identity checks should use `isinstance` or a typed property instead of comparing
name strings. The `'Prisoner'` check in `events.py:750` is a concrete example.

After moving to `CareerSkillTables` with `assignment1/2/3`, the assignment can
also be identified by index (1, 2, or 3) rather than by the human-readable name
string, which is only needed for display.

### Sophont lookup by name

`sophonts/__init__.py` finds sophonts by string name. Sophonts should be
referenced as typed objects or an enum rather than matched by string.
