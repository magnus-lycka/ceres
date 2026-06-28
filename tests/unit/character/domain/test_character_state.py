"""Unit tests for character_state — CharacterSummary and CharacterProjection mechanics."""

import pytest

from ceres.character.domain.career import ARMY
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.career.career_events import SurviveHandler
from ceres.character.domain.character_state import (
    CharacterProjection,
    CharacterSummary,
    diff_summaries,
)
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Drive, Level, Medic
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _summary(**kwargs) -> CharacterSummary:
    return CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs)


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(character_id=1, summary=_summary(**kwargs))


def _army_term(muster_out=None) -> CareerTerm:
    return CareerTerm(career=ARMY, assignment=ARMY.assignment('Support'), muster_out=muster_out)


def _any_event() -> Event:
    return Event(handler=SurviveHandler(roll=5))


class TestCurrentCareer:
    def test_returns_none_with_no_terms(self):
        assert _summary().current_career is None

    def test_returns_none_when_muster_out_is_none(self):
        s = _summary()
        s.terms.append(_army_term(muster_out=None))
        assert s.current_career is None

    def test_returns_career_with_active_muster_out(self):
        from ceres.character.domain.career.career_data import MusterOut

        s = _summary()
        s.terms.append(_army_term(muster_out=MusterOut()))
        assert s.current_career == ARMY


class TestLatestCareer:
    def test_returns_current_career_when_active(self):
        from ceres.character.domain.career.career_data import MusterOut

        s = _summary()
        s.terms.append(_army_term(muster_out=MusterOut()))
        assert s.latest_career == ARMY

    def test_returns_last_career_when_no_current(self):
        s = _summary()
        s.terms.append(_army_term(muster_out=None))
        s.last_career = ARMY
        assert s.latest_career == ARMY


class TestCurrentTerm:
    def test_raises_when_no_career_terms(self):
        s = _summary()
        with pytest.raises(ReplayError, match='No current career term'):
            s.current_term()


class TestRankTitle:
    def test_returns_zero_title_when_rank_is_none(self):
        assert _summary().rank_title == ('0', '')

    def test_returns_str_rank_when_no_career_terms(self):
        s = _summary(rank=3)
        assert s.rank_title == ('3', '')


class TestTermsStarted:
    def test_includes_precareer_count(self):
        from ceres.character.domain.precareer.loader import load_precareers

        university = next(p for p in load_precareers() if p.name == 'University')
        s = _summary()
        term = university.make_term()
        term.completed = True
        s.terms.append(term)
        assert s.terms_started_in_pre_and_careers == 1

    def test_precareer_in_progress_counts(self):
        from ceres.character.domain.precareer.loader import load_precareers

        university = next(p for p in load_precareers() if p.name == 'University')
        s = _summary()
        s.terms.append(university.make_term())
        assert s.terms_started_in_pre_and_careers == 1


class TestSkillLevel:
    def test_skill_without_level_field_returns_zero(self):
        from ceres.character.domain.skills import JackOfAllTrades

        s = _summary(skills=[JackOfAllTrades()])
        assert s.skill_level(JackOfAllTrades, 0) == 0


class TestDiff:
    def _base(self) -> CharacterSummary:
        return _summary()

    def test_narrative_additions_appear(self):
        before = self._base()
        after = self._base()
        after.narrative.append('Something happened')
        changes = diff_summaries(before, after)
        assert 'Something happened' in changes

    def test_joined_career_appears(self):
        from ceres.character.domain.career.career_data import MusterOut

        before = self._base()
        after = self._base()
        after.terms.append(_army_term(muster_out=MusterOut()))
        changes = diff_summaries(before, after)
        assert any('Joined Army' in c for c in changes)

    def test_rank_change_appears(self):
        before = self._base()
        after = self._base()
        after.rank = 2
        changes = diff_summaries(before, after)
        assert any('Rank' in c for c in changes)

    def test_forced_stay_appears(self):
        before = self._base()
        before.terms.append(_army_term())
        after = self._base()
        term = _army_term()
        term.forced_stay = True
        after.terms.append(term)
        changes = diff_summaries(before, after)
        assert any('12' in c for c in changes)

    def test_forced_leave_appears(self):
        before = self._base()
        before.terms.append(_army_term())
        after = self._base()
        term = _army_term()
        term.forced_leave = True
        after.terms.append(term)
        changes = diff_summaries(before, after)
        assert any('forced muster out' in c for c in changes)

    def test_characteristic_change_appears(self):
        before = self._base()
        before.characteristics[Chars.STR] = 7
        after = self._base()
        after.characteristics[Chars.STR] = 9
        changes = diff_summaries(before, after)
        assert any('STR 7 → 9' in c for c in changes)

    def test_new_skill_appears(self):
        before = self._base()
        after = self._base()
        after.skills.append(Admin(level=Level(value=1)))
        changes = diff_summaries(before, after)
        assert any('Gained Admin' in c for c in changes)

    def test_skill_increase_appears(self):
        before = self._base()
        before.skills.append(Admin(level=Level(value=1)))
        after = self._base()
        after.skills.append(Admin(level=Level(value=2)))
        changes = diff_summaries(before, after)
        assert any('Admin 1 → 2' in c for c in changes)

    def test_cash_delta_appears(self):
        before = self._base()
        after = self._base()
        after.cash = 5000
        changes = diff_summaries(before, after)
        assert any('Cash +Cr5,000' in c for c in changes)

    def test_empty_when_nothing_changed(self):
        s = _summary()
        assert diff_summaries(s, s) == []


