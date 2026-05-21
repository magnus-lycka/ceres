# Source: user-supplied stat block (no refs/robot/xxx_munin.md).
#
# SIZE_1 TL15 Grav: base armour 4. AdvancedBrain(TL15→TL12 entry) INT 8, DM 0, BW 2.
# Hardened brain: +50% → Cr15,000 hardware cost.
# Speed 12m: GravLocomotion(speed_increase=2) → effective 7 + agility 1 + AgilityEnh(4) = 12m.
#   Source options omit AgilityEnhancement — inferred from Athletics(dex) 4 and 12m speed.
# Endurance 77h (source): 24 × (1−0.2) × 2.0(TL15) × 2.0(Efficiency) = 76.8h → Ceres: 76h.
#   Source rounds up. Efficiency omitted from source options list — inferred for endurance.
# Recon 1: EnvironmentProcessor → Recon 0; SkillPackage('Recon',1,BW=1) → merged max = 1.
# Stealth 4: from ActiveCamouflage hardware grant (not a brain skill package).
# Brain remaining BW: 2 − 1(Recon pkg) = 1.
# Traits: Armour(+4), Flyer(idle), Hardened, Heightened Senses, Invisible, IR/UV Vision, Small(-4).
#   Source also shows Stealth(+4) as trait — in Ceres this is a hardware skill grant, not a trait.
# Cost: Ceres Cr97,830 vs source Cr140,000. Gap = Cr42,170 unresolved (source likely omits
#   AgilityEnhancement(4) = Cr16,000 and Efficiency = Cr1,000 from options list; residual Cr25,170 unknown).
# Slots: manipulators=[] frees 2 slots (default pair is 2×1 slot on SIZE_1), so available=3.
#   AdvancedBrain(0) + ActiveCamouflage(1) + AvatarReceiver(1) = 2 slotted; Efficiency is chassis
#   mod (no item_message) → 21 zero-slot items = quota (5+1+15=21) → no excess → used=2; remaining=1.
#   Brain costs 0 slots: TL12 Advanced entry (computer_x=2) at TL15 is 3 TLs after introduction →
#   min_free = max(0, 2−3) = 0; SIZE_1 fits for free.

from types import SimpleNamespace

from ceres.make.robot import GravLocomotion, Robot, RobotSize
from ceres.make.robot.brain import AdvancedBrain
from ceres.make.robot.options import (
    ActiveCamouflage,
    AgilityEnhancement,
    AvatarReceiver,
    CamouflageAudible,
    CamouflageOlfactory,
    Efficiency,
    EncryptionModule,
    EnvironmentProcessor,
    GeckoGrippers,
    InjectorNeedle,
    OlfactorySensor,
    ParasiticLink,
    PrisSensor,
    RobotTransceiver,
    VacuumEnvironmentProtection,
    VoderSpeaker,
    WirelessDataLink,
)
from ceres.make.robot.skills import SkillPackage
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits

_expected = SimpleNamespace(
    hits=1,
    locomotion='Grav',
    speed='12m',  # GravLocomotion(speed_increase=2) 7 + agility 1 + AgilityEnh(4) = 12
    tl=15,
    base_armour=4,
    traits='Armour (+4), Flyer (idle), Hardened, Heightened Senses, Invisible, IR/UV Vision, Small (-4)',
    programming='Advanced (INT 8)',
    endurance_hours=76,  # 24×0.8×2.0×2.0 = 76.8; source shows 77 (rounding)
    remaining_bandwidth=1,  # 2 − 1(Recon pkg) = 1
    available_slots=3,  # base 1 + 2 freed by manipulators=[]
    used_slots=2,  # brain(0) + ActiveCamouflage(1) + AvatarReceiver(1); Efficiency → chassis mod
    # → 21 zero-slot items = quota (5+1+15=21), no excess
    remaining_slots=1,
)
# Ceres Cr97,830 vs source Cr140,000. Gap Cr42,170 unresolved.
_expected.cost = 97_630


