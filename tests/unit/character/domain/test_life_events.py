"""Unit tests for life_events.py — LifeEventHandler, ConnectionKindChoiceHandler, etc."""

import pytest

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.domain.connection import Ally, Contact
from ceres.character.domain.life_events import (
    BetrayalConvertHandler,
    ConnectionKindChoiceHandler,
    LifeEventCrimeLoseBenefitRoll,
    LifeEventCrimeTakePrisoner,
    LifeEventHandler,
    LifeEventUnusualHandler,
    PendingLifeEvent,
    PendingLifeEventAlienScience,
    PendingLifeEventBetrayalConvert,
    PendingLifeEventChoice,
    PendingLifeEventUnusual,
)
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
    from ceres.character.domain.career.career_events import SurviveHandler

    return Event(handler=SurviveHandler(roll=5))


class TestLifeEventHandler:
    def test_out_of_range_roll_raises(self):
        proj = _projection()
        with pytest.raises(ReplayError, match='must be 2-12'):
            LifeEventHandler(roll=1).apply(proj, _any_event())

    def test_roll_13_raises(self):
        proj = _projection()
        with pytest.raises(ReplayError, match='must be 2-12'):
            LifeEventHandler(roll=13).apply(proj, _any_event())

    def test_roll_2_queues_injury_pending(self):
        from ceres.character.domain.health.health_events import PendingInjuryTable

        proj = _projection()
        LifeEventHandler(roll=2).apply(proj, _any_event())
        assert any(isinstance(p, PendingInjuryTable) for p in proj.pending_inputs)

    def test_roll_2_adds_sickness_narrative(self):
        proj = _projection()
        LifeEventHandler(roll=2).apply(proj, _any_event())
        assert any('sickness' in n for n in proj.summary.narrative)

    def test_roll_4_queues_life_event_choice(self):
        proj = _projection()
        LifeEventHandler(roll=4).apply(proj, _any_event())
        assert any(isinstance(p, PendingLifeEventChoice) for p in proj.pending_inputs)

    def test_roll_5_adds_ally(self):
        proj = _projection()
        LifeEventHandler(roll=5).apply(proj, _any_event())
        allies = [c for c in proj.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1

    def test_roll_6_adds_ally(self):
        proj = _projection()
        LifeEventHandler(roll=6).apply(proj, _any_event())
        allies = [c for c in proj.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1

    def test_roll_7_adds_contact(self):
        proj = _projection()
        LifeEventHandler(roll=7).apply(proj, _any_event())
        contacts = [c for c in proj.summary.connections if isinstance(c, Contact)]
        assert len(contacts) == 1

    def test_roll_8_no_contacts_queues_choice(self):
        proj = _projection()
        LifeEventHandler(roll=8).apply(proj, _any_event())
        assert any(isinstance(p, PendingLifeEventChoice) for p in proj.pending_inputs)

    def test_roll_8_with_contact_queues_betrayal_convert(self):
        proj = _projection()
        proj.summary.connections.append(Contact(origin='Old contact'))
        LifeEventHandler(roll=8).apply(proj, _any_event())
        assert any(isinstance(p, PendingLifeEventBetrayalConvert) for p in proj.pending_inputs)

    def test_roll_9_increases_qualification_dm(self):
        proj = _projection()
        LifeEventHandler(roll=9).apply(proj, _any_event())
        assert proj.pending_qualification_dm == 2

    def test_roll_11_queues_crime_choices(self):
        from ceres.character.domain.career.career_events import PendingChoices

        proj = _projection()
        LifeEventHandler(roll=11).apply(proj, _any_event())
        assert any(isinstance(p, PendingChoices) for p in proj.pending_inputs)

    def test_roll_12_queues_unusual_pending(self):
        proj = _projection()
        LifeEventHandler(roll=12).apply(proj, _any_event())
        assert any(isinstance(p, PendingLifeEventUnusual) for p in proj.pending_inputs)


class TestLifeEventUnusualHandler:
    def test_out_of_range_raises(self):
        proj = _projection()
        with pytest.raises(ReplayError, match='must be 1-6'):
            LifeEventUnusualHandler(roll=7).apply(proj, _any_event())

    def test_roll_1_queues_psionics_pending(self):
        from ceres.character.domain.psionics import PendingLifeEventPsionicsRoll

        proj = _projection()
        LifeEventUnusualHandler(roll=1).apply(proj, _any_event())
        assert any(isinstance(p, PendingLifeEventPsionicsRoll) for p in proj.pending_inputs)

    def test_roll_2_adds_contact_and_skill_pending(self):
        proj = _projection()
        LifeEventUnusualHandler(roll=2).apply(proj, _any_event())
        contacts = [c for c in proj.summary.connections if isinstance(c, Contact)]
        assert len(contacts) == 1
        assert any(isinstance(p, PendingLifeEventAlienScience) for p in proj.pending_inputs)

    def test_roll_3_adds_narrative(self):
        proj = _projection()
        LifeEventUnusualHandler(roll=3).apply(proj, _any_event())
        assert any('artefact' in n for n in proj.summary.narrative)

    def test_roll_4_adds_amnesia_narrative(self):
        proj = _projection()
        LifeEventUnusualHandler(roll=4).apply(proj, _any_event())
        assert any('amnesia' in n for n in proj.summary.narrative)


class TestConnectionKindChoiceHandler:
    def test_adds_rival_connection(self):
        proj = _projection()
        pending = PendingLifeEventChoice(
            pending_id=(1, 0), instruction='Choose', roll=4, options=[ConnectionKind.RIVAL, ConnectionKind.ENEMY]
        )
        handler = ConnectionKindChoiceHandler(connection_kind=ConnectionKind.RIVAL)
        handler.apply(proj, _any_event(), fulfilled_pending=pending)
        from ceres.character.domain.connection import Rival

        rivals = [c for c in proj.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_adds_narrative_for_roll_4_rival(self):
        proj = _projection()
        pending = PendingLifeEventChoice(
            pending_id=(1, 0), instruction='Choose', roll=4, options=[ConnectionKind.RIVAL]
        )
        handler = ConnectionKindChoiceHandler(connection_kind=ConnectionKind.RIVAL)
        handler.apply(proj, _any_event(), fulfilled_pending=pending)
        assert any('rival' in n for n in proj.summary.narrative)


class TestBetrayalConvertHandler:
    def test_converts_contact_to_rival(self):
        proj = _projection()
        proj.summary.connections.append(Contact(origin='Old friend'))
        handler = BetrayalConvertHandler(connection_index=0, new_kind=ConnectionKind.RIVAL)
        handler.apply(proj, _any_event())
        from ceres.character.domain.connection import Rival

        assert isinstance(proj.summary.connections[0], Rival)

    def test_out_of_range_index_raises(self):
        proj = _projection()
        handler = BetrayalConvertHandler(connection_index=5, new_kind=ConnectionKind.RIVAL)
        with pytest.raises(ReplayError, match='out of range'):
            handler.apply(proj, _any_event())


class TestLifeEventCrimeChoices:
    def _proj_with_career(self) -> CharacterProjection:
        from ceres.character.domain.career import ARMY
        from ceres.character.domain.career.career_data import CareerTerm, MusterOut

        proj = _projection()
        proj.summary.terms.append(
            CareerTerm(career=ARMY, assignment=ARMY.assignment('Support'), muster_out=MusterOut())
        )
        return proj

    def test_crime_lose_benefit_roll_increments_lost_rolls(self):
        proj = self._proj_with_career()
        choice = LifeEventCrimeLoseBenefitRoll()
        choice.handle(proj, _any_event())
        assert proj.summary.career_terms[-1].require_muster_out().lost_rolls == 1

    def test_crime_take_prisoner_sets_forced_career(self):
        from ceres.character.domain.career.prisoner import PRISONER

        proj = self._proj_with_career()
        choice = LifeEventCrimeTakePrisoner()
        choice.handle(proj, _any_event())
        assert proj.forced_next_career is PRISONER

    def test_crime_take_prisoner_sets_prison_note(self):
        proj = self._proj_with_career()
        choice = LifeEventCrimeTakePrisoner()
        choice.handle(proj, _any_event())
        assert proj.summary.career_terms[-1].prison is not None


class TestPendingLifeEvent:
    def test_event_from_form_creates_life_event_handler(self):
        pending = PendingLifeEvent(pending_id=(1, 0), instruction='Roll')
        event = pending.event_from_form({'roll': '7'})
        assert isinstance(event.handler, LifeEventHandler)
        assert event.handler.roll == 7

    def test_input_specs_returns_number_entry(self):
        pending = PendingLifeEvent(pending_id=(1, 0), instruction='Roll')
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], NumberEntry)


class TestPendingLifeEventChoice:
    def test_event_from_form_creates_connection_kind_handler(self):
        pending = PendingLifeEventChoice(
            pending_id=(1, 0), instruction='Choose', roll=4, options=[ConnectionKind.RIVAL, ConnectionKind.ENEMY]
        )
        event = pending.event_from_form({'connection_kind': ConnectionKind.ENEMY.value})
        assert isinstance(event.handler, ConnectionKindChoiceHandler)
        assert event.handler.connection_kind == ConnectionKind.ENEMY

    def test_input_specs_returns_select(self):
        pending = PendingLifeEventChoice(
            pending_id=(1, 0), instruction='Choose', roll=4, options=[ConnectionKind.RIVAL, ConnectionKind.ENEMY]
        )
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], Select)


