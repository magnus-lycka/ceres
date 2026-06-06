# Architecture

## Core patterns

### Pydantic models

The core models are ordinary Pydantic `BaseModel` subclasses. In practice we
still treat them as design declarations plus derived values, but they are not
globally frozen.

### Parts expose numeric values

`ShipPart` exposes `cost`, `power`, and `tons` as the public numeric API.
Simple ad hoc parts can still store those as ordinary `float` fields, while
domain part families generally expose them as properties computed from design
state and the bound ship context. Binding must not copy derived values back onto
frozen parts as cached fields.

`tons` in Traveller ship design means **displacement tons** (`dTons`), not
metric mass. One displacement ton is a volume measure: the volume occupied by
one metric ton of liquid hydrogen, conventionally about 14 cubic metres. In
other words, Ceres' tonnage model is volumetric. A part's `tons` field answers
"how much ship displacement / internal volume does this consume or represent?",
not "how many kilograms does it weigh?".

As a house rule for cargo realism, we also assume that one displacement ton of
cargo space normally yields about one metric ton of practical net payload. This
is not a geometric truth about every possible cargo, but it keeps Traveller's
trade assumptions in a usable range and avoids treating `dTons` of cargo as if
they were magically much denser than the hydrogen-reference volume.

### Operation fuel and endurance

The detailed policy for `OperationFuel` belongs in
`RULE_INTERPRETATIONS.md`. In short, `weeks` is treated as a minimum requested
endurance, and the design may end up displaying a longer actual endurance once
tankage has been rounded according to the current rules interpretation.

### Two-phase construction: creation then binding

Parts are created as plain Pydantic models. `Ship.model_post_init()` then calls
`part.bind(ship)` on every installed part, which sets the owner, validates TL
requirements, records the part label notes, and prepares any armoured-bulkhead
companion part. Ship-dependent numeric logic lives in `cost`, `power`, and
`tons` properties and is only reliable after binding when it needs assembly
context.

### JSON roundtripping

A complete ship design must serialize to JSON and deserialize back to a
functionally identical ship — same structure, same types, same field values.
This is a core feature: designs are stored, transferred between systems, and
loaded as templates. Serialized ships are also used for rendering (HTML, PDF)
without re-running Python-side business logic.

`tests/make/ship/test_serialization.py` is the explicit guardian of this contract.
As the codebase evolves, that file must be kept current: any new field or
polymorphic type that matters to a ship's identity must have a roundtrip test.

The markdown rendering path is being phased out in favour of the HTML and PDF
transforms, which means JSON becomes the primary regression artefact. Future
feature tests should verify correctness through JSON comparison wherever
possible, integrating roundtrip verification into the feature test rather than
treating it as a separate concern.

Polymorphic fields use Pydantic discriminated unions so the correct concrete
type is resolved during deserialization. `armour` and `stealth` on `Hull` use
`description` as the discriminator. Any new polymorphic field must follow the
same pattern — add a `Literal` discriminator field to each subclass and annotate
the union with `Field(discriminator=...)`.

### Derived data in model JSON

Derived values (`cost`, `power`, `tons`) are generally excluded from JSON for
computed part families. JSON represents the design inputs, not cached output
from a previous bind. On deserialization, stale numeric values for computed-only
parts are ignored and the public properties recompute from the design and bound
ship context. Explicit design tonnage or cost still serializes through the
public input name where that number is actually part of the design.

### Tech level model

The intended conceptual model is:

- `ship.tl`: the ship's TL
- `part.tl`: the part's own technology level / variant TL

In the common case, `part.tl` is also the required ship TL for installing that
part. However, those are still different ideas and should not be conflated in
the design.

Customisation grades such as `Early Prototype`, `Prototype`, `Budget`,
`Advanced`, `Very Advanced`, and `High Technology` do **not** change what part
the thing is. A TL12 fusion plant remains a TL12 fusion plant. A TL10 beam
laser remains a TL10 beam laser. Customisation instead changes how the part may
be used and with what consequences: altered ship-TL requirement, cost, tonnage,
power, fuel use, notes, and similar effects.

