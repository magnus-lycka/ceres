# Solar Energy Systems: High Guard vs Spinward Extents

This note compares solar-energy ship-building products in:

- `refs/hg/25_solar_energy_systems.md`
- `refs/spinext/59_arcturus.md`

The two sources appear to describe related but distinct technologies. Ceres
should keep source identity explicit until we decide whether to support one
family, both families, or a unified API with source-specific variants.

## Shared Concepts

Both sources treat solar systems as ship components that need nearby starlight.
Both assume listed output near a star's habitable zone and make output weaker
farther from the star. Both sources state that solar collectors are useless in
interstellar space. Both allow solar systems to support battery charging.

These distance and deployment effects are operational context, not normal ship
construction totals. Ceres should keep them as notes unless we later add a
scenario-state model.

## Solar Panels

High Guard solar panels:

- use named quality tiers: Basic TL6, Improved TL8, Enhanced TL10, Advanced TL12
- measure panel size in units, where one unit consumes one ton
- provide Power per unit:
  - Basic TL6: 0.25 Power/unit, MCr0.1/unit
  - Improved TL8: 0.5 Power/unit, MCr0.2/unit
  - Enhanced TL10: 1 Power/unit, MCr0.3/unit
  - Advanced TL12: 2 Power/unit, MCr0.4/unit
- provide power only while deployed
- require one six-minute space-combat turn to deploy
- cannot accelerate while deployed or deploying without critically damaging the
  array
- make the ship easier to detect by DM+2 while deployed

Spinward Extents solar panels:

- use direct TL rows: TL6, TL8, TL12
- measure panel size as stored tonnage
- have a minimum size of 0.5 tons
- provide Power per ton:
  - TL6: 1 Power/ton, MCr0.1/ton
  - TL8: 2 Power/ton, MCr0.2/ton
  - TL12: 3 Power/ton, MCr0.4/ton
- require 1D rounds to deploy or retract
- cannot be deployed during jump
- limit manoeuvre to Thrust 1 while deployed
- can charge batteries

Key difference: Spinward Extents panels are much more powerful per ton and have
a minimum size rule. The deployment constraints also differ: High Guard says no
acceleration while panels are deployed, while Spinward Extents allows manoeuvre
up to Thrust 1.

## Solar Hull Coatings

High Guard solar coatings:

- are available only at Enhanced TL10 and Advanced TL12
- use units rather than covered hull tonnage
- have no internal tonnage
- provide:
  - Enhanced TL10: 0.1 Power/unit, MCr0.3/unit
  - Advanced TL12: 0.2 Power/unit, MCr0.4/unit
- are typically used on standard and sphere hulls
- produce 50% less energy on close-structure and dispersed hulls
- are not applied to streamlined hulls
- make the ship easier to detect by DM+1
- make coated-hull repairs cost twice the normal repair amount

Spinward Extents solar panel hull coating:

- is available at TL6, TL8, and TL12
- is added directly to the hull in increments of 10 tons of displacement
- requires no internal tonnage
- provides Power per covered ton:
  - TL6: 0.01 Power/covered ton, Cr1000/covered ton
  - TL8: 0.02 Power/covered ton, Cr2000/covered ton
  - TL12: 0.03 Power/covered ton, Cr4000/covered ton
- is destroyed in proportion to hull damage and must be replaced rather than
  repaired
- only the TL12 coating can be used with Heat Shielding or Stealth Hull options

Key difference: the Spinward Extents coating is based on covered displacement
and has explicit compatibility rules with Heat Shielding and Stealth. The High
Guard coating has hull-shape limits and repair-cost rules instead.

## Solar Sails

High Guard solar sail:

- is a drive accessory rather than a power source
- consumes 5% of hull tonnage
- costs MCr0.2 per ton
- provides effective Thrust 0 and requires days to meaningfully change speed or
  course
- prevents jump while deployed

Spinward Extents solar sails:

- are direct TL rows with stored sail tonnage
- provide thrust based on percentage of total ship tonnage dedicated to sails:
  - TL6: 0.0005 Thrust per %
  - TL8: 0.001 Thrust per %
  - TL12: 0.002 Thrust per %
- cost:
  - TL6: MCr0.2/ton
  - TL8: MCr0.4/ton
  - TL12: MCr0.8/ton
- require 1D x 10 rounds to deploy and 1D x 10 rounds to retract
- prevent jump while deployed
- prevent use of any other manoeuvre drive while deployed
- can act as solar panels for double cost, producing half the Power output of
  same-tonnage solar panels

Key difference: High Guard treats solar sails as a fixed 5% hull option with
very low effective thrust. Spinward Extents gives a scalable thrust formula and
an optional power-generation mode.

## Modelling Options

Option 1: Support only High Guard solar systems.

This keeps the model closest to the main ship-building rules, but cannot support
Spinward Extents low-tech spacecraft accurately.

Option 2: Support only Spinward Extents solar systems.

This supports Arcturus/Creswell-style low-tech spacecraft, but conflicts with
High Guard stat blocks and terminology.

Option 3: Support both as explicit variants.

This is likely the safest route. Possible names:

- `SolarPanels`, `SolarCoating`, `SolarSail` for versions in HG
- `SpinExtSolarPanels`, `SpinExtSolarCoating`, `SpinExtSolarSail`

The shared concept can be "solar power source" or "solar auxiliary system", but
the classes should preserve source identity because the tables and constraints
do not line up cleanly.

## Current Recommendation

Keep Spinward Extents solar panels separate from High Guard solar energy systems
in the API. Do not merge coating or sail rules until we choose:

- whether covered coating should be represented as `covered_tons`
- whether Spinward Extents coating must enforce multiples of 10 tons
- whether solar sails belong under drives, power, or a separate auxiliary-system
  section
- how to display operational constraints without turning Ceres into an
  operations simulator
