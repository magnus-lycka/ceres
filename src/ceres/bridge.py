from .parts import ShipPart


class Cockpit(ShipPart):
    power: float = 0.0
    holographic: bool = False

    def compute_tons(self) -> float:
        return 1.5

    def compute_cost(self) -> float:
        cost = 10_000
        if self.holographic:
            cost += 2_500
        return float(cost)
