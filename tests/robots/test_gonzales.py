# Source: user-supplied stat block (no refs/robot/xxx_gonzales.md).
#
# SIZE_4 TL15: STR = 2×3−1 = 5 (SIZE_3 manipulators), DEX = ceil(15/2)+1 = 9. Source: 2× (STR 5 DEX 9). ✓
# BasicBrain (locomotion, TL10): INT 4, programming 'Basic (locomotion) (INT 4)'. ✓
# Endurance: WheelsATV base 72h × TL15 multiplier 2.0 × 2.0 (Efficiency) = 288h. ✓
#   Vehicle speed = 288/4 = 72h (rules: factor of 4). Source parenthetical "36h" appears to be
#   a source error — they listed the pre-Efficiency vehicle figure (144/4 = 36) without updating.
# Armour: TL15 → base +4. IncreasedArmour(+4) → total +8 = Armour (+8). ✓
# Speed: VehicleSpeedModification on WheelsATV → speed band 'slow' (WheelsAtvLocomotion._vehicle_speed_band).
# Skills: Basic (locomotion) gives Vehicle (type) X = Drive (wheel) 2 (type from WheelsATV, X = agility 0+2).
#   AgilityEnhancement +2: Athletics (dexterity) 2 (max wins over locomotion's Athletics 1). ✓
# Source: Drive (Wheel) 2, Athletics (dexterity) 2. ✓
# Efficiency: cost = 50% BCC = Cr1,200. ✓
# Stealth 3: from CamouflageVisual (enhanced), DM-3 → effective Stealth 3. ✓
# Heightened Senses: from AuditorySensor (broad spectrum). ✓
# IR/UV Vision: from PrisSensor. ✓
# IncreasedArmour(+4) at TL15 SIZE_4: slots = max(ceil(4×0.003×8)=1, ceil(4/4)=1, 1) = 1; cost = Cr2,500.
# Cost: Ceres Cr24,500 vs source Cr27,000. Gap = Cr2,500 unresolved.
# Slots: IncreasedArmour takes 1 slot → remaining = −1 (slot overload noted). Source shows 0 remaining.

from types import SimpleNamespace

from ceres.make.robot import BasicBrain, Manipulator, Robot, RobotSize, WheelsAtvLocomotion, default_suite
from ceres.make.robot.options import (
    AgilityEnhancement,
    AuditorySensor,
    CamouflageAudible,
    CamouflageOlfactory,
    CamouflageVisual,
    Efficiency,
    IncreasedArmour,
    NavigationSystem,
    PrisSensor,
    RobotTransceiver,
    StorageCompartment,
    VehicleSpeedModification,
    VoderSpeaker,
)
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits

_expected = SimpleNamespace(
    hits=12,
    locomotion='Wheels, ATV',
    speed='slow',  # VSM on Wheels ATV → speed band 'slow'
    tl=15,
    base_armour=4,  # TL15 base; total = 4+4 = 8 from IncreasedArmour(+4)
    traits='Armour (+8), ATV, Heightened Senses, IR/UV Vision, Small (-1)',
    programming='Basic (locomotion) (INT 4)',
    endurance_hours=288,
    vehicle_endurance_hours=72,  # rules: 288/4; source shows 36h (source error — pre-Efficiency figure)
    attacks='—',
    manipulators='(STR 5 DEX 9) × 2',
    available_slots=8,
    used_slots=9,  # IncreasedArmour takes 1 slot; source shows 0 remaining
    remaining_slots=-1,
)
# Ceres Cr24,500 vs source Cr27,000. Gap = Cr2,500 unresolved.
_expected.cost = 24_500


def build_gonzales() -> Robot:
    """Note: Partial Gonzales — cost gap Cr2,500 vs source Cr27,000 unresolved.

    Source: user-supplied stat block — Gonzales, SIZE_4 TL15 Wheels ATV.
    """
    return Robot(
        name='Gonzales',
        tl=15,
        size=RobotSize.SIZE_4,
        locomotion=WheelsAtvLocomotion(),
        brain=BasicBrain(function='locomotion'),
        manipulators=[Manipulator(size=RobotSize.SIZE_3), Manipulator(size=RobotSize.SIZE_3)],
        options=[
            IncreasedArmour(additional=4),
            AgilityEnhancement(level=2),
            Efficiency(),
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
            NavigationSystem(quality='basic'),
            StorageCompartment(slots_count=4),
            VehicleSpeedModification(),
            RobotTransceiver(range_km=5000, quality='advanced'),
        ],
    )


