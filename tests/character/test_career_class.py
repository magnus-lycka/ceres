"""Tests for the typed Career identifier class."""

import pytest

from ceres.character.domain.career import (
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
from ceres.character.domain.career.career_data import CareerData
from ceres.character.domain.career.career_events import (
    AdvancementHandler,
    CareerEntryHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.loader import load_careers
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD


def _full_setup():
    from ceres.character.domain.skills import Admin, Athletics, Drive, Electronics

    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Test')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3,
            fulfills=(2, 0),
            handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Drive(), Electronics()]),
        ),
    ]


class TestCareerClass:
    def test_career_equality_by_type(self):
        assert load_careers()['Scout'] == SCOUT

    def test_career_inequality_different_name(self):
        assert SCOUT != ARMY

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
    def test_career_data_name_matches(self):
        careers = load_careers()
        assert careers['Scout'].name == 'Scout'
        assert careers['Prisoner'].name == 'Prisoner'

    def test_career_data_source_is_core(self):
        careers = load_careers()
        for career_data in careers.values():
            assert career_data.source == 'Core'

    def test_career_data_equals_constant(self):
        careers = load_careers()
        assert careers['Scout'] == SCOUT
        assert careers['Prisoner'] == PRISONER
        assert careers['Marines'] == MARINES


class TestCareerInState:
    def test_current_career_is_career_data_after_joining(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)
        assert isinstance(projection.summary.current_career, CareerData)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'

    def test_current_career_equals_constant(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career == SCOUT

    def test_career_term_career_is_career_data(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)
        term = projection.summary.career_terms[0]
        assert isinstance(term.career, CareerData)
        assert term.career.name == 'Scout'

    def test_career_term_career_equals_constant(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[0].career == SCOUT

    def test_survive_keeps_current_career_as_career_data(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=8)),
        ]
        projection = replay(1, events)
        assert isinstance(projection.summary.current_career, CareerData)
        assert projection.summary.current_career == SCOUT

    def test_after_term_advancement_still_career_object(self):

        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=8)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career == SCOUT


class TestCareersInit:
    def test_load_careers_accessible_via_package(self):
        import ceres.character.domain.career as careers_pkg

        fn = careers_pkg.load_careers
        assert callable(fn)

    def test_selectable_careers_accessible_via_package(self):
        import ceres.character.domain.career as careers_pkg

        fn = careers_pkg.selectable_careers
        assert callable(fn)

    def test_unknown_attribute_raises(self):
        import ceres.character.domain.career as careers_pkg

        with pytest.raises(AttributeError):
            _ = careers_pkg.NonExistentCareer


class TestCareerDataCoverageGaps:
    def test_handler_base_default_handle_returns_pending_idx(self):
        from ceres.character.domain.career.career_data import CareerHandlerBase
        from ceres.character.domain.character_state import CharacterProjection, CharacterSummary

        class MinimalHandler(CareerHandlerBase):
            type: str = 'test'

        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        result = MinimalHandler.handle(proj, 5, 3)
        assert result == 3

    def test_officer_skill_table_returns_table(self):
        army = load_careers()['Army']
        table = army.skill_table('officer')
        assert table is not None

    def test_can_attempt_commission_returns_false_when_already_commissioned(self):
        from ceres.character.domain.career.career_data import CareerTerm
        from ceres.character.domain.character_state import CharacterProjection, CharacterSummary

        army = load_careers()['Army']
        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        proj.summary.career_terms.append(CareerTerm(career=army, assignment='Infantry', commission=True))
        assert army.can_attempt_commission(proj) is False

    def test_can_attempt_commission_soc_check_after_two_terms(self):
        from ceres.character.domain.career.career_data import CareerTerm
        from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
        from ceres.character.domain.characteristics import Chars

        army = load_careers()['Army']
        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(
                name='Test',
                sophont=VILANI,
                homeworld=MOCK_WORLD,
                characteristics={Chars.SOC: 7},
            ),
        )
        proj.summary.career_terms.extend(
            [
                CareerTerm(career=army, assignment='Infantry'),
                CareerTerm(career=army, assignment='Infantry'),
            ]
        )
        assert army.can_attempt_commission(proj) is False

    def test_apply_rank_bonus_characteristic_increase(self):
        from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
        from ceres.character.domain.characteristics import Chars

        merchant = load_careers()['Merchant']
        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(
                name='Test',
                sophont=VILANI,
                homeworld=MOCK_WORLD,
                current_career=merchant,
                current_assignment=merchant.assignment('Merchant Marine'),
                rank=4,
                characteristics={Chars.INT: 9, Chars.SOC: 5},
            ),
        )
        merchant._apply_fixed_rank_bonus(proj, 5)
        assert proj.summary.characteristics.get(Chars.SOC) == 6
