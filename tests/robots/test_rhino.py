# Source: user-supplied stat block + detailed design-tool breakdown
#
# SIZE_8 Walker TL15 MCr6.8
#
# Brain: SelfAwareBrain TL15, bandwidth 18 (base 10 + delta 8, Cr100,000 upgrade).
#   Hardened. Hardening extra = 0.5×1,000,000 + 0.5×100,000 = Cr550,000 ✓
#   INT 12 → DM+2 for INT skills.
#   DEX = ceil(15/2)+1 = 9 → DM+1 for DEX skills.
#   STR = 2×8−1 = 15 → DM+3 for STR skills.
#
# Software: Fab Creator/3 (BW 3, TL13, Cr20,000); Translator/0 (BW 0, TL9, Cr50).
#
# Skills: skill packages listed below. Source shows specialization names
#   even for level-0 packages (e.g. "Profession (Belter) 0"). Ceres collapses
#   level-0 specializations to "(All)" so "Profession (Belter) 0 + DM+2" →
#   "Profession (All) 2" in Ceres. Athletics specializations are exceptions: their
#   specialization names are preserved because the characteristic varies.
#
# Bandwidth: skill BW = 2(Medic)+3(Investigate)+2(Sci.Bio)+2(Sci.Chem)+2(Sci.Rob)+
#   2(Prof.Fab)+2(Prof.Rob) = 15. Software BW = 3(Fab Creator/3)+0(Translator/0) = 3.
#   Total used = 18. Brain BW = 18 → remaining = 0.
#
# Manipulators: 2× SIZE_8 default (STR 15, DEX 9); 2× SIZE_3 str_bonus=1
#   dex_bonus=6 (STR 2×3−1+1=6, DEX 9+6=15).
#
# Options: source design-tool shows Speakers: None → no VoderSpeaker;
#   Transceiver: None → no RobotTransceiver; Visual: None → no PrisSensor.
#   MedicalChamber base = 40 slots (40×Cr200=Cr8,000); sub-options add slots.
#   Total medical system: 40(base)+8(improved LB)+8(reanimation)+4(species)=60 slots.
#
# Slots: Ceres uses base_available=128; actual slot usage differs from source tool
#   accounting (source reports 0 remaining).

from types import SimpleNamespace

from ceres.make.robot import (
    Robot,
    RobotSize,
    SelfAwareBrain,
    WalkerLocomotion,
    default_suite,
)
from ceres.make.robot.manipulators import Manipulator
from ceres.make.robot.options import (
    BioscanneSensor,
    DensitometerSensor,
    EncryptionModule,
    EnvironmentProcessor,
    FabricationChamber,
    InjectorNeedle,
    MedicalChamber,
    Medikit,
    NeuralActivitySensor,
    OlfactorySensor,
    RoboticDroneController,
    ScientificToolkit,
    SolarCoating,
    StorageCompartment,
    SwarmController,
    VacuumEnvironmentProtection,
    VideoScreen,
)
from ceres.make.robot.skills import (
    Athletics,
    BrainSoftware,
    Electronics,
    Engineer,
    Investigate,
    LifeScience,
    Mechanic,
    Medic,
    Melee,
    PhysicalScience,
    Recon,
    RoboticScience,
    RobotProfession,
    SpacerProfession,
    Survival,
    Tactics,
)
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits

_expected = SimpleNamespace(
    hits=72,
    locomotion='Walker',
    speed='5m',
    tl=15,
    base_armour=4,
    traits='Armour (+4), ATV, Hardened, Heightened Senses, Large (+3)',
    programming='Self-Aware (INT 12)',
    endurance_hours=144,
    # Ceres: remaining_bandwidth = 18 − 15(skill BW) − 3(software BW) = 0
    remaining_bandwidth=0,
)


