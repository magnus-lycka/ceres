from typing import ClassVar, Literal

from .common import _ZeroPowerSystemPart


class ProbeDrones(_ZeroPowerSystemPart):
    drone_type: Literal['PROBE_DRONES'] = 'PROBE_DRONES'
    tl: int = 9
    tons: ClassVar[float]
    cost: ClassVar[float]
    drones_per_ton: ClassVar[int] = 5
    cost_per_ton: ClassVar[float] = 500_000.0
    count: int

    def item_description(self) -> str:
        if self.count == 1:
            return 'Probe Drone'
        return 'Probe Drones'

    @property
    def tons(self) -> float:
        return self.count / self.drones_per_ton

    @property
    def cost(self) -> float:
        return (self.count / self.drones_per_ton) * self.cost_per_ton


class AdvancedProbeDrones(ProbeDrones):
    drone_type: Literal['ADVANCED_PROBE_DRONES'] = 'ADVANCED_PROBE_DRONES'
    tl: int = 12
    cost_per_ton: ClassVar[float] = 800_000.0

    def item_description(self) -> str:
        if self.count == 1:
            return 'Advanced Probe Drone'
        return 'Advanced Probe Drones'


class RepairDrones(_ZeroPowerSystemPart):
    """Repair drones: 1 ton per 100 tons of displacement, Cr200,000 per ton."""

    drone_type: Literal['REPAIR_DRONES'] = 'REPAIR_DRONES'
    description: Literal['Repair Drones'] = 'Repair Drones'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return self.assembly.displacement / 100

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0


class MiningDrones(_ZeroPowerSystemPart):
    drone_type: Literal['MINING_DRONES'] = 'MINING_DRONES'
    tons: ClassVar[float]
    cost: ClassVar[float]
    count: int

    def item_description(self) -> str:
        if self.count == 1:
            return 'Mining Drone'
        return 'Mining Drones'

    @property
    def tons(self) -> float:
        return self.count * 2.0

    @property
    def cost(self) -> float:
        return self.count * 200_000.0
