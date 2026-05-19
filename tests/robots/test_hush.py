# Source: user-supplied stat block (no refs/robot/xxx_hush.md).
#
# SIZE_2 TL15: STR = 2×2−1 = 3, DEX = ceil(15/2)+1 = 9. Source: 2× (STR 3 DEX 9). ✓
# BasicBrain (recon, TL10): INT 4, programming 'Basic (recon) (INT 4)'. ✓
#
# Speed 10m and Endurance 173h discrepancy:
#   WalkerLocomotion base 5m, TL15 base endurance 72h × 2.0 = 144h.
#   173h ≈ 72 × 1.2 × 2.0 — matches speed_reduction=2 (+20% endurance) + Agility Enhancement
#   giving the extra speed back: e.g., speed_reduction=2 (→3m) + AgilityEnhancement+7 (→10m),
#   but AgilityEnhancement is not yet implemented and Tactical Speed Reduction is incompatible
#   with Agility Enhancement per rules. Modelled with WalkerLocomotion() (no modification);
#   speed=5m, endurance=144h in partial build.
#
# Armour: TL15 → base +4. Source: Armour (+4). ✓ (No IncreasedArmour here.)
#
# GeckoGrippers: zero-slot, TL9, Cr500 × base_slots = Cr500 × 2 = Cr1,000. ✓
# Navigation 1: from NavigationSystem (Basic). ✓
# Stealth 3: from CamouflageVisual (Enhanced), DM-3. ✓
# Recon 2, Athletics (dexterity) 1: from BasicBrain (recon) function. ✓
#
# Default suite: PRIS (paid upgrade), broad audio (paid upgrade), broad voder (paid upgrade),
#   DroneInterface (free, 1 of 5 slots). Remaining 4 free slots treated as unused.
#   Source shows no standard Transceiver 5km.
#
# Slots: available=2 (SIZE_2). NavigationSystem(basic)=2 slots. Used=2, remaining=0. ✓
#
# Cost discrepancy (partial): Ceres Cr12,700 vs source Cr17,000.
#   Source includes speed/agility modifications (unimplemented, ~Cr4,300 gap).

from types import SimpleNamespace

from ceres.make.robot import BasicBrain, Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.options import (
    AuditorySensor,
    CamouflageAudible,
    CamouflageOlfactory,
    CamouflageVisual,
    GeckoGrippers,
    NavigationSystem,
    PrisSensor,
    RobotTransceiver,
    VoderSpeaker,
)
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits

_expected = SimpleNamespace(
    hits=4,
    locomotion='Walker',
    speed='5m',  # source: '10m' — Agility Enhancement + speed modification not yet implemented
    tl=15,
    base_armour=4,
    traits='Armour (+4), ATV, Heightened Senses, IR/UV Vision, Small (-3)',
    programming='Basic (recon) (INT 4)',
    endurance_hours=144,  # source: 173h — requires speed_reduction=2 + AgilityEnhancement, not yet implemented
    attacks='—',
    manipulators='(STR 3 DEX 9) × 2',
    available_slots=2,
    used_slots=2,
    remaining_slots=0,
)
# Partial build: source Cr17,000; missing speed/agility modifications (~Cr4,300 gap).
_expected.cost = 12_700


def build_hush() -> Robot:
    """Note: Partial Hush — speed and agility modifications not yet implemented.

    Speed shown as 5m (source: 10m) and endurance as 144h (source: 173h).
    Source: user-supplied stat block — Hush, SIZE_2 TL15 Walker.
    """
    return Robot(
        name='Hush',
        tl=15,
        size=RobotSize.SIZE_2,
        locomotion=WalkerLocomotion(),
        brain=BasicBrain(function='recon'),
        manipulators=[Manipulator(), Manipulator()],
        options=[
            PrisSensor(),
            AuditorySensor(quality='broad_spectrum'),
            VoderSpeaker(quality='broad_spectrum'),
            *default_suite(
                drone=True,
                see=False,
                hear=False,
                speak=False,
                wireless=False,
                improved_transceiver=False,
            ),
            CamouflageVisual(quality='enhanced'),
            CamouflageAudible(quality='advanced'),
            CamouflageOlfactory(quality='advanced'),
            GeckoGrippers(),
            NavigationSystem(quality='basic'),
            RobotTransceiver(range_km=5000, quality='advanced'),
        ],
    )


class TestHushPartial:
    def test_hits(self):
        assert build_hush().hits == _expected.hits

    def test_base_armour(self):
        assert build_hush().base_armour == _expected.base_armour

    def test_traits(self):
        assert format_traits(build_hush().traits) == _expected.traits

    def test_programming(self):
        assert build_hush().brain.programming_label() == _expected.programming

    def test_endurance(self):
        assert int(build_hush().base_endurance) == _expected.endurance_hours

    def test_cost(self):
        assert build_hush().total_cost == _expected.cost

    def test_locomotion_label(self):
        assert build_hush().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_hush().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_hush().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_hush().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_hush().remaining_slots == _expected.remaining_slots

    def test_spec_attacks_row(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == _expected.manipulators

    def test_spec_options_has_pris_sensor(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'PRIS Sensor' in value

    def test_spec_options_has_auditory_broad_spectrum(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Auditory Sensor (broad spectrum)' in value

    def test_spec_options_has_voder_broad_spectrum(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Voder Speaker (broad spectrum)' in value

    def test_spec_options_has_camouflage_visual(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Camouflage: Visual (enhanced)' in value

    def test_spec_options_has_camouflage_audible(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Camouflage: Audible (advanced)' in value

    def test_spec_options_has_camouflage_olfactory(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Camouflage: Olfactory (advanced)' in value

    def test_spec_options_has_gecko_grippers(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Gecko Grippers' in value

    def test_spec_options_has_navigation(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Navigation System (basic)' in value

    def test_spec_options_has_transceiver_5000km(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Transceiver 5,000km (advanced)' in value

    def test_no_spare_slots_in_options(self):
        spec = build_hush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Spare Slots' not in value

    def test_pris_sensor_gives_ir_uv_vision_trait(self):
        robot = build_hush()
        trait_names = [t.name for t in robot.traits]
        assert 'IR/UV Vision' in trait_names

    def test_auditory_broad_spectrum_gives_heightened_senses_trait(self):
        robot = build_hush()
        trait_names = [t.name for t in robot.traits]
        assert 'Heightened Senses' in trait_names

    def test_camouflage_visual_gives_stealth_3(self):
        robot = build_hush()
        assert 'Stealth 3' in robot.skills_display

    def test_basic_brain_recon_gives_recon_2(self):
        robot = build_hush()
        assert 'Recon 2' in robot.skills_display

    def test_basic_brain_recon_gives_athletics_dex_1(self):
        robot = build_hush()
        assert 'Athletics (dexterity) 1' in robot.skills_display

    def test_navigation_system_gives_navigation_1(self):
        robot = build_hush()
        assert 'Navigation 1' in robot.skills_display

    def test_gecko_grippers_cost(self):
        # Cr500 × base_slots(SIZE_2=2) = Cr1,000
        robot = build_hush()
        grippers = next(o for o in robot.options if isinstance(o, GeckoGrippers))
        assert grippers.cost == 1000.0

    def test_json_roundtrip(self):
        robot = build_hush()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Hush'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_2
        assert isinstance(restored.locomotion, WalkerLocomotion)
        assert isinstance(restored.brain, BasicBrain)
        assert restored.brain.function == 'recon'
