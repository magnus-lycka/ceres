#!/bin/sh
set -eu

uv run pytest --all-tests
uvx ruff check --no-fix src
uvx ruff format --check src
uv run deptry .
uvx bandit -r src
