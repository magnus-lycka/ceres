# Plan: CharacterService — Domain Façade for Character Operations

## Problem

`routes.py` imports from nine different modules across the character domain:

```python
from ceres.character.domain.career.loader import load_careers
from ceres.character.domain.character_state import CharacterProjection, diff_summaries
from ceres.character.domain.precareer.loader import load_precareers
from ceres.character.domain.sophont import SOPHONT_NAMES, available_sophont_names, get_sophont
from ceres.character.domain.spec import spec_from_summary
from ceres.character.input_specs import SelectWorld, WorldFilterCriteria
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import ReplayError
from ceres.character.mechanism.store import SqliteCharacterBackend
```

All of these should become a single import:

```python
from ceres.character.service import CharacterService
```

`routes.py` is currently doing two jobs: mapping HTTP endpoints to character operations, and
orchestrating across the domain. The second job belongs in a service layer. The web layer
should only know about HTTP — requests, responses, templates, redirects.

The same coupling exists for any future client of the character domain (a REST API, a CLI,
an export script, tests). Each would have to re-import and re-orchestrate the same
collection of domain modules.

## Rule: CharacterService is the only entry point

All clients — the web app, uc approval tests, e2e approval tests, any future CLI or REST
API — use `CharacterService` exclusively. None of them import from
`ceres.character.domain.*` or `ceres.character.mechanism.*` directly.

The exception is unit tests for the domain and mechanism layers themselves. Those test
those layers directly by design — that is already the pattern with `CharacterDriver` and
the career rule tests.

Implementing this plan means adapting both the web app and the approval test suites to go
through the service. The existing `uc` approval tests and `CharacterDriver` migrate to
`CharacterService`; the e2e tests are written against it from the start.

## Design

`CharacterService` is a stateful object that owns the storage backend and exposes all
character operations as methods. It is instantiated once (at app startup) and injected
where needed. `build_app(service: CharacterService)` replaces
`build_app(backend: SqliteCharacterBackend)`.

### Construction

```python
service = CharacterService(database=Path('characters.sqlite'))
```

Internally it holds a `SqliteCharacterBackend` and any other long-lived state (loaded
career/precareer catalogues, world references, etc.). Passing `':memory:'` gives an
in-memory instance suitable for tests.

### Character creation wizard flow

Homeworld is selected before sophont. `create_character` creates a minimal record and
returns the character ID; the wizard then drives homeworld selection and sophont selection
as the first two pending inputs, before UCP. This means `CharacterStartedHandler` is split:
the initial event carries only `name` and `player`; homeworld and sophont arrive as
subsequent events.

Because homeworld is always the first event after creation, `birthworld` equals `homeworld`
by definition at creation time — no separate stored field is needed.

### Methods (illustrative, not exhaustive)

The web layer only ever holds a `character_id` (from the URL). It never receives or stores
a `CharacterProjection` — all projection retrieval happens inside the service.

```python
# Character lifecycle
service.create_character(name, player) -> int  # new character_id; homeworld & sophont come as wizard events
service.delete_character(character_id) -> None
service.rename_character(character_id, name) -> bool
service.list_characters() -> list[CharacterListItem]

# Read — returns presentation-ready view, never a raw projection
service.get_view(character_id) -> CharacterView | None

# History — full career narrative, derived from term notes in the summary
service.get_history(character_id) -> list[TermSummaryRow]

# Event submission — form_data is Mapping[str, str]; routes.py converts FormData before calling
service.submit_event(character_id, fulfills, form_data) -> SubmitResult
# SubmitResult carries: view, changes (diff), notes (narrative from the event just processed), error

# Catalogue queries
service.available_sophonts() -> list[str]
service.all_careers() -> list[CareerData]

# Output
service.stat_block_pdf(character_id) -> bytes
service.gallery_pdf(character_ids) -> bytes
```

### SubmitResult and the session log

`SubmitResult` carries:

