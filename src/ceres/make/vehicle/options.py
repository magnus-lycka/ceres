"""Options: what a vehicle is fitted with.

An option is bought and installed. Most cost Credits and some consume Spaces.
What distinguishes the core options here is that they also give the vehicle a
capability the stat block reports — an Agility, a skill level, a check DM.

Only the options the current designs need are described.

Rules: refs/vehicle/09_core_options.md
"""

from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import Field

from ceres.shared import CeresModel


class _Option(CeresModel):
    """What every option can be asked, whether or not it answers."""

    @property
    def agility(self) -> int:
        return 0

    def cost(self, spaces: int) -> float:
        return 0.0

    def spaces(self, spaces: int) -> int:
        """Spaces consumed on a vehicle this big."""
        return 0


@dataclass(frozen=True)
class _Grade:
    """One row of an option's quality table."""

    tl: int
    cost: float
    value: int = 0
    range_km: int = 0


# refs/vehicle/09_core_options.md — Control Systems
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

    def cost(self, spaces: int) -> float:
        return _CONTROL[self.quality].cost


class Autopilot(_Option):
    """A system that can operate the vehicle at the skill level shown."""

    kind: Literal['AUTOPILOT'] = 'AUTOPILOT'
    quality: Literal['basic', 'improved', 'enhanced', 'advanced', 'superior'] = 'basic'

    @property
    def skill_level(self) -> int:
        return _AUTOPILOT[self.quality].value

    def cost(self, spaces: int) -> float:
        return _AUTOPILOT[self.quality].cost


class NavigationSystem(_Option):
    """Route-finding, worth a DM to Navigation checks."""

    kind: Literal['NAVIGATION_SYSTEM'] = 'NAVIGATION_SYSTEM'
    quality: Literal['basic', 'improved', 'enhanced', 'advanced', 'superior'] = 'basic'

    @property
    def navigation_dm(self) -> int:
        return _NAVIGATION[self.quality].value

    def cost(self, spaces: int) -> float:
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

    def cost(self, spaces: int) -> float:
        return _SENSORS[self.quality].cost


OptionUnion = Annotated[
    ControlSystem | Autopilot | NavigationSystem | SensorSystem,
    Field(discriminator='kind'),
]
