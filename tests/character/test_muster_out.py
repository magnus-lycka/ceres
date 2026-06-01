"""Tests for muster out: benefit rolls, cash limits, and roll counts."""

import pytest

from ceres.character.characteristics import Chars
from ceres.character.events import (
    AdvancementEvent,
    AgingRollEvent,
    BackgroundSkillsEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    MusterOutEvent,
    PendingMusterOut,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import ReplayError, replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive, Medic, SpaceScience
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


def _scholar_setup(character_id: int = 1) -> list:
    """Like _full_setup() but with Medic instead of Drive.

    Scholar service_skills row 1 offers Drive/Flyer. Using Drive in background causes Flyer to be
    auto-granted (only 1 option left). This setup preserves both options so Scholar initial training
    creates two choice pendings: Drive/Flyer (id .0) and Science (id .1).
    """
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Medic()]),
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
        AdvancementEvent(id=17, fulfills='16.0', roll=3),
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
        AdvancementEvent(id=22, fulfills='21.0', roll=3),
    ]


def _setup_through_reenlist_false() -> list:
    """1 Scout Courier term, reenlist=False. Age=22, career ended. Muster out pending at '7.0'."""
    # term_count=1, rank=0 → 1 muster out roll (1 term + 0 rank // 2)
    return [
        *_full_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
        SurviveEvent(id=5, fulfills='4.0', roll=7),
        TermEventEvent(id=6, fulfills='5.0', roll=5),
        AdvancementEvent(id=7, fulfills='6.0', roll=3),  # fail advancement — rank stays 0
        ReenlistEvent(id=8, fulfills='7.0', reenlist=False),
    ]


