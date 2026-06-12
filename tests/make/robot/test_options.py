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
    AquaticLocomotion,
    GravLocomotion,
    HovercraftLocomotion,
    PrimitiveBrain,
    Robot,
    RobotSize,
    ThrusterLocomotion,
    TracksLocomotion,
    VtolLocomotion,
    WalkerLocomotion,
    WheelsLocomotion,
)
from ceres.make.robot.options import (
    AgilityEnhancement,
    AgriculturalEquipment,
    Autobar,
    Autochef,
    AvatarController,
    BioscanneSensor,
    CamouflageAudible,
    CamouflageOlfactory,
    CamouflageVisual,
    DecreasedResiliency,
    DensitometerSensor,
    DomesticCleaningEquipment,
    Efficiency,
    EncryptionModule,
    EnvironmentProcessor,
    ExternalPower,
    FabricationChamber,
    GeckoGrippers,
    IncreasedArmour,
    InjectorNeedle,
    LightIntensifierSensor,
    MedicalChamber,
    Medikit,
    NavigationSystem,
    NeuralActivitySensor,
    OlfactorySensor,
    ParasiticLink,
    PrisSensor,
    RadiationEnvironmentProtection,
    ReconSensor,
    RoboticDroneController,
    ScientificToolkit,
    SecondaryLocomotion,
    SelfMaintenanceEnhancement,
    SolarCoating,
    StorageCompartment,
    StylistToolkit,
    SwarmController,
    ThermalSensor,
    VacuumEnvironmentProtection,
    VehicleSpeedModification,
)


