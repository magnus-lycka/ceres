from math import ceil
from typing import ClassVar, Literal

from ceres.shared import NoteList, _Note

from ..parts import ShipPart


class GravScreen(ShipPart):
    system_type: Literal['GRAV_SCREEN'] = 'GRAV_SCREEN'
    description: Literal['Grav Screen'] = 'Grav Screen'
    tl: int = 12
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Blocks densitometers; the presence of a grav screen is obvious to sensor operators')
        return notes

    @property
    def tons(self) -> float:
        return float(ceil(self.assembly.displacement / 200))

    @property
    def cost(self) -> float:
        return self.tons * 1_000_000.0

    @property
    def power(self) -> float:
        return self.tons * 2.0


class GravityWellGenerator(ShipPart):
    system_type: Literal['GRAVITY_WELL_GENERATOR'] = 'GRAVITY_WELL_GENERATOR'
    description: Literal['Gravity Well Generator'] = 'Gravity Well Generator'
    tl: int = 16
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Creates an artificial gravity well; tactical effects are out of scope')
        return notes

    @property
    def tons(self) -> float:
        return 100.0

    @property
    def cost(self) -> float:
        return 120_000_000.0

    @property
    def power(self) -> float:
        return 500.0


class JumpFilter(ShipPart):
    system_type: Literal['JUMP_FILTER'] = 'JUMP_FILTER'
    description: Literal['Jump Filter'] = 'Jump Filter'
    tl: int = 14
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    bandwidth: ClassVar[int] = 5

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Analyses witnessed jumps to help predict destination; operational effects are out of scope')
        return notes

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        return 5_000_000.0

    @property
    def power(self) -> float:
        return 1.0
