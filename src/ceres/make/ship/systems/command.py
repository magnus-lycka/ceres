from typing import ClassVar, Literal

from ceres.shared import NoteList, _Note

from ..base import ShipBase
from .common import _ZeroPowerSystemPart

COMMAND_BRIDGE_MIN_DISPLACEMENT = 5_000


class BriefingRoom(_ZeroPowerSystemPart):
    system_type: Literal['BRIEFING_ROOM'] = 'BRIEFING_ROOM'
    description: Literal['Briefing Room'] = 'Briefing Room'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 4.0

    @property
    def cost(self) -> float:
        return 500_000.0


class CommandBridge(_ZeroPowerSystemPart):
    system_type: Literal['COMMAND_BRIDGE'] = 'COMMAND_BRIDGE'
    description: Literal['Command Bridge'] = 'Command Bridge'
    tons: ClassVar[float]
    cost: ClassVar[float]

    def bind(self, assembly: ShipBase) -> None:
        super().bind(assembly)
        if self.assembly.displacement <= COMMAND_BRIDGE_MIN_DISPLACEMENT:
            self.error('Command bridge requires displacement greater than 5000 tons')

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +1 to Tactics (naval) checks made within the command bridge')
        return notes

    @property
    def tons(self) -> float:
        return 40.0

    @property
    def cost(self) -> float:
        return 30_000_000.0

    @property
    def tactics_naval_dm(self) -> int:
        return 1
