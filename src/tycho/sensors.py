from typing import Annotated, Any, Literal, cast

from pydantic import Field

from .base import CeresModel, Note, NoteCategory, ShipBase
from .parts import ShipPart
from .spec import ShipSpec, SpecSection


def _sensor_feature(sensor: str, *, effective_tl: int) -> str:
    if sensor in ('Radar', 'Lidar'):
        if effective_tl >= 10:
            return f'{sensor} (ELPI)'
        if effective_tl >= 9:
            return f'{sensor} (LPI)'
        return sensor
    if sensor == 'Densitometer':
        if effective_tl >= 15:
            return 'Densitometer (ELPI)'
        if effective_tl >= 13:
            return 'Densitometer (LPI)'
        return 'Densitometer'
    if sensor == 'Neural Activity Sensor':
        return 'Neural Activity Sensor (passive only)'
    return sensor


def _sensor_package_notes(
    *,
    suite: tuple[str, ...],
    dm: str,
    package_capabilities: tuple[str, ...] = (),
    effective_tl: int,
) -> list[Note]:
    features = ['Passive optical and thermal sensors']
    features.extend(_sensor_feature(sensor, effective_tl=effective_tl) for sensor in suite)
    features.extend(package_capabilities)
    notes = [
        Note(category=NoteCategory.INFO, message=f'Features: {", ".join(features)}'),
        Note(
            category=NoteCategory.INFO,
            message=f'Sensor DM {dm} to Electronics (comms) and Electronics (sensors) checks',
        ),
    ]
    return notes


def _note_tl(part: ShipPart) -> int:
    owner = getattr(part, '_ship', None)
    if owner is None:
        return part.minimum_tl
    return part.effective_tl


class SensorPackage(ShipPart):
    def bind(self, owner: ShipBase) -> None:
        super().bind(owner)
        retained_notes = [note for note in self.notes if note.category in (NoteCategory.WARNING, NoteCategory.ERROR)]
        object.__setattr__(self, 'notes', [])
        if message := self.build_item():
            self.item(message)
        self.notes.extend(self.build_notes())
        self.notes.extend(retained_notes)


class BasicSensors(SensorPackage):
    description: Literal['Basic'] = 'Basic'
    minimum_tl = 8

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return _sensor_package_notes(suite=('Radar', 'Lidar'), dm='-4', effective_tl=_note_tl(self))

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return 0.0

    def compute_power(self) -> float:
        return 0.0


class CivilianSensors(SensorPackage):
    description: Literal['Civilian Grade'] = 'Civilian Grade'
    minimum_tl = 9

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return _sensor_package_notes(suite=('Radar', 'Lidar'), dm='-2', effective_tl=_note_tl(self))

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 3_000_000.0

    def compute_power(self) -> float:
        return 1.0


class MilitarySensors(SensorPackage):
    description: Literal['Military Grade'] = 'Military Grade'
    minimum_tl = 10

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar'),
            dm='+0',
            package_capabilities=('Jammers', 'Emissions Control (EMCON)'),
            effective_tl=_note_tl(self),
        )

    def compute_tons(self) -> float:
        return 2.0

    def compute_cost(self) -> float:
        return 4_100_000.0

    def compute_power(self) -> float:
        return 2.0


class ImprovedSensors(SensorPackage):
    description: Literal['Improved Sensors'] = 'Improved Sensors'
    minimum_tl = 12

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar', 'Densitometer'),
            dm='+1',
            package_capabilities=('Jammers', 'Emissions Control (EMCON)'),
            effective_tl=_note_tl(self),
        )

    def compute_tons(self) -> float:
        return 3.0

    def compute_cost(self) -> float:
        return 4_300_000.0

    def compute_power(self) -> float:
        return 3.0


class AdvancedSensors(SensorPackage):
    description: Literal['Advanced'] = 'Advanced'
    minimum_tl = 15

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar', 'Densitometer', 'Neural Activity Sensor'),
            dm='+2',
            package_capabilities=('Jammers', 'Extreme Emissions Control'),
            effective_tl=_note_tl(self),
        )

    def compute_tons(self) -> float:
        return 5.0

    def compute_cost(self) -> float:
        return 5_300_000.0

    def compute_power(self) -> float:
        return 6.0


class CountermeasuresSuite(ShipPart):
    description: Literal['Countermeasures Suite'] = 'Countermeasures Suite'
    minimum_tl = 11

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='DM +4 to all jamming and electronic warfare attempts')]

    def compute_tons(self) -> float:
        return 2.0

    def compute_cost(self) -> float:
        return 4_000_000.0

    def compute_power(self) -> float:
        return 1.0


class LifeScannerAnalysisSuite(ShipPart):
    description: Literal['Life Scanner Analysis Suite'] = 'Life Scanner Analysis Suite'
    minimum_tl = 14

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return [
            Note(category=NoteCategory.INFO, message='Advanced ship-mounted life scanner'),
            Note(
                category=NoteCategory.INFO,
                message='Requires Electronics (sensors) to interpret; improves biological analysis',
            ),
        ]

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 4_000_000.0

    def compute_power(self) -> float:
        return 1.0


class SensorStations(ShipPart):
    count: int

    def build_item(self) -> str | None:
        if self.count == 1:
            return 'Sensor Station'
        return 'Sensor Stations'

    def bulkhead_label(self) -> str:
        if self.count == 1:
            return 'Sensor Station'
        return f'Sensor Stations × {self.count}'

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
        return cast(Any, self.ship).sensors.primary

    def compute_tons(self) -> float:
        return self._primary_suite.tons * 2

    def compute_cost(self) -> float:
        return self._primary_suite.cost * 2

    def compute_power(self) -> float:
        return self._primary_suite.power * 3


class RapidDeploymentExtendedArrays(ExtendedArrays):
    description: Literal['Rapid Deployment Extended Arrays'] = 'Rapid Deployment Extended Arrays'

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[Note]:
        return [
            Note(category=NoteCategory.INFO, message='Can expend Thrust or jump in the same round'),
            Note(category=NoteCategory.INFO, message='DM +2 to detect ship while in use'),
        ]

    def compute_cost(self) -> float:
        return self._primary_suite.cost * 4


ShipSensors = Annotated[
    BasicSensors | CivilianSensors | MilitarySensors | ImprovedSensors | AdvancedSensors,
    Field(discriminator='description'),
]


class SensorsSection(CeresModel):
    primary: ShipSensors = Field(default_factory=BasicSensors)
    life_scanner_analysis_suite: LifeScannerAnalysisSuite | None = None
    countermeasures: CountermeasuresSuite | None = None
    signal_processing: EnhancedSignalProcessing | None = None
    extended_arrays: ExtendedArrays | RapidDeploymentExtendedArrays | None = None
    sensor_stations: SensorStations | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = [self.primary]
        if self.life_scanner_analysis_suite is not None:
            parts.append(self.life_scanner_analysis_suite)
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
