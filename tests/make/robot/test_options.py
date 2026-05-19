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
    GravLocomotion,
    PrimitiveBrain,
    Robot,
    RobotSize,
    WheelsLocomotion,
)
from ceres.make.robot.options import (
    AgriculturalEquipment,
    Autochef,
    AvatarController,
    CamouflageAudible,
    CamouflageOlfactory,
    CamouflageVisual,
    DecreasedResiliency,
    DomesticCleaningEquipment,
    EncryptionModule,
    EnvironmentProcessor,
    ExternalPower,
    GeckoGrippers,
    InjectorNeedle,
    LightIntensifierSensor,
    NavigationSystem,
    OlfactorySensor,
    ParasiticLink,
    PrisSensor,
    ReconSensor,
    RoboticDroneController,
    SelfMaintenanceEnhancement,
    StorageCompartment,
    StylistToolkit,
    SwarmController,
    ThermalSensor,
    VacuumEnvironmentProtection,
    VehicleSpeedModification,
)
from ceres.make.robot.skills import SkillGrant


def _robot(size=RobotSize.SIZE_3, tl=8, locomotion=None, options=None) -> Robot:
    kwargs: dict = dict(
        name='T',
        tl=tl,
        size=size,
        locomotion=locomotion or WheelsLocomotion(),
        brain=PrimitiveBrain(),
    )
    if options is not None:
        kwargs['options'] = options
    return Robot(**kwargs)


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

    def test_display_label_wraps_description(self):
        robot = _robot()
        opt = StorageCompartment(slots_count=4, display_label='Sample Drawer')
        opt.bind(robot)
        assert opt.notes.item_message == 'Sample Drawer (Storage Compartment (4 Slots))'

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


# ── EncryptionModule ──────────────────────────────────────────────────────────


class TestEncryptionModule:
    """refs/robot/14_encryption_module.md — TL6, zero-slot, Cr4000."""

    def test_tl(self):
        assert EncryptionModule().tl == 6

    def test_slots_is_zero(self):
        assert EncryptionModule().slots == 0

    def test_cost(self):
        assert EncryptionModule().cost == 4000.0

    def test_label(self):
        opt = EncryptionModule()
        opt.bind(_robot())
        assert opt.notes.item_message == 'Encryption Module'

    def test_cost_added_to_robot(self):
        base = _robot(options=[])
        with_opt = _robot(options=[EncryptionModule()])
        assert with_opt.total_cost == base.total_cost + 4000.0


# ── EnvironmentProcessor ──────────────────────────────────────────────────────


class TestEnvironmentProcessor:
    """refs/robot/17_stinger.md — TL10, zero-slot, Cr10000, Heightened Senses, Recon 0."""

    def test_tl(self):
        assert EnvironmentProcessor().tl == 10

    def test_slots_is_zero(self):
        assert EnvironmentProcessor().slots == 0

    def test_cost(self):
        assert EnvironmentProcessor().cost == 10_000.0

    def test_robot_traits_has_heightened_senses(self):
        traits = EnvironmentProcessor().robot_traits
        assert len(traits) == 1
        assert traits[0].name == 'Heightened Senses'

    def test_skill_grants_recon_0(self):
        grants = EnvironmentProcessor().skill_grants
        assert grants == (SkillGrant('Recon', 0),)

    def test_label(self):
        opt = EnvironmentProcessor()
        opt.bind(_robot(tl=10))
        assert opt.notes.item_message == 'Environment Processor'

    def test_heightened_senses_in_robot_traits(self):
        robot = _robot(tl=10, options=[EnvironmentProcessor()])
        assert any(t.name == 'Heightened Senses' for t in robot.traits)

    def test_recon_0_in_skills_display(self):
        robot = _robot(tl=10, options=[EnvironmentProcessor()])
        assert 'Recon 0' in robot.skills_display


# ── ParasiticLink ──────────────────────────────────────────────────────────────


