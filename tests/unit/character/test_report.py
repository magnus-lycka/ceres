"""Unit tests for character/report.py — _career_rank_line and _build_stat_block_context."""

from ceres.character.domain.spec import StatBlockSpec
from ceres.character.report import _build_stat_block_context, _career_rank_line


def _spec(**kwargs) -> StatBlockSpec:
    return StatBlockSpec(name='Test NPC', **kwargs)


class TestCareerRankLine:
    def test_no_career_returns_dash(self):
        assert _career_rank_line(_spec()) == '—'

    def test_career_only(self):
        assert _career_rank_line(_spec(career='Navy')) == 'Navy'

    def test_career_with_assignment(self):
        assert _career_rank_line(_spec(career='Navy', assignment='Engineer')) == 'Navy (Engineer)'

    def test_career_with_rank(self):
        assert _career_rank_line(_spec(career='Army', rank=3)) == 'Army / Rank 3'

    def test_career_with_terms_singular(self):
        assert _career_rank_line(_spec(career='Scouts', terms=1)) == 'Scouts / 1 term'

    def test_career_with_terms_plural(self):
        assert _career_rank_line(_spec(career='Scouts', terms=2)) == 'Scouts / 2 terms'

    def test_all_fields(self):
        result = _career_rank_line(_spec(career='Navy', assignment='Pilot', rank=4, terms=3))
        assert result == 'Navy (Pilot) / Rank 4 / 3 terms'


class TestBuildStatBlockContext:
    def test_name_in_context(self):
        ctx = _build_stat_block_context(_spec(career='Merchant'))
        assert ctx['name'] == 'Test NPC'

    def test_notes_from_spec_when_not_overridden(self):
        ctx = _build_stat_block_context(_spec(notes='My note'))
        assert ctx['notes'] == 'My note'

    def test_notes_override_takes_precedence(self):
        ctx = _build_stat_block_context(_spec(notes='Original'), notes='Override')
        assert ctx['notes'] == 'Override'

    def test_cash_in_equipment(self):
        ctx = _build_stat_block_context(_spec(cash=5_000))
        assert 'Cr5,000' in ctx['equipment']
