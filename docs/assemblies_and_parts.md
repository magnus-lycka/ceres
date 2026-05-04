# Parts, Assemblies, and Context Mixins

Ceres models buildable things as assemblies made from zero or more parts.

An assembly is something that can be used independently in the game model: a starship, vehicle, robot, weapon, suit, shop item, or similar. Assemblies normally contain parts, but some assemblies may have no explicitly modelled parts if their internal structure is not relevant.

A part is a reusable rules object that can appear inside one or more assembly contexts. For example, a machine gun may exist as handheld gear, a vehicle-mounted weapon, a robot weapon, or a ship-mounted weapon. These are not modelled as one physical instance being moved between assemblies. They are modelled as different concrete rules classes sharing a common generic part base.

## Core Rule

A class has exactly one real domain inheritance chain rooted in CeresPart.

Context-specific assembly properties are added only through pure mixins.

```
class CeresPart(CeresModel):
    tl: int
    cost: Cost
```

A mixin may add fields and simple behavior, but must not inherit from CeresModel, BaseModel, or another domain model.

```
class ShipPartMixin:
    tons: Tons
    armored_bulkheads: bool = False


class RobotPartMixin:
    slots: int



class VehiclePartMixin:
    spaces: int
```

Canonical context part classes may then be defined as simple combinations:

```
class ShipPart(CeresPart, ShipPartMixin):
    pass


class RobotPart(CeresPart, RobotPartMixin):
    pass


class VehiclePart(CeresPart, VehiclePartMixin):
    pass
```

Generic reusable parts define what the item is, independent of where it is used:

```
class ComputerPart(CeresPart):
    performance: int
    software: list[Software] = Field(default_factory=list)
```

Concrete context-specific parts combine the generic part with the appropriate context mixin:

```
class ShipComputer(ComputerPart, ShipPartMixin):
    pass


class RobotComputer(ComputerPart, RobotPartMixin):
    pass


class VehicleComputer(ComputerPart, VehiclePartMixin):
    pass
```

## Interpretation

ComputerPart defines computer semantics: performance, software handling, cost, tech level, and other context-independent rules.

ShipPartMixin defines the properties required when something is used as a ship part: tonnage, bulkheads, and other ship-installation attributes.

ShipComputer therefore means:

A computer, interpreted as a ship part.

It is not necessary for ShipComputer to inherit from ShipPart. It is sufficient that it inherits from ComputerPart and ShipPartMixin.

## Constraints

Use this rule:

One real superclass chain, any number of pure context/capability mixins.

Allowed:

```
class ShipComputer(ComputerPart, ShipPartMixin):
    pass
```

Forbidden:

```
class ShipComputer(ComputerPart, ShipPart):
    pass
```

because both ComputerPart and ShipPart are domain model classes rooted in CeresPart.

Mixins must be non-overlapping. Two mixins used on the same class must not define the same field name unless the conflict is intentional and documented.

## Type Checks

Do not rely on:

```
isinstance(part, ShipPart)
```

for all ship-usable parts, because a ShipComputer may not inherit from ShipPart.

Prefer capability checks, protocols, or collection-level validation based on required fields or mixin membership:

```
isinstance(part, ShipPartMixin)
```

or, where static typing is important:

```
class ShipPartLike(Protocol):
    tons: Tons
    armored_bulkheads: bool
```

## Design Principle

Context-independent properties belong on the generic part.

Context-dependent properties belong in the relevant context mixin.

Concrete classes combine both.
