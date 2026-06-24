"""Tests for CareerTerm narrative fields: event, mishap, prison."""

from ceres.character.domain.career import ARMY, ROGUE
from ceres.character.domain.career.career_events import (
    CareerEntryHandler,
    MishapHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5."""
    ev1 = Event(handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Test'))
    ev2 = Event(fulfills=(ev1.id, 0), handler=UcpHandler(ucp='7869A5'))
    return [
        ev1,
        ev2,
        Event(fulfills=(ev2.id, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])),
    ]


def _enter_army() -> list:
    """Army Support: END 5+, DM+0, roll=5 — pass."""
    _base = _setup()
    return [
        *_base,
        Event(
            fulfills=(_base[-1].id, 0),
            handler=CareerEntryHandler(career=ARMY, assignment=ARMY.assignment('Support'), qualification_roll=5),
        ),
    ]


def _enter_rogue() -> list:
    """Rogue Thief: DEX 6+, DEX=8 DM+0, roll=6 — pass."""
    _base = _setup()
    return [
        *_base,
        Event(
            fulfills=(_base[-1].id, 0),
            handler=CareerEntryHandler(career=ROGUE, assignment=ROGUE.assignment('Thief'), qualification_roll=6),
        ),
    ]


def test_career_term_event_is_none_before_term_event():
    projection = replay(1, _enter_army())
    assert projection.summary.career_terms[-1].event is None


def test_term_event_sets_event_narrative():
    # Army event roll=5: "You are given a special assignment or duty in your unit."
    _base = _enter_army()
    ev5 = Event(fulfills=(_base[-1].id, 0), handler=SurviveHandler(roll=5))
    events = [
        *_base,
        ev5,
        Event(fulfills=(ev5.id, 0), handler=TermEventHandler(roll=5)),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].event == (
        'You are given a special assignment or duty in your unit. Gain DM+1 to any one Benefit roll.'
    )


def test_term_event_without_known_roll_leaves_event_none():
    # Roll=99 is not a valid Army event entry; field should stay None.
    _base = _enter_army()
    ev5 = Event(fulfills=(_base[-1].id, 0), handler=SurviveHandler(roll=5))
    events = [
        *_base,
        ev5,
        Event(fulfills=(ev5.id, 0), handler=TermEventHandler(roll=99)),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].event is None


def test_career_term_mishap_is_none_before_mishap():
    projection = replay(1, _enter_army())
    assert projection.summary.career_terms[-1].mishap is None


def test_mishap_ejection_sets_mishap_narrative():
    # Army mishap roll=2: full blame/enemy/removed text
    # Army Support survival: END 5+, DM+0, roll=4 — fail.
    _base = _enter_army()
    ev5 = Event(fulfills=(_base[-1].id, 0), handler=SurviveHandler(roll=4))
    events = [
        *_base,
        ev5,
        Event(fulfills=(ev5.id, 0), handler=MishapHandler(roll=2)),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].mishap == (
        'Your unit is slaughtered in a disastrous battle, for which you blame your commander.'
        ' Gain them as an Enemy as they have you removed from the service.'
    )


def test_stay_in_career_mishap_does_not_set_mishap_narrative():
    # Army event roll=2 triggers "Disaster!" — stay_in_career mishap, not ejected.
    # Army mishap roll=5: "You quarrel with an officer or fellow soldier. Gain a Rival."
    _base = _enter_army()
    ev5 = Event(fulfills=(_base[-1].id, 0), handler=SurviveHandler(roll=5))
    ev6 = Event(fulfills=(ev5.id, 0), handler=TermEventHandler(roll=2))
    events = [
        *_base,
        ev5,
        ev6,
        Event(fulfills=(ev6.id, 0), handler=MishapHandler(roll=5, stay_in_career=True)),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].mishap is None


def test_career_term_prison_is_none_without_prison_path():
    projection = replay(1, _enter_army())
    assert projection.summary.career_terms[-1].prison is None


def test_rogue_mishap_2_arrested_sets_prison_narrative():
    # Rogue Thief mishap 2: "Arrested. You must take the Prisoner career in your next term."
    # Thief survival: INT 6+, DM+1, roll=4 → 5 < 6 — fail.
    _base = _enter_rogue()
    ev5 = Event(fulfills=(_base[-1].id, 0), handler=SurviveHandler(roll=4))
    events = [
        *_base,
        ev5,
        Event(fulfills=(ev5.id, 0), handler=MishapHandler(roll=2)),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].prison is not None
    assert 'Prisoner' in projection.summary.career_terms[-1].prison
