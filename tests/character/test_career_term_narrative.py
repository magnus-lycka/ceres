"""Tests for CareerTerm narrative fields: event, mishap, prison."""

from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    SkillChoiceEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive
from ceres.character.sophonts import VILANI
from tests.character.helpers import MOCK_WORLD


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5."""
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Test'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _enter_army() -> list:
    """Army Support: END 5+, DM+0, roll=5 — pass."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Army', assignment='Support', qualification_roll=5),
        SkillChoiceEvent(id=5, fulfills='4.0', skill=Drive()),
    ]


def _enter_rogue() -> list:
    """Rogue Thief: DEX 6+, DEX=8 DM+0, roll=6 — pass."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Rogue', assignment='Thief', qualification_roll=6),
    ]


def test_career_term_event_is_none_before_term_event():
    projection = replay(1, _enter_army())
    assert projection.summary.career_terms[-1].event is None


def test_term_event_sets_event_narrative():
    # Army event roll=5: "You are given a special assignment or duty in your unit."
    events = [
        *_enter_army(),
        SurviveEvent(id=6, fulfills='5.0', roll=5),
        TermEventEvent(id=7, fulfills='6.0', roll=5),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].event == ('You are given a special assignment or duty in your unit.')


def test_term_event_without_known_roll_leaves_event_none():
    # Roll=99 is not a valid Army event entry; field should stay None.
    events = [
        *_enter_army(),
        SurviveEvent(id=6, fulfills='5.0', roll=5),
        TermEventEvent(id=7, fulfills='6.0', roll=99),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].event is None


def test_career_term_mishap_is_none_before_mishap():
    projection = replay(1, _enter_army())
    assert projection.summary.career_terms[-1].mishap is None


def test_mishap_ejection_sets_mishap_narrative():
    # Army mishap roll=2: "Your unit is slaughtered in a disastrous battle. Gain the commander as an Enemy."
    # Army Support survival: END 5+, DM+0, roll=4 — fail.
    events = [
        *_enter_army(),
        SurviveEvent(id=6, fulfills='5.0', roll=4),
        MishapEvent(id=7, fulfills='6.0', roll=2),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].mishap == (
        'Your unit is slaughtered in a disastrous battle. Gain the commander as an Enemy.'
    )


def test_stay_in_career_mishap_does_not_set_mishap_narrative():
    # Army event roll=2 triggers "Disaster!" — stay_in_career mishap, not ejected.
    # Army mishap roll=5: "You quarrel with an officer or fellow soldier. Gain a Rival."
    events = [
        *_enter_army(),
        SurviveEvent(id=6, fulfills='5.0', roll=5),
        TermEventEvent(id=7, fulfills='6.0', roll=2),
        MishapEvent(id=8, fulfills='7.0', roll=5, stay_in_career=True),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].mishap is None


def test_career_term_prison_is_none_without_prison_path():
    projection = replay(1, _enter_army())
    assert projection.summary.career_terms[-1].prison is None


def test_rogue_mishap_2_arrested_sets_prison_narrative():
    # Rogue Thief mishap 2: "Arrested. You must take the Prisoner career in your next term."
    # Thief survival: INT 6+, DM+1, roll=4 → 5 < 6 — fail.
    events = [
        *_enter_rogue(),
        SurviveEvent(id=5, fulfills='4.0', roll=4),
        MishapEvent(id=6, fulfills='5.0', roll=2),
    ]
    projection = replay(1, events)
    assert projection.summary.career_terms[-1].prison is not None
    assert 'Prisoner' in projection.summary.career_terms[-1].prison
