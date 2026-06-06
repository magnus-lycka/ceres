"""Tests for aging: age tracking, aging roll effects, and aging crisis."""

import pytest

from ceres.character.characteristics import Chars
from ceres.character.events import (
    AdvancementEvent,
    AgingCrisisEvent,
    AgingRollEvent,
    BackgroundSkillsEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    MishapEvent,
    PendingAgingChoice,
    PendingAgingCrisis,
    PendingAgingRoll,
    PendingMusterOut,
    PendingSkillTable,
    ReenlistEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import ReplayError, replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive
from ceres.character.sophonts import VILANI
from tests.character.helpers import MOCK_WORLD


def _full_setup(character_id: int = 1) -> list:
    """Return events that get a character through setup: started → ucp → background skills."""
    # STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 → 4 background skills
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _setup_through_3_terms_reenlist() -> list:
    """Complete setup and 3 Scout Courier terms. Age=30 after. Skill_table pending at '18.0'."""
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
        # Term 1
        CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        SurviveEvent(id=5, fulfills='4.0', roll=7),
        TermEventEvent(id=6, fulfills='5.0', roll=5),
        AdvancementEvent(id=7, fulfills='6.0', roll=3),
        ReenlistEvent(id=8, fulfills='7.0', reenlist=True),  # age=22
        # Term 2
        SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
        SurviveEvent(id=10, fulfills='9.0', roll=7),
        TermEventEvent(id=11, fulfills='10.0', roll=5),
        AdvancementEvent(id=12, fulfills='11.0', roll=3),
        ReenlistEvent(id=13, fulfills='12.0', reenlist=True),  # age=26
        # Term 3
        SkillTableEvent(id=14, fulfills='13.0', table='service_skills', roll=1),
        SurviveEvent(id=15, fulfills='14.0', roll=7),
        TermEventEvent(id=16, fulfills='15.0', roll=5),
        AdvancementEvent(id=17, fulfills='16.0', roll=4),
        ReenlistEvent(id=18, fulfills='17.0', reenlist=True),  # age=30
    ]


def _setup_through_4_terms_advancement() -> list:
    """Complete setup through advancement of term 4. Age still 30.
    Next: ReenlistEvent(fulfills='22.0') triggers aging (age->34)."""
    return [
        *_setup_through_3_terms_reenlist(),
        # Term 4
        SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
        SurviveEvent(id=20, fulfills='19.0', roll=7),
        TermEventEvent(id=21, fulfills='20.0', roll=5),
        AdvancementEvent(id=22, fulfills='21.0', roll=5),
    ]


def _setup_low_str(character_id: int = 1) -> list:
    """Character with STR=1 for aging crisis tests. UCP '1869A5'."""
    # STR=1 DEX=8 END=6 INT=9 EDU=10 SOC=5 — 4 background skills
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='1869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _setup_low_str_through_4_terms_advancement() -> list:
    """Low-STR character through 4 terms to advancement, ready for ReenlistEvent."""
    return [
        *_setup_low_str(),
        # Term 1
        CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        SurviveEvent(id=5, fulfills='4.0', roll=7),
        TermEventEvent(id=6, fulfills='5.0', roll=5),
        AdvancementEvent(id=7, fulfills='6.0', roll=3),
        ReenlistEvent(id=8, fulfills='7.0', reenlist=True),  # age=22
        # Term 2
        SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
        SurviveEvent(id=10, fulfills='9.0', roll=7),
        TermEventEvent(id=11, fulfills='10.0', roll=5),
        AdvancementEvent(id=12, fulfills='11.0', roll=3),
        ReenlistEvent(id=13, fulfills='12.0', reenlist=True),  # age=26
        # Term 3
        SkillTableEvent(id=14, fulfills='13.0', table='service_skills', roll=1),
        SurviveEvent(id=15, fulfills='14.0', roll=7),
        TermEventEvent(id=16, fulfills='15.0', roll=5),
        AdvancementEvent(id=17, fulfills='16.0', roll=4),
        ReenlistEvent(id=18, fulfills='17.0', reenlist=True),  # age=30
        # Term 4
        SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
        SurviveEvent(id=20, fulfills='19.0', roll=7),
        TermEventEvent(id=21, fulfills='20.0', roll=5),
        AdvancementEvent(id=22, fulfills='21.0', roll=5),
    ]


