from typing import ClassVar

from .standard import HullConfiguration

PRIMITIVE_TL5 = 5


class SpinExtPrimitiveHull(HullConfiguration):
    primitive: ClassVar[bool] = True
    description: str = 'SpinExt Primitive Hull'

    def cost(self, ton, tl: int | None = None):
        tl_multiplier = 2 if tl == PRIMITIVE_TL5 else 1
        return 15_000 * ton * self.effective_hull_cost_modifier * tl_multiplier

    def automation_basis_cost(self, ton: float) -> float:
        modifier = self.hull_cost_modifier_without_non_gravity()
        return 15_000 * ton * modifier

    def points(self, ton):
        return super().points(ton) * 0.5
