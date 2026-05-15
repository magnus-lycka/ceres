"""Tests for robot option classes.

All rule data from:
  refs/robot/21_cleaning_options.md
  refs/robot/29_storage_compartment.md
  refs/robot/31_neural_activity_sensor.md    (Recon Sensor)
  refs/robot/22_communications_options.md    (Robotic Drone Controller)
  refs/robot/07_chassis_options.md           (Decreased Resiliency)
"""

import pytest

from ceres.make.robot import (
    PrimitiveBrain,
    Robot,
    RobotSize,
    WheelsLocomotion,
)
from ceres.make.robot.options import (
    DecreasedResiliency,
    DomesticCleaningEquipment,
    ExternalPower,
    ReconSensor,
    RoboticDroneController,
    StorageCompartment,
)
from ceres.make.robot.skills import SkillGrant


def _robot(size=RobotSize.SIZE_3, tl=8, locomotion=None) -> Robot:
    return Robot(
        name='T',
        tl=tl,
        size=size,
        locomotion=locomotion or WheelsLocomotion(),
        brain=PrimitiveBrain(),
    )


# ──────────────────────────────────────────────────────
# StorageCompartment
# ──────────────────────────────────────────────────────


class TestStorageCompartment:
    """refs/robot/29_storage_compartment.md — Cr50/slot, TL6."""

    def test_slots_equals_slots_count(self):
        opt = StorageCompartment(slots_count=4)
        assert opt.slots == 4

    def test_cost(self):
        assert StorageCompartment(slots_count=4).cost == 200.0

    def test_cost_single_slot(self):
        assert StorageCompartment(slots_count=1).cost == 50.0

    def test_tl(self):
        assert StorageCompartment(slots_count=1).tl == 6

    def test_label(self):
        robot = _robot()
        opt = StorageCompartment(slots_count=4)
        opt.bind(robot)
        assert opt.notes.item_message == 'Storage Compartment (4 Slots)'

    def test_label_different_count(self):
        robot = _robot()
        opt = StorageCompartment(slots_count=1)
        opt.bind(robot)
        assert opt.notes.item_message == 'Storage Compartment (1 Slots)'


# ──────────────────────────────────────────────────────
# DomesticCleaningEquipment
# ──────────────────────────────────────────────────────


class TestDomesticCleaningEquipment:
    """refs/robot/21_cleaning_options.md."""

    @pytest.mark.parametrize(
        'size, expected_slots, expected_cost',
        [
            ('small', 1, 100.0),
            ('medium', 4, 1000.0),
            ('large', 8, 5000.0),
        ],
    )
    def test_slots_and_cost(self, size, expected_slots, expected_cost):
        opt = DomesticCleaningEquipment(size=size)
        assert opt.slots == expected_slots
        assert opt.cost == expected_cost

    def test_tl(self):
        assert DomesticCleaningEquipment(size='small').tl == 5

    def test_label(self):
        robot = _robot()
        opt = DomesticCleaningEquipment(size='small')
        opt.bind(robot)
        assert opt.notes.item_message == 'Domestic Cleaning Equipment (small)'

    def test_label_medium(self):
        robot = _robot()
        opt = DomesticCleaningEquipment(size='medium')
        opt.bind(robot)
        assert opt.notes.item_message == 'Domestic Cleaning Equipment (medium)'


# ──────────────────────────────────────────────────────
# ReconSensor
# ──────────────────────────────────────────────────────


