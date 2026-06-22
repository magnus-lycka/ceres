"""Unit tests for career_data table entry objects."""

from types import SimpleNamespace

from ceres.character.domain.career import SCOUT
from ceres.character.domain.career.career_data import (
    AdvancementDmEntry,
    AutoAdvanceEntry,
    AutoQualifyCareerEntry,
    BenefitDmEntry,
    CareerEventEntry,
    CareerHandlerBase,
    CareerTableEntry,
    CareerTerm,
    CharacteristicLossChoiceEntry,
    CharacteristicLossEntry,
    CharacteristicLossesAndConnectionEntry,
    CharacteristicLossOutcome,
    DiceRoll,
    GainConnectionAndAdvancementDmEntry,
    GainConnectionAndBenefitDmEntry,
    GainConnectionAndParoleThresholdChangeEntry,
    GainConnectionAndSkillChoiceEntry,
    GainConnectionEntry,
    GainConnectionsAndSkillChoiceEntry,
    GainSkillAndConnectionEntry,
    GainSkillEntry,
    InjuryAndGainConnectionEntry,
    InjuryEntry,
    LifeEventEntry,
    LoseAllCareerBenefitsAndGainConnectionEntry,
    LoseAllCareerBenefitsEntry,
    MishapEntry,
    NoEffectEntry,
    ParoleThresholdChangeEntry,
    QualificationDmEntry,
    RolledConnectionOutcome,
    RolledConnectionsEntry,
    RolledConnectionsGroupEntry,
    RollMishapEntry,
    SkillChoiceEntry,
)
from ceres.character.domain.career.career_events import PendingMishap
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.connection_events import PendingConnectionsRoll
from ceres.character.domain.health.health_events import PendingCharacteristicChoice, PendingInjuryTable
from ceres.character.domain.life_events import PendingLifeEvent
from ceres.character.domain.skill_events import PendingSkillChoice
from ceres.character.domain.skills import Admin, Electronics, Level
from ceres.character.domain.sophont import VILANI
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


class _TestCareerHandler(CareerHandlerBase):
    type: str = 'test_handler'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.summary.narrative.append(f'handled {event_id}:{pending_idx}')
        return pending_idx + 1


# ── Career table entries ──────────────────────────────────────────────────────


def test_legacy_entry_types_share_table_entry_base():
    assert isinstance(CareerEventEntry(text='Event'), CareerTableEntry)
    assert isinstance(MishapEntry(text='Mishap'), CareerTableEntry)


def test_table_entries_can_carry_mishap_framing_flags():
    entry = GainConnectionEntry(text='Stay in career.', connection=ConnectionKind.RIVAL, stay_in_career=True)

    assert entry.stay_in_career is True
    assert entry.defer_ejection is False


def test_no_effect_entry_leaves_pending_index_unchanged():
    p = _projection()

    next_idx = NoEffectEntry(text='Nothing happens.').apply(p, event=SimpleNamespace(id=12), pending_idx=3)

    assert next_idx == 3
    assert p.pending_inputs == []


def test_skill_choice_entry_queues_choice_and_pauses_progression():
    p = _projection()

    next_idx = SkillChoiceEntry(text='Choose a skill.', options=[Admin(), Electronics()], level=1).apply(
        p, event=SimpleNamespace(id=12), pending_idx=0
    )

    pending = next(pending for pending in p.pending_inputs if isinstance(pending, PendingSkillChoice))
    assert next_idx == 1
    assert pending.pending_id == (12, 0)
    assert pending.options == [Admin(), Electronics()]
    assert pending.level == 1
    assert SkillChoiceEntry(text='Choose a skill.', options=[Admin()]).continues_career_progress() is False


def test_characteristic_loss_choice_entry_queues_choice():
    p = _projection()

    next_idx = CharacteristicLossChoiceEntry(
        text='Choose characteristic loss.',
        options=[Chars.STR, Chars.DEX],
        amount=2,
    ).apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    pending = p.pending_inputs[0]
    assert next_idx == 1
    assert isinstance(pending, PendingCharacteristicChoice)
    assert pending.pending_id == (12, 0)
    assert pending.options == [Chars.STR, Chars.DEX]
    assert pending.amount == 2