class TestAgeTracking:
    """Character age starts at 18 and increases by 4 per completed term."""

    def test_reenlist_false_increments_age_by_4(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills='6.0', roll=5),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 22

    def test_reenlist_true_also_increments_age_by_4(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills='6.0', roll=5),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 22

    def test_two_terms_adds_8_years(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=7, fulfills='6.0', roll=5),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),  # benefit_dm → direct advancement
            AdvancementEvent(id=12, fulfills='11.0', roll=5),
            ReenlistEvent(id=13, fulfills='12.0', reenlist=False),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 26

    def test_mishap_that_ejects_increments_age_by_4(self):
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=3),
            MishapEvent(id=6, fulfills='5.0', roll=5),  # Scout mishap 5: no effects, career ends
        ]
        projection = replay(1, events)

        assert projection.summary.age == 22

    def test_age_starts_at_18_before_any_career(self):
        projection = replay(1, _full_setup())

        assert projection.summary.age == 18


class TestAging:
    """Aging starts at 34 (end of 4th term). Roll 2D - term_count on aging table."""

    def test_no_aging_at_30(self):
        # After 3 complete terms, age=30 -> no aging_roll pending
        projection = replay(1, _setup_through_3_terms_reenlist())

        assert not any(isinstance(p, PendingAgingRoll) for p in projection.pending_inputs)
        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_aging_roll_pending_after_4th_term_advancement(self):
        projection = replay(1, _setup_through_4_terms_advancement())

        assert any(isinstance(p, PendingAgingRoll) for p in projection.pending_inputs)

    def test_no_skill_table_before_aging_resolves(self):
        projection = replay(1, _setup_through_4_terms_advancement())

        assert not any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_age_is_34_after_4th_term_reenlist(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert projection.summary.age == 34

    def test_no_effect_creates_skill_table(self):
        # 4 terms: DM=-4. roll=5 -> 5-4=1 -> no effect -> reenlist pending -> reenlist -> skill_table
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=5),
            ReenlistEvent(id=24, fulfills='23.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_no_effect_preserves_characteristics(self):
        # STR=7 DEX=8 END=6 -- unchanged
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.STR] == 7
        assert projection.summary.characteristics[Chars.END] == 6

    def test_effective_0_creates_one_aging_choice(self):
        # roll=4 -> 4-4=0 -> reduce 1 physical by 1
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=4),
        ]
        projection = replay(1, events)

        aging_choices = [p for p in projection.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(aging_choices) == 1
        assert set(aging_choices[0].options) == {'STR', 'DEX', 'END'}

    def test_effective_0_choice_reduces_characteristic(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic=Chars.STR, amount=1),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.STR] == 6  # was 7

    def test_effective_0_after_choice_creates_skill_table(self):
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=4),
            CharacteristicChoiceEvent(id=24, fulfills='23.0', characteristic=Chars.STR, amount=1),
            ReenlistEvent(id=25, fulfills='24.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_effective_minus1_creates_two_aging_choices(self):
        # roll=3 -> 3-4=-1 -> reduce 2 physicals by 1
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=3),
        ]
        projection = replay(1, events)

        aging_choices = [p for p in projection.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(aging_choices) == 2

    def test_effective_minus1_no_skill_table_until_both_resolved(self):
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=3),
            CharacteristicChoiceEvent(id=24, fulfills='23.0', characteristic=Chars.STR, amount=1),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAgingChoice) for p in projection.pending_inputs)
        assert not any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_effective_minus1_skill_table_after_both_resolved(self):
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=3),
            CharacteristicChoiceEvent(id=24, fulfills='23.0', characteristic=Chars.STR, amount=1),
            CharacteristicChoiceEvent(id=25, fulfills='23.1', characteristic=Chars.DEX, amount=1),
            ReenlistEvent(id=26, fulfills='25.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_effective_minus2_auto_reduces_all_physicals(self):
        # roll=2 -> 2-4=-2 -> auto reduce all 3 physicals by 1, no choice pending
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=2),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.STR] == 6  # was 7
        assert projection.summary.characteristics[Chars.DEX] == 7  # was 8
        assert projection.summary.characteristics[Chars.END] == 5  # was 6

    def test_effective_minus2_no_aging_choice_pending(self):
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=2),
        ]
        projection = replay(1, events)

        assert not any(isinstance(p, PendingAgingChoice) for p in projection.pending_inputs)

    def test_effective_minus2_creates_skill_table(self):
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=2),
            ReenlistEvent(id=24, fulfills='23.0', reenlist=True),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_reenlist_false_aging_then_career_ends(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=False),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),  # no effect
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_reenlist_false_aging_no_skill_table(self):
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=False),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),
        ]
        projection = replay(1, events)

        assert not any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_mishap_ejection_at_34_triggers_aging(self):
        # 3 terms (age=30), start 4th, fail survive -> mishap -> age=34 -> aging
        events = [
            *_setup_through_3_terms_reenlist(),
            SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
            SurviveEvent(id=20, fulfills='19.0', roll=3),
            MishapEvent(id=21, fulfills='20.0', roll=5),  # Scout mishap 5: no effects, ejected
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAgingRoll) for p in projection.pending_inputs)

    def test_mishap_ejection_aging_career_stays_ended(self):
        events = [
            *_setup_through_3_terms_reenlist(),
            SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
            SurviveEvent(id=20, fulfills='19.0', roll=3),
            MishapEvent(id=21, fulfills='20.0', roll=5),
            AgingRollEvent(id=22, fulfills='21.0', roll=5),  # no effect
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None


class TestAgingCrisis:
    """Aging crisis: any characteristic reduced to 0 triggers crisis pending."""

    def test_crisis_pending_when_str_reaches_0(self):
        # STR=1, aging effective=0 (1 physical -1) → choose STR → STR=0 → crisis
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),  # 4-4=0: one physical -1
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic=Chars.STR, amount=1),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAgingCrisis) for p in projection.pending_inputs)

    def test_no_skill_table_before_crisis_resolved(self):
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic=Chars.STR, amount=1),
        ]
        projection = replay(1, events)

        assert not any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)

    def test_crisis_triggered_by_auto_reduction(self):
        # STR=1, aging effective=-2 (all 3 physicals -1, auto) → STR=0 → crisis
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=2),  # 2-4=-2: auto all physicals -1
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingAgingCrisis) for p in projection.pending_inputs)

    def test_crisis_clears_remaining_aging_choices(self):
        # effective=-1: 2 aging_choices; choose STR first → STR=0 → crisis clears the other
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=3),  # 3-4=-1: 2 physicals -1
            CharacteristicChoiceEvent(id=24, fulfills='23.0', characteristic=Chars.STR, amount=1),
        ]
        projection = replay(1, events)

        aging_choices = [p for p in projection.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(aging_choices) == 0
        assert any(isinstance(p, PendingAgingCrisis) for p in projection.pending_inputs)

    def test_crisis_paid_restores_str_to_1(self):
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic=Chars.STR, amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=True, medical_roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.STR] == 1

    def test_crisis_paid_ends_career(self):
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic=Chars.STR, amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=True, medical_roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.current_career is None

    def test_crisis_paid_creates_muster_out_pendings(self):
        # 4 terms reenlisting → crisis during term 5 aging (reenlist=True path)
        # term_count at crisis: 4 (from 4 reenlist=True increments in _complete_aging for terms 1-4)
        # Actually: in reenlist=True aging path, term_count is incremented in _complete_aging.
        # After 3 completed terms (3 reenlist=True non-aging), term_count=3 after 3rd reenlist.
        # Then term 4: reenlist=True with aging → pending_reenlist=True → crisis before _complete_aging
        # → term_count still=3 at crisis time, but _apply_aging_crisis adds 1 for completed term → 4 rolls
        # rank=0 → 4 + 0 = 4 muster out rolls
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),  # triggers aging
            AgingRollEvent(id=24, fulfills='23.0', roll=4),  # effective=0: one choice
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic=Chars.STR, amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=True, medical_roll=3),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) > 0

    def test_crisis_die_marks_character_dead(self):
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic=Chars.STR, amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=False, medical_roll=0),
        ]
        projection = replay(1, events)

        assert projection.summary.dead is True

    def test_crisis_die_no_muster_out(self):
        events = [
            *_setup_low_str_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=True),
            AgingRollEvent(id=24, fulfills='23.0', roll=4),
            CharacteristicChoiceEvent(id=25, fulfills='24.0', characteristic=Chars.STR, amount=1),
            AgingCrisisEvent(id=26, fulfills='25.crisis', paid=False, medical_roll=0),
        ]
        projection = replay(1, events)

        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


