"""Tests for SkillGrant and skill package helpers.

refs/robot/35_skill_packages.md — Primitive brain package table.
"""

from inspect import isclass

from pydantic import ValidationError
import pytest

from ceres.character.domain import skills as character_skills
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import (
    Electronics,
    Level,
    Recon,
    Steward,
    field_for_spec,
)
from ceres.make.robot.skills import (
    BrainSoftware,
    RobotProfession,
    SkillGrant,
    SkillPackage,
    Weapon,
    primitive_package_skills,
)

# Standard Skill Packages table — refs/robot/35_skill_packages.md
# Columns: (skill_class, min_tl, base_bandwidth, characteristic, base_cost_cr)
# characteristic: Chars.INT/DEX/STR, or None = varies by speciality
# cost at level N = base_cost × 10^N
_STANDARD_SKILL_PACKAGES = [
    (character_skills.Admin, 8, 0, Chars.INT, 100),
    (character_skills.Advocate, 10, 0, Chars.INT, 500),
    (character_skills.Animals, 9, 0, None, 200),
    (character_skills.ArtSkill, 10, 0, Chars.INT, 500),
    (character_skills.Astrogation, 12, 1, Chars.INT, 500),
    (character_skills.Athletics, 8, 0, None, 100),
    (character_skills.Broker, 10, 0, Chars.INT, 200),
    (character_skills.Carouse, 11, 1, Chars.INT, 500),
    (character_skills.Deception, 13, 1, Chars.INT, 1000),
    (character_skills.Diplomat, 10, 1, Chars.INT, 500),
    (character_skills.Drive, 8, 0, Chars.DEX, 100),
    (character_skills.Electronics, 8, 0, Chars.INT, 100),
    (character_skills.Engineer, 9, 0, Chars.INT, 200),
    (character_skills.Explosives, 8, 0, Chars.INT, 100),
    (character_skills.Flyer, 8, 0, Chars.DEX, 100),
    (character_skills.Gambler, 10, 0, Chars.INT, 500),
    (character_skills.GunCombat, 8, 0, Chars.DEX, 100),
    (character_skills.Gunner, 8, 0, None, 100),
    (character_skills.HeavyWeapons, 8, 0, Chars.DEX, 100),
    (character_skills.Investigate, 11, 1, Chars.INT, 500),
    (character_skills.LanguageSkill, 9, 0, Chars.INT, 200),
    (character_skills.Leadership, 13, 1, Chars.INT, 1000),
    (character_skills.Mechanic, 8, 0, Chars.INT, 100),
    (character_skills.Medic, 9, 0, Chars.INT, 200),
    (character_skills.Melee, 8, 0, Chars.DEX, 100),
    (character_skills.Navigation, 8, 0, Chars.INT, 100),
    (character_skills.Persuade, 11, 1, Chars.INT, 500),
    (character_skills.Pilot, 8, 0, None, 100),
    (character_skills.ProfessionSkill, 9, 0, Chars.INT, 200),
    (character_skills.Recon, 10, 0, Chars.INT, 500),
    (character_skills.ScienceSkill, 9, 0, Chars.INT, 200),
    (character_skills.Seafarer, 8, 0, None, 100),
    (character_skills.Stealth, 10, 0, Chars.DEX, 500),
    (character_skills.Steward, 8, 0, Chars.INT, 100),
    (character_skills.Streetwise, 13, 1, Chars.INT, 1000),
    (character_skills.Survival, 10, 0, Chars.INT, 200),
    (character_skills.Tactics, 8, 0, Chars.INT, 100),
]

_STANDARD_SKILL_PACKAGE_DICT = {
    skill_class: (tl, bw, char, cost) for (skill_class, tl, bw, char, cost) in _STANDARD_SKILL_PACKAGES
}

# Per-speciality characteristic overrides for variable-char skills (None = no robot char).
_STANDARD_SKILL_VARYING_CHAR: dict[object, dict[str, Chars | None]] = {
    character_skills.Animals: {'Handling': Chars.DEX, 'Training': Chars.INT, 'Veterinary': Chars.INT},
    character_skills.Athletics: {'Strength': Chars.STR, 'Dexterity': Chars.DEX, 'Endurance': None},
    character_skills.Gunner: {'Turret': Chars.DEX, 'Ortillery': Chars.INT, 'Screen': Chars.DEX, 'Capital': Chars.INT},
    character_skills.Pilot: {'Small Craft': Chars.DEX, 'Spacecraft': Chars.DEX, 'Capital Ships': Chars.INT},
    character_skills.Seafarer: {
        'Ocean Ships': Chars.INT,
        'Personal': Chars.DEX,
        'Sail': Chars.DEX,
        'Submarine': Chars.INT,
    },
}

