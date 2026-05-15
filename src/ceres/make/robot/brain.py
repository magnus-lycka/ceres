"""Robot brain types.

Brain table values from refs/robot/33_brain.md.
"""

from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import Field

from ceres.shared import CeresModel

from .skills import SkillGrant, SkillPackage, primitive_package_skills


@dataclass(frozen=True)
class _BrainEntry:
    tl: int
    bandwidth: int
    computer_x: int  # Computer/X rating; determines minimum chassis size for free fit
    cost: float
    base_int: int
    skill_dm: int


_PRIMITIVE_TABLE: tuple[_BrainEntry, ...] = (
    _BrainEntry(tl=7, bandwidth=0, computer_x=0, cost=10000.0, base_int=1, skill_dm=-2),
    _BrainEntry(tl=8, bandwidth=0, computer_x=0, cost=100.0, base_int=1, skill_dm=-2),
)

_BASIC_TABLE: tuple[_BrainEntry, ...] = (
    _BrainEntry(tl=8, bandwidth=1, computer_x=1, cost=20000.0, base_int=3, skill_dm=-1),
    _BrainEntry(tl=10, bandwidth=1, computer_x=1, cost=4000.0, base_int=4, skill_dm=-1),
)

_ADVANCED_TABLE: tuple[_BrainEntry, ...] = (
    _BrainEntry(tl=10, bandwidth=2, computer_x=2, cost=100000.0, base_int=6, skill_dm=0),
    _BrainEntry(tl=11, bandwidth=2, computer_x=2, cost=50000.0, base_int=7, skill_dm=0),
    _BrainEntry(tl=12, bandwidth=2, computer_x=2, cost=10000.0, base_int=8, skill_dm=0),
)


def _lookup(table: tuple[_BrainEntry, ...], tl: int) -> _BrainEntry:
    """Return the highest table entry whose TL is ≤ tl; fall back to lowest."""
    entry = table[0]
    for e in table:
        if e.tl <= tl:
            entry = e
    return entry


class _BrainBase(CeresModel):
    model_config = {'frozen': True}

    @property
    def base_int(self) -> int:
        raise NotImplementedError

    @property
    def bandwidth(self) -> int:
        raise NotImplementedError

    @property
    def brain_cost(self) -> float:
        raise NotImplementedError

    @property
    def skill_dm(self) -> int:
        raise NotImplementedError

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        return ()

    @property
    def remaining_bandwidth(self) -> int | None:
        return None

    def brain_slots(self, robot_tl: int, robot_size: int) -> int:
        raise NotImplementedError

    def programming_label(self) -> str:
        raise NotImplementedError


class PrimitiveBrain(_BrainBase):
    type: Literal['PRIMITIVE'] = 'PRIMITIVE'
    brain_tl: int = 8
    function: str = 'none'

    def _entry(self) -> _BrainEntry:
        return _lookup(_PRIMITIVE_TABLE, self.brain_tl)

    @property
    def base_int(self) -> int:
        return self._entry().base_int

    @property
    def bandwidth(self) -> int:
        return self._entry().bandwidth

    @property
    def brain_cost(self) -> float:
        return self._entry().cost

    @property
    def skill_dm(self) -> int:
        return self._entry().skill_dm

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        return primitive_package_skills(self.function)

    def brain_slots(self, robot_tl: int, robot_size: int) -> int:
        min_free = max(0, self._entry().computer_x - (robot_tl - self.brain_tl))
        return 1 if robot_size < min_free else 0

    def programming_label(self) -> str:
        if self.function and self.function != 'none':
            return f'Primitive ({self.function})'
        return 'Primitive'


class BasicBrain(_BrainBase):
    type: Literal['BASIC'] = 'BASIC'
    brain_tl: int = 10
    function: str = 'none'

    def _entry(self) -> _BrainEntry:
        return _lookup(_BASIC_TABLE, self.brain_tl)

    @property
    def base_int(self) -> int:
        return self._entry().base_int

    @property
    def bandwidth(self) -> int:
        return self._entry().bandwidth

    @property
    def brain_cost(self) -> float:
        return self._entry().cost

    @property
    def skill_dm(self) -> int:
        return self._entry().skill_dm

    def brain_slots(self, robot_tl: int, robot_size: int) -> int:
        min_free = max(0, self._entry().computer_x - (robot_tl - self.brain_tl))
        return 1 if robot_size < min_free else 0

    def programming_label(self) -> str:
        if self.function and self.function != 'none':
            return f'Basic ({self.function})'
        return 'Basic'


class AdvancedBrain(_BrainBase):
    type: Literal['ADVANCED'] = 'ADVANCED'
    brain_tl: int = 12
    installed_skills: tuple[SkillPackage, ...] = ()

    def _entry(self) -> _BrainEntry:
        return _lookup(_ADVANCED_TABLE, self.brain_tl)

    @property
    def base_int(self) -> int:
        return self._entry().base_int

    @property
    def bandwidth(self) -> int:
        return self._entry().bandwidth

    @property
    def brain_cost(self) -> float:
        return self._entry().cost + sum(pkg.cost for pkg in self.installed_skills)

    @property
    def skill_dm(self) -> int:
        return self._entry().skill_dm

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        dm = self.skill_dm
        return tuple(SkillGrant(pkg.name, max(0, pkg.level + dm)) for pkg in self.installed_skills)

    @property
    def used_bandwidth(self) -> int:
        return sum(pkg.bandwidth for pkg in self.installed_skills)

    @property
    def remaining_bandwidth(self) -> int | None:
        return self.bandwidth - self.used_bandwidth

    def brain_slots(self, robot_tl: int, robot_size: int) -> int:
        min_free = max(0, self._entry().computer_x - (robot_tl - self.brain_tl))
        return 1 if robot_size < min_free else 0

    def programming_label(self) -> str:
        return f'Advanced (INT {self.base_int})'


RobotBrainUnion = Annotated[
    PrimitiveBrain | BasicBrain | AdvancedBrain,
    Field(discriminator='type'),
]

__all__ = [
    'RobotBrainUnion',
    'PrimitiveBrain',
    'BasicBrain',
    'AdvancedBrain',
]
