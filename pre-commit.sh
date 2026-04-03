#!/bin/sh
set -eu

uvx ruff check --no-fix src
uvx ruff format --check src
uv run deptry .
uvx bandit -r src
