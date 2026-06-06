"""Tests for aging: age tracking, aging roll effects, and aging crisis."""

import pytest

from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, Pilot
from ceres.character.domain.sophont import VILANI
from ceres.character.events import (
    PendingAgingChoice,
    PendingAgingChoiceMental,
    PendingAgingCrisis,
    PendingAgingRoll,
    PendingMusterOut,
    PendingSkillTable,
)
from ceres.character.mechanism.replay import ReplayError
from tests.character.helpers import MOCK_WORLD, CharacterDriver


def _make_setup(name: str = 'Boss', ucp: str = '7869A5') -> CharacterDriver:
    """Character after ucp + 4 background skills. STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5."""
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD, player='NPC', name=name)
    d.ucp(ucp)
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    return d


def _scout_term(d: CharacterDriver, advancement_roll: int) -> None:
    """Drive one continuation Scout Courier term through advancement (no reenlist — caller decides)."""
    d.skill_table('service_skills', 1)  # Pilot: specialized, requires a choice
    d.skill_table_choice(Pilot())
    d.survive(7)
    d.term_event(5)
    d.advancement(advancement_roll)


def _make_3_terms() -> CharacterDriver:
    """3 Scout Courier terms completed. Age=30. PendingSkillTable for term 4 pending."""
    d = _make_setup()
    # Term 1: basic training grants all service skills at 0, then PendingSurvive directly
    d.career('Scout', 'Courier', roll=7)
    d.survive(7)
    d.term_event(5)
    d.advancement(3)  # EDU 9+, DM+1: 3+1=4 < 9 → fail; age=22
    d.reenlist(True)
    # Terms 2 and 3: continuation, each starts with PendingSkillTable
    _scout_term(d, advancement_roll=3)
    d.reenlist(True)  # age=26, term 3 starts
    _scout_term(d, advancement_roll=4)
    d.reenlist(True)  # age=30, term 4 starts → PendingSkillTable
    return d


def _make_4_terms_advanced() -> CharacterDriver:
    """4th term through advancement. Age=34. PendingAgingRoll pending."""
    d = _make_3_terms()
    d.skill_table('service_skills', 1)
    d.skill_table_choice(Pilot())
    d.survive(7)
    d.term_event(5)
    d.advancement(5)  # 5+1=6 < 9 → fail; age=34 → PendingAgingRoll
    return d


def _make_low_str_setup() -> CharacterDriver:
    """Character with STR=1 for aging crisis tests. UCP '1869A5'."""
    return _make_setup(ucp='1869A5')


def _make_low_str_4_terms_advanced() -> CharacterDriver:
    """Low-STR character through 4 terms to advancement. Age=34. PendingAgingRoll pending."""
    d = _make_low_str_setup()
    d.career('Scout', 'Courier', roll=7)
    d.survive(7)
    d.term_event(5)
    d.advancement(3)
    d.reenlist(True)
    _scout_term(d, advancement_roll=3)
    d.reenlist(True)
    _scout_term(d, advancement_roll=4)
    d.reenlist(True)
    d.skill_table('service_skills', 1)
    d.skill_table_choice(Pilot())
    d.survive(7)
    d.term_event(5)
    d.advancement(5)
    return d


def _make_5_terms_advanced() -> CharacterDriver:
    """5th term through advancement. Age=38. PendingAgingRoll pending.

    Aging after term 4 resolves with no effect (roll=5, effective=1). Term 5 uses
    service_skills roll=2 (Survival — not specialized, no choice pending).
    Advancement fails → age=38 → PendingAgingRoll.
    """
    d = _make_4_terms_advanced()
    d.aging_roll(5)  # effective=5-4=1 → no effect → PendingAssignmentChangeChoice
    d.reenlist(True)  # term 5 starts → PendingSkillTable
    d.skill_table('service_skills', 2)  # Survival: non-specialized, no choice needed
    d.survive(10)
    d.term_event(5)
    d.advancement(6)  # 6+1=7 < 9 → fail; age=38 → PendingAgingRoll
    return d


