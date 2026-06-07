"""Tests for muster out: benefit rolls, cash limits, and roll counts."""

import pytest

from ceres.character.domain.career import AGENT, ARMY, CITIZEN, SCHOLAR, SCOUT
from ceres.character.domain.career.career_data import BenefitRollDm
from ceres.character.domain.career.career_events import (
    AdvancementHandler,
    CareerEntryHandler,
    MishapHandler,
    MusterOutHandler,
    PendingDraftChoice,
    PendingMusterOut,
    ReenlistHandler,
    SkillChoiceHandler,
    SkillTableHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.health.health_events import AgingRollHandler
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, JackOfAllTrades, Medic, SpaceScience
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import ReplayError, replay
from tests.character.helpers import MOCK_WORLD


def _full_setup(character_id: int = 1) -> list:
    """Return events that get a character through setup: started → ucp → background skills."""
    # STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 → 4 background skills
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
        ),
    ]


def _scholar_setup(character_id: int = 1) -> list:
    """Like _full_setup() but with Medic instead of Drive.

    Scholar service_skills row 1 offers Drive/Flyer. Using Drive in background causes Flyer to be
    auto-granted (only 1 option left). This setup preserves both options so Scholar initial training
    creates two choice pendings: Drive/Flyer (id .0) and Science (id .1).
    """
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Medic()])
        ),
    ]


