# Source: user-supplied stat block
#
# Brain: SelfAwareBrain TL15, bandwidth upgraded to 20 (base 10 + delta 10),
#   hardened=True. Hardware cost = (1,000,000 + 500,000) × 1.5 = 2,250,000.
#
# Bandwidth reconciliation:
#   Non-zero BW packages (8): Recon(2)+Stealth(1)+Investigate(3)+Broker(3)
#     +Admin(1)+Advocate(1)+Medic(2)+Science(2) = 15 BW used.
#   Universal Translator (software): 3 BW. Total used = 15 + 3 = 18.
#   Zero-BW packages (8): Electronics, Engineer, Mechanic, Steward, Language,
#     Tactics, Flyer, Navigation — within base-BW quota of 10 (all free).
#   Ceres remaining_bandwidth: 20 − 18 = 2.
#   Source shows "2 Bandwidth Remaining". Both agree (different accounting paths
#   that happen to converge: source=zero-BW quota remaining=10−8=2;
#   Ceres=total BW − used non-zero BW=20−18=2).
#
# Skill DM: SelfAwareBrain INT 12 → INT DM+2 for INT skills; DEX DM+1 for DEX
#   skills (robot TL15: DEX=ceil(15/2)+1=9 → DM+1).
#   Source shows Stealth 1+DEX DM+1=Stealth 2, superseded by CamouflageVisual(adv)
#   Stealth 4. Flyer (Grav) 0+DEX DM+1=Flyer (All) 1.
#
# SIZE_1 + NoneLocomotion: base available = ceil(1 × 1.25) = 2 slots.
# No manipulators: _manipulator_slot_effect = 0 − 2×std_slots(1) = −2, so
#   available_slots gains 2 → total available = 4.
# SelfAwareBrain(hardened, TL15) in SIZE_1: base brain_slots = 1 (min_free=10,
#   size=1 < 10). BW upgrade (delta>0): +1 slot → brain_slots = 2.
#   AvatarController(enhanced) = 1 slot. SwarmController(advanced) = 1 slot.
#   Total used = 4. Remaining = 4−4 = 0. Source: used=4, remaining=0. ✓
#
# Zero-slot count: 5 (default suite) + 15 extras = 20 < quota(5+1+15=21). ✓
#
# Endurance: NoneLocomotion base 216h × TL15 ×2.0 × SME(improved) ×2.0 = 864h. ✓
# Traits: Armour(+4) TL15, Small(−4) SIZE_1, Hardened (brain), Heightened
#   Senses (EnvironmentProcessor), IR/UV Vision (PrisSensor). ✓
# Cost: not asserted — partial reconciliation of hardware options cost.

from types import SimpleNamespace

from ceres.make.robot import (
    NoneLocomotion,
    Robot,
    RobotSize,
    SelfAwareBrain,
    UniversalTranslator,
    default_suite,
)
from ceres.make.robot.options import (
    AvatarController,
    CamouflageAudible,
    CamouflageVisual,
    EncryptionModule,
    EnvironmentProcessor,
    InjectorNeedle,
    ParasiticLink,
    PrisSensor,
    SelfMaintenanceEnhancement,
    SwarmController,
    VacuumEnvironmentProtection,
)
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits
from tests.robots import skill_packages as sp

_expected = SimpleNamespace(
    hits=1,
    locomotion='None',
    speed='0m',
    tl=15,
    base_armour=4,
    traits='Armour (+4), Hardened, Heightened Senses, IR/UV Vision, Small (-4)',
    programming='Self-Aware (INT 12)',
    endurance_hours=864,
    attacks='—',
    manipulators='—',
    available_slots=4,  # Ceres: ceil(1×1.25)+2(no-arm bonus)=4
    used_slots=4,  # brain(2)+AvatarController(1)+SwarmController(1)=4; matches source
    remaining_slots=0,  # 4−4=0; matches source
    remaining_bandwidth=2,  # 20−15(skills)−3(UT)=2; matches source
)


