#!/bin/sh

failures=0

run() {
    label="$1"; shift
    echo ""
    echo "============================================================"
    echo "  $label"
    echo "============================================================"
    "$@" || failures=$((failures + 1))
}

run "ruff format"                   uvx ruff format src tests
run "ruff check --fix"              uvx ruff check --fix src tests
run "deptry"                        uv run deptry .
run "bandit"                        uvx bandit -r src
run "pytest (--all-tests, --cov)"   uv run pytest --cov --all-tests --cov-branch --cov-report=term-missing

exit $failures
