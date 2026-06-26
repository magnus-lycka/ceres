# Plan: Approval Testing for Complex State Deltas

## Decision

**Syrupy (Option B) is the chosen approach.** The inline-snapshot vs. Syrupy
experiment is complete. Use Syrupy with `JSONSnapshotExtension` for all complex
state-delta approval tests. Do not implement Option C (custom fixtures).

The snapshot update workflow is `pytest --snapshot-update`. Snapshot files live
under `__snapshots__/` beside the test file, committed to the repository.

## Concept

Approval testing is a methodology where the assertions in a test evolve by
inspection rather than being hand-written up front. The workflow is:

1. Write the test structure (setup + action) — this is the TDD part, done first
2. Run the test; the first run captures the current output as the *approved*
   reference
3. Write the code under test (or run on existing code to capture baseline)
4. Run the tests; the framework compares current output to the approved reference
5. For each test where current output differs from the reference, the developer
   reviews the diff and decides: **approve the new output** (it is correct) or
   **keep the old reference** (the change is a regression)
6. Approved references are committed to the repository

The key difference from classical TDD red-green-refactor: the test assertions
are not written before the code. Instead, the test *structure* is written first
and the assertions are captured from a run and then evolved by inspection. A
change in output is not automatically a failure — it is a *signal* that requires
human judgement. A zero diff when you expected a change is also a failure.

## When to Use Approval Tests

Approval tests are appropriate for **multi-effect events** where the complete
state delta — including the guarantee that nothing unexpected changed — is the
invariant under test. Examples:

- Scholar event 3 (accept): creates 2 skills, D3 enemies, defers a benefit roll,
  replaces a pending
- A complex mishap with several simultaneous effects
- Any handler that touches 3+ distinct parts of the projection

They are **not** appropriate for single-effect actions. Those get plain
assertions using `CharacterDriver`. The bar for an approval test is: "I care
that *only* these things changed, not just that these things changed."

## Implementation Options

