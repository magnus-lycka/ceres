# Command, Comms, Sensors, Countermeasures

This note collects rule text that affects how we think about command,
communications, sensors, countermeasures, and nearby systems such as
electronic warfare and sandcaster-launched chaff.

The goal is not to settle every interpretation. Where the rules leave room for
interpretation, we record the question and avoid silently baking in one answer.

## What the rules say

### Bridge and command

Core spacecraft construction says every ship has a bridge containing:

- basic controls
- communications equipment
- avionics
- scanners
- detectors
- sensors
- other equipment necessary for ship operation

This strongly suggests that command, comms, and sensors overlap physically even
when we model them as different design concerns.

High Guard habitation options adds that every bridge already has equipment for
monitoring and controlling the ship's sensors, even if that is tied to the
pilot's display.

### Small bridge

High Guard crew rules explicitly say:

- a ship with a smaller bridge suffers `DM-1` for all checks related to
  spacecraft operations made from within the bridge
- examples given include `Astrogation` and `Pilot`

This is broader than pilot checks alone.

Current Ceres therefore treats the small bridge penalty as a general
spacecraft-operations note, not a pilot-only note.

If a check is made from a dedicated sensor station, the small-bridge penalty
does not apply. The rule text limits the penalty to checks made from within the
bridge, and a dedicated sensor station is treated as an independent station
rather than part of the cramped small-bridge workspace.

### Sensor packages

Core rules say:

- all ships have Basic sensors unless upgraded
- the DM column in the Sensors table applies to both
  `Electronics (comms)` and `Electronics (sensors)` checks made by crew in the
  ship

This means the installed sensor package is not just a sensor-only quality
modifier. It affects communications checks as well.

Package contents from Core are:

- `Basic`: Radar, Lidar
- `Civilian Grade`: Radar, Lidar
- `Military Grade`: Jammers, Radar, Lidar
- `Improved`: Densitometer, Jammers, Radar, Lidar
- `Advanced`: Densitometer, Jammers, Neural Activity Sensor, Radar, Lidar

JTAS #4 adds useful operational colour without replacing the above:

- all starship sensor packages also contain passive optical and thermal sensors
- radar and lidar are active sensors
- optical and thermal sensors are passive
- military packages also imply `Emissions Control (EMCON)`
- improved packages also imply `Emissions Control (EMCON)`
- advanced packages imply `Extreme Emissions Control`

### Communications overlap

The rules do not flatten comms and sensors into one identical subsystem, but
they are heavily intertwined:

- sensor package DM affects both `Electronics (comms)` and
  `Electronics (sensors)`
- `Transponder or radio comms` can make a ship easier to detect
- ships can share or relay sensor data to one another over their communications
  systems
- sandcaster chaff clouds affect both `Electronics (comms)` and
  `Electronics (sensors)`

So while comms and sensors are distinct game uses, they are not cleanly
separable in the underlying ship architecture.

### Sensor stations

High Guard says sensor stations:

- are extra stations beyond the default bridge capability
- allow multiple simultaneous sensor tasks during combat
- are associated with detection, sensor locks, and electronic warfare
- are only optional on ships of `7,500 tons or less`

This supports treating sensor stations as command/operations positions rather
than free-floating standalone electronics.

### Countermeasures and electronic warfare

High Guard electronics options define:

- `Countermeasures Suite`: `DM +4` to all jamming and electronic warfare attempts
- `Military Countermeasures Suite`: `DM +6`

JTAS #4 also reinforces that:

- jammers are tied to the sensor types carried
- `Emissions Control (EMCON)` reduces a ship's detectable signature, but it is
  not the same thing as invisibility
- `Low-Probability-of-Intercept (LPI)` and
  `Extremely Low-Probability-of-Intercept (ELPI)` reduce the probability that
  active sensor emissions reveal the ship, and Ceres treats them as included
  functionality when the installed sensor type and its effective TL are high
  enough