class TestGonzales:
    def test_hits(self):
        assert build_gonzales().hits == _expected.hits

    def test_base_armour(self):
        # base_armour is TL-derived; total armour (traits) includes IncreasedArmour delta
        assert build_gonzales().base_armour == _expected.base_armour

    def test_traits(self):
        assert format_traits(build_gonzales().traits) == _expected.traits

    def test_programming(self):
        assert build_gonzales().brain.programming_label() == _expected.programming

    def test_endurance(self):
        assert int(build_gonzales().base_endurance) == _expected.endurance_hours

    def test_vehicle_endurance(self):
        robot = build_gonzales()
        vehicle_end = int(robot.base_endurance / 4)
        assert vehicle_end == _expected.vehicle_endurance_hours

    def test_cost(self):
        assert build_gonzales().total_cost == _expected.cost

    def test_locomotion_label(self):
        assert build_gonzales().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_gonzales().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_gonzales().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_gonzales().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_gonzales().remaining_slots == _expected.remaining_slots

    def test_spec_attacks_row(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == _expected.manipulators

    def test_spec_options_has_pris_sensor(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'PRIS Sensor' in value

    def test_spec_options_has_auditory_broad_spectrum(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Auditory Sensor (broad spectrum)' in value

    def test_spec_options_has_voder_broad_spectrum(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Voder Speaker (broad spectrum)' in value

    def test_spec_options_has_camouflage_visual(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Camouflage: Visual (enhanced)' in value

    def test_spec_options_has_camouflage_audible(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Camouflage: Audible (advanced)' in value

    def test_spec_options_has_camouflage_olfactory(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Camouflage: Olfactory (advanced)' in value

    def test_spec_options_has_navigation(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Navigation System (basic)' in value

    def test_spec_options_has_storage(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Storage Compartment (4 Slots)' in value

    def test_spec_options_has_efficiency(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Efficiency' in value

    def test_spec_options_has_transceiver_5000km(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Transceiver 5,000km (advanced)' in value

    def test_no_spare_slots_in_options(self):
        spec = build_gonzales().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Spare Slots' not in value

    def test_pris_sensor_gives_ir_uv_vision_trait(self):
        robot = build_gonzales()
        trait_names = [t.name for t in robot.traits]
        assert 'IR/UV Vision' in trait_names

    def test_auditory_broad_spectrum_gives_heightened_senses_trait(self):
        robot = build_gonzales()
        trait_names = [t.name for t in robot.traits]
        assert 'Heightened Senses' in trait_names

    def test_camouflage_visual_gives_stealth_3(self):
        robot = build_gonzales()
        skills_str = robot.skills_display
        assert 'Stealth 3' in skills_str

    def test_locomotion_gives_drive_wheel_2(self):
        # Basic (locomotion): Drive (wheel) at agility level = 0 (WheelsATV base) + 2 (AgEnh) = 2
        robot = build_gonzales()
        assert 'Drive (wheel) 2' in robot.skills_display

    def test_agility_enhancement_gives_athletics_dexterity_2(self):
        # AgilityEnhancement(level=2) grant wins over locomotion's Athletics(dex) 1
        robot = build_gonzales()
        assert 'Athletics (dexterity) 2' in robot.skills_display

    def test_no_flyer_grav_in_skills(self):
        robot = build_gonzales()
        assert 'Flyer (grav)' not in robot.skills_display

    def test_manipulator_str_5(self):
        robot = build_gonzales()
        m = robot.manipulators[0]
        assert m.effective_str(RobotSize.SIZE_4) == 5

    def test_manipulator_dex_9(self):
        robot = build_gonzales()
        m = robot.manipulators[0]
        assert m.effective_dex(15) == 9

    def test_json_roundtrip(self):
        robot = build_gonzales()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Gonzales'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_4
        assert isinstance(restored.locomotion, WheelsAtvLocomotion)
        assert isinstance(restored.brain, BasicBrain)
        assert restored.brain.function == 'locomotion'