def build_rhino() -> Robot:
    return Robot(
        name='Rhino',
        tl=15,
        size=RobotSize.SIZE_8,
        locomotion=WalkerLocomotion(),
        brain=SelfAwareBrain(
            hardened=True,
            bandwidth=18,
            installed_skills=(
                # STR skill: pkg 0 + STR DM+3 = 3
                Athletics(strength=0),
                # DEX skill: pkg 0 + DEX DM+1 = 1
                Athletics(dexterity=0),
                # INT skills: pkg 2 + DM+2 = 4
                Medic(level=2),
                # Investigate base BW=1; pkg 2 + DM+2 = 4
                Investigate(level=2),
                LifeScience(biology=2),
                PhysicalScience(chemistry=2),
                RoboticScience(robotics=2),
                RobotProfession(fabricator=2),
                RobotProfession(robotics=2),
                # INT skills, level 0 → (All) in Ceres; source shows individual speciality
                Electronics(),
                Engineer(),
                Mechanic(),
                Tactics(),
                SpacerProfession(belter=0),
                # DEX skill at level 0; collapse to "Melee (All)"; pkg 0 + DEX DM+1 = 1
                Melee(),
                Recon(),
                Survival(),
            ),
            installed_software=(
                BrainSoftware(name='Fab Creator/3', bandwidth=3, tl=13, cost=20_000.0),
                BrainSoftware(name='Translator/0', bandwidth=0, tl=9, cost=50.0),
            ),
        ),
        manipulators=[
            Manipulator(),  # STR 15, DEX 9
            Manipulator(),  # STR 15, DEX 9
            Manipulator(size=RobotSize.SIZE_3, str_bonus=1, dex_bonus=6),  # STR 6, DEX 15
            Manipulator(size=RobotSize.SIZE_3, str_bonus=1, dex_bonus=6),  # STR 6, DEX 15
        ],
        options=[
            *default_suite(speak=False, hear=False, improved_transceiver=False, drone=True),
            BioscanneSensor(),
            DensitometerSensor(),
            EncryptionModule(),
            EnvironmentProcessor(),
            *[InjectorNeedle() for _ in range(8)],
            Medikit(quality='advanced'),
            MedicalChamber(
                slots_count=40,
                low_berth='improved',
                reanimation=True,
                species_specific=1,
            ),
            NeuralActivitySensor(),
            OlfactorySensor(quality='advanced'),
            RoboticDroneController(quality='advanced'),
            ScientificToolkit(quality='advanced'),
            SolarCoating(quality='advanced'),
            StorageCompartment(slots_count=8, storage_type='refrigerated'),
            SwarmController(quality='advanced'),
            VacuumEnvironmentProtection(),
            VideoScreen(quality='advanced'),
            FabricationChamber(quality='enhanced', slots_count=64),
        ],
    )


