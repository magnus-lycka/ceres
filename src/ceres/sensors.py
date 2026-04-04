from .base import Note, NoteCategory
from .parts import ShipPart


class CivilianGradeSensors(ShipPart):
    minimum_tl = 9

    def build_item(self) -> str | None:
        return 'Civilian Grade'

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='Radar, Lidar; DM -2')]

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 3_000_000.0

    def compute_power(self) -> float:
        return 1.0


class MilitaryGradeSensors(ShipPart):
    minimum_tl = 10

    def build_item(self) -> str | None:
        return 'Military Grade'

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='Jammers, Radar, Lidar; DM +0')]

    def compute_tons(self) -> float:
        return 2.0

    def compute_cost(self) -> float:
        return 4_100_000.0

    def compute_power(self) -> float:
        return 2.0
