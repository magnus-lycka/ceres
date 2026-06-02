"""Tests for the typed Career identifier class."""

import pytest

from ceres.character.careers import (
    AGENT,
    ARMY,
    CITIZEN,
    DRIFTER,
    ENTERTAINER,
    MARINES,
    MERCHANT,
    NAVY,
    NOBLE,
    PRISONER,
    ROGUE,
    SCHOLAR,
    SCOUT,
)
from ceres.character.careers.career_data import Career
from ceres.character.careers.loader import load_careers
from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerEvent,
    CharacterStartedEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import replay
from ceres.character.sophonts import VILANI
from tests.character.helpers import MOCK_WORLD


def _full_setup():
    from ceres.character.skills import Admin, Athletics, Drive, Electronics

    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Test'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Drive(), Electronics()]),
    ]


class TestCareerClass:
    def test_career_equality_by_value(self):
        assert Career(name='Scout', source='Core') == Career(name='Scout', source='Core')

    def test_career_inequality_different_name(self):
        assert Career(name='Scout', source='Core') != Career(name='Army', source='Core')

    def test_career_inequality_different_source(self):
        assert Career(name='Scout', source='Core') != Career(name='Scout', source='Other')

    def test_career_hashable(self):
        c = Career(name='Scout', source='Core')
        assert hash(c) == hash(Career(name='Scout', source='Core'))
        s = {c}
        assert Career(name='Scout', source='Core') in s

    def test_career_immutable(self):
        c = Career(name='Scout', source='Core')
        with pytest.raises((TypeError, AttributeError)):
            c.name = 'Army'  # type: ignore

    def test_career_has_description(self):
        assert SCOUT.description != ''
        assert 'explore' in SCOUT.description.lower()


class TestCareerConstants:
    def test_all_thirteen_constants_exist(self):
        constants = [
            AGENT,
            ARMY,
            CITIZEN,
            DRIFTER,
            ENTERTAINER,
            MARINES,
            MERCHANT,
            NAVY,
            NOBLE,
            PRISONER,
            ROGUE,
            SCHOLAR,
            SCOUT,
        ]
        assert len(constants) == 13

    def test_all_constants_source_is_core(self):
        constants = [
            AGENT,
            ARMY,
            CITIZEN,
            DRIFTER,
            ENTERTAINER,
            MARINES,
            MERCHANT,
            NAVY,
            NOBLE,
            PRISONER,
            ROGUE,
            SCHOLAR,
            SCOUT,
        ]
        for c in constants:
            assert c.source == 'Core', f'{c.name}.source should be Core'

    def test_prisoner_constant_name(self):
        assert PRISONER.name == 'Prisoner'

    def test_scout_constant_name(self):
        assert SCOUT.name == 'Scout'

    def test_constants_match_registry_names(self):
        careers = load_careers()
        constants = [
            AGENT,
            ARMY,
            CITIZEN,
            DRIFTER,
            ENTERTAINER,
            MARINES,
            MERCHANT,
            NAVY,
            NOBLE,
            PRISONER,
            ROGUE,
            SCHOLAR,
            SCOUT,
        ]
        registry_names = set(careers.keys())
        constant_names = {c.name for c in constants}
        assert constant_names == registry_names


class TestCareerDataCareerField:
    def test_career_data_has_career_attribute(self):
        careers = load_careers()
        scout = careers['Scout']
        assert hasattr(scout, 'career')
        assert isinstance(scout.career, Career)

    def test_career_data_career_name_matches(self):
        careers = load_careers()
        assert careers['Scout'].career.name == 'Scout'
        assert careers['Prisoner'].career.name == 'Prisoner'

    def test_career_data_career_source_is_core(self):
        careers = load_careers()
        for career_data in careers.values():
            assert career_data.career.source == 'Core'

    def test_career_data_name_property_delegates(self):
        careers = load_careers()
        for career_data in careers.values():
            assert career_data.name == career_data.career.name

    def test_career_data_career_equals_constant(self):
        careers = load_careers()
        assert careers['Scout'].career == SCOUT
        assert careers['Prisoner'].career == PRISONER
        assert careers['Marines'].career == MARINES


class TestCareerInState:
    def test_current_career_is_career_object_after_joining(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]
        projection = replay(1, events)
        assert isinstance(projection.summary.current_career, Career)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'

    def test_current_career_equals_constant(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career == SCOUT

    def test_career_term_career_is_career_object(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]
        projection = replay(1, events)
        term = projection.summary.career_terms[0]
        assert isinstance(term.career, Career)
        assert term.career.name == 'Scout'

    def test_career_term_career_equals_constant(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[0].career == SCOUT

    def test_survive_keeps_current_career_as_career_object(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=8),
        ]
        projection = replay(1, events)
        assert isinstance(projection.summary.current_career, Career)
        assert projection.summary.current_career == SCOUT

    def test_after_term_advancement_still_career_object(self):
        from ceres.character.events import AdvancementEvent

        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=8),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career == SCOUT
