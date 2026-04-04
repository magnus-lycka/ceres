import math
from typing import ClassVar

from pydantic import BaseModel

from .parts import ShipPart


class Workshop(ShipPart):
    power: float = 0.0

    def compute_tons(self) -> float:
        return 6.0

    def compute_cost(self) -> float:
        return 900_000.0


class ProbeDrones(ShipPart):
    drones_per_ton: ClassVar[int] = 5
    cost_per_ton: ClassVar[float] = 500_000.0
    power: float = 0.0
    count: int

    def compute_tons(self) -> float:
        return self.count / self.drones_per_ton

    def compute_cost(self) -> float:
        return (self.count / self.drones_per_ton) * self.cost_per_ton


class SmallCraft(BaseModel):
    shipping_size: int
    cost: float
    model_config = {'frozen': True}


class AirRaft(SmallCraft):
    shipping_size: int = 4
    cost: float = 250_000.0


class InternalDockingSpace(ShipPart):
    power: float = 0.0
    craft: AirRaft

    def compute_tons(self) -> float:
        return float(math.ceil(self.craft.shipping_size * 1.1))

    def compute_cost(self) -> float:
        return self.compute_tons() * 250_000.0
