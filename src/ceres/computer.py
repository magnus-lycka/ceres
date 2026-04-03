from typing import ClassVar

from pydantic import model_validator

from .parts import ShipPart, Power

_COMPUTER_COST: dict[int, int] = {
    5: 30_000,
    10: 160_000,
    15: 2_000_000,
    20: 5_000_000,
    25: 10_000_000,
    30: 20_000_000,
    35: 30_000_000,
}
_COMPUTER_MIN_TL: dict[int, int] = {
    5: 7, 10: 9, 15: 11, 20: 12, 25: 13, 30: 14, 35: 15,
}


class Computer(ShipPart):
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    _explicit_power: ClassVar[bool] = True

    power: Power = Power(value=0)
    rating: int

    @model_validator(mode="before")
    @classmethod
    def _set_tl(cls, data: dict) -> dict:
        if "tl" not in data:
            rating = data.get("rating")
            if rating in _COMPUTER_MIN_TL:
                data["tl"] = _COMPUTER_MIN_TL[rating]
        return data

    def _check_tl(self) -> None:
        min_tl = _COMPUTER_MIN_TL[self.rating]
        if self.owner.tl < min_tl:
            raise ValueError(
                f"Computer/{self.rating} requires TL{min_tl}, ship is TL{self.owner.tl}"
            )

    def calculate_tons(self) -> float:
        return 0.0

    def calculate_cost(self) -> float:
        self._check_tl()
        return float(_COMPUTER_COST[self.rating])
