from typing import Annotated, Any, ClassVar, Literal, cast

from pydantic import Field

from ceres.shared import CeresModel, NoteList, _Note

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
    notes: ClassVar[NoteList]
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    base_tons: ClassVar[float] = 0.0
    base_cost: ClassVar[float] = 0.0
    base_power: ClassVar[float] = 0.0
    low_intercept: LowInterceptMode = 'NONE'

    @property
    def notes(self) -> NoteList:
        notes = NoteList()
        if message := self.build_item():
            notes.item(message)
        notes.extend(self.build_notes())
        notes.extend(self._tl_notes())
        return notes

    def check_tl(self) -> None:
        return None

    def _tl_notes(self) -> NoteList:
        notes = NoteList()
        owner = getattr(self, '_assembly', None)
        if owner is None:
            return notes
        if self.assembly_tl < self.tl:
            notes.error(f'Requires TL{self.tl}, ship is TL{self.assembly_tl}')
        if self.low_intercept == 'LPI' and self.assembly_tl < 9:
            notes.error('LPI requires TL9 for installed radar/lidar')
        if self.low_intercept == 'ELPI' and self.assembly_tl < 10:
            notes.error('ELPI requires TL10 for installed radar/lidar')
        return notes

    @property
    def tons(self) -> float:
        return self.base_tons

    @property
    def cost(self) -> float:
        return self.base_cost * (2 if self.low_intercept != 'NONE' else 1)

    @property
    def power(self) -> float:
        return self.base_power


class BasicSensors(SensorPackage):
    description: Literal['Basic Sensors'] = 'Basic Sensors'
    tl: int = 8

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar'),
            dm='-4',
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )


class CivilianSensors(SensorPackage):
    description: Literal['Civilian Grade Sensors'] = 'Civilian Grade Sensors'
    tl: int = 9
    base_tons: ClassVar[float] = 1.0
    base_cost: ClassVar[float] = 3_000_000.0
    base_power: ClassVar[float] = 1.0

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar'),
            dm='-2',
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )


class MilitarySensors(SensorPackage):
    description: Literal['Military Grade Sensors'] = 'Military Grade Sensors'
    tl: int = 10
    base_tons: ClassVar[float] = 2.0
    base_cost: ClassVar[float] = 4_100_000.0
    base_power: ClassVar[float] = 2.0

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar'),
            dm='+0',
            package_capabilities=('Jammers', 'EMCON'),
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )


class ImprovedSensors(SensorPackage):
    description: Literal['Improved Sensors'] = 'Improved Sensors'
    tl: int = 12
    base_tons: ClassVar[float] = 3.0
    base_cost: ClassVar[float] = 4_300_000.0
    base_power: ClassVar[float] = 3.0

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar', 'Densitometer'),
            dm='+1',
            package_capabilities=('Jammers', 'EMCON'),
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )


class AdvancedSensors(SensorPackage):
    description: Literal['Advanced Sensors'] = 'Advanced Sensors'
    tl: int = 15
    base_tons: ClassVar[float] = 5.0
    base_cost: ClassVar[float] = 5_300_000.0
    base_power: ClassVar[float] = 6.0

    def build_notes(self) -> list[_Note]:
        return _sensor_package_notes(
            suite=('Radar', 'Lidar', 'Densitometer', 'Neural Activity Sensor'),
            dm='+2',
            package_capabilities=('Jammers', 'Extreme Emissions Control'),
            capability_tl=_capability_tl(self),
            low_intercept=self.low_intercept,
        )


class CountermeasuresSuite(ShipPart):
    description: Literal['Countermeasures Suite'] = 'Countermeasures Suite'
    tl: int = 13
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +4 to all jamming and electronic warfare attempts')
        return notes

    @property
    def tons(self) -> float:
        return 2.0

    @property
    def cost(self) -> float:
        return 4_000_000.0

    @property
    def power(self) -> float:
        return 1.0


class MilitaryCountermeasuresSuite(ShipPart):
    description: Literal['Military Countermeasures Suite'] = 'Military Countermeasures Suite'
    tl: int = 15
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +6 to all jamming and electronic warfare attempts')
        return notes

    @property
    def tons(self) -> float:
        return 15.0

    @property
    def cost(self) -> float:
        return 28_000_000.0

    @property
    def power(self) -> float:
        return 2.0


