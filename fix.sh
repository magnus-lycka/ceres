#!/bin/sh
set -eu

uvx ruff format src tests
uvx ruff check --fix src tests
uv run deptry .
uvx bandit -r src
uv run pytest --cov --all-tests --cov-report=term-missing
