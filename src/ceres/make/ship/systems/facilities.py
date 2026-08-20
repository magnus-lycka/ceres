from typing import ClassVar, Literal

from ceres.shared import NoteList, _Note

from ..parts import ShipPartBase, UnpoweredShipPart


class Workshop(UnpoweredShipPart):
    system_type: Literal['WORKSHOP'] = 'WORKSHOP'
    description: Literal['Workshop'] = 'Workshop'
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 6.0

    @property
    def cost(self) -> float:
        return 900_000.0


class Laboratory(UnpoweredShipPart):
    system_type: Literal['LABORATORY'] = 'LABORATORY'
    description: Literal['Laboratory'] = 'Laboratory'
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 4.0

    @property
    def cost(self) -> float:
        return 1_000_000.0


class LibraryFacility(UnpoweredShipPart):
    system_type: Literal['LIBRARY'] = 'LIBRARY'
    description: Literal['Library'] = 'Library'
    tl: int = 8
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 4.0

    @property
    def cost(self) -> float:
        return 4_000_000.0


class ConstructionDeck(ShipPartBase):
    tons: float = 0.0
    system_type: Literal['CONSTRUCTION_DECK'] = 'CONSTRUCTION_DECK'
    description: Literal['Construction Deck'] = 'Construction Deck'
    cost: ClassVar[float]

    @property
    def maximum_constructible_tons(self) -> float:
        return self.tons / 2.0

    @property
    def cost(self) -> float:
        return self.tons * 500_000.0

    @property
    def power(self) -> float:
        return self.tons

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info(f'Can build or repair ships up to {self.maximum_constructible_tons:g} tons at TL{self.assembly_tl}')
        return notes


class TrainingFacility(UnpoweredShipPart):
    system_type: Literal['TRAINING_FACILITY'] = 'TRAINING_FACILITY'
    cost: ClassVar[float]
    trainees: int

    def item_description(self) -> str:
        return f'Training Facility: {self.trainees}-person capacity'

    @property
    def tons(self) -> float:
        return self.trainees * 2.0

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0
