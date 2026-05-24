from typing import ClassVar, Literal

from ceres.shared import NoteList, _Note

from ..parts import ShipPart
from .common import _ZeroPowerSystemPart


class Aerofins(_ZeroPowerSystemPart):
    description: Literal['Aerofins'] = 'Aerofins'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def atmospheric_pilot_dm(self) -> int:
        return 2

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +2 to Pilot checks in atmosphere')
        return notes

    @property
    def tons(self) -> float:
        return self.assembly.displacement * 0.05

    @property
    def cost(self) -> float:
        return self.tons * 100_000.0


class HolographicHull(ShipPart):
    system_type: Literal['HOLOGRAPHIC_HULL'] = 'HOLOGRAPHIC_HULL'
    description: Literal['Holographic Hull'] = 'Holographic Hull'
    tl: int = 10
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        return self.assembly.displacement * 100_000.0

    @property
    def power(self) -> float:
        return self.assembly.displacement / 2.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        notes.info('Can change hull colours, add graphics, and alter visual appearance without changing shape')
        return notes


class TowCable(_ZeroPowerSystemPart):
    system_type: Literal['TOW_CABLE'] = 'TOW_CABLE'
    tl: int = 7
    description: Literal['Tow Cable'] = 'Tow Cable'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return self.assembly.displacement * 0.01

    @property
    def cost(self) -> float:
        return self.assembly.displacement * 0.01 * 5_000


class GrapplingArm(_ZeroPowerSystemPart):
    system_type: Literal['GRAPPLING_ARM'] = 'GRAPPLING_ARM'
    tl: int = 9
    description: Literal['Grappling Arm'] = 'Grappling Arm'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 2.0

    @property
    def cost(self) -> float:
        return 1_000_000.0
