"""Tests for index-based career/assignment identity (replacing string identity checks)."""

from ceres.character.domain.career import NOBLE, SCOUT
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
from tests.character.helpers import MOCK_WORLD, CharacterDriver


def _full_setup():
    from ceres.character.domain.skills import Admin, Athletics, Drive, Electronics

    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Test')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),  # INT=9 EDU=10 → 4 background skills
        Event(
            id=3,
            fulfills=(2, 0),
            handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Drive(), Electronics()]),
        ),
    ]


class TestCareerDataAdvancementIsSpecial:
    def test_base_career_advancement_not_special(self):
        careers = load_careers()
        scout = careers['Scout']
        assert scout.advancement_is_special() is False

    def test_prisoner_advancement_is_special(self):
        careers = load_careers()
        prisoner = careers['Prisoner']
        assert prisoner.advancement_is_special() is True

    def test_all_non_prisoner_careers_not_special(self):
        careers = load_careers()
        non_prisoner = [c for name, c in careers.items() if name != 'Prisoner']
        for career in non_prisoner:
            assert career.advancement_is_special() is False, f'{career.name} should not be special'


class TestCareerDataAssignmentIndex:
    def test_assignment_by_index_returns_first_assignment(self):
        careers = load_careers()
        scout = careers['Scout']
        result = scout.assignment_by_index(1)
        assert result is not None
        assert result.name == 'Courier'

    def test_assignment_by_index_returns_second_assignment(self):
        careers = load_careers()
        scout = careers['Scout']
        result = scout.assignment_by_index(2)
        assert result is not None
        assert result.name == 'Surveyor'

    def test_assignment_by_index_returns_third_assignment(self):
        careers = load_careers()
        scout = careers['Scout']
        result = scout.assignment_by_index(3)
        assert result is not None
        assert result.name == 'Explorer'

    def test_assignment_by_index_returns_none_for_zero(self):
        careers = load_careers()
        scout = careers['Scout']
        assert scout.assignment_by_index(0) is None

    def test_assignment_by_index_returns_none_for_out_of_range(self):
        careers = load_careers()
        scout = careers['Scout']
        assert scout.assignment_by_index(4) is None

    def test_assignment_index_returns_one_for_first(self):
        careers = load_careers()
        scout = careers['Scout']
        assignment = scout.assignments[0]
        assert scout.assignment_index(assignment) == 1

    def test_assignment_index_returns_two_for_second(self):
        careers = load_careers()
        scout = careers['Scout']
        assignment = scout.assignments[1]
        assert scout.assignment_index(assignment) == 2

    def test_assignment_index_returns_three_for_third(self):
        careers = load_careers()
        scout = careers['Scout']
        assignment = scout.assignments[2]
        assert scout.assignment_index(assignment) == 3

    def test_assignment_by_index_round_trips(self):
        careers = load_careers()
        for career in careers.values():
            for i, assignment in enumerate(career.assignments, 1):
                by_index = career.assignment_by_index(i)
                assert by_index is assignment, f'{career.name} index {i} did not round-trip'
                assert career.assignment_index(assignment) == i