Some subsystems may also care about `ship.tl` separately from `part.tl`. The
most obvious example is sensors, where the installed sensor package has its own
TL floor but some capabilities or notes may still depend on the ship's TL.

In the code, ordinary parts should expose `part.tl` and check themselves
against `self.ship.tl`. Customisable parts keep the same `part.tl` and let the
chosen customisation decide whether that part may be used on the current ship
TL and whether any warnings should be attached.

Ceres currently supports ship TL16 and lower. We cap `ship.tl` at 16 and do
not attempt to model TL17+ features for now.

### Notes and validation

Errors, warnings, and informational messages are stored as `Note` objects on
the part or ship that detected the problem. Intrinsic notes are created during
`model_post_init()` from `build_item()` and `build_notes()`. Context-dependent
validation adds later notes without clearing the earlier ones. This is
intentional: if something triggers duplicate or strange notes, that should be
visible instead of being masked by a note-reset step. Notes with category
`ITEM` are special: they carry the human-readable row label for the stat
sheet.

### Hull

`HullConfiguration` defines hull properties (streamlining, cost modifier, hull
points modifier, usage factor, etc.). Seven predefined configurations exist as
module-level instances (`standard_hull`, `streamlined_hull`, `planetoid`, etc.)
and can be modified further with flags such as `reinforced`, `light`, and
`military`.

`Hull` combines a `HullConfiguration` with optional armour, optional stealth,
and optional surface options (`heat_shielding`, `radiation_shielding`, `reflec`).
Armour and stealth are discriminated unions keyed by their `description` fields
so the Python API remains natural while roundtrip serialization still resolves
the correct concrete type.

### Ship aggregation

`Ship` owns the full installed-part graph and aggregates ship-level values such
as power budget (available, load by category), production cost, sales price,
cargo, crew roles, and operating expenses. `build_spec()` produces the
structured `ShipSpec` used by the HTML/PDF/Typst renderers and JSON regression
artifacts. These remain ship-level concerns rather than cached part data.

The installed-part graph is now section-based rather than mostly flat:

- `hull`
- `drives`
- `power`
- `fuel`
- `command`
- `computer`
- `sensors`
- `weapons`
- `craft`
- `habitation`
- `systems`
- `cargo`

### Collections vs parts

Ceres should model a **thing** as a thing, and a **collection of things** as a
collection. We should avoid hybrid models where one object tries to be both a
particular installed thing and a counted bag of such things at the same time.

In practice, that means we prefer:

- `list[Stateroom]` rather than a synthetic `Staterooms(count=...)`
- `ShipCrew.roles: list[CrewRole]` rather than a role object with `count=...`
- `list[Turret]`, `list[Vehicle]`, `list[SpaceCraft]`, and similar lists of
  concrete objects rather than "one turret / one craft / one vehicle with
  `count=X`"

Grouping and `× N` presentation belong in the spec / rendering layer, not in
the domain model.

Some facilities and magazines still have a `count` field where the rules define
a single installed facility that contains a number of identical sub-items. That
is different from making one object stand in for many independently installed
parts, and it should not be copied as a pattern for new repeated ship parts or
occupants.

### Carried craft and external loads

Internally carried craft use dedicated ship volume. For `Internal Docking Space`
or `Full Hangar`, the mothership pays the tonnage and cost of the docking /
hangar facility, while the carried craft itself contributes only its own cost
to the spec. The carried craft's own fuel, cargo, and other internal resources
are not added separately to the mothership spec.

