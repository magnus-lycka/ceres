from pydantic import Field, computed_field, model_validator

from .parts import ShipPart


class _Armour(ShipPart):
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
        return self.displacement * self._tonnage_consumed * self.protection


class TitaniumSteelArmour(_Armour):
    _cost_per_ton = 50_000
    _tonnage_consumed = 0.025
    tl: int = Field(ge=7)