from typing import ClassVar

from .standard import HullConfiguration


class SpinExtPrimitiveHull(HullConfiguration):
    primitive: ClassVar[bool] = True
    description: str = 'SpinExt Primitive Hull'

    def cost(self, ton):
        return 15_000 * ton * self.effective_hull_cost_modifier

    def automation_basis_cost(self, ton: float) -> float:
        modifier = self.hull_cost_modifier
        if self.reinforced:
            modifier *= 1.5
        if self.light:
            modifier *= 0.75
        if self.military:
            modifier *= 1.25
        return 15_000 * ton * modifier

    def points(self, ton):
        return super().points(ton) * 0.5
