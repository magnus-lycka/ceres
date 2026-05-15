from abc import ABC, abstractmethod
from typing import Any

from ceres.shared import CeresPart, NoteList

from .base import RobotBase
from .chassis import Trait
from .skills import SkillGrant


class RobotPartMixin(ABC):
    """Pure-Python ABC mixin for parts installable in a robot."""

    cost: float
    tl: int
    notes: NoteList

    @property
    @abstractmethod
    def slots(self) -> int: ...

    def bind(self, assembly: RobotBase) -> None:
        self._assembly = assembly  # type: ignore[attr-defined]
        self.check_tl()
        if message := self.build_item():  # type: ignore[attr-defined]
            self.item(message)  # type: ignore[attr-defined]

    @property
    @abstractmethod
    def assembly(self) -> RobotBase: ...

    @abstractmethod
    def build_item(self) -> str | None: ...

    @abstractmethod
    def item(self, message: str) -> None: ...

    @abstractmethod
    def error(self, message: str) -> None: ...

    @property
    def assembly_tl(self) -> int:
        return self.assembly.tl

    def check_tl(self) -> None:
        if self.assembly_tl < self.tl:
            self.error(f'Requires TL{self.tl}, robot is TL{self.assembly_tl}')

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        return ()

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        return ()


class RobotPart(CeresPart, RobotPartMixin):
    """Concrete base for robot-installable parts."""

    cost: float = 0.0

    @property
    def slots(self) -> int:
        return 0

    @property
    def assembly(self) -> RobotBase:
        a = self._assembly
        if a is None:
            raise RuntimeError(f'{type(self).__name__} not bound to an Assembly')
        if not isinstance(a, RobotBase):
            raise RuntimeError(f'{type(self).__name__} bound to unexpected type {type(a).__name__}')
        return a

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)


__all__ = ['RobotPartMixin', 'RobotPart']
