from typing import Annotated, Any, Literal, cast

from pydantic import Field

from .base import CeresModel, NoteList, ShipBase, _Note
from .parts import ShipPart
from .spec import ShipSpec, SpecSection
from .text import format_counted_label, optional_count

LowInterceptMode = Literal['NONE', 'LPI', 'ELPI']


def _intercept_available(sensor: str, mode: LowInterceptMode, *, tl: int) -> bool:
    if mode == 'NONE':
        return True
    if sensor in ('Radar', 'Lidar'):
        return tl >= (9 if mode == 'LPI' else 10)
    if sensor == 'Densitometer':
        return tl >= (13 if mode == 'LPI' else 15)
    if sensor == 'Neural Activity Sensor':
        return False
    return False


def _sensor_feature(sensor: str, *, low_intercept: LowInterceptMode, tl: int) -> str | None:
    if sensor == 'Neural Activity Sensor':
        if low_intercept == 'NONE':
            return 'Neural Activity Sensor (passive only)'
        return None
    if low_intercept == 'NONE':
        return sensor
    if _intercept_available(sensor, low_intercept, tl=tl):
        return f'{sensor} ({low_intercept})'
    if sensor in ('Radar', 'Lidar'):
        return sensor
    return None


def _sensor_package_notes(
    *,
    suite: tuple[str, ...],
    dm: str,
    package_capabilities: tuple[str, ...] = (),
    capability_tl: int,
    low_intercept: LowInterceptMode,
) -> list[_Note]:
    features = ['Passive optical and thermal sensors']
    unavailable: list[str] = []
    for sensor in suite:
        feature = _sensor_feature(sensor, low_intercept=low_intercept, tl=capability_tl)
        if feature is not None:
            features.append(feature)
            continue
        if low_intercept != 'NONE':
            unavailable.append(sensor)
    features.extend(package_capabilities)
    notes = NoteList()
    notes.content(', '.join(features))
    notes.info(f'DM {dm} to Electronics (comms) and Electronics (sensors) checks')
    if low_intercept == 'LPI':
        notes.info('DM -1 to detect the ship by sensor emissions while using low-intercept mode')
    if low_intercept == 'ELPI':
        notes.info('DM -3 to detect the ship by sensor emissions while using low-intercept mode')
    for sensor in unavailable:
        if sensor == 'Neural Activity Sensor':
            message = f'{sensor} is unavailable in {low_intercept} mode'
        else:
            message = f'{sensor} is unavailable in {low_intercept} mode at TL{capability_tl}'
        notes.info(message)
    return notes


def _capability_tl(part: ShipPart) -> int:
    owner = getattr(part, '_assembly', None)
    if owner is None:
        return part.tl
    return part.assembly_tl


class SensorPackage(ShipPart):
    low_intercept: LowInterceptMode = 'NONE'

    def check_tl(self) -> None:
        if self.assembly_tl < self.tl:
            self.error(f'Requires TL{self.tl}, ship is TL{self.assembly_tl}')
        if self.low_intercept == 'LPI' and self.assembly_tl < 9:
            self.error('LPI requires TL9 for installed radar/lidar')
        if self.low_intercept == 'ELPI' and self.assembly_tl < 10:
            self.error('ELPI requires TL10 for installed radar/lidar')

    def bind(self, assembly: ShipBase) -> None:
        super().bind(assembly)
        retained_notes = NoteList(self.notes).problems
        object.__setattr__(self, 'notes', NoteList())
        if message := self.build_item():
            self.item(message)
        self.notes.extend(self.build_notes())
        self.notes.extend(retained_notes)


class BasicSensors(SensorPackage):
    description: Literal['Basic Sensors'] = 'Basic Sensors'
    tl: int = 8

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar'),
            dm='-4',
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return 0.0

    def compute_power(self) -> float:
        return 0.0


class CivilianSensors(SensorPackage):
    description: Literal['Civilian Grade Sensors'] = 'Civilian Grade Sensors'
    tl: int = 9

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar'),
            dm='-2',
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 6_000_000.0 if self.low_intercept != 'NONE' else 3_000_000.0

    def compute_power(self) -> float:
        return 1.0


class MilitarySensors(SensorPackage):
    description: Literal['Military Grade Sensors'] = 'Military Grade Sensors'
    tl: int = 10

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar'),
            dm='+0',
            package_capabilities=('Jammers', 'EMCON'),
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )

    def compute_tons(self) -> float:
        return 2.0

    def compute_cost(self) -> float:
        return 8_200_000.0 if self.low_intercept != 'NONE' else 4_100_000.0

    def compute_power(self) -> float:
        return 2.0


class ImprovedSensors(SensorPackage):
    description: Literal['Improved Sensors'] = 'Improved Sensors'
    tl: int = 12

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar', 'Densitometer'),
            dm='+1',
            package_capabilities=('Jammers', 'EMCON'),
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )

    def compute_tons(self) -> float:
        return 3.0

    def compute_cost(self) -> float:
        return 8_600_000.0 if self.low_intercept != 'NONE' else 4_300_000.0

    def compute_power(self) -> float:
        return 3.0


class AdvancedSensors(SensorPackage):
    description: Literal['Advanced Sensors'] = 'Advanced Sensors'
    tl: int = 15

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar', 'Densitometer', 'Neural Activity Sensor'),
            dm='+2',
            package_capabilities=('Jammers', 'Extreme Emissions Control'),
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )

    def compute_tons(self) -> float:
        return 5.0

    def compute_cost(self) -> float:
        return 10_600_000.0 if self.low_intercept != 'NONE' else 5_300_000.0

    def compute_power(self) -> float:
        return 6.0


class CountermeasuresSuite(ShipPart):
    description: Literal['Countermeasures Suite'] = 'Countermeasures Suite'
    tl: int = 11

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +4 to all jamming and electronic warfare attempts')
        return notes

    def compute_tons(self) -> float:
        return 2.0

    def compute_cost(self) -> float:
        return 4_000_000.0

    def compute_power(self) -> float:
        return 1.0


class LifeScannerAnalysisSuite(ShipPart):
    description: Literal['Life Scanner Analysis Suite'] = 'Life Scanner Analysis Suite'
    tl: int = 14

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.content('Advanced ship-mounted life scanner')
        notes.info('Requires Electronics (sensors) to interpret; improves biological analysis')
        return notes

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
        return format_counted_label('Sensor Stations', self.count)

    def compute_tons(self) -> float:
        return float(self.count)

    def compute_cost(self) -> float:
        return self.count * 500_000.0


class EnhancedSignalProcessing(ShipPart):
    description: Literal['Enhanced Signal Processing'] = 'Enhanced Signal Processing'
    tl: int = 13

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +4 to all sensor-related checks')
        return notes

    def compute_tons(self) -> float:
        return 2.0

    def compute_cost(self) -> float:
        return 8_000_000.0

    def compute_power(self) -> float:
        return 2.0


class ExtendedArrays(ShipPart):
    description: Literal['Extended Arrays'] = 'Extended Arrays'
    tl: int = 11

    def build_item(self) -> str | None:
        return self.description

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Cannot expend Thrust or jump while in use')
        notes.info('DM +2 to detect ship while in use')
        return notes

    @property
    def _primary_suite(self) -> ShipPart:
        return cast(Any, self.assembly).sensors.primary

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

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Can expend Thrust or jump in the same round')
        notes.info('DM +2 to detect ship while in use')
        return notes

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
                spec.rows_for_section(SpecSection.SENSORS)[-1].quantity = optional_count(sensor_part.count)
