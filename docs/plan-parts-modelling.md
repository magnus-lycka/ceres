# Plan: model part attributes honestly

Status: **complete** — all eight phases done. Move to `docs/archive/` once
#57 is closed.

Tracking issue: [#57](https://github.com/magnus-lycka/ceres/issues/57)

## Problem

Ceres tells one small lie 312 times. Across ~35 modules, part classes declare an
attribute as a class variable and then implement it as a per-instance property:

```python
class Armour(ShipPart):
    tons: ClassVar[float]  # not true: tons differs per instance
    ...

    @property
    def tons(self) -> float:  # the real, computed value
        ...
```

`ClassVar` here does not mean "class variable". It means **"Pydantic, do not make
this a field"**. That is a different statement, and using the wrong words for it
has grown into a structural problem.

### Evidence

Counted across `src/ceres/make`:

| attribute | real Pydantic field | `ClassVar` + `@property` |
| --- | --- | --- |
| `tons` | 9 | 106 |
| `power` | 9 | 81 |
| `cost` | 19 | 119 |

These count **declarations in the source**. The Inventory section later counts
**classes at runtime** — 298 parts *resolve* to a computed `tons` because they
inherit one of those 106 declarations. Both are right; they answer different
questions ("how many lines must change" versus "how many parts are affected").

Roughly **90% of parts compute these values; about 10% store them.** Yet
`ShipPart` declares them as *stored fields with defaults*:

```python
class ShipPart(CeresPart, ShipPartMixin):
    tons: float = 0.0
    power: float = 0.0
```

**The base class models the exception rather than the rule.** Every one of the
~300 computing parts must then opt out, and `ClassVar` is the opt-out.

### The cost of getting it backwards

Because the base declares a field, the majority case needs a workaround — and so
does the minority case. Expressing "this part simply has a tonnage" currently
takes three stacked mechanisms, duplicated in three modules
(`habitation.py`, `storage.py`, `systems/common.py`):

```python
class _ExplicitTonsSystemPart(ShipPart):
    tons: ClassVar[float]  # suppress the inherited field
    base_tons: float = Field(0.0, alias='tons')  # rename the real field, alias it back
    model_config = ConfigDict(frozen=True, populate_by_name=True, serialize_by_alias=True)

    @property
    def tons(self) -> float:  # re-expose under the original name
        return self.base_tons
```

The simplest possible requirement is the hardest thing to express in the model.
That is the signal that the abstraction is inverted.

### The second problem: mixins that leak fields

`ShipPartMixin` and `RobotPartMixin` are plain ABCs that annotate the contract
they expect of concrete parts:

```python
class ShipPartMixin(ABC):
    """Pydantic cannot see annotations on a plain mixin, so concrete classes
    must redeclare tons, power, and armoured_bulkhead as explicit Pydantic
    fields."""

    tons: float
    power: float
    notes: NoteList
```

**That docstring is false.** Pydantic *does* collect annotations from plain
mixin bases and turns them into required fields. Verified empirically across
Pydantic 2.5.3 → 2.13.4 and Python 3.12 → 3.14 — the behaviour has never
differed, so this was mistaken when written (`50de3ac`, 2026-05-04), not merely
stale:

```text
class Mixin:        foo: int
class A(SomeModel, Mixin): ...   ->  A.model_fields == ['foo'], A() raises ValidationError
```

The code survives only because every leaked name is independently rescued: by a
concrete class redeclaring it with a default, or — for `notes` — by a
`notes: ClassVar[NoteList]` shield on `CeresModel`. Two hacks propping each
other up. Nothing enforces the rescue: adding one attribute to a mixin's
contract, or forgetting one redeclaration, silently makes it a **required
constructor argument on every ship or robot part**, surfacing as a validation
error far from the cause.

This is also what `ty` began reporting in 0.0.58 ("Pydantic: Add fields from
mixin classes"), which is correct behaviour on its part. That produced ~2300 of
the ~2700 diagnostics currently in `uvx ty check`. The diagnostics are a symptom;
this plan addresses the cause.

## Four concepts, one name

The mechanical problem above is a symptom. The deeper one is that four distinct
ideas are all carried by the single class `ShipPart`:

1. **Persisted state and shared behaviour** — a Pydantic base with `tl`,
   `armoured_bulkhead`, binding, note collection.
2. **The contract of something installed in a ship** — it can report tonnage,
   power, cost and notes, and can be bound.
3. **Reusable installation behaviour** — what `ShipPartMixin` provides.
4. **Numeric values consumed by aggregation** — what `Ship` sums.

Because one class carries all four, there is no way to say "this is the promise"
separately from "this is the shared implementation", and every attempt to state
the promise (annotations on a mixin, `ClassVar` declarations) ends up creating
Pydantic fields instead. Naming the four separately is most of the fix.

| concept | today | proposed |
| --- | --- | --- |
| persisted state + shared behaviour | `ShipPart` | `ShipPartBase` |
| the contract of an installed part | implied by `ShipPart` annotations | `ShipPart` (Protocol) |
| reusable installation behaviour | `ShipPartMixin` | `ShipPartMixin` (unchanged) |
| typing scaffolding for a mixin's `self` | — | `_ShipPartMixinHost`, `_RobotPartMixinHost` |

**The domain word should name the domain concept.** "A ship part" is a thing
installable in a ship — a contract — not a particular implementation-sharing
device. So the Protocol takes the name `ShipPart`, and the base class becomes
`ShipPartBase`. This has a pleasant consequence: the 35 existing annotations
such as `list[ShipPart]` become *correct as written*, because they always meant
the contract rather than the base.

The one `isinstance(obj, ShipPart)` (`ship.py:287`) is asking "is this one of our
part objects", which is a base-class question, so it becomes
`isinstance(obj, ShipPartBase)`. No `runtime_checkable` protocol is needed.

**The rename is a committed part of the design, and happens early.** The base
class and the Protocol cannot both be called `ShipPart`, so introducing the
Protocol *is* the rename; they are one atomic step in phase 2. Doing it early
also avoids migrating consumer annotations twice. An earlier draft called the
rename optional and deferred it to last, which was incoherent: if the vocabulary
is the fix, it cannot also be the disposable part.

Earlier drafts proposed `PartValues` and `PartPresentation`. Those are dropped:
they do not name domain concepts, and `armoured_bulkhead_part` is installation
structure rather than "presentation". Narrow protocols are implementation
details, to be introduced only where a call site genuinely needs one — not as
the public vocabulary.

## What we actually want to model

Three genuinely different things are expressed with one mechanism today:

1. **A contract.** "Anything installable in a ship can report its tons, power
   and cost." Implementations legitimately differ: some compute, some store.
2. **A derived value.** `Armour.tons` depends on the hull it is bound to; it is
   not known at construction and must never be persisted. Most parts are like
   this, including ones that look constant: `Airlock.tons` derives from `size`,
   ship displacement, hull membership and installed order
   (`systems/access.py:34`).
3. **A supplied design input.** `DeepPenetrationScanners.tons`
   (`sensors.py:266`) and `_SpinExtSolarSail.tons` (`drives/standard.py:602`)
   are required fields the designer sets. These *must* persist.

## The serialisation invariant

A load-bearing contract, already asserted by
`test_cockpit_values_are_computed_properties_not_serialized_fields`
(`tests/unit/make/ship/test_bridge.py:77`):

> **Derived values must never serialise. Only supplied design inputs appear in
> `model_dump()`, under their public name.**

`Cockpit.model_validate({'tons': 999, ...})` must accept and *discard* the input,
recompute from the bound ship, and emit a dump containing no `tons` key.

**`computed_field` is therefore ruled out.** It would turn derived state back
into persisted state and silently invert this contract.

## Target design

### `ShipPartBase` declares nothing; each part says what it is

Generic aggregation depends on every part answering `tons`, `power` and `cost` —
`sum(p.power for p in ...)`, `remaining -= part.tons`, `part.cost * 1.5`
throughout `ship.py`. That dependency is real and must be preserved. Two designs
were measured against the full suite.

**Option A — the base declares nothing.** Each part declares honestly, and the
conflict disappears because it only ever existed where a base declared
something:

| subclass style | count | result under option A |
| --- | --- | --- |
| computed (`@property`) | ~262 | works; **just delete the `ClassVar`** |
| stored (plain field) | ~18 | **works unchanged — no migration at all** |
| declares neither | 2 sections + intermediates + fixtures | `AttributeError` — **loud** |

```text
Stored(tons=4.44)  -> tons 4.44, dump {'tons': 4.44}   # supplied: kept and persisted
Computed()         -> tons 1.5,  dump {}               # derived: absent, as required
Silent()           -> AttributeError: no attribute 'tons'
```

**Option B — the base declares a non-abstract property returning `0.0`.** This
keeps minimal subclasses working, but a subclass declaring `tons` as an ordinary
field then **diverges silently**: the inherited property wins attribute lookup,
so `part.tons` reads `0.0` while `model_dump()` reports `2.0`, with only a
`UserWarning`. All ~18 stored parts would need rewriting onto a
rename-and-alias mechanism, and the footgun would remain for every future part.

**Option A is chosen.** It migrates 2 sections plus 2 fixtures rather than ~18
stored parts; it fails **loudly** rather than silently, which matters when a
wrong tonnage would otherwise propagate quietly into a ship design; it keeps the
supplied-value capability option B destroys; and it needs no permanent guard
test, because the language enforces the invariant.

### No `ZeroTonnagePart`

An earlier draft proposed a shared zero-valued base. It is dropped:

- The name described one of the two values it supplied.
- `CustomisableShipPart` is **not** a zero-valued part. It is an intermediate
  capability base with **117 descendants** that supply their own values. Putting
  it under a zero base would make every descendant that declares a `tons` field
  diverge silently — reintroducing precisely the footgun option A was chosen to
  avoid. The `CustomPart` fixture is a concrete instance of that risk.
- Only two classes genuinely have no values of their own, and two explicit
  property pairs are clearer than an abstraction invented for two users.

So **`CustomisableShipPart` declares neither value**, and `DriveSection` and
`PowerSection` each declare explicit zero properties saying why:

```python
class DriveSection(ShipPartBase):
    @property
    def tons(self) -> float:
        """A section has no tonnage of its own; its drives carry it."""
        return 0.0
```

If more genuine aggregates appear later, a shared base named for the *reason* —
`AggregateShipPart` — can be extracted then.

### The base is not the interface, and a test says so

Under option A, `ShipPartBase` guarantees no `tons`. A reader could reasonably
expect otherwise, so this separation must be stated rather than left implicit:
**the `ShipPart` Protocol is the promise; `ShipPartBase` is only shared
implementation.**

To keep that honest, an architecture-level conformance test asserts that every
installable ship-part type implements each of `tons` and `power` as exactly one
of:

- a **Pydantic field** — meaning "this is a supplied design input"; or
- a **property** — meaning "this is derived".

That catches an incomplete part at development time instead of as an
`AttributeError` during aggregation, and it documents the two legitimate forms
directly in executable form.

**The population must be defined authoritatively, not inferred.** "Leaf type" is
the wrong rule — a usable concrete part may have subclasses, and an
implementation base may happen to be a leaf. Worse, ship-installability is *not*
signalled by inheriting `ShipPartBase`: `ComputerBase` is
`ComputerPart + ShipPartMixin` (`computer.py:18`), and **17 installable classes
sit outside the `ShipPartBase` tree entirely** — the computers, which are gear
parts installed in a ship. That is the mixin architecture working exactly as
`CeresPart`'s docstring intends, and a population defined by the base class
would silently skip all of them.

The authoritative population is therefore **every non-abstract implementation of
`ShipPartMixin`** — 318 classes, against 301 under `ShipPartBase`. Intermediate
classes that are not installable in their own right must be **explicitly marked**
rather than guessed at from the subclass tree; the marking mechanism is part of
phase 5's work.

This also confirms what the mixin really is: `ShipPartMixin` is the marker of
ship-installability. That is a second reason not to dissolve it into protocols.

`cost` is deliberately **not** asserted by this test. Whether every part must
have a cost is exactly the question #58 exists to answer, and the test should not
pre-empt it. #58 can extend the test once the semantics are decided.

This test, not the class hierarchy, is what makes "every part has a tonnage"
true.

### Not-installable is marked explicitly, and discovery is deterministic

Two mechanisms the conformance test depends on. Both are settled here rather than
during implementation, because each changes what a reader sees at a class
definition.

**Marking.** Some classes implement `ShipPartMixin` without being installable in
their own right: `ShipPartBase` itself and **eleven intermediate bases** whose
descendants supply the values — `CustomisableShipPart` (117 descendants),
`_ZeroPowerSystemPart` (25), `_ZeroPowerStoragePart` (14) and eight smaller ones,
enumerated in the Inventory below. These are marked with an explicit decorator at
the definition site:

```python
@not_installable
class _ZeroPowerSystemPart(ShipPartBase): ...
```

**The marker must match the exact class, never inheritance.** A plain class
attribute would be inherited, and the descendants of these bases *are*
installable — so an inherited marker would silently excuse the very classes the
test exists to check. The decorator records the exact type, and the test asks
`type in _NOT_INSTALLABLE`, not `issubclass`.

**Declared bases nest.** `_ReEntrySystem` extends `_ZeroPowerSystemPart`, so a
marked class may appear among another marked class's descendants. Any test over
this set must exclude descendants that are themselves declared bases, rather
than treating them as leaked markings.

This one mechanism also replaces "make `ShipPartBase` abstract". That idea does
not work: `ShipPartBase.__abstractmethods__` is empty, so making it
abstract means introducing a *new* abstract member, which would leave every one
of its subclasses abstract until each adds a mechanical override. Marking the
base as not-installable achieves the same exclusion, in the same vocabulary as
the intermediates, with no cascade.

**Discovery.** `ShipPartMixin.__subclasses__()` only sees classes whose modules
have been imported, so a new ship module could quietly evade a permanent
architecture guard. Discovery must therefore import every module under
`ceres.make.ship` — `pkgutil.walk_packages` — before enumerating, and **the
discovery itself must be tested**: assert the population contains known members
from several modules and does not fall below a recorded floor. A guard that can
be evaded by adding a file is not a guard.

### Protocols are used structurally, never inherited

*Implemented in phase 2; the shapes below are what is in the code.*

One coherent public contract, plus private scaffolding where `ty` needs it.
**Every member is read-only**, because parts are frozen Pydantic models: a
member declared as a plain attribute demands a writability they do not have, and
`ty` rejects `tl: int` here with "the member does not accept writes of type
`int`". An earlier draft of this plan specified exactly that and was wrong.

```python
class ShipPart(Protocol):
    """Everything a ship may ask of an installed part."""

    @property
    def tl(self) -> int: ...
    @property
    def tons(self) -> float: ...
    @property
    def power(self) -> float: ...
    @property
    def cost(self) -> float: ...
    @property
    def notes(self) -> NoteList: ...
    @property
    def group_key(self) -> str: ...
    @property
    def armoured_bulkhead_part(self) -> ShipPartBase | None: ...

    def bind(self, assembly: ShipBase) -> None: ...
```

`_base_parts()` and its consumers need all of this at once — they bind, inspect
`armoured_bulkhead_part`, render `notes` and `group_key`, and aggregate the
numbers (`ship.py:244`, `:299`, `:418`). A split pair of protocols could not
type them, which is why the earlier `PartValues`/`PartPresentation` division is
abandoned in favour of one contract.

The mixin's own body needs a different and private set:

```python
class _ShipPartMixinHost(Protocol):
    """Typing scaffolding: what ShipPartMixin's methods need of their host."""

    @property
    def tl(self) -> int: ...
    @property
    def tons(self) -> float: ...
    @property
    def armoured_bulkhead(self) -> bool: ...
    @property
    def notes(self) -> NoteList: ...
    @property
    def armoured_bulkhead_part(self) -> ShipPartBase | None: ...

    def store_armoured_bulkhead_part(self, part: ShipPartBase | None) -> None: ...
    def item(self, message: str) -> Any: ...
    def error(self, message: str) -> Any: ...
```

**A protocol may declare a private attribute for reading, but a frozen model
cannot satisfy one that declares a *writable* private attribute** — even though
Pydantic permits the assignment at runtime. Verified against a minimal repro
where the same protocol accepts a non-frozen model and rejects a frozen one.

The mixin writes `_armoured_bulkhead_part` in `_refresh_armoured_bulkhead`, so
rather than exposing the slot, the host declares
`store_armoured_bulkhead_part(...)` and the mixin asks its host to store. That
is a better arrangement than the one planned: the mixin stops reaching into its
host's private state, and the protocol declares behaviour rather than mutable
data.

`RobotPartMixin` needed the same treatment on a much smaller surface. With its
annotations stripped, `ty` reports only `tl` unresolved — `item()`, `error()` and
`_assembly` resolve through the mixin itself — so `_RobotPartMixinHost` declares
a single read-only `tl`.

**A protocol must never be inherited by a model class.** Inheriting one with
bare annotations recreates the field leak; inheriting one with properties
recreates the descriptor conflict. Protocols appear only as annotations: at
consumer call sites, and on the mixin's own `self` parameters
(`def bind(self: _ShipPartMixinHost, …)`). That `self`-annotation approach was
the design's main unproven assumption; it was **validated in phase 1** against a
fixture reproducing the phase-3 condition, with a control showing 6
`unresolved-attribute` errors without the annotation.

### Consumers must be migrated too

Aggregation APIs are annotated with the concrete type, e.g.
`Ship._all_parts() -> list[ShipPartBase]` (`ship.py:256`). Once `ShipPartBase`
stops declaring `tons`/`power` in phase 4, those signatures no longer tell a type
checker that parts have them — and they never expressed the intent anyway, since
what they mean is "any installed part", not "anything built on our base".

**Status after phase 2: 39 such annotations still name `ShipPartBase`.** The
rename moved them along with the 69 legitimate base-class references, which are
correct as they stand. Migrating the 39 to the `ShipPart` Protocol is the
remaining phase 2 step, and is what makes the Protocol load-bearing rather than
decorative.

Distinguishing the two is the whole point of the vocabulary: `class Foo(
ShipPartBase)` is an implementation choice, while `def f() -> list[ShipPart]` is
a statement about what the code requires.

### Inventory

Measured over the authoritative population — the **318 non-abstract
`ShipPartMixin` implementations**, which is 17 more than the `ShipPartBase` tree
contains:

| how `tons` is provided | count | how `power` is provided | count |
| --- | --- | --- | --- |
| `@property` | 298 | `@property` | 305 |
| stored field | 10 | stored field | 4 |
| inherits the base | 10 | inherits the base | 9 |

The ~300 computed parts need only their `ClassVar` line removed. The stored-field
parts (`DeepPenetrationScanners`, `BlackGlobeCapacitorBank`, `LoadingBeltTL7`,
`SpinExtSolarPanelsTL6` …) **are already correct and need no change**.

Those inheriting the base for `tons` and/or `power` are **14 classes**, and they
are not 14 parts needing migration. Taking the union of both attributes:

- **Two genuine aggregates** — `DriveSection` and `PowerSection`, no descendants
  — which gain the explicit zero properties. These are the only two that change.
- **Eleven intermediate bases** whose descendants supply the value, and which
  therefore need no value of their own — only *marking*:
  `CustomisableShipPart` (117 descendants), `_ZeroPowerSystemPart` (25),
  `_ZeroPowerStoragePart` (14), `_ExplicitTonsSystemPart` (10),
  `_SolarPowerSource` (8), `_ExplicitTonsStoragePart` (4), `_ReEntrySystem` (4),
  `_ExplicitTonsHabitationPart` (3), `_ZeroPowerCraftPart` (3), `_LoadingBelt`
  (2), `_ExplicitCostHabitationPart` (1).
- **The base class itself**, which is currently instantiable and would fail its
  own conformance test. It is marked too — see the marking section above for why
  making it abstract does not work.

So the marker has **twelve users**, not a handful, and it is what distinguishes
"a part" from "a base that parts are built from" at a glance. Note that several
of those intermediates disappear in phase 7 anyway, since the `_ExplicitTons*`
family dissolves; the marking set shrinks as the helpers are resolved.

Test fixtures `FixedPart` and `CustomPart` rely on supplied `tons`/`power` and
each gain an explicit field declaration.

### `cost` is a separate architectural decision

`cost` is **not** a `ShipPartBase` field. It lives on `CeresPart` (`shared.py:226`),
shared with gear and robots, and `CeresPart`'s docstring calls it one of "the two
universal part properties". Changing it is therefore not a mechanical extension
of this migration — it asks domain questions this plan should not answer in
passing:

- Does every part necessarily have a cost?
- Is a zero cost an explicit domain fact, or a missing override?
- Is `CeresPart` a complete part interface, or only a persistence base?
- Should the universal contract be something like `PricedPart`?

**`cost` is therefore out of scope here and is tracked separately as
[#58](https://github.com/magnus-lycka/ceres/issues/58).** This plan changes
`tons` and `power` only, and leaves every `cost` `ClassVar` in place. Nothing in
the phases below touches `cost`.

## Verified by spike

Measured on throwaway worktrees at HEAD.

**Correction:** the first spike runs used `uv run pytest`, which *skips the 303
approval tests*, so they were reported as green when they had not run. These are
the corrected `--all-tests` numbers.

| change | `pytest` | `pytest --all-tests` | `ty` |
| --- | --- | --- | --- |
| baseline | 4060 pass | 4418 pass | 2727 |
| strip both mixins + the `CeresModel` shield | 4060 pass | **4 snapshots fail** | ~564 |
| **option A** — also remove the base fields | 3 fail | 7 fail | ~445 |
| option B — also make the base a zero-property | — | **23 fail** | — |

Option A's 3 failures are the `FixedPart`/`CustomPart` fixtures, needing one
field declaration each. Option B's 23 are the stored parts it would force onto
the alias mechanism.

The 4 snapshot failures are **key ordering only** — no key added, removed or
changed in value. Pydantic orders fields by MRO declaration order, so removing
the mixin annotations moves `tl`, `cost` and `armoured_bulkhead` within the
output; syrupy reports "(no structural differences)". Regeneration is a
deliberate, reviewable step.

Residual after the mixin work: ~425 diagnostics, of which **384 come from a
single line** (`character/domain/career/skill_table_entries.py:176`). Separate
question, out of scope.

## Phases

Each phase is red → green → refactor, one step at a time, with
`pytest --all-tests` (never the quick suite — it skips the 303 approval tests)
and `ruff`/`ty` run at every step.

1. **Pin the serialisation invariant.** ✅ *Done — see results below.* Add
   `model_dump()`/schema tests
   asserting that derived `tons`/`power` stay out of the dump and supplied ones
   stay in, across a representative sample. Green immediately; they are the
   safety net for everything after. Then validate `self: _ShipPartMixinHost` on
   one mixin method, and land the `@not_installable` decorator itself — phase 2
   applies it, so the mechanism must exist first.
2. **Rename and introduce the vocabulary, atomically.** ✅ *Done — see results
   below.* Rename the class
   `ShipPart` → `ShipPartBase` (69 base-class references;
   `isinstance(obj, ShipPart)` at `ship.py:287` becomes `ShipPartBase`), and in
   the same step introduce the `ShipPart` Protocol plus `_ShipPartMixinHost` and
   `_RobotPartMixinHost`. These cannot be separated — the class and the Protocol
   cannot share a name — and doing the rename here rather than last means
   consumer annotations are migrated once. The 35 existing `list[ShipPart]`
   annotations become correct as written. Mark `ShipPartBase` and the eleven
   non-installable intermediates with `@not_installable` in the same step; do
   **not** try to make the base abstract, which would cascade a mechanical
   override onto every subclass.
3. **Mixin cleanup.** ✅ *Done — see results below.* Strip the attribute annotations from both mixins; remove
   the `CeresModel.notes` shield; point the mixins' `self` at their host
   protocols. Regenerate the 4 affected snapshots, confirming the diff is
   ordering-only. **Must precede phase 4** — see the forced ordering below.
4. ✅ **One atomic step:** remove `tons`/`power` from `ShipPartBase` *and* add the
   explicit zero properties to `DriveSection` and `PowerSection` *and* give
   `FixedPart`/`CustomPart` their field declarations. These cannot be separated:
   adding a property while the inherited field still exists makes the field's
   default *the property object*, which then serialises.
5. ✅ **Add the conformance test** over every unmarked non-abstract
   `ShipPartMixin` implementation, including the 17 computers outside the
   `ShipPartBase` tree. Discovery imports every module under `ceres.make.ship`
   before enumerating, and is itself tested against known members and a
   population floor. Asserts `tons` and `power` only; `cost` belongs to #58.
   Passes as soon as phase 4 lands, and guards the invariant thereafter.
6. ✅ **Delete the redundant `tons`/`power` `ClassVar` lines, module by module.**
   One module per step, ~35 modules. **`cost` declarations are untouched.**
7. ✅ **Resolve the six helpers — they encode two different things, and get
   opposite treatments.**
   - `_ExplicitTons*` (17 users across 3 bases) means *"tonnage is a supplied
     design input"*. With no inherited field to suppress, that is just
     `tons: float`, so these three bases **dissolve entirely** and their users
     declare an ordinary field.
   - `_ZeroPower*` (42 users across 3 bases) means *"this part draws no power"* —
     a derived constant, not a supplied value, and a genuine shared concept at
     that scale. These **consolidate into one base named for the reason**, e.g.
     `UnpoweredShipPart`, rather than three near-duplicates named for a value.
   The seventh helper, `_ExplicitCostHabitationPart` (`habitation.py:109`), is
   `cost`-based and stays for #58.
8. ✅ **Rewrite the architecture documentation.** `docs/assemblies_and_parts.md` is
   the **primary artifact**, not `ARCHITECTURE.md`: it is the canonical statement
   of this design and its "Core Rule" section currently teaches the false rule
   outright — *"A mixin may add fields and simple behavior"*, illustrated with
   `class ShipPartMixin: tons: Tons`. That single sentence is the origin of the
   leak this plan exists to remove. Rewrite it around the new vocabulary, the
   base-is-not-the-interface split and the conformance test; then correct the
   `ShipPartMixin` docstring and have `ARCHITECTURE.md` summarise and link to it.
   Two other documents cite the old rule and need checking:
   `docs/plan-gear-backed-robot-options.md:26` and
   `docs/archive/plan-robot-brains-as-computers.md:85`.

There is no separate robot phase. Robot parts have **zero** `ClassVar`-shadowed
properties; their mixin and host protocol are handled in phases 2 and 3, and
`RobotPart.cost` belongs to #58. `RobotPart.slots` is already a non-abstract
property returning `0`, so the codebase already contains a correct instance of
the pattern.

**Forced ordering, established by a failed attempt rather than by reasoning:**
removing the base fields while the mixin still annotates them turns the leaked
annotations from harmless into *required* —
`ValidationError: 2 validation errors for DriveSection — tons missing, power
missing`. Hence phase 3 precedes phase 4.

## Phase 1 results

Landed: `src/ceres/make/ship/installable.py`,
`tests/unit/make/ship/test_installable.py`,
`tests/unit/make/ship/test_serialisation_invariant.py`. Full suite 4441 passed,
175 snapshots passed; `ruff` and `ty` clean on the new files.

**The serialisation safety net is 21 tests** over a sample spanning `bridge`,
`armour`, `habitation`, `sensors`, `screens`, `storage` and `computer` — the last
being one of the 17 parts that reach a ship through `ShipPartMixin` rather than
the shared base, and `FuelProcessor` exercising the rename-and-alias path.

Because these assert existing behaviour rather than driving new behaviour, they
were mutation-checked rather than trusted:

| mutation | result |
| --- | --- |
| drop `Cockpit`'s `ClassVar` shield so derived tonnage serialises | **red** (2 tests) |
| turn `DeepPenetrationScanners.tons` into a computed property | **red** (1 test) |
| mark a helper with an *inherited* attribute instead of the exact-class registry | **red** (1 test) |

Writing them also corrected a wrong assumption: `BlackGlobeCapacitorBank`
supplies **both** `tons` and `power`, so power is now classified independently of
tonnage rather than assumed derived everywhere.

**`self: _ShipPartMixinHost` is validated**, which was the design's main unproven
assumption. A fixture reproducing the phase-3 condition — the mixin carrying *no*
attribute annotations — type-checks clean, including the private
`_armoured_bulkhead_part`. The control matters as much as the result: the same
fixture *without* the `self` annotation produces 6 `unresolved-attribute` errors,
so the annotation is doing the work rather than ty being permissive.

**Known cost:** repo-wide `ty` moved 2727 → 2731. All four are the `notes`
false positive from the mixin leak, raised by constructing parts in the new
tests. They are four more instances of the single root cause and disappear in
phase 3.

## Phase 2 results

Landed, full suite **4468 passed, 175 snapshots passed**, `ruff` clean (bar the
3 `PLR0917` since silenced), `ty` 2731 → 2735 with all four new diagnostics being
the known `notes` false positive.

- **Rename applied**: 145 occurrences of the exact word `ShipPart` across 32
  files, `ShipPartMixin` untouched. Checked first that no string literal,
  discriminator or snapshot depended on the name, and that nothing instantiates
  the base directly (so the `__class__.__name__` fallbacks never see it).
- **`ShipPart` Protocol added**, and pinned by tests that `ty` verifies
  structurally from the consumer's side — including `Computer5`, which reaches a
  ship through the mixin alone.
- **`_ShipPartMixinHost` and `_RobotPartMixinHost` added**, each pinned against a
  real class.
- **Twelve classes marked `@not_installable`**, with the marking under test.

Three corrections the work forced, none of which the plan anticipated:

1. **The contract must be read-only throughout.** Parts are frozen Pydantic
   models, so a protocol member declared as a plain attribute demands a
   writability they lack: `ty` rejects `tl: int` with "the member does not accept
   writes of type `int`". Every member is now a read-only property.
2. **A frozen model cannot satisfy a protocol that declares a mutable private
   attribute**, even though Pydantic permits the write at runtime. Confirmed
   against a minimal repro where the same protocol accepts a non-frozen model and
   rejects a frozen one. So `_ShipPartMixinHost` declares
   `store_armoured_bulkhead_part(...)` instead of `_armoured_bulkhead_part`, and
   the mixin now asks its host to store rather than assigning private state
   directly — a better arrangement than the one planned.
3. **Declared bases nest.** `_ReEntrySystem` extends `_ZeroPowerSystemPart`, so
   "every descendant of a base is installable" is too strong; the test excludes
   descendants that are themselves declared bases.

**Consumer migration — done, by audit rather than replacement.** Aggregation
collections, `_all_parts()` results, grouping helpers and consumer parameters now
name `ShipPart`. Two sites deliberately keep `ShipPartBase` because they need
behaviour the ship-facing contract does not carry: `sensors._capability_tl`
(reaches `_assembly` and `assembly_tl`) and `security._BoobyTrap.check_tl`
(reaches `assembly_tl` and `error`). That the contract is *narrower* than some
internal helpers need is a real result, not a gap.

**The casts are gone, which is the proof the contract does real work.**
`ComputerSection._all_parts()` previously declared `list[ShipPartBase]` and had
to `cast()` its computers into it, because a computer is a gear part plus
`ShipPartMixin` and never inherited the base. Retyping to `list[ShipPart]`
removed both casts, and `ruff` then removed the now-unused `cast` import. A
production-path test pins it: a `Computer5` reaches `Ship._base_parts()` and
carries its cost into the aggregate, with no cast.

The plumbing method is `_store_armoured_bulkhead_part`, private, and the contract
no longer names the base class in its own signatures.

**A lesson for phase 3's mixin edits:** the pre-rename safety check searched for
`'ShipPart` — a quote immediately before the name — and so missed a class name
used *mid-sentence* in a referee-facing warning. That string is now "the
protected part", naming the concept rather than a class, which is both clearer
and rename-proof.

## Phase 3 results

**The backlog this plan exists to remove is gone: `ty` 2736 → 419**, a drop of
2,317. Full suite **4469 passed, 175 snapshots**, `ruff` clean bar the 3
3 `PLR0917` since silenced, `deptry` clean.

Both mixins now declare **no attributes at all** and carry behaviour only. The
`CeresModel.notes` shield is gone, since the leak it blocked no longer exists.

**The snapshot change was proved before it was accepted.** The four failures were
verified deep-equal after sorting keys — no key added, removed, or changed in
value — and the regenerated diff is 145 insertions against 145 deletions, the
same lines reordered by Pydantic's MRO-driven field order.

**The `self: Protocol` approach costs more than phase 1 measured.** Phase 1
validated it against a fixture and found the robot host needed only `tl`. In
practice, once a method's `self` is typed as a protocol, `ty` sees *only* what
the protocol declares — so each host protocol must also carry every mixin method
called on `self`, and every host member those reach. `_ShipPartMixinHost` grew to
include `assembly_tl`, `bulkhead_protected_tonnage`, `bulkhead_label`,
`build_item`, `check_tl`, `_refresh_armoured_bulkhead` and `_store_assembly`;
`_RobotPartMixinHost` grew from one member to seven. The mechanism works, but
"a two-line protocol" was wrong.

**A second private-write site appeared.** `bind()` assigns `self._assembly`, the
same frozen-model problem as `_armoured_bulkhead_part`. Resolved the same way and
one level up: `CeresPart._store_assembly()` now owns the slot, and both mixins
ask rather than poke. That is the pattern for context mixins generally.

**All remaining diagnostics were then cleared too: `ty` reports zero.** They
were not part-related, but they were real, and several were the same mistakes
this plan exists to correct:

- **390 from one line.** `skill_table_entries` splatted a runtime-built
  `dict[str, Level]` into a union of 60+ skill classes, so `ty` matched every key
  against every parameter of every variant. Extracted to one documented helper,
  `skill_with_levels()`, which states that the mapping is dynamic.
- **The `Occupant` protocol declared a mutable member against frozen models** —
  exactly the error found in `ShipPart` during phase 2, pre-existing and
  independent. Made read-only.
- **`default_suite()` was typed by the mixin**, which after phase 3 declares
  nothing. `RobotTransceiver` is the robot twin of the computer case: a gear part
  reaching a robot through `RobotPartMixin` alone. Fixed by mirroring the ship
  vocabulary — `RobotPart` (class) → `RobotPartBase`, plus a `RobotPart`
  Protocol. The robot side now matches the ship side rather than diverging.
- **Two dead `# type: ignore` comments** in mypy syntax that `ty` never honoured,
  replaced by explicit `cast()` at the two runtime-narrowing sites.
- **Two genuine latent bugs in tests**: `(ship_class or ship_type).lower()` could
  reach `.lower()` on `None`, and `sum(row.power ...)` could sum a `None`.
- **Two deliberate invalid assignments** inside `pytest.raises`, now carrying
  `# ty: ignore[invalid-assignment]` with the reason.

## Gate status

`./pre-commit.sh` passes end to end: **4469 tests, `ruff check`, `ruff format`,
`ty`, `deptry`, `bandit` — all green, exit 0.** `ty` went 2727 → 0.

`PLR0917` (too many positional arguments) is now in the `ruff` ignore list beside
its sibling `PLR0913`, which was already ignored as noisy. It began appearing
only because `pre-commit.sh` invokes `uvx ruff` unpinned, so a tool release
changed the gate without a commit — which is the argument for pinning `ruff` and
`ty` versions, still outstanding.

## Phases 4-8 results

`./pre-commit.sh` green throughout: **4466 tests, 175 snapshots, `ruff`, `ty`,
`deptry`, `bandit` — exit 0.**

- **Phase 4** removed `tons`/`power` from `ShipPartBase` atomically with the two
  section properties and the fixture fields. Two snapshots changed, and this time
  **not** by ordering: `DriveSection` and `PowerSection` stopped persisting four
  meaningless zeros, because they now compute those values. Verified round-trip
  idempotent and production cost unchanged before accepting; diff was 8 deletions
  and 0 insertions.
- **Phase 5** added the conformance test with tested discovery. It found a flaw
  in itself immediately: `__subclasses__()` picked up *test-defined* doubles, so
  the guard was order-dependent. Discovery is now scoped to `ceres.` and that
  scoping is asserted.
- **Phase 6** deleted 187 redundant `ClassVar` lines across 32 modules. The
  conformance test caught the one case the deletion exposed.
- **Phase 7** treated the two helper families oppositely, as planned:
  `_ZeroPower*` (42 users) consolidated into **`UnpoweredShipPart`**, named for
  the reason; `_ExplicitTons*` (17 users) **dissolved** into ordinary `tons`
  fields. One exception emerged and is documented: `CommonArea` keeps the
  rename-and-alias form because `HotTub` derives its tonnage from `users`, and a
  subclass cannot override an inherited field with a property.
- **Phase 8** rewrote `docs/assemblies_and_parts.md`. Its architecture was sound
  all along — one inheritance chain plus context mixins, no `isinstance` against
  the base, prefer protocols; it even anticipated `ShipPartLike`. Its *"A mixin
  may add fields and simple behavior"* was **true**, but granted a permission
  without its consequence: the field is required, on every model using the
  mixin. The genuinely false claim was in `ShipPartMixin`'s own docstring —
  *"Pydantic cannot see annotations on a plain mixin"* — the opposite of the
  document, and the version the code was written to. The rewrite states the rule
  as a prohibition and says why. `ARCHITECTURE.md` now summarises and links to
  it.

**Found along the way:** `DockingClamp.maintained` is inert — `crew.py` reads it
via `getattr(part, 'maintained', True)` but no such field exists, so every
carried craft counts as maintained. Filed as
[#59](https://github.com/magnus-lycka/ceres/issues/59); the call sites carry a
directive pointing at it rather than hiding it.

## Risks and open questions

- ~~**`self: _ShipPartMixinHost` is unproven.**~~ Resolved in phase 1: validated
  against a fixture reproducing the phase-3 condition, with a control showing 6
  `unresolved-attribute` errors without the annotation.
- **Serialisation is the highest risk.** Phase 1's tests exist to catch a
  regression, since a mistake silently changes persisted output rather than
  failing loudly. Run approval snapshots with `--all-tests` at every step; the
  default suite skips all 303 of them.
- **Every part must declare `tons`/`power`.** There is no inherited default, so
  an incomplete part fails — at test time via the conformance test, or otherwise
  with `AttributeError`. This is a real change to how a new part is written and
  belongs in `docs/assemblies_and_parts.md`.
- **The `@not_installable` marker is load-bearing and easy to misapply.** It
  must match the exact class; an inherited marker would excuse precisely the
  descendants the conformance test exists to check. The decorator's own
  behaviour deserves a test.
- **The rename is committed, and lands early.** 69 base-class references move in
  phase 2. It is not optional: the Protocol cannot take the name `ShipPart`
  while the class holds it, and the vocabulary is the point of the exercise
  rather than a cosmetic afterthought.
- **`CeresPart.cost` is deliberately unresolved** and is the largest remaining
  question. It may justify splitting a pure-data `PartSpec` from a behavioural
  `Part`, which would dissolve the field-versus-property tension entirely. This
  plan is written so as not to foreclose that.
