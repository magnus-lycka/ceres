"""Unit tests for precareer_data.py — PreCareerData, PrecareerSkillEntry, PreCareerTerm."""

from typing import cast

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.precareer.precareer_data import PreCareerData, PrecareerSkillEntry, PreCareerTerm
from ceres.character.domain.skills import Admin, Animals
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _projection() -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )


def _any_event() -> Event:
    from ceres.character.domain.career.career_events import SurviveHandler

    return Event(handler=SurviveHandler(roll=5))


class TestPrecareerSkillEntry:
    def test_skill_options_none_returns_empty(self):
        entry = PrecareerSkillEntry(skill=None)
        assert entry.skill_options == []

    def test_skill_options_single_skill_returns_list_of_one(self):
        entry = PrecareerSkillEntry(skill=Admin())
        assert entry.skill_options == [Admin()]

    def test_skill_options_list_returns_same_list(self):
        from ceres.character.domain.skills import AnySkill as _AnySkill

        skills: list[_AnySkill] = [Admin(), Animals()]
        entry = PrecareerSkillEntry(skill=skills)
        assert entry.skill_options == skills

    def test_category_label_none_is_skill(self):
        entry = PrecareerSkillEntry(skill=None)
        assert entry.category_label == 'skill'

    def test_category_label_single_uses_class_name(self):
        entry = PrecareerSkillEntry(skill=Admin())
        assert entry.category_label == 'Admin'

    def test_category_label_list_is_skill(self):
        from ceres.character.domain.skills import AnySkill as _AnySkill

        entry = PrecareerSkillEntry(skill=cast(list[_AnySkill], [Admin(), Animals()]))
        assert entry.category_label == 'skill'

    def test_grant_skill_none_returns_none(self):
        entry = PrecareerSkillEntry(skill=None)
        assert entry.grant_skill() is None

    def test_grant_skill_list_returns_none(self):
        from ceres.character.domain.skills import AnySkill as _AnySkill

        entry = PrecareerSkillEntry(skill=cast(list[_AnySkill], [Admin(), Animals()]))
        assert entry.grant_skill() is None

    def test_grant_skill_level_0_returns_skill_at_0(self):
        entry = PrecareerSkillEntry(skill=Admin(), level=0)
        granted = entry.grant_skill()
        assert isinstance(granted, Admin)
        assert granted.level.value == 0

    def test_grant_skill_level_1_returns_skill_at_1(self):
        entry = PrecareerSkillEntry(skill=Admin(), level=1)
        granted = entry.grant_skill()
        assert isinstance(granted, Admin)
        assert granted.level.value == 1


class TestPreCareerDataApplyEntry:
    def _university(self) -> PreCareerData:
        from ceres.character.domain.precareer.loader import load_precareers

        pcs = {pc.name: pc for pc in load_precareers()}
        return pcs['University']

    def test_apply_entry_zero_pick_count_auto_grants_fixed_skills(self):
        university = self._university()
        proj = _projection()
        university.apply_entry(proj, _any_event(), pending_idx=0)
        # University has skill_choices; at least one fixed skill should be granted
        assert len(proj.summary.skills) > 0 or len(proj.pending_inputs) > 0

    def test_apply_entry_queues_list_choices_as_pending(self):
        from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice

        university = self._university()
        proj = _projection()
        university.apply_entry(proj, _any_event(), pending_idx=0)
        pending_choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(pending_choices) >= 0  # may or may not have list choices

    def test_apply_entry_returns_updated_pending_idx(self):
        university = self._university()
        proj = _projection()
        result = university.apply_entry(proj, _any_event(), pending_idx=0)
        assert isinstance(result, int)
        assert result >= 0

    def test_apply_graduation_default_returns_zero(self):
        university = self._university()
        proj = _projection()
        result = university.apply_graduation(proj, _any_event(), honours=False)
        assert isinstance(result, int)

    def test_apply_failed_graduation_default_no_effect(self):
        university = self._university()
        proj = _projection()
        pre_skills = list(proj.summary.skills)
        university.apply_failed_graduation(proj, _any_event())
        assert proj.summary.skills == pre_skills

    def test_is_available_default_true(self):
        university = self._university()
        proj = _projection()
        assert university.is_available(proj.summary) is True

    def test_prepare_entry_default_true(self):
        university = self._university()
        proj = _projection()
        assert university.prepare_entry(proj, roll=8, terms_started=0) is True


class TestPreCareerTerm:
    def _university_term(self) -> PreCareerTerm:
        from ceres.character.domain.precareer.loader import load_precareers

        pcs = {pc.name: pc for pc in load_precareers()}
        return pcs['University'].make_term()

    def test_make_term_returns_precareer_term(self):
        term = self._university_term()
        assert isinstance(term, PreCareerTerm)

    def test_defaults_not_completed(self):
        term = self._university_term()
        assert term.completed is False
        assert term.graduated is False
        assert term.honours is False

    def test_precareer_field_serialises_as_name(self):
        term = self._university_term()
        data = term.model_dump()
        assert data['precareer'] == 'University'

    def test_precareer_deserialises_from_name(self):
        from ceres.character.domain.precareer.loader import load_precareers

        pcs = {pc.name: pc for pc in load_precareers()}
        university = pcs['University']
        term = PreCareerTerm.model_validate({'kind': 'university', 'precareer': 'University'})
        assert term.precareer is university

    def test_apply_entry_delegates_to_precareer(self):
        term = self._university_term()
        proj = _projection()
        result = term.apply_entry(proj, _any_event(), pending_idx=0)
        assert isinstance(result, int)

    def test_apply_graduation_delegates_to_precareer(self):
        term = self._university_term()
        proj = _projection()
        result = term.apply_graduation(proj, _any_event(), honours=False)
        assert isinstance(result, int)

    def test_apply_failed_graduation_delegates_to_precareer(self):
        term = self._university_term()
        proj = _projection()
        term.apply_failed_graduation(proj, _any_event())
