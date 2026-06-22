"""Unit tests for career_data effect apply() methods.

Each effect class that has an apply() method is tested here in isolation.
Effects that only store data and are dispatched by career_events.py are NOT
tested here — those belong in test_events_pending_inputs.py.
"""

import pytest

from ceres.character.domain.career import SCOUT
from ceres.character.domain.career.career_data import (
    AdvancementDmEffect,
    AdvancementDmEntry,
    AutoQualifyCareerEffect,
    AutoQualifyCareerEntry,
    BenefitDmEffect,
    BenefitDmEntry,
    CareerEventEntry,
    CareerTableEntry,
    CareerTerm,
    CharacteristicLossEntry,
    DecreaseCharacteristicEffect,
    GainAllyEffect,
    GainConnectionEntry,
    GainContactEffect,
    GainEnemyEffect,
    GainRivalEffect,
    GainSkillAndConnectionEntry,
    GainSkillEffect,
    GainSkillEntry,
    LoseAllCareerBenefitsEffect,
    LoseAllCareerBenefitsEntry,
    MishapEntry,
    ParoleThresholdChangeEffect,
    ParoleThresholdChangeEntry,
    QualificationDmEffect,
    QualificationDmEntry,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.psionics import Psionics
from ceres.character.domain.skills import Admin, Electronics, Level
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.errors import ReplayError
from tests.character.helpers import MOCK_WORLD


def _projection() -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )


def _projection_with_career_term() -> CharacterProjection:
    p = _projection()
    p.summary.career_terms.append(CareerTerm(career=SCOUT, assignment=SCOUT.assignment('Courier')))
    return p


# ── Career table entries ──────────────────────────────────────────────────────


def test_legacy_entry_types_share_table_entry_base():
    assert isinstance(CareerEventEntry(text='Event'), CareerTableEntry)
    assert isinstance(MishapEntry(text='Mishap'), CareerTableEntry)


def test_table_entries_can_carry_mishap_framing_flags():
    entry = GainConnectionEntry(text='Stay in career.', connection=ConnectionKind.RIVAL, stay_in_career=True)

    assert entry.stay_in_career is True
    assert entry.defer_ejection is False


def test_gain_skill_entry_grants_skill_and_returns_pending_index():
    p = _projection()

    next_idx = GainSkillEntry(text='Gain Admin.', skill=Admin(level=Level(value=1))).apply(p, event=None, pending_idx=2)

    assert p.summary.skill_level(Admin) == 1
    assert next_idx == 2


def test_characteristic_loss_entry_decreases_characteristic():
    p = _projection()
    p.summary.characteristics[Chars.STR] = 7

    CharacteristicLossEntry(text='Lose STR.', characteristic=Chars.STR, amount=2).apply(p, event=None, pending_idx=0)

    assert p.summary.characteristics[Chars.STR] == 5


def test_gain_connection_entry_adds_connection_with_text_as_origin():
    p = _projection()

    GainConnectionEntry(text='You gain a Rival.', connection=ConnectionKind.RIVAL).apply(p, event=None, pending_idx=0)

    rival = next(c for c in p.summary.connections if c.kind == ConnectionKind.RIVAL.value)
    assert rival.origin == 'You gain a Rival.'


def test_gain_skill_and_connection_entry_applies_both_outcomes():
    p = _projection()

    GainSkillAndConnectionEntry(
        text='Gain an Enemy and Admin 1.',
        skill=Admin(level=Level(value=1)),
        connection=ConnectionKind.ENEMY,
    ).apply(p, event=None, pending_idx=0)

    assert p.summary.skill_level(Admin) == 1
    assert any(c.kind == ConnectionKind.ENEMY.value for c in p.summary.connections)


def test_advancement_dm_entry_adds_dm():
    p = _projection()

    AdvancementDmEntry(text='DM+2 to advancement.', amount=2).apply(p, event=None, pending_idx=0)

    assert p.pending_advancement_dm == 2


def test_qualification_dm_entry_adds_dm():
    p = _projection()

    QualificationDmEntry(text='DM+3 to qualification.', amount=3).apply(p, event=None, pending_idx=0)

    assert p.pending_qualification_dm == 3


def test_benefit_dm_entry_adds_benefit_dm():
    p = _projection_with_career_term()

    BenefitDmEntry(text='DM+1 to benefit.', amount=1).apply(p, event=None, pending_idx=0)

    dms = p.summary.career_terms[-1].require_muster_out().benefit_roll_dms
    assert len(dms) == 1
    assert dms[0].amount == 1


