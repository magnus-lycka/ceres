# Development and Testing

This document is the authoritative reference for how to develop and test Ceres.
`CLAUDE.md` and `AI_README.md` both refer here for the full picture.

## Ways of Working

- **TDD** — Write tests first, then implement. Tests live in `tests/`.
- **Test Design** — Tests should verify that the code under test does what it
  is *supposed* to do. A test that encodes whatever the code currently does is
  of much less value. If code is broken with respect to the behaviour under
  test, the test must go red. Never route around, weaken, skip, or narrowly
  assert past a known bug to keep the suite green. Red tests are useful
  evidence of required work; green tests that tolerate known broken behaviour
  make correctness harder to achieve.
- **Code Design** — Before writing code, ask whether this is the right place
  for it. Assume one module, class, or function is always responsible for any
  given thing. That is where the code belongs. If no good place exists, the
  structure needs to change.
- **SRP / DRY / KISS** — Each module, class, and function has one reason to
  change. Shared setup and assertion patterns belong in helpers, not
  copy-pasted across test files. The simplest test that expresses the intent
  is the right test.
- **Tests must mirror the structure of the code.** When a subsystem changes,
  it should be obvious which tests are affected and why. A test that breaks
  because an internal implementation detail changed — but observable behaviour
  did not — is at the wrong abstraction level.

## Python Style

- **Python 3.14+**: Use modern typing syntax throughout.
  - `X | None` not `Optional[X]`
  - `list[X]` not `List[X]`, `dict[K, V]` not `Dict[K, V]`
  - No `from __future__ import annotations` (deprecated in 3.14)
  - No quoted type hints — PEP 649 makes annotations lazy by default in 3.14

## Alpha Status and Backward Compatibility

Ceres is Alpha software (version 0.1.x). There is one user, all existing data
lives in the test suite, and nothing is deployed. Therefore:

- **Never consider backward compatibility or data migration.** If changing a
  model, event, or serialization format is the right design decision, do it.
  Do not add shims, compatibility hacks, migration scripts, or deprecated
  aliases to avoid breaking saved state.
- This applies to event logs, JSON snapshots, Pydantic model fields, API
  signatures, and any other artifact. Just change it.

## Rules Reference

Use the `refs/` directory (gitignored) for relevant Traveller source material
converted to text/markdown, screenshots, or local PDF excerpts. This directory
is expected to exist in a working copy, but it must not be committed. Examples
include `refs/hg`, `refs/csc`, `refs/robot`, `refs/spinext`, and source-derived
test case notes. Read relevant pages when implementing or verifying a
subsystem.

Do not treat any reference design output as an unquestionable answer key. If
Ceres differs from a published sheet or external design tool, first determine
which explicit rule, table, or stated interpretation would produce that result.
Only then adjust the code. Never change the model merely to "match the source"
without understanding the rule path that leads there.

When writing tests that verify Traveller rules, derive the expected assertions
from the Traveller rules and from
[RULE_INTERPRETATIONS.md](docs/RULE_INTERPRETATIONS.md), not from the current
implementation. Tests must not inspect production code and then encode whatever
it already does. Likewise, when changing production code to make tests pass,
base the implementation on an honest reading of the rules. Do not tweak
formulas, constants, or edge cases merely to turn the suite green; if the rule
path is unclear, document the interpretation before encoding it.

See [RULE_INTERPRETATIONS.md](docs/RULE_INTERPRETATIONS.md) and
[TEST_CASE_ASSEMBLIES.md](docs/TEST_CASE_ASSEMBLIES.md).

Source-derived design tests should assert against an `_expected =
SimpleNamespace(...)` built from the source material. If Ceres deliberately
differs because of a rule interpretation, TCS convention, or source error,
modify `_expected` with a nearby comment explaining why. These tests validate a
design against source-derived expectations; lower-level behaviour belongs in
unit tests. They should also check that no unexpected errors or warnings appear.

---

## Test Categories

Ceres has six categories of test, each with a clear location and purpose.

### Unit Tests — `tests/unit/`

Focused tests for individual modules and functions. Each test file mirrors a
single source file: `src/ceres/foo/bar.py` → `tests/unit/foo/test_bar.py`. A
unit test breaks if the unit it targets is broken, and for no other reason.

| Directory | What it tests |
| --- | --- |
| `tests/unit/character/` | Traveller career rules, event/pending mechanics, web forms, character domain |
| `tests/unit/make/` | Ship and robot construction, spec building |
| `tests/unit/report/` | HTML, Typst, and PDF rendering |
| `tests/unit/gear/` | Gear catalogue |
| `tests/unit/shared/` | Shared domain primitives |
| `tests/unit/worlds/` | Sector/world filters |
| `tests/unit/adapters/` | External adapter code |

**Test abstraction rules for character tests:**

Abstraction levels must not be crossed:

- **Career rule tests** (`tests/unit/character/test_army.py`, `test_careers.py`,
  etc.) verify Traveller rules: "does Army survival with END 5 and a roll of 4
  produce a mishap?" These tests use `CharacterDriver`
  (`tests/unit/character/helpers.py`) exclusively. They must not reference event
  class names, pending type names, event IDs, or fulfilment order — those are
  implementation details of the event/pending layer.

- **Event and pending mechanics tests** (`tests/approval/character/uc/test_events_pending_inputs.py`)
  verify the event sourcing machinery: `apply()`, `resolve()`,
  `event_from_form()`. These tests work directly with event and pending objects
  and may reference their internals.

- **Form and web-layer tests** verify `input_specs()` and form parsing. They
  test the web boundary only.

