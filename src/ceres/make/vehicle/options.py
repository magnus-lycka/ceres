"""Options: what a vehicle is fitted with.

An option is bought and installed. Most cost Credits and some consume Spaces.
What distinguishes the core options here is that they also give the vehicle a
capability the stat block reports — an Agility, a skill level, a check DM.

Only the options the current designs need are described.

Rules: refs/vehicle/09_core_options.md
"""

from dataclasses import dataclass
from math import ceil
from typing import Annotated, Literal

from pydantic import Field, PrivateAttr

from ceres.gear.comm import RadioTransceiverPart
from ceres.gear.computer import ComputerPart
from ceres.gear.safety import FireExtinguisherPart
from ceres.shared import CeresModel

from .base import VehicleBase


class _Option(CeresModel):
    """What every option can be asked, whether or not it answers.

    An option is bound to the vehicle it is installed in (ARCHITECTURE.md,
    two-phase construction), because what it costs and occupies can depend on
    that vehicle's size and Tech Level.
    """

    _vehicle: VehicleBase | None = PrivateAttr(default=None)

    def bind(self, vehicle: VehicleBase) -> None:
        self._vehicle = vehicle

    @property
    def vehicle(self) -> VehicleBase:
        if self._vehicle is None:
            raise RuntimeError(f'{type(self).__name__} is not installed in a vehicle')
        return self._vehicle

    @property
    def label(self) -> str:
        """How the equipment list names this, quality and quantity included."""
        name = _NAMES[type(self).__name__]
        quality = getattr(self, 'quality', None)
        if quality:
            name = f'{name} ({quality})'
        count = getattr(self, 'count', 1)
        if count > 1:
            name = f'{name} x{count}'
        return name

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


@dataclass(frozen=True)
class _Grade:
    """One row of an option's quality table."""

    tl: int
    cost: float
    value: int = 0
    range_km: int = 0


# refs/vehicle/09_core_options.md — Control Systems
# How each option is named in an equipment list.
_NAMES = {
    'ControlSystem': 'Control System',
    'Autopilot': 'Autopilot',
    'NavigationSystem': 'Navigation System',
    'SensorSystem': 'Sensor System',
    'CollisionProtection': 'Collision Protection',
    'AirLock': 'Air Lock',
    'LifeSupport': 'Life Support',
    'Bunk': 'Bunk',
    'Fresher': 'Fresher',
    'Galley': 'Galley',
    'EntertainmentSystem': 'Entertainment System',
    'VacuumEnvironment': 'Vacuum Environment Protection',
    'FireExtinguishers': 'Fire Extinguishers',
    'VehicleComputer': 'Computer',
    'VehicleTransceiver': 'Transceiver',
}

_CONTROL: dict[str, _Grade] = {
    'primitive': _Grade(tl=1, cost=-25, value=-1),
    'basic': _Grade(tl=0, cost=0, value=0),
    'improved': _Grade(tl=7, cost=5_000, value=1),
    'enhanced': _Grade(tl=10, cost=15_000, value=2),
    'advanced': _Grade(tl=12, cost=25_000, value=3),
    'superior': _Grade(tl=15, cost=100_000, value=4),
}

# refs/vehicle/09_core_options.md — Autopilot
_AUTOPILOT: dict[str, _Grade] = {
    'basic': _Grade(tl=5, cost=2_000, value=0),
    'improved': _Grade(tl=7, cost=7_500, value=1),
    'enhanced': _Grade(tl=9, cost=10_000, value=2),
    'advanced': _Grade(tl=11, cost=15_000, value=3),
    'superior': _Grade(tl=14, cost=60_000, value=4),
}

# refs/vehicle/09_core_options.md — Navigation Systems
_NAVIGATION: dict[str, _Grade] = {
    'basic': _Grade(tl=5, cost=2_000, value=1),
    'improved': _Grade(tl=9, cost=10_000, value=2),
    'enhanced': _Grade(tl=11, cost=25_000, value=3),
    'advanced': _Grade(tl=13, cost=50_000, value=4),
}

# refs/vehicle/09_core_options.md — Sensor Systems
_SENSORS: dict[str, _Grade] = {
    'basic': _Grade(tl=5, cost=2_000, value=0, range_km=1),
    'improved': _Grade(tl=7, cost=15_000, value=1, range_km=5),
    'enhanced': _Grade(tl=11, cost=25_000, value=2, range_km=15),
    'advanced': _Grade(tl=13, cost=50_000, value=3, range_km=25),
    'superior': _Grade(tl=16, cost=100_000, value=4, range_km=50),
}


class ControlSystem(_Option):
    """How well the vehicle answers its operator.

    Any control system granting a positive Agility DM requires a powered vehicle.
    """

    kind: Literal['CONTROL_SYSTEM'] = 'CONTROL_SYSTEM'
    quality: Literal['primitive', 'basic', 'improved', 'enhanced', 'advanced', 'superior'] = 'basic'

    @property
    def agility(self) -> int:
        return _CONTROL[self.quality].value

    @property
    def cost(self) -> float:
        return _CONTROL[self.quality].cost


