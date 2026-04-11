from typing import Annotated, Any, Literal, cast

from pydantic import Field

from .base import CeresModel, Note, NoteCategory
from .parts import ShipPart
from .spec import ShipSpec, SpecSection


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


class SensorStations(ShipPart):
    count: int

    def build_item(self) -> str | None:
        if self.count == 1:
            return 'Sensor Station'
        return 'Sensor Stations'

    def compute_tons(self) -> float:
        return float(self.count)

    def compute_cost(self) -> float:
        return self.count * 500_000.0


class EnhancedSignalProcessing(ShipPart):
    description: Literal['Enhanced Signal Processing'] = 'Enhanced Signal Processing'
    minimum_tl = 13

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='DM +4 to all sensor-related checks')]

    def compute_tons(self) -> float:
        return 2.0

    def compute_cost(self) -> float:
        return 8_000_000.0

    def compute_power(self) -> float:
        return 2.0


class ExtendedArrays(ShipPart):
    description: Literal['Extended Arrays'] = 'Extended Arrays'
    minimum_tl = 11

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return [
            Note(category=NoteCategory.INFO, message='Cannot expend Thrust or jump while in use'),
            Note(category=NoteCategory.INFO, message='DM +2 to detect ship while in use'),
        ]

    @property
    def _primary_suite(self) -> ShipPart:
        return cast(Any, self.owner).sensors.primary

    def compute_tons(self) -> float:
        return self._primary_suite.tons * 2

    def compute_cost(self) -> float:
        return self._primary_suite.cost * 2

    def compute_power(self) -> float:
        return self._primary_suite.power * 2


ShipSensors = Annotated[
    BasicSensors | CivilianSensors | MilitarySensors | ImprovedSensors,
    Field(discriminator='description'),
]


class SensorsSection(CeresModel):
    primary: ShipSensors = Field(default_factory=BasicSensors)
    countermeasures: CountermeasuresSuite | None = None
    signal_processing: EnhancedSignalProcessing | None = None
    extended_arrays: ExtendedArrays | None = None
    sensor_stations: SensorStations | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = [self.primary]
        if self.countermeasures is not None:
            parts.append(self.countermeasures)
        if self.signal_processing is not None:
            parts.append(self.signal_processing)
        if self.extended_arrays is not None:
            parts.append(self.extended_arrays)
        if self.sensor_stations is not None:
            parts.append(self.sensor_stations)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for sensor_part in self._all_parts():
            spec.add_row(ship._spec_row_for_part(SpecSection.SENSORS, sensor_part))
            if isinstance(sensor_part, SensorStations):
                spec.rows_for_section(SpecSection.SENSORS)[-1].quantity = (
                    sensor_part.count if sensor_part.count > 1 else None
                )
