import math
from typing import ClassVar

from pydantic import BaseModel

from .parts import ShipPart, TechLevel, Power

_PULSE_LASER_POWER = 4
_PULSE_LASER_COST = 1_000_000
_FIXED_MOUNT_COST = 100_000


class PulseLaser(BaseModel):
    """Pulse laser weapon (TL9, 2D damage, Long range)."""

    model_config = {"frozen": True}

    very_high_yield: bool = False  # 2 advantages
    energy_efficient: bool = False  # 1 advantage

    @property
    def base_cost(self) -> int:
        return _PULSE_LASER_COST

    @property
    def base_power(self) -> int:
        return _PULSE_LASER_POWER

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
    _explicit_cost: ClassVar[bool] = False
    _explicit_tons: ClassVar[bool] = False
    _explicit_power: ClassVar[bool] = False

    tl: TechLevel = TechLevel(value=9)  # min TL for pulse laser
    weapon: PulseLaser

    def calculate_tons(self) -> float:
        return 0.0

    def calculate_cost(self) -> float:
        return _FIXED_MOUNT_COST + self.weapon.base_cost * self.weapon.cost_modifier

    def calculate_power(self) -> float:
        power = self.weapon.base_power
        if self.weapon.energy_efficient:
            power *= 0.75
        # Firmpoint reduces power by 25%; apply combined then floor
        power *= 0.75
        return float(math.floor(power))