class TestParasiticLink:
    """refs/robot/16_laser_designator.md — TL10, zero-slot, Cr10000."""

    def test_tl(self):
        assert ParasiticLink().tl == 10

    def test_slots_is_zero(self):
        assert ParasiticLink().slots == 0

    def test_cost(self):
        assert ParasiticLink().cost == 10_000.0

    def test_label(self):
        opt = ParasiticLink()
        opt.bind(_robot(tl=10))
        assert opt.notes.item_message == 'Parasitic Link'

    def test_no_robot_traits(self):
        assert ParasiticLink().robot_traits == ()

    def test_no_skill_grants(self):
        assert ParasiticLink().skill_grants == ()


# ── InjectorNeedle ─────────────────────────────────────────────────────────────


class TestInjectorNeedle:
    """refs/robot/15_voder_speaker.md — TL7, zero-slot, Cr20 each."""

    def test_tl(self):
        assert InjectorNeedle().tl == 7

    def test_slots_is_zero(self):
        assert InjectorNeedle().slots == 0

    def test_cost(self):
        assert InjectorNeedle().cost == 20.0

    def test_label(self):
        opt = InjectorNeedle()
        opt.bind(_robot())
        assert opt.notes.item_message == 'Injector Needle'

    def test_multiple_injectors_add_independently(self):
        # 7 injectors: 7 × 20 = 140 added to robot cost
        base = _robot(options=[])
        with_7 = _robot(options=[InjectorNeedle() for _ in range(7)])
        assert with_7.total_cost == base.total_cost + 140.0

    def test_no_robot_traits(self):
        assert InjectorNeedle().robot_traits == ()


# ── SelfMaintenanceEnhancement ────────────────────────────────────────────────


class TestSelfMaintenanceEnhancement:
    """refs/robot/16_laser_designator.md — bind-based cost, quality basic/improved."""

    @pytest.mark.parametrize(
        'quality, expected_tl',
        [
            ('basic', 7),
            ('improved', 8),
        ],
    )
    def test_tl_by_quality(self, quality, expected_tl):
        assert SelfMaintenanceEnhancement(quality=quality).tl == expected_tl

    def test_slots_is_zero(self):
        assert SelfMaintenanceEnhancement().slots == 0

    @pytest.mark.parametrize(
        'quality, size, expected_cost',
        [
            # basic: Cr20000/slot; improved: Cr50000/slot
            ('basic', RobotSize.SIZE_1, 20_000.0),  # 20000 × 1 slot
            ('basic', RobotSize.SIZE_3, 80_000.0),  # 20000 × 4 slots
            ('improved', RobotSize.SIZE_1, 50_000.0),  # 50000 × 1 slot
            ('improved', RobotSize.SIZE_3, 200_000.0),  # 50000 × 4 slots
        ],
    )
    def test_bind_based_cost(self, quality, size, expected_cost):
        robot = _robot(size=size)
        opt = SelfMaintenanceEnhancement(quality=quality)
        opt.bind(robot)
        assert opt.cost == expected_cost

    @pytest.mark.parametrize(
        'quality, expected_multiplier',
        [
            ('basic', 1.0),
            ('improved', 2.0),
        ],
    )
    def test_endurance_multiplier(self, quality, expected_multiplier):
        assert SelfMaintenanceEnhancement(quality=quality).endurance_multiplier == expected_multiplier

    def test_label_basic(self):
        robot = _robot()
        opt = SelfMaintenanceEnhancement(quality='basic')
        opt.bind(robot)
        assert opt.notes.item_message == 'Self-Maintenance Enhancement (basic)'

    def test_label_improved(self):
        robot = _robot()
        opt = SelfMaintenanceEnhancement(quality='improved')
        opt.bind(robot)
        assert opt.notes.item_message == 'Self-Maintenance Enhancement (improved)'

    def test_improved_doubles_robot_endurance(self):
        robot_base = _robot(tl=10, options=[])
        robot_sme = _robot(tl=10, options=[SelfMaintenanceEnhancement(quality='improved')])
        assert robot_sme.base_endurance == pytest.approx(robot_base.base_endurance * 2.0)

    def test_basic_does_not_change_endurance(self):
        robot_base = _robot(tl=10, options=[])
        robot_sme = _robot(tl=10, options=[SelfMaintenanceEnhancement(quality='basic')])
        assert robot_sme.base_endurance == pytest.approx(robot_base.base_endurance)

    def test_default_endurance_multiplier_on_other_options_is_1(self):
        # EncryptionModule should return 1.0 (the default from RobotPartMixin)
        assert EncryptionModule().endurance_multiplier == 1.0


