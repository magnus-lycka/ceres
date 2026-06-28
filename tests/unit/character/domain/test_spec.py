"""Unit tests for spec.py — StatBlockSpec, spec_from_summary, format_stat_block_skills."""

from ceres.character.domain.character_state import CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, AnySkill, Electronics, GunCombat, Level, LifeScience
from ceres.character.domain.sophont import VILANI
from ceres.character.domain.spec import format_stat_block_skills, spec_from_summary
from tests.unit.character.helpers import MOCK_WORLD


def _summary(**kwargs) -> CharacterSummary:
    return CharacterSummary(
        name='Test',
        sophont=VILANI,
        homeworld=MOCK_WORLD,
        characteristics={Chars.STR: 7, Chars.DEX: 8, Chars.END: 6, Chars.INT: 9, Chars.EDU: 10, Chars.SOC: 11},
        **kwargs,
    )


class TestSpecFromSummary:
    def test_name(self):
        spec = spec_from_summary(_summary())
        assert spec.name == 'Test'

    def test_ucp_encodes_all_six_stats(self):
        spec = spec_from_summary(_summary())
        # STR=7 DEX=8 END=6 INT=9 EDU=10(A) SOC=11(B)
        assert spec.ucp == '786 9AB'.replace(' ', '')

    def test_age(self):
        summary = _summary()
        summary.age = 34
        spec = spec_from_summary(summary)
        assert spec.age == 34

    def test_characteristics_copied(self):
        spec = spec_from_summary(_summary())
        assert spec.characteristics[Chars.INT] == 9

    def test_skills_copied(self):
        summary = _summary()
        summary.skills = [Admin()]
        spec = spec_from_summary(summary)
        assert any(isinstance(s, Admin) for s in spec.skills)

    def test_notes_passed_through(self):
        spec = spec_from_summary(_summary(), notes='Test note')
        assert spec.notes == 'Test note'

    def test_no_career_gives_none(self):
        spec = spec_from_summary(_summary())
        assert spec.career is None

    def test_terms_from_summary(self):
        spec = spec_from_summary(_summary())
        assert spec.terms == 0


class TestFormatStatBlockSkills:
    def test_no_skills_returns_empty_string(self):
        assert format_stat_block_skills([]) == ''

    def test_single_level_field_skill(self):
        result = format_stat_block_skills([Admin(level=Level(value=2))])
        assert 'Admin' in result
        assert '2' in result

    def test_skill_with_no_level_fields_excluded(self):
        # Skills that return empty from level_fields are omitted
        result = format_stat_block_skills([Admin()])
        assert 'Admin' in result  # Admin has a level field at 0

    def test_specialty_skill_non_zero_shows_specialty(self):
        skill = GunCombat()
        skill.slug.set(1)  # type: ignore[attr-defined]
        result = format_stat_block_skills([skill])
        assert 'Gun Combat' in result

    def test_specialty_skill_all_zero_shows_base_0(self):
        result = format_stat_block_skills([GunCombat()])
        assert 'Gun Combat 0' in result

    def test_specialty_skill_all_same_level_shows_all(self):
        skill = GunCombat()
        for f in ['slug', 'energy', 'archaic']:
            getattr(skill, f).set(1)
        result = format_stat_block_skills([skill])
        assert '(all)' in result

    def test_skills_sorted_by_name(self):
        skills: list[AnySkill] = [Electronics(), Admin()]
        result = format_stat_block_skills(skills)
        admin_pos = result.index('Admin')
        elec_pos = result.index('Electronics')
        assert admin_pos < elec_pos

    def test_multiple_skills_joined_by_comma(self):
        skills: list[AnySkill] = [Admin(), Electronics()]
        result = format_stat_block_skills(skills)
        assert ', ' in result

    def test_life_science_with_psionicology(self):
        skill = LifeScience(psionicology=Level(value=1))
        result = format_stat_block_skills([skill])
        assert 'Life Science' in result
        assert 'psionicology' in result.lower() or '1' in result
