# Accomodation

This note describes how Ceres should think about accommodation, berthing, and
related human-occupancy space on ships.

The purpose is to separate:

- what the rules explicitly say
- what seems like a good modelling consequence
- what remains open

This is important because habitation is currently modelled in a way that grew
incrementally around `StateroomGroup(count=...)`, `LowBerthGroup(count=...)`, and
`CabinSpace(tons=...)`. That is no longer a good fit for the full range of
accommodation types found in Core and High Guard.

## What the rules explicitly give us

### Standard staterooms

From Core and High Guard:

- a `Stateroom` is a discrete unit
- it contains living and sleeping facilities, including a bed, fresher, and a
  basic kitchen / food-preparation area
- it consumes `4 tons`
- it costs `MCr0.5`
- most ships allocate `one person` to each stateroom
- `double occupancy` is explicitly allowed in some ships

This means a stateroom is not merely "some amount of generic floor space". It
is a standardised accommodation unit.

### High and luxury staterooms

High Guard habitation options and Core both define these as separate
accommodation types:

- `High Stateroom`: `6 tons`, `MCr0.8`, `Cr3000` life support
- `Luxury Stateroom`: `10 tons`, `MCr1.5`, `Cr5000` life support

The rules also say:

- they are not strictly required for high passengers
- but high passengers strongly prefer them
- a `High Stateroom` typically grants `DM +1` when seeking high passengers
- a `Luxury Stateroom` typically grants `DM +2`

So these are not just "nicer stateroom notes". They are concrete build choices.

### Barracks

High Guard defines `Barracks` separately from staterooms:

- `1 passenger per ton`
- `Cr50000 per ton`
- `Cr500` life support per ton

Barracks are for soldiers, basic passengers, and others willing to accept
cramped conditions.

This is accommodation, but not the same kind of accommodation as staterooms.

### Cabin space

High Guard defines `Cabin Space` as:

- `Cr50000 per ton`
- `Cr250` life support per ton
- every `1.5 tons` allows one additional passenger in moderate comfort

The text also says:

- it gives more room to move around and reach other ship systems
- it is not comfortable living space
- it is generally used in interplanetary craft where passengers are only on
  board for a few hours

So cabin space is not a stateroom. It is area-based and passenger-capacity
based, not room-based.

### Acceleration benches and seats

High Guard defines:

- `Acceleration Bench`: `4 seats`, `1 ton`, `Cr10000`
- `Acceleration Seat`: `1 seat`, `0.5 ton`, `Cr30000`

The text makes their intended use very clear:

- they are for temporary transport
- comfort is limited
- they are commonly used on short-haul small craft

These are sitting-capacity components, not sleeping accommodation.

### Low berths

Core and High Guard both define `Low Berth` as a separate category:

- `0.5 ton`
- `Cr50000`
- holds `1 passenger`
- requires `1 Power per 10 berths or part thereof`

Running costs also differ:

- occupied low berths cost `Cr100` per maintenance period

So low berths are not just another kind of bed. They are a frozen-occupancy
system with their own economics and power rules.

### Emergency low berths

High Guard also defines `Emergency Low Berth`:

- `1 ton`
- `MCr1`
- `1 Power`
- can hold up to `4 people in dire circumstances`

This is a separate system from ordinary low berths and should not be merged
with them.

### Brig

High Guard defines `Brig` as:

- `4 tons`
- `MCr0.25`
- `Cr1000` life support
- designed to hold `6 prisoners`
- can uncomfortably hold `12`
- contains `six pull-down slabs that can be used as beds`

This matters because a brig can contain sleeping surfaces and human occupancy
without being ordinary accommodation.

### Medical bay

High Guard systems define `Medical Bay` as:

- `4 tons`
- `MCr2`
- `DM +1` to Medic checks made within it
- each 4 tons supports treatment of up to 3 patients

Again, this is human-occupancy space but not ordinary habitation by default.

### Common area

Core and High Guard both say it is common practice to assign common-area space,
roughly around one quarter of stateroom tonnage.

The text also says:

- common areas are for recreation, dining, laundry, and unwinding
- cutting them too far can have crew-performance consequences

This means common area is not accommodation itself, but it is strongly coupled
to accommodation quality and crew comfort.

### Steward and passenger support

Crew tables in Core and High Guard give:

- `Steward`: `1 per 10 High` or `100 Middle` passengers

This is explicit and should be modelled as a support requirement for passenger
service, not as a feature of accommodation itself.

## What the rules do not fully settle

Some useful modelling questions are only partially answered by the rules.

### High passage requirements

The rules clearly say:

- high passengers prefer high/luxury accommodation
- high and luxury staterooms can grant DMs when seeking high passengers

But the rules do not give a strict universal formula such as:

- "high passage requires single occupancy"
- "high passage requires X square metres per person"
- "high passage requires 1 ton baggage space"

Those are plausible campaign/economic assumptions, but they are not hard design
rules in the text we have.

### Whether brigs, medical bays, and similar spaces count as permanent capacity

The rules tell us these spaces can contain people, patients, or prisoners, and
may include sleeping surfaces.

They do not say they should automatically count as:

- normal crew accommodation
- passenger capacity
- long-term habitable berthing

So that must remain an explicit modelling choice.

### Luxury beyond stateroom class

The rules strongly imply that:

- gourmet kitchens
- theatres
- pools
- advanced entertainment systems
- other high-end common-area options

can make a ship more attractive, especially to high passengers.

However, this is not expressed as a general quantitative "luxury score" in the
rules.

## Modelling consequences for Ceres

### Accommodation should not be represented by one count-field per category

The current style:

- `staterooms=StateroomGroup(count=4)`
- `low_berths=LowBerthGroup(count=20)`

works for a narrow subset but does not scale well when we need:

