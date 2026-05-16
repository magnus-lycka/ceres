# Plan: Complete Manipulator Rules

**Source**: `refs/robot/09_manipulators.md` (Robot Handbook pp. 25–28)

## Goal

Implement the full Robot Handbook manipulator rules using a single `Manipulator`
class. The unified class replaces both the current `list[str]` representation of
standard manipulators and the separate `AdditionalManipulator` option class. The
result is one consistent API: `Robot(manipulators=[...])`.

The complete model must correctly calculate slot usage, cost, and statistics for
all manipulator configurations: removed, standard, resized, additional, and
STR/DEX-enhanced manipulators.

## Current State

`Robot.manipulators: list[str]` holds strings such as `'Standard'`. A separate
`AdditionalManipulator` class in `ceres.make.robot.options` handles extra
manipulators as a distinct robot option. The two representations are disconnected:

- Standard manipulators carry no typed attributes.
- Additional manipulators are a separate `RobotPart` in the options list.
- Removal discount: `Cr100 × size × removed` with no 20% BCC cap (known bug).
- No STR or DEX values are computed for any manipulator.
- No resizing support exists for the standard pair.

## Design

### `Manipulator` Class

A single `Manipulator(RobotPart)` replaces all of the above. It lives in a new
file `ceres.make.robot.manipulators`:

```python
class Manipulator(RobotPart):
    model_config = {'frozen': True}

    size: RobotSize | None = None  # None = inherit robot size at bind time
    str_bonus: int = 0             # STR above default; cost = Cr100 × size × bonus²
    dex_bonus: int = 0             # DEX above default; cost = Cr200 × size × bonus²

    def resolved_size(self, robot_size: RobotSize) -> RobotSize: ...
    def default_str(self, robot_size: RobotSize) -> int: ...   # 2 × size − 1
    def default_dex(self, tl: int) -> int: ...          # ceil(TL / 2) + 1
    def effective_str(self, robot_size: RobotSize) -> int: ...
    def effective_dex(self, tl: int) -> int: ...
    def stat_label(self, robot_size: RobotSize, tl: int) -> str: ...
```

`Manipulator.build_item()` returns `None` (manipulators are shown in the
Manipulators section, not the Options section).

`Manipulator.slots` returns `0`; the robot is responsible for all manipulator
slot math (see below).

### `Robot.manipulators` Field

```python
manipulators: list[Manipulator] = Field(
    default_factory=lambda: [Manipulator(), Manipulator()]
)
```

**Position semantics** determine how each manipulator is priced and slotted:

- **Positions 0 and 1** — the standard slots included in the base chassis cost.
  A `Manipulator(size=None)` (or `size == robot_size`) here costs nothing extra
  and uses no additional slots. An absent position (list shorter than 2 entries)
  triggers a removal bonus.
- **Position 2 and beyond** — additional manipulators. Each uses slots from the
  percentage table and costs `Cr100 × resolved_size`.

Concrete examples:

```python
Robot(manipulators=[])
# No manipulators. Both standard slots removed.

Robot(manipulators=[Manipulator()])
# One standard manipulator. One standard slot removed.

Robot(manipulators=[Manipulator(), Manipulator()])
# Default pair. Same as not specifying manipulators at all.

Robot(manipulators=[Manipulator()] * 3)
# Default pair plus one additional manipulator of robot size.

Robot(manipulators=[Manipulator(size=7), Manipulator(size=5), Manipulator(size=3)])
# Two resized standard manipulators plus one additional.
```

`model_post_init` calls `m.bind(self)` for each manipulator so each instance has
access to robot context (TL, size) for TL checking and stat calculations.

`AdditionalManipulator` is removed from `ceres.make.robot.options` once the
migration is complete.

### Slot and Cost Rules

BCC includes exactly two manipulators of robot size. Net manipulator cost and slot
effects are computed by comparing the actual list against that baseline:

```text
std_cost  = Cr100 × robot_size
std_slots = max(1, ceil(0.10 × base_slots))

net_cost  = sum(m.cost  for m in manipulators) - 2 × std_cost
net_slots = sum(m.slots for m in manipulators) - 2 × std_slots
```

A negative `net_cost` is a credit (BCC includes more than what is installed);
that credit is capped at 20% of BCC:

```text
net_cost = max(net_cost, -0.20 × base_chassis_cost)
```

The current implementation omits this cap — a known bug fixed in Phase 1.

Each `Manipulator` exposes `cost` and `slots` reflecting its own size. Both are
set during `bind()` so the part has access to robot context:

```text
m.cost  = Cr100 × m.resolved_size
m.slots = max(1, ceil(pct(Δsize) × base_slots))
```

where `Δsize = m.resolved_size − robot_size` and `pct` follows the table:

