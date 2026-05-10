from ceres.shared import Assembly


class ShipBase(Assembly):
    """Minimal ship interface that ShipPart subclasses depend on."""

    tl: int
    displacement: int

    @property
    def performance_displacement(self) -> float:
        return float(self.displacement)

    @property
    def armour_volume_modifier(self) -> float:
        return 1.0

    def parts_of_type(self, part_cls: type) -> list:
        return []

    def remaining_usable_tonnage(self) -> float:
        return 0.0


__all__ = ['ShipBase']