For internal carriage, the facility's displacement already includes the carried
craft in volumetric terms. A `Full Hangar (95 tons)` has the same total
displacement whether it currently contains a `Passenger Shuttle` or stands
empty, because the shuttle fits inside that reserved internal volume. Likewise,
an `Air/Raft` occupying a `Docking Space (5 tons)` does not add another 4
displacement tons on top of the docking-space row; the craft fits within that
allocated internal space.

Externally carried craft or cargo are different. For systems such as docking
clamps, tow cables, cargo nets, external cargo mounts, jump nets, jump shuttles
and similar arrangements, the attached load must be treated as extra effective
displacement when assessing drives and other displacement-sensitive performance.
This is not yet modelled in code.

Docking clamps are therefore different from hangars or internal docking spaces:
the clamp itself has its own displacement, but a craft attached to it during
flight remains an additional external load whose displacement must still be
handled by the carrying ship.

When we later model crew effects from carried craft, a single
`engineering_tonnage` figure on the carried-craft data is likely sufficient for
Ceres' purposes. That value should be understood as the total drives-plus-power
engineering burden relevant to engineer staffing, not as a narrower physical
"drive mass" figure.

When we add these external-load systems, we will likely want some form of
parameterized spec output, so a design can state performance at one or more
extra carried displacements, such as “Thrust X / Jump Y while carrying Z dTons”.

Just as important, "relevant displacement" is not always the same for every
calculation. A design may have:

- a structural / design displacement used for hull, internal space budgeting,
  most maintenance, and the ship's own crew rules
- an effective in-flight displacement used for thrust, jump, fuel use, and
  other performance calculations while carrying external loads or certain
  detachable modules

This distinction matters for examples such as modular cutters, detachable
modules, docking clamps, jump shuttles, drop tanks, and jump nets. A ship can
be one size as a design object and another size for a specific flight profile.
Ceres should therefore avoid assuming that a single displacement value is
always correct for every rule.

### Armour

`Armour` extends `ShipPart` with derived cost and tonnage. Tonnage scales with
displacement and a per-type `_tonnage_consumed` constant; small ships (< 100 t)
get a size-factor multiplier. Each concrete armour type enforces its own
protection limits and minimum TL via `check_protection_limit()`.

### Weapons

`FixedMount` and the turret classes compose weapon value objects. Weapon models
carry their own cost/power characteristics while the mount applies mount-level
rules such as firmpoint reductions or turret mount overhead. `WeaponsSection`
owns capacity checks such as hardpoints versus firmpoints and the small-craft
restriction to single turrets.

### Software

`SoftwarePackage` is a separate hierarchy from `ShipPart` — software has no
tonnage or owner-binding. `Computer.can_run()` checks bandwidth against the
computer's processing rating; `Core` computers have unlimited jump control
bandwidth. A computer automatically includes `Library`, `Manoeuvre/0`, and
(from TL11) `Intellect` in its software list.

`ComputerSection` normalizes installed software as singleton families. For
packages such as `Jump Control`, `Evade`, `Fire Control`, and `Auto-Repair`,
only the highest installed rating counts for cost and capability. Lower
redundant entries are not kept as active packages; instead, the retained
package gets a warning note describing the redundancy.

Cross-checks between `JumpDrive` and `Jump Control` are initiated from
`Ship.model_post_init()` but owned by the relevant sections:

- `DriveSection` warns on the jump drive if control software is missing or too weak
- `ComputerSection` warns on jump control software if there is no jump drive or
  the drive rating is lower than the software rating

### Crew

`Ship.crew` is now a dedicated sub-object. It holds explicit crew input
(`roles`) and crew-specific notes, so crew-related messages do not have to be
stored at ship level and filtered back into the crew table later.

Crew rows in the spec represent rule-indicated positions / functions, not
necessarily unique individuals. A single sophont (or sometimes robot) may
fulfill more than one of these positions in practice.

Automation and equipment can impact crew needs, e.g. with Starhip Automation
(Traveller Companion.)

