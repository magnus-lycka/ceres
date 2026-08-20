# Parts, Assemblies, and Context Mixins

Ceres models buildable things as assemblies made from zero or more parts.

An assembly is something that can be used independently in the game model: a starship, vehicle, robot, weapon, suit,
shop item, or similar. Assemblies normally contain parts, but some assemblies may have no explicitly modelled parts if
their internal structure is not relevant.

A part is a reusable rules object that can appear inside one or more assembly contexts. For example, a machine gun may
exist as handheld gear, a vehicle-mounted weapon, a robot weapon, or a ship-mounted weapon. These are not modelled as
one physical instance being moved between assemblies. They are modelled as different concrete rules classes sharing a
common generic part base.

## Core Rule

A class has exactly one real domain inheritance chain rooted in CeresPart.

Context-specific behaviour is added only through pure mixins.

```python
class CeresPart(CeresModel):
    tl: int
    cost: float
```

**A mixin carries behaviour only. It must not declare attributes, and must not inherit from CeresModel, BaseModel, or
another domain model.**

This is the rule most easily got wrong, so it is worth stating why. Pydantic *does* collect annotations from a plain
mixin base and turns them into **required fields** on every model that uses the mixin:

```python
class Mixin:
    foo: int

class Thing(SomeModel, Mixin): ...
# Thing.model_fields == ['foo']  and  Thing() raises ValidationError
```

Verified across Pydantic 2.5–2.13 and Python 3.12–3.14; the behaviour has never differed.

An earlier version of this document said a mixin "may add fields and simple behavior". That was *true* — fields are
exactly what those annotations produce — but it granted the permission without stating the consequence: the field is
**required**, on every model using the mixin, whether or not that model wants it.

`ShipPartMixin`'s own docstring meanwhile claimed the opposite, that "Pydantic cannot see annotations on a plain mixin",
and the code was written to that version. The leaked fields survived only because each name happened to be rescued
independently — by a concrete class redeclaring it with a default, or by a `ClassVar` shield on `CeresModel`. Nothing
enforced the rescue, and the arrangement produced ~2,300 type-checker errors before it was unpicked.

The rule is therefore stated as a prohibition rather than a permission: not because a mixin *cannot* add fields, but
because the fields it adds are rarely the ones anyone intended.

So mixins declare methods:

```python
class ShipPartMixin(ABC):
    """Reusable installation behaviour. No attributes."""

    def bind(self, assembly: ShipBase) -> None: ...


class RobotPartMixin(ABC):
    @property
    @abstractmethod
    def slots(self) -> int: ...
```

Implementing a context mixin is what marks a class as installable in that context.

## Contract, base, and mixin are three different things

Four ideas used to share one name. They are now separate:

| concept | name |
| --- | --- |
| the contract a ship may rely on | `ShipPart` — a `Protocol` |
| shared persisted state and behaviour | `ShipPartBase` — a class |
| reusable installation behaviour | `ShipPartMixin` |
| typing scaffolding for a mixin's `self` | `_ShipPartMixinHost` — private |

Robots mirror this exactly: `RobotPart`, `RobotPartBase`, `RobotPartMixin`, `_RobotPartMixinHost`.

The domain word names the domain concept, so **the protocol takes the plain name**. Type consumers against `ShipPart`,
not `ShipPartBase`:

```python
def _all_parts(self) -> list[ShipPart]: ...
```

Reserve the base class for inheritance, `isinstance`, and APIs that genuinely need base-only behaviour — for instance
`sensors._capability_tl`, which reaches for `assembly_tl` and private state that the ship-facing contract does not
carry.

## The base guarantees nothing; a test does

`ShipPartBase` declares neither `tons` nor `power`. Roughly 90% of parts derive those values and about 10% supply them,
so a base that declared either would be modelling the exception.

Each part therefore says which it is, and the choice is a statement about the domain:

- a **Pydantic field** — a supplied design input, which persists;
- a **property** — a derived value, which must never persist.

```python
class DeepPenetrationScanners(ShipPartBase):
    tons: float          # supplied by the designer


class Cockpit(ShipPartBase):
    @property
    def tons(self) -> float:   # derived from the ship it is bound to
        ...
```

Because nothing in the hierarchy enforces this, `tests/unit/make/ship/test_part_conformance.py` does: it walks every
non-abstract, installable `ShipPartMixin` implementation and requires each to provide `tons` and `power` in one of those
two forms. Discovery imports the whole `ceres.make.ship` package first, so a new module cannot evade the guard, and the
discovery itself is tested.

A class that implements the mixin without being an installable part — the shared base, or an intermediate whose
descendants supply the values — is marked at its definition:

```python
@not_installable
class UnpoweredShipPart(ShipPartBase):
    ...
```

The marker matches the **exact class**, never inheritance: the descendants of these bases *are* parts, and an inherited
marker would excuse precisely the classes the guard exists to check.

### Serialisation invariant

> Derived values must never serialise. Only supplied design inputs appear in `model_dump()`, under their public name.

`Cockpit.model_validate({'tons': 999})` accepts the input, discards it, recomputes from the bound ship, and emits a dump
with no `tons` key. `computed_field` is therefore not used for derived values: it would turn derived state back into
persisted state.

One indirection remains where a **stored parent has a derived child** — a subclass cannot override an inherited field
with a property. `CommonArea` stores its tonnage under another name and exposes a property, so `HotTub` can derive its
own from `users`. Needed only in that situation.

## Interpretation

`ComputerPart` defines computer semantics: performance, software handling, cost, tech level, and other
context-independent rules.

`ShipPartMixin` supplies the behaviour required when something is installed in a ship: binding, TL checking, bulkhead
handling.

`ComputerBase(ComputerPart, ShipPartMixin)` therefore means: *a computer, interpreted as a ship part*. It does not
inherit `ShipPartBase`, and does not need to — 17 installable classes sit outside that tree. This is the mixin
architecture working as intended, and it is why consumers must be typed against the protocol.

## Constraints

One real superclass chain, any number of pure context mixins.

Allowed:

```python
class ShipComputer(ComputerPart, ShipPartMixin): ...
```

Forbidden:

```python
class ShipComputer(ComputerPart, ShipPartBase): ...
```

because both `ComputerPart` and `ShipPartBase` are domain model classes rooted in `CeresPart`.

**A protocol must never be inherited by a model class.** Inheriting one with bare annotations recreates the field leak;
inheriting one with properties makes the descriptor shadow any field a subclass declares. Protocols appear only as
annotations.

## Type Checks

Do not rely on:

```python
isinstance(part, ShipPartBase)
```

for all ship-usable parts, because a computer may not inherit it. Prefer mixin membership at runtime:

```python
isinstance(part, ShipPartMixin)
```

and the protocol for static typing:

```python
class ShipPart(Protocol):
    @property
    def tl(self) -> int: ...
    @property
    def tons(self) -> float: ...
    @property
    def power(self) -> float: ...
    def bind(self, assembly: ShipBase) -> None: ...
```

**Every protocol member is read-only.** Parts are frozen Pydantic models, so a member declared as a plain attribute
demands a writability they do not have — a type checker rejects `tl: int` here with "the member does not accept writes
of type `int`". For the same reason a protocol cannot declare a *writable* private attribute: where a mixin needs to
store host state, the host exposes a method (`_store_assembly`, `_store_armoured_bulkhead_part`) and the mixin asks
rather than assigning.

## Design Principle

Context-independent properties belong on the generic part.

Context-dependent behaviour belongs in the relevant context mixin.

The contract belongs in a protocol; the class hierarchy is an implementation detail.

Concrete classes combine them, and say for themselves whether each value is supplied or derived.
