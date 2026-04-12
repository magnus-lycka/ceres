#!/bin/sh
set -eu

uv run pytest
uvx ruff check --no-fix src
uvx ruff format --check src
uv run deptry .
uvx bandit -r src
