"""Tests for muster out: benefit rolls, cash limits, and roll counts."""

from typing import Literal

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
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, JackOfAllTrades, SpaceScience
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import ReplayError, replay
from tests.character.helpers import MOCK_WORLD, _scholar_setup, pending_id as _pending, scripted_event as _event


def _full_setup(character_id: int = 1) -> list:
    """Return events that get a character through setup: started → ucp → background skills."""
    # STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 → 4 background skills
    started = _event(handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'))
    ucp = _event(fulfills=_pending(started, 0), handler=UcpHandler(ucp='7869A5'))
    background = _event(
        fulfills=_pending(ucp, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    return [started, ucp, background]


def _append_event(events: list, *, handler, pending_index: int = 0):
    event = _event(fulfills=_pending(events[-1], pending_index), handler=handler)
    events.append(event)
    return event


def _scout_courier_entry_events() -> list:
    events = _full_setup()
    _append_event(
        events,
        handler=CareerEntryHandler(career=SCOUT, assignment=SCOUT.assignment('Courier'), qualification_roll=7),
    )
    return events


def _scout_courier_terms(advancement_rolls: list[int], *, final_reenlist: bool) -> list:
    events = _scout_courier_entry_events()
    for term_index, advancement_roll in enumerate(advancement_rolls):
        if term_index > 0:
            _append_event(
                events,
                handler=SkillTableHandler(table='service_skills', roll=5),
            )
        _append_event(events, handler=SurviveHandler(roll=7))
        _append_event(events, handler=TermEventHandler(roll=5))
        _append_event(events, handler=AdvancementHandler(roll=advancement_roll))
        _append_event(
            events,
            handler=ReenlistHandler(reenlist=final_reenlist if term_index == len(advancement_rolls) - 1 else True),
        )
    return events


def _with_muster_out(events: list, *, table: Literal['cash', 'benefits'], roll: int) -> list:
    events = [*events]
    _append_event(events, handler=MusterOutHandler(table=table, roll=roll))
    return events


def _enter_career(
    events: list,
    *,
    career,
    assignment_name: str,
    qualification_roll: int,
):
    return _append_event(
        events,
        handler=CareerEntryHandler(
            career=career,
            assignment=career.assignment(assignment_name),
            qualification_roll=qualification_roll,
        ),
    )


def _citizen_colonist_one_term(events: list, *, muster_out_roll: int | None = 4) -> list:
    events = [*events]
    _enter_career(events, career=CITIZEN, assignment_name='Colonist', qualification_roll=12)
    _append_event(events, handler=SkillChoiceHandler(skill=JackOfAllTrades()))
    _append_event(events, handler=SurviveHandler(roll=7))
    _append_event(events, handler=TermEventHandler(roll=5))
    _append_event(events, handler=AdvancementHandler(roll=3))
    _append_event(events, handler=ReenlistHandler(reenlist=False))
    if muster_out_roll is not None:
        _append_event(events, handler=MusterOutHandler(table='benefits', roll=muster_out_roll))
    return events


def _scholar_field_researcher_one_term() -> list:
    events = _scholar_setup()
    entry = _enter_career(
        events,
        career=SCHOLAR,
        assignment_name='Field Researcher',
        qualification_roll=5,
    )
    _append_event(events, pending_index=0, handler=SkillChoiceHandler(skill=Drive()))
    science = _event(fulfills=_pending(entry, 1), handler=SkillChoiceHandler(skill=SpaceScience()))
    events.append(science)
    _append_event(events, handler=SurviveHandler(roll=7))
    _append_event(events, handler=TermEventHandler(roll=5))
    _append_event(events, handler=AdvancementHandler(roll=3))
    _append_event(events, handler=ReenlistHandler(reenlist=False))
    return events


def _ejected_from(career, assignment_name: str, *, survive_roll: int, mishap_roll: int) -> list:
    events = _full_setup()
    _enter_career(events, career=career, assignment_name=assignment_name, qualification_roll=7)
    _append_event(events, handler=SurviveHandler(roll=survive_roll))
    _append_event(events, handler=MishapHandler(roll=mishap_roll))
    return events


def _setup_through_3_terms_reenlist() -> list:
    """Complete setup and 3 Scout Courier terms. Age=30 after.

    Uses service_skills roll=5 (a non-specialized skill) to avoid PendingSkillTableChoice.
    """
    return _scout_courier_terms([3, 3, 4], final_reenlist=True)


def _setup_through_4_terms_advancement() -> list:
    """Complete setup through advancement of term 4. Age still 30.
    Resolving the advancement pending with reenlist=True triggers aging (age->34).
    """
    base = _setup_through_3_terms_reenlist()
    _append_event(base, handler=SkillTableHandler(table='service_skills', roll=5))
    _append_event(base, handler=SurviveHandler(roll=7))
    _append_event(base, handler=TermEventHandler(roll=5))
    _append_event(base, handler=AdvancementHandler(roll=5))
    return base


def _setup_through_reenlist_false() -> list:
    """1 Scout Courier term, reenlist=False. Age=22, career ended."""
    # term_count=1, rank=0 → 1 muster out roll (1 term + 0 rank // 2)
    return _scout_courier_terms([3], final_reenlist=False)


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

    def test_career_recorded_on_term_while_muster_out_pending(self):
        projection = replay(1, _setup_through_reenlist_false())

        assert projection.summary.career_terms[-1].career.name == 'Scout'
        assert projection.summary.career_terms[-1].muster_out is not None
        assert projection.summary.career_terms[-1].muster_out.rolls_remaining > 0

    def test_cash_roll_adds_to_summary_cash(self):
        # Scout roll 1 on cash table → Cr20000
        events = _with_muster_out(_setup_through_reenlist_false(), table='cash', roll=1)
        projection = replay(1, events)

        assert projection.summary.cash == 20000

    def test_cash_roll_3_gives_cr30000(self):
        events = _with_muster_out(_setup_through_reenlist_false(), table='cash', roll=3)
        projection = replay(1, events)

        assert projection.summary.cash == 30000

    def test_benefits_roll_weapon_adds_to_benefits(self):
        # Scout benefits roll 4 → Weapon
        events = _with_muster_out(_setup_through_reenlist_false(), table='benefits', roll=4)
        projection = replay(1, events)

        assert any(b.key == 'weapon' for b in projection.summary.benefits)

    def test_benefits_roll_ship_share_adds_to_benefits(self):
        # Scout benefits roll 1 → ship_share
        events = _with_muster_out(_setup_through_reenlist_false(), table='benefits', roll=1)
        projection = replay(1, events)

        assert any(b.key == 'ship_share' for b in projection.summary.benefits)

    def test_benefits_roll_int_plus_1_increases_int(self):
        # Scout benefits roll 2 → INT +1 (INT was 9)
        events = _with_muster_out(_setup_through_reenlist_false(), table='benefits', roll=2)
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.INT] == 10

    def test_benefits_roll_edu_plus_1_increases_edu(self):
        # Scout benefits roll 3 → EDU +1 (EDU was 10)
        events = _with_muster_out(_setup_through_reenlist_false(), table='benefits', roll=3)
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.EDU] == 11

    def test_benefits_roll_scout_ship_adds_to_benefits(self):
        # Scout benefits roll 6 → scout_ship
        events = _with_muster_out(_setup_through_reenlist_false(), table='benefits', roll=6)
        projection = replay(1, events)

        assert any(b.key == 'scout_ship' for b in projection.summary.benefits)

    def test_benefit_from_continued_career_run_is_counted_once(self):
        events = _with_muster_out(_scout_courier_terms([3, 3], final_reenlist=False), table='benefits', roll=6)

        projection = replay(1, events)

        assert [benefit.key for benefit in projection.summary.benefits] == ['scout_ship']

    def test_muster_out_marked_used_after_all_rolls(self):
        events = _with_muster_out(_setup_through_reenlist_false(), table='cash', roll=1)
        projection = replay(1, events)

        assert projection.summary.career_terms[-1].muster_out is not None
        assert projection.summary.career_terms[-1].muster_out.used is True

    def test_roll_count_two_terms_rank_0(self):
        # 2 terms, rank 0 → 2 + 0//2 = 2 rolls
        events = _scout_courier_terms([3, 3], final_reenlist=False)
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1
        assert projection.summary.career_terms[-1].require_muster_out().rolls_remaining == 2
        assert projection.summary.career_terms[-1].require_muster_out().terms == 2

    def test_roll_count_includes_rank_bonus(self):
        # Rules: rank 1-2 → +1 roll, rank 3-4 → +2, rank 5-6 → +3
        # 1 term, rank 1 → 1 + 1 = 2 rolls
        # Scout Courier advancement: EDU 9+, EDU=10 DM+1, roll=8 → 8+1=9 ≥ 9 ✓ → rank 1
        events = _scout_courier_terms([8], final_reenlist=False)
        projection = replay(1, events)

        assert projection.summary.career_terms[-1].require_muster_out().rolls_remaining == 2

    def test_roll_count_rank_2_gives_extra_roll(self):
        # rank 2 → +1 extra roll (rules: rank 1-2 gives +1). 2 terms + rank 2 = 3 rolls.
        events = _scout_courier_terms([8, 8], final_reenlist=False)
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1
        assert projection.summary.career_terms[-1].require_muster_out().rolls_remaining == 3

    def test_cash_max_3_times(self):
        # 3 terms, rank 0 → 3 rolls. Take cash 3 times: ok
        events = _scout_courier_terms([3, 3, 4], final_reenlist=False)
        for _ in range(3):
            _append_event(events, handler=MusterOutHandler(table='cash', roll=1))
        projection = replay(1, events)

        assert projection.summary.cash == 60000
        assert projection.summary.muster_out_cash_count == 3
        assert projection.summary.career_terms[-1].require_muster_out().cash_count == 3

    def test_muster_out_from_multiple_careers_accumulates_cash_and_benefits(self):
        scout_cash = _with_muster_out(_setup_through_reenlist_false(), table='cash', roll=1)  # Scout cash: Cr20000
        events = _citizen_colonist_one_term(scout_cash, muster_out_roll=4)  # Citizen benefits: Weapon

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
        events = _with_muster_out(_setup_through_reenlist_false(), table='cash', roll=1)
        events = _citizen_colonist_one_term(events, muster_out_roll=4)  # intervening Citizen run
        _enter_career(events, career=SCOUT, assignment_name='Courier', qualification_roll=7)
        _append_event(events, handler=SurviveHandler(roll=7))
        _append_event(events, handler=TermEventHandler(roll=5))
        _append_event(events, handler=AdvancementHandler(roll=3))
        _append_event(events, handler=ReenlistHandler(reenlist=False))

        projection = replay(1, events)

        assert [term.career.name for term in projection.summary.career_terms] == ['Scout', 'Citizen', 'Scout']
        assert projection.summary.career_terms[-1].require_muster_out().terms == 1
        assert len([p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]) == 1

    def test_cash_4th_time_raises_error(self):
        # 3 terms, rank 2 → 3 + 1 = 4 rolls; cash max 3 → 4th raises error
        # Advance twice: Scout Courier EDU 9+, EDU=10 (DM+1), roll=8 → 8+1=9 ≥ 9 ✓
        events = _scout_courier_terms([8, 8, 4], final_reenlist=False)
        for _ in range(4):
            _append_event(events, handler=MusterOutHandler(table='cash', roll=1))
        with pytest.raises(ReplayError, match='Cash'):
            replay(1, events)

    def test_mishap_ejection_loses_current_term_benefit(self):
        # 1 term enter → mishap → lose current term's roll → 0 muster out rolls
        events = _ejected_from(SCOUT, 'Courier', survive_roll=3, mishap_roll=5)
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 0

    def test_mishap_ejection_after_2_terms_gets_1_roll(self):
        # 2 terms: first completes normally (reenlist=True), second term mishap → lose current → 1 roll
        events = _scout_courier_terms([3], final_reenlist=True)
        _append_event(events, handler=SkillTableHandler(table='service_skills', roll=5))
        _append_event(events, handler=SurviveHandler(roll=3))  # fail survive
        _append_event(events, handler=MishapHandler(roll=5))  # ejected, lose current term → 1 roll
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1

    def test_benefit_dm_tracked_on_muster_out(self):
        # Scholar event 5 grants benefit_dm+1 — stored on MusterOut.benefit_roll_dms.
        # The player includes the DM in their roll value (MusterOutEvent.roll already includes DMs).
        # Scholar cash row 1=Cr5000, row 2=Cr10000. Player rolls 1 and applies DM+1 → submits roll=2.
        events = _scholar_field_researcher_one_term()
        projection = replay(1, events)

        assert projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms == [BenefitRollDm(amount=1)]

    def test_scholar_soc_plus_1_benefit(self):
        # Scholar benefits roll 4 → SOC +1 (SOC was 5)
        events = _with_muster_out(_scholar_field_researcher_one_term(), table='benefits', roll=4)
        projection = replay(1, events)

        assert projection.summary.characteristics[Chars.SOC] == 6  # was 5

    def test_scholar_two_ship_shares_benefit(self):
        # Scholar benefits roll 3 → Two Ship Shares → 2 ship_share entries
        events = _with_muster_out(_scholar_field_researcher_one_term(), table='benefits', roll=3)
        projection = replay(1, events)

        assert sum(1 for b in projection.summary.benefits if b.key == 'ship_share') == 2

    def test_scholar_scientific_equipment_benefit(self):
        # Scholar benefits roll 5 → scientific_equipment
        events = _with_muster_out(_scholar_field_researcher_one_term(), table='benefits', roll=5)
        projection = replay(1, events)

        assert any(b.key == 'scientific_equipment' for b in projection.summary.benefits)

    def test_aging_reenlist_false_gets_muster_out_after_aging(self):
        # 4 terms, age=34 → aging roll first (no effect), then reenlist=False → muster out
        events = _setup_through_4_terms_advancement()
        aging = _append_event(events, handler=AgingRollHandler(roll=5))  # no effect (5-4=1)
        events.append(Event(fulfills=_pending(aging, 0), handler=ReenlistHandler(reenlist=False)))
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) > 0

    def test_aging_reenlist_false_roll_count(self):
        # 4 terms, rank 0 → 4 muster out rolls
        events = _setup_through_4_terms_advancement()
        aging = _append_event(events, handler=AgingRollHandler(roll=5))  # no effect → reenlist pending
        events.append(Event(fulfills=_pending(aging, 0), handler=ReenlistHandler(reenlist=False)))
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1
        assert projection.summary.career_terms[-1].require_muster_out().rolls_remaining == 4

    def test_mishap_aging_muster_out_loses_current_term(self):
        # 4th term mishap ejection with aging → 3 rolls (4-1=3 terms, rank 0)
        events = _setup_through_3_terms_reenlist()
        _append_event(events, handler=SkillTableHandler(table='service_skills', roll=5))
        _append_event(events, handler=SurviveHandler(roll=3))  # fail
        _append_event(events, handler=MishapHandler(roll=5))  # ejected, age=34
        _append_event(events, handler=AgingRollHandler(roll=5))  # no effect
        projection = replay(1, events)

        muster_out_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]
        assert len(muster_out_pendings) == 1
        assert projection.summary.career_terms[-1].require_muster_out().rolls_remaining == 3


