from bisect import bisect_left
from typing import ClassVar

from ceres.shared import CeresModel, NoteList, _Note

from .parts import ShipPart
from .spec import ShipSpec, SpecSection


class Cockpit(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    holographic: bool = False

    def build_item(self) -> str | None:
        if self.holographic:
            return 'Holographic Cockpit'
        return 'Cockpit'

    @property
    def tons(self) -> float:
        return 1.5

    @property
    def cost(self) -> float:
        cost = 10_000
        if self.holographic:
            cost += 2_500
        return float(cost)

    @property
    def power(self) -> float:
        return 0.0


class Bridge(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    small: bool = False
    holographic: bool = False

    def build_item(self) -> str | None:
        if self.holographic:
            if self.small:
                return 'Smaller Holographic Controls'
            return 'Holographic Controls'
        if self.small:
            return 'Smaller Bridge'
        return 'Standard Bridge'

    def bulkhead_label(self) -> str:
        return 'Bridge'

    def build_notes(self) -> list[_Note]:
        if self.small:
            notes = NoteList()
            notes.info('DM -1 for all checks related to spacecraft operations')
            return notes
        return []

    @property
    def tons(self) -> float:
        displacement = self.assembly.displacement
        if displacement <= 200_000:
            weight_limits = [50, 99, 200, 1000, 2000, 100_000]
            ix = bisect_left(weight_limits, displacement)
            if ix > 0 and self.small:
                ix -= 1
            return [3.0, 6.0, 10.0, 20.0, 40.0, 60.0, 80.0][ix]
        if self.small:
            displacement -= 100_000
        extra_steps = (displacement - 100_001) // 100_000 + 1
        return 60.0 + extra_steps * 20.0

    @property
    def cost(self) -> float:
        factor = 0.5 if self.small else 1
        cost = float(((self.assembly.displacement - 1) // 100 + 1) * 500_000)
        if self.holographic:
            cost *= 1.25
        return cost * factor

    @property
    def power(self) -> float:
        return 0.0

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
