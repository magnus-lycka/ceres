# GitHub Issues Workflow

This document describes how we want to use GitHub Issues as a work queue for
Ceres. The goal is to replace `docs/todo_maybe.md` with one queue that works for
humans, Codex, Claude Code, and pull request work.

## Why Issues?

Issues are better than a local todo file for work and planning that is:

- concrete and actionable
- worth prioritising, labelling, or discussing
- connected to code references, tests, or pull requests
- something an agent should be able to pick up and continue
- an idea or concern that we may need to reason about over time

Issues are the canonical place to track planning, progress, status, and
discussion. Documentation is still useful for durable design notes and larger
plans, but those documents should be attached to issues rather than becoming a
parallel backlog.

## What Goes Where?

Use GitHub Issues for:

- bugs
- refactors
- test gaps
- architecture and complexity findings that can be acted on
- ideas that may become future work
- design questions that need triage or a decision
- planning and progress tracking
- small and medium improvements
- tasks that should be closed by a pull request

Use `docs/plan-*.md` for:

- larger refactors
- TDD plans
- design decisions with multiple phases
- context where the reasoning matters more than the checklist

Plan documents are supporting artifacts. Every active plan should have a
tracking issue, and the issue should link to the plan document.

Do not add new work to `docs/todo_maybe.md`. Treat it as a read-only migration
ledger and temporary index. When a todo in `todo_maybe.md` is still worth
keeping, move it to an issue and add the issue reference. Keep the todo text
until work starts; once work starts, the issue becomes the single source of truth
and `todo_maybe.md` should keep only a short reference. We will decide later when
to fully retire, archive, or delete the todo file.

## Issue Template

Use this structure for most issues:

```md
## Problem

What is wrong, difficult, unclear, or accidentally complex?

## Evidence / Code References

Links to files, lines, test names, error messages, or examples.

## Desired Direction

What should the solution roughly look like?

## Acceptance Criteria

- [ ] Concrete observable condition
- [ ] Concrete observable condition
- [ ] Documentation/tests updated where needed

## Tests / Verification

Which tests, scan tests, `ruff`, `ty`, `pre-commit.sh`, or manual checks should
show that the work is complete?

## Related Plans or Docs

Links to relevant `docs/plan-*.md`, architecture documents, or earlier issues.
```

Small bugs can use a shorter template, but they should still include the
problem, acceptance criteria, and verification.

During bulk migration from `todo_maybe.md`, not every issue needs to be rewritten
into this template immediately. It is acceptable to create rough issues from the
existing todo text, then improve the issue body when the work is triaged or
started.

## Labels

Start with a small label set. Add labels when the need is clear rather than
building a large taxonomy up front.

### Area

- `area:character`
- `area:ships`
- `area:robots`
- `area:web`
- `area:tests`
- `area:docs`
- `area:tools`

### Kind

- `kind:bug`
- `kind:architecture`
- `kind:cleanup`
- `kind:feature`
- `kind:idea`
- `kind:test`
- `kind:docs`
- `kind:plan`

### Status

- `status:needs-triage`
- `status:ready`
- `status:in-progress`
- `status:needs-review`

### Size

- `size:small`
- `size:medium`
- `size:large`

### Optional

Add these only if we actually use them:

- `priority:high`
- `priority:low`
- `good-first-agent-task`
- `needs-decision`
- `has-plan`

## Recommended Flow

1. Create an issue when a problem or improvement is concrete enough.
2. Set at least `area:*`, `kind:*`, and `status:needs-triage`.
3. When the task is clear, change it to `status:ready`.
4. When someone starts work, leave a short comment and set
   `status:in-progress`.
5. Link any relevant plan document from the issue.
6. When a pull request is opened and waiting for human review, link it from the
   issue and set `status:needs-review`. Prefer `Fixes #NN` or `Refs #NN` in the
   pull request description.
7. Close the issue when the pull request is merged and the acceptance criteria
   are satisfied.

