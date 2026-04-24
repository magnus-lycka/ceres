#!/bin/sh
set -eu

uvx ruff format src
uvx ruff check --fix src
uv run deptry .
uvx bandit -r src
uv run pytest --cov --all-tests
