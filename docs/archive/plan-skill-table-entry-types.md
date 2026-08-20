# Plan: Skill Table Entry Types

## STATUS: COMPLETE (2026-07-05)

All six steps implemented. The final design differs from the sketches below in
one significant way: specialization restrictions are expressed with typed
`SpecRef` references (`Skill(Seafarer, specs=(Seafarer.personal, Seafarer.sail))`,
via a metaclass that makes class-level Level-field access return a `SpecRef`)
rather than string specializations or instance-holding entry types — the
interim `SpecificSkill` and `InstanceChoice` types were introduced and then
removed in favour of the `specs` parameter on `Skill` and `SkillChoice`.
Career skill-table cells carry no levels (they are increments per the book);
levels appear only in rank bonuses. The legacy `psionics_data.Psi` RootModel
is deleted; psion rank-bonus talents use the new `Psi` entry with inline
acquisition-roll resolution on `PendingRankBonusChoice`. Follow-on OOP
cleanups are tracked in GitHub issues #53 and #54.

## Background

### The Problem

Skill table entries are currently encoded as a union type:

```python
type SkillTableItem = AnySkill | Psi | Chars
type SkillTableEntry = SkillTableItem | tuple[SkillTableItem, ...]
```

All routing and application logic lives in free functions that dispatch on type
with `isinstance` chains: `_apply_skill_table_entry()`,
`_skill_table_item_choices()`, `_queue_skill_table_choice()` in
`career_events.py`, and `_training_pending_choices()`,
`_training_selectable_skills()`, `_training_option_name()`,
`_training_option_is_unknown()`, `_unknown_training_skills()` in
`career_data.py`.

Entry types are dumb data; all behaviour is external. Adding a new entry
type (or changing how an existing one applies) requires touching multiple
dispatch sites. The entry types do not know how to apply themselves. The
service-skills Psi routing bug (see
[archive/plan-psionic-skill-table.md](archive/plan-psionic-skill-table.md))
is a direct consequence: `Psion.skill_table_option_is_available` was abused
as a routing switch because the entry could not carry its own semantics.

### The Fix

Replace the current union with 5 explicit entry types, each carrying its own
`apply()` method. Free-function isinstance dispatch is eliminated; the entry
itself knows what to do.

---

## Stub Definitions

New file: `src/ceres/character/domain/career/skill_table_entries.py`

These stubs pin down names, fields, and discriminators. Bodies are elided;
the exact signatures of helper methods will emerge test by test.

```python
class SkillTableApplyContext:
    """Carries the event, pending-id allocation, and application mode.

    One event can spawn several pendings (basic training grant-all queues one
    PendingInitialTrainingChoice per multi-option row, ids (event_id, 0),
    (event_id, 1), ...). Entries must never improvise (event.id, 0); they ask
    the context for the next id.
    """

    event: Event
    level: int | None = None  # mode: None = increment; 0 = grant base at 0; N = set-if-lower

    def next_pending_id(self) -> tuple[int, int]: ...  # allocates (event.id, idx), idx increments


class SkillTableEntryBase(CeresModel):
    """A cell in a career skill table. Knows how to apply itself to a character."""

    def apply(self, projection: CharacterProjection, ctx: SkillTableApplyContext) -> None:
        """Apply this entry: change state directly or queue a pending input."""
        raise NotImplementedError

    def label(self) -> str:
        """Display name for choice options and instructions."""
        raise NotImplementedError


class Char(SkillTableEntryBase):
    kind: Literal['char'] = 'char'
    characteristic: Chars

    def __init__(self, characteristic: Chars, **kwargs) -> None:
        super().__init__(characteristic=characteristic, **kwargs)


class Skill(SkillTableEntryBase):
    kind: Literal['skill'] = 'skill'
    skill: type[AnySkill]  # serialized as the skill's kind string
    level: int | None = None  # None = increment; int = set-if-lower

    def __init__(self, skill: type[AnySkill], level: int | None = None, **kwargs) -> None:
        super().__init__(skill=skill, level=level, **kwargs)


class SkillChoice(SkillTableEntryBase):
    kind: Literal['skill_choice'] = 'skill_choice'
    skills: UnionType | type[AnySkill]  # Drive | VaccSuit, or a broad alias like Sciences
    level: int | None = None

    def __init__(self, skills: UnionType | type[AnySkill], level: int | None = None, **kwargs) -> None:
        super().__init__(skills=skills, level=level, **kwargs)


class Psi(SkillTableEntryBase):
    kind: Literal['psi'] = 'psi'
    talent: PsionicTalentSkillClass
    level: int | None = None
    allow_acquisition: bool = False

    def __init__(self, talent: PsionicTalentSkillClass, level: int | None = None, **kwargs) -> None:
        super().__init__(talent=talent, level=level, **kwargs)


class PsiChoice(SkillTableEntryBase):
    kind: Literal['psi_choice'] = 'psi_choice'
    talents: UnionType  # Telepathy | Clairvoyance | ...
    level: int | None = None
    allow_acquisition: bool = False

    def __init__(self, talents: UnionType, level: int | None = None, **kwargs) -> None:
        super().__init__(talents=talents, level=level, **kwargs)


type SkillTableItem = Annotated[Char | Skill | SkillChoice | Psi | PsiChoice, Field(discriminator='kind')]
```

