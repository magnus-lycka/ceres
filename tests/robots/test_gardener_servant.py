# Source: refs/robot/121_hiver.md
#
# SIZE_5 TL15 Walker.
# Brain: AdvancedBrain TL15, int_upgrade=1 → INT 9, DM+1. bandwidth=6 (delta=4, cost Cr20,000).
#   int_upgrade_bw = 1×2/2 = 1. Skill BW used = 5 (5 skills × 1 each). Total used = 6. Remaining = 0.
# Skills (source level 2 = pkg 1 + DM+1): Animals(veterinary)1, Medic 1, Profession(cleaning)1,
#   Profession(gardening)1, Steward 1.
# Speed: WalkerLocomotion(speed_increase=1) → 6m, endurance −10%.
#   Base endurance: 72 × 0.9 × 2.0 = 129.6 → int = 129. Source says 130 (rounds to nearest).
# Armour: TL15 → base +4. No IncreasedArmour. Source: Armour (+4). ✓
# Traits: Armour (+4), ATV (Walker), Heightened Senses (PRIS + Olfactory advanced), IR/UV Vision (PRIS).
# Manipulators: 4 arm + 2 leg, all SIZE_5 default STR 9 DEX 9.
# Cost: Ceres ~Cr86,100 vs source Cr85,000. Gap ~Cr1,100 unresolved (possible rounding in source).
# Default suite: see, wireless, improved_transceiver (5km), drone — 4 items (no voder, no std auditory).

from types import SimpleNamespace

from ceres.make.robot import Manipulator, Robot, RobotSize, WalkerLocomotion, default_suite
from ceres.make.robot.brain import AdvancedBrain
from ceres.make.robot.options import (
    AgriculturalEquipment,
    AuditorySensor,
    Autobar,
    Autochef,
    DomesticCleaningEquipment,
    Medikit,
    OlfactorySensor,
    PrisSensor,
    StorageCompartment,
)
from ceres.make.robot.skills import Animals, Medic, RobotProfession, Steward
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits

_expected = SimpleNamespace(
    hits=20,
    locomotion='Walker',
    speed='6m',
    tl=15,
    base_armour=4,
    traits='Armour (+4), ATV, Heightened Senses, IR/UV Vision',
    programming='Advanced (INT 9)',
    endurance_hours=129,  # 72 × 0.9 × 2.0 = 129.6 truncated; source rounds to 130
    remaining_bandwidth=0,
    manipulators='(STR 9 DEX 9) × 4, Manipulator leg (STR 9 DEX 9) × 2',
)


def build_gardener_servant() -> Robot:
    """Note: Gardener Servant — endurance 129h (Ceres) vs 130h (source rounds 129.6 up).

    Source: refs/robot/121_hiver.md — Gardener Servant, SIZE_5 TL15 Walker.
    """
    return Robot(
        name='Gardener Servant',
        tl=15,
        size=RobotSize.SIZE_5,
        locomotion=WalkerLocomotion(speed_increase=1),
        brain=AdvancedBrain(
            brain_tl=15,
            int_upgrade=1,
            bandwidth=6,
            installed_skills=(
                Animals(veterinary=1),
                Medic(level=1),
                RobotProfession(cleaning=1),
                RobotProfession(gardening=1),
                Steward(level=1),
            ),
        ),
        manipulators=[Manipulator(), Manipulator(), Manipulator(), Manipulator()],
        legs=[Manipulator(), Manipulator()],
        options=[
            *default_suite(speak=False, hear=False, drone=True),
            AgriculturalEquipment(size='small'),
            AuditorySensor(quality='broad_spectrum'),
            Autobar(quality='enhanced'),
            Autochef(quality='enhanced'),
            DomesticCleaningEquipment(size='small'),
            Medikit(quality='enhanced'),
            OlfactorySensor(quality='advanced'),
            PrisSensor(),
            StorageCompartment(slots_count=3, storage_type='refrigerated'),
        ],
    )


class TestGardenerServant:
    def test_hits(self):
        assert build_gardener_servant().hits == _expected.hits

    def test_base_armour(self):
        assert build_gardener_servant().base_armour == _expected.base_armour

    def test_traits(self):
        assert format_traits(build_gardener_servant().traits) == _expected.traits

    def test_programming(self):
        assert build_gardener_servant().brain.programming_label() == _expected.programming

    def test_endurance(self):
        assert int(build_gardener_servant().base_endurance) == _expected.endurance_hours

    def test_locomotion_label(self):
        assert build_gardener_servant().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_gardener_servant().speed_label == _expected.speed

    def test_remaining_bandwidth(self):
        assert build_gardener_servant().brain.remaining_bandwidth == _expected.remaining_bandwidth

    def test_skills_animals_veterinary_2(self):
        # pkg 1 + INT DM+1 = 2
        assert 'Animals (Veterinary) 2' in build_gardener_servant().skills_display

    def test_skills_medic_2(self):
        assert 'Medic 2' in build_gardener_servant().skills_display

    def test_skills_profession_cleaning_2(self):
        assert 'Profession (Cleaning) 2' in build_gardener_servant().skills_display

    def test_skills_profession_gardening_2(self):
        assert 'Profession (Gardening) 2' in build_gardener_servant().skills_display

    def test_skills_steward_2(self):
        assert 'Steward 2' in build_gardener_servant().skills_display

    def test_skills_no_bandwidth_surplus(self):
        assert 'Bandwidth available' not in build_gardener_servant().skills_display

    def test_manipulators_display(self):
        robot = build_gardener_servant()
        assert _expected.manipulators == robot._manipulators_display

    def test_leg_manipulators_count(self):
        robot = build_gardener_servant()
        assert len(robot._leg_manipulators) == 2

    def test_leg_manipulator_stats(self):
        robot = build_gardener_servant()
        m = robot._leg_manipulators[0]
        assert m.effective_str(RobotSize.SIZE_5) == 9
        assert m.effective_dex(15) == 9

    def test_spec_options_has_autobar(self):
        spec = build_gardener_servant().build_spec()
        assert 'Autobar (enhanced)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_autochef(self):
        spec = build_gardener_servant().build_spec()
        assert 'Autochef (enhanced)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_pris_sensor(self):
        spec = build_gardener_servant().build_spec()
        assert 'PRIS Sensor' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_olfactory_sensor(self):
        spec = build_gardener_servant().build_spec()
        assert 'Olfactory Sensor (advanced)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_medikit(self):
        spec = build_gardener_servant().build_spec()
        assert 'Medikit (enhanced)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_spec_options_has_storage_refrigerated(self):
        spec = build_gardener_servant().build_spec()
        assert 'Storage Compartment (3 Slots refrigerated)' in spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value

    def test_json_roundtrip(self):
        robot = build_gardener_servant()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Gardener Servant'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_5
        assert isinstance(restored.locomotion, WalkerLocomotion)
        assert isinstance(restored.brain, AdvancedBrain)
        assert restored.brain.bandwidth == 6
        assert len(restored.brain.installed_skills) == 5
        assert len(restored.manipulators) == 4
        assert len(restored.legs) == 2
