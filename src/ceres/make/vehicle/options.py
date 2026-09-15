"""Options: what a vehicle is fitted with.

An option is bought and installed. Most cost Credits and some consume Spaces.
What distinguishes the core options here is that they also give the vehicle a
capability the stat block reports — an Agility, a skill level, a check DM.

Only the options the current designs need are described.

Rules: refs/vehicle/09_core_options.md
"""

from dataclasses import dataclass
from enum import StrEnum
from math import ceil
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.gear.comm import RadioTransceiverPart
from ceres.gear.computer import ComputerPart
from ceres.gear.safety import FireExtinguisherPart

from .base import InstalledInVehicle
from .grades import Grade
from .spec import EquipmentSpec


class _Option(InstalledInVehicle):
    """What every option can be asked, whether or not it answers."""

    _equipment_name: ClassVar[str]

    @property
    def grade(self) -> str | None:
        return None

    @property
    def quantity(self) -> int:
        return 1

    @property
    def equipment(self) -> EquipmentSpec:
        """This option as an item of equipment."""
        return EquipmentSpec(name=self._equipment_name, grade=self.grade, quantity=self.quantity)

    @property
    def agility(self) -> int:
        return 0

    @property
    def cost(self) -> float:
        return 0.0

    @property
    def spaces(self) -> int:
        """Spaces this consumes in the vehicle it is installed in."""
        return 0

    @property
    def comfort_points(self) -> float:
        return 0.0


class FresherSize(StrEnum):
    HALF = 'half'
    STANDARD = 'standard'
    FULL = 'full'


class GalleyKind(StrEnum):
    MINI = 'mini'
    FULL = 'full'
    GOURMET = 'gourmet'


class LifeSupportDuration(StrEnum):
    SHORT_TERM = 'short term'
    LONG_TERM = 'long term'
    CLOSED_CYCLE = 'closed cycle'


@dataclass(frozen=True)
class _GradeRow:
    """One row of an option's quality table."""

    tl: int
    cost: float
    value: int = 0
    range_km: int = 0


# refs/vehicle/09_core_options.md — Control Systems
_CONTROL: dict[Grade, _GradeRow] = {
    Grade.PRIMITIVE: _GradeRow(tl=1, cost=-25, value=-1),
    Grade.BASIC: _GradeRow(tl=0, cost=0, value=0),
    Grade.IMPROVED: _GradeRow(tl=7, cost=5_000, value=1),
    Grade.ENHANCED: _GradeRow(tl=10, cost=15_000, value=2),
    Grade.ADVANCED: _GradeRow(tl=12, cost=25_000, value=3),
    Grade.SUPERIOR: _GradeRow(tl=15, cost=100_000, value=4),
}

# refs/vehicle/09_core_options.md — Autopilot
_AUTOPILOT: dict[Grade, _GradeRow] = {
    Grade.BASIC: _GradeRow(tl=5, cost=2_000, value=0),
    Grade.IMPROVED: _GradeRow(tl=7, cost=7_500, value=1),
    Grade.ENHANCED: _GradeRow(tl=9, cost=10_000, value=2),
    Grade.ADVANCED: _GradeRow(tl=11, cost=15_000, value=3),
    Grade.SUPERIOR: _GradeRow(tl=14, cost=60_000, value=4),
}

# refs/vehicle/09_core_options.md — Navigation Systems
_NAVIGATION: dict[Grade, _GradeRow] = {
    Grade.BASIC: _GradeRow(tl=5, cost=2_000, value=1),
    Grade.IMPROVED: _GradeRow(tl=9, cost=10_000, value=2),
    Grade.ENHANCED: _GradeRow(tl=11, cost=25_000, value=3),
    Grade.ADVANCED: _GradeRow(tl=13, cost=50_000, value=4),
}

# refs/vehicle/09_core_options.md — Sensor Systems
_SENSORS: dict[Grade, _GradeRow] = {
    Grade.BASIC: _GradeRow(tl=5, cost=2_000, value=0, range_km=1),
    Grade.IMPROVED: _GradeRow(tl=7, cost=15_000, value=1, range_km=5),
    Grade.ENHANCED: _GradeRow(tl=11, cost=25_000, value=2, range_km=15),
    Grade.ADVANCED: _GradeRow(tl=13, cost=50_000, value=3, range_km=25),
    Grade.SUPERIOR: _GradeRow(tl=16, cost=100_000, value=4, range_km=50),
}