Notes on the stubs:

- **Positional constructors.** Pydantic models are keyword-only by default;
  the small `__init__` overrides give the table-definition ergonomics the
  design calls for: `Char(Chars.STR)`, `Skill(Admin)`, `Psi(Telepathy,
  allow_acquisition=True)`.
- **`kind` discriminators** follow the house style used by events, skills,
  and pendings, so the union serializes the same way everything else does.
- **`type[AnySkill]` serialization.** A `type` field is not natively
  Pydantic-serializable. Add a reusable annotated type (BeforeValidator /
  PlainSerializer pair) that maps a skill class to/from its `kind` string.
  This is needed because concrete entries cross the web form boundary (see
  Boundaries below).
- **`UnionType` fields** never need serialization: tables are `ClassVar`
  data, and choice entries are expanded to concrete `Skill`/`Psi` entries
  *before* anything is queued or rendered (see Boundaries). Mark them with
  `arbitrary_types_allowed` and exclude from serialization, or assert they
  never reach a serialization path.
- **Name collision.** `Skill` (entry) collides with `skills.Skill` (the
  skill base class), and `Psi` replaces the current `psionics_data.Psi`.
  Modules that need both use qualified or aliased imports
  (`from ... import skill_table_entries as ste`, or
  `from ...skills import Skill as SkillModel`). Career table files mostly
  need only the entry types plus skill classes, which do not collide.
  If this gets ugly in practice, renaming the entry (e.g. `GainSkill`) is a
  cheap decision to revisit at Step 1 — record the outcome here.
  **Step 1 decision:** Class names stay as planned (`Char`, `Skill`, etc.).
  Discriminator values are prefixed `ste_` to avoid collisions with the
  discriminator-literal audit (which scans HTML templates by substring, so
  short values like `'char'` and `'skill'` collide with Jinja2 variables and
  template prose). Discriminators: `'ste_char'`, `'ste_skill'`,
  `'ste_skill_choice'`, `'ste_psi'`, `'ste_psi_choice'`.
- **Level: data vs mode.** `level` appears both on entries (table data, e.g.
  a rank bonus granted at level 1) and on the context (application mode, e.g.
  basic training grants everything at level 0). Rule: `ctx.level` overrides
  `entry.level` when set. Decide the exact precedence in Step 2 tests and
  record it here.

### Union types for choices

In Python 3.10+, `Drive | VaccSuit` is a runtime `types.UnionType` value, and
broad skill aliases (`Sciences`, `Languages`) are already unions. This is more
natural at the table-definition site than a tuple of types.

Expansion is centralized in two planned, tested helpers in
`skill_table_entries.py`:

```python
def expand_skill_classes(skills: UnionType | type[AnySkill]) -> tuple[type[AnySkill], ...]: ...
def expand_talent_classes(talents: UnionType) -> tuple[PsionicTalentSkillClass, ...]: ...
```