def test_injury_entry_queues_injury_table():
    p = _projection()

    next_idx = InjuryEntry(text='Injured.', severity='from_table').apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    assert next_idx == 1
    assert isinstance(p.pending_inputs[0], PendingInjuryTable)
    assert p.pending_inputs[0].pending_id == (12, 0)


def test_rolled_connections_entry_queues_roll_and_allows_progression():
    p = _projection()

    entry = RolledConnectionsEntry(
        text='Roll contacts.',
        connection=ConnectionKind.CONTACT,
        dice=DiceRoll.parse('d3'),
    )
    next_idx = entry.apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    pending = p.pending_inputs[0]
    assert next_idx == 1
    assert isinstance(pending, PendingConnectionsRoll)
    assert pending.pending_id == (12, 0)
    assert pending.connection_type == ConnectionKind.CONTACT
    assert pending.options == [1, 2, 3]
    assert entry.continues_career_progress() is True


def test_rolled_connections_group_entry_queues_multiple_rolls():
    p = _projection()

    next_idx = RolledConnectionsGroupEntry(
        text='Roll multiple connections.',
        rolls=[
            RolledConnectionOutcome(connection=ConnectionKind.CONTACT, dice=DiceRoll.parse('1d6')),
            RolledConnectionOutcome(connection=ConnectionKind.ENEMY, dice=DiceRoll.parse('d3')),
        ],
    ).apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    pendings = [pending for pending in p.pending_inputs if isinstance(pending, PendingConnectionsRoll)]
    assert next_idx == 2
    assert [pending.pending_id for pending in pendings] == [(12, 0), (12, 1)]
    assert [pending.connection_type for pending in pendings] == [
        ConnectionKind.CONTACT,
        ConnectionKind.ENEMY,
    ]


def test_roll_mishap_entry_queues_mishap_and_pauses_progression():
    p = _projection()

    entry = RollMishapEntry(text='Roll mishap.', leave=False)
    next_idx = entry.apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    pending = p.pending_inputs[0]
    assert next_idx == 1
    assert isinstance(pending, PendingMishap)
    assert pending.pending_id == (12, 0)
    assert pending.stay_in_career is True
    assert entry.continues_career_progress() is False


def test_life_event_entry_queues_life_event_and_pauses_progression():
    p = _projection()

    entry = LifeEventEntry(text='Life event.')
    next_idx = entry.apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    assert next_idx == 1
    assert isinstance(p.pending_inputs[0], PendingLifeEvent)
    assert p.pending_inputs[0].pending_id == (12, 0)
    assert entry.continues_career_progress() is False


def test_auto_advance_entry_applies_auto_advance_and_pauses_progression():
    p = _projection_with_career_term()

    entry = AutoAdvanceEntry(text='Auto advance.')
    next_idx = entry.apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    assert next_idx == 0
    assert p.summary.rank == 1
    assert entry.continues_career_progress() is False


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


def test_characteristic_losses_and_connection_entry_applies_all_outcomes():
    p = _projection()
    p.summary.characteristics[Chars.STR] = 8
    p.summary.characteristics[Chars.DEX] = 7

    CharacteristicLossesAndConnectionEntry(
        text='Gain an enemy and lose characteristics.',
        connection=ConnectionKind.ENEMY,
        losses=[
            CharacteristicLossOutcome(characteristic=Chars.STR, amount=1),
            CharacteristicLossOutcome(characteristic=Chars.DEX, amount=2),
        ],
    ).apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    assert p.summary.characteristics[Chars.STR] == 7
    assert p.summary.characteristics[Chars.DEX] == 5
    assert any(connection.kind == ConnectionKind.ENEMY.value for connection in p.summary.connections)


def test_gain_connection_and_advancement_dm_entry_applies_both_outcomes():
    p = _projection()

    GainConnectionAndAdvancementDmEntry(
        text='Gain an Ally and DM+2 to advancement.',
        connection=ConnectionKind.ALLY,
        amount=2,
    ).apply(p, event=None, pending_idx=0)

    assert any(c.kind == ConnectionKind.ALLY.value for c in p.summary.connections)
    assert p.pending_advancement_dm == 2


