"""Tests for skill package helpers.

refs/robot/35_skill_packages.md — Primitive brain package table.
"""

from inspect import isclass
from typing import get_args

from pydantic import ValidationError
import pytest

from ceres.character.domain import skills as character_skills
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import level_fields, speciality_label
from ceres.make.robot.skills import (
    Animals,
    AnyRobotSkill,
    BrainSoftware,
    Engineer,
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

# Per-speciality characteristic overrides for variable-char skills (None = no robot characteristic).
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


def _build_char_to_facade() -> dict[type, type]:
    facade_types = get_args(get_args(AnyRobotSkill)[0])
    return {cls._char_cls: cls for cls in facade_types if getattr(cls, '_char_cls', None) is not None}


_CHAR_TO_FACADE = _build_char_to_facade()


_DM0: dict[Chars, int] = {}  # all DMs zero — used where no characteristic bonus applies


class TestStandardSkills:
    def test_skills_no_specialisation_0(self):
        for skill_cls in _SIMPLE_SKILLS:
            tl, bw, _, cost = _STANDARD_SKILL_PACKAGE_DICT[skill_cls]
            facade_cls = _CHAR_TO_FACADE[skill_cls]
            pkg = facade_cls(level=0)
            assert pkg.tl == tl
            assert pkg.bandwidth == bw
            assert pkg.cost == cost
            assert pkg.display_entries(_DM0) == {skill_cls.name(): 0}

    def test_skills_no_specialisation_1(self):
        all_plus1 = {Chars.STR: 1, Chars.DEX: 1, Chars.INT: 1}
        for skill_cls in _SIMPLE_SKILLS:
            tl, bw, _, cost = _STANDARD_SKILL_PACKAGE_DICT[skill_cls]
            facade_cls = _CHAR_TO_FACADE[skill_cls]
            pkg = facade_cls(level=1)
            assert pkg.tl == tl
            assert pkg.bandwidth == bw + 1
            assert pkg.cost == cost * 10
            assert pkg.display_entries(all_plus1) == {skill_cls.name(): 2}

    def test_skills_specialisation(self):
        for skill_cls in _SPECIALISATION_SKILLS:
            _, _, char, _ = _STANDARD_SKILL_PACKAGE_DICT[skill_cls]
            facade_cls = _CHAR_TO_FACADE[skill_cls]
            instance = skill_cls()
            for field in level_fields(skill_cls):
                speci = speciality_label(instance, field)
                spec_char = char if char is not None else _STANDARD_SKILL_VARYING_CHAR[skill_cls].get(speci)
                if spec_char is None:
                    continue
                pkg = facade_cls(**{field: 1})
                assert pkg.display_entries(_DM0) == {f'{skill_cls.name()} ({speci})': 1}

    def test_broad_skills_no_specialisation_2(self):
        tl, bw, _, cost = _STANDARD_SKILL_PACKAGE_DICT[character_skills.LanguageSkill]
        all_plus1 = {Chars.STR: 1, Chars.DEX: 1, Chars.INT: 1}
        for skill_cls in _BROAD_SIMPLE_SKILLS:
            facade_cls = _CHAR_TO_FACADE[skill_cls]
            pkg = facade_cls(level=2)
            assert pkg.tl == tl
            assert pkg.bandwidth == bw + 2
            assert pkg.cost == cost * 100
            assert pkg.display_entries(all_plus1) == {skill_cls.name(): 3}

    def test_broad_skills_specialisation(self):
        for skills in _BROAD_SPECIALISATION_SKILLS.values():
            for skill_cls in skills:
                facade_cls = _CHAR_TO_FACADE[skill_cls]
                instance = skill_cls()
                for field in level_fields(skill_cls):
                    speci = speciality_label(instance, field)
                    pkg = facade_cls(**{field: 1})
                    assert pkg.display_entries(_DM0) == {f'{skill_cls.name()} ({speci})': 1}

    def test_smart_engineer_all_specs_at_same_level(self):
        # Engineer() level-0 all specs; INT DM+1 → each spec at 1 → compact to (All) 1
        pkg = Engineer()
        assert pkg.display_entries({Chars.INT: 1}) == {'Engineer (All)': 1}

    def test_smart_power_engineer_specs_differ(self):
        # Power at 1 + INT DM+1 = 2; others at 0+1=1 → not all equal → list individually
        pkg = Engineer(power=1)
        assert pkg.display_entries({Chars.INT: 1}) == {
            'Engineer (Power)': 2,
            'Engineer (J-Drive)': 1,
            'Engineer (M-Drive)': 1,
            'Engineer (Life Support)': 1,
        }

    def test_animals_all_implied_familiarity_neutral_dm(self):
        # All Animals specialities at 0, all DMs 0 → all equal → 'Animals 0'
        pkg = Animals()
        assert pkg.display_entries(_DM0) == {'Animals': 0}

    def test_animals_all_implied_familiarity_high_dms(self):
        # Animals: Handling DEX DM+2=2, Training INT DM+1=1, Veterinary INT DM+1=1
        pkg = Animals()
        assert pkg.display_entries({Chars.DEX: 2, Chars.INT: 1}) == {
            'Animals (Handling)': 2,
            'Animals (Training)': 1,
            'Animals (Veterinary)': 1,
        }


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
        'function, expected',
        [
            ('clean', {'Profession (Domestic Cleaner)': 2}),
            ('alert', {'Recon': 0}),
            ('homing', {'Weapon': 1}),
            ('none', {}),
        ],
    )
    def test_primitive_package_skills(self, function, expected):
        assert primitive_package_skills(function) == expected

    def test_evade_has_two_skills(self):
        skills = primitive_package_skills('evade')
        assert skills.get('Athletics (Dexterity)') == 1
        assert skills.get('Stealth') == 2