def test_parole_threshold_change_entry_adjusts_parole_threshold():
    p = _projection()
    p.summary.parole_threshold = 5

    ParoleThresholdChangeEntry(text='Parole threshold increases.', amount=2).apply(p, event=None, pending_idx=0)

    assert p.summary.parole_threshold == 7


def test_auto_qualify_career_entry_marks_career_for_auto_qualification():
    p = _projection()

    AutoQualifyCareerEntry(text='Auto qualify for Scout.', career=type(SCOUT)).apply(p, event=None, pending_idx=0)

    assert type(SCOUT) in p.auto_qualify_careers


def test_lose_all_career_benefits_entry_forfeits_benefits():
    p = _projection_with_career_term()
    muster_out = p.summary.career_terms[-1].require_muster_out()

    LoseAllCareerBenefitsEntry(text='Lose all benefits.').apply(p, event=None, pending_idx=0)

    assert muster_out.lost_rolls == 9999


# ── GainSkillEffect ───────────────────────────────────────────────────────────


def test_gain_skill_effect_grants_skill():
    p = _projection()
    GainSkillEffect(skill=Admin()).apply(p)
    assert p.summary.skill_level(Admin) == 0


def test_gain_skill_effect_with_explicit_level_grants_that_level():
    p = _projection()
    GainSkillEffect(skill=Admin(level=Level(value=1))).apply(p)
    assert p.summary.skill_level(Admin) == 1


def test_gain_skill_effect_does_not_downgrade_existing_higher_level():
    p = _projection()
    GainSkillEffect(skill=Admin(level=Level(value=2))).apply(p)
    GainSkillEffect(skill=Admin(level=Level(value=1))).apply(p)
    assert p.summary.skill_level(Admin) == 2


def test_gain_skill_effect_grants_different_skills_independently():
    p = _projection()
    GainSkillEffect(skill=Admin()).apply(p)
    GainSkillEffect(skill=Electronics(comms=Level(value=1))).apply(p)
    assert p.summary.skill_level(Admin) == 0
    assert p.summary.skill_level(Electronics) == 1


# ── DecreaseCharacteristicEffect ──────────────────────────────────────────────


def test_decrease_characteristic_reduces_by_amount():
    p = _projection()
    p.summary.characteristics[Chars.STR] = 7
    DecreaseCharacteristicEffect(characteristic=Chars.STR, amount=3).apply(p)
    assert p.summary.characteristics[Chars.STR] == 4


def test_decrease_characteristic_floors_at_zero():
    p = _projection()
    p.summary.characteristics[Chars.STR] = 1
    DecreaseCharacteristicEffect(characteristic=Chars.STR, amount=5).apply(p)
    assert p.summary.characteristics[Chars.STR] == 0


def test_decrease_characteristic_default_amount_is_one():
    p = _projection()
    p.summary.characteristics[Chars.END] = 6
    DecreaseCharacteristicEffect(characteristic=Chars.END).apply(p)
    assert p.summary.characteristics[Chars.END] == 5


def test_decrease_psi_to_zero_removes_psi_entry():
    p = _projection()
    p.summary.characteristics[Chars.PSI] = 1
    DecreaseCharacteristicEffect(characteristic=Chars.PSI, amount=1).apply(p)
    assert Chars.PSI not in p.summary.characteristics


def test_decrease_psi_to_zero_clears_psionics():
    p = _projection()
    p.summary.characteristics[Chars.PSI] = 1
    p.summary.psionics = Psionics()
    DecreaseCharacteristicEffect(characteristic=Chars.PSI, amount=1).apply(p)
    assert p.summary.psionics is None


def test_decrease_psi_not_to_zero_keeps_psi_entry():
    p = _projection()
    p.summary.characteristics[Chars.PSI] = 3
    DecreaseCharacteristicEffect(characteristic=Chars.PSI, amount=1).apply(p)
    assert p.summary.characteristics[Chars.PSI] == 2


# ── GainContactEffect / GainAllyEffect / GainRivalEffect / GainEnemyEffect ───


def test_gain_contact_adds_contact():
    p = _projection()
    GainContactEffect().apply(p)
    assert any(c.kind == 'connection_contact' for c in p.summary.connections)


def test_gain_ally_adds_ally():
    p = _projection()
    GainAllyEffect().apply(p)
    assert any(c.kind == 'connection_ally' for c in p.summary.connections)


