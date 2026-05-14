# Test Case Ships

This document records general conventions and normalizations used when
translating external ship designs into Ceres test cases.

These entries are not rules of Traveller and not rules of Ceres runtime
behaviour. They describe how source material is mapped into the structures used
by Ceres when building reference ships for tests.

Use stable identifiers like `TCS-001`.

## Gallery Requirement

Every ship test file in `tests/ships/` must be registered in
`tests/ships/test_gallery.py`. This is enforced automatically by
`tests/ships/test_gallery_coverage.py`.

When adding a new ship test file:

1. Expose a public `build_<ship_name>()` function (no leading underscore).
2. Import it in `test_gallery.py` and add it to all four parametrized lists.

## Expected-Values Pattern

Each ship test file should define an `_expected` `SimpleNamespace` object that
captures the values **exactly as they appear in the source document**. This
object is the authoritative record of what the source says.

```python
from types import SimpleNamespace

_expected = SimpleNamespace(
    displacement=6,
    hull_cost_mcr=0.24,
    power_basic=2,        # stat block says 2
    ...
)
```

When Ceres computes a different value than the source (due to a rule
interpretation, a rounding policy, or an explicit deviation), override the
field on `_expected` and document why with a comment referencing the relevant
RI entry:

```python
# Tycho tool uses floor; ceil per RI-013 gives 2, not 1
_expected.power_basic = 2
```

All test assertions must reference `_expected` fields rather than magic
numbers:

```python
def test_basic_power():
    assert _build().basic_hull_power_load == _expected.power_basic
```

This makes it immediately visible when a source value and a Ceres value differ,
and where the deviation is intentional.

Ship-specific source notes and deviation explanations belong in the test file's
module docstring, not in this document.

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
