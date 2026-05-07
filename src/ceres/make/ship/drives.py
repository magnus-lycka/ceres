import math
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.gear.software import SoftwarePackage
from ceres.shared import NoteList

from .parts import (
    CustomisableShipPart,
    EnergyEfficient,
    EnergyInefficient,
    IncreasedSize,
    Modification,
    ShipPart,
    SizeReduction,
)
from .software import JumpControl
from .spec import ShipSpec, SpecSection

LimitedRange = Modification(
    name='Limited Range',
    disadvantage=1,
    info_notes=('This manoeuvre drive only functions within the 100-diameter limit',),
)

OrbitalRange = Modification(
    name='Orbital Range',
    disadvantage=2,
    info_notes=('Operational range increased to orbital distances',),
)

DecreasedFuel = Modification(
    name='Decreased Fuel',
    advantage=1,
    fuel_delta_percent=-0.05,
)


class _RDrive(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    drive_type: str
    level: ClassVar[int]
    _tons_percent: ClassVar[float]
    high_burn_thruster: bool = False

    def build_item(self) -> str | None:
        if self.high_burn_thruster:
            return f'High-Burn Thruster, Thrust {self.level}'
        return f'R-Drive Thrust {self.level}'

    def bulkhead_label(self) -> str:
        return 'R-Drive'

    @property
    def tons(self) -> float:
        return self.assembly.performance_displacement * self._tons_percent

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0

    @property
    def power(self) -> float:
        return 0.0

    def build_notes(self) -> list:
        if not self.high_burn_thruster:
            return []
        notes = NoteList()
        notes.info('No inertial compensation above manoeuvre-drive thrust')
        return notes


class RDrive0(_RDrive):
    drive_type: Literal['rdrive_0'] = 'rdrive_0'
    tl: int = 7
    level: ClassVar[int] = 0
    _tons_percent: ClassVar[float] = 0.01


class RDrive1(_RDrive):
    drive_type: Literal['rdrive_1'] = 'rdrive_1'
    tl: int = 7
    level: ClassVar[int] = 1
    _tons_percent: ClassVar[float] = 0.02


class RDrive2(_RDrive):
    drive_type: Literal['rdrive_2'] = 'rdrive_2'
    tl: int = 7
    level: ClassVar[int] = 2
    _tons_percent: ClassVar[float] = 0.04


class RDrive3(_RDrive):
    drive_type: Literal['rdrive_3'] = 'rdrive_3'
    tl: int = 7
    level: ClassVar[int] = 3
    _tons_percent: ClassVar[float] = 0.06


class RDrive4(_RDrive):
    drive_type: Literal['rdrive_4'] = 'rdrive_4'
    tl: int = 8
    level: ClassVar[int] = 4
    _tons_percent: ClassVar[float] = 0.08


class RDrive5(_RDrive):
    drive_type: Literal['rdrive_5'] = 'rdrive_5'
    tl: int = 8
    level: ClassVar[int] = 5
    _tons_percent: ClassVar[float] = 0.10


class RDrive6(_RDrive):
    drive_type: Literal['rdrive_6'] = 'rdrive_6'
    tl: int = 8
    level: ClassVar[int] = 6
    _tons_percent: ClassVar[float] = 0.12


class RDrive7(_RDrive):
    drive_type: Literal['rdrive_7'] = 'rdrive_7'
    tl: int = 9
    level: ClassVar[int] = 7
    _tons_percent: ClassVar[float] = 0.14


class RDrive8(_RDrive):
    drive_type: Literal['rdrive_8'] = 'rdrive_8'
    tl: int = 9
    level: ClassVar[int] = 8
    _tons_percent: ClassVar[float] = 0.16


class RDrive9(_RDrive):
    drive_type: Literal['rdrive_9'] = 'rdrive_9'
    tl: int = 9
    level: ClassVar[int] = 9
    _tons_percent: ClassVar[float] = 0.18


class RDrive10(_RDrive):
    drive_type: Literal['rdrive_10'] = 'rdrive_10'
    tl: int = 10
    level: ClassVar[int] = 10
    _tons_percent: ClassVar[float] = 0.20


class RDrive11(_RDrive):
    drive_type: Literal['rdrive_11'] = 'rdrive_11'
    tl: int = 10
    level: ClassVar[int] = 11
    _tons_percent: ClassVar[float] = 0.22


class RDrive12(_RDrive):
    drive_type: Literal['rdrive_12'] = 'rdrive_12'
    tl: int = 10
    level: ClassVar[int] = 12
    _tons_percent: ClassVar[float] = 0.24


class RDrive13(_RDrive):
    drive_type: Literal['rdrive_13'] = 'rdrive_13'
    tl: int = 11
    level: ClassVar[int] = 13
    _tons_percent: ClassVar[float] = 0.26


class RDrive14(_RDrive):
    drive_type: Literal['rdrive_14'] = 'rdrive_14'
    tl: int = 11
    level: ClassVar[int] = 14
    _tons_percent: ClassVar[float] = 0.28


class RDrive15(_RDrive):
    drive_type: Literal['rdrive_15'] = 'rdrive_15'
    tl: int = 11
    level: ClassVar[int] = 15
    _tons_percent: ClassVar[float] = 0.30


class RDrive16(_RDrive):
    drive_type: Literal['rdrive_16'] = 'rdrive_16'
    tl: int = 12
    level: ClassVar[int] = 16
    _tons_percent: ClassVar[float] = 0.32


type RDrive = Annotated[
    RDrive0
    | RDrive1
    | RDrive2
    | RDrive3
    | RDrive4
    | RDrive5
    | RDrive6
    | RDrive7
    | RDrive8
    | RDrive9
    | RDrive10
    | RDrive11
    | RDrive12
    | RDrive13
    | RDrive14
    | RDrive15
    | RDrive16,
    Field(discriminator='drive_type'),
]


class _MDrive(CustomisableShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    drive_type: str
    level: ClassVar[int]
    _tons_percent: ClassVar[float]
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            EnergyEfficient.name,
            EnergyInefficient.name,
            IncreasedSize.name,
            LimitedRange.name,
            OrbitalRange.name,
            SizeReduction.name,
        }
    )

    def build_item(self) -> str | None:
        if self._assembly is not None and self.assembly.transported_external_displacement > 0:
            return f'M-Drive {self.level} ({self.assembly.performance_displacement:g}t)'
        return f'M-Drive {self.level}'

    def bulkhead_label(self) -> str:
        return 'M-Drive'

    def _base_tons(self) -> float:
        return self.assembly.performance_displacement * self._tons_percent

    @property
    def tons(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return self._base_tons() * multiplier

    @property
    def cost(self) -> float:
        cost = self._base_tons() * 2_000_000
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return cost * multiplier

    @property
    def power(self) -> float:
        if self.level == 0:
            power = float(math.ceil(0.1 * self.assembly.performance_displacement * 0.25))
        else:
            power = float(math.ceil(0.1 * self.assembly.performance_displacement * self.level))
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return power * multiplier


class MDrive0(_MDrive):
    drive_type: Literal['mdrive_0'] = 'mdrive_0'
    tl: int = 9
    level: ClassVar[int] = 0
    _tons_percent: ClassVar[float] = 0.005


class MDrive1(_MDrive):
    drive_type: Literal['mdrive_1'] = 'mdrive_1'
    tl: int = 9
    level: ClassVar[int] = 1
    _tons_percent: ClassVar[float] = 0.01


class MDrive2(_MDrive):
    drive_type: Literal['mdrive_2'] = 'mdrive_2'
    tl: int = 10
    level: ClassVar[int] = 2
    _tons_percent: ClassVar[float] = 0.02


class MDrive3(_MDrive):
    drive_type: Literal['mdrive_3'] = 'mdrive_3'
    tl: int = 10
    level: ClassVar[int] = 3
    _tons_percent: ClassVar[float] = 0.03


class MDrive4(_MDrive):
    drive_type: Literal['mdrive_4'] = 'mdrive_4'
    tl: int = 11
    level: ClassVar[int] = 4
    _tons_percent: ClassVar[float] = 0.04


class MDrive5(_MDrive):
    drive_type: Literal['mdrive_5'] = 'mdrive_5'
    tl: int = 11
    level: ClassVar[int] = 5
    _tons_percent: ClassVar[float] = 0.05


class MDrive6(_MDrive):
    drive_type: Literal['mdrive_6'] = 'mdrive_6'
    tl: int = 12
    level: ClassVar[int] = 6
    _tons_percent: ClassVar[float] = 0.06


class MDrive7(_MDrive):
    drive_type: Literal['mdrive_7'] = 'mdrive_7'
    tl: int = 13
    level: ClassVar[int] = 7
    _tons_percent: ClassVar[float] = 0.07


class MDrive8(_MDrive):
    drive_type: Literal['mdrive_8'] = 'mdrive_8'
    tl: int = 14
    level: ClassVar[int] = 8
    _tons_percent: ClassVar[float] = 0.08


class MDrive9(_MDrive):
    drive_type: Literal['mdrive_9'] = 'mdrive_9'
    tl: int = 15
    level: ClassVar[int] = 9
    _tons_percent: ClassVar[float] = 0.09


class MDrive10(_MDrive):
    drive_type: Literal['mdrive_10'] = 'mdrive_10'
    tl: int = 16
    level: ClassVar[int] = 10
    _tons_percent: ClassVar[float] = 0.10


class MDrive11(_MDrive):
    drive_type: Literal['mdrive_11'] = 'mdrive_11'
    tl: int = 17
    level: ClassVar[int] = 11
    _tons_percent: ClassVar[float] = 0.11


type MDrive = Annotated[
    MDrive0
    | MDrive1
    | MDrive2
    | MDrive3
    | MDrive4
    | MDrive5
    | MDrive6
    | MDrive7
    | MDrive8
    | MDrive9
    | MDrive10
    | MDrive11,
    Field(discriminator='drive_type'),
]


class _JDrive(CustomisableShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    drive_type: str
    level: ClassVar[int]
    _tons_percent: ClassVar[float]
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            DecreasedFuel.name,
            EnergyEfficient.name,
            SizeReduction.name,
        }
    )

    def build_item(self) -> str | None:
        if self._assembly is not None and self.assembly.transported_external_displacement > 0:
            return f'Jump {self.level} ({self.assembly.performance_displacement:g}t)'
        return f'Jump {self.level}'

    def bulkhead_label(self) -> str:
        return 'Jump Drive'

    @property
    def parsecs(self) -> int:
        return self.level

    @property
    def tons(self) -> float:
        base_tons = self.assembly.performance_displacement * self._tons_percent + 5
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return base_tons * multiplier

    @property
    def cost(self) -> float:
        base_cost = (self.assembly.performance_displacement * self._tons_percent + 5) * 1_500_000
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return base_cost * multiplier

    @property
    def power(self) -> float:
        base_power = float(math.ceil(0.1 * self.assembly.performance_displacement * self.level))
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return base_power * multiplier


