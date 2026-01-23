from pydantic import Field, computed_field, model_validator

from .parts import ShipPart


class Armour(ShipPart):
    protection: int
    displacement: int = Field(ge=5)
    _cost_per_ton = 0
    _tonnage_consumed = 0

    @model_validator(mode="before")
    @classmethod
    def forbid_cost(cls, data):
        if "cost" in data:
            raise ValueError("cost is derived for Armour")
        return data

    @model_validator(mode="before")
    @classmethod
    def forbid_tons(cls, data):
        if "tons" in data:
            raise ValueError("tons is derived for Armour")
        return data

    @model_validator(mode="before")
    @classmethod
    def forbid_power(cls, data):
        if "power" in data:
            raise ValueError("power is derived for Armour")
        return data

    @computed_field
    @property
    def cost(self) -> int:
        return self.displacement * self._cost_per_ton * self.protection

    @computed_field
    @property
    def tons(self) -> int:
        if self.displacement < 16:
            size_factor = 4
        elif self.displacement < 26:
            size_factor = 3
        elif self.displacement < 100:
            size_factor = 2
        else:
            size_factor = 1
        return (
            self.displacement * self._tonnage_consumed * self.protection * size_factor
        )


class TitaniumSteelArmour(Armour):
    _cost_per_ton = 50_000
    _tonnage_consumed = 0.025
    tl: int = Field(ge=7)

    @model_validator(mode="before")
    @classmethod
    def protection_limit(cls, data):
        if data.get("protection", 0) > data["tl"]:
            raise ValueError("Protection can't be more than TL")
        if data.get("protection", 0) > 9:
            raise ValueError("Protection can't be more than 9")
        return data


class CrystalironArmour(Armour):
    _cost_per_ton = 200_000
    _tonnage_consumed = 0.0125
    tl: int = Field(ge=10)

    @model_validator(mode="before")
    @classmethod
    def protection_limit(cls, data):
        if data.get("protection", 0) > data["tl"]:
            raise ValueError("Protection can't be more than TL")
        if data.get("protection", 0) > 13:
            raise ValueError("Protection can't be more than 9")
        return data


class BondedSuperdenseArmour(Armour):
    _cost_per_ton = 500_000
    _tonnage_consumed = 0.008
    tl: int = Field(ge=14)

    @model_validator(mode="before")
    @classmethod
    def protection_limit(cls, data):
        if data.get("protection", 0) > data["tl"]:
            raise ValueError("Protection can't be more than TL")
        return data


class MolecularBondedArmour(Armour):
    _cost_per_ton = 1_500_000
    _tonnage_consumed = 0.005
    tl: int = Field(ge=16)

    @model_validator(mode="before")
    @classmethod
    def protection_limit(cls, data):
        if data.get("protection", 0) > data["tl"]:
            raise ValueError("Protection can't be more than TL")
        return data