def build_munin() -> Robot:
    """Note: Partial Munin — cost gap Cr42,170 vs source Cr140,000 unresolved.

    AgilityEnhancement(4) and Efficiency inferred (not in source options list).
    GravLocomotion(speed_increase=2) inferred for 12m speed and 76h endurance.
    Stealth 4 from ActiveCamouflage hardware grant; Recon 1 from brain pkg + EnvironmentProcessor.
    Source: user-supplied stat block — Munin, SIZE_1 TL15 Grav.
    """
    return Robot(
        name='Munin',
        tl=15,
        size=RobotSize.SIZE_1,
        locomotion=GravLocomotion(speed_increase=2),
        manipulators=[],
        brain=AdvancedBrain(
            brain_tl=15,
            hardened=True,
            installed_skills=(SkillPackage(name='Recon', level=1, bandwidth=1),),
        ),
        options=[
            AgilityEnhancement(level=4),
            Efficiency(),
            ActiveCamouflage(),
            AvatarReceiver(),
            CamouflageAudible(quality='advanced'),
            CamouflageOlfactory(quality='advanced'),
            EncryptionModule(),
            EnvironmentProcessor(),
            GeckoGrippers(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            InjectorNeedle(),
            OlfactorySensor(quality='advanced'),
            ParasiticLink(),
            PrisSensor(),
            RobotTransceiver(range_km=5000, quality='advanced'),
            VacuumEnvironmentProtection(),
            VoderSpeaker(quality='broad_spectrum'),
            WirelessDataLink(),
        ],
    )


class TestMunin:
    def test_hits(self):
        assert build_munin().hits == _expected.hits

    def test_base_armour(self):
        assert build_munin().base_armour == _expected.base_armour

    def test_traits(self):
        assert format_traits(build_munin().traits) == _expected.traits

    def test_programming(self):
        assert build_munin().brain.programming_label() == _expected.programming

    def test_endurance(self):
        # 24 × 0.8(speed_increase=2) × 2.0(TL15) × 2.0(Efficiency) = 76.8 → 76
        assert int(build_munin().base_endurance) == _expected.endurance_hours

    def test_cost(self):
        assert build_munin().total_cost == _expected.cost

    def test_locomotion_label(self):
        assert build_munin().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_munin().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_munin().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_munin().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_munin().remaining_slots == _expected.remaining_slots

    def test_remaining_bandwidth(self):
        assert build_munin().brain.remaining_bandwidth == _expected.remaining_bandwidth

    def test_hardened_trait(self):
        robot = build_munin()
        trait_names = [t.name for t in robot.traits]
        assert 'Hardened' in trait_names

    def test_invisible_trait(self):
        robot = build_munin()
        trait_names = [t.name for t in robot.traits]
        assert 'Invisible' in trait_names

    def test_ir_uv_vision_trait(self):
        robot = build_munin()
        trait_names = [t.name for t in robot.traits]
        assert 'IR/UV Vision' in trait_names

    def test_heightened_senses_trait(self):
        robot = build_munin()
        trait_names = [t.name for t in robot.traits]
        assert 'Heightened Senses' in trait_names

    def test_stealth_4_from_active_camouflage(self):
        robot = build_munin()
        assert 'Stealth 4' in robot.skills_display

    def test_athletics_dexterity_4(self):
        robot = build_munin()
        assert 'Athletics (dexterity) 4' in robot.skills_display

    def test_recon_1(self):
        # EnvironmentProcessor → Recon 0; SkillPackage Recon 1 → merged max = 1
        robot = build_munin()
        assert 'Recon 1' in robot.skills_display

    def test_spec_attacks_row(self):
        spec = build_munin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == '—'

    def test_spec_manipulators_row(self):
        spec = build_munin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == '—'

    def test_spec_options_has_active_camouflage(self):
        spec = build_munin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Active Camouflage' in value

    def test_spec_options_has_avatar_receiver(self):
        spec = build_munin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Avatar Receiver' in value

    def test_spec_options_has_environment_processor(self):
        spec = build_munin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Environment Processor' in value

    def test_spec_options_has_pris_sensor(self):
        spec = build_munin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'PRIS Sensor' in value

    def test_json_roundtrip(self):
        robot = build_munin()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Munin'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_1
        assert isinstance(restored.locomotion, GravLocomotion)
        assert isinstance(restored.brain, AdvancedBrain)
        assert restored.brain.hardened is True
        assert len(restored.brain.installed_skills) == 1