If an agent discovers that an issue is larger than expected, it should comment
with a suggested split instead of doing a large opportunistic refactor.

For loose ideas, use `kind:idea` and `status:needs-triage`. If an idea becomes a
plan, either relabel the same issue as `kind:plan` or create a plan issue that
links back to the idea issue.

## Dependencies

Use GitHub's built-in blocked/blocking relationships for dependency state.
Do not use a separate `status:blocked` label.

An issue that cannot proceed because another issue must be finished first should
remain in its normal workflow status, usually `status:needs-triage` or
`status:ready`, and should link the blocker explicitly:

```bash
gh issue edit BLOCKED_ISSUE --add-blocked-by BLOCKER_ISSUE
gh issue edit BLOCKER_ISSUE --add-blocking BLOCKED_ISSUE
```

Add a short comment explaining why the dependency exists when the relationship
is not obvious from the issue titles.

## Agent Rules

When Codex or Claude works from an issue:

- read the whole issue and linked plan documents first
- do not turn the issue into a parallel plan if a plan document already exists
- update the issue with important decisions or blocking discoveries
- keep the pull request narrow against the issue acceptance criteria
- create new issues for adjacent findings instead of mixing them directly into
  the current work
- update or archive affected docs when the work makes them obsolete

When an agent creates issues from code review:

- prefer several small issues over one large "fix architecture" issue
- include file and line references
- explain why it is a problem, not only what looks ugly
- suggest verification
- mark large uncertain items with `status:needs-triage` or `needs-decision`

## `gh` Commands

Basic checks:

```bash
gh auth status
gh repo view
gh issue list
```

Create an issue:

```bash
gh issue create --title "Short actionable title" --label area:character --label kind:cleanup
```

View an issue:

```bash
gh issue view 123 --comments
```

Comment:

```bash
gh issue comment 123 --body "Short status update."
```

Close an issue:

```bash
gh issue close 123 --comment "Fixed by #456."
```

## Migrating From `todo_maybe.md`

The target state is no active `todo_maybe.md`, but we do not need to decide the
retirement date immediately. In the transition period, `todo_maybe.md` is a
read-only migration ledger and temporary index, not a second backlog.

Plan:

- migrate all or almost all todos to GitHub Issues in one pass
- add the GitHub issue reference to each migrated todo
- keep the existing todo text in `todo_maybe.md` until work starts
- once work starts, make the GitHub issue the single source of truth
- after work starts, leave only a short reference in `todo_maybe.md`
- do not add new todo items to `todo_maybe.md`; create issues instead
- decide later when to fully retire, archive, or delete `todo_maybe.md`

Bulk-migrated issues may be rough. They can be normalised into the issue template
when they are triaged or picked up.

Good first migration candidates:

- "Character code: accidental-complexity cleanup candidates"
- "Import character-domain names from their owning modules"
- test suite profiling and coverage items

For each migrated todo:

1. Create an issue.
2. Add the issue reference next to the todo in `todo_maybe.md`.
3. Add a link to the issue in the relevant plan/doc if the plan is still active.
4. Keep the todo text in `todo_maybe.md` until work starts.
5. Once work starts, reduce the todo entry to a short issue reference.
6. Move fully completed historical todo items to `docs/archive/done_todos.md`.
7. Discard stale ideas instead of preserving them mechanically.

After migration:

- stop adding new entries to `todo_maybe.md`
- keep issue links in docs only when they help readers find current status
- archive or delete `todo_maybe.md` once nothing active remains

Mark `docs/archive/done_todos.md` as historical. It can remain useful as a record
of old local todo cleanup, but it should not be treated as a current planning
tool.

## When Not To Create An Issue

Do not create issues for:

- things already covered by an active pull request
- small fixes done directly in the same workflow that do not need tracking
- short-lived implementation scratch notes that belong in the current branch or
  pull request

If we may want to reason about planning, priority, status, or progress later,
create an issue. Use `kind:idea` for things that are not yet actionable.
