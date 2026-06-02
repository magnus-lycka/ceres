"""Tests for index-based career/assignment identity (replacing string identity checks)."""

from ceres.character.careers.loader import load_careers
from ceres.character.events import (
    AdvancementEvent,
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
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),  # INT=9 EDU=10 → 4 background skills
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Drive(), Electronics()]),
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

    def test_available_tables_uses_int_assignment_index(self):
        careers = load_careers()
        scout = careers['Scout']
        edu = 7
        # Courier is assignment index 1
        tables = scout.available_tables(edu, 1)
        assert 'courier' in tables
        assert 'service_skills' in tables
        assert 'personal_development' in tables

    def test_available_tables_different_assignments_return_different_tables(self):
        careers = load_careers()
        scout = careers['Scout']
        tables_courier = scout.available_tables(7, 1)
        tables_surveyor = scout.available_tables(7, 2)
        assert 'courier' in tables_courier
        assert 'surveyor' in tables_surveyor
        assert 'courier' not in tables_surveyor
        assert 'surveyor' not in tables_courier


class TestCareerTermIndex:
    def test_career_term_has_assignment_index_after_career_start(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]
        projection = replay(1, events)
        assert len(projection.summary.career_terms) == 1
        assert projection.summary.career_terms[0].assignment_index == 1  # Courier is index 1

    def test_career_term_assignment_index_for_second_assignment(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Surveyor', qualification_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[0].assignment_index == 2  # Surveyor is index 2

    def test_career_term_assignment_index_for_third_assignment(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Explorer', qualification_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[0].assignment_index == 3  # Explorer is index 3


class TestCurrentAssignmentIndex:
    def test_current_assignment_index_set_after_courier(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.current_assignment_index == 1
        assert projection.summary.current_assignment == 'Courier'  # string still present for display

    def test_current_assignment_index_set_after_surveyor(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Surveyor', qualification_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.current_assignment_index == 2

    def test_current_assignment_index_for_noble_administrator(self):
        # Noble requires SOC 10+; with SOC=5 (DM=-1) need roll >= 11
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Noble', assignment='Administrator', qualification_roll=11),
        ]
        projection = replay(1, events)
        assert projection.summary.current_assignment_index == 1

    def test_current_assignment_index_for_noble_dilettante(self):
        # Noble requires SOC 10+; with SOC=5 (DM=-1) need roll >= 11
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Noble', assignment='Dilettante', qualification_roll=11),
        ]
        projection = replay(1, events)
        assert projection.summary.current_assignment_index == 3

    def test_assignment_change_updates_index(self):
        from ceres.character.events import AssignmentChangeChoiceEvent

        # Noble requires SOC 10+; with SOC=5 (DM=-1) need roll >= 11
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Noble', assignment='Administrator', qualification_roll=11),
        ]
        projection = replay(1, events)
        assert projection.summary.current_assignment_index == 1
        # Noble allows assignment changes; simulate it
        from ceres.character.events import PendingAssignmentChangeChoice

        # Find if there's a pending assignment change (there won't be mid-term, but we test the event directly)
        # We'll apply an AssignmentChangeChoiceEvent directly
        projection2 = projection.model_copy(deep=True)
        projection2.pending_inputs.append(
            PendingAssignmentChangeChoice(
                id='99.0',
                instruction='Change assignment',
                options=['Administrator', 'Diplomat', 'Dilettante'],
            )
        )

        event = AssignmentChangeChoiceEvent(id=100, fulfills='99.0', choice='Diplomat', qualification_roll=12)
        event.apply(projection2)
        assert projection2.summary.current_assignment == 'Diplomat'
        assert projection2.summary.current_assignment_index == 2


class TestAdvancementEventUsesSpecialMethod:
    """Verify that AdvancementEvent uses advancement_is_special() not career.name == 'Prisoner'."""

    def test_non_prisoner_advancement_applies_normally(self):
        # A Scout Courier survives, then advances — should use normal advancement logic.
        # Survive pending is 4.0, term event 5.0, advancement 6.0 (from career_progress_pending).
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=8),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=9),
        ]
        projection = replay(1, events)
        # Should not crash and should still be in Scout career
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Scout'