class JDrive1(_JDrive):
    drive_type: Literal['jdrive_1'] = 'jdrive_1'
    tl: int = 9
    level: ClassVar[int] = 1
    _tons_percent: ClassVar[float] = 0.025


class JDrive2(_JDrive):
    drive_type: Literal['jdrive_2'] = 'jdrive_2'
    tl: int = 11
    level: ClassVar[int] = 2
    _tons_percent: ClassVar[float] = 0.05


class JDrive3(_JDrive):
    drive_type: Literal['jdrive_3'] = 'jdrive_3'
    tl: int = 12
    level: ClassVar[int] = 3
    _tons_percent: ClassVar[float] = 0.075


class JDrive4(_JDrive):
    drive_type: Literal['jdrive_4'] = 'jdrive_4'
    tl: int = 13
    level: ClassVar[int] = 4
    _tons_percent: ClassVar[float] = 0.10


class JDrive5(_JDrive):
    drive_type: Literal['jdrive_5'] = 'jdrive_5'
    tl: int = 14
    level: ClassVar[int] = 5
    _tons_percent: ClassVar[float] = 0.125


class JDrive6(_JDrive):
    drive_type: Literal['jdrive_6'] = 'jdrive_6'
    tl: int = 15
    level: ClassVar[int] = 6
    _tons_percent: ClassVar[float] = 0.15


