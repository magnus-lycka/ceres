# Working Agreement

How Magnus and Claude build `ceres.rounds`. Magnus drives user experience and
decides what the app should do. Claude writes the code and is responsible for
keeping it changeable — the goal is not to follow a plan but to be able to
change direction cheaply, without breaking what already works.

This document is about *how we work*. Traveller rule decisions belong in
[RULE_INTERPRETATIONS.md](RULE_INTERPRETATIONS.md); code structure belongs in
[ARCHITECTURE.md](ARCHITECTURE.md).

## The loop

One small change at a time, each ending in something Magnus can look at.

1. **Magnus names a change.** Usually a sentence, often about what the screen
   should do.
2. **Claude makes exactly that change**, with tests, and runs the gate.
3. **Magnus looks at it** and says what is wrong.
4. **Commit** when it is right, then repeat.

A turn that ends with "here are six things I also built" has broken the loop:
it gives Magnus six things to judge instead of one, and hides the change he
asked about.

## Scope

**Implement what was asked, not the neighbourhood around it.** An unrequested
feature is a defect — it costs a round trip to remove, and it implies the
request was incomplete when it was not.

When adjacent work looks necessary, name it in one sentence and let Magnus
decide. When a request could mean two things — "X instead of Y" or "X as well
as Y" — ask. One line of question beats a rewrite.

This cuts the other way too: deliver the *whole* of what was asked. If part of
it turns out to be blocked, finish the rest and say plainly what was left out.

## Reading before writing

Read a file's existing conventions before adding to it. This applies to
documents as much as to code: identifiers, section structure and purpose are
all discoverable, and guessing at them produces edits that have to be reverted.

`RULE_INTERPRETATIONS.md` is for Traveller rules only — a vague rule that needs
a reading, an option where we chose one, or a deliberate deviation. Code design
decisions do not go there. They go in the module that implements them, or in
`ARCHITECTURE.md` if they are cross-cutting.

## What keeps change cheap

Claude is responsible for these. They are not style preferences; they are what
lets us rewrite a screen on a Tuesday without archaeology.

- **One definition of the model.** `schema/actor.ts` is the single zod
  definition that produces the TypeScript types, the runtime validation and the
  JSON Schema. A second definition anywhere is a drift bug waiting.
- **Rules know nothing about the UI.** Nothing under `$lib/rules/**` imports
  Svelte or touches the DOM. That boundary is what makes the rules testable in
  milliseconds and survivable across a UI rewrite.
- **Boundaries are drawn in application concepts, not vendor ones.**
  `ActorGrid` takes actors and reports the selected actor; the page above it
  never sees a column definition, a cell context or a row index. Replacing
  SvGrid means rewriting `ActorGrid` — a bounded, comprehensible job — and
  leaves the rest of the application alone.

  This is *not* a claim that grid libraries are interchangeable. They are not:
  column vocabulary, editors, renderers, clipboard hooks and row semantics
  differ deeply, and that is where nearly all the coupling lives. A generic
  wrapper taking `columns: unknown[]` does not contain that coupling, it
  **conceals** it — the caller writes vendor-shaped objects with the types
  switched off. We had exactly that, and typing the columns properly
  immediately exposed three latent bugs it had been hiding. Depend on SvGrid
  openly, with its types, in one named place.

  The useful target is a bounded replacement, not a nominal one-file swap. A
  shared vendor-specific component is worth extracting when several grids need
  identical setup — for consistency and central configuration, not for
  interchangeability. Not yet: there is one grid.
- **Tests assert behaviour, not structure.** A test that breaks because an
  internal detail moved — while observable behaviour did not — is at the wrong
  level and will make change expensive rather than safe.
- **Delete rather than deprecate.** Alpha software, one user, no deployed data.
  No shims, no compatibility aliases, no archived state.

## Technical debt

Claude raises debt when it is created, not later. If a change needs a shortcut,
say so in the same turn and name the cost. Known-broken behaviour is never
papered over to keep the suite green — a red test is useful information.

Two specific habits, both learned the hard way:

- **Look at the screen before claiming a screen works.** The type checker
  cannot see a blank grid, a wrong height, or a page laid out badly.
- **Write a correction down when it lands**, not at the end of the session.
  Conversational corrections degrade when context is summarised; what survives
  is what is on disk.

## Quality gate

`./pre-commit.sh` is the whole gate and must pass before a commit. On the web
side it runs, in order: `eslint --fix`, `prettier --check`, `svelte-check`,
`vitest`, `vite build`. See [DEVELOPMENT_AND_TESTING.md](../DEVELOPMENT_AND_TESTING.md).

The web tests are two suites, split by what they need:

- **`rules`** — pure functions over plain data, in Node. Milliseconds. This is
  the suite to keep large; the Traveller rules live here.
- **`components`** — Svelte rendered in real Chromium. Seconds. For what a type
  checker cannot see: does the grid show its data, does the panel offer the
  right controls, does an edit reach the caller.

`npm run coverage` reports on `src/lib`. Coverage is a signal about untested
behaviour, not a number to optimise.

## Commit rhythm

Commit at every green gate. Long uncommitted stretches remove the cheap review
point and let mistakes pile onto unreviewed work — the diff *is* the unit
Magnus reviews. Claude proposes the commit; Magnus decides when to make it.
