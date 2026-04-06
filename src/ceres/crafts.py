import math

from .base import CeresModel
from .parts import ShipPart


class CarriedCraft(CeresModel):
    shipping_size: int
    cost: float
    model_config = {'frozen': True}

    def build_item(self) -> str | None:
        return self.__class__.__name__


class AirRaft(CarriedCraft):
    shipping_size: int = 4
    cost: float = 250_000.0

    def build_item(self) -> str | None:
        return 'Air/Raft'


class InternalDockingSpace(ShipPart):
    craft: AirRaft

    def build_item(self) -> str | None:
        return f'Internal Docking Space: {self.craft.build_item()}'

    def compute_tons(self) -> float:
        return float(math.ceil(self.craft.shipping_size * 1.1))

    def compute_cost(self) -> float:
        return self.compute_tons() * 250_000.0