class TestAssignmentRanksByIndex:
    def test_assignment_ranks_accepts_int_index(self):
        careers = load_careers()
        noble = careers['Noble']
        # Noble has ranks_by_assignment with 3 assignments
        result = noble.assignment_ranks(1)
        # Assignment 1 is Administrator; rank 1 title is 'Clerk'
        assert result[1].title == 'Clerk'

    def test_assignment_ranks_falls_back_to_default_for_unknown_index(self):
        careers = load_careers()
        scout = careers['Scout']
        # Scout has no ranks_by_assignment, should return default ranks
        result = scout.assignment_ranks(1)
        assert result is scout.ranks

    def test_rank_title_retains_latest_assignment_title_until_replaced(self):
        psion = load_careers()['Psion']
        adept = psion.assignment('Adept')
        assert adept is not None

        assert psion.rank_title(False, 1, adept) == ('1', 'Initiate')
        assert psion.rank_title(False, 2, adept) == ('2', 'Initiate')
        assert psion.rank_title(False, 3, adept) == ('3', 'Acolyte')
        assert psion.rank_title(False, 5, adept) == ('5', 'Acolyte')
        assert psion.rank_title(False, 6, adept) == ('6', 'Master')

    def test_rank_title_before_first_assignment_title_is_empty(self):
        psion = load_careers()['Psion']
        wild_talent = psion.assignment('Wild Talent')
        assert wild_talent is not None

        assert psion.rank_title(False, 0, wild_talent) == ('0', '')

    def test_available_tables_uses_assignment_object(self):
        careers = load_careers()
        scout = careers['Scout']
        courier = scout.assignment_by_index(1)
        edu = 7
        tables = scout.available_tables(edu, courier)
        keys = [t.key for t in tables]
        assert 'assignment1' in keys
        assert 'service_skills' in keys
        assert 'personal_development' in keys
        labels = [t.label for t in tables]
        assert 'Courier' in labels

    def test_available_tables_different_assignments_return_different_tables(self):
        careers = load_careers()
        scout = careers['Scout']
        courier = scout.assignment_by_index(1)
        surveyor = scout.assignment_by_index(2)
        tables_courier = scout.available_tables(7, courier)
        tables_surveyor = scout.available_tables(7, surveyor)
        labels_courier = [t.label for t in tables_courier]
        labels_surveyor = [t.label for t in tables_surveyor]
        assert 'Courier' in labels_courier
        assert 'Surveyor' in labels_surveyor
        assert 'Courier' not in labels_surveyor
        assert 'Surveyor' not in labels_courier


class TestCareerTermIndex:
    def test_career_term_has_assignment_after_career_start(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)
        assert len(projection.summary.career_terms) == 1
        assert projection.summary.career_terms[0].assignment.name == 'Courier'

    def test_career_term_assignment_for_second_assignment(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Surveyor'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[0].assignment.name == 'Surveyor'

    def test_career_term_assignment_for_third_assignment(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Explorer'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[0].assignment.name == 'Explorer'


class TestCurrentAssignment:
    def test_current_assignment_set_after_courier(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_assignment is not None
        assert projection.summary.current_assignment.name == 'Courier'

    def test_current_assignment_set_after_surveyor(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Surveyor'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_assignment is not None
        assert projection.summary.current_assignment.name == 'Surveyor'

    def test_current_assignment_for_noble_administrator(self):
        # Noble requires SOC 10+; with SOC=5 (DM=-1) need roll >= 11
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=NOBLE, assignment=NOBLE.assignment('Administrator'), qualification_roll=11
                ),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_assignment is not None
        assert projection.summary.current_assignment.name == 'Administrator'

    def test_current_assignment_for_noble_dilettante(self):
        # Noble requires SOC 10+; with SOC=5 (DM=-1) need roll >= 11
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=NOBLE, assignment=NOBLE.assignment('Dilettante'), qualification_roll=11
                ),
            ),
        ]
        projection = replay(1, events)
        assert projection.summary.current_assignment is not None
        assert projection.summary.current_assignment.name == 'Dilettante'

    def test_assignment_change_updates_current_assignment(self):
        from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive

        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Scout', 'Courier', roll=7)
        assert d.projection.summary.current_assignment is not None
        assert d.projection.summary.current_assignment.name == 'Courier'
        d.survive(roll=7)
        d.term_event(roll=5)
        d.advancement(roll=9)
        d.switch_assignment('Surveyor', roll=5)
        assert d.projection.summary.current_assignment is not None
        assert d.projection.summary.current_assignment.name == 'Surveyor'


class TestAdvancementEventUsesSpecialMethod:
    """Verify that AdvancementEvent uses advancement_is_special() not career.name == 'Prisoner'."""

    def test_non_prisoner_advancement_applies_normally(self):
        # A Scout Courier survives, then advances — should use normal advancement logic.
        # Survive pending is 4.0, term event 5.0, advancement 6.0 (from career_progress_pending).
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
        # Should not crash and should still be in Scout career
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'
