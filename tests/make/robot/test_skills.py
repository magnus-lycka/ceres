"""Tests for SkillGrant and skill package helpers.

refs/robot/35_skill_packages.md — Primitive brain package table.
"""

import pytest

from ceres.character import skills as character_skills
from ceres.character.skills import Electronics, Level, Recon, Steward
from ceres.make.robot.skills import (
    _DEX_SKILLS,
    BrainSoftware,
    RobotProfession,
    SkillGrant,
    SkillPackage,
    Weapon,
    primitive_package_skills,
)


def _skill(skill_cls, field_name: str = 'level', value: int = 1):
    skill = skill_cls()
    getattr(skill, field_name).set(value)
    return skill


class TestSkillGrant:
    def test_str_with_level(self):
        assert str(SkillGrant(Electronics(remote_ops=Level(value=1)), 1)) == 'Electronics (Remote Ops) 1'

    def test_str_zero_level(self):
        assert str(SkillGrant(Recon(), 0)) == 'Recon 0'

    def test_equality(self):
        assert SkillGrant(Recon(), 1) == SkillGrant(Recon(), 1)

    def test_inequality_level(self):
        assert SkillGrant(Recon(), 0) != SkillGrant(Recon(), 1)

    def test_inequality_name(self):
        assert SkillGrant(Recon(), 0) != SkillGrant(Electronics(), 0)

    def test_character_skill_str_uses_speciality(self):
        grant = SkillGrant(Electronics(remote_ops=Level(value=1)), 1)

        assert str(grant) == 'Electronics (Remote Ops) 1'


class TestSkillPackage:
    def test_fields(self):
        pkg = SkillPackage(name=Electronics(remote_ops=Level(value=1)), level=1, bandwidth=1)
        assert pkg.name_text == 'Electronics (Remote Ops)'
        assert pkg.level == 1
        assert pkg.bandwidth == 1

    def test_roundtrip_json(self):
        pkg = SkillPackage(name=Steward(level=Level(value=2)), level=2, bandwidth=2)
        restored = SkillPackage.model_validate_json(pkg.model_dump_json())
        assert restored == pkg

    def test_character_skill_roundtrip_json(self):
        pkg = SkillPackage(name=Steward(level=Level(value=2)), level=2, bandwidth=2)
        restored = SkillPackage.model_validate_json(pkg.model_dump_json())

        assert restored == pkg
        assert restored.name_text == 'Steward'

    def test_group_skill_cost_uses_union_key(self):
        pkg = SkillPackage(name=character_skills.RoboticScience(robotics=Level(value=1)), level=2, bandwidth=2)
        assert pkg.cost == 20_000.0

    def test_robot_specific_profession_cost_uses_class_key(self):
        pkg = SkillPackage(name=RobotProfession(domestic_cleaner=Level(value=1)), level=2, bandwidth=2)
        assert pkg.cost == 20_000.0


class TestSkillPackageGrantName:
    """Level-0 speciality packages display as (All); level 1+ keep their speciality."""

    def test_level_0_specialty_becomes_all(self):
        pkg = SkillPackage(name=Electronics(remote_ops=Level(value=1)), level=0, bandwidth=0)
        assert pkg.skill_grant(0).name_text == 'Electronics (All)'

    def test_level_1_specialty_preserved(self):
        pkg = SkillPackage(name=Electronics(remote_ops=Level(value=1)), level=1, bandwidth=1)
        assert pkg.skill_grant(1).name_text == 'Electronics (Remote Ops)'

    def test_character_skill_speciality_preserved(self):
        pkg = SkillPackage(name=Electronics(remote_ops=Level(value=1)), level=1, bandwidth=1)
        assert pkg.skill_grant(1).name_text == 'Electronics (Remote Ops)'

    def test_level_0_no_specialty_unchanged(self):
        pkg = SkillPackage(name=character_skills.Admin(), level=0, bandwidth=0)
        assert pkg.skill_grant(0).name_text == 'Admin'

    def test_level_2_specialty_preserved(self):
        pkg = SkillPackage(name=character_skills.RoboticScience(robotics=Level(value=1)), level=2, bandwidth=2)
        assert pkg.skill_grant(2).name_text == 'Robotic Science (Robotics)'

    def test_level_0_engineer_specialty_becomes_all(self):
        pkg = SkillPackage(name=character_skills.Engineer(j_drive=Level(value=1)), level=0, bandwidth=0)
        assert pkg.skill_grant(0).name_text == 'Engineer (All)'

    def test_level_0_flyer_specialty_becomes_all(self):
        pkg = SkillPackage(name=character_skills.Flyer(grav=Level(value=1)), level=0, bandwidth=0)
        assert pkg.skill_grant(0).name_text == 'Flyer (All)'


class TestDexSkillsSet:
    """_DEX_SKILLS identifies skills whose characteristic is DEX per the skill packages table."""

    def test_flyer_is_dex(self):
        assert character_skills.Flyer in _DEX_SKILLS

    def test_stealth_is_dex(self):
        assert character_skills.Stealth in _DEX_SKILLS

    def test_drive_is_dex(self):
        assert character_skills.Drive in _DEX_SKILLS

    def test_pilot_is_not_whole_skill_dex(self):
        assert character_skills.Pilot not in _DEX_SKILLS

    def test_admin_not_dex(self):
        assert character_skills.Admin not in _DEX_SKILLS

    def test_recon_not_dex(self):
        assert character_skills.Recon not in _DEX_SKILLS


class TestBrainSoftware:
    """Non-skill brain software consuming bandwidth (e.g. Universal Translator)."""

    def test_fields(self):
        sw = BrainSoftware(name='Universal Translator', bandwidth=3, tl=12, cost=25000.0)
        assert sw.name == 'Universal Translator'
        assert sw.bandwidth == 3
        assert sw.tl == 12
        assert sw.cost == 25000.0

    def test_defaults(self):
        sw = BrainSoftware(name='Minimal', bandwidth=1)
        assert sw.tl == 0
        assert sw.cost == 0.0

    def test_frozen(self):
        sw = BrainSoftware(name='X', bandwidth=1)
        import pytest

        with pytest.raises(Exception):
            setattr(sw, 'bandwidth', 2)

    def test_json_roundtrip(self):
        sw = BrainSoftware(name='Universal Translator', bandwidth=3, tl=12, cost=25000.0)
        restored = BrainSoftware.model_validate_json(sw.model_dump_json())
        assert restored == sw


class TestPrimitivePackageSkills:
    """refs/robot/35_skill_packages.md — Primitive brain package skill table."""

    @pytest.mark.parametrize(
        'function, expected_grants',
        [
            ('clean', (SkillGrant(_skill(RobotProfession, 'domestic_cleaner'), 2),)),
            ('alert', (SkillGrant(Recon(), 0),)),
            ('homing', (SkillGrant(Weapon(), 1),)),
            ('none', ()),
        ],
    )
    def test_primitive_package_skills(self, function, expected_grants):
        assert primitive_package_skills(function) == expected_grants

    def test_evade_has_two_skills(self):
        skills = primitive_package_skills('evade')
        assert SkillGrant(character_skills.Athletics(dexterity=Level(value=1)), 1) in skills
        assert SkillGrant(character_skills.Stealth(), 2) in skills
