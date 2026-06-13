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

run "pytest (--all-tests)"          uv run pytest -n auto --maxprocesses=3 --all-tests
#run "pylint (duplicate-code)"      uvx pylint --disable=all --enable=duplicate-code src tests
run "ruff check"                    uvx ruff check --no-fix src tests
run "ruff format --check"           uvx ruff format --check src tests
run "ty check"                      uvx ty check
run "deptry"                        uv run deptry .
run "bandit"                        uvx bandit -r src

exit $failures