class JDrive7(_JDrive):
    drive_type: Literal['jdrive_7'] = 'jdrive_7'
    tl: int = 16
    level: ClassVar[int] = 7
    _tons_percent: ClassVar[float] = 0.175


class JDrive8(_JDrive):
    drive_type: Literal['jdrive_8'] = 'jdrive_8'
    tl: int = 17
    level: ClassVar[int] = 8
    _tons_percent: ClassVar[float] = 0.20


class JDrive9(_JDrive):
    drive_type: Literal['jdrive_9'] = 'jdrive_9'
    tl: int = 18
    level: ClassVar[int] = 9
    _tons_percent: ClassVar[float] = 0.225


type JDrive = Annotated[
    JDrive1 | JDrive2 | JDrive3 | JDrive4 | JDrive5 | JDrive6 | JDrive7 | JDrive8 | JDrive9,
    Field(discriminator='drive_type'),
]


class DriveSection(ShipPart):
    m_drive: MDrive | None = None
    r_drive: RDrive | None = None
    j_drive: JDrive | None = None

    def _all_parts(self) -> list[ShipPart]:
        return [part for part in [self.m_drive, self.r_drive, self.j_drive] if part is not None]

    def validate_jump_control(self, software_packages: list[SoftwarePackage]) -> None:
        if self.j_drive is None:
            return
        jump_control = next((package for package in software_packages if isinstance(package, JumpControl)), None)
        if jump_control is None:
            self.j_drive.warning('No Jump Control software')
            return
        effective = jump_control.effective_rating
        if effective is None:
            return
        if effective < self.j_drive.level:
            self.j_drive.warning(f'Limited to Jump {effective} by control software')

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.j_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.JUMP, self.j_drive))
        if self.r_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.PROPULSION, self.r_drive))
        if self.m_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.PROPULSION, self.m_drive))


