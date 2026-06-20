# Sophont Support Plan

## Goal

Support multiple sophonts (species) in `ceres.character`. The system must allow
new species to be added by creating a new module (and optionally a new career
subpackage) without modifying existing code. Species are added one at a time,
incrementally, each with its own tests.

---

## Architecture changes (one-time, before adding any species)

### 1. Sophont self-registration

`__init__.py` currently has a hardcoded `SOPHONTS` list. Replace with an
auto-discovery loader that mirrors the career loader pattern: scan the sophont
package directory, import each module, collect all registered `Sophont`
instances. Each species module calls `register_sophont(X)` at module level.

### 2. `Sophont` dataclass — extend with species data

```python
@dataclass(frozen=True)
class Sophont:
    name: str
    ucp_stats: tuple[Chars, ...]
    char_mods: dict[Chars, int] = field(default_factory=dict)
    extra_chars: tuple[Chars, ...] = ()   # e.g. PSI, CHA, TER when always rolled
    traits: tuple[str, ...] = ()          # named trait flags, e.g. 'small', 'heightened_senses'
```

`char_mods` are applied once at character start (after UCP rolls). `extra_chars`
are additional characteristics rolled at start. `traits` drive trait-based rules
downstream; add trait handlers only when a trait is first needed.

### 3. Apply char_mods at character start

In the handler that processes UCP characteristic assignment, add a step that
applies `sophont.char_mods` to each characteristic. No other code needs to know
about species modifiers.

### 4. Career loader — support subpackages

`load_careers()` currently scans only `*.py` files at the top level of
`career/`. Extend it to also import any subpackage in `career/` (i.e. any
subdirectory with an `__init__.py`). The subpackage's `__init__.py` imports
its own careers, which register themselves via the existing `CareerData._registry`
mechanism. This is a single change to `loader.py`, done once.

### 5. Career selection context

`is_selectable(projection)` currently ignores `projection`. Extend it to accept
species and polity context. The projection already has `sophont`; add
`birthworld_allegiance: str | None` to `CharacterSummary` (set when homeworld
is assigned from sector data).

Species-gated careers override `is_selectable()`:
```python
def is_selectable(self, projection=None) -> bool:
    return projection is not None and projection.sophont.name == 'Vargr'
```

Polity-gated careers check allegiance:
```python
def is_selectable(self, projection=None) -> bool:
    return projection is not None and projection.birthworld_allegiance == 'DaCf'
```

---

## Incremental species rollout

Add species in this order. Each phase has its own tests before moving on.

### Phase 1 — Infrastructure validation with no-op species

Add two or three minor human races that have no char mods and use core careers
(e.g. Darmine, Liberts, Murrissi). Goal: validate that self-registration,
loader, and `CharacterSummary.sophont` work end-to-end. These files are trivial:

```python
DARMINE = Sophont(name='Darmine', ucp_stats=_HUMANITI_UCP)
register_sophont(DARMINE)
```

Tests: character can be created as Darmine, career selection unchanged.

### Phase 2 — Char mods: simple human minor races

Add species with characteristic modifiers: Geonee (STR+2 DEX-1 END+2 SOC-1),
Jonkeereen (END+1 END-1), Sylean (STR-1 EDU+1), Solomani (no mods, but Race
Roll mechanic). Goal: validate that char_mods are applied correctly.

Tests: assert final characteristics reflect the species modifier.

### Phase 3 — Daryen + first polity career subpackage

Daryen has char mods (STR-1 DEX+1 END-1 INT+1 EDU+1), a mandatory first term
in a specific career, and a restricted career list when in Darrian space.
This requires:
- `birthworld_allegiance` in `CharacterSummary`
- Career subpackage `ceres.character.domain.career.darrian` with AoCS-3 careers
- Darrian careers gated by `birthworld_allegiance == 'DaCf'`

A Daryen character born in the Imperium (A:Im*) uses core careers. A Daryen in
the Darrian Confederation (A:DaCf) uses Darrian careers and has a restricted
list. The career package is polity-gated, not species-gated.

Tests: Daryen in DaCf gets Darrian careers; Daryen elsewhere does not.

### Phase 4 — Vargr

Vargr replaces SOC with CHA. `ucp_stats` already supports this; add CHA to the
`Chars` enum if not present. Vargr char mods: STR-2 DEX+1 END-1.

Career subpackage `ceres.character.domain.career.vargr`. Vargr careers are
gated by `sophont.name == 'Vargr'` AND birthworld in Vargr Extents (A:V*).

CHA's role in career checks (replaces SOC) needs a lookup in career_data:
careers that check SOC should check the sophont's equivalent stat. This may
require a `social_char` field on Sophont or a stat-aliasing mechanism — design
that when it is first needed.

### Phase 5 — Aslan

Most complex. New TER characteristic, sex-locked career assignments, Rite of
Passage pre-career step, and household-as-character.

Break into sub-steps:
- Aslan in Humaniti (Core book): simpler, no TER, STR+2 DEX-2 — add first
- Aslan in Hierate (AoCS 1): full TER, sex-locked, household — add second
- Aslan in Darrian (AoCS 3): different rules, same polity-gate approach

---

## Birthworld → available sophonts

A utility `ceres.character.domain.sophont.world_sophonts` maps a world's UWP
remark field to a list of registered Sophont instances. Uses
`sophont_codes_in_sectors.json` (plus the parenthesized forms documented in
`docs/concepts/sophonts.md`). Returns only sophonts that are currently
registered (i.e. implemented). This is the layer that connects sector data to
the character creation UI.

This can be added at any time; it is not a prerequisite for any phase above.

---

## What does NOT need to change when adding a new species

- `career_data.py` — base career logic unchanged
- `loader.py` — after the subpackage extension is done
- `characteristics.py` — `char_mods` keys are already `Chars` enum members
- `character_start.py` — after the char_mods application hook is in place
- Any existing species module

The only additions are: a new `src/ceres/character/domain/sophont/<name>.py`
and optionally `src/ceres/character/domain/career/<polity>/__init__.py` plus
career files.
