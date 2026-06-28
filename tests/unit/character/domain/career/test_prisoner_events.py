"""Unit tests for prisoner_events.py — ParoleRollHandler, PendingParoleRoll, set_forced_prison_career."""

from ceres.character.domain.career.prisoner_events import (
    ParoleRollHandler,
    PendingParoleRoll,
    set_forced_prison_career,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import NumberEntry
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _proj() -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(
            name='T',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.STR: 7},
        ),
    )


def _event(roll: int = 4) -> Event:
    return Event(handler=ParoleRollHandler(roll=roll))


class TestParoleRollHandler:
    def test_sets_parole_threshold_to_roll_plus_2(self):
        proj = _proj()
        ParoleRollHandler(roll=4).apply(proj, _event(roll=4))
        assert proj.summary.parole_threshold == 6

    def test_threshold_varies_with_roll(self):
        proj = _proj()
        ParoleRollHandler(roll=1).apply(proj, _event(roll=1))
        assert proj.summary.parole_threshold == 3

    def test_appends_narrative_entry(self):
        proj = _proj()
        ParoleRollHandler(roll=4).apply(proj, _event(roll=4))
        assert any('Parole Threshold' in n for n in proj.summary.narrative)

    def test_narrative_includes_threshold(self):
        proj = _proj()
        ParoleRollHandler(roll=3).apply(proj, _event(roll=3))
        assert any('5' in n for n in proj.summary.narrative)


class TestPendingParoleRoll:
    def test_event_from_form_creates_parole_roll_event(self):
        pending = PendingParoleRoll(pending_id=(1, 0), instruction='Roll 1D')
        event = pending.event_from_form({'roll': '4'})
        assert isinstance(event.handler, ParoleRollHandler)
        assert event.handler.roll == 4

    def test_event_fulfills_pending_id(self):
        pending = PendingParoleRoll(pending_id=(1, 0), instruction='Roll 1D')
        event = pending.event_from_form({'roll': '3'})
        assert event.fulfills == (1, 0)

    def test_input_specs_has_number_entry(self):
        pending = PendingParoleRoll(pending_id=(1, 0), instruction='Roll 1D')
        specs = pending.input_specs(_proj())
        assert len(specs) == 1
        assert isinstance(specs[0], NumberEntry)

    def test_input_spec_range_1_to_6(self):
        pending = PendingParoleRoll(pending_id=(1, 0), instruction='Roll 1D')
        spec = pending.input_specs(_proj())[0]
        assert isinstance(spec, NumberEntry)
        assert spec.min == 1
        assert spec.max == 6


class TestSetForcedPrisonCareer:
    def test_sets_forced_next_career(self):
        from ceres.character.domain.career.prisoner import PRISONER

        proj = _proj()
        set_forced_prison_career(proj, 'Crime: Murder')
        assert proj.forced_next_career is PRISONER

    def test_sets_prison_note_on_last_career_term(self):
        from ceres.character.domain.career.army import ARMY
        from ceres.character.domain.career.career_data import CareerTerm

        proj = _proj()
        support = ARMY.assignment('Support')
        assert support is not None
        proj.summary.terms.append(CareerTerm(career=ARMY, assignment=support))
        set_forced_prison_career(proj, 'Crime: Theft')
        assert proj.summary.career_terms[-1].prison == 'Crime: Theft'

    def test_no_error_when_no_career_terms(self):
        proj = _proj()
        set_forced_prison_career(proj, 'Crime')
        # no career_terms — no crash, just sets forced_next_career