def test_gain_rival_adds_rival():
    p = _projection()
    GainRivalEffect().apply(p)
    assert any(c.kind == 'connection_rival' for c in p.summary.connections)


def test_gain_enemy_adds_enemy():
    p = _projection()
    GainEnemyEffect().apply(p)
    assert any(c.kind == 'connection_enemy' for c in p.summary.connections)


def test_gain_connection_effects_can_stack():
    p = _projection()
    GainContactEffect().apply(p)
    GainContactEffect().apply(p)
    assert len([c for c in p.summary.connections if c.kind == 'connection_contact']) == 2


# ── AdvancementDmEffect ───────────────────────────────────────────────────────


def test_advancement_dm_effect_increments_pending_dm():
    p = _projection()
    AdvancementDmEffect(amount=2).apply(p)
    assert p.pending_advancement_dm == 2


def test_advancement_dm_effect_accumulates():
    p = _projection()
    AdvancementDmEffect(amount=2).apply(p)
    AdvancementDmEffect(amount=1).apply(p)
    assert p.pending_advancement_dm == 3


# ── QualificationDmEffect ─────────────────────────────────────────────────────


def test_qualification_dm_effect_increments_pending_dm():
    p = _projection()

    QualificationDmEffect(amount=3).apply(p)
    assert p.pending_qualification_dm == 3


# ── BenefitDmEffect ───────────────────────────────────────────────────────────


def test_benefit_dm_effect_adds_to_last_career_terms_muster_out():
    p = _projection_with_career_term()
    BenefitDmEffect(amount=1).apply(p)
    dms = p.summary.career_terms[-1].require_muster_out().benefit_roll_dms
    assert len(dms) == 1
    assert dms[0].amount == 1


def test_benefit_dm_effect_does_nothing_without_career_term():
    p = _projection()
    BenefitDmEffect(amount=1).apply(p)  # must not raise
    assert p.summary.career_terms == []


# ── ParoleThresholdChangeEffect ───────────────────────────────────────────────


def test_parole_threshold_change_increases():
    p = _projection()
    p.summary.parole_threshold = 5
    ParoleThresholdChangeEffect(amount=3).apply(p)
    assert p.summary.parole_threshold == 8


def test_parole_threshold_change_decreases():
    p = _projection()
    p.summary.parole_threshold = 5
    ParoleThresholdChangeEffect(amount=-3).apply(p)
    assert p.summary.parole_threshold == 2


def test_parole_threshold_change_clamped_to_zero():
    p = _projection()
    p.summary.parole_threshold = 2
    ParoleThresholdChangeEffect(amount=-10).apply(p)
    assert p.summary.parole_threshold == 0


def test_parole_threshold_change_clamped_to_twelve():
    p = _projection()
    p.summary.parole_threshold = 11
    ParoleThresholdChangeEffect(amount=5).apply(p)
    assert p.summary.parole_threshold == 12


def test_parole_threshold_change_does_nothing_when_none():
    p = _projection()
    assert p.summary.parole_threshold is None
    ParoleThresholdChangeEffect(amount=3).apply(p)  # must not raise
    assert p.summary.parole_threshold is None


# ── AutoQualifyCareerEffect ───────────────────────────────────────────────────


def test_auto_qualify_career_effect_adds_career():
    p = _projection()
    AutoQualifyCareerEffect(career=SCOUT.__class__).apply(p)
    assert SCOUT.__class__ in p.auto_qualify_careers


def test_auto_qualify_career_effect_does_not_duplicate():
    p = _projection()
    AutoQualifyCareerEffect(career=SCOUT.__class__).apply(p)
    AutoQualifyCareerEffect(career=SCOUT.__class__).apply(p)
    assert p.auto_qualify_careers.count(SCOUT.__class__) == 1


# ── LoseAllCareerBenefitsEffect ───────────────────────────────────────────────


def test_lose_all_career_benefits_forfeits_muster_rolls():
    p = _projection_with_career_term()
    muster_out = p.summary.career_terms[-1].require_muster_out()
    LoseAllCareerBenefitsEffect().apply(p)
    assert muster_out.lost_rolls == 9999


def test_lose_all_career_benefits_raises_without_active_career():
    p = _projection()
    with pytest.raises(ReplayError, match='No active career'):
        LoseAllCareerBenefitsEffect().apply(p)