class ControlSystem(_Option):
    """How well the vehicle answers its operator.

    Any control system granting a positive Agility DM requires a powered vehicle.
    """

    kind: Literal['CONTROL_SYSTEM'] = 'CONTROL_SYSTEM'
    _equipment_name: ClassVar[str] = 'Control System'
    quality: Literal[Grade.PRIMITIVE, Grade.BASIC, Grade.IMPROVED, Grade.ENHANCED, Grade.ADVANCED, Grade.SUPERIOR] = (
        Grade.BASIC
    )

    @property
    def grade(self) -> str | None:
        return self.quality

    @property
    def agility(self) -> int:
        return _CONTROL[self.quality].value

    @property
    def cost(self) -> float:
        return _CONTROL[self.quality].cost


class Autopilot(_Option):
    """A system that can operate the vehicle at the skill level shown."""

    kind: Literal['AUTOPILOT'] = 'AUTOPILOT'
    _equipment_name: ClassVar[str] = 'Autopilot'
    quality: Literal[Grade.BASIC, Grade.IMPROVED, Grade.ENHANCED, Grade.ADVANCED, Grade.SUPERIOR] = Grade.BASIC

    @property
    def grade(self) -> str | None:
        return self.quality

    @property
    def skill_level(self) -> int:
        return _AUTOPILOT[self.quality].value

    @property
    def cost(self) -> float:
        return _AUTOPILOT[self.quality].cost


class NavigationSystem(_Option):
    """Route-finding, worth a DM to Navigation checks."""

    kind: Literal['NAVIGATION_SYSTEM'] = 'NAVIGATION_SYSTEM'
    _equipment_name: ClassVar[str] = 'Navigation System'
    # Its table stops at advanced.
    quality: Literal[Grade.BASIC, Grade.IMPROVED, Grade.ENHANCED, Grade.ADVANCED] = Grade.BASIC

    @property
    def grade(self) -> str | None:
        return self.quality

    @property
    def navigation_dm(self) -> int:
        return _NAVIGATION[self.quality].value

    @property
    def cost(self) -> float:
        return _NAVIGATION[self.quality].cost


class SensorSystem(_Option):
    """A package of active and passive sensors appropriate to its Tech Level."""

    kind: Literal['SENSOR_SYSTEM'] = 'SENSOR_SYSTEM'
    _equipment_name: ClassVar[str] = 'Sensor System'
    quality: Literal[Grade.BASIC, Grade.IMPROVED, Grade.ENHANCED, Grade.ADVANCED, Grade.SUPERIOR] = Grade.BASIC

    @property
    def grade(self) -> str | None:
        return self.quality

    @property
    def sensors_dm(self) -> int:
        return _SENSORS[self.quality].value

    @property
    def range_km(self) -> int:
        return _SENSORS[self.quality].range_km

    @property
    def cost(self) -> float:
        return _SENSORS[self.quality].cost


# refs/vehicle/13_internal_options.md — Collision Protection
_COLLISION: dict[Grade, _GradeRow] = {
    Grade.BASIC: _GradeRow(tl=7, cost=500, value=8),
    Grade.IMPROVED: _GradeRow(tl=9, cost=1_000, value=12),
    Grade.ADVANCED: _GradeRow(tl=12, cost=2_000, value=20),
}

# refs/vehicle/13_internal_options.md — Life Support
_LIFE_SUPPORT: dict[LifeSupportDuration, _GradeRow] = {
    LifeSupportDuration.SHORT_TERM: _GradeRow(tl=4, cost=10_000, value=20),
    LifeSupportDuration.LONG_TERM: _GradeRow(tl=6, cost=50_000, value=5),
    LifeSupportDuration.CLOSED_CYCLE: _GradeRow(tl=8, cost=100_000, value=5),
}

# refs/vehicle/13_internal_options.md — Fresher and Galley, by Spaces and Cost per Space
# (TL, Spaces, Cost per Space, Comfort Points)
_FRESHER: dict[FresherSize, tuple[int, int, float, float]] = {
    FresherSize.HALF: (4, 1, 500, 1),
    FresherSize.STANDARD: (5, 2, 750, 2),
    FresherSize.FULL: (5, 4, 1_500, 8),
}
_GALLEY: dict[GalleyKind, tuple[int, int, float, float]] = {
    GalleyKind.MINI: (2, 1, 250, 1),
    GalleyKind.FULL: (2, 5, 500, 5),
    GalleyKind.GOURMET: (3, 5, 2_000, 10),
}

# refs/vehicle/16_automation.md — Computers. A computer is free once the vehicle
# reaches the Tech Level at which it becomes standard equipment.
_COMPUTERS: dict[int, tuple[int, float, int]] = {
    0: (7, 1_000, 8),
    1: (8, 500, 11),
    2: (10, 1_000, 13),
    3: (12, 2_000, 16),
}

