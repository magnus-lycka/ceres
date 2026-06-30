"""Tests for advancement.py — cross-career advancement and commission mechanics."""

import json

import pytest

from ceres.character.domain.career import ARMY, SCOUT
from ceres.character.domain.career.advancement import (
    AdvancementHandler,
    CommissionHandler,
    PendingAdvancement,
    PendingCommissionChoice,
    advancement_pending,
    career_progress_pending,
    rank_bonus_skill,
)
from ceres.character.domain.career.career_data import AdvancementDmOption, RankBonus
from ceres.character.domain.career.career_events import (
    AdvancementDmChoiceHandler,
    PendingRankBonusChoice,
    SkillChoiceHandler,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, GunCombat, Medic
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.errors import ReplayError
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver

# Army Support: advancement EDU 7+, commission SOC 8+.
# EDU=A(10) DM+2 → 4 background skills.  SOC=9 DM+1 → commission 8+ succeeds on roll 7.
# Term event roll 5 (BenefitDm entry) leaves PendingCommissionChoice without a blocking skill choice.
_UCP = '7869A9'


def _army() -> CharacterDriver:
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp(_UCP)
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    d.career('Army', 'Support', roll=5)
    d.rank_bonus_choice(GunCombat())
    return d


def _army_after_term_event() -> CharacterDriver:
    """Army through survive + term_event(5) — PendingCommissionChoice is next."""
    d = _army()
    d.survive(5)
    d.term_event(5)
    return d


def test_roll_12_records_forced_stay_on_term():
    """Rolling 12 on advancement records the forced stay on the career term."""
    d = _army_after_term_event()
    d.commission(attempt=False)
    d.advancement(12)
    assert d.projection.summary.career_terms[-1].forced_stay is True


def test_roll_12_prevents_muster_out():
    """Rolling 12 on advancement forbids mustering out that term."""
    from ceres.character.domain.career.career_events import PendingAssignmentChangeChoice

    d = _army_after_term_event()
    d.commission(attempt=False)
    d.advancement(12)
    choices = [p for p in d.projection.pending_inputs if isinstance(p, PendingAssignmentChangeChoice)]
    assert choices and choices[0].muster_out is False


def test_successful_advancement_increases_rank():
    d = _army_after_term_event()
    d.commission(attempt=False)
    rank_before = d.projection.summary.rank or 0
    d.advancement(10)
    assert (d.projection.summary.rank or 0) > rank_before


def test_failed_advancement_does_not_change_rank():
    d = _army_after_term_event()
    d.commission(attempt=False)
    rank_before = d.projection.summary.rank or 0
    d.advancement(1)
    assert (d.projection.summary.rank or 0) == rank_before


def test_commission_success_grants_officer_rank():
    d = _army_after_term_event()
    d.commission(attempt=True, roll=8)
    rank_before = d.projection.summary.rank or 0
    assert rank_before >= 1


def test_skipping_commission_does_not_grant_rank():
    d = _army()
    d.survive(5)
    d.term_event(5)
    d.commission(attempt=False)
    d.advancement(1)
    assert (d.projection.summary.rank or 0) == 0


def test_roll_1_in_first_term_records_forced_leave_on_term():
    """Rolling 1 on advancement (≤ 1 prior term) records forced leave on the career term."""
    d = _army_after_term_event()
    d.commission(attempt=False)
    d.advancement(1)
    assert d.projection.summary.career_terms[-1].forced_leave is True


def test_roll_1_in_first_term_forces_muster_out():
    """Rolling 1 on advancement in term 1 (≤ 1 prior term) forces immediate muster out."""
    from ceres.character.domain.career.muster_out import PendingMusterOut

    d = _army_after_term_event()
    d.commission(attempt=False)
    d.advancement(1)
    assert any(isinstance(p, PendingMusterOut) for p in d.projection.pending_inputs)


def test_roll_2_in_first_term_allows_reenlist_or_muster():
    """Rolling 2 (not ≤ 1 prior term) after a failed advancement gives a choice to stay or leave."""
    from ceres.character.domain.career.career_events import PendingAssignmentChangeChoice

    d = _army_after_term_event()
    d.commission(attempt=False)
    d.advancement(2)  # 2 + DM+2 = 4 < 7 target → fail, but 2 > 1 prior term → no forced leave
    choices = [p for p in d.projection.pending_inputs if isinstance(p, PendingAssignmentChangeChoice)]
    assert choices and choices[0].muster_out is True


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


class TestPendingAdvancement:
    def test_event_from_form_parses_roll(self):
        pending = PendingAdvancement(pending_id=(1, 0), instruction='Roll 2D')
        event = pending.event_from_form({'roll': '9'})
        assert isinstance(event.handler, AdvancementHandler)
        assert event.handler.roll == 9

    def test_event_from_form_defaults_roll(self):
        pending = PendingAdvancement(pending_id=(1, 0), instruction='Roll 2D')
        event = pending.event_from_form({})
        assert isinstance(event.handler, AdvancementHandler)
        assert event.handler.roll == 2

    def test_input_specs_returns_roll_entry(self):
        specs = PendingAdvancement(pending_id=(1, 0), instruction='Roll').input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], NumberEntry) and specs[0].name == 'roll'


