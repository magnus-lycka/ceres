# Plan: Unified `terms` List and `PreCareerTerm` Model

**Status: Complete** — implemented in commit 9bc4a64.

## Context

`CharacterSummary` currently tracks career history and pre-career history in separate, incompatible
structures:

```python
career_terms: list[CareerTerm]               # career history only
precareer: _PreCareerField | None            # currently in-progress pre-career
precareer_completed: _PreCareerField | None  # at most one completed pre-career
precareer_skills: list[AnySkill]             # skills pending graduation boost
```

Problems with this layout:
- Only one pre-career is supported (hard `ReplayError` guard), but the rules permit multiple
  pre-careers as long as each is taken within terms 1–3 (one per term).
- `precareer_skills` is anonymous global state; with multiple pre-careers it becomes ambiguous and
  the link to a specific pre-career term is lost.
- `terms_started_in_pre_and_careers` adds at most 1 regardless of how many pre-careers were
  attended.
- Pre-career terms are invisible to `diff()`, `notes.py`, and the term list in `routes.py`.
- Code that belongs to the pre-career term object (e.g. University graduation effects) is
  scattered across `precareer_events.py`, `university.py`, and `character_state.py` fields.

The fix is a unified `terms: list[AnyTerm]` that holds both `CareerTerm` and `PreCareerTerm`
records in chronological order, plus `PreCareerTerm` subclasses that own their own state and
behaviour.

`docs/character-creation-rules.md` also needs updating: section 10 covers only University and
Military Academy but five Companion pre-careers are already implemented.

---

## Class Design

### `Term` base — `src/ceres/character/domain/term_data.py`

Add alongside the existing `TermData` (which is the *definition* base; `Term` is the *record* base):

```python
class Term(BaseModel):
    kind: str          # discriminator; concrete subclasses fix to a Literal
    event: str | None = None
    mishap: str | None = None
    prison: str | None = None

    @property
    def notes(self) -> NoteList: ...
```

`event`, `mishap`, `prison`, and `notes` are relevant to both career and pre-career terms (pre-career
events, mishap-like non-graduation outcomes, and potential prison sends from events).

### `CareerTerm` — `src/ceres/character/domain/career/career_data.py`

```python
class CareerTerm(Term):
    kind: Literal['career'] = 'career'
    # all existing fields unchanged
```

`career_data.py` already has no dependency on `character_state.py`, so importing `Term` from
`term_data.py` introduces no new circular imports.

### `PreCareerTerm` hierarchy — `src/ceres/character/domain/precareer/precareer_term.py` (new file)

```python
class PreCareerTerm(Term):
    """Base record for all pre-career terms."""
    completed: bool = False   # True once graduation or non-graduation is resolved
    graduated: bool = False
    honours: bool = False

    def apply_entry(self, projection: CharacterProjection, event: Event, pending_idx: int) -> int:
        return pending_idx

    def apply_graduation(self, projection: CharacterProjection, event: Event, honours: bool) -> int:
        return 0

    def apply_failed_graduation(self, projection: CharacterProjection, event: Event) -> None:
        pass
```

Concrete subclasses, one per pre-career type:

| Class | `kind` | Extra fields |
|---|---|---|
| `UniversityTerm` | `'university'` | `pending_skills: list[AnySkill]` |
| `ArmyAcademyTerm` | `'army_academy'` | — |
| `MarineAcademyTerm` | `'marine_academy'` | — |
| `NavyAcademyTerm` | `'navy_academy'` | — |
| `ColonialUprbringingTerm` | `'colonial_upbringing'` | — |
| `MerchantAcademyBusinessTerm` | `'merchant_academy_business'` | — |
| `MerchantAcademyShipboardTerm` | `'merchant_academy_shipboard'` | — |
| `PsionicCommunityTerm` | `'psionic_community'` | — |
| `SchoolOfHardKnocksTerm` | `'school_of_hard_knocks'` | — |
| `SpacerCommunityTerm` | `'spacer_community'` | — |

`UniversityTerm.apply_graduation()` is the primary case that needs extra state: it reads
`self.pending_skills` (skills chosen during entry) and increments each of them on graduation. This
replaces the current `projection.summary.precareer_skills` read in `UniversityPreCareer.apply_graduation()`.

`UniversityTerm.apply_entry()` queues skill-choice pendings and delegates back to the
projection (no change to skill-choice logic; just moves from `UniversityPreCareer.apply_entry`).

