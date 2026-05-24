from math import ceil
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import CeresModel, NoteList, _Note

from ..parts import ShipPart
from .common import _ExplicitTonsSystemPart, _ZeroPowerSystemPart


class Armoury(_ZeroPowerSystemPart):
    system_type: Literal['ARMOURY'] = 'ARMOURY'
    description: Literal['Armoury'] = 'Armoury'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def cost(self) -> float:
        return 250_000.0


class PsionicShielding(ShipPart):
    system_type: Literal['PSIONIC_SHIELDING'] = 'PSIONIC_SHIELDING'
    description: Literal['Psionic Shielding'] = 'Psionic Shielding'
    tl: int = 12
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        displacement = self.assembly.displacement
        if displacement < 100:
            notes.info('Psionic shielding makes ships under 100 tons impenetrable to Clairvoyance and Telepathy')
        elif displacement <= 300:
            notes.info('DM-4 to Clairvoyance and Telepathy powers within or upon the ship')
        elif displacement <= 500:
            notes.info('DM-2 to Clairvoyance and Telepathy powers within or upon the ship')
        else:
            notes.info('No Clairvoyance or Telepathy DM for ships above 500 tons')
        return notes

    @property
    def tons(self) -> float:
        return self.assembly.displacement * 0.01

    @property
    def cost(self) -> float:
        return self.tons * 500_000.0

    @property
    def power(self) -> float:
        return 0.0


class AdvancedPsionicShielding(ShipPart):
    system_type: Literal['ADVANCED_PSIONIC_SHIELDING'] = 'ADVANCED_PSIONIC_SHIELDING'
    description: Literal['Advanced Psionic Shielding'] = 'Advanced Psionic Shielding'
    tl: int = 16
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Advanced psionic shielding consumes no tonnage')
        return notes

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        return ceil(self.assembly.displacement / 100) * 1_000_000.0

    @property
    def power(self) -> float:
        return 0.0


class Vault(_ExplicitTonsSystemPart):
    system_type: Literal['VAULT'] = 'VAULT'
    description: Literal['Vault'] = 'Vault'
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def cost(self) -> float:
        return self.tons * 500_000.0

    @property
    def power(self) -> float:
        return 0.0

    @property
    def content_armour(self) -> int:
        return min(10, int(self.tons))

    @property
    def content_hull_points(self) -> int:
        return int(self.tons // 5)

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        if self.tons < 4 or self.tons > 40:
            notes.error('Vault size must be between 4 and 40 tons')
        notes.info('Vault armour and Hull points protect contents only, not the ship')
        notes.info('Contents can survive in vacuum for a limited time if the ship is destroyed')
        return notes


class _BoobyTrap(CeresModel):
    trap_type: str
    tl: int
    cost: float
    damage_per_round: str

    def check_tl(self, part: ShipPart) -> None:
        if part.assembly_tl < self.tl:
            part.error(f'Requires TL{self.tl}, ship is TL{part.assembly_tl}')


class BoobyTrapTL6(_BoobyTrap):
    trap_type: Literal['BOOBY_TRAP_TL6'] = 'BOOBY_TRAP_TL6'
    tl: Literal[6] = 6
    cost: float = 100_000.0
    damage_per_round: Literal['3D'] = '3D'


class BoobyTrapTL8(_BoobyTrap):
    trap_type: Literal['BOOBY_TRAP_TL8'] = 'BOOBY_TRAP_TL8'
    tl: Literal[8] = 8
    cost: float = 300_000.0
    damage_per_round: Literal['5D'] = '5D'


class BoobyTrapTL10(_BoobyTrap):
    trap_type: Literal['BOOBY_TRAP_TL10'] = 'BOOBY_TRAP_TL10'
    tl: Literal[10] = 10
    cost: float = 500_000.0
    damage_per_round: Literal['6D'] = '6D'


class BoobyTrapTL12(_BoobyTrap):
    trap_type: Literal['BOOBY_TRAP_TL12'] = 'BOOBY_TRAP_TL12'
    tl: Literal[12] = 12
    cost: float = 1_000_000.0
    damage_per_round: Literal['8D'] = '8D'


type BoobyTrap = Annotated[
    BoobyTrapTL6 | BoobyTrapTL8 | BoobyTrapTL10 | BoobyTrapTL12,
    Field(discriminator='trap_type'),
]
