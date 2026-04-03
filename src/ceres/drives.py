import math
from typing import ClassVar

from .parts import ShipPart, TechLevel, Power

_THRUST_PERCENT: dict[int, float] = {
    0: 0.005, 1: 0.01, 2: 0.02, 3: 0.03, 4: 0.04,
    5: 0.05, 6: 0.06, 7: 0.07, 8: 0.08, 9: 0.09, 10: 0.10, 11: 0.11,
}
_THRUST_MIN_TL: dict[int, int] = {
    0: 9, 1: 9, 2: 10, 3: 10, 4: 11, 5: 11,
    6: 12, 7: 13, 8: 14, 9: 15, 10: 16, 11: 17,
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

    def _check_tl(self) -> None:
        min_tl = _THRUST_MIN_TL[self.rating]
        if self.owner.tl < min_tl:
            raise ValueError(
                f"MDrive rating {self.rating} requires TL{min_tl}, ship is TL{self.owner.tl}"
            )

    def calculate_tons(self) -> float:
        self._check_tl()
        base = self._base_tons()
        return base * 1.25 if self.increased_size else base

    def calculate_cost(self) -> float:
        self._check_tl()
        base = self._base_tons() * 2_000_000
        return base * 0.75 if self.budget else base

    def calculate_power(self) -> float:
        return float(math.ceil(0.1 * self.owner.displacement * self.rating))


class FusionPlant(ShipPart):
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    _explicit_power: ClassVar[bool] = True

    power: Power = Power(value=0)
    fusion_tl: int
    output: int
    budget: bool = False
    increased_size: bool = False

    def _base_tons(self) -> float:
        return self.output / _FUSION_POWER_PER_TON[self.fusion_tl]

    def calculate_tons(self) -> float:
        base = self._base_tons()
        return base * 1.25 if self.increased_size else base

    def calculate_cost(self) -> float:
        base = self._base_tons() * _FUSION_COST_PER_TON[self.fusion_tl]
        return base * 0.75 if self.budget else base


class OperationFuel(ShipPart):
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    _explicit_power: ClassVar[bool] = True

    power: Power = Power(value=0)
    weeks: int

    def calculate_tons(self) -> float:
        plant = getattr(self.owner, "fusion_plant", None)
        if plant is None:
            raise ValueError("Ship must have a FusionPlant to compute OperationFuel")
        pp_tons = plant.calculate_tons()
        monthly = 0.10 * pp_tons
        weekly = monthly / 4
        total = weekly * self.weeks
        return math.ceil(total * 100) / 100

    def calculate_cost(self) -> float:
        return 0.0
