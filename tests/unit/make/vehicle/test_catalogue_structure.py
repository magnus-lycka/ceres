"""Structure, checked against every published design the model can yet express.

Each case is a design printed in refs/vehicle/26_wehicle_catalogue.md, giving its
type, its Spaces and the Structure the book states. Nothing here is computed the
way the code computes it: the expected value is transcribed from the page.

This is the check that would have caught both earlier errors in RIV-001 and
RIV-002 on its own, so it is deliberately broad — it spans every Hull-per-Space
rate in use (0.2 airship, 0.5 rotorcraft and hovercraft, 2 ground, grav, walker
and watercraft, 3 submersible) and sizes from 2 Spaces to 20 million.

The nine catalogue designs carrying an AFV feature or a structural reinforcement
(Archangel, Brutus, Express Food Truck, G/hauler, Gunskiff, Horizon Hover Ferry,
Paladin Laser Grav Tank, Palanquin, Sky Dirge) are absent because the model
cannot express those modifiers yet. They belong here the moment it can, and the
Paladin especially — it is the design that decides RIV-002.
"""

import pytest

from ceres.make.vehicle.types import (
    AIRSHIP,
    GRAV_VEHICLE,
    GROUND_VEHICLE,
    ROTORCRAFT,
    SUBMERSIBLE,
    WALKER,
    WATERCRAFT,
)
from ceres.make.vehicle.vehicle import Vehicle

# (design, type, Spaces, printed Structure) — refs/vehicle/26_wehicle_catalogue.md
PUBLISHED = [
    ('Aerocar SuperTaxi', ROTORCRAFT, 6, 1),
    ('Air/Raft', GRAV_VEHICLE, 8, 2),
    ('Assault Monocycle', GROUND_VEHICLE, 2, 1),
    ('ATV', GROUND_VEHICLE, 20, 4),
    ('Destroyer', WATERCRAFT, 4_000, 800),
    ('Dirt Bike', GROUND_VEHICLE, 2, 1),
    ('Dracoflame', ROTORCRAFT, 3, 1),
    ('G/racer', GRAV_VEHICLE, 2, 1),
    ('Gecko', GROUND_VEHICLE, 9, 2),
    ('Hyper MagTube Car', GROUND_VEHICLE, 40, 8),
    ('Light Cargo Lifter', WALKER, 3, 1),
    ('Nautilus', SUBMERSIBLE, 370, 111),
    ('Prospecting Buggy', GRAV_VEHICLE, 8, 2),
    ('Public Safety Cruiser', GRAV_VEHICLE, 16, 4),
    ('Runabout', GRAV_VEHICLE, 3, 1),
    ('SkyStrike G/Fighter', GRAV_VEHICLE, 14, 3),
    ('Speeder', GRAV_VEHICLE, 4, 1),
    ('Titan Turtle', SUBMERSIBLE, 20_000_000, 6_000_000),
    ('Vyrtybyrd Touring RV', ROTORCRAFT, 100, 5),
    ('VoidSailor Mobile Home', AIRSHIP, 215, 5),
]


@pytest.mark.parametrize(('design', 'vehicle_type', 'spaces', 'structure'), PUBLISHED, ids=[c[0] for c in PUBLISHED])
def test_published_structure(design, vehicle_type, spaces, structure):
    vehicle = Vehicle(name=design, vehicle_type=vehicle_type, spaces=spaces, tl=vehicle_type.tl)
    assert vehicle.structure == structure