These own the `get_args()` logic, including unwrapping `Annotated[...]`
aliases if one sneaks in. Table data should use raw runtime unions
(`Languages`, `Sciences`, `Drive | VaccSuit`), not `Annotated` Pydantic
aliases like `AnySkill` — the helpers validate and fail loudly on anything
they cannot expand. Choice expansion is thereby tested once, not per entry
type.

---

## Semantics per Type

### `Char`

`apply()` adds +1 to the characteristic. Replaces bare `Chars.STR` in table
data. (Uses the `Chars` enum for now;
[plan-characteristic-type.md](plan-characteristic-type.md) may later replace
it with a `Characteristic` class — `Char` then wraps that instead.)

### `Skill`

`apply()` is mode-sensitive via `ctx.level` — specialization choice is **not**
universal:

- **Level 0 (basic training):** grant the bare base skill at level 0, no
  specialization choice — even for multi-specialization skills. This is the
  current, deliberate behaviour (`build_skill_select_options` short-circuits
  at `level == 0` in `skill_events.py`, and `_apply_basic_training` grants
  `type(entry)()` for specific-specialty entries). Changing it would change
  basic-training behaviour, which this migration must not do.
- **Increment mode (`level` is `None`, normal skill-table roll):** if the
  skill class has multiple specialization fields and none is implied, queue a
  specialization choice (current `_skill_table_item_choices` behaviour);
  otherwise increment (`projection.increment_skill` semantics).
- **Set mode (`level` = N > 0, e.g. rank bonus):** grant at level N if that
  improves the character (`grant_skill` semantics), with specialization
  choice where applicable.

### `SkillChoice`

Disambiguation only. `apply()` expands the union via `expand_skill_classes()`
into concrete `Skill` entries and queues a `PendingSkillTableChoice` whose
options are those entries. It never touches character state itself.

### `Psi`

`apply()` handles three cases:

1. Character has no PSI → `projection.not_gained(...)`.
2. Character possesses the talent → increment talent level.
3. Character has PSI but not this talent:
   - `allow_acquisition=True` → queue a talent acquisition attempt
     (`PendingPsionicInstituteTraining` with the talent's learning DM and
     cumulative penalty).
   - `allow_acquisition=False` → `projection.not_gained(...)`.

`allow_acquisition=True` is set wherever the rules say "you may attempt to
learn this talent": the Psion service skills table, pre-career institute
training. The entry encodes the intent; `apply()` does not need to know which
table it came from. This deletes `skill_table_option_is_available()` — both
the `CareerData` base method and the Psion override — whose only real job was
smuggling this information into the routing.

### `PsiChoice`

Disambiguation only. `apply()` expands the union into concrete `Psi` entries
(each carrying the same `allow_acquisition` flag) and queues the choice
pending. Replaces the `_TALENTS` tuple for "Any Talent" rows (Psion service
skills 6, Zhodani careers).

---

## Boundaries

Who does what after this plan:

```text
skill_table_entries.py   entry types; all per-entry semantics (apply, label)
career_data.py           SkillTable, CareerSkillTables, table lookup,
                         available_tables(); basic-training orchestration
                         (which entries a term offers) — but per-entry
                         behaviour is delegated to the entry
career_events.py         event handlers and pendings: SkillTableHandler,
                         _PendingSkillOrPsiChoice hierarchy, form I/O
```

### `SkillTableHandler.apply()` (career_events.py)

Keeps: table lookup, EDU gate, roll validation. Loses: the tuple branch, the
`_skill_table_item_choices` call, the `skill_table_option_is_available`
filtering. Becomes:

```python
entry = table.entries[self.roll - 1]
entry.apply(projection, SkillTableApplyContext(event=event))
```

### `_PendingSkillOrPsiChoice` and subclasses (career_events.py)

Remain the web/pending boundary: `input_specs()`, `event_from_form()`, option
rendering. Their `options` hold **concrete** entries only (`Skill`, `Psi` —
never `SkillChoice`/`PsiChoice`/`Char`), because the XChoice types expand
unions before queueing. The form round-trip (options serialized into select
values, parsed back in `event_from_form`) is why concrete entries must be
JSON-serializable.

