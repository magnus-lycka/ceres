# Test Case Ships

This document records conventions and normalizations used when translating
external ship designs into Ceres test cases.

These entries are not rules of Traveller and not rules of Ceres runtime
behaviour. They describe how source material is mapped into the structures used
by Ceres when building reference ships for tests.

Use stable identifiers like `TCS-001`.

## Entries

### TCS-001 Armoured Bulkhead Normalization

When a source design bundles a protected component together with its armoured
bulkhead in one combined tonnage or cost figure, the corresponding Ceres test
case should normalize that into two separate model items:

- the protected part
- a separate `Armoured Bulkhead` entry under the Hull section

This matches the current Ceres model, where `armoured_bulkhead=True` on a
`ShipPart` generates a distinct `ArmouredBulkhead` record rather than inflating
the protected part's own tonnage or cost.

Because an armoured bulkhead consumes 10% of the protected tonnage, a bundled
source figure should be split as:

- protected part = bundled total × `10/11`
- armoured bulkhead = bundled total × `1/11`

The same normalization applies to cost when the source also bundles bulkhead
cost into the protected component.

### TCS-002 Ignore Battle Load Figures In Source Designs

Some external ship sources, especially Anderson-derived exports, show both
normal load and battle load figures.

When building Ceres test-case ships from those sources, use the normal-load
figures only. Do not add separate battle-load values to the reference test
case unless Ceres later gains an explicit battle-load model.

### TCS-003 Ignore Income / Profit Figures In Source Designs

Some external ship sources include expected income, profit, trade yield, or
similar operational/business figures.

These are not part of the current Ceres ship-design model and should not be
encoded as test-case expectations for a reference ship.

### TCS-004 Beagle Laboratory Ship: HG 2016 Software Packages

The Beagle source lists `Mentor/1`, `Planetology/1`, and `Research Assist/1`.
These are *High Guard* (2016) titles removed in the 2022 edition (see RI-008).

Mapping applied in the Ceres test case:

- `Planetology/1` → `Expert (Space Sciences (Planetology))/1` — closest
  current-rules equivalent
- `Research Assist/1` → skipped — no current-rules equivalent
- `Mentor/1` → skipped — no current-rules equivalent