def _setup_through_3_terms_reenlist() -> list:
    """Complete setup and 3 Scout Courier terms. Age=30 after. Skill_table pending at '18.0'.

    Uses service_skills roll=5 (a non-specialized skill) to avoid PendingSkillTableChoice.
    """
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
        ),
        # Term 1
        Event(
            id=4,
            fulfills=(3, 0),
            handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
        ),
        Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
        Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
        Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=3)),
        Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=True)),  # age=22
        # Term 2
        Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
        Event(id=10, fulfills=(9, 0), handler=SurviveHandler(roll=7)),
        Event(id=11, fulfills=(10, 0), handler=TermEventHandler(roll=5)),
        Event(id=12, fulfills=(11, 0), handler=AdvancementHandler(roll=3)),
        Event(id=13, fulfills=(12, 0), handler=ReenlistHandler(reenlist=True)),  # age=26
        # Term 3
        Event(id=14, fulfills=(13, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
        Event(id=15, fulfills=(14, 0), handler=SurviveHandler(roll=7)),
        Event(id=16, fulfills=(15, 0), handler=TermEventHandler(roll=5)),
        Event(id=17, fulfills=(16, 0), handler=AdvancementHandler(roll=4)),
        Event(id=18, fulfills=(17, 0), handler=ReenlistHandler(reenlist=True)),  # age=30
    ]


def _setup_through_4_terms_advancement() -> list:
    """Complete setup through advancement of term 4. Age still 30.
    Next: Event(fulfills=(22, 0), handler=ReenlistHandler()) triggers aging (age->34)."""
    return [
        *_setup_through_3_terms_reenlist(),
        # Term 4
        Event(id=19, fulfills=(18, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
        Event(id=20, fulfills=(19, 0), handler=SurviveHandler(roll=7)),
        Event(id=21, fulfills=(20, 0), handler=TermEventHandler(roll=5)),
        Event(id=22, fulfills=(21, 0), handler=AdvancementHandler(roll=5)),
    ]


def _setup_through_reenlist_false() -> list:
    """1 Scout Courier term, reenlist=False. Age=22, career ended. Muster out pending at '7.0'."""
    # term_count=1, rank=0 → 1 muster out roll (1 term + 0 rank // 2)
    return [
        *_full_setup(),
        Event(
            id=4,
            fulfills=(3, 0),
            handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
        ),
        Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
        Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
        Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=3)),  # fail advancement — rank stays 0
        Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=False)),
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

        assert projection.muster_out_career is not None
        assert projection.muster_out_career.name == 'Scout'

    def test_cash_roll_adds_to_summary_cash(self):
        # Scout roll 1 on cash table → Cr20000
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='cash', roll=1)),
        ]
        projection = replay(1, events)

        assert projection.summary.cash == 20000

    def test_cash_roll_3_gives_cr30000(self):
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='cash', roll=3)),
        ]
        projection = replay(1, events)

        assert projection.summary.cash == 30000

    def test_benefits_roll_weapon_adds_to_benefits(self):
        # Scout benefits roll 4 → Weapon
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='benefits', roll=4)),
        ]
        projection = replay(1, events)

        assert any(b.key == 'weapon' for b in projection.summary.benefits)

    def test_benefits_roll_ship_share_adds_to_benefits(self):
        # Scout benefits roll 1 → ship_share
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='benefits', roll=1)),
        ]
        projection = replay(1, events)

        assert any(b.key == 'ship_share' for b in projection.summary.benefits)

    def test_benefits_roll_int_plus_1_increases_int(self):
        # Scout benefits roll 2 → INT +1 (INT was 9)
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='benefits', roll=2)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.INT] == 10

    def test_benefits_roll_edu_plus_1_increases_edu(self):
        # Scout benefits roll 3 → EDU +1 (EDU was 10)
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='benefits', roll=3)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.EDU] == 11

    def test_benefits_roll_scout_ship_adds_to_benefits(self):
        # Scout benefits roll 6 → scout_ship
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='benefits', roll=6)),
        ]
        projection = replay(1, events)

        assert any(b.key == 'scout_ship' for b in projection.summary.benefits)

    def test_benefit_from_continued_career_run_is_counted_once(self):
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=3)),
            Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=True)),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
            Event(id=10, fulfills=(9, 0), handler=SurviveHandler(roll=7)),
            Event(id=11, fulfills=(10, 0), handler=TermEventHandler(roll=5)),
            Event(id=12, fulfills=(11, 0), handler=AdvancementHandler(roll=3)),
            Event(id=13, fulfills=(12, 0), handler=ReenlistHandler(reenlist=False)),
            Event(id=14, fulfills=(13, 0), handler=MusterOutHandler(table='benefits', roll=6)),
        ]

        projection = replay(1, events)

        assert [benefit.key for benefit in projection.summary.benefits] == ['scout_ship']

    def test_muster_out_career_cleared_after_all_rolls(self):
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='cash', roll=1)),
        ]
        projection = replay(1, events)

        assert projection.muster_out_career is None

    def test_roll_count_two_terms_rank_0(self):
        # 2 terms, rank 0 → 2 + 0//2 = 2 rolls
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=3)),  # fail — rank=0
            Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=True)),  # age=22
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
            Event(id=10, fulfills=(9, 0), handler=SurviveHandler(roll=7)),
            Event(id=11, fulfills=(10, 0), handler=TermEventHandler(roll=5)),
            Event(id=12, fulfills=(11, 0), handler=AdvancementHandler(roll=3)),  # fail — rank=0
            Event(id=13, fulfills=(12, 0), handler=ReenlistHandler(reenlist=False)),  # age=26
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 2
        assert projection.summary.career_terms[-1].require_muster_out().terms == 2

    def test_roll_count_includes_rank_bonus(self):
        # 1 term, rank 1 → 1 + 1//2 = 1 + 0 = 1. rank 2 → 1 + 2//2 = 2 rolls
        # Use 2 terms + advance to rank 1 in first term → 2 + 0 = 2
        # Use 1 term with rank 2 → 1 + 1 = 2 rolls
        # Simplest: setup_through_3_terms_reenlist has rank 0 (advancement rolls 3 always fail)
        # Advance in term 1: Scout Courier EDU 9+, EDU=10 DM+1, roll=8 → 8+1=9 ≥ 9 ✓
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=8)),  # 8+1=9>=9 → rank 1
            Event(
                id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=False)
            ),  # 1 term, rank 1 → 1 + 1//2 = 1 + 0 = 1
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1

    def test_roll_count_rank_2_gives_extra_roll(self):
        # rank 2 → rank//2 = 1 extra roll. With 1 term: 1+1=2 rolls
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=8)),  # rank 1
            Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=True)),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
            Event(id=10, fulfills=(9, 0), handler=SurviveHandler(roll=7)),
            Event(id=11, fulfills=(10, 0), handler=TermEventHandler(roll=5)),
            Event(id=12, fulfills=(11, 0), handler=AdvancementHandler(roll=8)),  # rank 2
            Event(id=13, fulfills=(12, 0), handler=ReenlistHandler(reenlist=False)),  # 2 terms, rank 2 → 2+1=3 rolls
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 3

    def test_cash_max_3_times(self):
        # 3 terms, rank 0 → 3 rolls. Take cash 3 times: ok
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=3)),
            Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=True)),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
            Event(id=10, fulfills=(9, 0), handler=SurviveHandler(roll=7)),
            Event(id=11, fulfills=(10, 0), handler=TermEventHandler(roll=5)),
            Event(id=12, fulfills=(11, 0), handler=AdvancementHandler(roll=3)),
            Event(id=13, fulfills=(12, 0), handler=ReenlistHandler(reenlist=True)),
            Event(id=14, fulfills=(13, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
            Event(id=15, fulfills=(14, 0), handler=SurviveHandler(roll=7)),
            Event(id=16, fulfills=(15, 0), handler=TermEventHandler(roll=5)),
            Event(id=17, fulfills=(16, 0), handler=AdvancementHandler(roll=4)),
            Event(id=18, fulfills=(17, 0), handler=ReenlistHandler(reenlist=False)),  # 3 terms, rank 0 → 3 rolls
            Event(id=19, fulfills=(18, 0), handler=MusterOutHandler(table='cash', roll=1)),
            Event(id=20, fulfills=(18, 1), handler=MusterOutHandler(table='cash', roll=1)),
            Event(id=21, fulfills=(18, 2), handler=MusterOutHandler(table='cash', roll=1)),
        ]
        projection = replay(1, events)

        assert projection.summary.cash == 60000
        assert projection.summary.muster_out_cash_count == 3
        assert projection.summary.career_terms[-1].require_muster_out().cash_count == 3

    def test_muster_out_from_multiple_careers_accumulates_cash_and_benefits(self):
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='cash', roll=1)),  # Scout cash: Cr20000
            Event(
                id=10,
                fulfills=(9, 0),
                handler=CareerEntryHandler(
                    career=CITIZEN, assignment=CITIZEN.assignment('Colonist'), qualification_roll=12
                ),
            ),
            Event(id=11, fulfills=(10, 0), handler=SkillChoiceHandler(skill=JackOfAllTrades())),
            Event(id=12, fulfills=(11, 0), handler=SurviveHandler(roll=7)),
            Event(id=13, fulfills=(12, 0), handler=TermEventHandler(roll=5)),
            Event(id=14, fulfills=(13, 0), handler=AdvancementHandler(roll=3)),
            Event(id=15, fulfills=(14, 0), handler=ReenlistHandler(reenlist=False)),
            Event(
                id=16, fulfills=(15, 0), handler=MusterOutHandler(table='benefits', roll=4)
            ),  # Citizen benefits: Weapon
        ]

        projection = replay(1, events)

        assert [term.career.name for term in projection.summary.career_terms] == ['Scout', 'Citizen']
        assert projection.summary.cash == 20000
        assert projection.summary.muster_out_cash_count == 1
        assert projection.summary.career_terms[0].require_muster_out().cash_count == 1
        assert projection.summary.career_terms[1].require_muster_out().cash_count == 0
        assert [benefit.key for benefit in projection.summary.benefits] == ['weapon']
        assert [benefit.key for benefit in projection.summary.career_terms[1].require_muster_out().benefits] == [
            'weapon'
        ]

    def test_muster_out_counts_only_current_career_run_when_reentering_same_career(self):
        # All Scout service skills already known from first run → re-entry gives survival directly (no skill table)
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='cash', roll=1)),  # first Scout run
            Event(
                id=10,
                fulfills=(9, 0),
                handler=CareerEntryHandler(
                    career=CITIZEN, assignment=CITIZEN.assignment('Colonist'), qualification_roll=12
                ),
            ),
            Event(id=11, fulfills=(10, 0), handler=SkillChoiceHandler(skill=JackOfAllTrades())),
            Event(id=12, fulfills=(11, 0), handler=SurviveHandler(roll=7)),
            Event(id=13, fulfills=(12, 0), handler=TermEventHandler(roll=5)),
            Event(id=14, fulfills=(13, 0), handler=AdvancementHandler(roll=3)),
            Event(id=15, fulfills=(14, 0), handler=ReenlistHandler(reenlist=False)),
            Event(
                id=16, fulfills=(15, 0), handler=MusterOutHandler(table='benefits', roll=4)
            ),  # intervening Citizen run
            Event(
                id=17,
                fulfills=(16, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=18, fulfills=(17, 0), handler=SurviveHandler(roll=7)),
            Event(id=19, fulfills=(18, 0), handler=TermEventHandler(roll=5)),
            Event(id=20, fulfills=(19, 0), handler=AdvancementHandler(roll=3)),
            Event(id=21, fulfills=(20, 0), handler=ReenlistHandler(reenlist=False)),
        ]

        projection = replay(1, events)

        assert [term.career.name for term in projection.summary.career_terms] == ['Scout', 'Citizen', 'Scout']
        assert projection.summary.career_terms[-1].require_muster_out().terms == 1
        assert len([p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]) == 1

    def test_cash_4th_time_raises_error(self):
        # 3 terms, rank 2 → 3 + 1 = 4 rolls; cash max 3 → 4th raises error
        # Advance twice: Scout Courier EDU 9+, EDU=10 (DM+1), roll=8 → 8+1=9 ≥ 9 ✓
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=8)),  # rank 1
            Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=True)),  # age=22
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
            Event(id=10, fulfills=(9, 0), handler=SurviveHandler(roll=7)),
            Event(id=11, fulfills=(10, 0), handler=TermEventHandler(roll=5)),
            Event(id=12, fulfills=(11, 0), handler=AdvancementHandler(roll=8)),  # rank 2
            Event(id=13, fulfills=(12, 0), handler=ReenlistHandler(reenlist=True)),  # age=26
            Event(id=14, fulfills=(13, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
            Event(id=15, fulfills=(14, 0), handler=SurviveHandler(roll=7)),
            Event(id=16, fulfills=(15, 0), handler=TermEventHandler(roll=5)),
            Event(id=17, fulfills=(16, 0), handler=AdvancementHandler(roll=4)),  # fail
            Event(id=18, fulfills=(17, 0), handler=ReenlistHandler(reenlist=False)),  # age=30, 3 terms rank 2 → 4 rolls
            Event(id=19, fulfills=(18, 0), handler=MusterOutHandler(table='cash', roll=1)),
            Event(id=20, fulfills=(18, 1), handler=MusterOutHandler(table='cash', roll=1)),
            Event(id=21, fulfills=(18, 2), handler=MusterOutHandler(table='cash', roll=1)),
            Event(id=22, fulfills=(18, 3), handler=MusterOutHandler(table='cash', roll=1)),  # 4th cash → error
        ]
        with pytest.raises(ReplayError, match='Cash'):
            replay(1, events)

    def test_mishap_ejection_loses_current_term_benefit(self):
        # 1 term enter → mishap → lose current term's roll → 0 muster out rolls
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=3)),  # fail survive
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=5)),  # Scout mishap 5: no effects, ejected
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 0

    def test_mishap_ejection_after_2_terms_gets_1_roll(self):
        # 2 terms: first completes normally (reenlist=True), second term mishap → lose current → 1 roll
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=7)),
            Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=5)),
            Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=3)),
            Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=True)),
            Event(id=9, fulfills=(8, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
            Event(id=10, fulfills=(9, 0), handler=SurviveHandler(roll=3)),  # fail survive
            Event(id=11, fulfills=(10, 0), handler=MishapHandler(roll=5)),  # ejected, lose current term → 1 roll
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1

    def test_benefit_dm_tracked_on_muster_out(self):
        # Scholar event 5 grants benefit_dm+1 — stored on MusterOut.benefit_roll_dms.
        # The player includes the DM in their roll value (MusterOutEvent.roll already includes DMs).
        # Scholar cash row 1=Cr5000, row 2=Cr10000. Player rolls 1 and applies DM+1 → submits roll=2.
        events = [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=5)),  # scholar event 5: benefit_dm +1
            Event(id=9, fulfills=(8, 0), handler=AdvancementHandler(roll=3)),
            Event(id=10, fulfills=(9, 0), handler=ReenlistHandler(reenlist=False)),
        ]
        projection = replay(1, events)

        assert projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms == [BenefitRollDm(amount=1)]

    def test_scholar_soc_plus_1_benefit(self):
        # Scholar benefits roll 4 → SOC +1 (SOC was 5)
        events = [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=5)),
            Event(id=9, fulfills=(8, 0), handler=AdvancementHandler(roll=3)),
            Event(id=10, fulfills=(9, 0), handler=ReenlistHandler(reenlist=False)),
            Event(id=11, fulfills=(10, 0), handler=MusterOutHandler(table='benefits', roll=4)),
        ]
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.SOC] == 6  # was 5

    def test_scholar_two_ship_shares_benefit(self):
        # Scholar benefits roll 3 → Two Ship Shares → 2 ship_share entries
        events = [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=5)),
            Event(id=9, fulfills=(8, 0), handler=AdvancementHandler(roll=3)),
            Event(id=10, fulfills=(9, 0), handler=ReenlistHandler(reenlist=False)),
            Event(id=11, fulfills=(10, 0), handler=MusterOutHandler(table='benefits', roll=3)),
        ]
        projection = replay(1, events)

        assert sum(1 for b in projection.summary.benefits if b.key == 'ship_share') == 2

    def test_scholar_scientific_equipment_benefit(self):
        # Scholar benefits roll 5 → scientific_equipment
        events = [
            *_scholar_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=SCHOLAR, assignment=SCHOLAR.assignment('Field Researcher'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SkillChoiceHandler(skill=Drive())),
            Event(id=6, fulfills=(4, 1), handler=SkillChoiceHandler(skill=SpaceScience())),
            Event(id=7, fulfills=(6, 0), handler=SurviveHandler(roll=7)),
            Event(id=8, fulfills=(7, 0), handler=TermEventHandler(roll=5)),
            Event(id=9, fulfills=(8, 0), handler=AdvancementHandler(roll=3)),
            Event(id=10, fulfills=(9, 0), handler=ReenlistHandler(reenlist=False)),
            Event(id=11, fulfills=(10, 0), handler=MusterOutHandler(table='benefits', roll=5)),
        ]
        projection = replay(1, events)

        assert any(b.key == 'scientific_equipment' for b in projection.summary.benefits)

    def test_aging_reenlist_false_gets_muster_out_after_aging(self):
        # 4 terms, reenlist=False, age=34 → aging required → muster out after aging resolves
        events = [
            *_setup_through_4_terms_advancement(),
            Event(id=23, fulfills=(22, 0), handler=ReenlistHandler(reenlist=False)),
            Event(id=24, fulfills=(23, 0), handler=AgingRollHandler(roll=5)),  # no effect (5-4=1)
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) > 0

    def test_aging_reenlist_false_roll_count(self):
        # 4 terms, rank 0 → 4 muster out rolls
        events = [
            *_setup_through_4_terms_advancement(),
            Event(id=23, fulfills=(22, 0), handler=AgingRollHandler(roll=5)),  # no effect → reenlist pending
            Event(id=24, fulfills=(23, 0), handler=ReenlistHandler(reenlist=False)),
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 4

    def test_mishap_aging_muster_out_loses_current_term(self):
        # 4th term mishap ejection with aging → 3 rolls (4-1=3 terms, rank 0)
        events = [
            *_setup_through_3_terms_reenlist(),
            Event(id=19, fulfills=(18, 0), handler=SkillTableHandler(table='service_skills', roll=5)),
            Event(id=20, fulfills=(19, 0), handler=SurviveHandler(roll=3)),  # fail
            Event(id=21, fulfills=(20, 0), handler=MishapHandler(roll=5)),  # ejected, age=34
            Event(id=22, fulfills=(21, 0), handler=AgingRollHandler(roll=5)),  # no effect
        ]
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 3


# ── Career run continuity ──────────────────────────────────────────────────────


def _agent_one_term_muster_out() -> list:
    """Agent/Intelligence one term, then muster out.
    STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5. Age=22 after one term.
    Event 4: BenefitDmEffect — no pending input created.
    Advancement: INT 5+, DM+1, roll=3 → 4 < 5 → fail.
    1 term rank 0 → 1 muster-out roll at '8.0'.
    Career choice pending at '9.0' after roll.
    """
    return [
        *_full_setup(),
        Event(
            id=4,
            fulfills=(3, 0),
            handler=CareerEntryHandler(career=AGENT, assignment=AGENT.assignment('Intelligence'), qualification_roll=5),
        ),
        Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=6)),
        Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=4)),
        Event(id=7, fulfills=(6, 0), handler=AdvancementHandler(roll=3)),
        Event(id=8, fulfills=(7, 0), handler=ReenlistHandler(reenlist=False)),
        Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='benefits', roll=1)),
    ]


