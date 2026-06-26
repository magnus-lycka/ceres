"""Unit tests for precareer_events — pending input mechanics and handler helpers."""

import pytest

from ceres.character.domain.career.career_events import SurviveHandler
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_events import (
    PendingPreCareerEvent,
    PendingPreCareerGraduation,
    PendingPreCareerSkillChoice,
    PreCareerEventHandler,
    PreCareerGraduationHandler,
    PreCareerSkillChoiceHandler,
    _conditional_characteristic_dms,
    _expand_skill_to_spec_instances,
)
from ceres.character.domain.skills import Admin, Drive, Level
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


def _any_event() -> Event:
    return Event(handler=SurviveHandler(roll=5))


class TestConditionalCharacteristicDms:
    def test_adds_dm_when_char_meets_threshold(self):
        summary = CharacterSummary(
            name='T',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.EDU: 8},
        )
        result = _conditional_characteristic_dms(summary, {'EDU_8+': 1})
        assert result == 1

    def test_no_dm_when_char_below_threshold(self):
        summary = CharacterSummary(
            name='T',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.EDU: 7},
        )
        result = _conditional_characteristic_dms(summary, {'EDU_8+': 1})
        assert result == 0

    def test_skips_malformed_keys(self):
        summary = CharacterSummary(name='T', sophont=VILANI, homeworld=MOCK_WORLD)
        result = _conditional_characteristic_dms(summary, {'BAD_KEY': 1, 'ALSO_BAD': 2})
        assert result == 0

    def test_accumulates_multiple_matching_dms(self):
        summary = CharacterSummary(
            name='T',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.EDU: 10, Chars.SOC: 9},
        )
        result = _conditional_characteristic_dms(summary, {'EDU_8+': 1, 'SOC_9+': 2})
        assert result == 3


class TestExpandSkillToSpecInstances:
    def test_unspecialised_skill_returns_itself(self):
        skill = Admin(level=Level(value=1))
        result = _expand_skill_to_spec_instances(skill)
        assert len(result) == 1 and isinstance(result[0], Admin)

    def test_specialised_skill_returns_one_instance_per_spec(self):
        skill = Drive()
        result = _expand_skill_to_spec_instances(skill)
        assert len(result) == 5  # hovercraft, mole, track, walker, wheel
        for s in result:
            assert isinstance(s, Drive)


class TestPendingPreCareerSkillChoice:
    def test_event_from_form_parses_skill(self):
        import json

        pending = PendingPreCareerSkillChoice(pending_id=(1, 0), instruction='Choose', level=0, options=[Admin()])
        event = pending.event_from_form({'skill': json.dumps({'kind': 'ADMIN'})})
        assert isinstance(event.handler, PreCareerSkillChoiceHandler)
        assert isinstance(event.handler.skill, Admin)

    def test_input_specs_returns_select(self):
        pending = PendingPreCareerSkillChoice(pending_id=(1, 0), instruction='Choose', level=0, options=[Admin()])
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], Select) and specs[0].name == 'skill'

    def test_level_zero_options_not_expanded(self):
        pending = PendingPreCareerSkillChoice(pending_id=(1, 0), instruction='Choose', level=0, options=[Drive()])
        options = pending._expanded_options()
        assert len(options) == 1 and isinstance(options[0], Drive)

    def test_level_nonzero_specialised_skill_expands(self):
        pending = PendingPreCareerSkillChoice(pending_id=(1, 0), instruction='Choose', level=1, options=[Drive()])
        options = pending._expanded_options()
        assert len(options) == 5


class TestPreCareerSkillChoiceHandler:
    def test_apply_level_zero_grants_skill(self):
        proj = _projection()
        event = _any_event()
        handler = PreCareerSkillChoiceHandler(skill=Admin(level=Level(value=1)))
        handler.apply(proj, event)
        assert proj.summary.skill_level(Admin, 0) == 1

    def test_apply_level_nonzero_increments_skill(self):
        proj = _projection(skills=[Admin(level=Level(value=1))])
        pending = PendingPreCareerSkillChoice(pending_id=(1, 0), instruction='Choose', level=1, options=[Admin()])
        handler = PreCareerSkillChoiceHandler(skill=Admin(level=Level(value=1)))
        handler.apply(proj, _any_event(), fulfilled_pending=pending)
        assert proj.summary.skill_level(Admin, 0) == 2

    def test_apply_records_skill_in_university_pending_skills(self):
        from ceres.character.domain.precareer.loader import precareer_of_type
        from ceres.character.domain.precareer.precareer_term import UniversityTerm
        from ceres.character.domain.precareer.university import UniversityPreCareer

        proj = _projection()
        university = precareer_of_type(UniversityPreCareer)
        term = university.make_term()
        proj.summary.terms.append(term)
        pending = PendingPreCareerSkillChoice(pending_id=(1, 0), instruction='Choose', level=0, options=[Admin()])
        handler = PreCareerSkillChoiceHandler(skill=Admin())
        handler.apply(proj, _any_event(), fulfilled_pending=pending)
        assert isinstance(term, UniversityTerm)
        assert any(isinstance(s, Admin) for s in term.pending_skills)


