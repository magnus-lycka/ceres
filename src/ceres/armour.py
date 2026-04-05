from typing import ClassVar, Literal

from .base import ShipBase
from .parts import ShipPart


class Armour(ShipPart):
    power: float = 0.0
    description: str
    protection: int
    _min_tl: ClassVar[int] = 0
    _cost_per_ton: ClassVar[int] = 0
    _tonnage_consumed: ClassVar[int] = 0

    def bind(self, owner: ShipBase) -> None:
        super().bind(owner)
        self.check_protection_limit()

    def _effective_tl(self) -> int | None:
        """Resolve the TL to use for protection-limit checks.

        Returns None and adds an error note if the TL is invalid.
        """
        if self.tl:
            if self.owner.tl < self.tl:
                self.error(f'Ship TL{self.owner.tl} is below armour TL{self.tl}')
                return None
            tl = self.tl
        else:
            tl = self.owner.tl
        if tl < self._min_tl:
            self.error(f'{self.description} requires TL{self._min_tl}')
            return None
        return tl

    def check_protection_limit(self) -> None:
        pass

    def build_item(self) -> str | None:
        return f'{self.description}, Armour: {self.protection}'

    def compute_cost(self) -> float:
        return self.compute_tons() * self._cost_per_ton

    def compute_tons(self) -> float:
        displacement = self.owner.displacement
        if displacement < 5:
            raise ValueError('Displacement must be at least 5 tons for armour.')
        if displacement < 16:
            size_factor = 4
        elif displacement < 26:
            size_factor = 3
        elif displacement < 100:
            size_factor = 2
        else:
            size_factor = 1
        armour_volume_modifier = self.owner.armour_volume_modifier
        return displacement * self._tonnage_consumed * self.protection * size_factor * armour_volume_modifier


class TitaniumSteelArmour(Armour):
    description: Literal['Titanium Steel'] = 'Titanium Steel'
    _cost_per_ton = 50_000
    _tonnage_consumed = 0.025
    _min_tl = 7
    tl: int | None = None

    def check_protection_limit(self) -> None:
        tl = self._effective_tl()
        if tl is None:
            return
        if self.protection > tl:
            self.error(f'Protection {self.protection} exceeds TL{tl}')
        elif self.protection > 9:
            self.error(f'Protection {self.protection} exceeds maximum 9 for Titanium Steel')


class CrystalironArmour(Armour):
    description: Literal['Crystaliron'] = 'Crystaliron'
    _cost_per_ton = 200_000
    _tonnage_consumed = 0.0125
    _min_tl = 10
    tl: int | None = None

    def check_protection_limit(self) -> None:
        tl = self._effective_tl()
        if tl is None:
            return
        if self.protection > tl:
            self.error(f'Protection {self.protection} exceeds TL{tl}')
        elif self.protection > 13:
            self.error(f'Protection {self.protection} exceeds maximum 13 for Crystaliron')


class BondedSuperdenseArmour(Armour):
    description: Literal['Bonded Superdense'] = 'Bonded Superdense'
    _cost_per_ton = 500_000
    _tonnage_consumed = 0.008
    _min_tl = 14
    tl: int | None = None

    def check_protection_limit(self) -> None:
        tl = self._effective_tl()
        if tl is None:
            return
        if self.protection > tl:
            self.error(f'Protection {self.protection} exceeds TL{tl}')


class MolecularBondedArmour(Armour):
    description: Literal['Molecular Bonded'] = 'Molecular Bonded'
    _cost_per_ton = 1_500_000
    _tonnage_consumed = 0.005
    _min_tl = 16
    tl: int | None = None

    def check_protection_limit(self) -> None:
        tl = self._effective_tl()
        if tl is None:
            return
        if self.protection > tl + 4:
            self.error(f'Protection {self.protection} exceeds TL{tl}+4')