def _make_8_terms_advanced(ucp: str) -> CharacterDriver:
    """8 Scout Courier terms through advancement. Age=50. PendingAgingRoll pending.

    Uses EDU=3 (DM-1) so advancement always fails (EDU 9+, max roll+DM < 9).
    Aging rolls at terms 5-8 use effective=1 (no effect).
    """
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD, player='NPC', name='Test')
    d.ucp(ucp)
    d.background_skills([Admin(), Athletics()])  # EDU=3: DM-1, count=2
    # Term 1 (basic training)
    d.career('Scout', 'Courier', roll=7)
    d.survive(7)
    d.term_event(5)
    d.advancement(3)  # age=22
    d.reenlist(True)
    # Terms 2-3 (no aging)
    _scout_term(d, advancement_roll=3)
    d.reenlist(True)  # age=26, term 3 starts
    _scout_term(d, advancement_roll=4)
    d.reenlist(True)  # age=30, term 4 starts
    # Term 4 (age → 34 → PendingAgingRoll)
    d.skill_table('service_skills', 1)
    d.skill_table_choice(Pilot())
    d.survive(7)
    d.term_event(5)
    d.advancement(5)  # age=34 → PendingAgingRoll
    # Aging 4: effective=5-4=1 → no effect
    d.aging_roll(5)
    d.reenlist(True)  # term 5 starts
    # Term 5 (age → 38)
    d.skill_table('service_skills', 1)
    d.skill_table_choice(Pilot())
    d.survive(7)
    d.term_event(5)
    d.advancement(6)  # age=38 → PendingAgingRoll
    # Aging 5: effective=6-5=1 → no effect
    d.aging_roll(6)
    d.reenlist(True)  # term 6 starts
    # Term 6 (age → 42)
    d.skill_table('service_skills', 1)
    d.skill_table_choice(Pilot())
    d.survive(7)
    d.term_event(5)
    d.advancement(7)  # age=42 → PendingAgingRoll
    # Aging 6: effective=7-6=1 → no effect
    d.aging_roll(7)
    d.reenlist(True)  # term 7 starts
    # Term 7 (age → 46)
    d.skill_table('service_skills', 1)
    d.skill_table_choice(Pilot())
    d.survive(7)
    d.term_event(5)
    d.advancement(8)  # age=46 → PendingAgingRoll
    # Aging 7: effective=8-7=1 → no effect
    d.aging_roll(8)
    d.reenlist(True)  # term 8 starts
    # Term 8 (age → 50)
    d.skill_table('service_skills', 1)
    d.skill_table_choice(Pilot())
    d.survive(7)
    d.term_event(5)
    d.advancement(9)  # age=50 → PendingAgingRoll
    return d


class TestAgeTracking:
    """Character age starts at 18 and increases by 4 per completed term."""

    def test_reenlist_false_increments_age_by_4(self):
        d = _make_setup()
        d.career('Scout', 'Courier', roll=7)
        d.survive(7)
        d.term_event(5)
        d.advancement(5)
        d.reenlist(False)

        assert d.projection.summary.age == 22

    def test_reenlist_true_also_increments_age_by_4(self):
        d = _make_setup()
        d.career('Scout', 'Courier', roll=7)
        d.survive(7)
        d.term_event(5)
        d.advancement(5)
        d.reenlist(True)

        assert d.projection.summary.age == 22

    def test_two_terms_adds_8_years(self):
        d = _make_setup()
        d.career('Scout', 'Courier', roll=7)
        d.survive(7)
        d.term_event(5)
        d.advancement(5)
        d.reenlist(True)  # starts term 2
        _scout_term(d, advancement_roll=5)
        d.reenlist(False)  # muster out after term 2

        assert d.projection.summary.age == 26

    def test_mishap_that_ejects_increments_age_by_4(self):
        d = _make_setup()
        d.career('Scout', 'Courier', roll=7)
        d.survive(3)  # Scout Courier survival END 5+; END=6, DM=0: 3 < 5 → fail
        d.mishap(5)  # Scout mishap 5: no effects, career ends

        assert d.projection.summary.age == 22

    def test_age_starts_at_18_before_any_career(self):
        d = _make_setup()

        assert d.projection.summary.age == 18


