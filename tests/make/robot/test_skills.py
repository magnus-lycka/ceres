"""Tests for SkillGrant and skill package helpers.

refs/robot/35_skill_packages.md — Primitive brain package table.
"""

import pytest

from ceres.make.robot.skills import SkillGrant, SkillPackage, primitive_package_skills


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