`MilitaryAcademyTerm` subclasses move the graduation and failed-graduation logic from
`MilitaryAcademyPreCareer.apply_graduation/apply_failed_graduation`. These methods do not need
term-specific state, so the move is straightforward.

#### Factory method on `PreCareerData`

Each `PreCareerData` subclass gains a `make_term() -> PreCareerTerm` factory:

```python
class UniversityPreCareer(PreCareerData):
    def make_term(self) -> UniversityTerm:
        return UniversityTerm()
```

`PreCareerData.make_term()` raises `NotImplementedError` (or can be abstract) — subclasses must
implement it. Simple pre-careers with no extra state (Colonial Upbringing, etc.) just return the
plain subclass instance.

`PreCareerEntryHandler` calls `precareer.make_term()` to get the term, appends it to
`summary.terms`, then calls `term.apply_entry(projection, event, pending_idx)`.

### Serialization / circular import

`precareer_term.py` will import `CharacterProjection` from `character_state.py` (for the
`apply_*` method signatures). `character_state.py` needs `precareer_term.py` for the discriminated
union. This is a circular import at module level.

**Solution:** use the same `BeforeValidator`+deferred-import pattern already used for pending
inputs. Define a `_deserialise_term(v)` function in `character_state.py` that lazily imports the
concrete term classes:

```python
def _deserialise_term(v: object) -> object:
    if isinstance(v, Term):
        return v
    if isinstance(v, dict):
        match v.get('kind', 'career'):
            case 'career':
                return CareerTerm.model_validate(v)
            case 'university':
                from ceres.character.domain.precareer.precareer_term import UniversityTerm
                return UniversityTerm.model_validate(v)
            # ... remaining cases ...
```

`CharacterSummary.terms` is annotated with `BeforeValidator(_deserialise_term)` and
`SerializeAsAny[Term]`:

```python
terms: list[Annotated[Term, BeforeValidator(_deserialise_term), SerializeAsAny]] = Field(default_factory=list)
```

---

## `CharacterSummary` Changes — `character_state.py`

### Field replacements

```python
# Remove:
career_terms: list[CareerTerm]
precareer: _PreCareerField | None
precareer_completed: _PreCareerField | None
precareer_skills: list[SerializeAsAny[AnySkill]]

# Add:
terms: list[...]  # as above
```

### New / updated properties

```python
@property
def career_terms(self) -> list[CareerTerm]:
    return [t for t in self.terms if isinstance(t, CareerTerm)]

@property
def current_precareer_term(self) -> PreCareerTerm | None:
    """The in-progress pre-career term, if any."""
    from ceres.character.domain.precareer.precareer_term import PreCareerTerm
    t = self.terms[-1] if self.terms else None
    if isinstance(t, PreCareerTerm) and not t.completed:
        return t
    return None
```

The `career_terms` property means the ~40 internal call sites that read
`summary.career_terms[-1]`, iterate `summary.career_terms`, or pass it to helpers continue to
work without change. Only call sites that *append* to `career_terms` need updating (those are
in career event handlers).

### `terms_started` simplification

```python
def terms_started(self, *, only_current_career: bool, include_precareer: bool) -> int:
    if only_current_career:
        career = self.current_career
        ct = self.latest_career_run_terms(career) if career is not None else []
        return len(ct)
    if include_precareer:
        return len(self.terms)   # correctly counts all terms including multiple pre-careers
    return len(self.career_terms)
```

`terms_started_in_pre_and_careers` becomes `len(self.terms)`.

### `diff()` update

The `diff()` loop over `career_terms` handles career-specific fields (`forced_stay`,
`forced_leave`). Extend to also report when a pre-career term is added or completed.

---

## `precareer_events.py` Changes

### `PreCareerEntryHandler.apply()`

- **Remove** the `precareer_completed is not None` guard (multiple pre-careers are now permitted).
- Replace `projection.summary.precareer = precareer` with:
  ```python
  term = precareer.make_term()
  projection.summary.terms.append(term)
  ```
- Call `term.apply_entry(projection, event, pending_idx)` instead of
  `precareer.apply_entry(projection, event, pending_idx)`.

### `PreCareerSkillChoiceHandler.apply()`

Replace `projection.summary.precareer_skills.append(self.skill)` with:
```python
term = projection.summary.current_precareer_term
if isinstance(term, UniversityTerm):
    term.pending_skills.append(self.skill)
```
(Only University currently uses this list.)

### `PreCareerEventHandler.apply()`

