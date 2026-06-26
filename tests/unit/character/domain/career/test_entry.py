"""Unit tests for career entry.py — career/draft pending input mechanics."""

import pytest

from ceres.character.domain.career import AGENT, ARMY, SCOUT
from ceres.character.domain.career.entry import (
    CareerEntryHandler,
    DraftAssignmentHandler,
    DraftHandler,
    PendingCareerChoice,
    PendingDraftAssignmentChoice,
    PendingDraftChoice,
    queue_career_choice,
    queue_career_choice_indexed,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import CareerChoice, NumberEntry, Select
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


class TestCareerEntryHandler:
    def test_apply_starts_career(self):
        proj = _projection()
        assignment = ARMY.assignments[0]
        handler = CareerEntryHandler(career=ARMY, assignment=assignment, qualification_roll=8)
        handler.apply(proj, Event(handler=handler))
        assert proj.summary.current_career == ARMY

    def test_apply_sets_assignment(self):
        proj = _projection()
        support = ARMY.assignment('Support')
        handler = CareerEntryHandler(career=ARMY, assignment=support, qualification_roll=8)
        handler.apply(proj, Event(handler=handler))
        assert proj.summary.current_assignment == support


class TestDraftHandler:
    def test_apply_with_single_assignment_career_starts_term(self):
        # AGENT has a single draft assignment, so no assignment-choice pending is queued
        proj = _projection()
        handler = DraftHandler(career=AGENT)
        handler.apply(proj, Event(handler=handler))
        assert proj.summary.current_career is not None

    def test_apply_with_multi_assignment_career_queues_choice(self):
        # ARMY has 3 draft assignments — queues PendingDraftAssignmentChoice instead
        from ceres.character.domain.career.entry import PendingDraftAssignmentChoice

        proj = _projection()
        handler = DraftHandler(career=ARMY)
        handler.apply(proj, Event(handler=handler))
        assert any(isinstance(p, PendingDraftAssignmentChoice) for p in proj.pending_inputs)

    def test_apply_with_explicit_assignment_marks_drafted(self):
        proj = _projection()
        handler = DraftHandler(career=ARMY, assignment=ARMY.assignments[0])
        handler.apply(proj, Event(handler=handler))
        assert proj.summary.drafted is True

    def test_apply_twice_raises(self):
        proj = _projection()
        handler = DraftHandler(career=AGENT)
        handler.apply(proj, Event(handler=handler))
        with pytest.raises(ReplayError, match='draft'):
            handler.apply(proj, Event(handler=handler))


class TestPendingCareerChoice:
    def test_event_from_form_career_entry(self):
        pending = PendingCareerChoice(pending_id=(1, 0), instruction='Choose a career', options=[ARMY, SCOUT])
        event = pending.event_from_form({'career': 'Army', 'assignment': 'Support', 'roll': '8'})
        assert isinstance(event.handler, CareerEntryHandler)
        assert event.handler.career == ARMY
        assert event.handler.qualification_roll == 8

    def test_event_from_form_unknown_career_raises(self):
        pending = PendingCareerChoice(pending_id=(1, 0), instruction='Choose a career', options=[ARMY])
        with pytest.raises(ReplayError, match='Unknown career'):
            pending.event_from_form({'career': 'NonExistent', 'assignment': 'Support', 'roll': '8'})

    def test_event_from_form_unknown_assignment_raises(self):
        pending = PendingCareerChoice(pending_id=(1, 0), instruction='Choose a career', options=[ARMY])
        with pytest.raises(ReplayError, match='Unknown assignment'):
            pending.event_from_form({'career': 'Army', 'assignment': 'BadAssignment', 'roll': '8'})

    def test_input_specs_returns_career_choice(self):
        pending = PendingCareerChoice(pending_id=(1, 0), instruction='Choose a career', options=[ARMY])
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], CareerChoice)


class TestPendingDraftChoice:
    def test_input_specs_with_draft_includes_roll(self):
        pending = PendingDraftChoice(pending_id=(1, 0), instruction='Draft or alternative?', can_draft=True)
        specs = pending.input_specs(_projection())
        assert any(isinstance(s, NumberEntry) and s.name == 'roll' for s in specs)

    def test_input_specs_no_draft_has_no_roll(self):
        pending = PendingDraftChoice(pending_id=(1, 0), instruction='No draft available', can_draft=False)
        specs = pending.input_specs(_projection())
        assert not any(isinstance(s, NumberEntry) and s.name == 'roll' for s in specs)

    def test_event_from_form_draft_returns_draft_handler(self):
        pending = PendingDraftChoice(pending_id=(1, 0), instruction='Draft?', can_draft=True)
        event = pending.event_from_form({'choice': 'draft', 'roll': '1'})
        assert isinstance(event.handler, DraftHandler)


class TestPendingDraftAssignmentChoice:
    def test_event_from_form_returns_draft_assignment_handler(self):
        pending = PendingDraftAssignmentChoice(pending_id=(1, 0), instruction='Choose assignment', career=ARMY)
        event = pending.event_from_form({'assignment': ARMY.draft_assignments[0]})
        assert isinstance(event.handler, DraftAssignmentHandler)
        assert event.handler.assignment is not None

    def test_event_from_form_unknown_assignment_raises(self):
        pending = PendingDraftAssignmentChoice(pending_id=(1, 0), instruction='Choose assignment', career=ARMY)
        with pytest.raises(ReplayError, match='Unknown assignment'):
            pending.event_from_form({'assignment': 'BadOne'})

    def test_input_specs_returns_assignment_select(self):
        pending = PendingDraftAssignmentChoice(pending_id=(1, 0), instruction='Choose assignment', career=ARMY)
        specs = pending.input_specs(_projection())
        assert any(isinstance(s, Select) and s.name == 'assignment' for s in specs)


class TestQueueCareerChoice:
    def test_adds_pending_career_choice(self):
        proj = _projection()
        queue_career_choice(proj, event_id=1)
        assert any(isinstance(p, PendingCareerChoice) for p in proj.pending_inputs)

    def test_indexed_uses_given_idx(self):
        proj = _projection()
        queue_career_choice_indexed(proj, event_id=1, idx=3)
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingCareerChoice))
        assert pending.pending_id == (1, 3)

    def test_forced_next_career_constrains_options(self):
        proj = _projection()
        proj.forced_next_career = SCOUT
        queue_career_choice(proj, event_id=1)
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingCareerChoice))
        assert pending.options == [SCOUT]
        assert proj.forced_next_career is None
