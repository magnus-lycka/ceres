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

run "ruff check --fix"              uvx ruff check --fix src tests
run "pytest (--all-tests)"          uv run pytest -n auto --maxprocesses=3 --all-tests
#run "pylint (duplicate-code)"      uvx pylint --disable=all --enable=duplicate-code src tests
run "ruff format --check"           uvx ruff format --check src tests
run "ty check"                      uvx ty check
run "deptry"                        uv run deptry .
run "bandit"                        uvx bandit -q -r src

# The Svelte front end. Skipped rather than failed when its dependencies are
# not installed, so a clone that only works on the Python side still gets a
# usable gate; run `npm install` in web/ to switch these on.
if [ -d web/node_modules ]; then
    run "web: eslint --fix"         npm --prefix web run --silent lint:fix
    run "web: prettier --check"     npm --prefix web run --silent format:check
    run "web: svelte-check"         npm --prefix web run --silent check
    run "web: vitest"               npm --prefix web run --silent test
    run "web: build"                npm --prefix web run --silent build
else
    echo ""
    echo "============================================================"
    echo "  web: skipped (run 'npm install' in web/ to enable)"
    echo "============================================================"
fi

exit $failures