def test_gain_connection_and_benefit_dm_entry_applies_both_outcomes():
    p = _projection_with_career_term()

    GainConnectionAndBenefitDmEntry(
        text='Gain an Enemy and DM+2 to benefits.',
        connection=ConnectionKind.ENEMY,
        amount=2,
    ).apply(p, event=None, pending_idx=0)

    dms = p.summary.career_terms[-1].require_muster_out().benefit_roll_dms
    assert any(c.kind == ConnectionKind.ENEMY.value for c in p.summary.connections)
    assert [dm.amount for dm in dms] == [2]


def test_gain_connection_and_parole_threshold_change_entry_applies_both_outcomes():
    p = _projection()
    p.summary.parole_threshold = 5

    GainConnectionAndParoleThresholdChangeEntry(
        text='Gain an Enemy and increase parole threshold.',
        connection=ConnectionKind.ENEMY,
        amount=1,
    ).apply(p, event=None, pending_idx=0)

    assert any(c.kind == ConnectionKind.ENEMY.value for c in p.summary.connections)
    assert p.summary.parole_threshold == 6


def test_gain_connection_and_skill_choice_entry_queues_choice_without_immediate_progression():
    p = _projection()

    next_idx = GainConnectionAndSkillChoiceEntry(
        text='Gain an Ally and choose a skill.',
        connection=ConnectionKind.ALLY,
        options=[Admin(), Electronics()],
        level=1,
    ).apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    assert any(c.kind == ConnectionKind.ALLY.value for c in p.summary.connections)
    assert next_idx == 1
    assert (
        GainConnectionAndSkillChoiceEntry(
            text='Gain an Ally and choose a skill.',
            connection=ConnectionKind.ALLY,
            options=[Admin()],
        ).continues_career_progress()
        is False
    )
    pending = next(pending for pending in p.pending_inputs if isinstance(pending, PendingSkillChoice))
    assert isinstance(pending, PendingSkillChoice)
    assert pending.pending_id == (12, 0)
    assert pending.options == [Admin(), Electronics()]
    assert pending.level == 1


def test_gain_connections_and_skill_choice_entry_adds_connections_and_queues_choice():
    p = _projection()

    next_idx = GainConnectionsAndSkillChoiceEntry(
        text='Gain connections and choose a skill.',
        connections=[ConnectionKind.RIVAL, ConnectionKind.ALLY],
        options=[Admin()],
        level=1,
    ).apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    assert next_idx == 1
    assert [connection.kind for connection in p.summary.connections] == [
        ConnectionKind.RIVAL.value,
        ConnectionKind.ALLY.value,
    ]
    assert any(isinstance(pending, PendingSkillChoice) for pending in p.pending_inputs)
    assert (
        GainConnectionsAndSkillChoiceEntry(
            text='Gain connections and choose a skill.',
            connections=[ConnectionKind.RIVAL],
            options=[Admin()],
        ).continues_career_progress()
        is False
    )


def test_injury_and_gain_connection_entry_queues_injury_and_adds_connection():
    p = _projection()

    next_idx = InjuryAndGainConnectionEntry(
        text='Injured and gain a Rival.',
        severity='from_table',
        connection=ConnectionKind.RIVAL,
    ).apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    assert next_idx == 1
    assert any(c.kind == ConnectionKind.RIVAL.value for c in p.summary.connections)
    pending = next(pending for pending in p.pending_inputs if isinstance(pending, PendingInjuryTable))
    assert pending.pending_id == (12, 0)


def test_career_handler_base_is_a_table_entry():
    p = _projection()

    entry = _TestCareerHandler(text='Custom row.')
    next_idx = entry.apply(p, event=SimpleNamespace(id=12), pending_idx=0)

    assert isinstance(entry, CareerTableEntry)
    assert p.summary.narrative == ['handled 12:0']
    assert next_idx == 1
    assert entry.continues_career_progress() is False


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


def test_lose_all_career_benefits_and_gain_connection_entry_applies_both_outcomes():
    p = _projection_with_career_term()
    muster_out = p.summary.career_terms[-1].require_muster_out()

    LoseAllCareerBenefitsAndGainConnectionEntry(
        text='Lose benefits and gain a Rival.',
        connection=ConnectionKind.RIVAL,
    ).apply(p, event=None, pending_idx=0)

    assert muster_out.lost_rolls == 9999
    assert any(c.kind == ConnectionKind.RIVAL.value for c in p.summary.connections)
