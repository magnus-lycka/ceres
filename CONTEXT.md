# Ceres

Ceres builds Mongoose Traveller 2nd Edition assemblies — starships, robots,
vehicles, characters, worlds — as ordinary Python objects that validate
themselves and render to stat blocks.

This glossary is grown lazily, one domain at a time, as terms are settled by
being used in code rather than decided on paper. It currently covers vehicle
design and the cross-domain collisions that domain exposed; ships, robots,
characters and worlds are not yet written up.

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
