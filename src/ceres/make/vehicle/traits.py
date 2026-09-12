"""Vehicle traits: named properties a design has rather than buys.

A trait is not bought and has no cost of its own. It arrives from the vehicle's
type, its size band, or a feature, and carries rules consequences wherever the
rules name it.

Vehicle traits are their own vocabulary. A trait from the robot or ship domains
is not meaningful here even where the word is the same (see CONTEXT.md).

Rules: refs/vehicle/02_new_rules.md — Vehicle Traits
"""

from enum import StrEnum


class Trait(StrEnum):
    """A named property of a vehicle.

    Only the traits the type and size tables currently produce are named. Traits
    granted by features join them as features are modelled.
    """

    ATV = 'ATV'
    UNRESPONSIVE = 'Unresponsive'
    VTOL = 'VTOL'

    def __str__(self) -> str:
        return self.value
