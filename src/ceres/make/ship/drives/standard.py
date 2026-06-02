import math
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import NoteList

from ..parts import (
    CustomisableShipPart,
    EnergyEfficient,
    EnergyInefficient,
    IncreasedSize,
    Modification,
    ShipPart,
    SizeReduction,
)
from ..power import (  # noqa: F401
    AdvancedSolarCoating,
    AntimatterPlant,
    AnyHighEfficiencyBatteries,
    AnyPowerPlant,
    AnySolarPowerSource,
    ChemicalPlant,
    EmergencyPowerSystem,
    EnhancedSolarCoating,
    FissionPlant,
    FusionPlantTL8,
    FusionPlantTL12,
    FusionPlantTL15,
    HighEfficiencyBatteriesTL10,
    HighEfficiencyBatteriesTL12,
    PowerSection,
    SpinExtSolarPanelsTL6,
    SpinExtSolarPanelsTL8,
    SpinExtSolarPanelsTL12,
    SterlingFissionPlant,
    SterlingFissionPlantTL6,
    SterlingFissionPlantTL12,
)
from ..spec import ShipSpec, SpecSection
from .spinext import AnyPlasmaDrive

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

FuelEfficient = Modification(
    name='Fuel Efficient',
    advantage=1,
    fuel_delta_percent=-0.20,
)

FuelInefficient = Modification(
    name='Fuel Inefficient',
    disadvantage=1,
    fuel_delta_percent=0.25,
)

EarlyJump = Modification(
    name='Early Jump',
    advantage=1,
    info_notes=('Can jump at the 90-diameter limit',),
)

StealthJump = Modification(
    name='Stealth Jump',
    advantage=2,
    info_notes=('Reduces jump emergence radiation signature',),
)

JumpEnergyInefficient = Modification(
    name='Energy Inefficient',
    disadvantage=1,
    power_multiplier=1.30,
)

LateJump = Modification(
    name='Late Jump',
    disadvantage=1,
    info_notes=('Requires the 150-diameter limit before jumping',),
)


class _RDrive(CustomisableShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    drive_type: str
    level: ClassVar[int]
    _tons_percent: ClassVar[float]
    high_burn_thruster: bool = False
    allowed_modifications: ClassVar[frozenset[str]] = frozenset({FuelEfficient.name, FuelInefficient.name})

    def item_description(self) -> str:
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
        notes = NoteList(super().build_notes())
        if not self.high_burn_thruster:
            return notes
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
    concealed: bool = False
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

    def item_description(self) -> str:
        if self._assembly is not None and self.assembly.performance_displacement > self.assembly.displacement:
            return f'M-Drive {self.level} ({self.assembly.performance_displacement:g}t)'
        return f'M-Drive {self.level}'

    def bulkhead_label(self) -> str:
        return 'M-Drive'

    @property
    def effective_thrust(self) -> int:
        if self.concealed:
            return math.floor(self.level / 2)
        return self.level

    def _base_tons(self) -> float:
        return self.assembly.performance_displacement * self._tons_percent

    @property
    def concealed_multiplier(self) -> float:
        return 1.25 if self.concealed else 1.0

    @property
    def tons(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return self._base_tons() * multiplier * self.concealed_multiplier

    @property
    def cost(self) -> float:
        cost = self._base_tons() * 2_000_000
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return cost * multiplier * self.concealed_multiplier

    @property
    def power(self) -> float:
        if self.level == 0:
            power = float(math.ceil(0.1 * self.assembly.performance_displacement * 0.25))
        else:
            power = float(math.ceil(0.1 * self.assembly.performance_displacement * self.level))
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return power * multiplier

    def build_notes(self) -> list:
        notes = NoteList(super().build_notes())
        if self.concealed:
            notes.info(f'Concealed manoeuvre drive: effective Thrust {self.effective_thrust}')
            notes.info('Concealed manoeuvre drive must be within 3 metres of the accelerating surface')
            notes.info('Removing the outer bulkhead does not improve concealed manoeuvre drive performance')
        return notes


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
            EarlyJump.name,
            EnergyEfficient.name,
            JumpEnergyInefficient.name,
            LateJump.name,
            SizeReduction.name,
            StealthJump.name,
        }
    )

    def item_description(self) -> str:
        if self._assembly is not None and self.assembly.performance_displacement > self.assembly.displacement:
            return f'Jump {self.level} ({self.assembly.performance_displacement:g}t)'
        return f'Jump {self.level}'

    def bulkhead_label(self) -> str:
        return 'Jump Drive'

    def build_notes(self) -> list:
        notes = NoteList(super().build_notes())
        if self.customisation is not None:
            for mod in self.customisation.modifications:
                notes.extend(mod.build_notes())
        return notes

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