`ShipCrew()` means Ceres should derive the recommended crew from the ship
rules. `ShipCrew(roles=[])` is an explicit design statement that no crew are
modelled. Ceres should not silently turn an explicit empty crew list into a
pilot, steward, or other crew member for salary or accommodation purposes.

### Occupants

Ship occupants are sophonts on the ship who are not cargo. Occupant is not a
synonym for passenger. It is the broader domain concept used when asking what
living, working, travelling, or frozen bodies need from the ship.

Occupants are typically crew or passengers:

- Crew are the people doing ship work, whether they are pilots, engineers,
  stewards, bartenders, hair stylists, or anyone else whose role is part of
  running or serving the ship.
- Passengers are people being transported or hosted rather than working as crew.
  Owners and guests count as passengers in practice unless they are explicitly
  also crew.
- Troops may technically be neither crew nor normal passengers when they are
  simply being transported. They usually live like troops, for example in
  barracks, so they should not be treated as ordinary passenger stateroom
  demand.
- Low passage and frozen watch are passenger and crew-adjacent cases
  respectively, but for accommodation and operations they are frozen bodies.
  They cost Cr100 per maintenance period to keep alive. They do not eat, bother
  stewards, create normal mess, or perform crew tasks while frozen. A frozen
  watch member is therefore not crew in any practical operational sense until
  thawed.

`occupants.py` models this distinction. Occupants declare residence demand, and
rooms declare what they provide. This is why the residence allocator knows not
to casually mix crew and passengers in the same cabin and can prefer, for
example, single-occupancy staterooms for high passage before consuming
double-occupancy passenger capacity.

### Reporting and rendering

`ceres.report` is a template execution engine with three public functions:

```python
render_html(template_path: Path, context: dict) -> str
render_typst_source(template_path: Path, data: dict) -> str
render_pdf(template_path: Path, data: dict, *, page_size: str = 'a4') -> bytes
```

The engine has **no domain imports** — it may not import from `ceres.gear.*` or
`ceres.make.*`. This keeps the dependency direction clean: domain code calls the
engine, never the reverse.

Each domain that needs output owns:

- **A context builder** — a Python function that converts domain objects into a
  plain `dict` of strings, numbers, lists, and dicts. This is the boundary
  between domain logic and presentation.
- **Template files** — Jinja2 `.html.j2` for HTML, Typst `.typ` for PDF. These
  live alongside the domain code, not inside `ceres.report`.

Current rendering entry points:

- **Ships**: `ceres.make.ship.report` — builds context from `ShipSpec` and
  renders via `ceres.report.render`. Templates live in
  `ceres/make/ship/templates/`.
- **Gear catalog**: `ceres.gear.catalog` — builds context from computer
  equipment objects and renders via `ceres.report.render`. Templates live in
  `ceres/gear/templates/`.

`ceres.report` also re-exports the ship render functions as a convenience API
(via thin shims) so callers can do `from ceres.report import render_ship_pdf`.

#### HTML rendering (Jinja2)

`render_html` creates a Jinja2 environment with `autoescape=True` and
`StrictUndefined`. The template search path includes both the caller's directory
and `ceres/report/templates/` so templates can import from a shared base.
Custom filters `fmt_cost` and `fmt_mass` are registered on the environment.

#### PDF rendering (Typst)

`render_pdf` / `render_typst_source` serialize the context dict to a Typst
data preamble (`#let report_data = (...)`), prepend it to the template source,
write the combined file to a temp directory, and compile it with
`typst.compile()`. The Typst package `@preview/gentle-clues` is used for
error/warning/content/info admonition boxes, grouped by severity and role
(error → warning → content → info) within each call site.

## Rules interpretations

Cross-cutting rule decisions, intentional deviations, and interpretation notes
should now be recorded in [RULE_INTERPRETATIONS.md](/Users/magnuslycka/work/ceres/docs/RULE_INTERPRETATIONS.md).
Keep this section focused on high-level policy and only repeat details here
when they are needed to understand the architecture.

