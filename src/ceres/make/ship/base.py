from ceres.shared import CeresModel, CeresPart, Note, NoteCategory


class ShipBase(CeresModel):
    """Minimal ship interface that ShipPart subclasses depend on."""

    tl: int
    displacement: int
    maintained_external_displacement: float = 0.0
    unmaintained_external_displacement: float = 0.0

    @property
    def transported_external_displacement(self) -> float:
        return self.maintained_external_displacement + self.unmaintained_external_displacement

    @property
    def performance_displacement(self) -> float:
        return self.displacement + self.transported_external_displacement

    @property
    def armour_volume_modifier(self) -> float:
        return 1.0

    def parts_of_type(self, part_cls: type) -> list:
        return []

    def remaining_usable_tonnage(self) -> float:
        return 0.0


__all__ = ['CeresPart', 'CeresModel', 'Note', 'NoteCategory', 'ShipBase']
