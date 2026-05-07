# Ceres — Mongoose Traveller 2nd Edition in Python

Ceres builds Mongoose Traveller 2nd Edition things in Python, such as
starships (using the High Guard 2022 rules). A ship is an ordinary Python
object: instantiate `Ship`, pass it part objects and parameters, and get back
a validated design. Goals include:

- A ship description similar to official stat blocks
- Legality checks (tonnage, budget, TL consistency, required components)
- A data structure usable by other code (passenger transport, cargo, etc.)

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for patterns and technical choices.

## Output formats

Ships can be rendered to HTML or PDF from a `Ship` or `ShipSpec`:

```python
from ceres.report import render_ship_html, render_ship_pdf

html = render_ship_html(ship)          # Jinja2 → HTML string
pdf  = render_ship_pdf(ship)           # Typst → bytes

# From a pre-built spec:
from ceres.report import render_ship_spec_html, render_ship_spec_pdf
html = render_ship_spec_html(spec, theme='dark')
pdf  = render_ship_spec_pdf(spec, page_size='us-letter')
```

The gear catalog has its own entry points in `ceres.gear.catalog`:

```python
from ceres.gear.catalog import render_computer_catalog_html, render_computer_catalog_pdf
```

`ceres.report` is a template engine — it has no domain knowledge. Domain
packages own their Jinja2/Typst templates and context builders. See
[docs/plan-pdf-output.md](docs/plan-pdf-output.md) for design decisions.

## Rules Reference

Use the `refs/` directory (gitignored) for relevant parts of
Traveller rules converted to text/markdown, such as your copy of
Mongoose Traveller PDFs (High Guard 2022, etc.).
Read relevant pages when implementing or verifying a subsystem.

Do not treat any reference ship output as an unquestionable facit.
If Ceres differs from a published ship sheet or external design tool, first
determine which explicit rule, table, or stated interpretation would produce
that result. Only then adjust the code. Never change the model merely to
"match the facit" without understanding the rule path that leads there.

When writing tests that verify Traveller rules, derive the expected assertions
from the Traveller rules and from [RULE_INTERPRETATIONS.md](docs/RULE_INTERPRETATIONS.md),
not from the current implementation. Tests must not inspect the production code
and then encode whatever it already does. Likewise, when changing production
code to make tests pass, base the implementation on an honest reading of the
rules and recorded interpretations. Do not tweak formulas, constants, or edge
cases merely to turn the suite green; if the rule path is unclear, document the
interpretation before encoding it.

See [RULE_INTERPRETATIONS.md](docs/RULE_INTERPRETATIONS.md) and
[TEST_CASE_SHIPS.md](docs/TEST_CASE_SHIPS.md)

## Python Style

- **Python 3.14+**: Use modern typing syntax throughout.
  - `X | None` not `Optional[X]`
  - `list[X]` not `List[X]`, `dict[K, V]` not `Dict[K, V]`
  - No `from __future__ import annotations` (deprecated in 3.14)
  - No quoted type hints — PEP 649 makes annotations lazy by default in 3.14

## Ways of Working

- **TDD** - Write tests first, then implement. Tests live in `tests/`.
- **pytest**
  - `uv run pytest` for the quick default suite
  - `uv run pytest --with-slow` to include slow tests
  - `uv run pytest --with-generated-output` to include artifact-generating tests
  - `uv run pytest --all-tests` to run everything
  - `uv run pytest --cov --cov-report=term-missing` for coverage
- **ruff** - `uvx ruff check` and `uvx ruff format` (fix lint and formatting)
- **ty** - `uvx ty check` (type checking)

The usual full local gate is `./pre-commit.sh`, which also runs `deptry` and
`bandit`.

## Examples

The main source-derived reference cases live in `tests/ships/`, not in a
separate examples package. These serve as integration targets for rule
interpretation: as subsystems are implemented, differences against reference
stat blocks should be explained by rules, omissions, or explicit project
decisions. Expected values are documented in the test files and related docs,
but they are not to be copied blindly into the code without understanding why
the rules lead there.

## Commands

```bash
uv run pytest                                         # quick suite
uv run pytest --all-tests                            # full suite
uv run pytest --cov --cov-report=term-missing        # tests + coverage
uvx ruff check --fix                                   # lint and auto-fix
uvx ruff format                                        # format code
uvx ty check                                           # type check
```
