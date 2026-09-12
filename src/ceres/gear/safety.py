"""Safety equipment.

Rules: refs/csc/10_survival_gear.md
"""

from ceres.shared import CeresPart, Equipment


class FireExtinguisherPart(CeresPart):
    """A handheld firefighting device.

    Single use: it reduces flame damage by half in the round it is used and
    stops it entirely thereafter.
    """

    tl: int = 5
    cost: float = 50.0
    mass_kg: float = 2.0

    @property
    def description(self) -> str:
        return 'Fire Extinguisher'


class FireExtinguisher(Equipment):
    """A fire extinguisher as bought on its own."""

    tl: int = 5

    def __init__(self, **data):
        data.setdefault('parts', [FireExtinguisherPart()])
        part = data['parts'][0]
        data.setdefault('cost', part.cost)
        data.setdefault('mass_kg', part.mass_kg)
        super().__init__(**data)
