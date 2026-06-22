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

run "pytest (--all-tests, --cov)"   uv run pytest --cov --all-tests --cov-branch --cov-report=term-missing

exit $failures
