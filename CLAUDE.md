# Ceres — Mongoose Traveller 2nd Edition in Python

Ceres builds Mongoose Traveller 2nd Edition assemblies in Python. Current
domains include starships, robots, and reusable gear/catalogue items. A design
is an ordinary Python object: instantiate the relevant model, pass it part
objects and parameters, and get back a validated design. Goals include:

- Descriptions similar to official stat blocks or catalogue entries
- Legality checks (tonnage, budget, TL consistency, required components)
- Data structures usable by other code, reports, tests, and export tools

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for patterns and technical choices.
See [DEVELOPMENT_AND_TESTING.md](DEVELOPMENT_AND_TESTING.md) for the full
development workflow, test conventions, commands, and snapshot management.

## Output formats

Ships can be rendered to HTML, Typst, or PDF from a `Ship` or `ShipSpec`:

```python
from ceres.report import render_ship_html, render_ship_pdf, render_ship_typst

html = render_ship_html(ship)          # Jinja2 -> HTML string
typst = render_ship_typst(ship)        # Typst source string
pdf = render_ship_pdf(ship)            # Typst -> PDF bytes

# From a pre-built spec:
from ceres.report import render_ship_spec_html, render_ship_spec_pdf
html = render_ship_spec_html(spec, theme='dark')
pdf  = render_ship_spec_pdf(spec, page_size='us-letter')
```

Robots can be rendered to Typst or PDF from a `Robot` or `RobotSpec`:

```python
from ceres.report import render_robot_pdf, render_robot_typst
```

The gear catalog has its own entry points in `ceres.gear.catalog`:

```python
from ceres.gear.catalog import (
    render_communication_catalog_pdf,
    render_computer_catalog_html,
    render_gear_catalog_typst,
)
```

`ceres.report` is a template engine; it has no domain knowledge. Domain
packages own their Jinja2/Typst templates and context builders. See
[ARCHITECTURE.md](docs/ARCHITECTURE.md) for the current design.

## Rules Reference

Use the `refs/` directory (gitignored) for relevant Traveller source material
converted to text/markdown, screenshots, or local PDF excerpts. This directory
is expected to exist in a working copy, but it must not be committed. Examples
include `refs/hg`, `refs/csc`, `refs/robot`, `refs/spinext`, and source-derived
test case notes. Read relevant pages when implementing or verifying a
subsystem.

Do not treat any reference design output as an unquestionable answer key.
If Ceres differs from a published sheet or external design tool, first
determine which explicit rule, table, or stated interpretation would produce
that result. Only then adjust the code. Never change the model merely to
"match the source" without understanding the rule path that leads there.

When writing tests that verify Traveller rules, derive the expected assertions
from the Traveller rules and from [RULE_INTERPRETATIONS.md](docs/RULE_INTERPRETATIONS.md),
not from the current implementation. Tests must not inspect the production code
and then encode whatever it already does. Likewise, when changing production
code to make tests pass, base the implementation on an honest reading of the
rules and recorded interpretations. Do not tweak formulas, constants, or edge
cases merely to turn the suite green; if the rule path is unclear, document the
interpretation before encoding it.

See [RULE_INTERPRETATIONS.md](docs/RULE_INTERPRETATIONS.md) and
[TEST_CASE_ASSEMBLIES.md](docs/TEST_CASE_ASSEMBLIES.md)

Source-derived design tests should assert against an `_expected =
SimpleNamespace(...)` built from the source material. If Ceres deliberately
differs because of a rule interpretation, TCS convention, or source error,
modify `_expected` with a nearby comment explaining why. These tests validate a
design against source-derived expectations; lower-level behavior belongs in
unit tests. They should also check that no unexpected errors or warnings appear.

## Python Style

- **Python 3.14+**: Use modern typing syntax throughout.
  - `X | None` not `Optional[X]`
  - `list[X]` not `List[X]`, `dict[K, V]` not `Dict[K, V]`
  - No `from __future__ import annotations` (deprecated in 3.14)
  - No quoted type hints — PEP 649 makes annotations lazy by default in 3.14

## Alpha status and backward compatibility

Ceres is Alpha software (version 0.1.x). There is one user, all existing data
lives in the test suite, and nothing is deployed. Therefore:

- **Never consider backward compatibility or data migration.** If changing a
  model, event, or serialization format is the right design decision, do it.
  Do not add shims, compatibility hacks, migration scripts, or deprecated
  aliases to avoid breaking saved state.
