"""Unit tests for common_pending — shared career pending input mechanics."""

from ceres.character.domain.career.army import PendingArmyEvent11SkillChoice
from ceres.character.domain.career.career_events import SkillChoiceHandler, SkillRollHandler
from ceres.character.domain.career.common_pending import (
    PendingAdvancedTrainingSkillRoll,
    PendingAnySkillAtLevelOnSuccessRoll,
    append_increment_existing_skill_pending,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skill_events import PendingSkillChoice
from ceres.character.domain.skills import Admin, Drive, Level
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


class TestAppendIncrementExistingSkillPending:
    def test_appends_skill_choice_for_known_skills(self):
        proj = _projection(skills=[Admin(level=Level(value=1))])
        append_increment_existing_skill_pending(proj, (5, 0), 'Increase an existing skill')
        assert any(isinstance(p, PendingSkillChoice) for p in proj.pending_inputs)

    def test_options_are_current_skills(self):
        proj = _projection(skills=[Admin(level=Level(value=1)), Drive(wheel=Level(value=1))])
        append_increment_existing_skill_pending(proj, (5, 0), 'Increase')
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingSkillChoice))
        skill_types = {type(s) for s in pending.options}
        assert Admin in skill_types and Drive in skill_types


class TestPendingAdvancedTrainingSkillRoll:
    def test_event_from_form_parses_skill_and_roll(self):
        pending = PendingAdvancedTrainingSkillRoll(pending_id=(1, 0), instruction='Roll EDU 8+', options=[Admin()])
        event = pending.event_from_form({'skill': 'ADMIN', 'modified_roll': '9'})
        assert isinstance(event.handler, SkillRollHandler)
        assert event.handler.modified_roll == 9

    def test_event_from_form_handles_characteristic(self):
        pending = PendingAdvancedTrainingSkillRoll(pending_id=(1, 0), instruction='Roll EDU 8+', options=[Chars.EDU])
        event = pending.event_from_form({'skill': 'EDU', 'modified_roll': '8'})
        assert isinstance(event.handler, SkillRollHandler)
        assert event.handler.skill == Chars.EDU

    def test_input_specs_returns_select_and_roll(self):
        pending = PendingAdvancedTrainingSkillRoll(pending_id=(1, 0), instruction='Roll EDU 8+', options=[Admin()])
        specs = pending.input_specs(_projection())
        assert len(specs) == 2
        assert isinstance(specs[0], Select) and specs[0].name == 'skill'
        assert isinstance(specs[1], NumberEntry) and specs[1].name == 'modified_roll'

    def test_resolve_on_success_queues_increment_pending(self):
        pending = PendingAdvancedTrainingSkillRoll(pending_id=(1, 0), instruction='Roll EDU 8+', options=[Admin()])
        proj = _projection(skills=[Admin(level=Level(value=1))])
        event = Event(handler=SkillRollHandler(skill=Admin(), modified_roll=9))
        pending.resolve(proj, event)
        assert any(isinstance(p, PendingSkillChoice) for p in proj.pending_inputs)

    def test_resolve_on_failure_does_not_queue(self):
        pending = PendingAdvancedTrainingSkillRoll(
            pending_id=(1, 0), instruction='Roll EDU 8+', options=[Admin()], threshold=8
        )
        proj = _projection(skills=[Admin(level=Level(value=1))])
        event = Event(handler=SkillRollHandler(skill=Admin(), modified_roll=7))
        pending.resolve(proj, event)
        assert not any(isinstance(p, PendingSkillChoice) for p in proj.pending_inputs)

    def test_custom_threshold_used(self):
        pending = PendingAdvancedTrainingSkillRoll(
            pending_id=(1, 0), instruction='Roll EDU 10+', options=[Admin()], threshold=10
        )
        proj = _projection(skills=[Admin(level=Level(value=1))])
        event = Event(handler=SkillRollHandler(skill=Admin(), modified_roll=9))
        pending.resolve(proj, event)
        assert not any(isinstance(p, PendingSkillChoice) for p in proj.pending_inputs)


class TestPendingAnySkillAtLevelOnSuccessRoll:
    def test_resolve_success_queues_skill_choice(self):
        pending = PendingAnySkillAtLevelOnSuccessRoll(
            pending_id=(1, 0),
            instruction='Roll EDU 8+',
            options=[Admin()],
            success_instruction='Choose any skill at level 1',
        )
        proj = _projection()
        event = Event(handler=SkillRollHandler(skill=Admin(), modified_roll=8))
        pending.resolve(proj, event)
        choice = next((p for p in proj.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert choice is not None
        assert choice.instruction == 'Choose any skill at level 1'

    def test_resolve_failure_does_not_queue(self):
        pending = PendingAnySkillAtLevelOnSuccessRoll(
            pending_id=(1, 0),
            instruction='Roll EDU 8+',
            options=[Admin()],
            threshold=8,
            success_instruction='Choose any skill',
        )
        proj = _projection()
        event = Event(handler=SkillRollHandler(skill=Admin(), modified_roll=7))
        pending.resolve(proj, event)
        assert not any(isinstance(p, PendingSkillChoice) for p in proj.pending_inputs)


class TestCareerSkillChoicePendingBase:
    def test_event_from_form_returns_skill_choice_event(self):
        pending = PendingArmyEvent11SkillChoice(pending_id=(1, 0), instruction='Choose a skill', options=[Admin()])
        import json

        skill_json = json.dumps({'kind': 'ADMIN'})
        event = pending.event_from_form({'skill': skill_json})
        assert isinstance(event.handler, SkillChoiceHandler)
        assert isinstance(event.handler.skill, Admin)

    def test_input_specs_returns_select(self):
        pending = PendingArmyEvent11SkillChoice(pending_id=(1, 0), instruction='Choose a skill', options=[Admin()])
        proj = _projection()
        specs = pending.input_specs(proj)
        assert len(specs) == 1
        assert isinstance(specs[0], Select) and specs[0].name == 'skill'

    def test_on_skill_chosen_grants_skill(self):
        pending = PendingArmyEvent11SkillChoice(pending_id=(1, 0), instruction='Choose a skill', options=[Admin()])
        proj = _projection()
        event = Event(handler=SkillChoiceHandler(skill=Admin(level=Level(value=1))))
        pending.on_skill_chosen(proj, event)
        assert proj.summary.skill_level(Admin, 0) == 1