def build_mimer() -> Robot:
    return Robot(
        name='Mimer',
        tl=15,
        size=RobotSize.SIZE_1,
        locomotion=NoneLocomotion(),
        brain=SelfAwareBrain(
            hardened=True,
            bandwidth=20,
            installed_software=(UniversalTranslator(),),
            installed_skills=(
                sp.recon(level=2, bandwidth=2),
                sp.stealth(level=1, bandwidth=1),
                sp.investigate(level=2, bandwidth=3),
                sp.electronics_remote_ops(level=0, bandwidth=0),
                sp.broker(level=3, bandwidth=3),
                sp.admin(level=1, bandwidth=1),
                sp.advocate(level=1, bandwidth=1),
                sp.engineer_j_drive(level=0, bandwidth=0),
                sp.mechanic(level=0, bandwidth=0),
                sp.medic(level=2, bandwidth=2),
                sp.steward(level=0, bandwidth=0),
                sp.science_robotics(level=2, bandwidth=2),
                sp.language_vilani(level=0, bandwidth=0),
                sp.tactics_military(level=0, bandwidth=0),
                sp.flyer_grav(level=0, bandwidth=0),
                sp.navigation(level=0, bandwidth=0),
            ),
        ),
        manipulators=[],
        options=[
            *default_suite(),
            AvatarController(quality='enhanced'),
            SwarmController(quality='advanced'),
            CamouflageAudible(quality='advanced'),
            CamouflageVisual(quality='advanced'),
            EncryptionModule(),
            EnvironmentProcessor(),
            *[InjectorNeedle() for _ in range(7)],
            ParasiticLink(),
            PrisSensor(),
            SelfMaintenanceEnhancement(quality='improved'),
            VacuumEnvironmentProtection(),
        ],
    )


