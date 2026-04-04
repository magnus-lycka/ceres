import math
from typing import ClassVar

from .base import CeresModel
from .parts import ShipPart


class PulseLaser(CeresModel):
    """Pulse laser weapon (TL9, 2D damage, Long range)."""

    model_config = {'frozen': True}
    base_cost: ClassVar[int] = 1_000_000
    base_power: ClassVar[int] = 4

    very_high_yield: bool = False  # 2 advantages
    energy_efficient: bool = False  # 1 advantage

    def build_item(self) -> str | None:
        parts = ['Pulse Laser']
        if self.very_high_yield:
            parts.append('Very High Yield')
        if self.energy_efficient:
            parts.append('Energy Efficient')
        return ', '.join(parts)

    @property
    def cost_modifier(self) -> float:
        advantages = 0
        if self.very_high_yield:
            advantages += 2
        if self.energy_efficient:
            advantages += 1
        # Prototype/Advanced table
        if advantages >= 3:
            return 1.50  # High Technology
        if advantages == 2:
            return 1.25  # Very Advanced
        if advantages == 1:
            return 1.10  # Advanced
        return 1.0


class FixedFirmpoint(ShipPart):
    mount_cost: ClassVar[int] = 100_000
    minimum_tl = 9
    weapon: PulseLaser

    def build_item(self) -> str | None:
        return self.weapon.build_item()

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return self.mount_cost + self.weapon.base_cost * self.weapon.cost_modifier

    def compute_power(self) -> float:
        power = self.weapon.base_power
        if self.weapon.energy_efficient:
            power *= 0.75
        # Firmpoint reduces power by 25%; apply combined then floor
        power *= 0.75
        return float(math.floor(power))


class DoubleTurret(ShipPart):
    minimum_tl = 8

    def build_item(self) -> str | None:
        return 'Double Turret'

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 500_000.0

    def compute_power(self) -> float:
        return 1.0
