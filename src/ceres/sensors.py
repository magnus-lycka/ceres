from .parts import ShipPart


class CivilianGradeSensors(ShipPart):
    minimum_tl = 9

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 3_000_000.0

    def compute_power(self) -> float:
        return 1.0