class TestPendingLifeEventUnusual:
    def test_event_from_form_creates_unusual_handler(self):
        pending = PendingLifeEventUnusual(pending_id=(1, 0))
        event = pending.event_from_form({'roll': '3'})
        assert isinstance(event.handler, LifeEventUnusualHandler)
        assert event.handler.roll == 3


class TestPendingLifeEventBetrayalConvert:
    def test_event_from_form_creates_betrayal_handler(self):
        pending = PendingLifeEventBetrayalConvert(pending_id=(1, 0), instruction='Choose')
        form = {'betrayal_choice': f'0|{ConnectionKind.ENEMY.value}'}
        event = pending.event_from_form(form)
        assert isinstance(event.handler, BetrayalConvertHandler)
        assert event.handler.connection_index == 0
        assert event.handler.new_kind == ConnectionKind.ENEMY

    def test_input_specs_shows_contacts_and_allies(self):
        proj = _projection()
        proj.summary.connections.extend(
            [
                Contact(origin='C1'),
                Ally(origin='A1'),
            ]
        )
        pending = PendingLifeEventBetrayalConvert(pending_id=(1, 0), instruction='Choose')
        specs = pending.input_specs(proj)
        assert isinstance(specs[0], Select)
        assert len(specs[0].options) == 4  # Contact→Rival, Contact→Enemy, Ally→Rival, Ally→Enemy

    def test_input_specs_no_connections_returns_fallback(self):
        proj = _projection()
        pending = PendingLifeEventBetrayalConvert(pending_id=(1, 0), instruction='Choose')
        specs = pending.input_specs(proj)
        assert isinstance(specs[0], Select)
        assert len(specs[0].options) == 1


class TestPendingLifeEventAlienScience:
    def test_on_skill_chosen_grants_skill(self):
        from ceres.character.domain.career.career_events import SkillChoiceHandler
        from ceres.character.domain.skills import SpaceScience

        proj = _projection()
        pending = PendingLifeEventAlienScience(pending_id=(1, 0), instruction='Choose')
        event = Event(handler=SkillChoiceHandler(skill=SpaceScience()))
        pending.on_skill_chosen(proj, event)
        assert proj.summary.skill_level(SpaceScience, 0) == 0

    def test_input_specs_returns_select_with_science_skills(self):

        proj = _projection()
        pending = PendingLifeEventAlienScience(pending_id=(1, 0), instruction='Choose')
        specs = pending.input_specs(proj)
        assert isinstance(specs[0], Select)
        labels = [label for label, _ in specs[0].options]
        assert any('Science' in label for label in labels)
