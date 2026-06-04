from typing import TYPE_CHECKING

from ceres.shared import Assembly

if TYPE_CHECKING:
    from .hull import Hull


class ShipBase(Assembly):
    """Minimal ship interface that ShipPart subclasses depend on."""

    tl: int
    displacement: int
    if TYPE_CHECKING:
        hull: Hull | None = None

    @property
    def performance_displacement(self) -> float:
        return float(self.displacement)

    @property
    def armour_volume_modifier(self) -> float:
        return 1.0

    def remaining_usable_tonnage(self) -> float:
        return 0.0