class DeepPenetrationScanners(ShipPart):
    description: Literal['Deep Penetration Scanners'] = 'Deep Penetration Scanners'
    tl: int = 13
    tons: float
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Each ton scans 20 tons of target vessel per hour at Adjacent range')
        notes.info('Can reveal layout, hidden spaces, cargo, crew, and personal effects')
        return notes

    @property
    def cost(self) -> float:
        return self.tons * 1_000_000.0

    @property
    def power(self) -> float:
        return 1.0


class LifeScanner(ShipPart):
    description: Literal['Life Scanner'] = 'Life Scanner'
    tl: int = 12
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.content('Ship-mounted life scanner; typically 70-85% accurate')
        notes.info('Requires Electronics (sensors) to interpret results')
        return notes

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def cost(self) -> float:
        return 2_000_000.0

    @property
    def power(self) -> float:
        return 1.0


class LifeScannerAnalysisSuite(ShipPart):
    description: Literal['Life Scanner Analysis Suite'] = 'Life Scanner Analysis Suite'
    tl: int = 14
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.content('Advanced ship-mounted life scanner')
        notes.info('Requires Electronics (sensors) to interpret; improves biological analysis')
        return notes

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def cost(self) -> float:
        return 4_000_000.0

    @property
    def power(self) -> float:
        return 1.0


class MailDistributionArray(ShipPart):
    description: Literal['Mail Distribution Array'] = 'Mail Distribution Array'
    tl: Literal[10, 13] = 10
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def item_description(self) -> str:
        return f'Mail Distribution Array (TL{self.tl})'

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('High-volume mail data communications array for x-boats and similar ships')
        return notes

    @property
    def tons(self) -> float:
        if self.tl == 10:
            return 10.0
        return 20.0

    @property
    def cost(self) -> float:
        if self.tl == 10:
            return 20_000_000.0
        return 10_000_000.0

    @property
    def power(self) -> float:
        return 0.0


class MineralDetectionSuite(ShipPart):
    description: Literal['Mineral Detection Suite'] = 'Mineral Detection Suite'
    tl: int = 12
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.content('Determines mineral types and quantities')
        owner = getattr(self, '_assembly', None)
        if owner is not None:
            primary = cast(Any, self.assembly).sensors.primary
            if not isinstance(primary, ImprovedSensors | AdvancedSensors):
                notes.error('Mineral detection suite requires a sensor package with a densitometer')
        return notes

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def cost(self) -> float:
        return 5_000_000.0

    @property
    def power(self) -> float:
        return 0.0