class TestDecreaseCharacteristic:
    def test_psi_removed_when_reaches_zero(self):
        from ceres.character.domain.psionics import Psionics

        proj = _projection(characteristics={Chars.PSI: 1})
        proj.summary.psionics = Psionics()
        proj.decrease_characteristic(Chars.PSI, amount=1)
        assert Chars.PSI not in proj.summary.characteristics
        assert proj.summary.psionics is None


class TestGetCurrentCareer:
    def test_raises_when_no_active_career(self):
        proj = _projection()
        with pytest.raises(ReplayError, match='No active career'):
            proj.get_current_career()


class TestAdjustParoleThreshold:
    def test_does_nothing_when_parole_threshold_is_none(self):
        proj = _projection()
        proj.adjust_parole_threshold(3)  # should not raise
        assert proj.summary.parole_threshold is None

    def test_clamps_to_valid_range(self):
        proj = _projection(parole_threshold=11)
        proj.adjust_parole_threshold(5)  # would go to 16, clamp to 12
        assert proj.summary.parole_threshold == 12


class TestSkillChoices:
    def test_non_specialised_increment_when_at_max(self):
        proj = _projection(skills=[Admin(level=Level(value=4))])
        choices = proj.skill_choices([Admin], level=None)
        assert choices == []

    def test_specialised_level_zero_not_added_twice(self):
        proj = _projection(skills=[Drive()])
        choices = proj.skill_choices([Drive], level=0)
        assert choices == []

    def test_specialised_level_none_increments_field(self):
        proj = _projection(skills=[Drive(wheel=Level(value=1))])
        choices = proj.skill_choices([Drive], level=None)
        assert any(isinstance(c, Drive) for c in choices)


class TestIncrementSkill:
    def test_adds_skill_at_level_1_when_absent(self):
        proj = _projection()
        proj.increment_skill(Admin())
        assert proj.summary.skill_level(Admin, 0) == 1

    def test_increments_existing_non_specialised(self):
        proj = _projection(skills=[Admin(level=Level(value=1))])
        proj.increment_skill(Admin())
        assert proj.summary.skill_level(Admin, 0) == 2

    def test_increments_specialised_wheel(self):
        proj = _projection(skills=[Drive(wheel=Level(value=1))])
        proj.increment_skill(Drive(wheel=Level(value=1)))
        skill = next(s for s in proj.summary.skills if isinstance(s, Drive))
        assert skill.wheel.value == 2


class TestCheckSkillChoice:
    def test_valid_choice_returns_true(self):
        proj = _projection()
        assert proj.check_skill_choice([Admin], level=1, choice=Admin(level=Level(value=1))) is True

    def test_invalid_choice_returns_false(self):
        proj = _projection()
        assert proj.check_skill_choice([Medic], level=1, choice=Admin(level=Level(value=1))) is False


class TestDeserialiseTerms:
    def test_precareer_term_round_trips_via_model_dump_json(self):
        from ceres.character.domain.precareer.loader import load_precareers
        from ceres.character.domain.precareer.precareer_term import PreCareerTerm

        university = next(p for p in load_precareers() if p.name == 'University')
        s = _summary()
        s.terms.append(university.make_term())
        serialised = s.model_dump_json()
        restored = CharacterSummary.model_validate_json(serialised)
        term = restored.current_precareer_term
        assert term is not None
        assert isinstance(term, PreCareerTerm)
        assert term.precareer.name == 'University'

    def test_invalid_term_kind_raises(self):
        from pydantic import ValidationError

        data = _summary().model_dump()
        data['terms'] = [{'kind': 'nonexistent_kind'}]
        with pytest.raises(ValidationError):
            CharacterSummary.model_validate(data)
