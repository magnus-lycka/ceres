from abc import ABC, abstractmethod
from typing import Any, Protocol

from ceres.shared import Assembly, CeresPart, NoteList

from .base import RobotBase
from .chassis import Trait


class RobotPart(Protocol):
    """Everything a robot may ask of an installed part.

    The promise, as distinct from `RobotPartBase`, which is only shared
    implementation. Parts such as `RobotTransceiver` reach a robot through
    `RobotPartMixin` alone and never inherit the base, so consumers typed
    against the base would exclude them.

    Read-only throughout: parts are frozen models.
    """

    @property
    def tl(self) -> int: ...

    @property
    def cost(self) -> float: ...

    @property
    def slots(self) -> int: ...

    @property
    def notes(self) -> NoteList: ...


class _RobotPartMixinHost(Protocol):
    """Typing scaffolding: what `RobotPartMixin`'s own methods need of their host.

    Once a mixin method's `self` is typed as this protocol, `ty` sees only what
    the protocol declares — so it must carry the mixin's own self-called methods
    as well as the host's state, not merely the attributes the stripped mixin
    left unresolved.
    """

    @property
    def tl(self) -> int: ...

    @property
    def _assembly(self) -> Assembly | None: ...

    def _store_assembly(self, assembly: Assembly | None) -> None: ...

    def build_item(self) -> str | None: ...

    def check_tl(self) -> None: ...

    @property
    def assembly_tl(self) -> int: ...

    def item(self, message: str) -> Any: ...

    def error(self, message: str) -> Any: ...


class RobotPartMixin(ABC):
    """Reusable installation behaviour for parts installable in a robot.

    Carries behaviour only, and declares no attributes — see `ShipPartMixin`
    for why. What these methods need of their host is stated by
    `_RobotPartMixinHost`.
    """

    @property
    @abstractmethod
    def slots(self) -> int: ...

    def bind(self: _RobotPartMixinHost, assembly: RobotBase) -> None:
        self._store_assembly(assembly)
        self.check_tl()
        if message := self.build_item():
            self.item(message)

    @property
    @abstractmethod
    def assembly(self) -> RobotBase: ...

    def _robot_assembly(self: _RobotPartMixinHost) -> RobotBase:
        assembly = self._assembly
        if assembly is None:
            raise RuntimeError(f'{type(self).__name__} not bound to an Assembly')
        if not isinstance(assembly, RobotBase):
            raise TypeError(f'{type(self).__name__} bound to unexpected type {type(assembly).__name__}')
        return assembly

    def build_item(self) -> str | None:
        return None

    @abstractmethod
    def item(self, message: str) -> None: ...

    @abstractmethod
    def error(self, message: str) -> None: ...

    @property
    def assembly_tl(self) -> int:
        return self.assembly.tl

    def check_tl(self: _RobotPartMixinHost) -> None:
        if self.assembly_tl < self.tl:
            self.error(f'Requires TL{self.tl}, robot is TL{self.assembly_tl}')

    @property
    def hits_delta(self) -> int:
        return 0

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        return ()

    @property
    def skill_grants(self) -> dict[str, int]:
        return {}

    @property
    def endurance_multiplier(self) -> float:
        return 1.0

    @property
    def armour_delta(self) -> int:
        return 0

    @property
    def speed_bonus(self) -> int:
        return 0


class RobotPartBase(CeresPart, RobotPartMixin):
    """Concrete base for robot-installable parts."""

    cost: float = 0.0

    @property
    def slots(self) -> int:
        return 0

    @property
    def assembly(self) -> RobotBase:
        return self._robot_assembly()

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
