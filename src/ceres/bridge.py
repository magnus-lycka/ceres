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


class Bridge(ShipPart):
    def compute_tons(self) -> float:
        displacement = self.owner.displacement
        if displacement <= 50:
            return 3.0
        if displacement <= 99:
            return 6.0
        if displacement <= 200:
            return 10.0
        if displacement <= 1_000:
            return 20.0
        if displacement <= 2_000:
            return 40.0
        return 60.0

    def compute_cost(self) -> float:
        return float(((self.owner.displacement - 1) // 100 + 1) * 500_000)