def _setup_through_5_terms_advancement() -> list:
    """Extend _setup_through_4_terms_advancement() with a 5th term through advancement.

    Aging after term 4 resolves with no effect (roll=5, effective=1). Term 5 fails
    advancement, triggering a second aging roll at age=38, term_count=5.
    Leaves PendingAgingRoll('28.0').
    """
    return [
        *_setup_through_4_terms_advancement(),
        AgingRollEvent(id=23, fulfills='22.0', roll=5),  # effective=5-4=1 → no effect
        # _complete_aging → PendingAssignmentChangeChoice('23.0') (Scout has 3 assignments)
        ReenlistEvent(id=24, fulfills='23.0', reenlist=True),  # same assignment, term 5 starts
        SkillTableEvent(id=25, fulfills='24.0', table='service_skills', roll=2),  # Survival → PendingSurvive
        SurviveEvent(id=26, fulfills='25.0', roll=10),
        TermEventEvent(id=27, fulfills='26.0', roll=5),  # benefit_dm → PendingAdvancement
        AdvancementEvent(id=28, fulfills='27.0', roll=6),  # EDU 9+, DM+1 → 7<9 → fail → age=38
        # term_count=5, age=38 → PendingAgingRoll('28.0')
    ]


class TestAgingRollValidation:
    def test_roll_too_low_raises(self):
        events = [*_setup_through_4_terms_advancement(), AgingRollEvent(id=23, fulfills='22.0', roll=1)]
        with pytest.raises(ReplayError, match='2-12'):
            replay(1, events)

    def test_roll_too_high_raises(self):
        events = [*_setup_through_4_terms_advancement(), AgingRollEvent(id=23, fulfills='22.0', roll=13)]
        with pytest.raises(ReplayError, match='2-12'):
            replay(1, events)