class TestRhino:
    def test_hits(self):
        assert build_rhino().hits == _expected.hits

    def test_base_armour(self):
        assert build_rhino().base_armour == _expected.base_armour

    def test_traits(self):
        assert format_traits(build_rhino().traits) == _expected.traits

    def test_programming(self):
        assert build_rhino().brain.programming_label() == _expected.programming

    def test_endurance(self):
        assert int(build_rhino().base_endurance) == _expected.endurance_hours

    def test_locomotion_label(self):
        assert build_rhino().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_rhino().speed_label == _expected.speed

    def test_remaining_bandwidth(self):
        assert build_rhino().brain.remaining_bandwidth == _expected.remaining_bandwidth

    def test_hardened_trait(self):
        assert any(t.name == 'Hardened' for t in build_rhino().traits)

    def test_heightened_senses_trait(self):
        assert any(t.name == 'Heightened Senses' for t in build_rhino().traits)

    def test_large_plus_3_trait(self):
        assert any(str(t) == 'Large (+3)' for t in build_rhino().traits)

    def test_atv_trait(self):
        assert any(t.name == 'ATV' for t in build_rhino().traits)

    # ── Skills ────────────────────────────────────────────────────────────────

    def test_skills_athletics_dexterity_1(self):
        # pkg 0 + DEX DM+1 = 1; specialization preserved (variable characteristic)
        assert 'Athletics (Dexterity) 1' in build_rhino().skills_display

    def test_skills_athletics_strength_3(self):
        # pkg 0 + STR DM+3 = 3; specialization preserved (variable characteristic)
        assert 'Athletics (Strength) 3' in build_rhino().skills_display

    def test_skills_investigate_4(self):
        # pkg 2 + INT DM+2 = 4
        assert 'Investigate 4' in build_rhino().skills_display

    def test_skills_medic_4(self):
        assert 'Medic 4' in build_rhino().skills_display

    def test_skills_melee_all_1(self):
        # DEX skill at pkg level 0 + DM+1 = 1; specialization collapses to (All)
        assert 'Melee (All) 1' in build_rhino().skills_display

    def test_skills_profession_fabricator_4(self):
        assert 'Profession (Fabricator) 4' in build_rhino().skills_display

    def test_skills_profession_robotics_4(self):
        assert 'Profession (Robotics) 4' in build_rhino().skills_display

    def test_skills_science_biology_4(self):
        assert 'Science (Biology) 4' in build_rhino().skills_display

    def test_skills_science_chemistry_4(self):
        assert 'Science (Chemistry) 4' in build_rhino().skills_display

    def test_skills_science_robotics_4(self):
        assert 'Robotic Science (Robotics) 4' in build_rhino().skills_display

    def test_skills_recon_2(self):
        # pkg 0 + INT DM+2 = 2; EnvironmentProcessor Recon 0 superseded
        display = build_rhino().skills_display
        assert 'Recon 2' in display
        assert 'Recon 0' not in display

    def test_skills_electronics_all_2(self):
        # level-0 specialization → (All); INT DM+2
        assert 'Electronics (All) 2' in build_rhino().skills_display

    def test_skills_engineer_all_2(self):
        assert 'Engineer (All) 2' in build_rhino().skills_display

    def test_skills_mechanic_2(self):
        assert 'Mechanic 2' in build_rhino().skills_display

    def test_skills_survival_2(self):
        assert 'Survival 2' in build_rhino().skills_display

    def test_skills_tactics_all_2(self):
        assert 'Tactics (All) 2' in build_rhino().skills_display

    def test_skills_no_bandwidth_surplus(self):
        # 0 remaining bandwidth → no "+N Bandwidth available" suffix
        assert 'Bandwidth available' not in build_rhino().skills_display

    # ── Options ───────────────────────────────────────────────────────────────

    def test_spec_options_has_bioscanner_sensor(self):
        spec = build_rhino().build_spec()
        assert 'Bioscanner Sensor' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_densitometer_sensor(self):
        spec = build_rhino().build_spec()
        assert 'Densitometer Sensor' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_neural_activity_sensor(self):
        spec = build_rhino().build_spec()
        assert 'Neural Activity Sensor' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_encryption_module(self):
        spec = build_rhino().build_spec()
        assert 'Encryption Module' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_environment_processor(self):
        spec = build_rhino().build_spec()
        assert 'Environment Processor' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_fabrication_chamber(self):
        spec = build_rhino().build_spec()
        assert 'Fabrication Chamber (enhanced, 64 Slots)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_medical_chamber(self):
        spec = build_rhino().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        # slots_count=40 base + 8(improved LB) + 8(reanimation) + 4(species) = 60 total
        assert 'Medical Chamber (60 Slots, Improved Low Berth, Reanimation, Species-Specific Add-on)' in value

    def test_spec_options_has_medikit(self):
        spec = build_rhino().build_spec()
        assert 'Medikit (advanced)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_scientific_toolkit(self):
        spec = build_rhino().build_spec()
        assert 'Scientific Toolkit (advanced)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_solar_coating(self):
        spec = build_rhino().build_spec()
        assert 'Solar Coating (advanced)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_swarm_controller(self):
        spec = build_rhino().build_spec()
        assert 'Swarm Controller (advanced)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_robotic_drone_controller(self):
        spec = build_rhino().build_spec()
        assert 'Robotic Drone Controller (advanced)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_vacuum_environment_protection(self):
        spec = build_rhino().build_spec()
        assert 'Vacuum Environment Protection' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_manipulators_includes_large_arms(self):
        robot = build_rhino()
        assert '(STR 15 DEX 9)' in robot._manipulators_display

    def test_manipulators_includes_dexterous_arms(self):
        robot = build_rhino()
        assert '(STR 6 DEX 15)' in robot._manipulators_display

    def test_json_roundtrip(self):
        robot = build_rhino()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Rhino'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_8
        assert isinstance(restored.locomotion, WalkerLocomotion)
        assert isinstance(restored.brain, SelfAwareBrain)
        assert restored.brain.hardened is True
        assert restored.brain.bandwidth == 18
        assert len(restored.brain.installed_skills) == 17
        assert len(restored.brain.installed_software) == 2
        assert len(restored.manipulators) == 4
