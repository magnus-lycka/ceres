"""Unit tests for choice_events.py — ChoiceHandler and PendingChoices."""

import pytest

from ceres.character.domain.career.career_events import SurviveHandler
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.choice_events import ChoiceHandler, PendingChoices
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import Select
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.pending_input import ChoiceBase
from tests.unit.character.helpers import MOCK_WORLD


def _projection() -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )


def _any_event() -> Event:
    return Event(handler=SurviveHandler(roll=5))


class _TrackingChoice(ChoiceBase):
    kind: str = 'test_choice_a'
    label: str = 'Option A'
    called: bool = False

    def handle(self, projection: CharacterProjection, event: Event) -> None:
        projection.summary.narrative.append('choice_a_handled')


class TestChoiceHandler:
    def test_raises_without_fulfilled_pending(self):
        handler = ChoiceHandler(choice='test_choice_a')
        with pytest.raises(ReplayError, match='no matching pending input'):
            handler.apply(_projection(), _any_event())

    def test_raises_with_wrong_pending_type(self):
        from ceres.character.domain.career.career_events import PendingSurvive

        handler = ChoiceHandler(choice='test_choice_a')
        wrong = PendingSurvive(pending_id=(1, 0), instruction='Survive')
        with pytest.raises(ReplayError, match='unexpected pending type'):
            handler.apply(_projection(), _any_event(), fulfilled_pending=wrong)

    def test_raises_for_unknown_choice_kind(self):
        choice = _TrackingChoice()
        pending = PendingChoices(pending_id=(1, 0), instruction='Choose', choices=[choice])
        handler = ChoiceHandler(choice='nonexistent_kind')
        with pytest.raises(ReplayError, match='Unknown choice'):
            handler.apply(_projection(), _any_event(), fulfilled_pending=pending)

    def test_dispatches_to_matching_choice(self):
        choice = _TrackingChoice()
        pending = PendingChoices(pending_id=(1, 0), instruction='Choose', choices=[choice])
        handler = ChoiceHandler(choice='test_choice_a')
        proj = _projection()
        handler.apply(proj, _any_event(), fulfilled_pending=pending)
        assert 'choice_a_handled' in proj.summary.narrative


class TestPendingChoices:
    def test_event_from_form_creates_choice_handler(self):
        pending = PendingChoices(pending_id=(1, 0), instruction='Choose', choices=[_TrackingChoice()])
        event = pending.event_from_form({'choice': 'test_choice_a'})
        assert isinstance(event.handler, ChoiceHandler)
        assert event.handler.choice == 'test_choice_a'

    def test_input_specs_returns_select(self):
        pending = PendingChoices(pending_id=(1, 0), instruction='Choose', choices=[_TrackingChoice()])
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], Select) and specs[0].name == 'choice'

    def test_select_options_use_labels(self):
        choice = _TrackingChoice(label='My Option')
        pending = PendingChoices(pending_id=(1, 0), instruction='Choose', choices=[choice])
        specs = pending.input_specs(_projection())
        assert isinstance(specs[0], Select)
        assert any('My Option' in label for label, _ in specs[0].options)
