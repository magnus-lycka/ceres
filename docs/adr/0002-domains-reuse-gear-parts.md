# Domains reuse gear's parts, not gear itself

Ships, robots and vehicles all install things that also exist as gear: a
transceiver, a computer, a fire extinguisher. `ceres.gear` models such an item
twice over — as a `CeresPart` carrying its identity and Tech Level, and as an
`Equipment` assembly packaging one or more parts into something purchasable.
`TransceiverEquipment`, for instance, holds a `TransceiverPart` plus a
`ComputerPart` plus any encryption or uplink parts.

We decided that a domain needing such an item **reuses the part, not the
equipment**. `make.robot` already does this, importing `RadioTransceiverPart`
rather than `RadioTransceiverEquipment`. The part carries what is true of the
item everywhere — what it is, its Tech Level, its range; the installing domain
supplies what the installation costs and occupies *there*, from its own rules.

The alternative was for each domain to model its own version of the item from
its own rulebook. We rejected it because the two books then disagree with no
way to tell an intentional difference from a transcription error, and because a
laser transceiver is the same object in the world whichever hull it is bolted
into. The opposite alternative — reusing the `Equipment` — was rejected because
a purchasable package prices and sizes itself for standalone purchase, which is
not what a vehicle chapter charges for fitting one.

This is why the boundary matters: something is gear only if it makes sense in
isolation. A vehicle's collision protection, control system or air lock has no
existence outside a vehicle, so it is not gear and stays with the domain that
installs it, whatever the vehicle rules call it. See CONTEXT.md.

## Consequences

- A vehicle or ship option that wraps a gear part supplies its own Spaces or
  tonnage and its own Cost, taken from its own rules. The two figures differing
  between books is expected, not a discrepancy to reconcile.
- When a domain needs an item that is gear but is missing from `ceres.gear`, it
  is modelled in `ceres.gear` first, from a catalogue source — Core equipment,
  the Central Supply Catalogue, the Field Catalogue — rather than from the
  installing domain's table alone.
- Weapons are expected to become a sibling package of `ceres.gear` rather than
  living inside it. That is not decided or done, and is recorded here only so
  the intent is not lost.
