#!/bin/sh
set -eu

uv run pytest --all-tests
uvx ruff check --no-fix src tests
uvx ruff format --check src tests
uv run deptry .
uvx bandit -r src