Source-to-test-case normalization rules for external ship designs should be
recorded separately in [TEST_CASE_ASSEMBLIES.md](/Users/magnuslycka/work/ceres/docs/TEST_CASE_ASSEMBLIES.md).

Ceres targets **Mongoose Traveller 2nd Edition (MgT2)**, specifically the
*Core Rulebook* and *High Guard* (2022 update). Where the two books conflict,
**High Guard takes precedence**. Material from earlier MgT2 printings that
was removed or replaced in 2022 is out of scope; see RIS-008 in
`RULE_INTERPRETATIONS.md`.

We have studied Mark F. Anderson's ship design tool output and other external
sources, but cross-cutting decisions such as unsupported drive cost reduction
labels and unsupported retro starship computer pricing should now be recorded
in `RULE_INTERPRETATIONS.md` rather than duplicated here.

## Character creation, the ceres.character package

Architecture notes specific for ceres.character

### Character creation: event sourcing

Character creation is modelled as an event-sourced projection. An event log is
replayed from the beginning to produce the current `CharacterProjection`. Events
are immutable records of what happened; the projection is rebuilt on every
replay.

#### Event and handler

The mechanism layer owns two thin container types:

```python
class Event(BaseModel):
    id: int = 0                            # assigned by store on append
    fulfills: tuple[int, int] | None = None
    handler: EventHandlerBase

class EventHandlerBase(BaseModel):
    def apply(self, projection, event, fulfilled_pending=None): ...
```

**The handler is the payload.** There is no separate payload dict. Every
concrete event type is a subclass of `EventHandlerBase` that carries typed
fields *and* implements `apply()`. These subclasses live exclusively in the
relevant domain module — never in the mechanism layer.

```python
# In career_data.py (domain)
class SurviveHandler(EventHandlerBase):
    kind: Literal['survive'] = 'survive'   # Pydantic discriminator only
    roll: int

    def apply(self, projection, event, fulfilled_pending=None):
        if fulfilled_pending is not None:
            fulfilled_pending.handler.resolve(projection, event)
```

Creating an event:

```python
Event(handler=SurviveHandler(roll=5), fulfills=(4, 0))
```

The `kind` literal exists solely as a Pydantic discriminator for
serialisation. No application code ever references it as a string.

#### PendingInput and pending handler

The same pattern governs pending inputs:

```python
class PendingInput(BaseModel):
    pending_id: tuple[int, int]
    blocking: bool = True
    handler: PendingHandlerBase

class PendingHandlerBase(BaseModel):
    def resolve(self, projection, event): ...
    def input_specs(self) -> list[InputSpec]: ...
    def event_from_form(self, form, pending_id) -> Event: ...
```

Concrete `PendingHandlerBase` subclasses live in domain modules. The pending
handler knows how to present its input form *and* how to turn the submitted
form data into the next event — so `event_from_form` always produces the
correctly typed event with the right `fulfills` value.

#### Lifecycle of a pending input

1. **Creation** — an event handler's `apply()` appends a pending to the
   projection:

   ```python
   projection.pending_inputs.append(
       PendingInput(
           pending_id=(event.id, 0),
           handler=SurvivePendingHandler(instruction='Roll 2D survival'),
       )
   )
   ```

2. **Presentation** — the web layer calls `pending.handler.input_specs()` for
   every pending input and renders the resulting form fields. No type
   inspection; pure polymorphism.

3. **Submission** — the user submits form data. The web layer calls:

   ```python
   event = pending.handler.event_from_form(form_data, pending.pending_id)
   ```

   This returns a fully constructed `Event` with `fulfills` already set.

4. **Replay** — `replay()` matches `event.fulfills` to `pending.pending_id`,
   removes the pending, then calls:

   ```python
   event.handler.apply(projection, event, fulfilled_pending=pending)
   ```

