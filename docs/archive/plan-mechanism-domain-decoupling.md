# Plan: Decouple character.mechanism from character.domain

## Status: Complete

## Problem

`character.mechanism` currently imports from `character.domain`, reversing the
intended dependency direction. `domain` should depend on `mechanism`, not the
other way around.

Offending imports:

```
src/ceres/character/mechanism/event_base.py:    from ceres.character.domain.character_state import CharacterProjection
src/ceres/character/mechanism/pending_input.py:    from ceres.character.domain.character_state import CharacterProjection
src/ceres/character/mechanism/replay.py:from ceres.character.domain.character_state import CharacterProjection
src/ceres/character/mechanism/store.py:from ceres.character.domain.character_start import CharacterStartedHandler
src/ceres/character/mechanism/store.py:from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
src/ceres/character/mechanism/store.py:from ceres.character.domain.event_handlers import register_event_handlers
src/ceres/character/mechanism/store.py:from ceres.character.domain.sophont import Sophont
```

There are two distinct problems bundled together.

## Problem 1: Type references to CharacterProjection

`event_base.py`, `pending_input.py`, and `replay.py` reference
`CharacterProjection` only to type the object they call methods on (e.g.
`apply()`). They do not need the concrete class — they need its shape.

**Fix:** define a `Projection` protocol in `mechanism` (e.g.
`mechanism/projection.py`). The concrete `CharacterProjection` in `domain`
satisfies it structurally; no explicit inheritance is needed. Replace the
`domain` imports in `event_base.py`, `pending_input.py`, and `replay.py` with
the protocol.

If `CharacterSummary` is also referenced only as a type, define a `Summary`
protocol alongside `Projection`.

## Problem 2: Domain wiring in store.py

`store.py` imports `CharacterStartedHandler`, `register_event_handlers`, and
`Sophont`. These are domain-level concerns: registering which handlers exist,
and knowing which sophont type to construct. That is *wiring* — an
application/composition concern — not event-store mechanism.

**Fix:** push the wiring up to a composition layer. Options:

- A new `character/app.py` (or `character/composition.py`) that is explicitly
  allowed to depend on both `mechanism` and `domain` because its job is to
  assemble them.
- Alternatively, `character/__init__.py` if it is already the public entry
  point.

`store.py` should accept a projection factory or handler registry as a
parameter rather than importing concrete domain classes. After this change,
`store.py` knows nothing about `Sophont`, `CharacterStartedHandler`, or
`register_event_handlers`.

## Intended dependency direction after the fix

```
character.domain   →  character.mechanism
character.web      →  character.domain, character.mechanism
character.app      →  character.domain, character.mechanism   (wiring only)
character.mechanism  (no domain imports)
```

## Steps

1. Define `Projection` (and `Summary` if needed) protocols in
   `character/mechanism/projection.py`.
2. Replace `CharacterProjection` imports in `event_base.py`,
   `pending_input.py`, and `replay.py` with the protocol.
3. Identify exactly what `store.py` needs from domain at runtime vs. at
   construction time.
4. Extract domain wiring from `store.py` into a composition module; pass
   dependencies in rather than importing them.
5. Verify with `uvx pydeps src/ceres/character/mechanism --show-deps` that
   no `character.domain` imports remain in `character.mechanism`.
6. Run the full test suite.
