from typing import ClassVar, Literal

from .parts import ShipPart


class Computer(ShipPart):
    power: float = 0.0
    description: str
    minimum_tl: ClassVar[int]
    processing: ClassVar[int]
    base_cost: ClassVar[float]
    bis: bool = False
    fib: bool = False

    @property
    def effective_tl(self):
        return self.ship_tl

    @property
    def jump_control_processing(self) -> int:
        bonus = 5 if self.bis else 0
        return self.processing + bonus

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        multiplier = 1.0
        if self.bis:
            multiplier += 0.5
        if self.fib:
            multiplier += 0.5
        return self.base_cost * multiplier


class Computer5(Computer):
    description: Literal['Computer/5'] = 'Computer/5'
    minimum_tl = 7
    processing = 5
    base_cost = 30_000.0


class Computer10(Computer):
    description: Literal['Computer/10'] = 'Computer/10'
    minimum_tl = 9
    processing = 10
    base_cost = 160_000.0


class Computer15(Computer):
    description: Literal['Computer/15'] = 'Computer/15'
    minimum_tl = 11
    processing = 15
    base_cost = 2_000_000.0


class Computer20(Computer):
    description: Literal['Computer/20'] = 'Computer/20'
    minimum_tl = 12
    processing = 20
    base_cost = 5_000_000.0


class Computer25(Computer):
    description: Literal['Computer/25'] = 'Computer/25'
    minimum_tl = 13
    processing = 25
    base_cost = 10_000_000.0


class Computer30(Computer):
    description: Literal['Computer/30'] = 'Computer/30'
    minimum_tl = 14
    processing = 30
    base_cost = 20_000_000.0


class Computer35(Computer):
    description: Literal['Computer/35'] = 'Computer/35'
    minimum_tl = 15
    processing = 35
    base_cost = 30_000_000.0


class Core40(Computer):
    description: Literal['Core/40'] = 'Core/40'
    minimum_tl = 9
    processing = 40
    base_cost = 45_000_000.0


class Core50(Computer):
    description: Literal['Core/50'] = 'Core/50'
    minimum_tl = 10
    processing = 50
    base_cost = 60_000_000.0


class Core60(Computer):
    description: Literal['Core/60'] = 'Core/60'
    minimum_tl = 11
    processing = 60
    base_cost = 75_000_000.0


class Core70(Computer):
    description: Literal['Core/70'] = 'Core/70'
    minimum_tl = 12
    processing = 70
    base_cost = 80_000_000.0


class Core80(Computer):
    description: Literal['Core/80'] = 'Core/80'
    minimum_tl = 13
    processing = 80
    base_cost = 95_000_000.0


class Core90(Computer):
    description: Literal['Core/90'] = 'Core/90'
    minimum_tl = 14
    processing = 90
    base_cost = 120_000_000.0


class Core100(Computer):
    description: Literal['Core/100'] = 'Core/100'
    minimum_tl = 15
    processing = 100
    base_cost = 130_000_000.0
