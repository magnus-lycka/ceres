# Ceres - Ship Design for Mongoose Traveller 2nd Edition

Build Traveller starships according to Mongoose High Guard 2022 rules.
A starship is built as a Python object: instantiate a `Ship`, pass it parts
objects and parameters. The goals are:

- A ship description similar to official stat blocks
- Legality checks (tonnage, budget, TL consistency, required components)
- A data structure usable by other code (passenger transport, cargo, etc.)

See [ARCHITECTURE.md](ARCHITECTURE.md) for patterns and technical choices.

## Rules Reference

Use the `refs/` directory (gitignored) for your copy of
Mongoose Traveller PDFs (High Guard 2022, etc.).
Read relevant pages when implementing or verifying a subsystem.

## Python Style

- **Python 3.14+**: Use modern typing syntax throughout.
  - `X | None` not `Optional[X]`
  - `list[X]` not `List[X]`, `dict[K, V]` not `Dict[K, V]`
  - No `from __future__ import annotations` (deprecated in 3.14)
  - No quoted type hints — PEP 649 makes annotations lazy by default in 3.14

## Ways of Working

- **TDD** - Write tests first, then implement. Tests live in `tests/`.
- **pytest** - `uv run pytest` (with `pytest-cov` for coverage)
- **ruff** - `uvx ruff check` and `uvx ruff format` (fix lint and formatting)
- **ty** - `uvx ty check` (type checking)

All four must pass before considering work complete.

## Examples

The `examples/` directory contains ship definitions matching ships from the
reference PDFs. These serve as integration targets — as subsystems are
implemented, the examples should produce output matching the reference stat
blocks. Expected values are documented as comments in each example file.

## Commands

```bash
uv run pytest --cov=ceres --cov-report=term-missing   # tests + coverage
uvx ruff check --fix                                   # lint and auto-fix
uvx ruff format                                        # format code
uvx ty check                                           # type check
```