# ── VacuumEnvironmentProtection ───────────────────────────────────────────────


class TestVacuumEnvironmentProtection:
    """refs/robot/13_solar_coating.md — TL7, zero-slot, Cr600 per base slot."""

    def test_tl(self):
        assert VacuumEnvironmentProtection().tl == 7

    def test_slots_is_zero(self):
        assert VacuumEnvironmentProtection().slots == 0

    @pytest.mark.parametrize(
        'size, expected_cost',
        [
            (RobotSize.SIZE_1, 600.0),  # 600 × 1 slot
            (RobotSize.SIZE_3, 2_400.0),  # 600 × 4 slots
            (RobotSize.SIZE_5, 9_600.0),  # 600 × 16 slots
        ],
    )
    def test_bind_based_cost(self, size, expected_cost):
        robot = _robot(size=size)
        opt = VacuumEnvironmentProtection()
        opt.bind(robot)
        assert opt.cost == expected_cost

    def test_label(self):
        robot = _robot()
        opt = VacuumEnvironmentProtection()
        opt.bind(robot)
        assert opt.notes.item_message == 'Vacuum Environment Protection'

    def test_no_robot_traits(self):
        assert VacuumEnvironmentProtection().robot_traits == ()


# ── PrisSensor ────────────────────────────────────────────────────────────────


class TestPrisSensor:
    """refs/robot/18_geiger_counter.md — PRIS Sensor, TL12, zero-slot, Cr2000, IR/UV Vision."""

    def test_tl(self):
        assert PrisSensor().tl == 12

    def test_slots_is_zero(self):
        assert PrisSensor().slots == 0

    def test_cost(self):
        assert PrisSensor().cost == 2000.0

    def test_robot_traits_has_ir_uv_vision(self):
        traits = PrisSensor().robot_traits
        assert len(traits) == 1
        assert traits[0].name == 'IR/UV Vision'

    def test_label(self):
        opt = PrisSensor()
        opt.bind(_robot(tl=12))
        assert opt.notes.item_message == 'PRIS Sensor'

    def test_ir_uv_vision_in_robot_traits(self):
        robot = _robot(tl=12, options=[PrisSensor()])
        assert any(t.name == 'IR/UV Vision' for t in robot.traits)


# ── ThermalSensor ─────────────────────────────────────────────────────────────


class TestThermalSensor:
    """refs/robot/18_geiger_counter.md — Thermal Sensor, TL6, zero-slot, Cr500, IR Vision."""

    def test_tl(self):
        assert ThermalSensor().tl == 6

    def test_slots_is_zero(self):
        assert ThermalSensor().slots == 0

    def test_cost(self):
        assert ThermalSensor().cost == 500.0

    def test_robot_traits_has_ir_vision(self):
        traits = ThermalSensor().robot_traits
        assert len(traits) == 1
        assert traits[0].name == 'IR Vision'

    def test_label(self):
        opt = ThermalSensor()
        opt.bind(_robot())
        assert opt.notes.item_message == 'Thermal Sensor'


# ── LightIntensifierSensor ────────────────────────────────────────────────────


