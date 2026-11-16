"""Rule tests for School of Hard Knocks graduation benefits (Traveller Companion).

"Gain any three other skills listed above at level 0."
"DM-2 on checks to gain promotion or commission in first career. If the
Traveller leaves this career by choice, checks in subsequent careers are as
normal." Read as recorded in RIC-029.
"""

from ceres.character.domain.precareer.school_of_hard_knocks import SchoolOfHardKnocksPreCareer
from ceres.character.domain.skills import (
    Admin,
    Animals,
    AnySkill,
    Athletics,
    Carouse,
    Deception,
    Drive,
    Gambler,
    Melee,
    Persuade,
    Stealth,
)
from ceres.character.domain.sophont import VILANI
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver

# A term event that only adds a Benefit DM, in both Army and Citizen.
_QUIET_EVENT = 5


def _student(background: list[AnySkill], event_roll: int = 12) -> CharacterDriver:
    """STR DEX END INT EDU all 7 (DM+0), SOC 5: enters automatically, takes Deception and Gambler."""
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('777775')
    d.background_skills(background)
    d.precareer(SchoolOfHardKnocksPreCareer, roll=7)
    d.precareer_skill(Deception())
    d.precareer_skill(Gambler())
    d.precareer_event(event_roll)
    return d


def _graduate() -> CharacterDriver:
    """Graduates (INT 7+ on a 7) with Melee, Persuade and Stealth. SOC is now 4 (DM-1)."""
    d = _student([Admin(), Animals(), Carouse()])
    d.precareer_graduation(7)
    d.precareer_skill(Melee())
    d.precareer_skill(Persuade())
    d.precareer_skill(Stealth())
    return d


def _non_graduate() -> CharacterDriver:
    d = _student([Admin(), Animals(), Carouse()])
    d.precareer_graduation(6)
    return d


def _to_advancement(d: CharacterDriver) -> CharacterDriver:
    """Survive the term and pass a quiet event, declining any commission attempt."""
    d.survive(9)
    d.term_event(_QUIET_EVENT)
    if d.has_commission_choice():
        d.commission(attempt=False)
    return d


def _leave_by_choice(d: CharacterDriver) -> CharacterDriver:
    d.reenlist(False)
    while d.has_muster_out_roll():
        d.muster_out('cash', 1)
    return d


def _rank(d: CharacterDriver) -> int:
    return d.projection.summary.rank or 0


class TestGraduationSkills:
    def test_offers_only_listed_skills_not_already_held(self):
        d = _student([Admin(), Animals(), Carouse()])
        d.precareer_graduation(7)
        assert d.precareer_skill_options() == ['Athletics', 'Drive', 'Melee', 'Persuade', 'Stealth']

    def test_a_skill_gained_at_graduation_is_not_offered_again(self):
        d = _student([Admin(), Animals(), Carouse()])
        d.precareer_graduation(7)
        d.precareer_skill(Drive())
        assert d.precareer_skill_options() == ['Athletics', 'Melee', 'Persuade', 'Stealth']

    def test_skills_held_from_elsewhere_are_not_offered(self):
        d = _student([Admin(), Athletics(), Drive()])
        d.precareer_graduation(7)
        assert d.precareer_skill_options() == ['Melee', 'Persuade', 'Stealth']

    def test_three_skills_are_chosen(self):
        d = _student([Admin(), Animals(), Carouse()])
        d.precareer_graduation(7)
        assert d.precareer_skill_choices_left() == 3

    def test_fewer_skills_are_chosen_when_fewer_than_three_remain(self):
        # Pre-career event 9: a hobby grants any skill at level 0.
        d = _student([Admin(), Athletics(), Drive()], event_roll=9)
        d.choose_skill(Melee())
        d.precareer_graduation(7)
        assert d.precareer_skill_options() == ['Persuade', 'Stealth']
        assert d.precareer_skill_choices_left() == 2


class TestPromotionAndCommissionDm:
    def test_is_not_left_as_a_manual_problem(self):
        assert _graduate().projection.summary.problems == []

    def test_advancement_roll_suffers_dm_minus_2(self):
        d = _graduate()
        d.career('Army', 'Support', roll=12)
        _to_advancement(d).advancement(8)  # EDU 7+: 8 + 0 - 2 = 6
        assert _rank(d) == 0

    def test_advancement_still_succeeds_on_a_high_enough_roll(self):
        d = _graduate()
        d.career('Army', 'Support', roll=12)
        _to_advancement(d).advancement(9)  # EDU 7+: 9 + 0 - 2 = 7
        assert _rank(d) == 1

    def test_commission_roll_suffers_dm_minus_2(self):
        d = _graduate()
        d.career('Army', 'Support', roll=12)
        d.survive(9)
        d.term_event(_QUIET_EVENT)
        d.commission(attempt=True, roll=10)  # SOC 8+: 10 - 1 - 2 = 7
        assert not d.projection.summary.career_terms[-1].commission

    def test_commission_still_succeeds_on_a_high_enough_roll(self):
        d = _graduate()
        d.career('Army', 'Support', roll=12)
        d.survive(9)
        d.term_event(_QUIET_EVENT)
        d.commission(attempt=True, roll=11)  # SOC 8+: 11 - 1 - 2 = 8
        assert d.projection.summary.career_terms[-1].commission

    def test_a_student_who_did_not_graduate_has_no_dm(self):
        d = _non_graduate()
        d.career('Army', 'Support', roll=12)
        _to_advancement(d).advancement(7)  # EDU 7+: 7 + 0
        assert _rank(d) == 1

    def test_applies_in_every_term_of_the_career(self):
        d = _graduate()
        d.career('Army', 'Support', roll=12)
        _to_advancement(d).advancement(8)
        d.reenlist(True)
        _to_advancement(d).advancement(8)
        assert _rank(d) == 0

    def test_follows_a_traveller_who_is_forced_out(self):
        d = _graduate()
        d.career('Army', 'Support', roll=12)
        d.survive(2)
        d.mishap(5)  # driven out of the service by a Rival
        d.name_connection('Rival')
        d.career('Citizen', 'Worker', roll=12)
        _to_advancement(d).advancement(9)  # EDU 8+: 9 + 0 - 2 = 7
        assert _rank(d) == 0

    def test_ends_when_the_traveller_leaves_a_career_by_choice(self):
        d = _graduate()
        d.career('Army', 'Support', roll=12)
        _to_advancement(d).advancement(8)
        _leave_by_choice(d)
        d.career('Citizen', 'Worker', roll=12)
        _to_advancement(d).advancement(8)  # EDU 8+: 8 + 0
        assert _rank(d) == 1

    def test_stays_after_a_change_of_assignment_within_the_army(self):
        d = _graduate()
        d.career('Army', 'Support', roll=12)
        _to_advancement(d).advancement(8)
        d.switch_assignment('Infantry', roll=12)
        _to_advancement(d).advancement(7)  # Infantry EDU 6+: 7 + 0 - 2 = 5
        assert _rank(d) == 0

    def test_ends_with_a_new_assignment_in_citizen_which_is_a_new_career(self):
        d = _graduate()
        d.career('Citizen', 'Worker', roll=12)
        _to_advancement(d).advancement(9)  # EDU 8+: 9 + 0 - 2 = 7
        assert _rank(d) == 0
        _leave_by_choice(d)
        d.career('Citizen', 'Colonist', roll=12)
        _to_advancement(d).advancement(5)  # END 5+: 5 + 0
        assert _rank(d) == 1