# refs/vehicle/08_options.md — Tech Level Stages. An item built well past its
# introduction is cheaper for the same capability.
_TECH_STAGE_COST: dict[Grade, float] = {
    Grade.BASIC: 1.0,
    Grade.IMPROVED: 0.5,
    Grade.ENHANCED: 0.25,
    Grade.ADVANCED: 0.1,
    Grade.SUPERIOR: 0.05,
}

# refs/vehicle/09_core_options.md — Transceivers, by range in kilometres: (TL, Cost)
_TRANSCEIVERS: dict[int, tuple[int, float]] = {
    5: (5, 200),
    50: (5, 600),
    500: (6, 600),
    5_000: (6, 3_000),
    50_000: (7, 50_000),
    500_000: (9, 50_000),
}

# refs/vehicle/09_core_options.md — Transceiver Options
_SATELLITE_UPLINK_COST = 1_000
_TIGHTBEAM_COST = 2_000
_ENCRYPTION_COST = 4_000


class CollisionProtection(_Option):
    """Airbags, gel or grav plates protecting the Spaces occupants sit in.

    Priced per Space protected, and includes vehicle-wide fire suppression.
    """

    kind: Literal['COLLISION_PROTECTION'] = 'COLLISION_PROTECTION'
    _equipment_name: ClassVar[str] = 'Collision Protection'
    quality: Literal[Grade.BASIC, Grade.IMPROVED, Grade.ADVANCED] = Grade.BASIC

    @property
    def grade(self) -> str | None:
        return self.quality

    spaces_protected: int = 1

    @property
    def quantity(self) -> int:
        return self.spaces_protected

    @property
    def protection(self) -> int:
        return _COLLISION[self.quality].value

    @property
    def cost(self) -> float:
        return _COLLISION[self.quality].cost * self.spaces_protected


class AirLock(_Option):
    """Lets occupants in and out without exposing the interior."""

    kind: Literal['AIR_LOCK'] = 'AIR_LOCK'
    _equipment_name: ClassVar[str] = 'Air Lock'
    count: int = 1

    @property
    def quantity(self) -> int:
        return self.count

    @property
    def spaces(self) -> int:
        return 2 * self.count

    @property
    def cost(self) -> float:
        return 2_000 * self.count


class LifeSupport(_Option):
    """A breathable atmosphere independent of the one outside."""

    kind: Literal['LIFE_SUPPORT'] = 'LIFE_SUPPORT'
    _equipment_name: ClassVar[str] = 'Life Support'
    duration: LifeSupportDuration = LifeSupportDuration.SHORT_TERM
    people: int = 1

    @property
    def grade(self) -> str | None:
        return self.duration

    @property
    def spaces(self) -> int:
        per_space = _LIFE_SUPPORT[self.duration].value
        return max(ceil(self.people / per_space), 1)

    @property
    def cost(self) -> float:
        return _LIFE_SUPPORT[self.duration].cost * self.spaces


class Bunk(_Option):
    """Cramped sleeping space for two, and somewhere to put their things."""

    kind: Literal['BUNK'] = 'BUNK'
    _equipment_name: ClassVar[str] = 'Bunk'
    count: int = 1

    @property
    def quantity(self) -> int:
        return self.count

    @property
    def spaces(self) -> int:
        return self.count

    @property
    def cost(self) -> float:
        return 200 * self.count

    @property
    def comfort_points(self) -> float:
        return float(self.count)


class Fresher(_Option):
    """Hygiene facilities."""

    kind: Literal['FRESHER'] = 'FRESHER'
    _equipment_name: ClassVar[str] = 'Fresher'
    quality: FresherSize = FresherSize.STANDARD

    @property
    def grade(self) -> str | None:
        return self.quality

    @property
    def spaces(self) -> int:
        return _FRESHER[self.quality][1]

    @property
    def cost(self) -> float:
        return _FRESHER[self.quality][2] * self.spaces

    @property
    def comfort_points(self) -> float:
        return _FRESHER[self.quality][3]


class Galley(_Option):
    """Food preparation and serving."""

    kind: Literal['GALLEY'] = 'GALLEY'
    _equipment_name: ClassVar[str] = 'Galley'
    quality: GalleyKind = GalleyKind.MINI

    @property
    def grade(self) -> str | None:
        return self.quality

    @property
    def spaces(self) -> int:
        return _GALLEY[self.quality][1]

    @property
    def cost(self) -> float:
        return _GALLEY[self.quality][2] * self.spaces

    @property
    def comfort_points(self) -> float:
        return _GALLEY[self.quality][3]