class TestMusterOut:
    """Muster out: benefit rolls when leaving a career."""

    def test_reenlist_false_creates_muster_out_pending(self):
        # 1 term, rank 0 → 1 roll (1 + 0//2 = 1)
        projection = replay(1, _setup_through_reenlist_false())

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1

    def test_muster_out_pending_has_cash_and_benefits_options(self):
        projection = replay(1, _setup_through_reenlist_false())

        p = next(p for p in projection.pending_inputs if isinstance(p, PendingMusterOut))
        assert set(p.options) == {'cash', 'benefits'}

    def test_muster_out_career_set_while_pendings_remain(self):
        projection = replay(1, _setup_through_reenlist_false())

        assert projection.muster_out_career == 'Scout'

    def test_cash_roll_adds_to_summary_cash(self):
        # Scout roll 1 on cash table → Cr20000
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='cash', roll=1),
        ]
        projection = replay(1, events)

        assert projection.summary.cash == 20000

    def test_cash_roll_3_gives_cr30000(self):
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='cash', roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.cash == 30000

    def test_benefits_roll_weapon_adds_to_benefits(self):
        # Scout benefits roll 4 → Weapon
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=4),
        ]
        projection = replay(1, events)

        assert any(b.key == 'weapon' for b in projection.summary.benefits)

    def test_benefits_roll_ship_share_adds_to_benefits(self):
        # Scout benefits roll 1 → ship_share
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=1),
        ]
        projection = replay(1, events)

        assert any(b.key == 'ship_share' for b in projection.summary.benefits)

    def test_benefits_roll_int_plus_1_increases_int(self):
        # Scout benefits roll 2 → INT +1 (INT was 9)
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=2),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.INT] == 10

    def test_benefits_roll_edu_plus_1_increases_edu(self):
        # Scout benefits roll 3 → EDU +1 (EDU was 10)
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=3),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.EDU] == 11

    def test_benefits_roll_scout_ship_adds_to_benefits(self):
        # Scout benefits roll 6 → scout_ship
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='benefits', roll=6),
        ]
        projection = replay(1, events)

        assert any(b.key == 'scout_ship' for b in projection.summary.benefits)

    def test_muster_out_career_cleared_after_all_rolls(self):
        events = [
            *_setup_through_reenlist_false(),
            MusterOutEvent(id=9, fulfills='8.0', table='cash', roll=1),
        ]
        projection = replay(1, events)

        assert projection.muster_out_career is None

    def test_roll_count_two_terms_rank_0(self):
        # 2 terms, rank 0 → 2 + 0//2 = 2 rolls
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),  # fail — rank=0
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),  # age=22
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),
            AdvancementEvent(id=12, fulfills='11.0', roll=3),  # fail — rank=0
            ReenlistEvent(id=13, fulfills='12.0', reenlist=False),  # age=26
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 2

    def test_roll_count_includes_rank_bonus(self):
        # 1 term, rank 1 → 1 + 1//2 = 1 + 0 = 1. rank 2 → 1 + 2//2 = 2 rolls
        # Use 2 terms + advance to rank 1 in first term → 2 + 0 = 2
        # Use 1 term with rank 2 → 1 + 1 = 2 rolls
        # Simplest: setup_through_3_terms_reenlist has rank 0 (advancement rolls 3 always fail)
        # Advance in term 1: Scout Courier EDU 9+, EDU=10 DM+1, roll=8 → 8+1=9 ≥ 9 ✓
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=8),  # 8+1=9>=9 → rank 1
            ReenlistEvent(id=8, fulfills='7.0', reenlist=False),  # 1 term, rank 1 → 1 + 1//2 = 1 + 0 = 1
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1

    def test_roll_count_rank_2_gives_extra_roll(self):
        # rank 2 → rank//2 = 1 extra roll. With 1 term: 1+1=2 rolls
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=8),  # rank 1
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),
            AdvancementEvent(id=12, fulfills='11.0', roll=8),  # rank 2
            ReenlistEvent(id=13, fulfills='12.0', reenlist=False),  # 2 terms, rank 2 → 2+1=3 rolls
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 3

    def test_cash_max_3_times(self):
        # 3 terms, rank 0 → 3 rolls. Take cash 3 times: ok
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),
            AdvancementEvent(id=12, fulfills='11.0', roll=3),
            ReenlistEvent(id=13, fulfills='12.0', reenlist=True),
            SkillTableEvent(id=14, fulfills='13.0', table='service_skills', roll=1),
            SurviveEvent(id=15, fulfills='14.0', roll=7),
            TermEventEvent(id=16, fulfills='15.0', roll=5),
            AdvancementEvent(id=17, fulfills='16.0', roll=3),
            ReenlistEvent(id=18, fulfills='17.0', reenlist=False),  # 3 terms, rank 0 → 3 rolls
            MusterOutEvent(id=19, fulfills='18.0', table='cash', roll=1),
            MusterOutEvent(id=20, fulfills='18.1', table='cash', roll=1),
            MusterOutEvent(id=21, fulfills='18.2', table='cash', roll=1),
        ]
        projection = replay(1, events)

        assert projection.summary.cash == 60000
        assert projection.summary.muster_out_cash_count == 3

    def test_cash_4th_time_raises_error(self):
        # 3 terms, rank 2 → 3 + 1 = 4 rolls; cash max 3 → 4th raises error
        # Advance twice: Scout Courier EDU 9+, EDU=10 (DM+1), roll=8 → 8+1=9 ≥ 9 ✓
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=8),  # rank 1
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),  # age=22
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=7),
            TermEventEvent(id=11, fulfills='10.0', roll=5),
            AdvancementEvent(id=12, fulfills='11.0', roll=8),  # rank 2
            ReenlistEvent(id=13, fulfills='12.0', reenlist=True),  # age=26
            SkillTableEvent(id=14, fulfills='13.0', table='service_skills', roll=1),
            SurviveEvent(id=15, fulfills='14.0', roll=7),
            TermEventEvent(id=16, fulfills='15.0', roll=5),
            AdvancementEvent(id=17, fulfills='16.0', roll=3),  # fail
            ReenlistEvent(id=18, fulfills='17.0', reenlist=False),  # age=30, 3 terms rank 2 → 4 rolls
            MusterOutEvent(id=19, fulfills='18.0', table='cash', roll=1),
            MusterOutEvent(id=20, fulfills='18.1', table='cash', roll=1),
            MusterOutEvent(id=21, fulfills='18.2', table='cash', roll=1),
            MusterOutEvent(id=22, fulfills='18.3', table='cash', roll=1),  # 4th cash → error
        ]
        with pytest.raises(ReplayError, match='Cash'):
            replay(1, events)

    def test_mishap_ejection_loses_current_term_benefit(self):
        # 1 term enter → mishap → lose current term's roll → 0 muster out rolls
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # fail survive
            MishapEvent(id=6, fulfills='5.0', roll=5),  # Scout mishap 5: no effects, ejected
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 0

    def test_mishap_ejection_after_2_terms_gets_1_roll(self):
        # 2 terms: first completes normally (reenlist=True), second term mishap → lose current → 1 roll
        events = [
            *_full_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scout', assignment='Courier', qualification_roll=7),
            SurviveEvent(id=5, fulfills='4.0', roll=7),
            TermEventEvent(id=6, fulfills='5.0', roll=5),
            AdvancementEvent(id=7, fulfills='6.0', roll=3),
            ReenlistEvent(id=8, fulfills='7.0', reenlist=True),
            SkillTableEvent(id=9, fulfills='8.0', table='service_skills', roll=1),
            SurviveEvent(id=10, fulfills='9.0', roll=3),  # fail survive
            MishapEvent(id=11, fulfills='10.0', roll=5),  # ejected, lose current term → 1 roll
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1

    def test_benefit_dm_tracked_as_scheduled_effect(self):
        # Scout event 5 grants benefit_dm+1 — tracked as a muster_out ScheduledEffect.
        # The player includes the DM in their roll value (MusterOutEvent.roll already includes DMs).
        # Scholar cash row 1=Cr5000, row 2=Cr10000. Player rolls 1 and applies DM+1 → submits roll=2.
        events = [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills='4.0', skill=Drive()),
            SkillChoiceEvent(id=6, fulfills='4.1', skill=SpaceScience()),
            SurviveEvent(id=7, fulfills='6.0', roll=7),
            TermEventEvent(id=8, fulfills='7.0', roll=5),  # scholar event 5: benefit_dm +1
            AdvancementEvent(id=9, fulfills='8.0', roll=3),
            ReenlistEvent(id=10, fulfills='9.0', reenlist=False),
        ]
        projection = replay(1, events)

        # benefit_dm tracked as a scheduled effect
        muster_out_dms = [se for se in projection.scheduled_effects if se.trigger == 'muster_out']
        assert len(muster_out_dms) == 1
        assert muster_out_dms[0].effect.get('amount') == 1

    def test_scholar_soc_plus_1_benefit(self):
        # Scholar benefits roll 4 → SOC +1 (SOC was 5)
        events = [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills='4.0', skill=Drive()),
            SkillChoiceEvent(id=6, fulfills='4.1', skill=SpaceScience()),
            SurviveEvent(id=7, fulfills='6.0', roll=7),
            TermEventEvent(id=8, fulfills='7.0', roll=5),
            AdvancementEvent(id=9, fulfills='8.0', roll=3),
            ReenlistEvent(id=10, fulfills='9.0', reenlist=False),
            MusterOutEvent(id=11, fulfills='10.0', table='benefits', roll=4),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.SOC] == 6  # was 5

    def test_scholar_two_ship_shares_benefit(self):
        # Scholar benefits roll 3 → Two Ship Shares → 2 ship_share entries
        events = [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills='4.0', skill=Drive()),
            SkillChoiceEvent(id=6, fulfills='4.1', skill=SpaceScience()),
            SurviveEvent(id=7, fulfills='6.0', roll=7),
            TermEventEvent(id=8, fulfills='7.0', roll=5),
            AdvancementEvent(id=9, fulfills='8.0', roll=3),
            ReenlistEvent(id=10, fulfills='9.0', reenlist=False),
            MusterOutEvent(id=11, fulfills='10.0', table='benefits', roll=3),
        ]
        projection = replay(1, events)

        assert sum(1 for b in projection.summary.benefits if b.key == 'ship_share') == 2

    def test_scholar_scientific_equipment_benefit(self):
        # Scholar benefits roll 5 → scientific_equipment
        events = [
            *_scholar_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Scholar', assignment='Field Researcher', qualification_roll=5),
            SkillChoiceEvent(id=5, fulfills='4.0', skill=Drive()),
            SkillChoiceEvent(id=6, fulfills='4.1', skill=SpaceScience()),
            SurviveEvent(id=7, fulfills='6.0', roll=7),
            TermEventEvent(id=8, fulfills='7.0', roll=5),
            AdvancementEvent(id=9, fulfills='8.0', roll=3),
            ReenlistEvent(id=10, fulfills='9.0', reenlist=False),
            MusterOutEvent(id=11, fulfills='10.0', table='benefits', roll=5),
        ]
        projection = replay(1, events)

        assert any(b.key == 'scientific_equipment' for b in projection.summary.benefits)

    def test_aging_reenlist_false_gets_muster_out_after_aging(self):
        # 4 terms, reenlist=False, age=34 → aging required → muster out after aging resolves
        events = [
            *_setup_through_4_terms_advancement(),
            ReenlistEvent(id=23, fulfills='22.0', reenlist=False),
            AgingRollEvent(id=24, fulfills='23.0', roll=5),  # no effect (5-4=1)
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) > 0

    def test_aging_reenlist_false_roll_count(self):
        # 4 terms, rank 0 → 4 muster out rolls
        events = [
            *_setup_through_4_terms_advancement(),
            AgingRollEvent(id=23, fulfills='22.0', roll=5),  # no effect → reenlist pending
            ReenlistEvent(id=24, fulfills='23.0', reenlist=False),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 4

    def test_mishap_aging_muster_out_loses_current_term(self):
        # 4th term mishap ejection with aging → 3 rolls (4-1=3 terms, rank 0)
        events = [
            *_setup_through_3_terms_reenlist(),
            SkillTableEvent(id=19, fulfills='18.0', table='service_skills', roll=1),
            SurviveEvent(id=20, fulfills='19.0', roll=3),  # fail
            MishapEvent(id=21, fulfills='20.0', roll=5),  # ejected, age=34
            AgingRollEvent(id=22, fulfills='21.0', roll=5),  # no effect
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 3