**Event shape.** `event_from_form()` currently produces two different
handlers depending on what was parsed: `SkillChoiceHandler(skill=...)` or
`PsionicTalentTrainingHandler(talent=..., roll=...)`. With concrete entries
as options, replace both with a single handler:

```python
class SkillTableEntryChosenHandler(EventHandlerBase):
    kind: Literal['skill_table_entry_chosen'] = 'skill_table_entry_chosen'
    entry: SkillTableItem  # the chosen concrete Skill or Psi entry
    roll: int | None = None  # psi acquisition roll (2D), when required

    def apply(self, projection, event, fulfilled_pending=None) -> None:
        # resolve pending, then: self.entry.apply(projection, ctx)
        ...
```

The form value serializes the concrete entry (possible because entries are
discriminated Pydantic models); `event_from_form()` parses it back and wraps
it. Alpha status: the old handlers are deleted when no producer remains, no
compatibility kept.

`on_skill_chosen` / `on_psi_chosen` shrink: applying the chosen entry is the
handler's job (`entry.apply(...)`), not the pending's. What remains of the
hooks is *continuation* only (rank-bonus `_continue`, initial-training
level-0 mode). Whether they survive as hooks or become explicit fields on the
pending (e.g. `continue_career_progress`) is decided when we get there — the
split between "apply the entry" and "continue the flow" must end up explicit.

### `CareerData` (career_data.py)

Keeps `skill_tables`, `skill_table(name)`, `available_tables()` and the
basic-training flow (deciding *which* table rows a new recruit trains from).
Loses `skill_table_option_is_available()` and the `_training_*` isinstance
helpers — basic training asks entries for their labels/options instead.

### Deleted

- `_apply_skill_table_entry()`, `_skill_table_item_choices()`,
  `_queue_skill_table_choice()` (career_events.py)
- `_training_pending_choices()`, `_training_selectable_skills()`,
  `_training_option_name()`, `_training_option_is_unknown()`,
  `_unknown_training_skills()` (career_data.py)
- `skill_table_option_is_available()` base + Psion override
- `Psi` RootModel in `psionics_data.py` (`Telepathy` etc. stay — they are
  domain skill classes, not table-entry types)
- The `tuple[SkillTableItem, ...]` branch and the `SkillTableEntry` alias

---

## Migration: Table Data

| Before | After |
| ------ | ----- |
| `Chars.STR` | `Char(Chars.STR)` |
| `Admin()` | `Skill(Admin)` |
| `Electronics()` | `Skill(Electronics)` |
| `(Admin(), Steward())` | `SkillChoice(Admin \| Steward)` |
| `skill_instances(LanguageSkill)` | `SkillChoice(Languages)` |
| `Psi(Telepathy())` on service skills | `Psi(Telepathy, allow_acquisition=True)` |
| `Psi(Telepathy())` elsewhere | `Psi(Telepathy)` |
| `_TALENTS` tuple | `PsiChoice(Telepathy \| ... \| Teleportation, allow_acquisition=True)` |

All career files that define `skill_tables` need updating.

---

## Incremental Strategy: Keeping the Suite Green

Old and new encodings coexist during migration. Two `Psi` classes exist
during this window (`psionics_data.Psi` RootModel and the new entry type), so
naming discipline is mandatory: modules touching both import the legacy one
as `LegacyPsi` (`from ...psionics_data import Psi as LegacyPsi`) and the new
types qualified (`from ... import skill_table_entries as ste`; `ste.Psi`).
Never have a bare `Psi` ambiguous in a bridge module — a TDD failure must
mean behaviour, not import confusion.

The bridge:

```python
type SkillTableItem = AnySkill | LegacyPsi | Chars | SkillTableEntryBase  # transitional
```

and at the top of each legacy dispatch site:

```python
if isinstance(entry, SkillTableEntryBase):
    entry.apply(projection, ctx)
    return
# ... legacy isinstance chain unchanged ...
```

This lets us migrate **one entry type at a time, one career table at a
time**, with the full suite green after every step. Career rule tests
(`CharacterDriver`-based) must not change at all during migration — observable
career behaviour is identical. If a driver test breaks, the migration step
changed behaviour and must be fixed before proceeding.