| Δ (manip − robot) | % of base_slots | Minimum |
|:------------------|:----------------|:--------|
| +2                | 40%             | 1       |
| +1                | 20%             | 1       |
| ±0                | 10%             | 1       |
| −1                | 5%              | 1       |
| −2                | 2%              | 1       |
| ≤−3               | 1%              | 1       |

Maximum manipulator size = `robot_size + 2` (size 8 robots may go to size 10).

### STR/DEX Enhancement

STR enhancement: no slots; cost = `Cr100 × resolved_size × str_bonus²`.
Maximum `str_bonus ≤ default_str` (so max STR = 2 × default STR).

DEX enhancement: no slots; cost = `Cr200 × resolved_size × dex_bonus²`.
Maximum `dex_bonus` such that `effective_dex ≤ TL + 3`.

### Display

The Manipulators row shows statistics for each manipulator:

```text
2× (STR 9 DEX 7)
```

When manipulators differ:

```text
(STR 12 DEX 7), (STR 5 DEX 12), (STR 3 DEX 7)
```

The format used by the existing `AdditionalManipulator.description` property is
correct; apply the same format to all `Manipulator` instances. The detail section
of the spec should show slot and cost deltas per manipulator for non-standard cases.

## Walker Leg Integration

Walker robots may have legs converted to manipulators.

### `Leg` Class

```python
class Leg(CeresModel):
    model_config = {'frozen': True}
```

A plain leg: no manipulation capability, no slot effect beyond the locomotive
cost already included in BCC.

### `WalkerLocomotion.legs` Field

```python
class WalkerLocomotion(_LocomotionBase):
    ...
    legs: list[Leg | Manipulator] = Field(
        default_factory=lambda: [Leg(), Leg()]
    )
```

When a `Manipulator` appears in `legs`:

- Cost: `Cr100 × robot_size` per leg-manipulator.
- Size: fixed at robot size (leg size cannot be changed).
- These count as additional manipulators beyond the two standard arm positions.

The robot's total manipulator list for statistics, display, and cost purposes
combines `robot.manipulators` with `Manipulator` instances in
`robot.locomotion.legs` (when `WalkerLocomotion` is used).

## Migration Plan

### Phase 1 — `Manipulator` Model, Standard Cases, 20% Cap Fix

- Define `Manipulator` in `ceres.make.robot.manipulators` (new file).
- Migrate `Robot.manipulators: list[str]` to `list[Manipulator]`.
- Accept `'Standard'` strings during migration via a `model_validator` alias.
- Implement `_manipulator_slot_effect` and `_manipulator_cost_effect` in `Robot`.
- Fix the 20% BCC cap bug.
- Update `Robot.available_slots` and `Robot._raw_cost` to use the new properties.
- Update the Manipulators spec row and detail section to display `STR N DEX M`.
- Tests: verify STR/DEX display for a size 5 TL10 robot; verify the 20% cap for
  full removal; verify existing robots with the AG300 additional manipulator case.

### Phase 2 — Resized Standard Manipulators

- Implement net slot and cost delta for `Manipulator(size != robot_size)` in
  positions 0–1.
- Tests: verify StarTek's resized size 3 arm (`refs/robot/99_startek.md`).

### Phase 3 — STR/DEX Enhancement

- Implement `str_bonus` and `dex_bonus` with the quadratic cost formula and max
  limits.
- Tests: verify StarTek's arm enhancement (STR +3, expected Cr4500 per arm);
  verify max limits are enforced.

### Phase 4 — Walker Legs

- Implement `Leg` and update `WalkerLocomotion` with a `legs` field.
- Add leg-to-manipulator conversion cost to `_manipulator_cost_effect`.
- Include leg-manipulators in statistics and display.
- Tests: choose a reference robot with leg manipulators.

## Interpretations to Document in RULE_INTERPRETATIONS.md

1. **20% cap is combined**: removal and downsize credits share a single cap.
2. **Resizing slot formula**: "slots gained = standard slots − new slots". Document
   with a worked example since the source phrasing is ambiguous.
3. **Walker leg counting**: the source says "two original manipulators, adding four
   manipulators and altering the two default legs." This implies leg-manipulators
   do not count as the standard arm pair but as additional manipulators.

## Test Cases

- **Steward Droid** (`refs/robot/101_steward_droid.md`): size 4 standard pair,
  STR 7 DEX 7. Smoke test for Phase 1.
- **StarTek** (`refs/robot/99_startek.md`): resized size 3 arm (DEX +4) and two
  size 5 arms (STR +3). Verification for Phases 2 and 3.
- **AG300** (`tests/robots/test_ag300.py`): has an `AdditionalManipulator` today.
  Verify Phase 1 migration does not break existing assertions.

## Out of Scope

- Weapon mounts on manipulators (see `docs/plan-gear-backed-robot-options.md`).
- Athletics skill requirement for STR/DEX DM (display logic, not domain logic;
  document the interpretation but do not implement until skill display needs it.
- Biological manipulators (separate subdomain).
