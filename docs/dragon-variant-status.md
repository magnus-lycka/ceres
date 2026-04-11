# Dragon Variant Status

This note compares the three Dragon reference variants with the current Ceres
model. The goal is not to chase the reference exports blindly, but to record
where we differ, which differences are explained by known rule choices or
missing features, and which differences still look like something is wrong in
Ceres, the reference export, or our understanding of the rules.

## Summary

| Variant | Metric | Reference | Ceres | Status |
| --- | --- | ---: | ---: | --- |
| Dragon | Cargo incl. stores | 18.00 | 16.90 | Off by 1.10 |
| Dragon | Design cost | 308.250 MCr | 308.470 MCr | Off by 0.220 MCr |
| Dragon | Sales price | 277.425 MCr | 277.623 MCr | Off by 0.198 MCr |
| Dragon | Available power | 450 | 450 | Matches |
| Dragon | Total power load | 435 | 433 | Off by 2; explanation still incomplete |
| Revised Dragon | Cargo incl. stores | 5.24 | 27.01 | Far off |
| Revised Dragon | Design cost | 292.855 MCr | 309.183 MCr | Far off |
| Revised Dragon | Sales price | 263.570 MCr | 278.265 MCr | Far off |
| Revised Dragon | Available power | 482 | 482 | Matches |
| Revised Dragon | Total power load | 426 | 429 | Off by 3; likely tied to missing customisations |
| Alt Dragon | Cargo incl. stores | 6.30 | -23.97 | Far off |
| Alt Dragon | Design cost | 293.083 MCr | 357.271 MCr | Far off |
| Alt Dragon | Sales price | 263.775 MCr | 321.544 MCr | Far off |
| Alt Dragon | Available power | 436 | 436 | Matches |
| Alt Dragon | Total power load | 436 | 453 | Far off |

Reference cargo above is adjusted as `cargo + stores/spares`, because the
reference exports show those as two separate lines:

- Dragon: `13.52 + 4.48 = 18.00`
- Revised Dragon: `0.76 + 4.48 = 5.24`
- Alt Dragon: `1.82 + 4.48 = 6.30`

## Dragon Tables Remaining Difference

These are intentionally kept as two separate tables before any attempt to
reconcile structure.

### Reference Dragon

Verified totals:

- Original Tons sum: `800.00`
- Original Cost sum: `308,250,000 Cr`

- Remaining Tons sum: `59.00`
- Remaining Cost sum: `6,700,000 Cr`

| Section | Item | Tons | Cost (Cr) |
| --- | --- | ---: | ---: |
| Hull | Armored Bulkhead for M-Drive M-Drive: 7 | 2.80 | 560,000 |
| Hull | Armored Bulkheads | 3.00 | 600,000 |
| Hull | Armored Bulkheads | 1.20 | 240,000 |
| Command | Bridge Standard Bridge | 20.00 | 2,000,000 |
| Command | Main Bridge Holographic Controls | 0.00 | 500,000 |
| Hull | Armored Bulkheads | 2.00 | 400,000 |
| Hull | Armored Bulkhead for 2x Additional Sensor Stations | 0.20 | 40,000 |
| Hull | Armored Bulkhead | 1.30 | 260,000 |
| Hull | Armored Bulkhead for Weapons 2x Barbette: Particle Barbette | 1.00 | 200,000 |
| Weapons | 1x Small Bay: Missile Bay (S), Adv - Size Reduction x3 | 35.00 | 18,000,000 |
| Hull | Armored Bulkhead for 1x Small Bay: Missile Bay (S), Adv - Size Reduction x3 | 3.50 | 700,000 |
| Weapons | 1x Point Defense Battery: Type II -L | 20.00 | 10,000,000 |
| Hull | Armored Bulkhead for 1x Point Defense Battery: Type II -L | 2.00 | 400,000 |
| Cargo | Cargo 1x 13.52 Ton Cargo Bay | 13.52 | 0 |
| Cargo | Supplies Stores and Spares: 112.00 Days | 4.48 | 0 |
| Hull | Armored Bulkhead for Magazine Missile Storage (480) | 4.00 | 800,000 |

### Ceres `test_dragon`

Verified totals:

- Tons sum: `800.00`
- Cost sum: `308,250,000 Cr`

- Remaining Tons sum: `59.00`
- Remaining Cost sum: `6,700,000 Cr`