class TestCareerRunContinuity:
    """Run-continuity semantics: which transitions extend a run vs. start a new one."""

    def test_agent_different_assignment_reentry_starts_new_run(self):
        """Agent/Intelligence → muster out → Agent/Corporate: new run (terms=1), not continuation."""
        events = [
            *_agent_one_term_muster_out(),
            Event(
                id=10,
                fulfills=(9, 0),
                handler=CareerEntryHandler(
                    career=AGENT, assignment=AGENT.assignment('Corporate'), qualification_roll=5
                ),
            ),
        ]
        projection = replay(1, events)

        assert [t.career.name for t in projection.summary.career_terms] == ['Agent', 'Agent']
        assert projection.summary.career_terms[-1].require_muster_out().terms == 1

    def test_new_career_after_muster_out_starts_fresh_run(self):
        """Scout → muster out → different career: fresh run (terms=1)."""
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='benefits', roll=1)),
            Event(
                id=10,
                fulfills=(9, 0),
                handler=CareerEntryHandler(career=ARMY, assignment=ARMY.assignment('Support'), qualification_roll=7),
            ),
        ]
        projection = replay(1, events)

        assert projection.summary.career_terms[-1].career.name == 'Army'
        assert projection.summary.career_terms[-1].require_muster_out().terms == 1

    def test_failed_qualification_after_muster_out_falls_to_draft(self):
        """After muster-out, a failed qualification roll for a new career produces a draft/Drifter choice."""
        events = [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='benefits', roll=1)),
            # Army qualification: STR 5+, STR=7 (DM+1). Roll=1 → 1+1=2 < 5 → fail.
            Event(
                id=10,
                fulfills=(9, 0),
                handler=CareerEntryHandler(career=ARMY, assignment=ARMY.assignment('Support'), qualification_roll=1),
            ),
        ]
        projection = replay(1, events)

        assert any(isinstance(p, PendingDraftChoice) for p in projection.pending_inputs)
        assert projection.summary.current_career is None

    def test_ejection_blocks_immediate_same_career_reentry(self):
        """A character ejected from Scout may not re-enter Scout the following term.

        Currently fails: start_career() does not enforce this restriction.
        Requires tracking whether the previous departure was a mishap ejection.
        """
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=3)),  # fail END 7+
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=5)),  # Scout mishap 5: no effects, ejected
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
        ]
        with pytest.raises(ReplayError, match='ejected'):
            replay(1, events)

    def test_ejection_blocks_same_career_different_assignment_reentry(self):
        """A character ejected from Agent may not re-enter any Agent assignment the following term."""
        events = [
            *_full_setup(),
            Event(
                id=4,
                fulfills=(3, 0),
                handler=CareerEntryHandler(
                    career=AGENT, assignment=AGENT.assignment('Intelligence'), qualification_roll=5
                ),
            ),
            Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=3)),  # fail END 6+
            Event(id=6, fulfills=(5, 0), handler=MishapHandler(roll=4)),  # Agent mishap 4: Enemy + Deception 1, ejected
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerEntryHandler(
                    career=AGENT, assignment=AGENT.assignment('Corporate'), qualification_roll=5
                ),
            ),
        ]
        with pytest.raises(ReplayError, match='ejected'):
            replay(1, events)

    def _scout_one_term_muster_out(self) -> list:
        return [
            *_setup_through_reenlist_false(),
            Event(id=9, fulfills=(8, 0), handler=MusterOutHandler(table='benefits', roll=1)),
        ]

    def test_voluntary_departure_blocks_same_assignment_in_assignment_change_career(self):
        """Scout voluntary muster-out → cannot re-enter Scout Courier the following term."""
        events = [
            *self._scout_one_term_muster_out(),
            Event(
                id=10,
                fulfills=(9, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
            ),
        ]
        with pytest.raises(ReplayError, match='voluntary'):
            replay(1, events)

    def test_voluntary_departure_blocks_any_assignment_in_assignment_change_career(self):
        """Scout voluntary muster-out → cannot re-enter Scout (any assignment) the following term."""
        events = [
            *self._scout_one_term_muster_out(),
            Event(
                id=10,
                fulfills=(9, 0),
                handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Surveyor'), qualification_roll=7),
            ),
        ]
        with pytest.raises(ReplayError, match='voluntary'):
            replay(1, events)

    def test_voluntary_departure_blocks_same_assignment_in_non_assignment_change_career(self):
        """Agent/Intelligence voluntary muster-out → cannot re-enter Agent/Intelligence the following term."""
        events = [
            *_agent_one_term_muster_out(),
            Event(
                id=10,
                fulfills=(9, 0),
                handler=CareerEntryHandler(
                    career=AGENT, assignment=AGENT.assignment('Intelligence'), qualification_roll=5
                ),
            ),
        ]
        with pytest.raises(ReplayError, match='voluntary'):
            replay(1, events)

    def test_voluntary_departure_allows_different_assignment_in_non_assignment_change_career(self):
        """Agent/Intelligence voluntary muster-out → Agent/Corporate is allowed (new career run)."""
        events = [
            *_agent_one_term_muster_out(),
            Event(
                id=10,
                fulfills=(9, 0),
                handler=CareerEntryHandler(
                    career=AGENT, assignment=AGENT.assignment('Corporate'), qualification_roll=5
                ),
            ),
        ]
        projection = replay(1, events)

        assert projection.summary.career_terms[-1].career.name == 'Agent'
        assert projection.summary.career_terms[-1].assignment.name == 'Corporate'
        assert projection.summary.career_terms[-1].require_muster_out().terms == 1