The one *intended* behaviour change is the Psion service-skills fix
(possessed talents increment, unlearned talents trigger acquisition — today
both silently no-op). Write those driver tests red first; they go green when
the Psion tables migrate.

### Step 1: Context, base class + `Char`

- TDD `SkillTableApplyContext`: `next_pending_id()` allocates
  `(event.id, 0)`, `(event.id, 1)`, ... — this is the contract basic
  training's multi-pending case relies on.
- TDD the stubs: `SkillTableEntryBase`, `Char`, discriminated serialization
  round-trip.
- TDD `Char.apply()`: increments the characteristic.
- Add the `isinstance(entry, SkillTableEntryBase)` bridge to
  `SkillTableHandler.apply()` and the training path; the bridge constructs
  the context (normal roll: `level=None`; basic training: `level=0`).
- Migrate `personal_development` tables (all pure `Chars` rows today —
  smallest possible data change) career by career; suite green after each.
- Record the name-collision decision (`ste.Skill` vs rename) here.

### Step 2: `Skill` (simple skills, level modes)

- TDD `Skill.apply()` for single-field skills in all three modes:
  increment (`ctx.level=None`), grant-at-0 (`ctx.level=0`), set-if-lower
  (`level=N`). Pin the `ctx.level` vs `entry.level` precedence with a test
  and record the decision in the stub notes above.
- TDD the `type[AnySkill]` ↔ kind-string serialization annotation.
- Migrate table rows that are bare single-specialization skill instances.

### Step 3: `Skill` (specialization choice)

- TDD: applying `Skill(Electronics)` (multi-field, no specialization) in
  increment mode queues the specialization choice pending with concrete
  options — and in level-0 mode grants the bare base skill with **no**
  choice (current basic-training behaviour, must not change).
- TDD `SkillTableEntryChosenHandler` and the form round-trip for the
  specialization choice.
- Migrate the remaining bare-instance rows.

### Step 4: `Psi`

- Driver tests red first for the Psion service-skills fix (see above).
- TDD `Psi.apply()`: the three cases, `allow_acquisition` both ways;
  pending ids via `ctx.next_pending_id()`.
- Migrate Psion (and any other) Psi rows. Driver tests go green.
- Delete `skill_table_option_is_available` once no legacy Psi rows remain.

### Step 5: `SkillChoice` and `PsiChoice`

- TDD `expand_skill_classes()` / `expand_talent_classes()` on raw unions,
  broad aliases, and the failure mode for unexpandable input.
- TDD choice application: pending queued with concrete expanded options,
  resolution via `SkillTableEntryChosenHandler` applies the chosen entry.
- Migrate tuple rows and `skill_instances(...)` rows, then `_TALENTS`.

### Step 6: Delete the legacy layer

- Remove the bridge, the legacy union members, the free functions listed
  under **Deleted**, the old `Psi` RootModel, and the now-unproduced
  `SkillChoiceHandler` / `PsionicTalentTrainingHandler` if no other
  producers remain (verify — pre-career institute training also uses
  `PsionicTalentTrainingHandler`).
- Narrow `SkillTableItem` to the new union; drop `SkillTableEntry`.
- Full gate: `./pre-commit.sh`.

Each step ends with the boy-scout refactor pass: ruff check/format, ty check,
duplicate-code scan on the touched area.

---

## Relationship to Other Plans

- [plan-characteristic-type.md](plan-characteristic-type.md): `Char` wraps
  `Chars` for now; revisit when Characteristic classes land.
- [plan-not-gained-api.md](plan-not-gained-api.md): `Psi.apply()` uses
  `projection.not_gained()` (already implemented in that plan's Step 1).
  Its Step 2 (`Chars` in choice forms) is resolved by this design: `Char`
  never becomes a choice option.
- [plan-pending-input-queue-api.md](plan-pending-input-queue-api.md): the
  XChoice types queue pending inputs; if the queue API lands first, use it
  here instead of `pending_inputs.insert(0, ...)`.
- [archive/plan-psionic-skill-table.md](archive/plan-psionic-skill-table.md):
  `Psi.apply()` with `allow_acquisition=True` is the proper fix for the
  service-skills routing bug documented there; the corresponding
  `todo_maybe.md` item is superseded by this plan.