class TestLightIntensifierSensor:
    """refs/robot/18_geiger_counter.md — Light Intensifier Sensor."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_cost',
        [
            ('basic', 7, 500.0),
            ('advanced', 9, 1250.0),
        ],
    )
    def test_table_values(self, quality, expected_tl, expected_cost):
        opt = LightIntensifierSensor(quality=quality)
        assert opt.tl == expected_tl
        assert opt.cost == expected_cost

    def test_basic_has_no_trait(self):
        assert LightIntensifierSensor(quality='basic').robot_traits == ()

    def test_advanced_has_ir_vision_trait(self):
        traits = LightIntensifierSensor(quality='advanced').robot_traits
        assert len(traits) == 1
        assert traits[0].name == 'IR Vision'

    def test_label(self):
        opt = LightIntensifierSensor(quality='basic')
        opt.bind(_robot())
        assert opt.notes.item_message == 'Light Intensifier Sensor (basic)'

    def test_label_advanced(self):
        opt = LightIntensifierSensor(quality='advanced')
        opt.bind(_robot(tl=9))
        assert opt.notes.item_message == 'Light Intensifier Sensor (advanced)'


# ── OlfactorySensor ───────────────────────────────────────────────────────────


class TestOlfactorySensor:
    """refs/robot/18_geiger_counter.md — Olfactory Sensor."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_cost',
        [
            ('basic', 8, 1000.0),
            ('improved', 10, 3500.0),
            ('advanced', 12, 10000.0),
        ],
    )
    def test_table_values(self, quality, expected_tl, expected_cost):
        opt = OlfactorySensor(quality=quality)
        assert opt.tl == expected_tl
        assert opt.cost == expected_cost

    def test_basic_has_no_trait(self):
        assert OlfactorySensor(quality='basic').robot_traits == ()

    def test_improved_has_heightened_senses(self):
        traits = OlfactorySensor(quality='improved').robot_traits
        assert len(traits) == 1
        assert traits[0].name == 'Heightened Senses'

    def test_advanced_has_no_trait(self):
        assert OlfactorySensor(quality='advanced').robot_traits == ()

    def test_label(self):
        opt = OlfactorySensor(quality='improved')
        opt.bind(_robot(tl=10))
        assert opt.notes.item_message == 'Olfactory Sensor (improved)'


# ── GeckoGrippers ─────────────────────────────────────────────────────────────


class TestGeckoGrippers:
    """refs/robot/15_voder_speaker.md — Gecko Grippers, TL9, zero-slot, Cr500/base slot."""

    def test_tl(self):
        assert GeckoGrippers().tl == 9

    def test_slots_is_zero(self):
        assert GeckoGrippers().slots == 0

    @pytest.mark.parametrize(
        'size, expected_cost',
        [
            (RobotSize.SIZE_1, 500.0),  # 500 × 1 slot
            (RobotSize.SIZE_3, 2_000.0),  # 500 × 4 slots
            (RobotSize.SIZE_5, 8_000.0),  # 500 × 16 slots
        ],
    )
    def test_bind_based_cost(self, size, expected_cost):
        robot = _robot(size=size, tl=9)
        opt = GeckoGrippers()
        opt.bind(robot)
        assert opt.cost == expected_cost

    def test_label(self):
        robot = _robot(tl=9)
        opt = GeckoGrippers()
        opt.bind(robot)
        assert opt.notes.item_message == 'Gecko Grippers'

    def test_no_robot_traits(self):
        assert GeckoGrippers().robot_traits == ()


# ── CamouflageVisual ──────────────────────────────────────────────────────────