class TestPendingCommissionChoice:
    def test_event_from_form_attempt(self):
        pending = PendingCommissionChoice(pending_id=(1, 0), instruction='Commission?')
        event = pending.event_from_form({'choice': 'attempt', 'roll': '8'})
        assert isinstance(event.handler, CommissionHandler)
        assert event.handler.attempt is True
        assert event.handler.roll == 8

    def test_event_from_form_skip(self):
        pending = PendingCommissionChoice(pending_id=(1, 0), instruction='Commission?')
        event = pending.event_from_form({'choice': 'skip'})
        assert isinstance(event.handler, CommissionHandler)
        assert event.handler.attempt is False

    def test_event_from_form_defaults_to_skip(self):
        pending = PendingCommissionChoice(pending_id=(1, 0), instruction='Commission?')
        event = pending.event_from_form({})
        assert isinstance(event.handler, CommissionHandler)
        assert event.handler.attempt is False

    def test_input_specs_returns_select_and_roll(self):
        specs = PendingCommissionChoice(pending_id=(1, 0), instruction='Commission?').input_specs(_projection())
        assert any(isinstance(s, Select) and s.name == 'choice' for s in specs)
        assert any(isinstance(s, NumberEntry) and s.name == 'roll' for s in specs)


class TestPendingRankBonusChoice:
    def test_event_from_form_skill_choice(self):
        pending = PendingRankBonusChoice(pending_id=(1, 0), instruction='Rank bonus', level=1, options=[Admin()])
        skill_json = json.dumps({'kind': 'ADMIN'})
        event = pending.event_from_form({'skill': skill_json})
        assert isinstance(event.handler, SkillChoiceHandler)

    def test_event_from_form_advancement_dm_choice(self):
        opt = AdvancementDmOption()
        pending = PendingRankBonusChoice(pending_id=(1, 0), instruction='Rank bonus', level=1, options=[opt])
        event = pending.event_from_form({'skill': opt.model_dump_json()})
        assert isinstance(event.handler, AdvancementDmChoiceHandler)

    def test_input_specs_returns_select(self):
        pending = PendingRankBonusChoice(pending_id=(1, 0), instruction='Rank bonus', level=1, options=[Admin()])
        specs = pending.input_specs(_projection())
        assert any(isinstance(s, Select) and s.name == 'skill' for s in specs)


class TestRankBonusSkill:
    def test_single_field_skill(self):
        bonus = RankBonus(skill=Admin(), level=1)
        result = rank_bonus_skill(bonus)
        assert type(result) is Admin
        assert result.level.value == 1  # type: ignore[union-attr]

    def test_no_skill_raises(self):
        bonus = RankBonus(level=1)
        with pytest.raises(ReplayError):
            rank_bonus_skill(bonus)


class TestAdvancementPending:
    def test_no_assignment_raises(self):
        with pytest.raises(ReplayError, match='No current assignment'):
            advancement_pending(ARMY, None, event_id=1)

    def test_returns_pending_with_correct_id(self):
        assignment = ARMY.assignment('Support')
        pending = advancement_pending(ARMY, assignment, event_id=7, pending_idx=2)
        assert pending.pending_id == (7, 2)


class TestCareerProgressPending:
    def test_returns_commission_choice_when_eligible(self):
        # Scout (no commission system) should return advancement directly
        # Army with eligible character returns commission choice
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp(_UCP)
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Army', 'Support', roll=5)
        d.rank_bonus_choice(GunCombat())
        d.survive(5)
        d.term_event(5)
        # After term event, career_progress_pending queued a commission choice — confirm it
        proj = d.projection
        result = career_progress_pending(proj, ARMY, event_id=99)
        assert isinstance(result, PendingCommissionChoice)

    def test_returns_advancement_when_no_commission(self):
        # Scout has no commission — should return PendingAdvancement directly
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('786655')
        d.background_skills([Admin(), Medic()])
        d.career('Scout', 'Courier', roll=5)
        d.survive(5)
        d.term_event(5)
        proj = d.projection
        result = career_progress_pending(proj, SCOUT, event_id=99)
        assert isinstance(result, PendingAdvancement)
