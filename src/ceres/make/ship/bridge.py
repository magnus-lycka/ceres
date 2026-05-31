from bisect import bisect_left
from typing import ClassVar

from ceres.shared import CeresModel, NoteList, _Note

from .parts import ShipPart
from .spec import ShipSpec, SpecSection

BRIDGE_TABLE_MAX_DISPLACEMENT = 200_000
BRIDGE_TABLE_LIMITS = [50, 99, 200, 1_000, 2_000, 100_000]
BRIDGE_TABLE_TONS = [3.0, 6.0, 10.0, 20.0, 40.0, 60.0, 80.0]
BRIDGE_EXTRA_STEP_TONS = 100_000
DETACHABLE_BRIDGE_MINIMUMS = (
    (200, 15.0),
    (1_000, 30.0),
    (2_000, 50.0),
)
DETACHABLE_CAPITAL_BRIDGE_MINIMUM_TONS = 80.0


class Cockpit(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    holographic: bool = False
    dual: bool = False
    ejector_seat: bool = False

    def item_description(self) -> str:
        cockpit = 'Dual Cockpit' if self.dual else 'Cockpit'
        if self.holographic:
            cockpit = f'Holographic {cockpit}'
        if self.ejector_seat:
            seat = 'Ejector Seats' if self.seat_count > 1 else 'Ejector Seat'
            return f'{cockpit} with {seat}'
        return cockpit

    @property
    def seat_count(self) -> int:
        return 2 if self.dual else 1

    @property
    def tons(self) -> float:
        tons = 1.5
        if self.dual:
            tons += 2.5
        return tons

    @property
    def cost(self) -> float:
        cost = 10_000
        if self.holographic:
            cost += 2_500
        if self.dual:
            cost += 15_000
        if self.ejector_seat:
            cost += 5_000 * self.seat_count
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
    detachable: bool = False

    def item_description(self) -> str:
        if self.holographic:
            item = 'Smaller Holographic Controls' if self.small else 'Holographic Controls'
        elif self.small:
            item = 'Smaller Bridge'
        else:
            item = 'Standard Bridge'
        if self.detachable:
            return f'Detachable {item}'
        return item

    def bulkhead_label(self) -> str:
        return 'Bridge'

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        if self.small:
            notes.info('DM -1 for all checks related to spacecraft operations')
        if self.detachable and self.tons < self.detachable_minimum_tons:
            notes.error(
                f'Detachable bridge below minimum size: {self.tons:.2f} < {self.detachable_minimum_tons:.2f} tons'
            )
        return notes

    @property
    def tons(self) -> float:
        tons = self._base_tons
        if self.detachable:
            tons *= 1.2
        return tons

    @property
    def _base_tons(self) -> float:
        displacement = self.assembly.displacement
        if displacement <= BRIDGE_TABLE_MAX_DISPLACEMENT:
            ix = bisect_left(BRIDGE_TABLE_LIMITS, displacement)
            if ix > 0 and self.small:
                ix -= 1
            return BRIDGE_TABLE_TONS[ix]
        if self.small:
            displacement -= BRIDGE_EXTRA_STEP_TONS
        extra_steps = (displacement - (BRIDGE_EXTRA_STEP_TONS + 1)) // BRIDGE_EXTRA_STEP_TONS + 1
        return 60.0 + extra_steps * 20.0

    @property
    def cost(self) -> float:
        factor = 0.5 if self.small else 1
        cost = float(((self.assembly.displacement - 1) // 100 + 1) * 500_000)
        if self.holographic:
            cost *= 1.25
        if self.detachable:
            cost *= 1.5
        return cost * factor

    @property
    def power(self) -> float:
        return 0.0

    @property
    def operations_dm(self) -> int:
        if self.small:
            return -1
        return 0

    @property
    def detachable_minimum_tons(self) -> float:
        displacement = self.assembly.displacement
        for displacement_limit, minimum_tons in DETACHABLE_BRIDGE_MINIMUMS:
            if displacement <= displacement_limit:
                return minimum_tons
        return DETACHABLE_CAPITAL_BRIDGE_MINIMUM_TONS


class CommandSection(CeresModel):
    bridge: Bridge | None = None
    cockpit: Cockpit | None = None

    def _all_parts(self) -> list[ShipPart]:
        return [part for part in (self.bridge, self.cockpit) if part is not None]

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for part in (self.bridge, self.cockpit):
            if part is not None:
                spec.add_row(ship._spec_row_for_part(SpecSection.COMMAND, part))