- This applies to event logs, JSON snapshots, Pydantic model fields, API
  signatures, and any other artifact. Just change it.

## Ways of Working

- **TDD** - Write tests first, then implement. Tests live in `tests/`.
- **Test Design** - Tests should verify that the code under test does what it is supposed to do.
  Tests written to verify that the code under test does what it does are of much less value.
  If code is broken with respect to the behaviour under test, the test must go red. Never
  route around, weaken, skip, or narrowly assert past a known bug just to keep the suite
  green. Red tests are useful evidence of required work; green tests that tolerate known
  broken behaviour make correctness harder to achieve.
- **Code Design** - Before writing code, always consider whether this is the right place for
  this particular code. Assume that one module, class or function is always responsible for
  anything in the system. That's where code should go. If there isn't a good place for some
  code, the structure needs to be modified.
- **pytest**
  - `uv run pytest` for the quick default suite
  - `uv run pytest --with-slow` to include slow tests
  - `uv run pytest --with-generated-output` to include artifact-generating tests
  - `uv run pytest --all-tests` to run everything
  - `uv run pytest --cov --cov-report=term-missing` for coverage
- **ruff** - `uvx ruff check` and `uvx ruff format` (fix lint and formatting)
- **ty** - `uvx ty check` (type checking)
- **pylint duplicate-code** - Run
  `uvx pylint --disable=all --enable=duplicate-code src/ceres/ tests`
  regularly as a design smell check. Treat the output as signal, not a
  commandment: source-derived reference data, intentionally parallel tests, and
  clear examples may stay duplicated. When the same setup, assertion block, or
  helper logic appears in several places, consider extracting a small test
  helper or shared assertion that keeps the tests readable.

The usual full local gate is `./pre-commit.sh`, which also runs `deptry` and
`bandit`.

## Code and Test Structure

The guiding principles are **SRP** (Single Responsibility Principle), **DRY**
(Don't Repeat Yourself), and **KISS** (Keep It Simple, Stupid). Each
module, class, and function has one reason to change. Shared setup and
assertion patterns belong in helpers, not copy-pasted across test files. The
simplest test that expresses the intent is the right test.

**Tests must mirror the structure of the code.** When a subsystem changes, it
should be obvious which tests are affected and why. A test that breaks because
an internal implementation detail changed — but observable behaviour did not —
is at the wrong abstraction level.

**Abstraction levels must not be crossed.** Tests written for code at one level
of abstraction must not rely on lower levels, and vice versa:

- **Career rule tests** (`tests/unit/character/test_army.py`, `test_careers.py`,
  etc.) verify Traveller rules: "does Army survival with END 5 and a roll of 4
  produce a mishap?" These tests use `CharacterDriver`
  (`tests/unit/character/helpers.py`) exclusively. They must not reference event
  class names, pending type names, event IDs, or fulfillment order — those are
  implementation details of the event/pending layer.

- **Event and pending mechanics tests** (`test_events_pending_inputs.py`)
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

Likewise in production code: event internals belong in `events.py` and
`state.py`; career rule logic belongs in `career_data.py` and assignment
classes. Code that mixes the two creates coupling that forces changes across
multiple concerns when only one should need to change.

## Examples

The main source-derived reference cases live in `tests/approval/ships/` and
`tests/approval/robots/`, with gallery output in `tests/gallery/`. These serve
as integration targets for rule interpretation: as subsystems are implemented,
differences against reference stat blocks should be explained by rules,
omissions, or explicit project decisions. Expected values are captured as
approval snapshots; annotate discrepancies with `snap.annotate(...)`.

Keep documentation in English. Use `docs/RULE_INTERPRETATIONS.md` for general
rule interpretations, `docs/TEST_CASE_ASSEMBLIES.md` for test-case mapping
conventions, and topic or `plan-*.md` files in `docs/` for implementation
plans.

## Commands

```bash
uv run pytest                                         # quick suite
uv run pytest --all-tests                            # full suite
uv run pytest --cov --cov-branch --all-tests --cov-report=term-missing # tests + coverage
uvx ruff check --fix                                   # lint and auto-fix
uvx ruff format                                        # format code
uvx ty check                                           # type check
uvx pylint --disable=all --enable=duplicate-code src/ceres/ tests
```
