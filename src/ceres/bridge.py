from typing import ClassVar

from .parts import Power, ShipPart


class Cockpit(ShipPart):
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    _explicit_power: ClassVar[bool] = True

    power: Power = Power(value=0)
    holographic: bool = False

    def calculate_tons(self) -> float:
        return 1.5

    def calculate_cost(self) -> float:
        cost = 10_000
        if self.holographic:
            cost += 2_500
        return float(cost)
