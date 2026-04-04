from .base import Note, NoteCategory
from .parts import ShipPart


class Cockpit(ShipPart):
    power: float = 0.0
    holographic: bool = False

    def build_item(self) -> str | None:
        if self.holographic:
            return 'Holographic Cockpit'
        return 'Cockpit'

    def compute_tons(self) -> float:
        return 1.5

    def compute_cost(self) -> float:
        cost = 10_000
        if self.holographic:
            cost += 2_500
        return float(cost)


class Bridge(ShipPart):
    small: bool = False

    def build_item(self) -> str | None:
        if self.small:
            return 'Smaller Bridge'
        return 'Bridge'

    def build_notes(self) -> list[Note]:
        if self.small:
            return [Note(category=NoteCategory.INFO, message='DM -1 to Pilot checks')]
        return []

    def _standard_tons(self) -> float:
        displacement = self.owner.displacement
        if displacement <= 50:
            return 3.0
        if displacement <= 99:
            return 6.0
        if displacement <= 200:
            return 10.0
        if displacement <= 1_000:
            return 20.0
        if displacement <= 2_000:
            return 40.0
        if displacement <= 100_000:
            return 60.0
        extra_steps = (displacement - 100_001) // 100_000 + 1
        return 60.0 + extra_steps * 20.0

    def _small_tons(self) -> float:
        displacement = self.owner.displacement
        if displacement <= 99:
            return 3.0
        if displacement <= 200:
            return 6.0
        if displacement <= 1_000:
            return 10.0
        if displacement <= 2_000:
            return 20.0
        if displacement <= 100_000:
            return 40.0
        if displacement <= 200_000:
            return 60.0
        extra_steps = (displacement - 200_001) // 100_000 + 1
        return 60.0 + extra_steps * 20.0

    def compute_tons(self) -> float:
        if self.small:
            return self._small_tons()
        return self._standard_tons()

    def compute_cost(self) -> float:
        factor = 0.5 if self.small else 1
        cost = float(((self.owner.displacement - 1) // 100 + 1) * 500_000)
        return cost * factor

    @property
    def operations_dm(self) -> int:
        if self.small:
            return -1
        return 0
