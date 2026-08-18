"""Tests for RobotPartBase binding behaviour.

A concrete subclass is defined locally. Tests verify the contract:
- unbound part raises RuntimeError on .assembly access
- bind() sets the assembly
- TL check adds an error note when part TL > robot TL
- robot_traits defaults to empty tuple
- skill_grants defaults to empty tuple
"""

from typing import Literal

import pytest

from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion
from ceres.make.robot.base import RobotBase
from ceres.make.robot.parts import RobotPartBase, RobotPartMixin
from ceres.shared import Assembly, NoteList


class _SamplePart(RobotPartBase):
    """Minimal concrete RobotPartBase for testing — zero slots, no label."""

    type: Literal['SAMPLE'] = 'SAMPLE'
    tl: int = 5


class _LabelledPart(RobotPartBase):
    """Part that returns a label from build_item."""

    type: Literal['LABELLED'] = 'LABELLED'
    tl: int = 5

    def item_description(self) -> str:
        return 'Sample Option'


class _MixinPart(RobotPartMixin):
    cost = 0.0
    tl = 5
    _assembly: RobotBase | None = None

    def __init__(self) -> None:
        self.notes = NoteList()

    def _store_assembly(self, assembly: Assembly | None) -> None:
        """A host owns its own assembly slot; the mixin asks rather than pokes."""
        self._assembly = assembly if isinstance(assembly, RobotBase) else None

    @property
    def slots(self) -> int:
        return 0

    @property
    def assembly(self) -> RobotBase:
        return self._robot_assembly()

    def item(self, message: str) -> None:
        pass

    def error(self, message: str) -> None:
        pass


def _robot(tl: int = 8) -> Robot:
    return Robot(
        name='Test',
        tl=tl,
        size=RobotSize.SIZE_3,
        locomotion=WheelsLocomotion(),
        brain=PrimitiveBrain(),
    )


class TestUnboundPart:
    def test_assembly_raises_when_unbound(self):
        part = _SamplePart()
        with pytest.raises(RuntimeError, match='not bound'):
            _ = part.assembly

    def test_assembly_tl_raises_when_unbound(self):
        part = _SamplePart()
        with pytest.raises(RuntimeError):
            _ = part.assembly_tl


class TestBoundPart:
    def test_bind_sets_assembly(self):
        part = _SamplePart()
        robot = _robot()
        part.bind(robot)
        assert part.assembly is robot

    def test_bound_part_knows_robot_tl(self):
        part = _SamplePart()
        robot = _robot(tl=10)
        part.bind(robot)
        assert part.assembly_tl == 10

    def test_no_error_when_tl_ok(self):
        part = _SamplePart(tl=8)
        robot = _robot(tl=8)
        part.bind(robot)
        assert not part.notes.errors

    def test_error_when_part_tl_exceeds_robot_tl(self):
        part = _SamplePart(tl=12)
        robot = _robot(tl=8)
        part.bind(robot)
        assert part.notes.errors
        assert 'TL12' in part.notes.errors[0]

    def test_build_item_label_added_on_bind(self):
        part = _LabelledPart()
        robot = _robot()
        part.bind(robot)
        assert part.notes.item_message == 'Sample Option'

    def test_default_build_item_returns_no_message(self):
        part = _MixinPart()
        assert part.build_item() is None


class TestDefaultProperties:
    def test_robot_traits_empty_by_default(self):
        part = _SamplePart()
        assert part.robot_traits == ()

    def test_skill_grants_empty_by_default(self):
        part = _SamplePart()
        assert part.skill_grants == {}

    def test_default_slots_zero(self):
        part = _SamplePart()
        assert part.slots == 0


class TestRobotBaseDefault:
    def test_parts_of_type_default_returns_empty(self):
        from ceres.make.robot import RobotSize, WheelsLocomotion
        from ceres.make.robot.base import RobotBase

        base = RobotBase(tl=8, size=RobotSize.SIZE_3, locomotion=WheelsLocomotion())
        assert base.parts_of_type(str) == []


class TestWrongAssemblyType:
    def test_assembly_raises_for_wrong_type(self):
        from ceres.shared import Assembly

        part = _SamplePart()
        part._assembly = Assembly(tl=8)
        with pytest.raises(TypeError, match='unexpected type'):
            _ = part.assembly
