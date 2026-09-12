# `make.ship` depends on `make.vehicle`, not the reverse

A ship carries vehicles: an Air/Raft in a docking space, an ATV in a hangar. Today
`ceres.make.ship.crafts.Vehicle` is a catalogue stub holding four flat numbers
(`kind`, `tl`, `shipping_size`, `cost`) with no construction behind them. Once
`ceres.make.vehicle` can build a real vehicle, those numbers become derived values
of an actual design, and the stub stops earning its place.

We decided the dependency runs **`make.ship` → `make.vehicle`**: ship holds a real
`Vehicle` design object and asks it for shipping tonnage and cost. This mirrors
`make.robot` depending on `character.domain.skills`. The alternatives were a narrow
shipping-view interface the vehicle package exposes, and keeping ship's catalogue
data independent with a test asserting the two agree. We rejected the narrow view
because a wrapper whose only job is to forward two attributes off a `Vehicle` is a
thin-wrapper smell; the seam stays narrow through *what ship reads*, not through an
extra class. We rejected independent data because it lets the two drift.

## Consequences

- **Not yet executed.** Ship keeps its existing `_VEHICLE_SPECS` stub until a
  vehicle catalogue home exists. Named designs (Air/Raft, ATV) deliberately do
  *not* live in `src/ceres/make/vehicle`; they are expected in a future
  cross-domain catalogue spanning vehicles, robots and ships, whose form — Python
  or JSON — is undecided and will be decided when more than one domain needs it.
  Until then, approval tests carry the named designs as source-derived cases.
- **Circularity risk to watch.** Vehicle weapons reference spacecraft-scale weapons
  (`refs/vehicle/23_spacecraft_scale_weapons.md`). When vehicle weapons are
  implemented, `make.vehicle` must not import from `make.ship`. Any shared weapon
  vocabulary belongs in a module below both.