These are not the same thing as hull stealth, though they overlap in effect.

### Life scanning

JTAS #4 says:

- only a `Neural Activity Sensor` can truly scan for life signs

High Guard electronics options add:

- `Life Scanner`
- `Life Scanner Analysis Suite`

There is therefore a rules tension here:

- JTAS #4 presents `Neural Activity Sensor` as the only true life-sign scanner
- High Guard presents `Life Scanner` and `Life Scanner Analysis Suite` as
  separate ship-mounted systems with their own cost, tonnage, and power

For Ceres, the safe conclusion is:

- `Neural Activity Sensor` is not the same thing as `Life Scanner`
- `Life Scanner` and `Life Scanner Analysis Suite` should be treated as
  separate installed parts in the sensor section
- we should not collapse them into one feature without explicit rule text

### Sandcaster chaff and sensor screen dispensers

High Guard weapons and screens defines `Chaff Canister` ammunition for
sandcasters:

- `20` canisters per ton
- `Cr30000` per `20`
- causes `DM-1` to `Electronics (comms)`, `Electronics (sensors)`,
  `Electronics (remote ops)`, and missile attack rolls within the cloud
- does not provide normal sand protection against laser, energy, or particle
  weapons

JTAS #4 describes `Sensor Screen Dispenser` as a sandcaster-fired canister that
breaks radar/lidar/optical-thermal lock and helps a ship enter EMCON.

In this context:

- `sand` is the usual defensive sand cloud that interferes with laser, energy,
  and particle attacks
- `chaff` is a cloud intended to confuse sensors, communications, remote ops,
  and missile targeting instead

The practical architectural takeaway is:

- this belongs with sandcaster ammunition, not with the ship's sensor suite

We should eventually model sandcaster ammunition stocks distinctly enough to
track at least:

- standard sand canisters
- chaff / sensor-screen style canisters
- any other supported sandcaster canister types

## Implications for Ceres

### Sensors should remain ShipParts

Sensor packages are real installed equipment with:

- TL
- cost
- tonnage
- power
- concrete package contents

They should remain modelled as their own `ShipPart`s.

### But they are structurally close to command

Even though sensors remain their own parts, the rules strongly support viewing
them as close to `command` in the ship's structure:

- bridge already contains baseline comms and sensors
- sensor stations are bridge options
- package DMs affect comms as well as sensors

This means it may make sense to present or document sensors in a way that keeps
their relationship to command visible.

### Notes should carry capability details

The item line for a sensor package is not enough. The rules attach capability
details to the installed package, so the package notes should carry things such
as:

- suite contents
- sensor/comms DM
- jammers / EMCON capability
- densitometer or neural activity sensor presence
- LPI / ELPI availability, where relevant

The renderer can then decide whether those notes appear as:

- bullet list
- comma-separated summary
- inline parenthetical text

### What this means in practice

- Operational descriptions from JTAS #4 may still belong in Ceres as part
  notes, capability notes, or future build options. We should list them and
  decide case by case, not ignore them.
- `Emissions Control (EMCON)` is treated as built into Military and Improved
  sensor suites, and `Extreme Emissions Control` as built into the Advanced
  suite.
- `Low-Probability-of-Intercept (LPI)` and
  `Extremely Low-Probability-of-Intercept (ELPI)` are treated as functionality
  that comes with a sensor type when its effective TL is high enough. They are
  not tracked in Ceres as separate purchased add-ons.
- Sensor-screen effects belong with sandcaster ammunition, not as a generic
  "electronic warfare" abstraction in the sensor suite.

When rules text describes how a system behaves in operation, that usually
belongs in notes on the relevant part. It only becomes a ship-building rule
when the text also defines a concrete installed option with TL, cost, tonnage,
power, or other explicit design consequences.

## Open questions

- Should sensors eventually move presentation-wise under `Command`, while still
  remaining separate `ShipPart`s in the model?
