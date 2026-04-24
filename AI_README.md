# Ceres - Ship Design for Mongoose Traveller 2nd Edition

Build Traveller starships according to Mongoose High Guard 2022 rules.
A starship is built as a Python object: instantiate a `Ship`, pass it parts
objects and parameters. The goals are:

- A ship description similar to official stat blocks
- Legality checks (tonnage, budget, TL consistency, required components)
- A data structure usable by other code (passenger transport, cargo, etc.)

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for patterns and technical choices.

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
