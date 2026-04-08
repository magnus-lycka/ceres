from typing import Annotated, Literal

from pydantic import Field

from .base import CeresModel, Note, NoteCategory
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


class ImprovedSensors(ShipPart):
    description: Literal['Improved'] = 'Improved'
    minimum_tl = 12

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='Radar, Lidar, EMS, Densitometer; DM +1')]

    def compute_tons(self) -> float:
        return 3.0

    def compute_cost(self) -> float:
        return 4_300_000.0

    def compute_power(self) -> float:
        return 3.0


class CountermeasuresSuite(ShipPart):
    description: Literal['Countermeasures Suite'] = 'Countermeasures Suite'
    minimum_tl = 11

    def build_item(self) -> str | None:
        return self.description

    def compute_tons(self) -> float:
        return 2.0

    def compute_cost(self) -> float:
        return 4_000_000.0

    def compute_power(self) -> float:
        return 2.0


ShipSensors = Annotated[
    BasicSensors | CivilianSensors | MilitarySensors | ImprovedSensors,
    Field(discriminator='description'),
]


class SensorsSection(CeresModel):
    primary: ShipSensors = Field(default_factory=BasicSensors)
    countermeasures: CountermeasuresSuite | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = [self.primary]
        if self.countermeasures is not None:
            parts.append(self.countermeasures)
        return parts
