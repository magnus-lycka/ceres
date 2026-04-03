from .parts import ShipPart

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
    5: 7,
    10: 9,
    15: 11,
    20: 12,
    25: 13,
    30: 14,
    35: 15,
}


class Computer(ShipPart):
    power: float = 0.0
    rating: int

    @property
    def minimum_tl(self) -> int:
        return _COMPUTER_MIN_TL[self.rating]

    @property
    def effective_tl(self):
        return self.ship_tl

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return float(_COMPUTER_COST[self.rating])