- standard + high + luxury staterooms at once
- different berth-like systems
- barracks
- cabin space
- seat-only transport
- prison or hospital layouts

`StateroomGroup(count=...)` also mixes two concepts:

- one accommodation unit
- a collection of many such units

That makes it awkward to combine variants.

### We need at least three distinct capacity axes

The rules strongly support tracking these separately:

- `sitting capacity`
- `sleeping / accommodation capacity`
- `frozen capacity`

These are not interchangeable.

Examples:

- acceleration seats increase sitting capacity, not sleeping capacity
- staterooms increase sleeping / habitation capacity
- low berths increase frozen capacity

### Accommodation should be more generic at the section level

`HabitationSection` should probably move toward something more general than
dedicated fields like:

- `staterooms`
- `low_berths`
- `cabin_space`

A better long-term structure is likely something like:

- `accommodations=[...]`

where the list can contain concrete units such as:

- `Stateroom(...)`
- `HighStateroom(...)`
- `LuxuryStateroom(...)`
- `Barracks(...)`
- `CabinSpace(...)`
- `LowBerth(...)`
- `EmergencyLowBerth(...)`
- `AccelerationSeat(...)`
- `AccelerationBench(...)`
- possibly `Brig(...)` or similar occupiable spaces

This matches how weapons are already handled: individual installed things,
rather than a hybrid "type + count" container class.

### We should prefer real classes over raw dicts as the primary model

Even though a tabular `_specs` approach will help, raw dicts are probably not
the best top-level domain model.

Better pattern:

- concrete classes per accommodation family
- internal `_specs` tables where that helps
- JSON roundtrip through discriminated unions where needed

This keeps:

- Python usage clearer
- JSON more explicit
- testing easier
- extension easier when new options are added

### Special one-off accommodation variants should be possible

The rules leave plenty of room for setting-specific variations:

- different low-berth makes
- unusual luxury rooms
- exotic alien accommodation
- prison or hospital conversions

For recurring variants, subclassing is a reasonable Python-native solution.
We do not need to invent a generic "variant" framework unless repeated use
shows that we need one.

## Proposed conceptual grouping

### 1. Sitting-only transport

Short-term human transport that should not count as real accommodation:

- `Acceleration Bench`
- `Acceleration Seat`

These should affect:

- seat count / temporary passenger capacity

but not automatically:

- sleeping capacity
- normal long-term life support assumptions

### 2. Sleeping accommodation

Ordinary living / berthing space:

- `Stateroom`
- `High Stateroom`
- `Luxury Stateroom`
- `Barracks`
- `Cabin Space`

These should affect:

- sleeping / habitation capacity
- accommodation life-support cost

But they do not all behave the same:

- staterooms are discrete units
- barracks are tonnage-per-passenger
- cabin space is tonnage-based and softer / less formal

### 3. Frozen accommodation

Cryogenic or suspended-occupancy systems:

- `Low Berth`
- `Emergency Low Berth`

These affect:

- frozen capacity
- low-berth running costs
- berth power requirements

### 4. Human-occupiable but not ordinary accommodation

Spaces that can hold people, sometimes even sleeping people, but should not
automatically count as normal accommodation:

- `Brig`
- `Medical Bay`
- possibly some craft bays / vaults / special mission spaces

These should exist as installable spaces, but whether they contribute to
practical berthing should be a deliberate rule, not an accidental side effect.

## Suggested future fields / concepts

Not everything here needs to be implemented immediately, but these concepts are
likely useful.

### Capacity-oriented derived values

At the ship level, we will probably want separate derived counts such as:

- `seat_capacity`
- `sleep_capacity`
- `frozen_capacity`
- perhaps `high_passage_quality_capacity`

### Occupancy assumptions

Some classes may eventually need explicit occupancy controls, for example:

- stateroom single vs double occupancy
- barracks capacity
- cabin space passenger count inferred from area, or explicitly constrained

### Passenger attraction / luxury

We do not need to solve this now, but the documents strongly suggest a future
concept such as:

- `luxury` flags or notes
- `high_passage_dm`
- or a more general attraction model

This could later allow:

- high/luxury stateroom bonuses
- gourmet kitchen bonuses
- theatre / pool / advanced entertainment bonuses

without forcing us to decide that whole system today.

## Proposed test plan

Before a major habitation refactor, we should write explicit tests for all the
important occupancy styles.

Suggested cases:

### Shuttle / launch

- acceleration seats
- acceleration benches
- short-haul capacity
- no claim of proper sleeping accommodation

### Free trader baseline

- standard staterooms
- low berths
- common area
- middle / low passenger support

### Barracks transport

- high troop density
- barracks instead of staterooms
- lower comfort assumptions

### Interplanetary passenger craft

- cabin space
- short-duration moderate-comfort transport

### Hospital ship

- medical bays
- standard accommodation
- explicit statement that medical capacity is not automatically permanent
  berthing

### Prison ship

- brig
- explicit prisoner capacity
- no automatic assumption that brig space counts as ordinary crew/passenger
  accommodation

### Luxury yacht / liner slice

- high staterooms
- luxury staterooms
- common-area luxuries
- steward requirements
- later, perhaps passenger-attraction effects

## Recommended next design direction

The safest path appears to be:

1. Stop growing the current `StateroomGroup(count=...)`-style pattern.
2. Introduce a more generic habitation / accommodation collection model.
3. Represent actual accommodation types as individual classes or installable
   units, not as one-off counts glued to section fields.
4. Keep explicit distinction between:
   - sitting
   - sleeping
   - frozen
5. Delay a general luxury / attraction system until the structure for
   accommodation itself is clean.

This should make habitation both more faithful to the rules and easier to grow
as we add the many remaining accommodation variants.
