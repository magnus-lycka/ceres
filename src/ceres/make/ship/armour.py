from typing import ClassVar, Literal

from pydantic import Field

from .base import ShipBase
from .parts import ShipPart


class Armour(ShipPart):
    description: str
    protection: int
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    _cost_per_ton: ClassVar[int] = 0
    _tonnage_consumed: ClassVar[int] = 0

    def bind(self, assembly: ShipBase) -> None:
        super().bind(assembly)
        self.check_protection_limit()

    def check_protection_limit(self) -> None:
        limit = self.protection_limit()
        if self.protection > limit:
            if self._military_hull():
                self.error(f'Protection {self.protection} exceeds military hull cap {limit}')
            else:
                self.error(self.protection_limit_error(limit))

    def protection_limit(self) -> int:
        limit = self.normal_protection_limit()
        if self._military_hull():
            return limit * 2
        return limit

    def normal_protection_limit(self) -> int:
        return self.assembly.tl

    def protection_limit_error(self, limit: int) -> str:
        return f'Protection {self.protection} exceeds TL{limit}'

    def _military_hull(self) -> bool:
        ship_hull = getattr(self.assembly, 'hull', None)
        configuration = getattr(ship_hull, 'configuration', None)
        return bool(getattr(configuration, 'military', False))

    def item_description(self) -> str:
        return f'{self.description}, Armour: {self.protection}'

    @property
    def cost(self) -> float:
        return self.tons * self._cost_per_ton

    @property
    def tons(self) -> float:
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

    @property
    def power(self) -> float:
        return 0.0


class TitaniumSteelArmour(Armour):
    description: Literal['Titanium Steel'] = 'Titanium Steel'
    tl: int = Field(default=7, exclude=True)
    _cost_per_ton = 50_000
    _tonnage_consumed = 0.025

    def normal_protection_limit(self) -> int:
        return min(self.assembly.tl, 9)

    def protection_limit_error(self, limit: int) -> str:
        if limit == self.assembly.tl:
            return f'Protection {self.protection} exceeds TL{limit}'
        return f'Protection {self.protection} exceeds maximum 9 for Titanium Steel'


class CrystalironArmour(Armour):
    description: Literal['Crystaliron'] = 'Crystaliron'
    tl: int = Field(default=10, exclude=True)
    _cost_per_ton = 200_000
    _tonnage_consumed = 0.0125

    def normal_protection_limit(self) -> int:
        return min(self.assembly.tl, 13)

    def protection_limit_error(self, limit: int) -> str:
        if limit == self.assembly.tl:
            return f'Protection {self.protection} exceeds TL{limit}'
        return f'Protection {self.protection} exceeds maximum 13 for Crystaliron'


class BondedSuperdenseArmour(Armour):
    description: Literal['Bonded Superdense'] = 'Bonded Superdense'
    tl: int = Field(default=14, exclude=True)
    _cost_per_ton = 500_000
    _tonnage_consumed = 0.008


class MolecularBondedArmour(Armour):
    description: Literal['Molecular Bonded'] = 'Molecular Bonded'
    tl: int = Field(default=16, exclude=True)
    _cost_per_ton = 1_500_000
    _tonnage_consumed = 0.005

    def normal_protection_limit(self) -> int:
        return self.assembly.tl + 4

    def protection_limit_error(self, limit: int) -> str:
        return f'Protection {self.protection} exceeds TL{self.assembly.tl}+4'
