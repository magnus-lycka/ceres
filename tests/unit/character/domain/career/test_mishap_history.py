"""A mishap that ends the career says so in the history, once, however the ending comes about."""

from ceres.character.domain.career.common import CommonMishap1Severe
from ceres.character.domain.career.scholar import ScholarMishap5GiveUp
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Advocate, Athletics, Carouse, Drive, LifeScience, Streetwise
from ceres.character.domain.sophont import VILANI
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver


def _failed_survival(career: str, assignment: str) -> CharacterDriver:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5, first term, survival failed with a 2."""
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('7869A5')
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    d.career(career, assignment, roll=12)
    if career == 'Scholar':
        d.initial_training(LifeScience())
    d.survive(2)
    return d


def _mishap_entry(d: CharacterDriver) -> str:
    return next(entry for entry in d.projection.creation_history if entry.startswith('Term 1 mishap ('))


class TestCareerEndedIsTold:
    def test_after_a_follow_up_roll(self):
        d = _failed_survival('Citizen', 'Corporate')
        d.mishap(5)
        d.skill_roll(Streetwise(), 9)
        assert _mishap_entry(d).count('Career ended.') == 1

    def test_after_a_follow_up_choice(self):
        d = _failed_survival('Citizen', 'Corporate')
        d.mishap(1)
        d.career_choice(CommonMishap1Severe)
        d.severely_injured(Chars.STR, 2)
        assert _mishap_entry(d).count('Career ended.') == 1

    def test_when_the_mishap_ends_the_career_by_its_own_route(self):
        d = _failed_survival('Agent', 'Law Enforcement')
        d.mishap(3)
        d.skill_roll(Advocate(), 5)
        assert _mishap_entry(d).count('Career ended.') == 1

    def test_when_the_traveller_gives_up(self):
        d = _failed_survival('Scholar', 'Field Researcher')
        d.mishap(5)
        d.career_choice(ScholarMishap5GiveUp)
        assert _mishap_entry(d).count('Career ended.') == 1

    def test_an_immediate_mishap_is_told_once(self):
        d = _failed_survival('Citizen', 'Corporate')
        d.mishap(3)  # lose one SOC; ends the career at once
        assert _mishap_entry(d).count('Career ended.') == 1


class TestNothingEndedIsNotTold:
    def test_a_mishap_after_event_2_does_not_end_the_career(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Citizen', 'Corporate', roll=12)
        d.survive(12)
        d.term_event(2)
        d.mishap(5)
        d.skill_roll(Streetwise(), 9)
        assert 'Career ended.' not in d.projection.creation_history[-1]