`CharacterDriver` is the single point of contact for career rule tests. It
finds pending inputs by *type*, not by ID, and submits the correct event type
automatically. Adding or reordering implementation steps inside a career should
not break a `CharacterDriver`-based test unless the observable career behaviour
changed.

When you find yourself writing a career rule test that imports `SurviveEvent`,
`PendingSurvive`, or any other event/pending type, stop: use `CharacterDriver`
instead. When you find yourself writing an event mechanics test that calls
`CharacterDriver`, stop: test `apply()` or `resolve()` directly.

### Use-case Approval Tests — `tests/approval/<package>/uc/`

Approval snapshot tests for complex multi-module scenarios where several
subsystems interact. They verify a complete state after a sequence of decisions
— both that the expected consequences occurred and that nothing unexpected
changed.

Use a use-case test when:

- Three or more distinct parts of the output change in a single event.
- "Nothing else changed" is part of the invariant.
- A plain assertion list would be long, brittle, or hard to review.
- The test spans multiple modules and does not have a clear 1:1 home in `tests/unit/`.

Character use-case tests drive the scenario with `CharacterDriver` and snapshot
`d.projection.summary.model_dump(mode='json')` at the natural resolution point.
This gives a stable, event-ID-free snapshot of the full observable character
state.

| Directory | What it covers |
| --- | --- |
| `tests/approval/character/uc/` | Career rules, precareers, aging, character summary, web, event/pending mechanics |
| `tests/approval/ship/uc/` | Ship customisation, drives, hulls, systems, weapons, serialization, HTML/PDF rendering |
| `tests/approval/robot/uc/` | Robot configuration, skill packages, serialization, PDF rendering |

### End-to-end Approval Tests — `tests/approval/<package>/e2e/`

Snapshot tests for complete assembled designs. They exercise the full build
pipeline from domain objects to a rendered spec.

| Directory | What it snapshots |
| --- | --- |
| `tests/approval/ship/e2e/` | `ship.build_spec().model_dump(mode='json')` |
| `tests/approval/robot/e2e/` | `robot.build_spec().model_dump(mode='json')` |
| `tests/approval/character/e2e/` | `spec_from_summary(summary).model_dump(mode='json')` |

Each test file has a `build_<name>()` function. `AnnotatedSnapshot` wraps the
data and allows notes explaining known discrepancies from source material.

### Gallery Tests — `tests/gallery/`

Generated-output tests that produce HTML, Typst, PDF, and JSON artifacts.
Marked `@pytest.mark.generated_output`; skipped by default. They import builder
functions from the corresponding approval test modules.

| Directory | What it generates |
| --- | --- |
| `tests/gallery/ships/` | HTML, Typst, PDF, JSON for all ships |
| `tests/gallery/robots/` | Typst and PDF for all robots |
| `tests/gallery/npcs/` | Typst and PDF for all NPC stat blocks |

`generated_output/` directories have a `.gitignore` (`*` / `!.gitignore`) so
generated files are never committed.

### Scan Tests — `tests/scan/`

Static analysis tests that enforce structural contracts on the codebase —
things that are too broad to be a unit test but are not about runtime behaviour.

| File | What it checks |
| --- | --- |
| `test_character_typing.py` | No broad `Any` annotations in character-domain APIs |
| `test_audit_discriminator_literals.py` | Discriminator literals are declared and used consistently |

### Tool Tests — `tests/tools/`

Tests for developer tooling and code-generation scripts.

| File | What it tests |
| --- | --- |
| `test_discriminator_literal_audit.py` | The discriminator-audit tool |
| `test_gen_robot_skills.py` | The robot-skills code generator |

---

## Running Tests

```bash
uv run pytest                                         # default suite (fast)
uv run pytest --with-slow                             # include slow tests
uv run pytest --with-generated-output                 # include gallery tests
uv run pytest --with-snapshots                        # include approval snapshots
uv run pytest --all-tests                             # everything
uv run pytest --cov --cov-branch --all-tests --cov-report=term-missing
```

## Managing Snapshots

Snapshots live in `__snapshots__/` directories next to the test files and are
committed to the repository.

```bash
# Regenerate all approval snapshots
uv run pytest tests/approval/ --with-snapshots --snapshot-update

# Update one file's snapshots
uv run pytest tests/approval/ship/e2e/test_beowulf.py --with-snapshots --snapshot-update
```

Always review the diff before committing updated snapshots. A snapshot update
is a test assertion change and must be justified.

## Adding New Tests

| Scenario | Where |
| --- | --- |
| Single-module behaviour | `tests/unit/<matching-path>/test_<module>.py` |
| Complex multi-module scenario | `tests/approval/<package>/uc/test_<topic>.py` |
| New ship design | `tests/approval/ship/e2e/test_<name>.py` + register in `tests/gallery/ships/test_gallery.py` |
| New robot design | `tests/approval/robot/e2e/test_<name>.py` + register in `tests/gallery/robots/test_gallery.py` |
| New NPC | `tests/approval/character/e2e/test_<name>.py` + register in `tests/gallery/npcs/test_gallery.py` |

Gallery coverage tests (`test_gallery_coverage.py`) enforce that every approval
test file is registered in the gallery.

---

## Commands

```bash
# Testing
uv run pytest                                         # quick suite
uv run pytest --all-tests                             # full suite
uv run pytest --cov --cov-branch --all-tests --cov-report=term-missing

# Lint and format
uvx ruff check --fix
uvx ruff format

# Type checking
uvx ty check

# Design smell check (duplicate code)
uvx pylint --disable=all --enable=duplicate-code src/ceres/ tests

# Full local gate
./pre-commit.sh
```