5. **Resolution** — the event handler delegates back to the pending handler:

   ```python
   fulfilled_pending.handler.resolve(projection, event)
   ```

   `resolve()` runs the domain logic and typically appends the next pending
   input to start the cycle again.

#### No isinstance in the call chain

Because every step calls a method on whatever object it holds, `isinstance`
checks never appear in production code. The web layer does not need to know
whether the current pending is a survive check or a skill choice — it calls
`input_specs()` and gets the right form either way.

The test helper `CharacterDriver` follows the same principle. When the test
calls `d.survive(5)`, the driver takes the next blocking pending and delegates:

```python
def survive(self, roll: int) -> CharacterDriver:
    pending = self._next_blocking_pending()
    return self._add(pending.handler.event_from_form({'roll': str(roll)}, pending.pending_id))
```

No type inspection; no knowledge of which handler class is present. If the
wrong pending is present, `event_from_form` or the subsequent replay will fail
— which is the correct and visible signal.

#### Module layout

```text
src/ceres/character/mechanism/
  event_base.py      — Event, EventHandlerBase, PendingInput, PendingHandlerBase
  replay.py          — replay(); no domain imports
  state.py           — CharacterProjection, CharacterSummary; no domain event imports

src/ceres/character/domain/
  career/            — one module per career (army.py, navy.py, …, prisoner.py)
                       plus shared career data (career_data.py)
  health/            — AgingHandler, InjuryHandler, … and their pending handlers
  homeworld/         — HomeworldChangedHandler, … and their pending handlers
  precareer/         — PreCareerEntryHandler, … and their pending handlers
```

There is no central aggregation module. Each `EventHandlerBase` and
`PendingHandlerBase` subclass registers itself into a mechanism-level registry
at class-definition time. `Event.handler` and `PendingInput.handler` are
deserialised using that registry. Domain modules push themselves in; the
mechanism never imports from domain. The dependency graph is a strict DAG:
mechanism ← domain ← replay.

### Career encapsulation rule

**No code outside the career, precareer, and sophont packages may hardcode
anything career-specific, precareer-specific, or sophont/species-specific.**
Adding a new career, precareer, or sophont must require changes only within
those packages.

What this means in practice:

- Career names, roll numbers, and event/mishap option sets are owned by the
  career package (`src/ceres/character/domain/career/`). External code — routes,
  templates, projection, bulk generation — treats careers generically.
- Per-career event and mishap logic lives in
  `src/ceres/character/domain/career/<name>.py` as `EventHandlerBase` and
  `PendingHandlerBase` subclasses. The mechanism layer never imports these
  classes; they are aggregated only in `event_types.py` for Pydantic
  deserialisation. The web layer and replay engine interact through the handler
  interface without knowing which career produced the pending or event.
- `CareerData` is the right place to add any data that generic infrastructure
  needs to query about a career (e.g., available tables, rank bonus rules). Do
  not let those queries leak out as hardcoded conditionals elsewhere.
- The same principle applies to precareers: entry conditions, curricula, event
  tables, and graduation effects belong entirely within
  `src/ceres/character/domain/precareer/`.
- Sophont/species data — characteristic arrays, UCP stat names, homeworld
  defaults — belongs in the sophont package. No external module may hardcode
  which characteristics a sophont has or what their labels are.

**Exceptions** — a small number of places may need to reference a specific
career or sophont name as a lookup key (e.g. finding a `CareerData` by name).
These are only acceptable when `CareerData` fields cannot carry the information
instead. Any such exception must be documented and approved before being
introduced; an unapproved hardcoded reference is a rule violation.

### Group-play mechanics are out of scope

The Connections Rule (linking two Travellers' histories for a free skill), 
skill packages (collectively chosen after creation and distributed round-robin),
and similar mechanics that operate across multiple characters are not planned
for `ceres.character`. They require a group session concept that is outside the
current single-character model.