class TestMimer:
    def test_hits(self):
        assert build_mimer().hits == _expected.hits

    def test_base_armour(self):
        assert build_mimer().base_armour == _expected.base_armour

    def test_traits(self):
        assert format_traits(build_mimer().traits) == _expected.traits

    def test_programming(self):
        assert build_mimer().brain.programming_label() == _expected.programming

    def test_endurance(self):
        assert int(build_mimer().base_endurance) == _expected.endurance_hours

    def test_locomotion_label(self):
        assert build_mimer().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_mimer().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_mimer().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_mimer().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_mimer().remaining_slots == _expected.remaining_slots

    def test_remaining_bandwidth(self):
        assert build_mimer().brain.remaining_bandwidth == _expected.remaining_bandwidth

    def test_hardened_trait_in_traits(self):
        robot = build_mimer()
        assert any(t.name == 'Hardened' for t in robot.traits)

    def test_heightened_senses_trait_in_traits(self):
        robot = build_mimer()
        assert any(t.name == 'Heightened Senses' for t in robot.traits)

    def test_ir_uv_vision_trait_in_traits(self):
        robot = build_mimer()
        assert any(t.name == 'IR/UV Vision' for t in robot.traits)

    def test_spec_attacks_row(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == _expected.manipulators

    def test_skills_admin_3(self):
        # Admin level 1 + brain DM+2 = Admin 3
        assert 'Admin 3' in build_mimer().skills_display

    def test_skills_advocate_3(self):
        # Advocate level 1 + brain DM+2 = Advocate 3
        assert 'Advocate 3' in build_mimer().skills_display

    def test_skills_broker_5(self):
        # Broker level 3 + brain DM+2 = Broker 5
        assert 'Broker 5' in build_mimer().skills_display

    def test_skills_investigate_4(self):
        # Investigate level 2 + brain DM+2 = Investigate 4
        assert 'Investigate 4' in build_mimer().skills_display

    def test_skills_recon_4(self):
        # Recon level 2 + brain DM+2 = Recon 4
        assert 'Recon 4' in build_mimer().skills_display

    def test_skills_medic_4(self):
        # Medic level 2 + brain DM+2 = Medic 4
        assert 'Medic 4' in build_mimer().skills_display

    def test_skills_science_robotics_4(self):
        # TCR-001 maps Science (Robotics) to Robotic Science (Robotics).
        assert 'Robotic Science (Robotics) 4' in build_mimer().skills_display

    def test_skills_stealth_4(self):
        # CamouflageVisual(advanced): detection DM −4 → Stealth 4 from hardware
        assert 'Stealth 4' in build_mimer().skills_display

    def test_skills_recon_0_superseded_by_package(self):
        # EnvironmentProcessor grants Recon 0 but Recon package (level 2 + DM 2 = 4)
        # supersedes it — only Recon 4 appears
        display = build_mimer().skills_display
        assert 'Recon 4' in display
        assert 'Recon 0' not in display

    def test_skills_stealth_4_supersedes_package(self):
        # Stealth package level 1 + DEX DM+1 = Stealth 2; CamouflageVisual gives Stealth 4
        # Only the higher level (Stealth 4) should appear
        display = build_mimer().skills_display
        assert 'Stealth 4' in display
        assert 'Stealth 2' not in display

    def test_spec_skills_detail_section_present(self):
        # SelfAwareBrain should produce a skills detail section like AdvancedBrain does
        spec = build_mimer().build_spec()
        titles = [s.title for s in spec.detail_sections]
        assert 'Skills' in titles

    def test_skills_electronics_all_2(self):
        # Electronics (Remote Ops) level 0 + DM+2: unspecialized → (All) 2
        assert 'Electronics (All) 2' in build_mimer().skills_display

    def test_skills_engineer_all_2(self):
        # Engineer (J-Drive) level 0 + DM+2: unspecialized → (All) 2
        assert 'Engineer (All) 2' in build_mimer().skills_display

    def test_skills_flyer_all_1(self):
        # Flyer (Grav) level 0 + DEX DM+1 (TL15: DEX=9 → DM+1): unspecialized → (All) 1
        assert 'Flyer (All) 1' in build_mimer().skills_display

    def test_skills_tactics_all_2(self):
        # Tactics (Military) level 0 + DM+2: unspecialized → (All) 2
        assert 'Tactics (All) 2' in build_mimer().skills_display

    def test_skills_language_all_2(self):
        # TCR-001 maps Language (Vilani) to the concrete Language Vilani skill.
        assert 'Language Vilani 2' in build_mimer().skills_display

    def test_skills_remaining_bandwidth_shown(self):
        # 20 − 15(skill BW) − 3(Universal Translator BW) = 2
        assert '+2 Bandwidth available' in build_mimer().skills_display

    def test_spec_options_has_avatar_controller(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Avatar Controller (enhanced)' in value

    def test_spec_options_has_encryption_module(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Encryption Module' in value

    def test_spec_options_has_pris_sensor(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'PRIS Sensor' in value

    def test_spec_options_has_self_maintenance_enhancement(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Self-Maintenance Enhancement (improved)' in value

    def test_spec_options_has_environment_processor(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Environment Processor' in value

    def test_spec_options_has_injector_needles(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Injector Needle × 7' in value

    def test_spec_options_has_vacuum_environment_protection(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Vacuum Environment Protection' in value

    def test_spec_options_has_camouflage_audible(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Camouflage: Audible (advanced)' in value

    def test_spec_options_has_camouflage_visual(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Camouflage: Visual (advanced)' in value

    def test_spec_options_has_parasitic_link(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Parasitic Link' in value

    def test_spec_options_has_swarm_controller(self):
        spec = build_mimer().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Swarm Controller (advanced)' in value

    def test_json_roundtrip(self):
        robot = build_mimer()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Mimer'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_1
        assert isinstance(restored.locomotion, NoneLocomotion)
        assert isinstance(restored.brain, SelfAwareBrain)
        assert restored.brain.hardened is True
        assert restored.brain.bandwidth == 20
        assert len(restored.brain.installed_skills) == 16
        assert len(restored.brain.installed_software) == 1
        assert restored.brain.installed_software[0].name == 'Universal Translator'