| Section | Item | Tons | Cost (Cr) |
| --- | --- | ---: | ---: |
| Hull | Basic Ship Systems | 0.00 | 0 |
| Hull | Armoured Bulkheads | 21.00 | 4,200,000 |
| Command | Bridge (Holographic) | 20.00 | 2,500,000 |
| Cargo | Cargo Hold | 18.00 | 0 |


## Dragon Table Verified Agreement

- Tons sum: `?`
- Cost sum: `?`

| Item ref | Item test | Tons | Cost (Cr) |
|----------|-----------|-----:|----------:|
| Streamlined-Needle, Reinforced Hull | Streamlined-Needle Hull | 400.00 | 36,000,000 |
| Improved Stealth | Improved Stealth | 0.00 | 40,000,000 |
| Radiation Shielding: Reduce Rads by 1,000 | Radiation Shielding: Reduce Rads by 1,000 | 0.00 | 10,000,000 |
| Armor Crystaliron: 13 | Crystaliron, Armour: 13 | 78.00 | 15,600,000 |
| Power Plant Fusion TL 12 Output: 450 | Fusion (TL 12) | 30.00 | 30,000,000 |
| Fuel 16 Weeks of Operation | 16 weeks of operation | 12.00 | 0 |
| Computer Comp/25/fib | Computer/25/fib | 0.00 | 15,000,000 |
| B/U Comp/20/fib | Backup Computer/20/fib | 0.00 | 7,500,000 |
| Software Library | Library | 0.00 | 0 |
| Intellect | Intellect | 0.00 | 0 |
| Auto-Repair/1 | Auto-Repair/1 | 0.00 | 5,000,000 |
| Evade/1 | Evade/1 | 0.00 | 1,000,000 |
| 1x Countermeasures Suite | Countermeasures Suite | 2.00 | 4,000,000 |
| 1x Enhanced Signal Processing | Enhanced Signal Processing | 2.00 | 8,000,000 |
| 1x Extended Arrays | Extended Arrays | 6.00 | 8,600,000 |
| Systems Repair Drones | Repair Drones | 4.00 | 800,000 |
| Fuel Scoops: Included Free w/ Streamlining | Fuel Scoops | 0.00 | 0 |
| 1x Crew Armory: Supports 25 Crew | Crew Armory: Supports 25 Crew | 1.00 | 250,000 |
| 1x Biosphere | Biosphere | 4.00 | 800,000 |
| 1x Medical Bay | Medical Bay | 4.00 | 2,000,000 |
| Training Facility: 2-person capacity | Training Facility: 2-person capacity | 4.00 | 800,000 |
| 1x Workshop | Workshop | 6.00 | 900,000 |



## Dragon

- Available power matches exactly.
- Adjusted cargo is now the right comparison: reference `18.00` versus Ceres
  `16.90`.
- That remaining `1.10` tons is not a rounding issue and should be treated as a
  real rule or modeling mismatch until explained.
- Total power load is 2 points lower than the reference and remains
  unexplained.
- Design cost is now `0.220 MCr` higher than the reference. That is close, but
  still unexplained.

## Revised Dragon

- Available power matches exactly.
- Adjusted cargo is still much too high in Ceres.
- Design cost is now also too high in Ceres.
- The biggest known explanations are customisation rules we do not yet model:
  - `Budget-Increased Size` on the manoeuvre drive
  - `Budget-Increased Size` on the power plant
  - `Very High Yield` on the particle barbettes
  - `Energy Efficient` on the point defense battery
- Those missing rules plausibly explain much of the tonnage and power-load
  mismatch, but they do not yet explain the full cost picture cleanly.

## Alt Dragon

- Available power matches exactly.
- The variant still differs heavily because several explicit reference features
  are not modeled:

- `Core/40/fib (Retro*)` is not modelled. We use a normal `Core/40/fib`, which
  is vastly more expensive.
- `Reduced Size` power plant is not modelled.
- `Emergency Power System` is not modelled.
- `Rapid Deployment Extended Arrays` is not modelled.
- `Basic Autodoc` is not modelled.
- The accommodation layout in the reference is not modelled; we still use a
  much simpler habitation model.

So Alt Dragon is still best treated as an unsupported-features stress case,
not as a near-match target.

## Takeaway

The three variants suggest:

- available power modelling is in reasonably good shape
- old pseudo-`armored` component modifiers were obscuring the real rule picture
- the next high-value work is ship customisation support, especially:
  - budget/increased-size drives and plants
  - reduced-size plants
  - selected weapon advantages
  - retro computers
