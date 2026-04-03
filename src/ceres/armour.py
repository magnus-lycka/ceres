from typing import ClassVar

from .parts import Power, ShipPart


class Armour(ShipPart):
    power: Power = Power(value=0)
    protection: int
    _min_tl: ClassVar[int] = 0
    _cost_per_ton: ClassVar[int] = 0
    _tonnage_consumed: ClassVar[int] = 0
    _explicit_cost = False
    _explicit_power = True
    _explicit_tons = False

    def check_protection_limit(self):
        return NotImplemented

    def calculate_cost(self) -> float:
        self.check_protection_limit()
        return self.calculate_tons() * self._cost_per_ton

    def calculate_tons(self) -> float:
        self.check_protection_limit()
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
    _cost_per_ton = 50_000
    _tonnage_consumed = 0.025
    _min_tl = 7
    tl: int | None = None

    def check_protection_limit(self):
        if self.tl:
            if self.owner.tl < self.tl:
                raise ValueError('Ship TL is below stated part TL')
            tl = self.tl
        else:
            tl = self.owner.tl
        if tl < self._min_tl:
            raise ValueError(f'Titanium Steel Armour needs TL {self._min_tl}')
        if self.protection > tl:
            raise ValueError("Protection can't be more than TL")
        if self.protection > 9:
            raise ValueError("Protection can't be more than 9")


class CrystalironArmour(Armour):
    _cost_per_ton = 200_000
    _tonnage_consumed = 0.0125
    _min_tl = 10
    tl: int | None = None

    def check_protection_limit(self):
        if self.tl:
            if self.owner.tl < self.tl:
                raise ValueError('Ship TL is below stated part TL')
            tl = self.tl
        else:
            tl = self.owner.tl
        if tl < self._min_tl:
            raise ValueError(f'Crystaliron Armour needs TL {self._min_tl}')
        if self.protection > tl:
            raise ValueError("Protection can't be more than TL")
        if self.protection > 13:
            raise ValueError("Protection can't be more than 13")


class BondedSuperdenseArmour(Armour):
    _cost_per_ton = 500_000
    _tonnage_consumed = 0.008
    _min_tl = 14
    tl: int | None = None

    def check_protection_limit(self):
        if self.tl:
            if self.owner.tl < self.tl:
                raise ValueError('Ship TL is below stated part TL')
            tl = self.tl
        else:
            tl = self.owner.tl
        if tl < self._min_tl:
            raise ValueError(f'Bonded Superdense Armour needs TL {self._min_tl}')
        if self.protection > tl:
            raise ValueError("Protection can't be more than TL")


class MolecularBondedArmour(Armour):
    _cost_per_ton = 1_500_000
    _tonnage_consumed = 0.005
    _min_tl = 16
    tl: int | None = None

    def check_protection_limit(self):
        if self.tl:
            if self.owner.tl < self.tl:
                raise ValueError('Ship TL is below stated part TL')
            tl = self.tl
        else:
            tl = self.owner.tl
        if tl < self._min_tl:
            raise ValueError(f'Molecular Bonded Armour needs TL {self._min_tl}')
        if self.protection > tl + 4:
            raise ValueError("Protection can't be more than TL+4")