class TestCamouflageVisual:
    """refs/robot/11_zero_slot_options.md — Visual Concealment, zero-slot, bind-based cost."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_stealth_level',
        [
            ('primitive', 1, 1),  # dm=-1 → Stealth 1
            ('basic', 4, 2),  # dm=-2 → Stealth 2
            ('improved', 7, 2),  # dm=-2 → Stealth 2
            ('enhanced', 11, 3),  # dm=-3 → Stealth 3
            ('advanced', 12, 4),  # dm=-4 → Stealth 4
            ('superior', 13, 4),  # dm=-4 → Stealth 4
        ],
    )
    def test_tl_and_stealth_grant(self, quality, expected_tl, expected_stealth_level):
        opt = CamouflageVisual(quality=quality)
        assert opt.tl == expected_tl
        grants = opt.skill_grants
        assert len(grants) == 1
        assert grants[0] == SkillGrant('Stealth', expected_stealth_level)

    @pytest.mark.parametrize(
        'quality, size, expected_cost',
        [
            ('advanced', RobotSize.SIZE_1, 500.0),  # 500 × 1 slot
            ('advanced', RobotSize.SIZE_3, 2_000.0),  # 500 × 4 slots
            ('enhanced', RobotSize.SIZE_3, 400.0),  # 100 × 4 slots
        ],
    )
    def test_bind_based_cost(self, quality, size, expected_cost):
        robot = _robot(size=size, tl=13)
        opt = CamouflageVisual(quality=quality)
        opt.bind(robot)
        assert opt.cost == expected_cost

    def test_label(self):
        robot = _robot(tl=13)
        opt = CamouflageVisual(quality='advanced')
        opt.bind(robot)
        assert opt.notes.item_message == 'Camouflage: Visual (advanced)'

    def test_stealth_skill_in_robot_skills_display(self):
        robot = _robot(tl=13, options=[CamouflageVisual(quality='advanced')])
        assert 'Stealth 4' in robot.skills_display


# ── CamouflageAudible ─────────────────────────────────────────────────────────


class TestCamouflageAudible:
    """refs/robot/12_camouflage_audible_concealment.md — Audible Concealment."""

    @pytest.mark.parametrize(
        'quality, expected_tl',
        [
            ('basic', 5),
            ('improved', 8),
            ('advanced', 10),
        ],
    )
    def test_tl_by_quality(self, quality, expected_tl):
        assert CamouflageAudible(quality=quality).tl == expected_tl

    @pytest.mark.parametrize(
        'quality, size, expected_cost',
        [
            ('advanced', RobotSize.SIZE_1, 50.0),  # 50 × 1 slot
            ('advanced', RobotSize.SIZE_3, 200.0),  # 50 × 4 slots
            ('basic', RobotSize.SIZE_3, 20.0),  # 5 × 4 slots
        ],
    )
    def test_bind_based_cost(self, quality, size, expected_cost):
        robot = _robot(size=size, tl=10)
        opt = CamouflageAudible(quality=quality)
        opt.bind(robot)
        assert opt.cost == expected_cost

    def test_label(self):
        robot = _robot(tl=10)
        opt = CamouflageAudible(quality='advanced')
        opt.bind(robot)
        assert opt.notes.item_message == 'Camouflage: Audible (advanced)'

    def test_no_robot_traits(self):
        assert CamouflageAudible().robot_traits == ()

    def test_no_skill_grants(self):
        assert CamouflageAudible().skill_grants == ()


# ── CamouflageOlfactory ───────────────────────────────────────────────────────


class TestCamouflageOlfactory:
    """refs/robot/12_camouflage_audible_concealment.md — Olfactory Concealment."""

    @pytest.mark.parametrize(
        'quality, expected_tl',
        [
            ('basic', 7),
            ('improved', 9),
            ('advanced', 12),
        ],
    )
    def test_tl_by_quality(self, quality, expected_tl):
        assert CamouflageOlfactory(quality=quality).tl == expected_tl

    @pytest.mark.parametrize(
        'quality, size, expected_cost',
        [
            ('advanced', RobotSize.SIZE_1, 100.0),  # 100 × 1 slot
            ('advanced', RobotSize.SIZE_3, 400.0),  # 100 × 4 slots
            ('improved', RobotSize.SIZE_3, 80.0),  # 20 × 4 slots
        ],
    )
    def test_bind_based_cost(self, quality, size, expected_cost):
        robot = _robot(size=size, tl=12)
        opt = CamouflageOlfactory(quality=quality)
        opt.bind(robot)
        assert opt.cost == expected_cost

    def test_label(self):
        robot = _robot(tl=12)
        opt = CamouflageOlfactory(quality='advanced')
        opt.bind(robot)
        assert opt.notes.item_message == 'Camouflage: Olfactory (advanced)'


# ── NavigationSystem ──────────────────────────────────────────────────────────


class TestNavigationSystem:
    """refs/robot/32_navigation_system.md — Navigation System, basic: TL8, 2 slots, Nav 1, Cr2000."""

    def test_tl(self):
        assert NavigationSystem(quality='basic').tl == 8

    def test_slots(self):
        assert NavigationSystem(quality='basic').slots == 2

    def test_cost(self):
        assert NavigationSystem(quality='basic').cost == 2000.0

    def test_skill_grant_navigation_1(self):
        grants = NavigationSystem(quality='basic').skill_grants
        assert grants == (SkillGrant('Navigation', 1),)

    def test_label(self):
        opt = NavigationSystem(quality='basic')
        opt.bind(_robot())
        assert opt.notes.item_message == 'Navigation System (basic)'

    def test_navigation_in_robot_skills_display(self):
        robot = _robot(options=[NavigationSystem(quality='basic')])
        assert 'Navigation 1' in robot.skills_display


# ── AgriculturalEquipment ─────────────────────────────────────────────────────


class TestAgriculturalEquipment:
    """refs/robot/105_utility_robots.md — Agricultural Equipment."""

    @pytest.mark.parametrize(
        'size, expected_slots, expected_cost',
        [
            ('small', 2, 500.0),
            ('medium', 4, 1000.0),
            ('large', 8, 5000.0),
        ],
    )
    def test_table_values(self, size, expected_slots, expected_cost):
        opt = AgriculturalEquipment(size=size)
        assert opt.slots == expected_slots
        assert opt.cost == expected_cost

    def test_tl_is_5(self):
        assert AgriculturalEquipment().tl == 5

    def test_label(self):
        opt = AgriculturalEquipment(size='medium')
        opt.bind(_robot())
        assert opt.notes.item_message == 'Agricultural Equipment (medium)'


# ── Autochef ──────────────────────────────────────────────────────────────────


class TestAutochef:
    """refs/robot/27_autobar.md — Autochef, 3 slots in all qualities."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_cost',
        [
            ('basic', 9, 500.0),
            ('improved', 10, 2000.0),
            ('enhanced', 11, 5000.0),
            ('advanced', 12, 10000.0),
        ],
    )
    def test_table_values(self, quality, expected_tl, expected_cost):
        opt = Autochef(quality=quality)
        assert opt.tl == expected_tl
        assert opt.cost == expected_cost
        assert opt.slots == 3

    def test_label(self):
        opt = Autochef(quality='basic')
        opt.bind(_robot(tl=9))
        assert opt.notes.item_message == 'Autochef (basic)'

    def test_no_skill_grants(self):
        assert Autochef().skill_grants == ()


