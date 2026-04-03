import math
from typing import ClassVar, Literal

from .parts import Power, ShipPart

_THRUST_PERCENT: dict[int, float] = {
    0: 0.005,
    1: 0.01,
    2: 0.02,
    3: 0.03,
    4: 0.04,
    5: 0.05,
    6: 0.06,
    7: 0.07,
    8: 0.08,
    9: 0.09,
    10: 0.10,
    11: 0.11,
}
_THRUST_MIN_TL: dict[int, int] = {
    0: 9,
    1: 9,
    2: 10,
    3: 10,
    4: 11,
    5: 11,
    6: 12,
    7: 13,
    8: 14,
    9: 15,
    10: 16,
    11: 17,
}

_FUSION_POWER_PER_TON: dict[int, int] = {8: 10, 12: 15, 15: 20}
_FUSION_COST_PER_TON: dict[int, int] = {8: 500_000, 12: 1_000_000, 15: 2_000_000}


class MDrive(ShipPart):
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    _explicit_power: ClassVar[bool] = False

    rating: int
    budget: bool = False
    increased_size: bool = False

    def _base_tons(self) -> float:
        return self.owner.displacement * _THRUST_PERCENT[self.rating]

    @property
    def minimum_tl(self) -> int:
        return _THRUST_MIN_TL[self.rating]

    def calculate_tons(self) -> float:
        base = self._base_tons()
        return base * 1.25 if self.increased_size else base

    def calculate_cost(self) -> float:
        base = self._base_tons() * 2_000_000
        return base * 0.75 if self.budget else base

    def calculate_power(self) -> float:
        return float(math.ceil(0.1 * self.owner.displacement * self.rating))


class _FusionPlant(ShipPart):
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    _explicit_power: ClassVar[bool] = True

    minimum_tl: ClassVar[int]
    power_per_ton: ClassVar[int]
    cost_per_ton: ClassVar[int]
    power: Power = Power(value=0)
    output: int
    budget: bool = False
    increased_size: bool = False

    def _base_tons(self) -> float:
        return self.output / self.power_per_ton

    @property
    def fusion_tl(self) -> int:
        return self.minimum_tl

    @property
    def effective_tl(self):
        return self.minimum_tl

    def calculate_tons(self) -> float:
        base = self._base_tons()
        return base * 1.25 if self.increased_size else base

    def calculate_cost(self) -> float:
        base = self._base_tons() * self.cost_per_ton
        return base * 0.75 if self.budget else base


class FusionPlantTL8(_FusionPlant):
    plant_type: Literal['fusion_tl8'] = 'fusion_tl8'
    minimum_tl = 8
    power_per_ton = 10
    cost_per_ton = 500_000


class FusionPlantTL12(_FusionPlant):
    plant_type: Literal['fusion_tl12'] = 'fusion_tl12'
    minimum_tl = 12
    power_per_ton = 15
    cost_per_ton = 1_000_000


class FusionPlantTL15(_FusionPlant):
    plant_type: Literal['fusion_tl15'] = 'fusion_tl15'
    minimum_tl = 15
    power_per_ton = 20
    cost_per_ton = 2_000_000


# Compatibility alias while the codebase migrates to explicit variants.
FusionPlant = FusionPlantTL12


class OperationFuel(ShipPart):
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    _explicit_power: ClassVar[bool] = True

    power: Power = Power(value=0)
    weeks: int

    def calculate_tons(self) -> float:
        plant = getattr(self.owner, 'fusion_plant', None)
        if plant is None:
            raise ValueError('Ship must have a FusionPlant to compute OperationFuel')
        pp_tons = plant.calculate_tons()
        monthly = 0.10 * pp_tons
        weekly = monthly / 4
        total = weekly * self.weeks
        return math.ceil(total * 100) / 100

    def calculate_cost(self) -> float:
        return 0.0