_SIMPLE_SKILLS = [skill for skill, *_ in _STANDARD_SKILL_PACKAGES if isclass(skill) and 'level' in skill.model_fields]

_SPECIALISATION_SKILLS = [
    skill for skill, *_ in _STANDARD_SKILL_PACKAGES if isclass(skill) and 'level' not in skill.model_fields
]

_BROAD_SIMPLE_SKILLS = character_skills._skill_classes(character_skills.LanguageSkill)

_BROAD_SPECIALISATION_SKILLS = {
    character_skills.ArtSkill: character_skills._skill_classes(character_skills.ArtSkill),
    character_skills.ScienceSkill: character_skills._skill_classes(character_skills.ScienceSkill),
    character_skills.ProfessionSkill: character_skills._skill_classes(character_skills.ProfessionSkill),
}


def _skill(skill_cls, field_name: str = 'level', value: int = 1):
    skill = skill_cls()
    getattr(skill, field_name).set(value)
    return skill


class StubBot:
    def __init__(self) -> None:
        self.characteristics: dict[Chars, int] = {Chars.STR: 7, Chars.DEX: 7, Chars.INT: 7}


class TestStandardSkills:
    def test_skills_no_specialisation_0(self):
        for skill_cls in _SIMPLE_SKILLS:
            tl, bw, _, cost = _STANDARD_SKILL_PACKAGE_DICT[skill_cls]
            pkg = SkillPackage(skill=_skill(skill_cls, 'level', 0))
            assert pkg.tl == tl
            assert pkg.bandwidth == bw
            assert pkg.cost == cost
            assert pkg.display_labels(StubBot().characteristics) == [f'{skill_cls.name()} 0']

    def test_skills_no_specialisation_1(self):
        better = {Chars.STR: 9, Chars.DEX: 9, Chars.INT: 9}
        for skill_cls in _SIMPLE_SKILLS:
            tl, bw, _, cost = _STANDARD_SKILL_PACKAGE_DICT[skill_cls]
            pkg = SkillPackage(skill=_skill(skill_cls, 'level', 1))
            assert pkg.tl == tl
            assert pkg.bandwidth == bw + 1
            assert pkg.cost == cost * 10
            assert pkg.display_labels(better) == [f'{skill_cls.name()} 2']

    def test_skills_specialisation(self):
        for skill_cls in _SPECIALISATION_SKILLS:
            _, _, char, _ = _STANDARD_SKILL_PACKAGE_DICT[skill_cls]
            for speci in skill_cls.specialities():
                spec_char = char if char is not None else _STANDARD_SKILL_VARYING_CHAR[skill_cls][speci]
                if spec_char is None:
                    continue
                pkg = SkillPackage(skill=_skill(skill_cls, field_for_spec(skill_cls, speci), 1))
                assert pkg.display_labels(StubBot().characteristics) == [f'{skill_cls.name()} ({speci}) 1']

    def test_broad_skills_no_specialisation_2(self):
        tl, bw, _, cost = _STANDARD_SKILL_PACKAGE_DICT[character_skills.LanguageSkill]
        better = {Chars.STR: 9, Chars.DEX: 9, Chars.INT: 9}
        for skill_cls in _BROAD_SIMPLE_SKILLS:
            pkg = SkillPackage(skill=_skill(skill_cls, 'level', 2))
            assert pkg.tl == tl
            assert pkg.bandwidth == bw + 2
            assert pkg.cost == cost * 100
            assert pkg.display_labels(better) == [f'{skill_cls.name()} 3']

    def test_broad_skills_specialisation(self):
        for broad, skills in _BROAD_SPECIALISATION_SKILLS.items():
            _, _, char, _ = _STANDARD_SKILL_PACKAGE_DICT[broad]
            for skill_cls in skills:
                for speci in skill_cls.specialities():
                    spec_char = char if char is not None else _STANDARD_SKILL_VARYING_CHAR[skill_cls][speci]
                    if spec_char is None:
                        continue
                    pkg = SkillPackage(skill=_skill(skill_cls, field_for_spec(skill_cls, speci), 1))
                    assert pkg.display_labels(StubBot().characteristics) == [f'{skill_cls.name()} ({speci}) 1']

    def test_smart_engineer_all_specs_at_same_level(self):
        # INT=9 → DM+1; Engineer() level-0 all specs → effective 0+1=1 each → compact to (All) 1
        pkg = SkillPackage(skill=character_skills.Engineer())
        assert pkg.display_labels({Chars.INT: 9}) == ['Engineer (All) 1']

    def test_smart_power_engineer_specs_differ(self):
        # Power spec at level 1 + INT DM+1 = 2; others at 0+1=1 → not all equal → list individually
        pkg = SkillPackage(skill=character_skills.Engineer(power=Level(value=1)))
        assert sorted(pkg.display_labels({Chars.INT: 9})) == sorted(
            ['Engineer (Power) 2', 'Engineer (J-Drive) 1', 'Engineer (M-Drive) 1', 'Engineer (Life Support) 1']
        )

    def test_animals_all_implied_familiarity_neutral_dm(self):
        # All Animals specialities at 0, all DMs 0 → all equal → 'Animals 0' not '(All) 0'
        pkg = SkillPackage(skill=character_skills.Animals())
        assert pkg.display_labels(StubBot().characteristics) == ['Animals 0']

    def test_animals_all_implied_familiarity_high_dms(self):
        # Animals level-0: Handling DEX12→DM+2=2, Training INT9→DM+1=1, Veterinary INT9→DM+1=1
        pkg = SkillPackage(skill=character_skills.Animals())
        assert sorted(pkg.display_labels({Chars.STR: 7, Chars.DEX: 12, Chars.INT: 9})) == sorted(
            ['Animals (Handling) 2', 'Animals (Training) 1', 'Animals (Veterinary) 1']
        )


