from ceres.shared import Assembly

from .chassis import RobotSize
from .locomotion import LocomotionUnion


class RobotBase(Assembly):
    """Minimal robot interface that RobotPart subclasses depend on."""

    tl: int
    size: RobotSize
    locomotion: LocomotionUnion

    def parts_of_type(self, part_cls: type) -> list:
        return []


__all__ = ['RobotBase']