- `view: CharacterView` — the updated presentation view
- `changes: list[...]` — diff between before and after (from `diff_summaries`)
- `notes: list[str]` — narrative output from `TermData.notes()` for the event just processed
- `error: str | None`

The session log currently accumulated by `CharacterDriver` during tests is derivable from
the `notes` of accumulated `SubmitResult` values — making it a first-class concept rather
than a test-only artifact.

### Presentation view

`CharacterView` is a dataclass (or small Pydantic model) whose fields map directly to what
the templates need — formatted strings, flat lists of display rows, booleans — with no
domain objects inside. Templates never import or discriminate on `CareerTerm`,
`PreCareerTerm`, `CharacterProjection`, or any other domain type.

`CharacterView` also carries the pending-input specs (`list[InputSpec]`) so the template
can render the next form without the route needing to know what kind of input is pending.

**Staging note**: The full "no domain objects" goal is reached incrementally.
`PendingInput` objects with pre-computed `input_specs` may stay in the view initially;
full flattening of summary fields into plain display types comes in a later pass.

### Open question: term notes storage vs derivation

`TermData.notes()` are currently embedded in `CharacterSummary` (stored in the DB as part
of the summary JSON). They could alternatively be derived by replaying the event log on
read. The stored approach is faster; the derived approach avoids duplication. This decision
is deferred — do not encode the current approach as final when implementing the service.

## What routes.py becomes

A thin dispatcher. Each endpoint:

1. Parses the HTTP request (path params, form data, query string).
2. Calls one `service.*` method.
3. Renders the result to an HTTP response (template, redirect, PDF bytes).

No projection retrieval, no projection-walking, no career/precareer loading, no diff
computation, no `_term_detail_rows` helpers — all of that moves into `CharacterService`.
`CharacterProjection` never appears in `routes.py`.

## Migration path

This is a larger refactor. Do it incrementally:

1. Create `src/ceres/character/service.py` with `CharacterService` wrapping
   `SqliteCharacterBackend`. Move storage calls first — easiest to isolate.
2. Move catalogue queries (`load_careers`, `load_precareers`, sophont helpers) into the
   service.
3. Move event submission and diff logic (`diff_summaries`, `build_event_from_form`, etc.).
4. Introduce `CharacterView` and the presentation adapter; migrate templates one section
   at a time.
5. Migrate `uc` approval tests and `CharacterDriver` to use the service.
6. Once routes.py imports only `CharacterService` and HTTP types, and no approval test
   touches domain internals, the migration is done.

## Files affected

- `src/ceres/character/service.py` (new) — `CharacterService`, `CharacterView`,
  `SubmitResult`, `CharacterListItem`, `TermSummaryRow`, and supporting dataclasses
- `src/ceres/character/web/app.py` — `build_app` takes `CharacterService`
- `src/ceres/character/web/routes.py` — shrinks to HTTP dispatch only; all domain imports
  replaced by `CharacterService`
- `src/ceres/character/web/templates/` — use `view.*` fields instead of `summary.*` /
  `projection.*`
- `tests/unit/character/helpers.py` — `CharacterDriver` uses `CharacterService`
- `tests/approval/character/uc/` — fixtures switch from backend to service
- `tests/approval/character/e2e/` — written against the service from the start

## Web e2e test

Once the service layer exists, add a single e2e test in `tests/approval/character/e2e/`
that drives a full character creation journey through the web client:

- Create a character (name + player only)
- Submit homeworld selection, sophont selection, UCP, background skills, a precareer
  (e.g. University), and 5 career terms
- Character ends up ~42 years old
- Snapshot the final character sheet HTML

All events are submitted via `POST /ui/characters/{id}/events` with real form data, not
by touching the backend or service directly. The test proves the full
HTTP → service → domain → template pipeline works end to end.

The test currently can't be written cleanly because routes.py mixes domain orchestration
into the HTTP layer, making monkeypatching awkward. With `CharacterService` in place,
the test will inject an in-memory service and drive the wizard purely through HTTP.
