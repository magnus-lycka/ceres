# Rule Interpretations

This document records deliberate rule interpretations, exclusions, and
normalizations used in Ceres.

It is intentionally sparse to begin with. Entries should be added when we
review source-derived ship test cases and need to distinguish between:

- supported behavior
- deliberately ignored source material
- deliberate interpretations
- unresolved TODOs

The goal is to document decisions that are intentional but not obvious from the
code alone, especially where published examples, third-party designs, or older
rules material differ from our implementation.

## Conventions

- Use stable identifiers like `RI-001`.
- Prefer documenting cross-cutting decisions here.
- Keep ship-specific source notes in the relevant test file unless the decision
  applies more broadly.
- Do not restate code that is already clear unless the reason for the behavior
  would otherwise be ambiguous.

## Entries

### RI-001 Stores And Spares Are Not Modelled As Reserved Design Tonnage

Ceres does not currently model stores and spares as a separate reserved tonnage
entry in ship designs.

Where source material gives recommended or expected stores/spares capacity, that
is treated as design guidance rather than a hard reduction in cargo capacity.
This may be surfaced as informational or warning output in the cargo section,
but it is not installed as a separate ship part.

### RI-002 Passenger Baggage Is Not Modelled As A Separate Design Allocation

Ceres does not model passenger baggage/storage space as a separate line item in
the ship design.

The working interpretation is:

- Middle Passage or lower in stateroom accommodation keeps baggage within the
  passenger's room allocation.
- Low berths are assumed to include space for the passenger's permitted small
  personal effects.
- High Passage reduces practical cargo availability by 1 ton per passenger in
  operation, but this is not reserved as fixed design tonnage.

This means baggage does not appear as a dedicated installed component in the
spec. If we later add explicit expected passenger manifests by class, this may
instead drive informational output, validation, or cargo-availability warnings.

### RI-003 Small Ships Do Not Require Separate Maintenance Crew

For crew-role calculation, Ceres follows the High Guard prose in
`refs/HG_CREW_ROLES.md` for separate maintenance staff on smaller ships.

The working interpretation is:

- commercial ships below 1,000 tons do not require a distinct `MAINTENANCE`
  role
- military ships below 500 tons do not require a distinct `MAINTENANCE` role
- once those thresholds are reached, separate maintenance crew scales by ship
  tonnage

On smaller ships, maintenance duties are assumed to be covered by engineering
staff rather than listed as a separate crew position.

### RI-004 Steward Requirements Depend On Planned Passenger Manifest

Steward staffing is treated as an operational requirement driven by the planned
passenger manifest, not by theoretical maximum berth capacity.

In practice, this means Ceres only derives steward requirements from an
explicit `passenger_vector`, rather than assuming that every available middle
berth or low berth is occupied for crew-planning purposes.

The steward requirement is interpreted as required `Steward` skill levels, not
raw headcount:

- each High Passage passenger counts as 10 Middle Passage passengers
- required steward level is `ceil((middle + 10 * high) / 100)`
- Ceres does not assume routine recruitment above `Steward 3`

When more than 3 total steward levels are needed, Ceres splits the requirement
across multiple stewards rather than assuming a single higher-skill recruit.

### RI-005 Retro Computer Pricing Is Not Currently Modelled

Ceres does not currently model the retrofitted computer pricing shown for some
ship computers in *Central Supply Catalogue* source material and derivative
exports.

In practice, this means:

- computer hardware in Ceres is priced from the normal computer model
- source rows marked as retrofitted, such as `Retro*`, are not given special
  discounted pricing
- when a reference ship depends on retro computer pricing, that difference
  should be documented explicitly in the relevant test case rather than hidden
  or silently normalized away

This is a current modeling limitation, not a statement that such source
material is invalid.

### RI-006 Marines On Liners Can Represent Shipboard Security Staff

When a commercial passenger ship or liner source lists `Marines` in its crew
manifest, Ceres does not interpret that alone as proof that the vessel should
be modelled as a military craft.

The working interpretation is that such `Marines` can represent embarked
security personnel: guards, police, response teams, or similar shipboard
security staff attached to a commercial operation.

This affects how source-derived test cases should be read:

- explicit `Marine` roles may appear on commercial ships
- their presence does not, by itself, imply military crew rules or military
  ship classification
- where relevant, the source test case should document that interpretation