class EntertainmentSystem(_Option):
    """Audio and, at higher Tech Levels, visual media."""

    kind: Literal['ENTERTAINMENT_SYSTEM'] = 'ENTERTAINMENT_SYSTEM'
    _equipment_name: ClassVar[str] = 'Entertainment System'

    @property
    def cost(self) -> float:
        return 200.0

    @property
    def comfort_points(self) -> float:
        return 0.1


class VacuumEnvironment(_Option):
    """Seals the vehicle against vacuum and trace atmospheres.

    Priced by the size of the vehicle it seals, not by any volume of its own.
    """

    kind: Literal['VACUUM_ENVIRONMENT'] = 'VACUUM_ENVIRONMENT'
    _equipment_name: ClassVar[str] = 'Vacuum Environment Protection'

    @property
    def cost(self) -> float:
        return 2_000 * self.vehicle.spaces


class FireExtinguishers(_Option):
    """Extinguishers throughout the vehicle.

    The item itself is gear (ceres.gear.safety); the vehicle rules say what
    fitting a vehicle out with them costs, which is by the vehicle's size.
    """

    kind: Literal['FIRE_EXTINGUISHERS'] = 'FIRE_EXTINGUISHERS'
    _equipment_name: ClassVar[str] = 'Fire Extinguishers'

    @property
    def part(self) -> FireExtinguisherPart:
        return FireExtinguisherPart()

    @property
    def cost(self) -> float:
        return 20 * self.vehicle.spaces


class VehicleComputer(_Option):
    """A general-purpose computer acting as the vehicle's interface.

    The computer is gear; the vehicle rules price installing one, and make it
    standard equipment at no cost once the vehicle is advanced enough.
    """

    kind: Literal['COMPUTER'] = 'COMPUTER'
    _equipment_name: ClassVar[str] = 'Computer'
    processing: int = 1

    @property
    def equipment(self) -> EquipmentSpec:
        return EquipmentSpec(name=f'{self._equipment_name}/{self.processing}')

    @property
    def part(self) -> ComputerPart:
        tl, _, _ = _COMPUTERS[self.processing]
        return ComputerPart(processing=self.processing, tl=tl)

    @property
    def cost(self) -> float:
        """Cheaper by one Tech Level Stage for each TL past its introduction, and
        free from the TL at which it is standard equipment (RIV-011)."""
        introduced_tl, listed, free_from_tl = _COMPUTERS[self.processing]
        if self.vehicle.tl >= free_from_tl:
            return 0.0
        stages = list(_TECH_STAGE_COST.values())
        levels = min(max(self.vehicle.tl - introduced_tl, 0), len(stages) - 1)
        return listed * stages[levels]


class VehicleTransceiver(_Option):
    """A radio transceiver, with the options it can carry.

    The transceiver is gear, so the vehicle installs the gear part, which says
    what the item is. The Vehicle Handbook says what fitting one costs: its
    transceiver table, discounted by the Tech Level Stage the design chooses
    (ADR-0002, RIV-011). Transceivers take no Spaces.
    """

    kind: Literal['TRANSCEIVER'] = 'TRANSCEIVER'
    _equipment_name: ClassVar[str] = 'Transceiver'
    range_km: int = 500
    stage: Literal[Grade.BASIC, Grade.IMPROVED, Grade.ENHANCED, Grade.ADVANCED, Grade.SUPERIOR] = Grade.BASIC
    satellite_uplink: bool = False
    tightbeam: bool = False
    encryption: bool = False

    @property
    def transceiver_part(self) -> RadioTransceiverPart:
        return RadioTransceiverPart(range_km=self.range_km, tl=self.vehicle.tl, cost=self._transceiver_cost)

    @property
    def grade(self) -> str | None:
        return self.stage

    @property
    def _transceiver_cost(self) -> float:
        _, listed = _TRANSCEIVERS[self.range_km]
        return listed * _TECH_STAGE_COST[self.stage]

    @property
    def cost(self) -> float:
        """The transceiver at its stage, and each option at its own price."""
        return (
            self._transceiver_cost
            + (_SATELLITE_UPLINK_COST if self.satellite_uplink else 0)
            + (_TIGHTBEAM_COST if self.tightbeam else 0)
            + (_ENCRYPTION_COST if self.encryption else 0)
        )


OptionUnion = Annotated[
    ControlSystem
    | Autopilot
    | NavigationSystem
    | SensorSystem
    | CollisionProtection
    | AirLock
    | LifeSupport
    | Bunk
    | Fresher
    | Galley
    | EntertainmentSystem
    | VacuumEnvironment
    | FireExtinguishers
    | VehicleComputer
    | VehicleTransceiver,
    Field(discriminator='kind'),
]