class TestReconSensor:
    """refs/robot/31_neural_activity_sensor.md — Recon Sensor table."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_slots, expected_level, expected_cost',
        [
            ('basic', 7, 2, 1, 1000.0),
            ('improved', 8, 1, 1, 100.0),
            ('enhanced', 10, 1, 2, 10000.0),
            ('advanced', 12, 1, 3, 20000.0),
        ],
    )
    def test_table_values(self, quality, expected_tl, expected_slots, expected_level, expected_cost):
        opt = ReconSensor(quality=quality)
        assert opt.tl == expected_tl
        assert opt.slots == expected_slots
        assert opt.cost == expected_cost
        grants = opt.skill_grants
        assert len(grants) == 1
        assert grants[0] == SkillGrant('Recon', expected_level)

    def test_default_quality_is_improved(self):
        assert ReconSensor().quality == 'improved'

    def test_label(self):
        robot = _robot()
        opt = ReconSensor(quality='improved')
        opt.bind(robot)
        assert opt.notes.item_message == 'Recon Sensor (improved)'

    def test_skill_not_modified_by_int(self):
        # Recon Sensor skills are hardware-based, not subject to INT DM.
        # Skill grant is always the table value regardless of brain INT.
        opt = ReconSensor(quality='improved')
        assert opt.skill_grants == (SkillGrant('Recon', 1),)


# ──────────────────────────────────────────────────────
# ExternalPower
# ──────────────────────────────────────────────────────


class TestExternalPower:
    """refs/robot/29_storage_compartment.md — External Power: 5% of base slots (ceil), Cr100/base slot."""

    def test_tl(self):
        assert ExternalPower().tl == 9

    @pytest.mark.parametrize(
        'size, expected_slots',
        [
            (RobotSize.SIZE_1, 1),  # ceil(0.05 * 1)   = 1
            (RobotSize.SIZE_3, 1),  # ceil(0.05 * 4)   = 1
            (RobotSize.SIZE_5, 1),  # ceil(0.05 * 16)  = 1
            (RobotSize.SIZE_6, 2),  # ceil(0.05 * 32)  = 2
            (RobotSize.SIZE_7, 4),  # ceil(0.05 * 64)  = 4
            (RobotSize.SIZE_8, 7),  # ceil(0.05 * 128) = 7
        ],
    )
    def test_slots_by_size(self, size, expected_slots):
        robot = _robot(size=size)
        opt = ExternalPower()
        opt.bind(robot)
        assert opt.slots == expected_slots

    @pytest.mark.parametrize(
        'size, expected_cost',
        [
            (RobotSize.SIZE_1, 100.0),  # 1 base slot × Cr100
            (RobotSize.SIZE_3, 400.0),  # 4 base slots × Cr100
            (RobotSize.SIZE_5, 1600.0),  # 16 base slots × Cr100
        ],
    )
    def test_cost_by_size(self, size, expected_cost):
        robot = _robot(size=size)
        opt = ExternalPower()
        opt.bind(robot)
        assert opt.cost == expected_cost

    def test_label(self):
        robot = _robot()
        opt = ExternalPower()
        opt.bind(robot)
        assert opt.notes.item_message == 'External Power'


# ──────────────────────────────────────────────────────
# RoboticDroneController
# ──────────────────────────────────────────────────────


class TestRoboticDroneController:
    """refs/robot/22_communications_options.md — Robotic Drone Controller table."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_slots, expected_cost',
        [
            ('basic', 7, 2, 2000.0),
            ('improved', 9, 1, 10000.0),
            ('enhanced', 10, 1, 20000.0),
            ('advanced', 11, 1, 50000.0),
        ],
    )
    def test_table_values(self, quality, expected_tl, expected_slots, expected_cost):
        opt = RoboticDroneController(quality=quality)
        assert opt.tl == expected_tl
        assert opt.slots == expected_slots
        assert opt.cost == expected_cost

    def test_default_quality_is_basic(self):
        assert RoboticDroneController().quality == 'basic'

    def test_label(self):
        robot = _robot()
        opt = RoboticDroneController(quality='basic')
        opt.bind(robot)
        assert opt.notes.item_message == 'Robotic Drone Controller (basic)'


# ──────────────────────────────────────────────────────
# DecreasedResiliency
# ──────────────────────────────────────────────────────


class TestDecreasedResiliency:
    """refs/robot/07_chassis_options.md — Decreased Resiliency."""

    def test_hits_delta_negative(self):
        opt = DecreasedResiliency(hit_reduction=2)
        assert opt.hits_delta == -2

    def test_cost_saving_wheels(self):
        # Wheels locomotion_multiplier = 2.0
        # cost saving = -hit_reduction × Cr50 × multiplier = -2 × 50 × 2 = -Cr200
        robot = _robot()
        opt = DecreasedResiliency(hit_reduction=2)
        opt.bind(robot)
        assert opt.cost == -200.0

    def test_not_listed_in_options_display(self):
        # Decreased Resiliency is a chassis modification; build_item returns None
        robot = _robot()
        opt = DecreasedResiliency(hit_reduction=2)
        opt.bind(robot)
        assert opt.notes.item_message is None


# ──────────────────────────────────────────────────────
# Integration: options in Robot
# ──────────────────────────────────────────────────────


class TestOptionsInRobot:
    def test_recon_sensor_skill_in_skills_display(self):
        robot = Robot(
            name='T',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
            options=[ReconSensor(quality='improved')],
        )
        assert 'Recon 1' in robot.skills_display

    def test_storage_compartment_reduces_remaining_slots(self):
        robot = Robot(
            name='T',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
            options=[StorageCompartment(slots_count=2)],
        )
        # Size 3 = 4 available, storage uses 2
        assert robot.used_slots == 2
        assert robot.remaining_slots == 2
