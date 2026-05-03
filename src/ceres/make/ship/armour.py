from typing import Any, ClassVar, Literal

from pydantic import AliasChoices, Field, model_validator

from .base import ShipBase
from .parts import ShipPart


class Armour(ShipPart):
    description: str
    protection: int
    # Override CeresPart.tl: excluded from JSON so part_tl's alias='tl' owns the JSON key.
    tl: int = Field(default=0, exclude=True)
    part_tl: int | None = Field(default=None, alias='tl', validation_alias=AliasChoices('part_tl', 'tl'))
    _min_tl: ClassVar[int] = 0
    _cost_per_ton: ClassVar[int] = 0
    _tonnage_consumed: ClassVar[int] = 0
    model_config = {'frozen': True, 'populate_by_name': True, 'serialize_by_alias': True}

    @model_validator(mode='before')
    @classmethod
    def _fill_tl_from_class_var(cls, data: Any) -> Any:
        # Strip tl=null so the int field falls back to its default (0) on roundtrip.
        if isinstance(data, dict) and 'tl' in data and data['tl'] is None:
            data = {k: v for k, v in data.items() if k != 'tl'}
        return data

    def bind(self, owner: ShipBase) -> None:
        super().bind(owner)
        self.check_protection_limit()

    def _selected_tl(self) -> int | None:
        """Resolve the armour TL to use for protection-limit checks.

        Returns None and adds an error note if the TL is invalid.
        """
        if self.part_tl:
            if self.ship.tl < self.part_tl:
                self.error(f'Ship TL{self.ship.tl} is below armour TL{self.part_tl}')
                return None
            tl = self.part_tl
        else:
            tl = self.ship.tl
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
        displacement = self.ship.displacement
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
        armour_volume_modifier = self.ship.armour_volume_modifier
        return displacement * self._tonnage_consumed * self.protection * size_factor * armour_volume_modifier


class TitaniumSteelArmour(Armour):
    description: Literal['Titanium Steel'] = 'Titanium Steel'
    _cost_per_ton = 50_000
    _tonnage_consumed = 0.025
    _min_tl = 7

    def check_protection_limit(self) -> None:
        tl = self._selected_tl()
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

    def check_protection_limit(self) -> None:
        tl = self._selected_tl()
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

    def check_protection_limit(self) -> None:
        tl = self._selected_tl()
        if tl is None:
            return
        if self.protection > tl:
            self.error(f'Protection {self.protection} exceeds TL{tl}')


class MolecularBondedArmour(Armour):
    description: Literal['Molecular Bonded'] = 'Molecular Bonded'
    _cost_per_ton = 1_500_000
    _tonnage_consumed = 0.005
    _min_tl = 16

    def check_protection_limit(self) -> None:
        tl = self._selected_tl()
        if tl is None:
            return
        if self.protection > tl + 4:
            self.error(f'Protection {self.protection} exceeds TL{tl}+4')
