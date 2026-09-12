"""Comfort Levels: how well a vehicle treats the people inside it.

Comfort Points come from the Spaces occupants sit in and from fittings such as
bunks, freshers and galleys. Shared between the occupants they serve, they give
a Comfort Level, which names how long people can stay aboard before it tells.

Rules: refs/vehicle/02_new_rules.md — Crew and Passenger Comfort
"""

# refs/vehicle/02_new_rules.md — Comfort Level, as (lower bound, name). A level
# on the boundary of two bands takes the better of them, so each band is read as
# starting at its lower bound.
_LEVELS: tuple[tuple[float, str], ...] = (
    (0.0, 'Intolerable'),
    (0.5, 'Uncomfortable Seating'),
    (1.0, 'Basic Seating'),
    (1.25, 'Long Duration Seating'),
    (1.5, 'Extended Seating'),
    (2.0, 'Basic Comfort'),
    (4.0, 'Standard Comfort'),
    (8.0, 'Good Comfort'),
    (24.0, 'Excellent Comfort'),
    (40.0, 'Luxury Comfort'),
)


def comfort_label(level: float) -> str:
    """Name the band a Comfort Level falls in."""
    return next(name for bound, name in reversed(_LEVELS) if level >= bound)