class TestPendingPreCareerEvent:
    def test_event_from_form_parses_roll(self):
        pending = PendingPreCareerEvent(pending_id=(1, 0), instruction='Roll 2D')
        event = pending.event_from_form({'roll': '9'})
        assert isinstance(event.handler, PreCareerEventHandler)
        assert event.handler.roll == 9

    def test_event_from_form_defaults_roll(self):
        pending = PendingPreCareerEvent(pending_id=(1, 0), instruction='Roll 2D')
        event = pending.event_from_form({})
        assert isinstance(event.handler, PreCareerEventHandler)
        assert event.handler.roll == 7

    def test_input_specs_returns_roll_entry(self):
        specs = PendingPreCareerEvent(pending_id=(1, 0), instruction='Roll').input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], NumberEntry) and specs[0].name == 'roll'


class TestPreCareerEventHandler:
    def _proj_with_precareer(self):
        from ceres.character.domain.precareer.loader import load_precareers

        university = next(p for p in load_precareers() if p.name == 'University')
        proj = _projection()
        proj.summary.terms.append(university.make_term())
        return proj

    def test_raises_when_no_precareer(self):
        proj = _projection()
        handler = PreCareerEventHandler(roll=5)
        with pytest.raises(ReplayError, match='No active pre-career'):
            handler.apply(proj, _any_event())

    def test_normal_roll_appends_narrative(self):
        proj = self._proj_with_precareer()
        PreCareerEventHandler(roll=5).apply(proj, _any_event())
        assert any('Pre-career event' in n for n in proj.summary.narrative)

    def test_roll_3_ends_precareer_without_graduation(self):
        from ceres.character.domain.precareer.precareer_term import PreCareerTerm

        proj = self._proj_with_precareer()
        PreCareerEventHandler(roll=3).apply(proj, _any_event())
        assert proj.summary.current_precareer_term is None
        assert any(isinstance(t, PreCareerTerm) and t.completed for t in proj.summary.terms)

    def test_roll_12_increases_soc(self):
        proj = self._proj_with_precareer()
        soc_before = proj.summary.characteristics.get(Chars.SOC, 0)
        PreCareerEventHandler(roll=12).apply(proj, _any_event())
        assert proj.summary.characteristics.get(Chars.SOC, 0) == soc_before + 1


class TestPendingPreCareerGraduation:
    def test_event_from_form_parses_roll(self):
        pending = PendingPreCareerGraduation(pending_id=(1, 0), instruction='Graduation roll')
        event = pending.event_from_form({'roll': '8'})
        assert isinstance(event.handler, PreCareerGraduationHandler)
        assert event.handler.roll == 8

    def test_event_from_form_defaults_roll(self):
        pending = PendingPreCareerGraduation(pending_id=(1, 0), instruction='Graduation roll')
        event = pending.event_from_form({})
        assert isinstance(event.handler, PreCareerGraduationHandler)
        assert event.handler.roll == 7

    def test_input_specs_returns_roll_entry(self):
        specs = PendingPreCareerGraduation(pending_id=(1, 0), instruction='Grad').input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], NumberEntry) and specs[0].name == 'roll'


class TestPreCareerGraduationHandler:
    def _proj_with_university(self):
        from ceres.character.domain.precareer.loader import load_precareers

        university = next(p for p in load_precareers() if p.name == 'University')
        proj = _projection(characteristics={Chars.EDU: 8})
        proj.summary.terms.append(university.make_term())
        return proj

    def test_raises_when_no_precareer(self):
        proj = _projection()
        with pytest.raises(ReplayError, match='No active pre-career for graduation'):
            PreCareerGraduationHandler(roll=8).apply(proj, _any_event())

    def test_successful_graduation_appends_narrative(self):
        proj = self._proj_with_university()
        PreCareerGraduationHandler(roll=10).apply(proj, _any_event())
        assert any('Graduated' in n for n in proj.summary.narrative)

    def test_failed_graduation_appends_failure_narrative(self):
        proj = self._proj_with_university()
        PreCareerGraduationHandler(roll=2).apply(proj, _any_event())
        assert any('not graduate' in n for n in proj.summary.narrative)

    def test_graduation_marks_term_completed(self):
        from ceres.character.domain.precareer.precareer_term import PreCareerTerm

        proj = self._proj_with_university()
        PreCareerGraduationHandler(roll=10).apply(proj, _any_event())
        assert proj.summary.current_precareer_term is None
        assert any(isinstance(t, PreCareerTerm) and t.completed and t.graduated for t in proj.summary.terms)