class Autopilot(_Option):
    """A system that can operate the vehicle at the skill level shown."""

    kind: Literal['AUTOPILOT'] = 'AUTOPILOT'
    quality: Literal['basic', 'improved', 'enhanced', 'advanced', 'superior'] = 'basic'

    @property
    def skill_level(self) -> int:
        return _AUTOPILOT[self.quality].value

    @property
    def cost(self) -> float:
        return _AUTOPILOT[self.quality].cost


class NavigationSystem(_Option):
    """Route-finding, worth a DM to Navigation checks."""

    kind: Literal['NAVIGATION_SYSTEM'] = 'NAVIGATION_SYSTEM'
    quality: Literal['basic', 'improved', 'enhanced', 'advanced', 'superior'] = 'basic'

    @property
    def navigation_dm(self) -> int:
        return _NAVIGATION[self.quality].value

    @property
    def cost(self) -> float:
        return _NAVIGATION[self.quality].cost


class SensorSystem(_Option):
    """A package of active and passive sensors appropriate to its Tech Level."""

    kind: Literal['SENSOR_SYSTEM'] = 'SENSOR_SYSTEM'
    quality: Literal['basic', 'improved', 'enhanced', 'advanced', 'superior'] = 'basic'

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
_COLLISION: dict[str, _Grade] = {
    'basic': _Grade(tl=7, cost=500, value=8),
    'improved': _Grade(tl=9, cost=1_000, value=12),
    'advanced': _Grade(tl=12, cost=2_000, value=20),
}

# refs/vehicle/13_internal_options.md — Life Support
_LIFE_SUPPORT: dict[str, _Grade] = {
    'short_term': _Grade(tl=4, cost=10_000, value=20),
    'long_term': _Grade(tl=6, cost=50_000, value=5),
    'closed_cycle': _Grade(tl=8, cost=100_000, value=5),
}

# refs/vehicle/13_internal_options.md — Fresher and Galley, by Spaces and Cost per Space
# (TL, Spaces, Cost per Space, Comfort Points)
_FRESHER: dict[str, tuple[int, int, float, float]] = {
    'half': (4, 1, 500, 1),
    'standard': (5, 2, 750, 2),
    'full': (5, 4, 1_500, 8),
}
_GALLEY: dict[str, tuple[int, int, float, float]] = {
    'mini': (2, 1, 250, 1),
    'full': (2, 5, 500, 5),
    'gourmet': (3, 5, 2_000, 10),
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
_TECH_STAGE_COST: dict[str, float] = {
    'basic': 1.0,
    'improved': 0.5,
    'enhanced': 0.25,
    'advanced': 0.1,
    'superior': 0.05,
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
    quality: Literal['basic', 'improved', 'advanced'] = 'basic'
    spaces_protected: int = 1

    @property
    def label(self) -> str:
        return f'Collision Protection ({self.quality}) x{self.spaces_protected}'

    @property
    def protection(self) -> int:
        return _COLLISION[self.quality].value

    @property
    def cost(self) -> float:
        return _COLLISION[self.quality].cost * self.spaces_protected


class AirLock(_Option):
    """Lets occupants in and out without exposing the interior."""

    kind: Literal['AIR_LOCK'] = 'AIR_LOCK'
    count: int = 1

    @property
    def spaces(self) -> int:
        return 2 * self.count

    @property
    def cost(self) -> float:
        return 2_000 * self.count


class LifeSupport(_Option):
    """A breathable atmosphere independent of the one outside."""

    kind: Literal['LIFE_SUPPORT'] = 'LIFE_SUPPORT'
    duration: Literal['short_term', 'long_term', 'closed_cycle'] = 'short_term'
    people: int = 1

    @property
    def label(self) -> str:
        return f'Life Support ({self.duration.replace("_", " ")})'

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
    count: int = 1

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
    quality: Literal['half', 'standard', 'full'] = 'standard'

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
    quality: Literal['mini', 'full', 'gourmet'] = 'mini'

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

    @property
    def cost(self) -> float:
        return 2_000 * self.vehicle.spaces


class FireExtinguishers(_Option):
    """Extinguishers throughout the vehicle.

    The item itself is gear (ceres.gear.safety); the vehicle rules say what
    fitting a vehicle out with them costs, which is by the vehicle's size.
    """

    kind: Literal['FIRE_EXTINGUISHERS'] = 'FIRE_EXTINGUISHERS'

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
    processing: int = 1

    @property
    def label(self) -> str:
        return f'Computer/{self.processing}'

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
    range_km: int = 500
    stage: Literal['basic', 'improved', 'enhanced', 'advanced', 'superior'] = 'basic'
    satellite_uplink: bool = False
    tightbeam: bool = False
    encryption: bool = False

    @property
    def transceiver_part(self) -> RadioTransceiverPart:
        return RadioTransceiverPart(range_km=self.range_km, tl=self.vehicle.tl, cost=self._transceiver_cost)

    @property
    def label(self) -> str:
        return f'Transceiver ({self.stage})'

    @property
    def communications(self) -> str:
        """What the equipment table reports for this transceiver."""
        parts = [f'{self.range_km}km']
        if self.tightbeam:
            parts.append('tightbeam')
        if self.satellite_uplink:
            parts.append('satellite uplink')
        if self.encryption:
            parts.append('encrypted')
        return ', '.join(parts)

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
