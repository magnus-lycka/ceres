"""JSON round-trip tests for Robot and its discriminated-union fields.

Design input (name, tl, size, locomotion type, brain type) must survive a
JSON round-trip unchanged. Derived values (base_armour, base_endurance,
base_chassis_cost, traits) must NOT appear in the serialised JSON.
"""

import pytest


def _make_minimal(size=3, tl=8, locomotion=None, brain=None):
    from ceres.make.robot import (
        PrimitiveBrain,
        Robot,
        RobotSize,
        WheelsLocomotion,
    )

    return Robot(
        name='Test',
        tl=tl,
        size=RobotSize(size),
        locomotion=locomotion or WheelsLocomotion(),
        brain=brain or PrimitiveBrain(),
    )


class TestRobotJsonRoundtrip:
    def test_minimal_robot_round_trips(self):
        from ceres.make.robot import Robot

        robot = _make_minimal()
        data = robot.model_dump()
        restored = Robot.model_validate(data)
        assert restored.name == robot.name
        assert restored.tl == robot.tl
        assert restored.size == robot.size
        assert type(restored.locomotion) is type(robot.locomotion)
        assert type(restored.brain) is type(robot.brain)

    def test_json_string_round_trips(self):
        from ceres.make.robot import Robot

        robot = _make_minimal()
        json_str = robot.model_dump_json()
        restored = Robot.model_validate_json(json_str)
        assert restored.tl == robot.tl
        assert restored.size == robot.size

    def test_derived_values_not_in_json(self):
        robot = _make_minimal()
        data = robot.model_dump()
        # Derived values must not be persisted as fields
        assert 'base_armour' not in data
        assert 'base_endurance' not in data
        assert 'base_chassis_cost' not in data
        assert 'traits' not in data
        assert 'available_slots' not in data
        assert 'used_slots' not in data

    def test_locomotion_discriminator_preserved(self):
        from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize

        robot = Robot(
            name='Lab',
            tl=12,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=AdvancedBrain(),
        )
        data = robot.model_dump()
        assert data['locomotion']['type'] == 'NONE'
        restored = Robot.model_validate(data)
        assert isinstance(restored.locomotion, NoneLocomotion)

    def test_brain_discriminator_preserved(self):
        from ceres.make.robot import AdvancedBrain, Robot, RobotSize, WheelsLocomotion

        robot = Robot(
            name='Lab',
            tl=12,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=AdvancedBrain(brain_tl=12),
        )
        data = robot.model_dump()
        assert data['brain']['type'] == 'ADVANCED'
        assert data['brain']['brain_tl'] == 12
        restored = Robot.model_validate(data)
        assert isinstance(restored.brain, AdvancedBrain)
        assert restored.brain.brain_tl == 12


class TestLocomotionUnionRoundtrip:
    """Each locomotion type survives a JSON round-trip via the discriminated union."""

    @pytest.mark.parametrize(
        'loco_cls',
        [
            'NoneLocomotion',
            'WheelsLocomotion',
            'WheelsAtvLocomotion',
            'TracksLocomotion',
            'GravLocomotion',
            'AeroplaneLocomotion',
            'AquaticLocomotion',
            'VtolLocomotion',
            'WalkerLocomotion',
            'HovercraftLocomotion',
            'ThrusterLocomotion',
        ],
    )
    def test_locomotion_roundtrip(self, loco_cls):
        import importlib

        mod = importlib.import_module('ceres.make.robot.locomotion')
        cls = getattr(mod, loco_cls)
        from pydantic import TypeAdapter

        from ceres.make.robot.locomotion import LocomotionUnion

        adapter = TypeAdapter(LocomotionUnion)
        loco = cls()
        restored = adapter.validate_json(loco.model_dump_json())
        assert type(restored) is cls
