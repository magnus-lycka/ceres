# Dragon Variant Status

This note compares the three Dragon reference variants with the current Ceres
model. The goal is not to chase the reference exports blindly, but to record
where we differ and which differences we believe we understand.

## Summary

| Variant | Metric | Reference | Ceres | Status |
| --- | --- | ---: | ---: | --- |
| Dragon | Cargo tons | 13.52 | 13.12 | Close |
| Dragon | Design cost | 308.250 MCr | 292.426 MCr | Still low |
| Dragon | Available power | 450 | 450 | Matches |
| Dragon | Total power load | 435 | 433 | Close |
| Revised Dragon | Cargo tons | 0.76 | 20.51 | Far off |
| Revised Dragon | Design cost | 292.855 MCr | 293.683 MCr | Close |
| Revised Dragon | Available power | 482 | 482 | Matches |
| Revised Dragon | Total power load | 426 | 429 | Close |
| Alt Dragon | Cargo tons | 1.82 | -19.57 | Far off |
| Alt Dragon | Design cost | 293.083 MCr | 346.391 MCr | Far off |
| Alt Dragon | Available power | 436 | 436 | Matches |
| Alt Dragon | Total power load | 436 | 453 | Far off |

## Dragon

What seems understood:

- Cargo is now very close to the reference. The remaining 0.40-ton delta is
  small enough that it is likely caused by one or two still-misaligned rule
  interpretations rather than a completely missing subsystem.
- Available power now matches exactly.
- Total power load is close.

What still looks unresolved:

- Design cost remains about 15.8 MCr lower than the reference.
- We no longer treat `Armored` on weapons, sensor stations, or missile
  magazines as a rules-backed modifier. That makes the model cleaner, but it
  also removes some cost that the reference export appears to have included one
  way or another.

## Revised Dragon

What seems understood:

- Design cost is now close to the reference.
- Available power matches exactly.
- Total power load is close.

What still looks unresolved:

- Cargo is still much too high in Ceres.
- The most likely explanations are customisation rules we do not yet model:
  - `Budget-Increased Size` on the manoeuvre drive
  - `Budget-Increased Size` on the power plant
  - `Very High Yield` on the particle barbettes
  - `Energy Efficient` on the point defense battery

In other words, Revised Dragon now looks like a mostly-good cost model with a
still-incomplete tonnage model.

## Alt Dragon

What seems understood:

- Available power matches exactly.

Why it still differs so much:

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

- power modelling is in reasonably good shape
- old pseudo-`armored` component modifiers were obscuring the real rule picture
- the next high-value work is ship customisation support, especially:
  - budget/increased-size drives and plants
  - reduced-size plants
  - selected weapon advantages
  - retro computers
