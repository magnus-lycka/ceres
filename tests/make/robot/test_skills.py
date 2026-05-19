"""Tests for SkillGrant and skill package helpers.

refs/robot/35_skill_packages.md — Primitive brain package table.
"""

import pytest

from ceres.make.robot.skills import _DEX_SKILLS, BrainSoftware, SkillGrant, SkillPackage, primitive_package_skills


class TestSkillGrant:
    def test_str_with_level(self):
        assert str(SkillGrant('Electronics (remote ops)', 1)) == 'Electronics (remote ops) 1'

    def test_str_zero_level(self):
        assert str(SkillGrant('Recon', 0)) == 'Recon 0'

    def test_equality(self):
        assert SkillGrant('Recon', 1) == SkillGrant('Recon', 1)

    def test_inequality_level(self):
        assert SkillGrant('Recon', 0) != SkillGrant('Recon', 1)

    def test_inequality_name(self):
        assert SkillGrant('Recon', 0) != SkillGrant('Electronics', 0)


class TestSkillPackage:
    def test_fields(self):
        pkg = SkillPackage(name='Electronics (remote ops)', level=1, bandwidth=1)
        assert pkg.name == 'Electronics (remote ops)'
        assert pkg.level == 1
        assert pkg.bandwidth == 1

    def test_roundtrip_json(self):
        pkg = SkillPackage(name='Steward', level=2, bandwidth=2)
        restored = SkillPackage.model_validate_json(pkg.model_dump_json())
        assert restored == pkg


class TestSkillPackageGrantName:
    """Level-0 speciality packages display as (All); level 1+ keep their speciality."""

    def test_level_0_specialty_becomes_all(self):
        pkg = SkillPackage(name='Electronics (Remote Ops)', level=0, bandwidth=0)
        assert pkg.grant_name() == 'Electronics (All)'

    def test_level_1_specialty_preserved(self):
        pkg = SkillPackage(name='Electronics (Remote Ops)', level=1, bandwidth=1)
        assert pkg.grant_name() == 'Electronics (Remote Ops)'

    def test_level_0_no_specialty_unchanged(self):
        pkg = SkillPackage(name='Admin', level=0, bandwidth=0)
        assert pkg.grant_name() == 'Admin'

    def test_level_2_specialty_preserved(self):
        pkg = SkillPackage(name='Science (Robotics)', level=2, bandwidth=2)
        assert pkg.grant_name() == 'Science (Robotics)'

    def test_level_0_engineer_specialty_becomes_all(self):
        pkg = SkillPackage(name='Engineer (J-Drive)', level=0, bandwidth=0)
        assert pkg.grant_name() == 'Engineer (All)'

    def test_level_0_flyer_specialty_becomes_all(self):
        pkg = SkillPackage(name='Flyer (Grav)', level=0, bandwidth=0)
        assert pkg.grant_name() == 'Flyer (All)'


class TestDexSkillsSet:
    """_DEX_SKILLS identifies skills whose characteristic is DEX per the skill packages table."""

    def test_flyer_is_dex(self):
        assert 'Flyer' in _DEX_SKILLS

    def test_stealth_is_dex(self):
        assert 'Stealth' in _DEX_SKILLS

    def test_drive_is_dex(self):
        assert 'Drive' in _DEX_SKILLS

    def test_pilot_is_dex(self):
        assert 'Pilot' in _DEX_SKILLS

    def test_admin_not_dex(self):
        assert 'Admin' not in _DEX_SKILLS

    def test_recon_not_dex(self):
        assert 'Recon' not in _DEX_SKILLS


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
            sw.bandwidth = 2  # type: ignore[misc]

    def test_json_roundtrip(self):
        sw = BrainSoftware(name='Universal Translator', bandwidth=3, tl=12, cost=25000.0)
        restored = BrainSoftware.model_validate_json(sw.model_dump_json())
        assert restored == sw


class TestPrimitivePackageSkills:
    """refs/robot/35_skill_packages.md — Primitive brain package skill table."""

    @pytest.mark.parametrize(
        'function, expected_grants',
        [
            ('clean', (SkillGrant('Profession (domestic cleaner)', 2),)),
            ('alert', (SkillGrant('Recon', 0),)),
            ('homing', (SkillGrant('Weapon', 1),)),
            ('none', ()),
        ],
    )
    def test_primitive_package_skills(self, function, expected_grants):
        assert primitive_package_skills(function) == expected_grants

    def test_evade_has_two_skills(self):
        skills = primitive_package_skills('evade')
        assert SkillGrant('Athletics (dexterity)', 1) in skills
        assert SkillGrant('Stealth', 2) in skills
