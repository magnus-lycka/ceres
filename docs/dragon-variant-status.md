# Dragon Variant Status

This note compares the three Dragon reference variants with the current Ceres
model after the life-support split into facility cost and people cost.

The goal is not to chase the reference exports blindly, but to record the
remaining differences and whether they look like:

- a likely missing rule in Ceres
- an intentional modeling choice
- or an inconsistency in the reference export

## Summary

| Variant | Metric | Reference | Ceres | Status |
| --- | --- | ---: | ---: | --- |
| Dragon | Cargo incl. stores | 18.00 | 18.00 | Matches |
| Dragon | Design cost | 308.250 MCr | 308.250 MCr | Matches |
| Dragon | Sales price | 277.425 MCr | 277.425 MCr | Matches |
| Dragon | Available power | 450 | 450 | Matches |
| Dragon | Total power load | 435 | 435 | Matches |
| Dragon | Fuel | 0.00 | 0.00 | Matches |
| Dragon | Life support | 22,000 | 29,000 | Ref looks inconsistent |
| Dragon | Crew salaries | 75,000 | 75,000 | Matches source crew |
| Revised Dragon | Cargo incl. stores | 5.24 | 5.24 | Matches |
| Revised Dragon | Design cost | 292.855 MCr | 292.855 MCr | Matches |
| Revised Dragon | Sales price | 263.570 MCr | 263.570 MCr | Matches |
| Revised Dragon | Available power | 482 | 482 | Matches |
| Revised Dragon | Total power load | 426 | 426 | Matches |
| Revised Dragon | Fuel | 0.00 | 0.00 | Matches |
| Revised Dragon | Life support | 30,000 | 29,000 | Ref looks inconsistent |
| Revised Dragon | Crew salaries | 77,000 | 77,000 | Matches source crew |
| Alt Dragon | Cargo incl. stores | 6.30 | 6.39 | Off by 0.09 |
| Alt Dragon | Design cost | 293.083 MCr | 293.063 MCr | Off by 0.020 MCr |
| Alt Dragon | Sales price | 263.775 MCr | 263.757 MCr | Off by 0.018 MCr |
| Alt Dragon | Available power | 436 | 436 | Matches |
| Alt Dragon | Total power load | 436 | 436 | Matches |
| Alt Dragon | Fuel | 0.00 | 0.00 | Matches |
| Alt Dragon | Life support | 7,750 | 24,750 | Ref looks inconsistent |
| Alt Dragon | Crew salaries | 68,000 | 68,000 | Matches source crew |

Reference cargo above is adjusted as `cargo + stores/spares`, because the
reference exports show those as two separate lines:

- Dragon: `13.52 + 4.48 = 18.00`
- Revised Dragon: `0.76 + 4.48 = 5.24`
- Alt Dragon: `1.82 + 4.48 = 6.30`

## Dragon

Everything physical and economic now matches exactly except life support.

Crew salary now matches exactly because the source crew manifest is carried into
the test case verbatim.

Ceres now emits warnings for the crew-rule deviations in the source:

- `ASTROGATOR above recommended count: 1 > 0`
- `GUNNER above recommended count: 6 > 5`
- `MAINTENANCE above recommended count: 1 > 0`

With the current split, Ceres is clearer about the life-support mismatch:

- `Facilities = 10,000`
- `People = 19,000`
- total `29,000`

The reference says `22,000`, which does not fit either:

- the reference crew count (`19`)

So the remaining life-support difference for standard Dragon looks like a
reference inconsistency, not a missing Ceres rule.

## Revised Dragon

Everything physical and economic now matches exactly except life support.

Crew salary now matches exactly because the source crew manifest is carried into
the test case verbatim.

Ceres now emits warnings for the crew-rule deviations in the source:

- `MAINTENANCE above recommended count: 1 > 0`
- `OFFICER above recommended count: 2 > 1`

With the current split, Ceres gives:

- `Facilities = 10,000`
- `People = 19,000`
- total `29,000`

The reference says `30,000`. That does not follow from either:

- the reference crew count (`19`)

So revised Dragon also looks like a case where the reference life-support line
is using a different or inconsistent estimate.

## Alt Dragon

Alt Dragon is still the one with real model differences left.

Remaining small physical/economic diffs:

- cargo including stores: `6.30` vs `6.3916`
- production cost: `293,083,146.67` vs `293,063,146.67`
- sales price: `263,774,832.00` vs `263,756,832.00`

Crew salary now matches exactly because the source crew manifest is carried into
the test case verbatim.

Ceres now emits warnings for the crew-rule deviations in the source:

- `MAINTENANCE above recommended count: 1 > 0`
- `MEDIC above recommended count: 1 > 0`

Life support is now much more obviously inconsistent in the reference. Ceres
computes:

- `Facilities = 7,750`
- `People = 17,000`
- total `24,750`

The reference says only `7,750`, which matches the facilities part alone and
appears to omit people entirely.

## Takeaway

- Standard Dragon is now effectively in agreement with the reference except for
  discretionary/possibly mistaken crew and an inconsistent life-support line.
- Revised Dragon is in the same situation, with one extra reference officer and
  another inconsistent life-support line.
- Alt Dragon still has small real model differences left, but the largest
  remaining expense mismatch is again the reference life-support line.