# ── StylistToolkit ────────────────────────────────────────────────────────────


class TestStylistToolkit:
    """refs/robot/32_fire_extinguisher.md — Stylist Toolkit, TL6, 3 slots, Cr2000."""

    def test_tl(self):
        assert StylistToolkit().tl == 6

    def test_slots(self):
        assert StylistToolkit().slots == 3

    def test_cost(self):
        assert StylistToolkit().cost == 2000.0

    def test_label(self):
        opt = StylistToolkit()
        opt.bind(_robot())
        assert opt.notes.item_message == 'Stylist Toolkit'

    def test_no_skill_grants(self):
        assert StylistToolkit().skill_grants == ()


# ── AvatarController ──────────────────────────────────────────────────────────


class TestAvatarController:
    """refs/robot/42_avatars.md — Avatar Controller table."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_slots, expected_cost',
        [
            ('basic', 11, 2, 50_000.0),
            ('improved', 13, 1, 200_000.0),
            ('enhanced', 14, 1, 500_000.0),
            ('advanced', 16, 1, 1_000_000.0),
        ],
    )
    def test_table_values(self, quality, expected_tl, expected_slots, expected_cost):
        opt = AvatarController(quality=quality)
        assert opt.tl == expected_tl
        assert opt.slots == expected_slots
        assert opt.cost == expected_cost

    def test_label(self):
        opt = AvatarController(quality='enhanced')
        opt.bind(_robot(tl=14))
        assert opt.notes.item_message == 'Avatar Controller (enhanced)'


# ── SwarmController ───────────────────────────────────────────────────────────


class TestSwarmController:
    """refs/robot/23_satellite_uplink.md — Swarm Controller table."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_slots, expected_cost',
        [
            ('basic', 8, 3, 10_000.0),
            ('improved', 10, 2, 20_000.0),
            ('enhanced', 12, 1, 50_000.0),
            ('advanced', 14, 1, 100_000.0),
        ],
    )
    def test_table_values(self, quality, expected_tl, expected_slots, expected_cost):
        opt = SwarmController(quality=quality)
        assert opt.tl == expected_tl
        assert opt.slots == expected_slots
        assert opt.cost == expected_cost

    def test_label(self):
        opt = SwarmController(quality='enhanced')
        opt.bind(_robot(tl=12))
        assert opt.notes.item_message == 'Swarm Controller (enhanced)'


