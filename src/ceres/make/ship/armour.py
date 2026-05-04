from typing import ClassVar, Literal

from pydantic import Field

from .base import ShipBase
from .parts import ShipPart


class Armour(ShipPart):
    description: str
    protection: int
    tl: int = Field(default=0, exclude=True)

    _cost_per_ton: ClassVar[int] = 0
    _tonnage_consumed: ClassVar[int] = 0

    def bind(self, assembly: ShipBase) -> None:
        super().bind(assembly)
        self.check_protection_limit()

    def check_protection_limit(self) -> None:
        pass

    def build_item(self) -> str | None:
        return f'{self.description}, Armour: {self.protection}'

    def compute_cost(self) -> float:
        return self.compute_tons() * self._cost_per_ton

    def compute_tons(self) -> float:
        displacement = self.assembly.displacement
        if displacement < 5:
            self.error('Displacement must be at least 5 tons for armour.')
            return 0.0
        if displacement < 16:
            size_factor = 4
        elif displacement < 26:
            size_factor = 3
        elif displacement < 100:
            size_factor = 2
        else:
            size_factor = 1
        armour_volume_modifier = self.assembly.armour_volume_modifier
        return displacement * self._tonnage_consumed * self.protection * size_factor * armour_volume_modifier


class TitaniumSteelArmour(Armour):
    description: Literal['Titanium Steel'] = 'Titanium Steel'
    _tl: ClassVar[int] = 7
    _cost_per_ton = 50_000
    _tonnage_consumed = 0.025

    def check_protection_limit(self) -> None:
        tl = self.assembly.tl
        if self.protection > tl:
            self.error(f'Protection {self.protection} exceeds TL{tl}')
        elif self.protection > 9:
            self.error(f'Protection {self.protection} exceeds maximum 9 for Titanium Steel')


class CrystalironArmour(Armour):
    description: Literal['Crystaliron'] = 'Crystaliron'
    _tl: ClassVar[int] = 10
    _cost_per_ton = 200_000
    _tonnage_consumed = 0.0125

    def check_protection_limit(self) -> None:
        tl = self.assembly.tl
        if self.protection > tl:
            self.error(f'Protection {self.protection} exceeds TL{tl}')
        elif self.protection > 13:
            self.error(f'Protection {self.protection} exceeds maximum 13 for Crystaliron')


class BondedSuperdenseArmour(Armour):
    description: Literal['Bonded Superdense'] = 'Bonded Superdense'
    _tl: ClassVar[int] = 14
    _cost_per_ton = 500_000
    _tonnage_consumed = 0.008

    def check_protection_limit(self) -> None:
        tl = self.assembly.tl
        if self.protection > tl:
            self.error(f'Protection {self.protection} exceeds TL{tl}')


class MolecularBondedArmour(Armour):
    description: Literal['Molecular Bonded'] = 'Molecular Bonded'
    _tl: ClassVar[int] = 16
    _cost_per_ton = 1_500_000
    _tonnage_consumed = 0.005

    def check_protection_limit(self) -> None:
        tl = self.assembly.tl
        if self.protection > tl + 4:
            self.error(f'Protection {self.protection} exceeds TL{tl}+4')