class TestAgingEffectiveMinus3:
    """Effective -3 aging: one -2 choice and two -1 choices."""

    def test_creates_three_aging_choices(self):
        # effective = 2 - 5 = -3 requires term_count=5
        events = [*_setup_through_5_terms_advancement(), AgingRollEvent(id=29, fulfills='28.0', roll=2)]
        projection = replay(1, events)

        aging_choices = [p for p in projection.pending_inputs if isinstance(p, PendingAgingChoice)]
        assert len(aging_choices) == 3

    def test_first_choice_reduces_by_2(self):
        events = [*_setup_through_5_terms_advancement(), AgingRollEvent(id=29, fulfills='28.0', roll=2)]
        projection = replay(1, events)

        by_2 = [
            p for p in projection.pending_inputs if isinstance(p, PendingAgingChoice) and 'reduce by 2' in p.instruction
        ]
        assert len(by_2) == 1

    def test_two_choices_reduce_by_1(self):
        events = [*_setup_through_5_terms_advancement(), AgingRollEvent(id=29, fulfills='28.0', roll=2)]
        projection = replay(1, events)

        by_1 = [
            p for p in projection.pending_inputs if isinstance(p, PendingAgingChoice) and 'reduce by 1' in p.instruction
        ]
        assert len(by_1) == 2