class SolarSail(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    description: Literal['Solar Sail'] = 'Solar Sail'
    drive_type: Literal['solar_sail'] = 'solar_sail'
    tl: int = 9
    power: float = 0.0

    @property
    def tons(self) -> float:
        return self.assembly.displacement * 0.05

    @property
    def cost(self) -> float:
        return self.tons * 200_000

    def build_notes(self) -> list:
        notes = NoteList()
        notes.info('Effective Thrust 0 while using the solar sail as primary propulsion')
        notes.info('Requires several days to change course or speed')
        notes.info('Jump drives cannot be engaged while the solar sail is deployed')
        return notes


class _SpinExtSolarSail(ShipPart):
    cost: ClassVar[float]
    power: ClassVar[float]
    drive_type: str
    tl: int
    tons: float
    solar_panel_mode: bool = False
    thrust_per_percent: ClassVar[float]
    cost_per_ton: ClassVar[int]
    panel_power_per_ton: ClassVar[float]

    @property
    def cost(self) -> float:
        multiplier = 2 if self.solar_panel_mode else 1
        return self.tons * self.cost_per_ton * multiplier

    @property
    def power(self) -> float:
        return 0.0

    @property
    def effective_thrust(self) -> float:
        return (self.tons / self.assembly.displacement) * 100 * self.thrust_per_percent

    @property
    def output(self) -> float:
        if not self.solar_panel_mode:
            return 0.0
        return self.tons * self.panel_power_per_ton * 0.5

    def item_description(self) -> str:
        label = f'SpinExt Solar Sail (TL {self.tl}), Thrust {self.effective_thrust:g}'
        if self.output:
            label += f', Power {self.output:g}'
        return label

    def build_notes(self) -> list:
        notes = NoteList()
        notes.info('Solar sail thrust assumes operation in a star habitable zone')
        notes.info('Solar sails are useless in interstellar space')
        notes.info('Solar sails require 1D × 10 rounds to deploy or retract')
        notes.info('Ships cannot jump with solar sails deployed')
        notes.info('Ships cannot use any other manoeuvre drive while solar sails are deployed')
        if self.solar_panel_mode:
            notes.info('Acts as solar panels for double cost at half same-tonnage solar panel Power')
        return notes


class SpinExtSolarSailTL6(_SpinExtSolarSail):
    drive_type: Literal['spinext_solar_sail_tl6'] = 'spinext_solar_sail_tl6'
    tl: int = 6
    thrust_per_percent: ClassVar[float] = 0.0005
    cost_per_ton: ClassVar[int] = 200_000
    panel_power_per_ton: ClassVar[float] = 1.0


class SpinExtSolarSailTL8(_SpinExtSolarSail):
    drive_type: Literal['spinext_solar_sail_tl8'] = 'spinext_solar_sail_tl8'
    tl: int = 8
    thrust_per_percent: ClassVar[float] = 0.001
    cost_per_ton: ClassVar[int] = 400_000
    panel_power_per_ton: ClassVar[float] = 2.0


class SpinExtSolarSailTL12(_SpinExtSolarSail):
    drive_type: Literal['spinext_solar_sail_tl12'] = 'spinext_solar_sail_tl12'
    tl: int = 12
    thrust_per_percent: ClassVar[float] = 0.002
    cost_per_ton: ClassVar[int] = 800_000
    panel_power_per_ton: ClassVar[float] = 3.0


type AnySolarSail = Annotated[
    SolarSail | SpinExtSolarSailTL6 | SpinExtSolarSailTL8 | SpinExtSolarSailTL12,
    Field(discriminator='drive_type'),
]


class DriveSection(ShipPart):
    m_drive: MDrive | None = None
    r_drive: RDrive | None = None
    j_drive: JDrive | None = None
    plasma_drive: AnyPlasmaDrive | None = None
    solar_sail: AnySolarSail | None = None

    def _all_parts(self) -> list[ShipPart]:
        return [
            part
            for part in [self.m_drive, self.r_drive, self.j_drive, self.plasma_drive, self.solar_sail]
            if part is not None
        ]

    @property
    def output(self) -> float:
        if self.solar_sail is None:
            return 0.0
        return getattr(self.solar_sail, 'output', 0.0)

    def validate_jump_control(self, effective_jump_control_rating: int | None) -> None:
        if self.j_drive is None:
            return
        if effective_jump_control_rating is None:
            self.j_drive.warning('No Jump Control software')
            return
        if effective_jump_control_rating < self.j_drive.level:
            self.j_drive.warning(f'Limited to Jump {effective_jump_control_rating} by control software')

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.j_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.JUMP, self.j_drive))
        if self.r_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.PROPULSION, self.r_drive))
        if self.m_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.PROPULSION, self.m_drive))
        if self.plasma_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.PROPULSION, self.plasma_drive))
        if self.solar_sail is not None:
            output = getattr(self.solar_sail, 'output', 0.0)
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.PROPULSION,
                    self.solar_sail,
                    power=output or None,
                    emphasize_power=bool(output),
                )
            )
