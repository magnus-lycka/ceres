"""Armour: Protection on each of a vehicle's six faces.

A vehicle is armoured face by face. Every face starts at the Base Protection its
Tech Level provides; added armour is then allocated across the faces, and may be
moved between them. Only the base case is modelled so far.

Rules: refs/vehicle/07_armour.md
"""

from enum import StrEnum

from pydantic import BaseModel


class Face(StrEnum):
    """One of a vehicle's six sides.

    The Vehicle Handbook borrows maritime naming so there is no confusion about
    which face is which. Declared in the order the catalogue prints them.
    """

    FORWARD = 'Forward'
    PORT = 'Port'
    DORSAL = 'Dorsal'
    AFT = 'Aft'
    STARBOARD = 'Starboard'
    VENTRAL = 'Ventral'


# refs/vehicle/07_armour.md — Vehicle Armour: Base Protection from Tech Level.
_BASE_PROTECTION: tuple[tuple[int, int], ...] = (
    (0, 0),
    (3, 1),
    (5, 2),
    (7, 3),
    (10, 5),
    (12, 6),
    (14, 8),
    (16, 10),
    (17, 15),
    (18, 20),
)


def base_protection(tl: int) -> int:
    """The Protection a vehicle's materials give it for free at this Tech Level."""
    return next(protection for threshold, protection in reversed(_BASE_PROTECTION) if tl >= threshold)


class Armour(BaseModel):
    """What a vehicle's six faces are protected by.

    Held as one object rather than six numbers because the rules treat the
    allocation as a whole: points move between faces, no face may fall below the
    Base Protection, and the total is bounded by the Tech Level's maximum.
    """

    tl: int
    faces: dict[Face, int]

    def protection(self, face: Face) -> int:
        return self.faces[face]

    def against_small_arms(self, face: Face) -> int:
        """Protection including the Tech Level bonus (RIV-003).

        The bonus applies to attacks that are not critical hits, not Destructive
        and do not have a non-stun Blast trait.
        """
        return self.protection(face) + self.tl

    @classmethod
    def unarmoured(cls, tl: int) -> Armour:
        """A vehicle that has bought no armour, protected only by its materials."""
        protection = base_protection(tl)
        return cls(tl=tl, faces=dict.fromkeys(Face, protection))
