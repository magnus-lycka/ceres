from typing import ClassVar, Literal

from ..parts import ShipPartBase


class UNREPSystem(ShipPartBase):
    tons: float = 0.0
    system_type: Literal['UNREP_SYSTEM'] = 'UNREP_SYSTEM'
    cost: ClassVar[float]

    def item_description(self) -> str:
        return f'UNREP System ({self.transfer_rate:g} tons/hour)'

    @property
    def transfer_rate(self) -> float:
        return self.tons * 20

    @property
    def cost(self) -> float:
        return self.tons * 500_000.0

    @property
    def power(self) -> float:
        return self.tons
