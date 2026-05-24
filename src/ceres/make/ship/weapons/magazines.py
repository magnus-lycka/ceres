from typing import ClassVar

from ..parts import ShipPart


class MissileStorage(ShipPart):
    """Magazine for missiles: 12 missiles per ton, no cost."""

    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    count: int

    def item_description(self) -> str:
        return f'Missile Storage ({self.count})'

    @property
    def tons(self) -> float:
        return self.count / 12

    @property
    def cost(self) -> float:
        return 0.0

    @property
    def power(self) -> float:
        return 0.0


class TorpedoStorage(ShipPart):
    """Magazine for torpedoes: 3 torpedoes per ton, no cost."""

    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    count: int

    def item_description(self) -> str:
        return f'Torpedo Storage ({self.count})'

    @property
    def tons(self) -> float:
        return self.count / 3

    @property
    def cost(self) -> float:
        return 0.0

    @property
    def power(self) -> float:
        return 0.0


class SandcasterCanisterStorage(ShipPart):
    """Magazine for sand canisters: 20 canisters per ton, no cost."""

    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    count: int

    def item_description(self) -> str:
        return f'Sandcaster Canister Storage ({self.count})'

    @property
    def tons(self) -> float:
        return self.count / 20

    @property
    def cost(self) -> float:
        return 0.0

    @property
    def power(self) -> float:
        return 0.0
