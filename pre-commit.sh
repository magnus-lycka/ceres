#!/bin/sh
set -eu

uv run pytest --all-tests
#uvx pylint --disable=all --enable=duplicate-code src tests
uvx ruff check --no-fix src tests
uvx ruff format --check src tests
uvx ty check
uv run deptry .
uvx bandit -r src
uvx yamllint src
