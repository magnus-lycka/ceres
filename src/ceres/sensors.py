from typing import ClassVar

from .parts import ShipPart, TechLevel, Power


class CivilianGradeSensors(ShipPart):
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    _explicit_power: ClassVar[bool] = False

    tl: TechLevel = TechLevel(value=9)

    def calculate_tons(self) -> float:
        return 1.0

    def calculate_cost(self) -> float:
        return 3_000_000.0

    def calculate_power(self) -> float:
        return 1.0