Before building custom approval infrastructure, evaluate whether
[`inline-snapshot`](https://pydantic.dev/articles/inline-snapshot) covers enough
of the workflow.

`inline-snapshot` stores the approved value directly in the test source and can
update it with `pytest --inline-snapshot=fix`. For this project, the value under
approval would usually be a normalised `projection_diff(before, after).to_dict()`
rather than the full projection.

Example shape:

```python
from inline_snapshot import snapshot


def test_scholar_event3_accept_full_delta():
    d = _setup_to_event_3_choice()
    before = d.snapshot()

    d.career_choice(ScholarEvent3Accept)
    d.connections_roll(1)
    d.choose_career_skill(SpaceScience(planetology=Level(value=1)))
    d.choose_career_skill(LifeScience(biology=Level(value=1)))
    d.name_connection()

    assert stable_projection_diff(before, d.projection) == snapshot({...})
```

The expected helper would:

- call `projection_diff(before, after).to_dict()`
- convert Pydantic objects to built-in JSON-compatible values
- normalise volatile event IDs, especially `pending_id[0]` values
- optionally use `dirty-equals` matchers for values that should satisfy a shape
  rather than equal a literal

### Option A: Inline snapshots

Advantages:

- much less custom tooling than a bespoke approval system
- approved expectations live beside the scenario setup
- ordinary pytest failures show the mismatch
- updates use an existing workflow instead of a custom review command
- works well with focused diffs of complex Python data structures

Risks:

- large snapshots can make test files bulky
- reviewers must still inspect generated updates carefully
- volatile value handling needs a small normalisation helper
- if snapshots become very large, separate fixture files may be easier to review

Evaluation criteria:

- Convert one existing `projection_diff` test, preferably Scholar event 3
  accept, to `inline-snapshot`.
- Confirm that normal pytest runs fail cleanly on mismatch.
- Confirm that `pytest --inline-snapshot=fix` updates only the expected
  snapshot.
- Confirm that event IDs and other volatile values are stable after
  normalisation.
- Compare review ergonomics against the current inline expected-dict style.

### Option B: Syrupy snapshots

Evaluate [`syrupy`](https://syrupy-project.github.io/syrupy/) if inline
snapshots make test files too bulky or if separate reviewed fixture files feel
better for large character deltas.

Syrupy is a pytest snapshot plugin. It stores approved values in snapshot files
under `__snapshots__` and updates them with `pytest --snapshot-update`.

Example shape:

```python
from syrupy.extensions.json import JSONSnapshotExtension


def test_scholar_event3_accept_full_delta(snapshot):
    d = _setup_to_event_3_choice()
    before = d.snapshot()

    d.career_choice(ScholarEvent3Accept)
    d.connections_roll(1)
    d.choose_career_skill(SpaceScience(planetology=Level(value=1)))
    d.choose_career_skill(LifeScience(biology=Level(value=1)))
    d.name_connection()

    assert stable_projection_diff(before, d.projection) == snapshot(
        extension_class=JSONSnapshotExtension
    )
```

Advantages:

- no custom approval fixture or review tool needed for basic snapshot workflow
- snapshots live outside test files, which may be better for large diffs
- built-in snapshot update command
- supports matchers and excludes for dynamic values
- JSON snapshot extension may suit `projection_diff(...).to_dict()` output

Risks:

- confirm compatibility with the project's pytest version before adopting
- review requires jumping between test and snapshot file
- snapshot files add another artifact type to maintain
- matchers/excludes may be less readable than explicit normalisation helpers

Evaluation criteria:

- Verify Syrupy works with the current pytest version used by the project.
- Convert the same candidate test used for the inline-snapshot experiment.
- Compare generated snapshot readability against the inline snapshot version.
- Confirm update workflow with `pytest --snapshot-update`.
- Check how unused/orphaned snapshots are reported.

### Option C: Custom approval fixtures

The custom fixture/review-tool approach below remains a fallback if inline
snapshots and Syrupy are both too noisy or too limited. It gives more control
over fixture file layout, volatile path metadata, and interactive review, but it
also creates project-specific infrastructure to maintain.

Do not implement Option C until Options A and B have each been tried on at least
one complex state-delta test.

## Custom Approval Architecture

### Fixture files

Approved references live in `tests/character/approvals/`. Each approval test
has a corresponding JSON fixture file named after the test:

```text
tests/character/approvals/
    test_scholar_event3_accept_full_delta.json
    test_scholar_event3_decline_full_delta.json
    test_scholar_mishap5_give_up_full_delta.json
    ...
```

The file is named by the test's approval key (see test structure below). Files
are committed to the repository and treated as the approved reference. A missing
file means the test has no approved reference yet; the first run that produces
output will create it (pending human approval).

### Fixture format

Each fixture is a JSON object with two sections:

```json
{
  "volatile_paths": [
    "root['pending_inputs'][0]['pending_id'][0]"
  ],
  "approved_diff": {
    "values_changed": {
      "root['pending_inputs'][0]['kind']": {
        "old_value": "pending_choices",
        "new_value": "pending_advancement"
      }
    },
    "iterable_item_added": {
      "root['summary']['connections'][0]": {
        "kind": "connection_enemy",
        "origin": "Scholar event 3"
      }
    }
  }
}
```

`volatile_paths` lists DeepDiff path strings that are excluded from the
comparison. Their presence in the diff is expected, but their values are not
checked. Typical volatile paths: `pending_id[0]` entries (auto-generated event
IDs), and any path that embeds a timestamp or generated identifier.

`approved_diff` is the expected DeepDiff output as a plain dict (the result of
`DeepDiff(...).to_dict()`), with volatile paths already removed.

### Test structure

Approval tests use a pytest fixture called `approval`:

```python
@pytest.mark.approval
def test_scholar_event3_accept_full_delta(approval):
    d = _setup_to_event_3_choice()
    before = d.snapshot()
    d.career_choice(ScholarEvent3Accept)
    d.connections_roll(1)
    d.choose_career_skill(SpaceScience(planetology=Level(value=1)))
    d.choose_career_skill(LifeScience(biology=Level(value=1)))
    d.name_connection()
    approval.assert_matches(before, d.projection)
```

The `approval` fixture:

- Derives the fixture key from the test node id (module + function name)
- Loads the corresponding fixture file from `tests/character/approvals/`
- Calls `projection_diff(before, after)` to get the current diff
- Strips volatile paths from the current diff
- If no fixture exists: records the current diff as a *pending* approval (test
  is marked as requiring review, not a hard failure)
- If a fixture exists: compares current diff (minus volatile paths) to
  `approved_diff`; fails the test if they differ

### The `approval` pytest fixture

Implemented in `tests/character/conftest.py` or `tests/character/helpers.py`.
The fixture receives the test's `request` to derive its key:

```python
@pytest.fixture
def approval(request):
    return ApprovalContext(request.node.nodeid)
```

`ApprovalContext.assert_matches(before, after)` does the comparison. It
exposes the current diff on the context object so the review tool can display
it.

## The Review Tool

The interactive review tool is a standalone script invoked as:

```shell
uv run python -m ceres.tools.approval_review
```

or via a pytest plugin option:

```shell
uv run pytest --approval-review tests/character/
```

### Behaviour

The tool:

1. Runs all `@pytest.mark.approval` tests (collecting results without failing)
2. Finds all tests where current output differs from the approved reference
   (including tests with no approved reference yet)
3. For each such test, **in sequence**:
   - Prints the test name and a brief description if available
   - Prints the diff between the *approved* fixture and the *current* output,
     formatted as a readable JSON diff
   - Prints a summary line: which paths were added, removed, or changed
   - Prompts: `[A] approve new  [K] keep old  [S] skip  [Q] quit`
4. On `A`: writes the current diff (minus detected volatile paths) as the new
   approved fixture and prints "Approved."
5. On `K`: leaves the fixture unchanged; the test will continue to fail
6. On `S`: skips without changing anything (can come back later)
7. On `Q`: exits immediately without changing anything

After processing, prints a summary: N approved, M kept as failing, P skipped.

### Display format

The diff displayed to the reviewer should be human-readable. Use `rich` (already
a project dependency) to render the JSON with colour: additions in green,
removals in red, unchanged context in grey. Show the full diff of the fixture,
not just a summary.

If the test has no approved fixture yet, display: `(new test — no previous
reference)` and show the full current diff as the candidate.

### Volatile path detection

When approving a new reference, the tool automatically identifies likely volatile
paths (any path whose value is an integer >= 1,000,000, which is the auto-id
range for `Event.id`) and adds them to `volatile_paths` in the fixture. The
developer can override this manually by editing the fixture file.

## Workflow

### First time: capturing a baseline

1. Write the test function with `@pytest.mark.approval` and call
   `approval.assert_matches(before, after)`. No fixture file exists yet.
2. Run `uv run pytest --approval-review`.
3. The tool shows the current diff for the new test.
4. Inspect it. If the output looks correct, press `A`.
5. The fixture file is created and committed.

### After a code change

1. Run `uv run pytest` (normal run). Approval tests fail if output changed.
2. Review failures: run `uv run pytest --approval-review`.
3. For each changed test: inspect the diff, decide whether the change is
   intentional (A) or a regression (K).
4. Commit updated fixture files alongside the code change.

### In CI

`uv run pytest` is used as normal. Any approval test failure (fixture mismatch
or missing fixture) fails the build. The developer must review and approve
before merging.

## Fixture file hygiene

- Fixture files are version-controlled. A PR that changes behaviour should
  include updated fixture files.
- If a test is deleted, its fixture file should be deleted too. The review tool
  can report orphaned fixture files.
- Fixture files should be reviewed in code review like any other test assertion.
  A sweeping "approve all" is a smell.

## Migration from current projection_diff tests

The two existing `projection_diff` tests in `test_scholar.py` and the one in
`test_scholar.py` (`TestScholarMishap5.test_give_up_state_delta`) are candidates
for migration. The migration steps:

1. Convert each test to the `@pytest.mark.approval` structure
2. Run `--approval-review`; inspect and approve the captured fixtures
3. Delete the old inline expected-dict assertions
4. The fixture files replace those embedded dicts

The resulting tests will be shorter, cleaner, and the references will be easier
to update when Scholar event 3 behaviour changes.

## Phases

### Phase 1: Core infrastructure (minimum viable)

- `ApprovalContext` class in `tests/character/helpers.py` or a new
  `tests/character/approval.py`
- `approval` pytest fixture in `conftest.py`
- Fixture file load/compare logic
- `@pytest.mark.approval` registration in `pyproject.toml`
- Tests run and fail on mismatch; no interactive tool yet (mismatch message
  shows the diff as text)

### Phase 2: Review tool

- `ceres/tools/approval_review.py` (or pytest plugin)
- Iterate over failing approval tests, show diff, prompt A/K/S/Q
- Auto-detect volatile paths on approval
- `rich` rendering for readable diffs

### Phase 3: Migration and guidance

- Migrate existing `projection_diff` tests to the new structure
- Remove the old `projection_diff` helper (or keep it as the underlying
  primitive used by `ApprovalContext`)
- Document in CLAUDE.md: when to use approval tests, when to use targeted
  assertions
- Add orphaned-fixture detection to the review tool

## Open questions

- **Where does the review tool live?** As a pytest option (`--approval-review`)
  or as a standalone script (`uv run python -m ceres.tools.approval_review`)?
  The pytest option is more discoverable; a standalone script is simpler to
  implement. Either works in phase 2.

- **Should approval tests be slow-marked?** They run the full projection replay
  and compute a deep diff. Likely fast enough for the default suite, but worth
  monitoring. If they become slow, add `@pytest.mark.slow`.

- **Normalising event IDs vs. volatile_paths list?** The plan uses an explicit
  volatile_paths list per fixture. An alternative is to normalise the JSON dump
  before diffing (replace all pending_id[0] values with stable sequential
  tokens). Normalisation is cleaner but more complex to implement and debug.
  Start with the explicit list; revisit if it becomes tedious.
