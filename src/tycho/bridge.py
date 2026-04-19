from bisect import bisect_left

from .base import CeresModel, Note, NoteCategory
from .parts import ShipPart
from .spec import ShipSpec, SpecSection


class Cockpit(ShipPart):
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
    holographic: bool = False

    def build_item(self) -> str | None:
        smaller = 'Smaller ' if self.small else ''
        holo = ' (Holographic)' if self.holographic else ''
        return f'{smaller}Bridge{holo}'

    def bulkhead_label(self) -> str:
        return 'Bridge'

    def build_notes(self) -> list[Note]:
        if self.small:
            return [
                Note(
                    category=NoteCategory.INFO,
                    message='DM -1 for all checks related to spacecraft operations',
                )
            ]
        return []

    def compute_tons(self) -> float:
        displacement = self.owner.displacement
        if displacement <= 200_000:
            weight_limits = [50, 99, 200, 1000, 2000, 100_000]
            ix = bisect_left(weight_limits, displacement)
            if ix > 0 and self.small:
                ix -= 1
            return [3.0, 6.0, 10.0, 20.0, 40.0, 60.0, 80.0][ix]
        # more than 200 000
        if self.small:
            displacement -= 100_000
        extra_steps = (displacement - 100_001) // 100_000 + 1
        return 60.0 + extra_steps * 20.0

    def compute_cost(self) -> float:
        factor = 0.5 if self.small else 1
        cost = float(((self.owner.displacement - 1) // 100 + 1) * 500_000)
        if self.holographic:
            cost *= 1.25
        return cost * factor

    @property
    def operations_dm(self) -> int:
        if self.small:
            return -1
        return 0


class CommandSection(CeresModel):
    bridge: Bridge | None = None
    cockpit: Cockpit | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        for part in (self.bridge, self.cockpit):
            if part is not None:
                parts.append(part)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for part in (self.bridge, self.cockpit):
            if part is not None:
                spec.add_row(ship._spec_row_for_part(SpecSection.COMMAND, part))
