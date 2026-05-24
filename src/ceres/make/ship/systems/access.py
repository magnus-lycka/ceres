from typing import ClassVar, Literal

from ceres.shared import NoteList, _Note

from ..base import ShipBase
from .common import _ZeroPowerSystemPart
from .security import BoobyTrap


class Airlock(_ZeroPowerSystemPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    size: float = 2.0
    booby_trap: BoobyTrap | None = None

    def item_description(self) -> str:
        return f'Airlock ({self.size:g} tons)'

    def bind(self, assembly: ShipBase) -> None:
        super().bind(assembly)
        if self.booby_trap is not None:
            self.booby_trap.check_tl(self)

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        if self.booby_trap is not None:
            notes.info(f'Booby-trapped: {self.booby_trap.damage_per_round} damage/round')
        return notes

    def am_i_for_free(self) -> bool:
        if self.assembly.displacement < 100:
            return False
        free_airlocks = self.assembly.displacement // 100
        hull = self.assembly.hull
        if hull is None:
            return False
        siblings = hull.airlocks
        index = next((i for i, sibling in enumerate(siblings) if sibling is self), -1)
        if index < 0:
            return False
        return index < free_airlocks

    @property
    def tons(self) -> float:
        if self.am_i_for_free():
            return 0.0
        return max(self.size, 2.0)

    @property
    def cost(self) -> float:
        trap_cost = 0.0 if self.booby_trap is None else self.booby_trap.cost
        if self.am_i_for_free():
            return trap_cost
        return self.tons * 100_000.0 + trap_cost


class BreachingTube(_ZeroPowerSystemPart):
    system_type: Literal['BREACHING_TUBE'] = 'BREACHING_TUBE'
    description: Literal['Breaching Tube'] = 'Breaching Tube'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 3.0

    @property
    def cost(self) -> float:
        return 3_000_000.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        notes.info('DM +1 to Boarding Actions rolls')
        notes.info('Can only attach to disabled or otherwise inert ships')
        notes.info('Destroyed if either ship moves while attached; attached ship receives 2D damage')
        return notes


_FORCED_LINKAGE_TABLE: dict[str, tuple[int, int, float]] = {
    'Basic': (7, -2, 50_000.0),
    'Improved': (9, -1, 75_000.0),
    'Enhanced': (12, 0, 100_000.0),
    'Advanced': (15, 2, 500_000.0),
}


class ForcedLinkageApparatus(_ZeroPowerSystemPart):
    system_type: Literal['FORCED_LINKAGE_APPARATUS'] = 'FORCED_LINKAGE_APPARATUS'
    tl: int = 0
    tons: ClassVar[float]
    cost: ClassVar[float]
    tier: Literal['Basic', 'Improved', 'Enhanced', 'Advanced']

    def __init__(self, **data):
        if 'tier' in data:
            data['tl'] = _FORCED_LINKAGE_TABLE[data['tier']][0]
        super().__init__(**data)

    def item_description(self) -> str:
        return f'Forced Linkage Apparatus ({self.tier})'

    @property
    def pilot_check_dm(self) -> int:
        return _FORCED_LINKAGE_TABLE[self.tier][1]

    @property
    def tons(self) -> float:
        return 2.0

    @property
    def cost(self) -> float:
        return _FORCED_LINKAGE_TABLE[self.tier][2]

    def bind(self, assembly: ShipBase) -> None:
        super().bind(assembly)
        if self.assembly.displacement > 5_000:
            self.error('Forced linkage apparatus may only be used on ships of 5000 tons or less')

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        notes.info(f'Pilot check DM {self.pilot_check_dm:+d}')
        notes.info('Requires Thrust advantage of at least 1 over the target')
        notes.info('Cannot target ships above 5000 tons')
        notes.info('May be combined with a breaching tube')
        return notes
