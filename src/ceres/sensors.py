from typing import Literal

from .base import Note, NoteCategory
from .parts import ShipPart


class BasicSensors(ShipPart):
    description: Literal['Basic'] = 'Basic'
    minimum_tl = 8

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='Radar, Lidar; DM -4')]

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return 0.0

    def compute_power(self) -> float:
        return 0.0


class CivilianSensors(ShipPart):
    description: Literal['Civilian Grade'] = 'Civilian Grade'
    minimum_tl = 9

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='Radar, Lidar; DM -2')]

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 3_000_000.0

    def compute_power(self) -> float:
        return 1.0


class MilitarySensors(ShipPart):
    description: Literal['Military Grade'] = 'Military Grade'
    minimum_tl = 10

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='Jammers, Radar, Lidar; DM +0')]

    def compute_tons(self) -> float:
        return 2.0

    def compute_cost(self) -> float:
        return 4_100_000.0

    def compute_power(self) -> float:
        return 2.0
