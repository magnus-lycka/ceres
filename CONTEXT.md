# Ceres

Ceres builds Mongoose Traveller 2nd Edition assemblies — starships, robots,
vehicles, characters, worlds — as ordinary Python objects that validate
themselves and render to stat blocks.

This glossary is grown lazily, one domain at a time, as terms are settled by
being used in code rather than decided on paper. It currently covers vehicle
design and its cross-domain collisions, plus the relationship between character
creation and rounds; ships, robots and worlds are not yet written up.

## Assemblies, parts and gear

**Part**:
A component with a Tech Level and a cost that can be installed into any
assembly — a ship, a robot, a vehicle, a piece of gear. What a part contributes
in a given context (displacement, Spaces, power) is supplied by that context,
not by the part.
_Avoid_: component, module, unit

**Assembly**:
Anything a part can be installed into. Ships, robots, vehicles and gear are all
assemblies.
_Avoid_: container, host, chassis

**Equipment**:
An assembly that packages one or more parts into a single thing — a transceiver
that is a radio part plus a computer part plus an encryption part.
_Avoid_: item, device, kit

**Gear**:
Equipment that makes sense on its own: something you could buy as a unit and
use without installing it in anything. A transceiver, a computer, a fire
extinguisher. The test is isolation, not size or portability.

A vehicle's air lock, collision protection or autopilot is *not* gear. It has no
existence outside the vehicle, so it belongs to the domain that installs it.

When a domain needs something that is gear, it reuses gear's **part**, not its
packaging: the part carries the item's identity and Tech Level, while the
installing domain supplies what the installation costs and occupies there.
_Avoid_: equipment (narrower here), accessory, kit

## Vehicle design

**Space**:
The unit a vehicle's size is measured in, and the unit anything installed in it
consumes. A vehicle has no fractional Spaces.
_Avoid_: slot, ton, volume

**Vehicle Type**:
What a vehicle fundamentally is, chosen mostly for its locomotion — ground
vehicle, grav vehicle, aeroplane, submersible and so on, including Structure,
which is not a vehicle at all. Sets the per-Space baselines everything else
scales from.
_Avoid_: chassis, class, category

**Size**:
The band a vehicle's Spaces put it in — Small, Light, Heavy, Huge, Massive.
A consequence of Spaces, never chosen directly.
_Avoid_: size class, weight class, tonnage band

**Hull**:
A vehicle's structural toughness before rounding: its Spaces times its type's
rate, as modified by features and structural reinforcement. An intermediate
value, not printed on a stat block. Distinct from a *ship's* Hull — see
Collisions below.
_Avoid_: frame, chassis strength

**Structure**:
A vehicle's damage threshold, one-tenth of its Hull rounded up. This is the
figure the stat block prints and play compares damage against.
_Avoid_: hull points, hits, structure points, damage track

**Shipping Tonnage**:
What a vehicle displaces when carried as cargo by a spacecraft, or occupies in
a docking space or hangar. Not the same quantity as its Spaces.
_Avoid_: displacement, tonnage, cargo size

**Speed Band**:
A rung on the named ladder from Stopped to Orbital that all vehicle speed is
expressed on. Each band has a number, which the rules use directly for
collisions and acceleration.
_Avoid_: velocity, kph, speed rating

**Cruise Speed**:
The Speed Band a vehicle sustains, one below its maximum.
_Avoid_: economy speed, normal speed

**Agility**:
How readily a vehicle answers its operator, as a modifier. A vehicle's Agility
comes from its type and size; a *ship's* comes from its thrust, and the two are
unrelated.
_Avoid_: handling, manoeuvrability

**Trait**:
A named property a vehicle has by virtue of its type, size or features, such as
Unresponsive or ATV. Carries rules consequences but is not itself bought.
_Avoid_: tag, flag, attribute, quality

## Characters and rounds

**Character**:
A Traveller whose characteristics, skills and biography are established through
character creation, including a generic NPC used as the basis for individuals
in play.

**Actor**:
An individual tracked for play in rounds: a sophont, animal or robot, including
its current injuries. Actors can originate from character creation, direct
creation in rounds, or other sources.

**Linked actor**:
An actor associated with its source character, whose character-derived details
can be refreshed explicitly while retaining its combat injuries.

**Actor copy**:
An independent actor created by copying another actor in rounds. It has no
link to the original actor's source character and can be edited independently.

## Collisions between domains

These words mean genuinely different things in different Ceres domains. They
are kept apart deliberately, not unified.

**Hull**:
In vehicles, a plain number (above). In ships, a *part* — a component with its
own configuration, armour and cost. A ship's Hull is a thing; a vehicle's Hull
is a quantity. This matters because ships will come to carry vehicles.

**Trait**:
Vehicles, robots and ship weapons each have their own trait vocabularies. They
share a formatting convention and nothing else; a trait from one domain is not
meaningful in another.

**Armour**:
Ships carry a single armour rating. Vehicles carry Protection independently on
six named faces. The vehicle term is Protection, and the allocation across
faces is part of what it means.
