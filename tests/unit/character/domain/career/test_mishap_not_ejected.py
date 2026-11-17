"""Event 2: "Disaster! Roll on the Mishap table but you are not ejected from this career." (RIC-031)

Some mishaps end the career only after a follow-up roll or choice. "Not ejected" still applies to them,
whatever the player chooses: the Traveller stays, keeps this term's Benefit roll and makes the
advancement roll. It does not protect against a prison sentence.
"""

from ceres.character.domain.career.agent import AgentMishap2Accept
from ceres.character.domain.career.citizen import CitizenMishap4Cooperate
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.marines import MarinesMishap4Refuse
from ceres.character.domain.career.navy import NavyMishap4Responsible
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Advocate, Athletics, Carouse, Drive, Streetwise
from ceres.character.domain.sophont import VILANI
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver


def _in_term_3_event(career: str, assignment: str, event_roll: int) -> CharacterDriver:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5, first term, survived, then the given event."""
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('7869A5')
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    d.career(career, assignment, roll=12)
    d.survive(12)
    d.term_event(event_roll)
    return d


def _career_name(d: CharacterDriver) -> str | None:
    career = d.projection.summary.current_career
    return career.name if career is not None else None


def _citizen_after_disaster(mishap_roll: int) -> CharacterDriver:
    d = _in_term_3_event('Citizen', 'Corporate', 2)
    d.mishap(mishap_roll)
    return d


class TestFollowUpMishapsDoNotEject:
    def test_severely_injured_stays_in_career(self):
        d = _citizen_after_disaster(1)
        d.career_choice(CommonMishap1Severe)
        d.severely_injured(Chars.STR, 2)
        assert _career_name(d) == 'Citizen'
        assert d.projection.summary.characteristics[Chars.STR] == 5

    def test_injured_twice_stays_in_career(self):
        d = _citizen_after_disaster(1)
        d.career_choice(CommonMishap1DoubleRoll)
        assert _career_name(d) == 'Citizen'

    def test_forced_off_planet_stays_in_career_on_success(self):
        d = _citizen_after_disaster(5)
        d.skill_roll(Streetwise(), 9)
        assert _career_name(d) == 'Citizen'

    def test_forced_off_planet_stays_in_career_on_failure(self):
        d = _citizen_after_disaster(5)
        d.skill_roll(Streetwise(), 3)
        assert _career_name(d) == 'Citizen'

    def test_a_mishap_choice_that_is_not_about_leaving_stays_in_career(self):
        d = _citizen_after_disaster(4)
        d.career_choice(CitizenMishap4Cooperate)
        assert _career_name(d) == 'Citizen'

    def test_a_mishap_that_ends_the_career_without_the_shared_helper_stays_in_career(self):
        # Agent mishap 3, "ruining your career", resolves through its own Advocate roll.
        d = _in_term_3_event('Agent', 'Law Enforcement', 2)
        d.mishap(3)
        d.skill_roll(Advocate(), 5)
        assert _career_name(d) == 'Agent'

    def test_a_betrayal_stays_in_career_and_the_history_does_not_say_it_ended(self):
        d = _in_term_3_event('Rogue', 'Thief', 2)
        d.mishap(3)
        d.betrayal_mishap('enemy', 7, name='Dana Okoye')
        assert _career_name(d) == 'Rogue'
        assert 'Career ended.' not in d.projection.creation_history[-1]


class TestTheCareerContinues:
    def test_the_advancement_roll_follows(self):
        d = _citizen_after_disaster(5)
        d.skill_roll(Streetwise(), 3)
        d.advancement(12)
        assert d.projection.summary.rank == 1

    def test_this_terms_benefit_roll_is_kept(self):
        disaster = _citizen_after_disaster(5)
        disaster.skill_roll(Streetwise(), 3)
        disaster.advancement(2)
        disaster.reenlist(False)
        quiet = _in_term_3_event('Citizen', 'Corporate', 9)  # rewarded: an advancement DM, nothing else
        quiet.advancement(2)
        quiet.reenlist(False)
        assert disaster.benefit_rolls_at_muster_out() == quiet.benefit_rolls_at_muster_out()


class TestNoMishapChoiceEndsTheCareer:
    """The mishap's choices change other things; ending the career is the mishap's, and event 2 voids it."""

    def test_accepting_the_criminals_deal(self):
        d = _in_term_3_event('Agent', 'Law Enforcement', 2)
        d.mishap(2)
        d.career_choice(AgentMishap2Accept)
        assert _career_name(d) == 'Agent'

    def test_refusing_the_black_ops_mission(self):
        d = _in_term_3_event('Marines', 'Support', 2)
        d.mishap(4)
        d.career_choice(MarinesMishap4Refuse)
        assert _career_name(d) == 'Marines'

    def test_accepting_responsibility_for_the_accident(self):
        d = _in_term_3_event('Navy', 'Line/Crew', 2)
        d.mishap(4)
        d.career_choice(NavyMishap4Responsible)
        assert _career_name(d) == 'Navy'


class TestPrisonSentences:
    """Not being ejected does not protect against prison: it is served from the next term."""

    def test_an_arrest_still_sends_the_traveller_to_prison_next_term(self):
        d = _in_term_3_event('Rogue', 'Thief', 2)
        d.mishap(2)  # Arrested. You must take the Prisoner career in your next term.
        assert _career_name(d) == 'Rogue'
        d.advancement(2)
        assert _career_name(d) is None
        assert d.benefit_rolls_at_muster_out() == 1  # not ejected: this term's Benefit roll is kept
        assert [career.name for career in d.career_choice_options()] == ['Prisoner']

    def test_a_crime_life_event_sends_the_traveller_to_prison_next_term(self):
        d = _in_term_3_event('Citizen', 'Corporate', 7)
        d.life_event(11)
        d.crime_consequence('prison')
        d.advancement(2)
        assert _career_name(d) is None
        d.benefit_rolls_at_muster_out()
        assert [career.name for career in d.career_choice_options()] == ['Prisoner']


class TestWithoutEvent2:
    def test_forced_off_planet_still_ends_the_career(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Citizen', 'Corporate', roll=12)
        d.survive(2)
        d.mishap(5)
        d.skill_roll(Streetwise(), 9)
        assert _career_name(d) is None


class TestPrompts:
    def test_forced_off_planet_prompt_is_the_rule_without_an_ejection_claim(self):
        d = _citizen_after_disaster(5)
        assert d.next_instruction() == 'Roll Streetwise 8+: on success, increase any skill you have by one level'

    def test_assassin_prompt_is_the_rule_without_an_ejection_claim(self):
        d = _in_term_3_event('Noble', 'Administrator', 2)
        d.mishap(5)
        assert d.next_instruction() == 'Roll END 8+: on failure, roll on the Injury table'
