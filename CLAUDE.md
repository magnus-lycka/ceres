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

## Ways of Working

- **TDD** - Write tests first, then implement. Tests live in `tests/`.
- **pytest** - `uv run pytest` (with `pytest-cov` for coverage)
- **ruff** - `uvx ruff check` and `uvx ruff format` (fix lint and formatting)
- **ty** - `uvx ty check` (type checking)

All four must pass before considering work complete.

## Commands

```
uv run pytest --cov=ceres --cov-report=term-missing   # tests + coverage
uvx ruff check --fix                                   # lint and auto-fix
uvx ruff format                                        # format code
uvx ty check                                           # type check
```
