"""Unit tests for skill_events.py — SkillChoiceHandler, PendingSkillChoice, helpers."""

import json

from ceres.character.domain.career.career_data import AdvancementDmOption
from ceres.character.domain.career.career_events import SurviveHandler
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.skill_events import (
    PendingSkillChoice,
    SkillChoiceHandler,
    build_skill_select_options,
    skill_option_label,
)
from ceres.character.domain.skills import Admin, Drive, Level
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import Select
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


def _any_event() -> Event:
    return Event(handler=SurviveHandler(roll=5))


class TestSkillOptionLabel:
    def test_non_specialised_returns_class_name(self):
        assert skill_option_label(Admin()) == 'Admin'

    def test_advancement_dm_returns_label(self):
        label = skill_option_label(AdvancementDmOption())
        assert 'advancement' in label.lower() or 'dm' in label.lower()

    def test_specialised_active_field_included(self):
        skill = Drive(wheel=Level(value=1))
        label = skill_option_label(skill)
        assert 'Drive' in label
        assert 'wheel' in label.lower() or 'Wheel' in label


class TestBuildSkillSelectOptions:
    def test_non_specialised_level_zero(self):
        proj = _projection()
        options = build_skill_select_options(proj, [Admin()], 0)
        assert len(options) == 1
        label, json_val = options[0]
        assert label == 'Admin'
        parsed = json.loads(json_val)
        assert parsed['kind'] == 'ADMIN'

    def test_advancement_dm_option(self):
        proj = _projection()
        opt = AdvancementDmOption()
        options = build_skill_select_options(proj, [opt], None)
        assert any(opt.label() in label for label, _ in options)

    def test_level_none_non_specialised_at_0_offers_level_1(self):
        proj = _projection()
        options = build_skill_select_options(proj, [Admin()], None)
        assert len(options) == 1


class TestSkillChoiceHandler:
    def test_grants_skill_when_no_on_skill_chosen(self):
        proj = _projection()
        handler = SkillChoiceHandler(skill=Admin(level=Level(value=1)))
        handler.apply(proj, _any_event())
        assert proj.summary.skill_level(Admin, 0) == 1

    def test_delegates_to_on_skill_chosen_when_present(self):
        from ceres.character.domain.life_events import PendingLifeEventAlienScience

        proj = _projection()
        pending = PendingLifeEventAlienScience(pending_id=(1, 0), instruction='Choose')
        admin = Admin(level=Level(value=1))
        event = Event(handler=SkillChoiceHandler(skill=admin))
        SkillChoiceHandler(skill=admin).apply(proj, event, fulfilled_pending=pending)
        assert proj.summary.skill_level(Admin, 0) == 1


class TestPendingSkillChoice:
    def test_event_from_form_parses_skill(self):
        pending = PendingSkillChoice(pending_id=(1, 0), instruction='Choose', options=[Admin()])
        event = pending.event_from_form({'skill': json.dumps({'kind': 'ADMIN'})})
        assert isinstance(event.handler, SkillChoiceHandler)
        assert isinstance(event.handler.skill, Admin)

    def test_event_from_form_advancement_dm(self):
        from ceres.character.domain.career.advancement import AdvancementDmChoiceHandler

        opt = AdvancementDmOption()
        pending = PendingSkillChoice(pending_id=(1, 0), instruction='Choose', options=[Admin()])
        event = pending.event_from_form({'skill': opt.model_dump_json()})
        assert isinstance(event.handler, AdvancementDmChoiceHandler)

    def test_input_specs_returns_select(self):
        pending = PendingSkillChoice(pending_id=(1, 0), instruction='Choose', options=[Admin()])
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], Select) and specs[0].name == 'skill'
