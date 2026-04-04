#!/bin/sh
set -eu

uvx ruff check --fix src
uvx ruff format src
uv run deptry .
uvx bandit -r src
uv run pytest --cov
