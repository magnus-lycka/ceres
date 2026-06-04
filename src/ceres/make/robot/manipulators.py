"""Robot manipulator classes.

Rules: refs/robot/09_manipulators.md
"""

from math import ceil
from typing import Annotated, Any, ClassVar, Literal

from pydantic import ConfigDict, Field

from ceres.shared import CeresModel

from .chassis import RobotSize, chassis_entry
from .parts import RobotBase, RobotPart

_DELTA_TO_PCT: list[tuple[int, float]] = [
    (2, 0.40),
    (1, 0.20),
    (0, 0.10),
    (-1, 0.05),
    (-2, 0.02),
]
_DEFAULT_PCT = 0.01


def _slot_pct(delta: int) -> float:
    for threshold, pct in _DELTA_TO_PCT:
        if delta >= threshold:
            return pct
    return _DEFAULT_PCT


class Leg(CeresModel):
    """A plain walker leg with no manipulation capability."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
    type: Literal['LEG'] = 'LEG'


class Manipulator(RobotPart):
    """A robot manipulator arm.

    size=None means inherit robot size at bind time.
    str_bonus and dex_bonus are enhancements above default values.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
    type: Literal['MANIPULATOR'] = 'MANIPULATOR'

    size: RobotSize | None = None
    str_bonus: int = 0
    dex_bonus: int = 0

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)

    def resolved_size(self, robot_size: RobotSize) -> RobotSize:
        return self.size if self.size is not None else robot_size

    def default_str(self, robot_size: RobotSize) -> int:
        return 2 * int(self.resolved_size(robot_size)) - 1

    def default_dex(self, tl: int) -> int:
        return ceil(tl / 2) + 1

    def effective_str(self, robot_size: RobotSize) -> int:
        return self.default_str(robot_size) + self.str_bonus

    def effective_dex(self, tl: int) -> int:
        return self.default_dex(tl) + self.dex_bonus

    def stat_label(self, robot_size: RobotSize, tl: int) -> str:
        return f'(STR {self.effective_str(robot_size)} DEX {self.effective_dex(tl)})'

    @property
    def slots(self) -> int:
        if self._assembly is None:
            return 0
        robot_size = self.assembly.size
        resolved = self.resolved_size(robot_size)
        base_slots = chassis_entry(robot_size).base_slots
        delta = int(resolved) - int(robot_size)
        pct = _slot_pct(delta)
        return max(1, ceil(pct * base_slots))

    def bind(self, assembly: RobotBase) -> None:
        resolved = self.resolved_size(assembly.size)
        size_val = int(resolved)
        max_str_bonus = self.default_str(resolved)
        if self.str_bonus > max_str_bonus:
            raise ValueError(
                f'str_bonus {self.str_bonus} exceeds maximum {max_str_bonus} '
                f'for {resolved.name} manipulator (default STR {max_str_bonus})'
            )
        max_dex = assembly.tl + 3
        if self.effective_dex(assembly.tl) > max_dex:
            raise ValueError(
                f'dex_bonus {self.dex_bonus} would give DEX {self.effective_dex(assembly.tl)}, exceeding TL+3={max_dex}'
            )
        base_cost = 100.0 * size_val
        str_cost = 100.0 * size_val * self.str_bonus**2
        dex_cost = 200.0 * size_val * self.dex_bonus**2
        object.__setattr__(self, 'cost', base_cost + str_cost + dex_cost)
        super().bind(assembly)


LegOrManipulator = Annotated[Leg | Manipulator, Field(discriminator='type')]