class SensorStations(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    count: int

    def item_description(self) -> str:
        if self.count == 1:
            return 'Sensor Station'
        return 'Sensor Stations'

    def bulkhead_label(self) -> str:
        return format_counted_label('Sensor Stations', self.count)

    @property
    def tons(self) -> float:
        return float(self.count)

    @property
    def cost(self) -> float:
        return self.count * 500_000.0

    @property
    def power(self) -> float:
        return 0.0


class ShallowPenetrationSuite(ShipPart):
    description: Literal['Shallow Penetration Suite'] = 'Shallow Penetration Suite'
    tl: int = 10
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.content('Thermal/EM hull penetration scanning up to Very Long range')
        return notes

    @property
    def tons(self) -> float:
        return 10.0

    @property
    def cost(self) -> float:
        return 5_000_000.0

    @property
    def power(self) -> float:
        return 1.0


class ImprovedSignalProcessing(ShipPart):
    description: Literal['Improved Signal Processing'] = 'Improved Signal Processing'
    tl: int = 11
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +2 to all sensor-related checks')
        notes.info('Other ships double all jamming DMs against this ship')
        return notes

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def cost(self) -> float:
        return 4_000_000.0

    @property
    def power(self) -> float:
        return 1.0


class EnhancedSignalProcessing(ShipPart):
    description: Literal['Enhanced Signal Processing'] = 'Enhanced Signal Processing'
    tl: int = 13
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('DM +4 to all sensor-related checks')
        return notes

    @property
    def tons(self) -> float:
        return 2.0

    @property
    def cost(self) -> float:
        return 8_000_000.0

    @property
    def power(self) -> float:
        return 2.0


class DistributedArray(ShipPart):
    description: Literal['Distributed Array'] = 'Distributed Array'
    tl: int = 11
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def _primary_suite(self) -> ShipPart:
        return cast(Any, self.assembly).sensors.primary

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Extends EM and active radar/lidar detection to Distant range')
        notes.info('Extends passive radar/lidar detection to Long range')
        notes.info('Only minimal information is available at the extended ranges')
        owner = getattr(self, '_assembly', None)
        if owner is not None:
            if not isinstance(self._primary_suite, ImprovedSensors | AdvancedSensors):
                notes.error('Distributed array requires Improved or Advanced sensors')
            if self.assembly.displacement <= 5_000:
                notes.error('Distributed array requires displacement greater than 5000 tons')
        return notes

    @property
    def tons(self) -> float:
        return self._primary_suite.tons * 2

    @property
    def cost(self) -> float:
        return self._primary_suite.cost * 2

    @property
    def power(self) -> float:
        return self._primary_suite.power * 3


class ExtendedArrays(ShipPart):
    description: Literal['Extended Arrays'] = 'Extended Arrays'
    tl: int = 11
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Cannot expend Thrust or jump while in use')
        notes.info('DM +2 to detect ship while in use')
        return notes

    @property
    def _primary_suite(self) -> ShipPart:
        return cast(Any, self.assembly).sensors.primary

    @property
    def tons(self) -> float:
        return self._primary_suite.tons * 2

    @property
    def cost(self) -> float:
        return self._primary_suite.cost * 2

    @property
    def power(self) -> float:
        return self._primary_suite.power * 3


class RapidDeploymentExtendedArrays(ExtendedArrays):
    description: Literal['Rapid Deployment Extended Arrays'] = 'Rapid Deployment Extended Arrays'

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Can expend Thrust or jump in the same round')
        notes.info('DM +2 to detect ship while in use')
        return notes

    @property
    def cost(self) -> float:
        return self._primary_suite.cost * 4


class ExtensionNet(ShipPart):
    description: Literal['Extension Net'] = 'Extension Net'
    tl: int = 10
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Raises Limited or Full detail range by one step')
        notes.info('Cannot be used with NAS or densitometers')
        notes.info('Cannot receive data while the deploying ship manoeuvres')
        return notes

    @property
    def tons(self) -> float:
        return max(1.0, self.assembly.displacement * 0.01)

    @property
    def cost(self) -> float:
        return self.tons * 1_000_000.0

    @property
    def power(self) -> float:
        return 0.0


ShipSensors = Annotated[
    BasicSensors | CivilianSensors | MilitarySensors | ImprovedSensors | AdvancedSensors,
    Field(discriminator='description'),
]

SignalProcessing = Annotated[
    ImprovedSignalProcessing | EnhancedSignalProcessing,
    Field(discriminator='description'),
]


class SensorsSection(CeresModel):
    primary: ShipSensors = Field(default_factory=BasicSensors)
    deep_penetration_scanners: DeepPenetrationScanners | None = None
    life_scanner: LifeScanner | None = None
    life_scanner_analysis_suite: LifeScannerAnalysisSuite | None = None
    mail_distribution_array: MailDistributionArray | None = None
    mineral_detection_suite: MineralDetectionSuite | None = None
    shallow_penetration_suite: ShallowPenetrationSuite | None = None
    countermeasures: CountermeasuresSuite | MilitaryCountermeasuresSuite | None = None
    signal_processing: SignalProcessing | None = None
    distributed_array: DistributedArray | None = None
    extended_arrays: ExtendedArrays | RapidDeploymentExtendedArrays | None = None
    extension_net: ExtensionNet | None = None
    sensor_stations: SensorStations | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = [self.primary]
        if self.deep_penetration_scanners is not None:
            parts.append(self.deep_penetration_scanners)
        if self.life_scanner is not None:
            parts.append(self.life_scanner)
        if self.life_scanner_analysis_suite is not None:
            parts.append(self.life_scanner_analysis_suite)
        if self.mail_distribution_array is not None:
            parts.append(self.mail_distribution_array)
        if self.mineral_detection_suite is not None:
            parts.append(self.mineral_detection_suite)
        if self.shallow_penetration_suite is not None:
            parts.append(self.shallow_penetration_suite)
        if self.countermeasures is not None:
            parts.append(self.countermeasures)
        if self.signal_processing is not None:
            parts.append(self.signal_processing)
        if self.distributed_array is not None:
            parts.append(self.distributed_array)
        if self.extended_arrays is not None:
            parts.append(self.extended_arrays)
        if self.extension_net is not None:
            parts.append(self.extension_net)
        if self.sensor_stations is not None:
            parts.append(self.sensor_stations)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for sensor_part in self._all_parts():
            spec.add_row(ship._spec_row_for_part(SpecSection.SENSORS, sensor_part))
            if isinstance(sensor_part, SensorStations):
                spec.rows_for_section(SpecSection.SENSORS)[-1].quantity = optional_count(sensor_part.count)