class TestSkillPackage:
    def test_level_0_simple_skill(self):
        pkg = SkillPackage(skill=Steward())
        assert pkg.level == 0
        assert pkg.bandwidth == 0
        assert pkg.name_text == 'Steward'

    def test_level_2_simple_skill(self):
        pkg = SkillPackage(skill=Steward(level=Level(value=2)))
        assert pkg.level == 2
        assert pkg.bandwidth == 2
        assert pkg.cost == 100.0 * 100

    def test_speciality_skill_level_derived_from_active_field(self):
        pkg = SkillPackage(skill=Electronics(remote_ops=Level(value=1)))
        assert pkg.level == 1
        assert pkg.bandwidth == 1
        assert pkg.name_text == 'Electronics (Remote Ops)'

    def test_level_0_speciality_skill_grants_all(self):
        pkg = SkillPackage(skill=Electronics(remote_ops=Level(value=1)))
        # level is 1, so grants_all_specialities is False
        assert not pkg.grants_all_specialities()
        assert pkg.name_text == 'Electronics (Remote Ops)'

    def test_level_0_speciality_no_active_field_grants_all(self):
        pkg = SkillPackage(skill=Electronics())
        assert pkg.level == 0
        assert pkg.grants_all_specialities()
        assert pkg.name_text == 'Electronics (All)'

    def test_roundtrip_json(self):
        pkg = SkillPackage(skill=Steward(level=Level(value=2)))
        restored = SkillPackage.model_validate_json(pkg.model_dump_json())
        assert restored == pkg
        assert restored.name_text == 'Steward'

    def test_group_skill_cost_uses_union_key(self):
        # RoboticScience is a subskill of ScienceSkill; base cost Cr200 (via group key).
        pkg = SkillPackage(skill=character_skills.RoboticScience(robotics=Level(value=2)))
        assert pkg.cost == 20_000.0  # 200 × 10²

    def test_robot_specific_profession_cost_uses_class_key(self):
        pkg = SkillPackage(skill=RobotProfession(domestic_cleaner=Level(value=2)))
        assert pkg.cost == 20_000.0  # 200 × 10²


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

        with pytest.raises(ValidationError):
            sw.bandwidth = 2

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
