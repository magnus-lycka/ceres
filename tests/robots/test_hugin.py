# Source: user-supplied stat block (no refs/robot/xxx_hugin.md).
#
# SIZE_1 TL15 Grav: base armour 4. AdvancedBrain(TL15→TL12 entry) INT 8, DM 0, BW 2.
# Hardened brain: +50% → Cr15,000 hardware cost.
# Speed 'High': VehicleSpeedModification on GravLocomotion → Flyer(high) trait.
# Endurance 96h (24h vehicle): 24 × 2.0(TL15) × 2.0(Efficiency) = 96h; vehicle = 96/4 = 24h.
#   Efficiency omitted from source options list — inferred for 96h endurance.
# AgilityEnhancement(4) inferred: source shows Athletics(dex) 4, not listed in options.
# Skills: Athletics(dex) 4 from AgilityEnhancement; Stealth 2 unexplained (source options omit source).
#   Flyer(Grav) 4 from source is not reproduced: would cost Cr1,000,000 as brain pkg (not viable).
#   Navigation 1 and Recon 1 from source also not reproduced here (no NavigationSystem in source options).
#   EnvironmentProcessor grants Recon 0 (Ceres) vs source's Recon 1 — source discrepancy.
# Cost: Ceres Cr84,910 vs source Cr130,000. Gap = Cr45,090 unresolved.
# Slots: manipulators=[] frees 2 slots → available=3. AdvancedBrain(0) + VSM(1) + AvatarReceiver(1) = 2
#   slotted; Efficiency is chassis mod (no item_message) → 21 zero-slot items = quota (5+1+15=21) →
#   no excess → used=2; remaining=1.
#   Brain costs 0 slots: TL12 Advanced entry (computer_x=2) at TL15 is 3 TLs after introduction →
#   min_free = max(0, 2−3) = 0; SIZE_1 fits for free.

from types import SimpleNamespace

from ceres.make.robot import GravLocomotion, Robot, RobotSize
from ceres.make.robot.brain import AdvancedBrain
from ceres.make.robot.options import (
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
    SolarCoating,
    VacuumEnvironmentProtection,
    VehicleSpeedModification,
    VoderSpeaker,
    WirelessDataLink,
)
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits

_expected = SimpleNamespace(
    hits=1,
    locomotion='Grav',
    speed='high',  # VehicleSpeedModification on GravLocomotion → Flyer(high) → speed_label='high'
    tl=15,
    base_armour=4,
    # Ceres uses lowercase 'high'; source shows 'Flyer (High)' with capital H.
    traits='Armour (+4), Flyer (high), Hardened, Heightened Senses, IR/UV Vision, Small (-4)',
    programming='Advanced (INT 8)',
    endurance_hours=96,  # 24 × 2.0(TL15) × 2.0(Efficiency) = 96h
    vehicle_endurance_hours=24,  # 96 / 4 ✓ (source confirms)
    available_slots=3,  # base 1 + 2 freed by manipulators=[]
    used_slots=2,  # brain(0) + VSM(1) + AvatarReceiver(1); Efficiency is chassis mod → 21 zero-slot = quota, no excess
    remaining_slots=1,
    remaining_bandwidth=2,  # no installed skills
)
# Ceres Cr84,710 vs source Cr130,000. Gap Cr45,290 unresolved.
_expected.cost = 84_710


def build_hugin() -> Robot:
    """Note: Partial Hugin — cost gap Cr45,090 vs source Cr130,000 unresolved.

    AgilityEnhancement(4) and Efficiency inferred (not in source options list).
    Flyer(Grav) 4 skill from source not reproduced: brain pkg at level 4 costs Cr1M (not viable).
    Stealth 2 from source not reproduced: origin unexplained from listed options.
    Navigation 1 and Recon 1 from source not reproduced (no NavigationSystem in source options).
    Source: user-supplied stat block — Hugin, SIZE_1 TL15 Grav VSM.
    """
    return Robot(
        name='Hugin',
        tl=15,
        size=RobotSize.SIZE_1,
        locomotion=GravLocomotion(),
        manipulators=[],
        brain=AdvancedBrain(
            brain_tl=15,
            hardened=True,
        ),
        options=[
            AgilityEnhancement(level=4),
            Efficiency(),
            VehicleSpeedModification(),
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
            OlfactorySensor(quality='advanced'),
            ParasiticLink(),
            PrisSensor(),
            SolarCoating(quality='advanced'),
            RobotTransceiver(range_km=5000, quality='advanced'),
            VacuumEnvironmentProtection(),
            VoderSpeaker(quality='broad_spectrum'),
            WirelessDataLink(),
        ],
    )


class TestHugin:
    def test_hits(self):
        assert build_hugin().hits == _expected.hits

    def test_base_armour(self):
        assert build_hugin().base_armour == _expected.base_armour

    def test_traits(self):
        assert format_traits(build_hugin().traits) == _expected.traits

    def test_programming(self):
        assert build_hugin().brain.programming_label() == _expected.programming

    def test_endurance(self):
        # 24 × 2.0(TL15) × 2.0(Efficiency) = 96h ✓
        assert int(build_hugin().base_endurance) == _expected.endurance_hours

    def test_vehicle_endurance(self):
        robot = build_hugin()
        vehicle_end = int(robot.base_endurance / 4)
        assert vehicle_end == _expected.vehicle_endurance_hours

    def test_cost(self):
        assert build_hugin().total_cost == _expected.cost

    def test_locomotion_label(self):
        assert build_hugin().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        # VSM on Grav → Flyer(high) trait → speed_label returns 'high'
        assert build_hugin().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_hugin().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_hugin().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_hugin().remaining_slots == _expected.remaining_slots

    def test_remaining_bandwidth(self):
        assert build_hugin().brain.remaining_bandwidth == _expected.remaining_bandwidth

    def test_hardened_trait(self):
        robot = build_hugin()
        trait_names = [t.name for t in robot.traits]
        assert 'Hardened' in trait_names

    def test_flyer_high_trait(self):
        robot = build_hugin()
        trait_strs = [str(t) for t in robot.traits]
        assert 'Flyer (high)' in trait_strs

    def test_ir_uv_vision_trait(self):
        robot = build_hugin()
        trait_names = [t.name for t in robot.traits]
        assert 'IR/UV Vision' in trait_names

    def test_heightened_senses_trait(self):
        robot = build_hugin()
        trait_names = [t.name for t in robot.traits]
        assert 'Heightened Senses' in trait_names

    def test_athletics_dexterity_4(self):
        robot = build_hugin()
        assert 'Athletics (dexterity) 4' in robot.skills_display

    def test_spec_attacks_row(self):
        spec = build_hugin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == '—'

    def test_spec_manipulators_row(self):
        spec = build_hugin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == '—'

    def test_spec_options_has_avatar_receiver(self):
        spec = build_hugin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Avatar Receiver' in value

    def test_spec_options_has_solar_coating(self):
        spec = build_hugin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Solar Coating' in value

    def test_spec_options_no_vehicle_speed_modification(self):
        # VSM is a locomotion mod — not listed in options display (same as BasicCourier)
        spec = build_hugin().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Vehicle Speed' not in value

    def test_json_roundtrip(self):
        robot = build_hugin()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Hugin'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_1
        assert isinstance(restored.locomotion, GravLocomotion)
        assert isinstance(restored.brain, AdvancedBrain)
        assert restored.brain.hardened is True