# ── Career run continuity ──────────────────────────────────────────────────────


def _agent_one_term_muster_out() -> list:
    """Agent/Intelligence one term, then muster out.
    STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5. Age=22 after one term.
    Event 4: BenefitDmEffect — no pending input created.
    Advancement: INT 5+, DM+1, roll=3 → 4 < 5 → fail.
    1 term rank 0 → 1 muster-out roll.
    Career choice is pending after the benefit roll.
    """
    events = _full_setup()
    _enter_career(events, career=AGENT, assignment_name='Intelligence', qualification_roll=5)
    _append_event(events, handler=SurviveHandler(roll=6))
    _append_event(events, handler=TermEventHandler(roll=4))
    _append_event(events, handler=AdvancementHandler(roll=3))
    _append_event(events, handler=ReenlistHandler(reenlist=False))
    _append_event(events, handler=MusterOutHandler(table='benefits', roll=1))
    return events


class TestCareerRunContinuity:
    """Run-continuity semantics: which transitions extend a run vs. start a new one."""

    def test_agent_different_assignment_reentry_starts_new_run(self):
        """Agent/Intelligence → muster out → Agent/Corporate: new run (terms=1), not continuation."""
        events = _agent_one_term_muster_out()
        _enter_career(events, career=AGENT, assignment_name='Corporate', qualification_roll=5)
        projection = replay(1, events)

        assert [t.career.name for t in projection.summary.career_terms] == ['Agent', 'Agent']
        assert projection.summary.career_terms[-1].require_muster_out().terms == 1

    def test_new_career_after_muster_out_starts_fresh_run(self):
        """Scout → muster out → different career: fresh run (terms=1)."""
        events = self._scout_one_term_muster_out()
        _enter_career(events, career=ARMY, assignment_name='Support', qualification_roll=7)
        projection = replay(1, events)

        assert projection.summary.career_terms[-1].career.name == 'Army'
        assert projection.summary.career_terms[-1].require_muster_out().terms == 1

    def test_failed_qualification_after_muster_out_falls_to_draft(self):
        """After muster-out, a failed qualification roll for a new career produces a draft/Drifter choice."""
        events = self._scout_one_term_muster_out()
        # Army qualification: STR 5+, STR=7 (DM+1). Roll=1 → 1+1=2 < 5 → fail.
        _enter_career(events, career=ARMY, assignment_name='Support', qualification_roll=1)
        projection = replay(1, events)

        assert any(isinstance(p, PendingDraftChoice) for p in projection.pending_inputs)
        assert projection.summary.current_career is None

    def test_ejection_blocks_immediate_same_career_reentry(self):
        """A character ejected from Scout may not re-enter Scout the following term.

        Currently fails: start_career() does not enforce this restriction.
        Requires tracking whether the previous departure was a mishap ejection.
        """
        events = _ejected_from(SCOUT, 'Courier', survive_roll=3, mishap_roll=5)
        _enter_career(events, career=SCOUT, assignment_name='Courier', qualification_roll=7)
        with pytest.raises(ReplayError, match='ejected'):
            replay(1, events)

    def test_ejection_blocks_same_career_different_assignment_reentry(self):
        """A character ejected from Agent may not re-enter any Agent assignment the following term."""
        events = _ejected_from(AGENT, 'Intelligence', survive_roll=3, mishap_roll=4)
        _enter_career(events, career=AGENT, assignment_name='Corporate', qualification_roll=5)
        with pytest.raises(ReplayError, match='ejected'):
            replay(1, events)

    def _scout_one_term_muster_out(self) -> list:
        return _with_muster_out(_setup_through_reenlist_false(), table='benefits', roll=1)

    def test_voluntary_departure_blocks_same_assignment_in_assignment_change_career(self):
        """Scout voluntary muster-out → cannot re-enter Scout Courier the following term."""
        events = self._scout_one_term_muster_out()
        _enter_career(events, career=SCOUT, assignment_name='Courier', qualification_roll=7)
        with pytest.raises(ReplayError, match='voluntary'):
            replay(1, events)

    def test_voluntary_departure_blocks_any_assignment_in_assignment_change_career(self):
        """Scout voluntary muster-out → cannot re-enter Scout (any assignment) the following term."""
        events = self._scout_one_term_muster_out()
        _enter_career(events, career=SCOUT, assignment_name='Surveyor', qualification_roll=7)
        with pytest.raises(ReplayError, match='voluntary'):
            replay(1, events)

    def test_voluntary_departure_blocks_same_assignment_in_non_assignment_change_career(self):
        """Agent/Intelligence voluntary muster-out → cannot re-enter Agent/Intelligence the following term."""
        events = _agent_one_term_muster_out()
        _enter_career(events, career=AGENT, assignment_name='Intelligence', qualification_roll=5)
        with pytest.raises(ReplayError, match='voluntary'):
            replay(1, events)

    def test_voluntary_departure_allows_different_assignment_in_non_assignment_change_career(self):
        """Agent/Intelligence voluntary muster-out → Agent/Corporate is allowed (new career run)."""
        events = _agent_one_term_muster_out()
        _enter_career(events, career=AGENT, assignment_name='Corporate', qualification_roll=5)
        projection = replay(1, events)

        assert projection.summary.career_terms[-1].career.name == 'Agent'
        assert projection.summary.career_terms[-1].assignment.name == 'Corporate'
        assert projection.summary.career_terms[-1].require_muster_out().terms == 1