class TestAging:
    """Aging starts at 34 (end of 4th term). Roll 2D - term_count on aging table."""

    def test_no_aging_at_30(self):
        d = _make_3_terms()  # age=30

        assert not any(isinstance(p, PendingAgingRoll) for p in d.projection.pending_inputs)
        assert any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

    def test_aging_roll_pending_after_4th_term_advancement(self):
        d = _make_4_terms_advanced()

        assert any(isinstance(p, PendingAgingRoll) for p in d.projection.pending_inputs)

    def test_no_skill_table_before_aging_resolves(self):
        d = _make_4_terms_advanced()

        assert not any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

    def test_age_is_34_after_4th_term_advancement(self):
        d = _make_4_terms_advanced()
        d.aging_roll(5)  # no effect → PendingAssignmentChangeChoice
        d.reenlist(True)  # start term 5

        assert d.projection.summary.age == 34

    def test_no_effect_creates_skill_table(self):
        d = _make_4_terms_advanced()
        d.aging_roll(5)  # effective=5-4=1 → no effect → PendingAssignmentChangeChoice
        d.reenlist(True)  # → PendingSkillTable

        assert any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

    def test_no_effect_preserves_characteristics(self):
        d = _make_4_terms_advanced()
        d.aging_roll(5)  # no effect

        assert d.projection.summary.characteristics[Chars.STR] == 7
        assert d.projection.summary.characteristics[Chars.END] == 6

    def test_effective_0_creates_one_aging_choice(self):
        d = _make_4_terms_advanced()
        d.aging_roll(4)  # effective=4-4=0 → reduce 1 physical by 1

        aging_choices = [p for p in d.projection.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(aging_choices) == 1
        assert set(aging_choices[0].options) == {'STR', 'DEX', 'END'}

    def test_effective_0_choice_reduces_characteristic(self):
        d = _make_4_terms_advanced()
        d.aging_roll(4)
        d.aging_choice(Chars.STR)

        assert d.projection.summary.characteristics[Chars.STR] == 6  # was 7

    def test_effective_0_after_choice_creates_skill_table(self):
        d = _make_4_terms_advanced()
        d.aging_roll(4)
        d.aging_choice(Chars.STR)  # resolves last choice → complete_aging → PendingAssignmentChangeChoice
        d.reenlist(True)  # → PendingSkillTable

        assert any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

    def test_effective_minus1_creates_two_aging_choices(self):
        d = _make_4_terms_advanced()
        d.aging_roll(3)  # effective=3-4=-1 → reduce 2 physicals by 1

        aging_choices = [p for p in d.projection.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(aging_choices) == 2

    def test_effective_minus1_no_skill_table_until_both_resolved(self):
        d = _make_4_terms_advanced()
        d.aging_roll(3)
        d.aging_choice(Chars.STR)  # one resolved, one remaining

        assert any(isinstance(p, PendingAgingChoice) for p in d.projection.pending_inputs)
        assert not any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

    def test_effective_minus1_skill_table_after_both_resolved(self):
        d = _make_4_terms_advanced()
        d.aging_roll(3)
        d.aging_choice(Chars.STR)
        d.aging_choice(Chars.DEX)  # both resolved → complete_aging → PendingAssignmentChangeChoice
        d.reenlist(True)  # → PendingSkillTable

        assert any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

    def test_effective_minus2_auto_reduces_all_physicals(self):
        d = _make_4_terms_advanced()
        d.aging_roll(2)  # effective=2-4=-2 → auto reduce all 3 physicals by 1

        assert d.projection.summary.characteristics[Chars.STR] == 6  # was 7
        assert d.projection.summary.characteristics[Chars.DEX] == 7  # was 8
        assert d.projection.summary.characteristics[Chars.END] == 5  # was 6

    def test_effective_minus2_no_aging_choice_pending(self):
        d = _make_4_terms_advanced()
        d.aging_roll(2)

        assert not any(isinstance(p, PendingAgingChoice) for p in d.projection.pending_inputs)

    def test_effective_minus2_creates_skill_table(self):
        d = _make_4_terms_advanced()
        d.aging_roll(2)  # auto reduces → complete_aging → PendingAssignmentChangeChoice
        d.reenlist(True)  # → PendingSkillTable

        assert any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

    def test_reenlist_false_aging_then_career_ends(self):
        d = _make_4_terms_advanced()
        d.aging_roll(5)  # no effect → PendingAssignmentChangeChoice
        d.reenlist(False)  # muster out → career ends

        assert d.projection.summary.current_career is None

    def test_reenlist_false_aging_no_skill_table(self):
        d = _make_4_terms_advanced()
        d.aging_roll(5)
        d.reenlist(False)

        assert not any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

    def test_mishap_ejection_at_34_triggers_aging(self):
        # 3 terms (age=30), start 4th, fail survive → mishap → age=34 → aging
        d = _make_3_terms()
        d.skill_table('service_skills', 1)
        d.skill_table_choice(Pilot())
        d.survive(3)  # fail → PendingMishap
        d.mishap(5)  # Scout mishap 5: no effects, ejected → age=34

        assert any(isinstance(p, PendingAgingRoll) for p in d.projection.pending_inputs)

    def test_mishap_ejection_aging_career_stays_ended(self):
        d = _make_3_terms()
        d.skill_table('service_skills', 1)
        d.skill_table_choice(Pilot())
        d.survive(3)
        d.mishap(5)
        d.aging_roll(5)  # no effect → complete_aging → muster out (ejected path)

        assert d.projection.summary.current_career is None


class TestAgingCrisis:
    """Aging crisis: any characteristic reduced to 0 triggers crisis pending."""

    def test_crisis_pending_when_str_reaches_0(self):
        # STR=1, aging effective=0 (1 physical -1) → choose STR → STR=0 → crisis
        d = _make_low_str_4_terms_advanced()
        d.aging_roll(4)  # effective=0: one choice
        d.aging_choice(Chars.STR)  # STR: 1→0 → crisis

        assert any(isinstance(p, PendingAgingCrisis) for p in d.projection.pending_inputs)

    def test_no_skill_table_before_crisis_resolved(self):
        d = _make_low_str_4_terms_advanced()
        d.aging_roll(4)
        d.aging_choice(Chars.STR)

        assert not any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

    def test_crisis_triggered_by_auto_reduction(self):
        # STR=1, aging effective=-2 (all 3 physicals -1, auto) → STR=0 → crisis
        d = _make_low_str_4_terms_advanced()
        d.aging_roll(2)  # effective=2-4=-2: auto all physicals -1

        assert any(isinstance(p, PendingAgingCrisis) for p in d.projection.pending_inputs)

    def test_crisis_clears_remaining_aging_choices(self):
        # effective=-1: 2 aging_choices; choose STR first → STR=0 → crisis clears the other
        d = _make_low_str_4_terms_advanced()
        d.aging_roll(3)  # effective=3-4=-1: 2 physicals -1
        d.aging_choice(Chars.STR)  # STR: 1→0 → crisis, other choice cleared

        aging_choices = [p for p in d.projection.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(aging_choices) == 0
        assert any(isinstance(p, PendingAgingCrisis) for p in d.projection.pending_inputs)

    def test_crisis_paid_restores_str_to_1(self):
        d = _make_low_str_4_terms_advanced()
        d.aging_roll(4)
        d.aging_choice(Chars.STR)
        d.aging_crisis(paid=True, medical_roll=3)

        assert d.projection.summary.characteristics[Chars.STR] == 1

    def test_crisis_paid_ends_career(self):
        d = _make_low_str_4_terms_advanced()
        d.aging_roll(4)
        d.aging_choice(Chars.STR)
        d.aging_crisis(paid=True, medical_roll=3)

        assert d.projection.summary.current_career is None

    def test_crisis_paid_creates_muster_out_pendings(self):
        d = _make_low_str_4_terms_advanced()
        d.aging_roll(4)
        d.aging_choice(Chars.STR)
        d.aging_crisis(paid=True, medical_roll=3)

        muster_out_pendings = [p for p in d.projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) > 0

    def test_crisis_die_marks_character_dead(self):
        d = _make_low_str_4_terms_advanced()
        d.aging_roll(4)
        d.aging_choice(Chars.STR)
        d.aging_crisis(paid=False, medical_roll=0)

        assert d.projection.summary.dead is True

    def test_crisis_die_no_muster_out(self):
        d = _make_low_str_4_terms_advanced()
        d.aging_roll(4)
        d.aging_choice(Chars.STR)
        d.aging_crisis(paid=False, medical_roll=0)

        assert not any(isinstance(p, PendingMusterOut) for p in d.projection.pending_inputs)


class TestAgingRollValidation:
    def test_roll_too_low_raises(self):
        d = _make_4_terms_advanced()
        with pytest.raises(ReplayError, match='2-12'):
            d.aging_roll(1)

    def test_roll_too_high_raises(self):
        d = _make_4_terms_advanced()
        with pytest.raises(ReplayError, match='2-12'):
            d.aging_roll(13)


class TestAgingEffectiveMinus3:
    """Effective -3 aging: one -2 choice and two -1 choices."""

    def test_creates_three_aging_choices(self):
        d = _make_5_terms_advanced()
        d.aging_roll(2)  # effective=2-5=-3

        aging_choices = [p for p in d.projection.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(aging_choices) == 3

    def test_first_choice_reduces_by_2(self):
        d = _make_5_terms_advanced()
        d.aging_roll(2)

        by_2 = [
            p
            for p in d.projection.pending_inputs
            if isinstance(p, PendingAgingChoice) and 'reduce by 2' in p.instruction
        ]
        assert len(by_2) == 1

    def test_two_choices_reduce_by_1(self):
        d = _make_5_terms_advanced()
        d.aging_roll(2)

        by_1 = [
            p
            for p in d.projection.pending_inputs
            if isinstance(p, PendingAgingChoice) and 'reduce by 1' in p.instruction
        ]
        assert len(by_1) == 2


class TestAgingEffectiveMinus6:
    """Effective ≤ −6: each physical −2, then INT or SOC −1 (unless a crisis fires first)."""

    def test_no_crisis_queues_mental_choice(self):
        # STR=7: after −2 → STR=5, DEX=6, END=4 — no zeros, no crisis → PendingAgingChoiceMental queued
        d = _make_8_terms_advanced('786935')
        d.aging_roll(2)  # effective=2-8=-6

        assert any(isinstance(p, PendingAgingChoiceMental) for p in d.projection.pending_inputs)

    def test_crisis_suppresses_mental_choice(self):
        # STR=2: after −2 → STR=0 — crisis fires, mental choice must not be queued
        d = _make_8_terms_advanced('286935')
        d.aging_roll(2)

        assert not any(isinstance(p, PendingAgingChoiceMental) for p in d.projection.pending_inputs)

    def test_crisis_queued_when_str_zero(self):
        d = _make_8_terms_advanced('286935')
        d.aging_roll(2)

        assert any(isinstance(p, PendingAgingCrisis) for p in d.projection.pending_inputs)
