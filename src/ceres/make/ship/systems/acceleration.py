from typing import ClassVar, Literal

from ..parts import UnpoweredShipPart


class AccelerationSeat(UnpoweredShipPart):
    system_type: Literal['ACCELERATION_SEAT'] = 'ACCELERATION_SEAT'
    tl: int = 1
    description: Literal['Acceleration Seat'] = 'Acceleration Seat'
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 0.5

    @property
    def cost(self) -> float:
        return 30_000.0


class AccelerationBench(UnpoweredShipPart):
    system_type: Literal['ACCELERATION_BENCH'] = 'ACCELERATION_BENCH'
    tl: int = 1
    description: Literal['Acceleration Bench'] = 'Acceleration Bench'
    cost: ClassVar[float]
    seats: int = 4

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def cost(self) -> float:
        return 10_000.0