# ── VehicleSpeedModification ──────────────────────────────────────────────────


class TestVehicleSpeedModification:
    """refs/robot/08_locomotion_modifications.md — slots = ceil(25% base), cost = BCC."""

    @pytest.mark.parametrize(
        'size, expected_slots',
        [
            (RobotSize.SIZE_1, 1),  # ceil(0.25 × 1) = 1
            (RobotSize.SIZE_3, 1),  # ceil(0.25 × 4) = 1
            (RobotSize.SIZE_4, 2),  # ceil(0.25 × 8) = 2
            (RobotSize.SIZE_5, 4),  # ceil(0.25 × 16) = 4
        ],
    )
    def test_slots_by_size(self, size, expected_slots):
        robot = _robot(size=size)
        opt = VehicleSpeedModification()
        opt.bind(robot)
        assert opt.slots == expected_slots

    def test_cost_equals_bcc(self):
        # SIZE_3 × Wheels (multiplier 2.0): BCC = 400 × 2.0 = 800
        robot = _robot(size=RobotSize.SIZE_3)
        opt = VehicleSpeedModification()
        opt.bind(robot)
        assert opt.cost == 800.0

    def test_with_grav_locomotion_has_flyer_high_trait(self):
        robot = Robot(
            name='T',
            tl=12,
            size=RobotSize.SIZE_3,
            locomotion=GravLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        opt = robot.options[-1]
        traits = opt.robot_traits
        assert any(t.name == 'Flyer' and t.value == 'high' for t in traits)

    def test_without_grav_locomotion_no_extra_traits(self):
        robot = _robot(options=[VehicleSpeedModification()])
        opt = robot.options[-1]
        assert opt.robot_traits == ()

    def test_build_item_returns_none(self):
        # VehicleSpeedModification is a locomotion mod — not listed in options display
        robot = _robot(options=[VehicleSpeedModification()])
        opt = robot.options[-1]
        assert opt.build_item() is None


# ── StorageCompartment extended ───────────────────────────────────────────────


class TestStorageCompartmentExtended:
    """Additional StorageCompartment tests not covered in the basic class."""

    def test_refrigerated_type_cost(self):
        opt = StorageCompartment(slots_count=2, storage_type='refrigerated')
        assert opt.cost == 200.0  # 2 × Cr100

    def test_hazardous_type_cost(self):
        opt = StorageCompartment(slots_count=1, storage_type='hazardous')
        assert opt.cost == 500.0  # 1 × Cr500

    def test_hazardous_label(self):
        robot = _robot()
        opt = StorageCompartment(slots_count=2, storage_type='hazardous')
        opt.bind(robot)
        assert opt.notes.item_message == 'Storage Compartment (2 Slots hazardous material)'

    def test_refrigerated_label(self):
        robot = _robot()
        opt = StorageCompartment(slots_count=3, storage_type='refrigerated')
        opt.bind(robot)
        assert opt.notes.item_message == 'Storage Compartment (3 Slots refrigerated)'