Replace `projection.summary.precareer` with `projection.summary.current_precareer_term.precareer_data`
(or however the precareer definition is accessed from the term). For non-graduation rolls (3, 11):
set `term.completed = True` and `term.event = term_event.text` on the term instead of clearing the
old three fields.

### `PreCareerGraduationHandler.apply()`

Replace:
```python
projection.summary.precareer_completed = precareer
projection.summary.precareer = None
projection.summary.precareer_skills = []
```
with:
```python
term = projection.summary.current_precareer_term
term.graduated = graduated
term.honours = honours
term.completed = True
```

Call `term.apply_graduation(projection, event, honours)` instead of
`precareer.apply_graduation(projection, event, honours)`. The graduation roll check
(`self.roll`, `precareer.graduation.target`, `precareer.honours_target`) stays in the handler
using `PreCareerData` fields; only the *effects* move to the term.

---

## `PreCareerData` Changes

- Add abstract `make_term() -> PreCareerTerm` to `PreCareerData`.
- Implement in each subclass (see table above).
- `apply_entry()`, `apply_graduation()`, `apply_failed_graduation()` on `PreCareerData` become
  dead code once moved to `PreCareerTerm` subclasses; remove them.
- `apply_entry()` on the base `PreCareerData` (the companion generic entry) moves to
  `PreCareerTerm` (or a `GenericPreCareerTerm` base that companion non-academy subclasses inherit).

---

## Other Changed Files

| File | Change |
|---|---|
| `src/ceres/character/domain/term_data.py` | Add `Term` base class |
| `src/ceres/character/domain/career/career_data.py` | `CareerTerm(Term)`, add `kind` |
| `src/ceres/character/domain/precareer/precareer_term.py` | **New file** — full `PreCareerTerm` hierarchy |
| `src/ceres/character/domain/precareer/precareer_data.py` | Add `make_term()`; remove `apply_entry/graduation/failed_graduation` defaults once moved |
| `src/ceres/character/domain/precareer/university.py` | Remove `apply_entry`, `apply_graduation`; implement `make_term()` returning `UniversityTerm` |
| `src/ceres/character/domain/precareer/military_academy.py` | Same; `ArmyAcademyPreCareer.make_term()` → `ArmyAcademyTerm()` |
| `src/ceres/character/domain/precareer/*.py` (companion) | Implement `make_term()` |
| `src/ceres/character/notes.py` | Iterate `summary.terms`; render both `CareerTerm` and `PreCareerTerm` notes |
| `src/ceres/character/web/routes.py` | Update term-list display (line 160) to `summary.terms` |

---

## Snapshot / JSON Changes

Adding `kind: 'career'` to `CareerTerm` and replacing `career_terms`, `precareer`,
`precareer_completed`, `precareer_skills` with `terms` changes the serialized JSON shape. All
snapshots that include these keys must be regenerated. Run:

```bash
uv run pytest --snapshot-update
```

---

## `docs/character-creation-rules.md` Update

Expand section 10 "Pre-Career Education" to include all Companion pre-careers. Clarify that
multiple pre-careers are allowed (one per term, terms 1–3 only). Add subsections:

- **Colonial Upbringing** — available automatically if homeworld TL 8 or lower; no entry roll.
- **Merchant Academy (Business curriculum)** — entry INT 7+.
- **Merchant Academy (Shipboard curriculum)** — entry DEX 7+.
- **Psionic Community** — available automatically if PSI 8+; no standard entry roll.
- **School of Hard Knocks** — available automatically if SOC 6 or lower; no entry roll.
- **Spacer Community** — available automatically if homeworld Code 0 and INT 4+; no entry roll.

---

## Test Changes

- Update tests checking `summary.precareer`, `summary.precareer_completed`, or
  `summary.precareer_skills` to use `summary.current_precareer_term` or `summary.terms[-1]`.
- Remove / update the test that asserts the "only one pre-career" guard error.
- Add an approval or use-case test: character takes Spacer Community in term 1 then University in
  term 2; assert both `PreCareerTerm` records appear in `summary.terms`, skills from each are
  correct, and University graduation bonus applies to the right `pending_skills`.

---

## Verification

```bash
uvx ruff check --fix && uvx ruff format   # after each edited file
uvx ty check
uv run pytest                              # quick suite must pass
uv run pytest --snapshot-update            # regenerate changed snapshots
uv run pytest --all-tests                  # full suite
```

Manually verify the character creation web UI still shows pre-career terms in the character sheet
and that both pre-career and career notes appear correctly.