def _robot(size=RobotSize.SIZE_3, tl=8, locomotion=None, options=None) -> Robot:
    kwargs: dict = {
        'name': 'T',
        'tl': tl,
        'size': size,
        'locomotion': locomotion or WheelsLocomotion(),
        'brain': PrimitiveBrain(),
    }
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
        assert opt.skill_grants == {'Recon': expected_level}

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
        assert opt.skill_grants == {'Recon': 1}


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
        assert EnvironmentProcessor().skill_grants == {'Recon': 0}

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
        assert ParasiticLink().skill_grants == {}


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
        assert opt.skill_grants == {'Stealth': expected_stealth_level}

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
        assert CamouflageAudible().skill_grants == {}


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
        assert NavigationSystem(quality='basic').skill_grants == {'Navigation': 1}

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
        assert Autochef().skill_grants == {}


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
        assert StylistToolkit().skill_grants == {}


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

    def test_with_vtol_locomotion_has_flyer_medium_trait(self):
        # refs/robot/08_locomotion_modifications.md — VTOL → Medium
        robot = Robot(
            name='T',
            tl=10,
            size=RobotSize.SIZE_3,
            locomotion=VtolLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        opt = robot.options[-1]
        traits = opt.robot_traits
        assert any(t.name == 'Flyer' and t.value == 'medium' for t in traits)

    def test_wheels_vsm_speed_label_slow(self):
        # refs/robot/08_locomotion_modifications.md — Wheels → Slow
        robot = Robot(
            name='T',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        assert robot.speed_label == '5m (slow)'

    def test_tracks_vsm_speed_label_very_slow(self):
        # refs/robot/08_locomotion_modifications.md — Tracks → Very Slow; 5−1=4m tactical
        robot = Robot(
            name='T',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=TracksLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        assert robot.speed_label == '4m (very slow)'

    def test_aquatic_vsm_speed_label_very_slow(self):
        # refs/robot/08_locomotion_modifications.md — Aquatic → Very Slow; 5−2=3m tactical
        robot = Robot(
            name='T',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=AquaticLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        assert robot.speed_label == '3m (very slow)'

    def test_vtol_vsm_speed_label_medium(self):
        # refs/robot/08_locomotion_modifications.md — VTOL → Medium; 5+0=5m tactical
        robot = Robot(
            name='T',
            tl=10,
            size=RobotSize.SIZE_3,
            locomotion=VtolLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        assert robot.speed_label == '5m (medium)'

    def test_walker_vsm_speed_label_very_slow(self):
        # refs/robot/08_locomotion_modifications.md — Walker → Very Slow; 5+0=5m tactical
        robot = Robot(
            name='T',
            tl=10,
            size=RobotSize.SIZE_3,
            locomotion=WalkerLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        assert robot.speed_label == '5m (very slow)'

    def test_hovercraft_vsm_speed_label_medium(self):
        # refs/robot/08_locomotion_modifications.md — Hovercraft → Medium; 5+1=6m tactical
        robot = Robot(
            name='T',
            tl=10,
            size=RobotSize.SIZE_3,
            locomotion=HovercraftLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        assert robot.speed_label == '6m (medium)'

    def test_thruster_vsm_speed_label_shows_thrust(self):
        # refs/robot/08_locomotion_modifications.md — Thruster → shows thrust e.g. '0.1G'
        robot = Robot(
            name='T',
            tl=10,
            size=RobotSize.SIZE_3,
            locomotion=ThrusterLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        assert robot.speed_label == '0.1G'

    def test_vtol_vsm_replaces_flyer_idle_with_flyer_medium(self):
        # refs/robot/08_locomotion_modifications.md — VTOL+VSM: Flyer(medium) not Flyer(idle)
        robot = Robot(
            name='T',
            tl=10,
            size=RobotSize.SIZE_3,
            locomotion=VtolLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        trait_strs = [str(t) for t in robot.traits]
        assert 'Flyer (medium)' in trait_strs
        assert 'Flyer (idle)' not in trait_strs

    def test_hovercraft_vsm_no_flyer_trait(self):
        # Hovercraft has ACV, not Flyer — VSM adds no Flyer trait
        robot = Robot(
            name='T',
            tl=10,
            size=RobotSize.SIZE_3,
            locomotion=HovercraftLocomotion(),
            brain=PrimitiveBrain(),
            options=[VehicleSpeedModification()],
        )
        trait_names = [t.name for t in robot.traits]
        assert 'Flyer' not in trait_names


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


# ── BioscanneSensor ───────────────────────────────────────────────────────────


class TestBioscanneSensor:
    """refs/robot/30_no_internal_power.md — Bioscanner Sensor, TL15, 2 slots, Cr350000."""

    def test_tl(self):
        assert BioscanneSensor().tl == 15

    def test_slots(self):
        assert BioscanneSensor().slots == 2

    def test_cost(self):
        assert BioscanneSensor().cost == 350000.0

    def test_label(self):
        opt = BioscanneSensor()
        opt.bind(_robot(tl=15))
        assert opt.notes.item_message == 'Bioscanner Sensor'


# ── DensitometerSensor ────────────────────────────────────────────────────────


class TestDensitometerSensor:
    """refs/robot/30_no_internal_power.md — Densitometer Sensor, TL14, 3 slots, Cr20000."""

    def test_tl(self):
        assert DensitometerSensor().tl == 14

    def test_slots(self):
        assert DensitometerSensor().slots == 3

    def test_cost(self):
        assert DensitometerSensor().cost == 20000.0

    def test_label(self):
        opt = DensitometerSensor()
        opt.bind(_robot(tl=14))
        assert opt.notes.item_message == 'Densitometer Sensor'


# ── NeuralActivitySensor ──────────────────────────────────────────────────────


class TestNeuralActivitySensor:
    """refs/robot/31_neural_activity_sensor.md — Neural Activity Sensor, TL15, 5 slots, Cr35000."""

    def test_tl(self):
        assert NeuralActivitySensor().tl == 15

    def test_slots(self):
        assert NeuralActivitySensor().slots == 5

    def test_cost(self):
        assert NeuralActivitySensor().cost == 35000.0

    def test_label(self):
        opt = NeuralActivitySensor()
        opt.bind(_robot(tl=15))
        assert opt.notes.item_message == 'Neural Activity Sensor'


# ── Medikit ───────────────────────────────────────────────────────────────────


class TestMediakit:
    """refs/robot/26_medikit.md — Medikit, 1 slot, quality-based TL and cost."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_cost',
        [
            ('basic', 8, 1000.0),
            ('improved', 10, 1500.0),
            ('enhanced', 12, 5000.0),
            ('advanced', 14, 10000.0),
        ],
    )
    def test_table_values(self, quality, expected_tl, expected_cost):
        opt = Medikit(quality=quality)
        assert opt.tl == expected_tl
        assert opt.cost == expected_cost

    def test_slots_always_one(self):
        for quality in ('basic', 'improved', 'enhanced', 'advanced'):
            assert Medikit(quality=quality).slots == 1

    def test_label_includes_quality(self):
        opt = Medikit(quality='advanced')
        opt.bind(_robot(tl=14))
        assert opt.notes.item_message == 'Medikit (advanced)'

    def test_label_basic(self):
        opt = Medikit(quality='basic')
        opt.bind(_robot(tl=8))
        assert opt.notes.item_message == 'Medikit (basic)'


# ── SolarCoating ──────────────────────────────────────────────────────────────


class TestSolarCoating:
    """refs/robot/13_solar_coating.md — zero-slot, cost = cost_per_base_slot × base_slots."""

    def test_slots_is_zero(self):
        assert SolarCoating().slots == 0

    @pytest.mark.parametrize(
        'quality, expected_tl',
        [
            ('basic', 6),
            ('improved', 8),
            ('enhanced', 10),
            ('advanced', 12),
        ],
    )
    def test_tl_by_quality(self, quality, expected_tl):
        assert SolarCoating(quality=quality).tl == expected_tl

    def test_cost_basic_size3(self):
        # SIZE_3 base_slots=4; basic cost_per_base_slot=500 → 2000
        opt = SolarCoating(quality='basic')
        opt.bind(_robot(size=RobotSize.SIZE_3))
        assert opt.cost == 2000.0

    def test_cost_advanced_size3(self):
        # SIZE_3 base_slots=4; advanced cost_per_base_slot=500 → 2000
        opt = SolarCoating(quality='advanced')
        opt.bind(_robot(size=RobotSize.SIZE_3))
        assert opt.cost == 2000.0

    def test_cost_improved_size5(self):
        # SIZE_5 base_slots=16; improved cost_per_base_slot=100 → 1600
        opt = SolarCoating(quality='improved')
        opt.bind(_robot(size=RobotSize.SIZE_5, tl=8))
        assert opt.cost == 1600.0

    def test_label_includes_quality(self):
        opt = SolarCoating(quality='advanced')
        opt.bind(_robot(tl=12))
        assert opt.notes.item_message == 'Solar Coating (advanced)'


# ── ScientificToolkit ─────────────────────────────────────────────────────────


class TestScientificToolkit:
    """refs/robot/32_fire_extinguisher.md — Scientific Toolkit, quality-based."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_slots, expected_cost',
        [
            ('basic', 5, 4, 2000.0),
            ('improved', 8, 3, 4000.0),
            ('enhanced', 11, 3, 6000.0),
            ('advanced', 14, 3, 8000.0),
        ],
    )
    def test_table_values(self, quality, expected_tl, expected_slots, expected_cost):
        opt = ScientificToolkit(quality=quality)
        assert opt.tl == expected_tl
        assert opt.slots == expected_slots
        assert opt.cost == expected_cost

    def test_label_without_speciality(self):
        opt = ScientificToolkit(quality='advanced')
        opt.bind(_robot(tl=14))
        assert opt.notes.item_message == 'Scientific Toolkit (advanced)'

    def test_label_with_speciality(self):
        opt = ScientificToolkit(quality='advanced', speciality='biology')
        opt.bind(_robot(tl=14))
        assert opt.notes.item_message == 'Scientific Toolkit (advanced, biology)'


# ── FabricationChamber ────────────────────────────────────────────────────────


class TestFabricationChamber:
    """refs/robot/28_fabrication_chamber.md — slots = slots_count, cost = slots × rate."""

    @pytest.mark.parametrize(
        'quality, expected_tl, expected_rate',
        [
            ('basic', 8, 2000.0),
            ('improved', 10, 10000.0),
            ('enhanced', 13, 50000.0),
            ('advanced', 17, 200000.0),
        ],
    )
    def test_tl_by_quality(self, quality, expected_tl, expected_rate):
        opt = FabricationChamber(quality=quality, slots_count=1)
        assert opt.tl == expected_tl
        assert opt.cost == expected_rate

    def test_slots_equals_slots_count(self):
        assert FabricationChamber(quality='basic', slots_count=10).slots == 10

    def test_cost_scales_with_slots_count(self):
        # enhanced: Cr50000/slot × 4 = Cr200000
        opt = FabricationChamber(quality='enhanced', slots_count=4)
        assert opt.cost == 200000.0

    def test_label(self):
        opt = FabricationChamber(quality='enhanced', slots_count=64)
        opt.bind(_robot(tl=13))
        assert opt.notes.item_message == 'Fabrication Chamber (enhanced, 64 Slots)'


# ── MedicalChamber ────────────────────────────────────────────────────────────


class TestMedicalChamber:
    """refs/robot/24_tightbeam_communicator.md — Medical Chamber, slots and cost with sub-options."""

    def test_default_tl(self):
        assert MedicalChamber().tl == 8

    def test_default_slots(self):
        assert MedicalChamber(slots_count=32).slots == 32

    def test_default_cost(self):
        # 32 × Cr200 = Cr6400
        assert MedicalChamber(slots_count=32).cost == 6400.0

    def test_basic_low_berth_adds_slots(self):
        # 32 base + 8 low_berth = 40
        opt = MedicalChamber(slots_count=32, low_berth='basic')
        assert opt.slots == 40

    def test_improved_low_berth_adds_slots(self):
        opt = MedicalChamber(slots_count=32, low_berth='improved')
        assert opt.slots == 40

    def test_reanimation_adds_slots(self):
        opt = MedicalChamber(slots_count=32, reanimation=True)
        assert opt.slots == 40

    def test_species_specific_adds_four_slots_each(self):
        opt = MedicalChamber(slots_count=32, species_specific=2)
        assert opt.slots == 40

    def test_all_sub_options_stack(self):
        # 20 + 8(low_berth) + 8(reanimation) + 4(species_specific×1) = 40
        opt = MedicalChamber(slots_count=20, low_berth='improved', reanimation=True, species_specific=1)
        assert opt.slots == 40

    def test_tl_raised_by_low_berth_improved(self):
        assert MedicalChamber(slots_count=32, low_berth='improved').tl == 12

    def test_tl_raised_by_reanimation(self):
        assert MedicalChamber(slots_count=32, reanimation=True).tl == 14

    def test_tl_raised_by_species_specific(self):
        assert MedicalChamber(slots_count=32, species_specific=1).tl == 10

    def test_cost_with_low_berth_improved(self):
        # 20 × Cr200 + Cr20000 = Cr24000
        opt = MedicalChamber(slots_count=20, low_berth='improved')
        assert opt.cost == 24000.0

    def test_cost_with_reanimation(self):
        # 20 × Cr200 + Cr900000 = Cr904000
        opt = MedicalChamber(slots_count=20, reanimation=True)
        assert opt.cost == 904000.0

    def test_cost_with_species_specific(self):
        # 20 × Cr200 + Cr10000 = Cr14000
        opt = MedicalChamber(slots_count=20, species_specific=1)
        assert opt.cost == 14000.0

    def test_label_base_only(self):
        opt = MedicalChamber(slots_count=32)
        opt.bind(_robot(tl=8))
        assert opt.notes.item_message == 'Medical Chamber (32 Slots)'

    def test_label_with_improved_low_berth(self):
        opt = MedicalChamber(slots_count=20, low_berth='improved')
        opt.bind(_robot(tl=12))
        assert opt.notes.item_message == 'Medical Chamber (28 Slots, Improved Low Berth)'

    def test_label_all_sub_options(self):
        opt = MedicalChamber(slots_count=20, low_berth='improved', reanimation=True, species_specific=1)
        opt.bind(_robot(tl=14))
        assert opt.notes.item_message == (
            'Medical Chamber (40 Slots, Improved Low Berth, Reanimation, Species-Specific Add-on)'
        )

    def test_label_species_specific_plural(self):
        opt = MedicalChamber(slots_count=20, species_specific=2)
        opt.bind(_robot(tl=10))
        assert opt.notes.item_message == 'Medical Chamber (28 Slots, Species-Specific Add-on ×2)'


# ──────────────────────────────────────────────────────
# Autobar
# ──────────────────────────────────────────────────────


class TestAutobar:
    """refs/robot/27_autobar.md — 2 slots always, TL8-11."""

    def test_slots_basic(self):
        assert Autobar(quality='basic').slots == 2

    def test_slots_advanced(self):
        assert Autobar(quality='advanced').slots == 2

    def test_cost_basic(self):
        assert Autobar(quality='basic').cost == 500.0

    def test_cost_improved(self):
        assert Autobar(quality='improved').cost == 1000.0

    def test_cost_enhanced(self):
        assert Autobar(quality='enhanced').cost == 2000.0

    def test_cost_advanced(self):
        assert Autobar(quality='advanced').cost == 5000.0

    def test_tl_basic(self):
        assert Autobar(quality='basic').tl == 8

    def test_tl_advanced(self):
        assert Autobar(quality='advanced').tl == 11

    def test_label(self):
        opt = Autobar(quality='enhanced')
        opt.bind(_robot())
        assert opt.notes.item_message == 'Autobar (enhanced)'


# ──────────────────────────────────────────────────────
# IncreasedArmour
# ──────────────────────────────────────────────────────


class TestIncreasedArmour:
    """refs/robot/07_chassis_options.md — Robot Armour table."""

    def test_armour_delta(self):
        assert IncreasedArmour(additional=4).armour_delta == 4

    def test_slots_tl15_size4_plus4(self):
        # TL15-17: 0.3% slots, max 4/slot. SIZE_4 base=8.
        # max(ceil(4×0.003×8)=ceil(0.096)=1, ceil(4/4)=1, 1) = 1
        opt = IncreasedArmour(additional=4)
        opt.bind(_robot(size=RobotSize.SIZE_4, tl=15))
        assert opt.slots == 1

    def test_cost_tl15_size4_plus4(self):
        # 1 slot × Cr2500 = Cr2500
        opt = IncreasedArmour(additional=4)
        opt.bind(_robot(size=RobotSize.SIZE_4, tl=15))
        assert opt.cost == 2500.0

    def test_slots_tl14_size5_plus6(self):
        # TL12-14: 0.4% slots, max 3/slot. SIZE_5 base=16.
        # max(ceil(6×0.004×16)=ceil(0.384)=1, ceil(6/3)=2, 1) = 2
        opt = IncreasedArmour(additional=6)
        opt.bind(_robot(size=RobotSize.SIZE_5, tl=14))
        assert opt.slots == 2

    def test_cost_tl14_size5_plus6(self):
        # 2 slots × Cr1500 = Cr3000
        opt = IncreasedArmour(additional=6)
        opt.bind(_robot(size=RobotSize.SIZE_5, tl=14))
        assert opt.cost == 3000.0

    def test_slots_tl8_size3_plus1(self):
        # TL6-8: 1% slots, max 1/slot. SIZE_3 base=4.
        # max(ceil(1×0.01×4)=1, ceil(1/1)=1, 1) = 1
        opt = IncreasedArmour(additional=1)
        opt.bind(_robot(size=RobotSize.SIZE_3, tl=8))
        assert opt.slots == 1

    def test_robot_total_armour_trait(self):
        # TL15 base=4 + IncreasedArmour(+4) = 8
        robot = _robot(size=RobotSize.SIZE_4, tl=15, options=[IncreasedArmour(additional=4)])
        armour_traits = [t for t in robot.traits if t.name == 'Armour']
        assert len(armour_traits) == 1
        assert armour_traits[0].value == '+8'


# ──────────────────────────────────────────────────────
# AgilityEnhancement
# ──────────────────────────────────────────────────────


class TestAgilityEnhancement:
    """refs/robot/08_locomotion_modifications.md — Agility Enhancement."""

    def test_speed_bonus(self):
        assert AgilityEnhancement(level=2).speed_bonus == 2

    def test_skill_grant(self):
        assert AgilityEnhancement(level=2).skill_grants == {'Athletics (Dexterity)': 2}

    def test_cost_level_1(self):
        # 100% BCC; SIZE_3 WheelsLocomotion BCC = 400×2 = 800
        opt = AgilityEnhancement(level=1)
        opt.bind(_robot(size=RobotSize.SIZE_3))
        assert opt.cost == 800.0

    def test_cost_level_2(self):
        # 200% BCC; SIZE_3 WheelsLocomotion BCC = 800
        opt = AgilityEnhancement(level=2)
        opt.bind(_robot(size=RobotSize.SIZE_3))
        assert opt.cost == 1600.0

    def test_cost_level_3(self):
        # 400% BCC
        opt = AgilityEnhancement(level=3)
        opt.bind(_robot(size=RobotSize.SIZE_3))
        assert opt.cost == 3200.0

    def test_cost_level_4(self):
        # 800% BCC
        opt = AgilityEnhancement(level=4)
        opt.bind(_robot(size=RobotSize.SIZE_3))
        assert opt.cost == 6400.0

    def test_speed_label_updated(self):
        # WheelsLocomotion base speed 5m + AgilityEnhancement(+2) = 7m
        robot = _robot(size=RobotSize.SIZE_3, options=[AgilityEnhancement(level=2)])
        assert robot.speed_label == '7m'


# ──────────────────────────────────────────────────────
# Efficiency
# ──────────────────────────────────────────────────────


class TestEfficiency:
    """refs/robot/07_chassis_options.md — Efficiency doubles endurance, costs 50% BCC."""

    def test_endurance_multiplier(self):
        assert Efficiency().endurance_multiplier == 2.0

    def test_cost_size3_wheels(self):
        # SIZE_3 WheelsLocomotion BCC = 400×2 = 800; cost = 50% × 800 = 400
        opt = Efficiency()
        opt.bind(_robot(size=RobotSize.SIZE_3))
        assert opt.cost == 400.0

    def test_cost_size5_grav(self):
        # SIZE_5 GravLocomotion BCC = 1000×20 = 20000; cost = 10000
        opt = Efficiency()
        opt.bind(_robot(size=RobotSize.SIZE_5, locomotion=GravLocomotion()))
        assert opt.cost == 10000.0

    def test_label(self):
        opt = Efficiency()
        opt.bind(_robot())
        assert opt.notes.item_message == 'Efficiency'

    def test_tl(self):
        assert Efficiency().tl == 7


# ──────────────────────────────────────────────────────
# RadiationEnvironmentProtection
# ──────────────────────────────────────────────────────


class TestRadiationEnvironmentProtection:
    """refs/robot/20_radiation_environment_protection.md — TL7, 1 slot, Cr600/base_slot."""

    def test_slots(self):
        assert RadiationEnvironmentProtection().slots == 1

    def test_tl(self):
        assert RadiationEnvironmentProtection().tl == 7

    def test_cost_size3(self):
        # SIZE_3 base_slots=4; 4×600=2400
        opt = RadiationEnvironmentProtection()
        opt.bind(_robot(size=RobotSize.SIZE_3))
        assert opt.cost == 2400.0

    def test_cost_size5(self):
        # SIZE_5 base_slots=16; 16×600=9600
        opt = RadiationEnvironmentProtection()
        opt.bind(_robot(size=RobotSize.SIZE_5))
        assert opt.cost == 9600.0

    def test_label(self):
        opt = RadiationEnvironmentProtection()
        opt.bind(_robot())
        assert opt.notes.item_message == 'Radiation Environment Protection'


# ──────────────────────────────────────────────────────
# SecondaryLocomotion
# ──────────────────────────────────────────────────────


class TestSecondaryLocomotion:
    """refs/robot/08_locomotion_modifications.md — Secondary Locomotion."""

    def test_slots_size5(self):
        # SIZE_5 base_slots=16; ceil(0.25×16)=4
        opt = SecondaryLocomotion(locomotion=WalkerLocomotion())
        opt.bind(_robot(size=RobotSize.SIZE_5))
        assert opt.slots == 4

    def test_slots_size4(self):
        # SIZE_4 base_slots=8; ceil(0.25×8)=2
        opt = SecondaryLocomotion(locomotion=WalkerLocomotion())
        opt.bind(_robot(size=RobotSize.SIZE_4))
        assert opt.slots == 2

    def test_cost_walker_size5(self):
        # slots=4; Walker multiplier=10; cost=500×4×10=20000
        opt = SecondaryLocomotion(locomotion=WalkerLocomotion())
        opt.bind(_robot(size=RobotSize.SIZE_5))
        assert opt.cost == 20000.0

    def test_robot_traits_from_walker_secondary(self):
        # Walker locomotion has ATV trait
        robot = _robot(
            size=RobotSize.SIZE_5,
            options=[SecondaryLocomotion(locomotion=WalkerLocomotion())],
        )
        trait_names = [t.name for t in robot.traits]
        assert 'ATV' in trait_names