class _FusionPlant(CustomisableShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    power_per_ton: ClassVar[int]
    cost_per_ton: ClassVar[int]
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            IncreasedSize.name,
            SizeReduction.name,
            EnergyInefficient.name,
        }
    )
    output: int

    def build_item(self) -> str | None:
        return f'Fusion (TL {self.tl}), Power {self.output}'

    def bulkhead_label(self) -> str:
        return 'Power Plant'

    @property
    def fusion_tl(self) -> int:
        return self.tl

    @property
    def tons(self) -> float:
        tons = self.output / self.power_per_ton
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return tons * multiplier

    @property
    def cost(self) -> float:
        cost = (self.output / self.power_per_ton) * self.cost_per_ton
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return cost * multiplier

    @property
    def power(self) -> float:
        return 0.0


class FusionPlantTL8(_FusionPlant):
    plant_type: Literal['fusion_tl8'] = 'fusion_tl8'
    tl: int = 8
    power_per_ton = 10
    cost_per_ton = 500_000


class FusionPlantTL12(_FusionPlant):
    plant_type: Literal['fusion_tl12'] = 'fusion_tl12'
    tl: int = 12
    power_per_ton = 15
    cost_per_ton = 1_000_000


class FusionPlantTL15(_FusionPlant):
    plant_type: Literal['fusion_tl15'] = 'fusion_tl15'
    tl: int = 15
    power_per_ton = 20
    cost_per_ton = 2_000_000


class EmergencyPowerSystem(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    @classmethod
    def from_fusion_plant(cls, plant: _FusionPlant) -> EmergencyPowerSystem:
        return cls()

    def build_item(self) -> str | None:
        return 'Emergency Power System'

    @property
    def source_plant(self) -> _FusionPlant:
        power_section = getattr(self.assembly, 'power', None)
        plant = None if power_section is None else power_section.fusion_plant
        if plant is None:
            raise RuntimeError('EmergencyPowerSystem requires a fusion plant')
        return plant

    @property
    def tons(self) -> float:
        return self.source_plant.tons * 0.1

    @property
    def cost(self) -> float:
        return self.source_plant.cost * 0.1

    @property
    def power(self) -> float:
        return 0.0


class PowerSection(ShipPart):
    fusion_plant: FusionPlantTL8 | FusionPlantTL12 | FusionPlantTL15 | None = None
    emergency_power_system: EmergencyPowerSystem | None = None

    def validate_emergency_power_system(self) -> None:
        if self.emergency_power_system is not None and self.fusion_plant is None:
            raise RuntimeError('EmergencyPowerSystem requires a fusion plant')

    def _all_parts(self) -> list[ShipPart]:
        return [part for part in [self.fusion_plant, self.emergency_power_system] if part is not None]

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.fusion_plant is not None:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.POWER,
                    self.fusion_plant,
                    power=float(self.fusion_plant.output),
                    emphasize_power=True,
                )
            )
        if self.emergency_power_system is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.POWER, self.emergency_power_system))
