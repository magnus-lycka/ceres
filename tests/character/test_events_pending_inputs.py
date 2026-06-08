from typing import Any, cast

import pytest

from ceres.character.domain import skills as character_skills
from ceres.character.domain.benefits import SHIP_SHARE, WEAPON
from ceres.character.domain.career import ARMY, PRISONER, SCOUT
from ceres.character.domain.career.career_data import (
    AdvancementDmEffect,
    AdvancementDmOption,
    AssignmentData,
    BenefitDmEffect,
    CareerTerm,
    CharCheck,
    DecreaseCharacteristicEffect,
    GainAllyEffect,
    GainContactEffect,
    GainEnemyEffect,
    GainRivalEffect,
    GainSkillEffect,
    ParoleThresholdChangeEffect,
    RankBonus,
    RankEntry,
    SkillTableOption,
)
from ceres.character.domain.career.career_events import (
    AdvancementDmChoiceHandler,
    AdvancementHandler,
    AssignmentChangeChoiceHandler,
    BenefitChoiceHandler,
    CareerChoiceHandler,
    CareerEntryHandler,
    CharacteristicChoiceHandler,
    CommissionHandler,
    ConnectionKindChoiceHandler,
    ConnectionsRollHandler,
    DraftAssignmentHandler,
    DraftHandler,
    LifeEventCrimeLoseBenefitRoll,
    LifeEventCrimeTakePrisoner,
    LifeEventHandler,
    LifeEventUnusualHandler,
    MishapHandler,
    MusterOutHandler,
    ParoleRollHandler,
    PendingAdvancement,
    PendingAssignmentChangeChoice,
    PendingBenefitChoice,
    PendingCareerChoice,
    PendingChoices,
    PendingCommissionChoice,
    PendingConnectionsRoll,
    PendingDraftAssignmentChoice,
    PendingDraftChoice,
    PendingInitialTrainingChoice,
    PendingLifeEvent,
    PendingLifeEventChoice,
    PendingLifeEventUnusual,
    PendingMishap,
    PendingMusterOut,
    PendingParoleRoll,
    PendingRankBonusChoice,
    PendingReenlist,
    PendingSkillChoice,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingSurvive,
    PendingSwitchAssignment,
    PendingTermEvent,
    ReenlistHandler,
    SkillChoiceHandler,
    SkillRollHandler,
    SkillTableHandler,
    SurviveHandler,
    SwitchAssignmentHandler,
    TermEventHandler,
    _advancement_pending,
    _apply_auto_advance,
    _apply_mishap_ejection,
    _apply_prisoner_advancement,
    _apply_skill_table_entry,
    _start_new_career_term,
    _survive_pending,
    career_progress_pending,
    muster_out_setup,
    queue_reenlist_or_aging,
)
from ceres.character.domain.career.loader import load_careers
from ceres.character.domain.character_start import (
    BackgroundSkillsHandler,
    FinishCreationHandler,
    PendingBackgroundSkills,
    UcpHandler,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.health.health_events import (
    AgingCrisisHandler,
    AgingRollHandler,
    DoubleInjuryTableHandler,
    InjuryTableHandler,
    PendingAgingChoice,
    PendingAgingChoiceMental,
    PendingAgingCrisis,
    PendingAgingRoll,
    PendingCharacteristicChoice,
    PendingDoubleInjuryRoll,
    PendingInjuryTable,
    PendingNearlyKilled,
    PendingSeverelyInjured,
    complete_aging,
)
from ceres.character.domain.precareer.precareer_events import (
    PendingPreCareerEvent,
    PendingPreCareerGraduation,
    PendingPreCareerSkillChoice,
    PreCareerEntryHandler,
    PreCareerEventHandler,
    PreCareerGraduationHandler,
    PreCareerSkillChoiceHandler,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import CareerChoice, NumberEntry, Reference, Select
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from tests.character.helpers import MOCK_WORLD


class Form(dict[str, str]):
    def getlist(self, key: str) -> list[str]:
        value = self.get(key, '')
        return [] if value == '' else value.split('|')


def _projection(**summary_kwargs: Any) -> CharacterProjection:
    term_count = summary_kwargs.pop('term_count', None)
    current_assignment = summary_kwargs.get('current_assignment')
    if isinstance(current_assignment, str):
        current_career = summary_kwargs.get('current_career') or SCOUT
        summary_kwargs['current_assignment'] = current_career.assignment(current_assignment)
    if term_count is not None and 'career_terms' not in summary_kwargs:
        current_career = summary_kwargs.get('current_career') or SCOUT
        assignment_obj = summary_kwargs.get('current_assignment') or current_career.assignment('Courier')
        assert assignment_obj is not None
        summary_kwargs['career_terms'] = [
            CareerTerm(career=current_career, assignment=assignment_obj) for _ in range(term_count)
        ]
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **summary_kwargs),
    )


class FakeCareer:
    name = 'Fake'

    def __init__(self, rank_bonus: RankBonus | None = None):
        self.rank_bonus = rank_bonus
        self.started_term = False

    def update_current_term_rank(self, projection: CharacterProjection) -> None:
        if projection.summary.career_terms:
            projection.summary.career_terms[-1].rank_after_term = projection.summary.rank or 0

    def current_ranks(self, projection: CharacterProjection) -> dict[int, RankEntry]:
        if self.rank_bonus is None:
            return {}
        return {1: RankEntry(rank=1, bonus=self.rank_bonus)}

    def available_tables(self, edu: int, assignment) -> list:
        from ceres.character.domain.career.career_data import SkillTableOption

        return [SkillTableOption(label='Service Skills', key='service_skills')]

    def assignment_by_index(self, index: int):
        return None

    def start_new_term(self, projection: CharacterProjection, assignment, event_id: int) -> None:
        self.started_term = True


class FakePrisonerCareer(FakeCareer):
    name = 'Prisoner'

    def __init__(self, rank_bonus: RankBonus | None = None):
        super().__init__(rank_bonus)
        self.assignment = AssignmentData(
            name='Inmate',
            description='',
            survival=CharCheck(characteristic=Chars.END, target=5),
            advancement=CharCheck(characteristic=Chars.INT, target=8),
        )

    def assignment_by_index(self, index: int):
        return self.assignment if index == 1 else None


def test_ucp_event_rejects_wrong_length():
    with pytest.raises(ReplayError, match='expected 6 hex digits'):
        Event(handler=UcpHandler(ucp='77777')).apply(_projection())


def test_effect_apply_methods_and_skill_entries():
    projection = _projection(characteristics={Chars.STR: 1, Chars.SOC: 7}, term_count=1)

    DecreaseCharacteristicEffect(characteristic=Chars.STR, amount=3).apply(projection)
    GainContactEffect().apply(projection, source='contact source')
    GainAllyEffect().apply(projection, source='ally source')
    GainRivalEffect().apply(projection, source='rival source')
    GainEnemyEffect().apply(projection, source='enemy source')
    GainSkillEffect(skill=character_skills.Admin()).apply(projection)
    AdvancementDmEffect(amount=2).apply(projection, source_event_id=10)
    BenefitDmEffect(amount=1).apply(projection, source_event_id=11)
    projection.summary.parole_threshold = 11
    ParoleThresholdChangeEffect(amount=5).apply(projection)
    ParoleThresholdChangeEffect(amount=-20).apply(projection)
    _apply_skill_table_entry(projection, character_skills.Electronics(comms=character_skills.Level(value=1)))

    assert projection.summary.characteristics[Chars.STR] == 0
    assert [connection.kind for connection in projection.summary.connections] == [
        'connection_contact',
        'connection_ally',
        'connection_rival',
        'connection_enemy',
    ]
    assert projection.summary.parole_threshold == 0
    assert projection.summary.skill_level(character_skills.Admin) == 0
    assert projection.summary.skill_level(character_skills.Electronics) == 1
    assert projection.pending_advancement_dm == 2
    assert projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms[0].amount == 1


def test_auto_advance_can_apply_characteristic_rank_bonus():
    projection = _projection(characteristics={Chars.SOC: 7})
    career = FakeCareer(RankBonus(characteristic=Chars.SOC, level=2))

    _apply_auto_advance(projection, career, 5)

    assert projection.summary.rank == 1
    assert projection.summary.characteristics[Chars.SOC] == 9
    assert any(isinstance(pending, PendingSkillTable) for pending in projection.pending_inputs)
    assert any(isinstance(pending, PendingReenlist) for pending in projection.pending_inputs)


def test_assignment_helper_errors_are_reported():
    projection = _projection()  # current_assignment=None
    career = FakeCareer()

    with pytest.raises(ReplayError, match='No current assignment'):
        _start_new_career_term(projection, career, 1)
    with pytest.raises(ReplayError, match='No current assignment'):
        _survive_pending(career, None, 1)
    with pytest.raises(ReplayError, match='No current assignment'):
        _advancement_pending(career, None, 1)


def test_mishap_ejection_queues_aging_for_older_character():
    projection = _projection(age=30, current_career=SCOUT, current_assignment='Courier')
    career = load_careers()['Scout']

    next_idx = _apply_mishap_ejection(projection, career, source_event_id=7, pending_idx=2)

    assert next_idx == 3
    assert projection.summary.age == 34
    assert projection.muster_out_career is not None
    assert projection.muster_out_career.name == 'Scout'
    assert projection.summary.current_career is None
    assert any(isinstance(pending, PendingAgingRoll) and pending.id == '7.2' for pending in projection.pending_inputs)


def test_basic_event_error_branches():
    from pydantic import ValidationError

    projection = _projection(drafted=True)
    with pytest.raises(ReplayError, match='may only enter the draft once'):
        Event(handler=DraftHandler(career=ARMY)).apply(projection)

    with pytest.raises((ValidationError, Exception)):
        DraftHandler(career='Nope')  # ty: ignore[invalid-argument-type]
    with pytest.raises((ValidationError, Exception)):
        DraftAssignmentHandler(career='Nope', assignment='Infantry')  # ty: ignore[invalid-argument-type]

    no_assignment = _projection(current_career=SCOUT)
    with pytest.raises(ReplayError, match='No current assignment'):
        PendingSurvive(pending_id=(1, 0), instruction='Survive').resolve(
            no_assignment, Event(handler=SurviveHandler(roll=8))
        )

    with pytest.raises(ReplayError, match='Injury table roll must be 1-6'):
        Event(handler=InjuryTableHandler(roll=0)).apply(_projection())
    with pytest.raises(ReplayError, match='Double injury roll must be 1-6'):
        Event(handler=DoubleInjuryTableHandler(roll1=1, roll2=7)).apply(_projection())


def test_muster_out_and_benefit_choice_error_branches():
    with pytest.raises(ReplayError, match='No muster out career set'):
        Event(handler=MusterOutHandler(table='cash', roll=1)).apply(_projection())

    with pytest.raises(ReplayError, match='must fulfill a PendingBenefitChoice'):
        Event(handler=BenefitChoiceHandler(choice_index=0)).apply(_projection())

    pending = PendingBenefitChoice(
        pending_id=(1, 0),
        instruction='Benefit',
        benefit_options=[SHIP_SHARE],
    )
    with pytest.raises(ReplayError, match='choice_index 2 out of range'):
        Event(handler=BenefitChoiceHandler(choice_index=2)).apply(_projection(), pending)


def test_aging_roll_extreme_results():
    effective_minus_4 = _projection(term_count=6, characteristics={Chars.STR: 7, Chars.DEX: 7, Chars.END: 7})
    Event(id=1, handler=AgingRollHandler(roll=2)).apply(effective_minus_4)
    minus_4_choices = [p for p in effective_minus_4.pending_inputs if isinstance(p, PendingAgingChoice)]
    assert [p.instruction for p in minus_4_choices] == [
        'Aging: choose STR, DEX, or END to reduce by 2',
        'Aging: choose STR, DEX, or END to reduce by 2',
        'Aging: choose STR, DEX, or END to reduce by 1',
    ]

    effective_minus_5 = _projection(term_count=7, characteristics={Chars.STR: 7, Chars.DEX: 7, Chars.END: 7})
    Event(id=2, handler=AgingRollHandler(roll=2)).apply(effective_minus_5)
    assert {char: effective_minus_5.summary.characteristics[char] for char in (Chars.STR, Chars.DEX, Chars.END)} == {
        Chars.STR: 5,
        Chars.DEX: 5,
        Chars.END: 5,
    }
    assert any(isinstance(p, PendingReenlist) for p in effective_minus_5.pending_inputs)

    effective_minus_6 = _projection(
        term_count=8,
        characteristics={Chars.STR: 7, Chars.DEX: 7, Chars.END: 7, Chars.INT: 7, Chars.SOC: 7},
    )
    Event(id=3, handler=AgingRollHandler(roll=2)).apply(effective_minus_6)
    assert any(isinstance(p, PendingAgingChoiceMental) for p in effective_minus_6.pending_inputs)


def test_commission_event_skip_failure_success_and_unsupported_career():
    scout = _projection(current_career=SCOUT, current_assignment='Courier')
    with pytest.raises(ReplayError, match='Scout does not support commission'):
        Event(handler=CommissionHandler(attempt=True, roll=12)).apply(scout)

    skipped = _projection(current_career=ARMY, current_assignment='Support')
    Event(id=1, handler=CommissionHandler(attempt=False)).apply(skipped)
    assert any(isinstance(p, PendingAdvancement) and p.id == '1.0' for p in skipped.pending_inputs)

    failed = _projection(
        current_career=ARMY,
        current_assignment='Support',
        characteristics={Chars.SOC: 2},
    )
    failed.pending_advancement_dm = 1
    Event(id=2, handler=CommissionHandler(attempt=True, roll=2)).apply(failed)
    assert failed.pending_advancement_dm == 0
    assert any(isinstance(p, PendingAdvancement) and p.id == '2.0' for p in failed.pending_inputs)

    succeeded = _projection(
        current_career=ARMY,
        current_assignment='Support',
        characteristics={Chars.SOC: 12, Chars.EDU: 10},
        career_terms=[CareerTerm(career=ARMY, assignment=ARMY.assignment('Support'))],
    )
    Event(id=3, handler=CommissionHandler(attempt=True, roll=12)).apply(succeeded)
    assert succeeded.summary.rank == 1
    assert succeeded.summary.career_terms[-1].commission is True
    assert succeeded.summary.skill_level(character_skills.Leadership) == 1
    assert any(isinstance(p, PendingSkillTable) and p.id == '3.0' for p in succeeded.pending_inputs)


def test_precareer_entry_error_and_failure_branches():
    with pytest.raises(ReplayError, match="Unknown pre-career: 'Nope'"):
        Event(handler=PreCareerEntryHandler(precareer='Nope', roll=7)).apply(_projection())
    with pytest.raises(ReplayError, match='only available in terms'):
        Event(handler=PreCareerEntryHandler(precareer='University', roll=7)).apply(_projection(term_count=3))
    with pytest.raises(ReplayError, match='may only attend one pre-career'):
        Event(handler=PreCareerEntryHandler(precareer='University', roll=7)).apply(
            _projection(precareer_completed='University')
        )

    failed = _projection(characteristics={Chars.EDU: 0})
    Event(id=4, handler=PreCareerEntryHandler(precareer='University', roll=2)).apply(failed)
    assert any(isinstance(p, PendingCareerChoice) for p in failed.pending_inputs)
    assert failed.summary.precareer is None

    soc_bonus = _projection(characteristics={Chars.INT: 12, Chars.SOC: 12})
    Event(id=5, handler=PreCareerEntryHandler(precareer='Merchant Academy (Business)', roll=7)).apply(soc_bonus)
    assert soc_bonus.summary.precareer == 'Merchant Academy (Business)'
    assert any(isinstance(p, PendingPreCareerEvent) for p in soc_bonus.pending_inputs)


@pytest.mark.parametrize(
    ('roll', 'pending_type'),
    [
        (6, PendingConnectionsRoll),
        (7, PendingLifeEvent),
        (9, PendingSkillChoice),
    ],
)
def test_precareer_event_effects_create_expected_pending_inputs(roll, pending_type):
    projection = _projection(precareer='University')
    Event(id=roll, handler=PreCareerEventHandler(roll=roll)).apply(projection)
    assert any(isinstance(p, pending_type) for p in projection.pending_inputs)


def test_precareer_event_error_manual_note_and_ending_branches():
    with pytest.raises(ReplayError, match='No active pre-career'):
        Event(handler=PreCareerEventHandler(roll=7)).apply(_projection())
    with pytest.raises(ReplayError, match="Unknown pre-career: 'Nope'"):
        Event(handler=PreCareerEventHandler(roll=7)).apply(_projection(precareer='Nope'))
    with pytest.raises(ReplayError, match='No pre-career event entry for roll 13'):
        Event(handler=PreCareerEventHandler(roll=13)).apply(_projection(precareer='University'))

    for roll, problem_text in ((2, 'attempt to enter the Psion career'), (4, 'Prisoner career next term')):
        projection = _projection(precareer='University')
        Event(id=roll, handler=PreCareerEventHandler(roll=roll)).apply(projection)
        assert any(problem_text in problem for problem in projection.summary.problems)

    ended = _projection(precareer='University')
    ended.pending_inputs.append(PendingPreCareerGraduation(pending_id=(11, 0), instruction='Graduation'))
    Event(id=11, handler=PreCareerEventHandler(roll=11)).apply(ended)
    assert ended.summary.precareer is None
    assert ended.summary.precareer_completed == 'University'
    assert not any(isinstance(p, PendingPreCareerGraduation) for p in ended.pending_inputs)
    assert any(isinstance(p, PendingCareerChoice) for p in ended.pending_inputs)

    recognised = _projection(precareer='University', characteristics={Chars.SOC: 7})
    Event(id=12, handler=PreCareerEventHandler(roll=12)).apply(recognised)
    assert recognised.summary.characteristics[Chars.SOC] == 8


def test_precareer_graduation_error_and_failure_branches():
    with pytest.raises(ReplayError, match='No active pre-career for graduation'):
        Event(handler=PreCareerGraduationHandler(roll=7)).apply(_projection())
    with pytest.raises(ReplayError, match="Unknown pre-career: 'Nope'"):
        Event(handler=PreCareerGraduationHandler(roll=7)).apply(_projection(precareer='Nope'))

    failed = _projection(precareer='University', characteristics={Chars.INT: 2})
    Event(id=1, handler=PreCareerGraduationHandler(roll=2)).apply(failed)
    assert failed.summary.precareer is None
    assert failed.summary.precareer_completed == 'University'
    assert failed.summary.precareer_skills == []
    assert any('Did not graduate from University.' in line for line in failed.summary.narrative)
    assert any(isinstance(p, PendingCareerChoice) for p in failed.pending_inputs)


def test_prisoner_advancement_special_cases():
    missing_assignment = _projection()
    with pytest.raises(ReplayError, match='No current assignment'):
        _apply_prisoner_advancement(
            missing_assignment, Event(id=1, handler=AdvancementHandler(roll=12)), FakePrisonerCareer()
        )

    choice_bonus = _projection(
        current_career=PRISONER,
        current_assignment='Inmate',
        characteristics={Chars.INT: 12, Chars.EDU: 10},
        parole_threshold=6,
    )
    choice_bonus.pending_advancement_dm = 1
    _apply_prisoner_advancement(
        choice_bonus,
        Event(id=2, handler=AdvancementHandler(roll=12)),
        FakePrisonerCareer(RankBonus(choices=[character_skills.Admin()], level=1)),
    )
    assert choice_bonus.pending_advancement_dm == 0
    assert choice_bonus.prisoner_freed is True
    assert any(
        isinstance(p, PendingRankBonusChoice) and p.options == [character_skills.Admin()]
        for p in choice_bonus.pending_inputs
    )

    characteristic_bonus = _projection(
        current_career=PRISONER,
        current_assignment='Inmate',
        characteristics={Chars.INT: 12, Chars.SOC: 7, Chars.EDU: 10},
        parole_threshold=20,
    )
    _apply_prisoner_advancement(
        characteristic_bonus,
        Event(id=3, handler=AdvancementHandler(roll=12)),
        FakePrisonerCareer(RankBonus(characteristic=Chars.SOC, level=2)),
    )
    assert characteristic_bonus.summary.characteristics[Chars.SOC] == 9
    assert any(isinstance(p, PendingSkillTable) for p in characteristic_bonus.pending_inputs)


def test_queue_reenlist_or_aging_handles_freed_prisoner_paths():
    older = _projection(
        age=30,
        current_career=PRISONER,
        current_assignment='Inmate',
    )
    older.prisoner_freed = True
    queue_reenlist_or_aging(older, event_id=4, idx=0)
    assert older.prisoner_freed is False
    assert older.pending_reenlist is False
    assert older.muster_out_career is not None
    assert older.muster_out_career.name == 'Prisoner'
    assert any(isinstance(p, PendingAgingRoll) for p in older.pending_inputs)

    younger = _projection(
        age=22,
        current_career=PRISONER,
        current_assignment='Inmate',
        term_count=1,
    )
    younger.prisoner_freed = True
    queue_reenlist_or_aging(younger, event_id=5, idx=1)
    assert younger.prisoner_freed is False
    assert younger.muster_out_career is not None
    assert younger.muster_out_career.name == 'Prisoner'
    assert any(isinstance(p, PendingMusterOut) for p in younger.pending_inputs)


def test_muster_out_setup_and_complete_aging_helper_branches():
    career = load_careers()['Scout']
    projection = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        term_count=1,
        rank=2,
    )
    projection.summary.career_terms[-1].require_muster_out().lost_rolls = 1
    projection.summary.career_terms[-1].require_muster_out().extra_rolls = 2

    next_idx = muster_out_setup(projection, career, source_event_id=6, pending_idx=0)

    assert next_idx == 1
    assert projection.summary.current_career is None
    assert len([p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]) == 1
    assert projection.summary.career_terms[-1].require_muster_out().rolls_remaining == 3

    assignment_change = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
    )
    complete_aging(assignment_change, source_event_id=7)
    pending = next(p for p in assignment_change.pending_inputs if isinstance(p, PendingAssignmentChangeChoice))
    assert pending.muster_out is True


def test_career_progress_pending_reports_invalid_career_shape():
    class BadCommissionCareer(FakeCareer):
        commission = None

        def can_attempt_commission(self, projection: CharacterProjection) -> bool:
            return True

    with pytest.raises(ReplayError, match='can attempt commission without commission rules'):
        career_progress_pending(_projection(), cast(Any, BadCommissionCareer()), event_id=1)


def test_pending_background_skills_builds_form_and_specs():
    pending = PendingBackgroundSkills(
        pending_id=(2, 0),
        instruction='Choose 2 background skills',
        options=[character_skills.Admin(), character_skills.Medic()],
    )
    admin_json = character_skills.Admin().model_dump_json()
    medic_json = character_skills.Medic().model_dump_json()
    form = Form(skill=f'{admin_json}|{medic_json}')

    form_event = pending.event_from_form(form)
    specs = pending.input_specs(_projection())

    assert isinstance(form_event.handler, BackgroundSkillsHandler)
    assert [skill.name() for skill in form_event.skills] == ['Admin', 'Medic']
    assert isinstance(specs[0], Select)
    assert specs[0].min_select == 2
    assert specs[0].max_select == 2
    assert [label for label, _value in specs[0].options] == ['Admin', 'Medic']


def test_pending_career_choice_form_and_specs():
    projection = _projection(term_count=4)
    pending = PendingCareerChoice(pending_id=(3, 0), instruction='Choose career', options=[load_careers()['Scout']])

    assert isinstance(pending.event_from_form(Form(kind='finish_creation')).handler, FinishCreationHandler)

    pre_career = pending.event_from_form(Form(kind='precareer_entry', precareer='University', roll='9'))
    assert isinstance(pre_career.handler, PreCareerEntryHandler)
    assert pre_career.precareer == 'University'
    assert pre_career.roll == 9

    career = pending.event_from_form(Form(career='Scout', assignment='Courier', roll='12'))
    assert isinstance(career.handler, CareerEntryHandler)
    assert career.career.name == 'Scout'
    assert career.assignment.name == 'Courier'
    assert career.qualification_roll == 12

    specs = pending.input_specs(projection)
    assert len(specs) == 1
    spec = specs[0]
    assert isinstance(spec, CareerChoice)
    assert spec.career_options[0].name == 'Scout'
    assert spec.career_options[0].description.startswith('Members of the exploratory service.')
    assert spec.career_options[0].qualification.characteristic == 'INT'
    assert spec.career_options[0].qualification.target == 5
    assert spec.career_options[0].assignments[0].name == 'Courier'
    assert spec.career_options[0].assignments[0].description.startswith('You are responsible for shuttling messages')


def test_pending_draft_choices_build_expected_events_and_specs():
    draft = PendingDraftChoice(pending_id=(3, 0), instruction='Draft or drift')
    draft_event = draft.event_from_form(Form(choice='draft', roll='2'))
    drifter_event = draft.event_from_form(Form(choice='drifter', assignment='Scavenger'))

    assert isinstance(draft_event.handler, DraftHandler)
    assert draft_event.career.name == 'Army'
    assert isinstance(drifter_event.handler, CareerEntryHandler)
    assert drifter_event.career.name == 'Drifter'
    assert drifter_event.assignment.name == 'Scavenger'
    assert draft.input_specs(_projection()) == []

    assignment = PendingDraftAssignmentChoice(
        pending_id=(4, 0), instruction='Assignment', career=load_careers()['Army']
    )
    form_event = assignment.event_from_form(Form(assignment='Support'))
    specs = assignment.input_specs(_projection())

    assert isinstance(form_event.handler, DraftAssignmentHandler)
    assert form_event.career.name == 'Army'
    assert form_event.assignment.name == 'Support'
    assert isinstance(specs[0], Reference)
    assert specs[0].value == 'Army'
    assert isinstance(specs[1], Select)


@pytest.mark.parametrize(
    ('pending', 'form', 'handler_type', 'field', 'expected'),
    [
        (PendingSurvive(pending_id=(1, 0), instruction='Survive'), Form(roll='9'), SurviveHandler, 'roll', 9),
        (PendingTermEvent(pending_id=(1, 0), instruction='Event'), Form(roll='8'), TermEventHandler, 'roll', 8),
        (PendingMishap(pending_id=(1, 0), instruction='Mishap'), Form(roll='4'), MishapHandler, 'roll', 4),
        (PendingAdvancement(pending_id=(1, 0), instruction='Advance'), Form(roll='10'), AdvancementHandler, 'roll', 10),
        (
            PendingSkillTable(
                pending_id=(1, 0),
                instruction='Skill table',
                options=[SkillTableOption(label='Service Skills', key='service_skills')],
            ),
            Form(table='service_skills', roll='5'),
            SkillTableHandler,
            'roll',
            5,
        ),
        (PendingInjuryTable(pending_id=(1, 0), instruction='Injury'), Form(roll='2'), InjuryTableHandler, 'roll', 2),
        (PendingAgingRoll(pending_id=(1, 0), instruction='Aging'), Form(roll='7'), AgingRollHandler, 'roll', 7),
        (PendingLifeEvent(pending_id=(1, 0), instruction='Life event'), Form(roll='6'), LifeEventHandler, 'roll', 6),
        (
            PendingLifeEventUnusual(pending_id=(1, 0), instruction='Unusual'),
            Form(roll='5'),
            LifeEventUnusualHandler,
            'roll',
            5,
        ),
        (
            PendingPreCareerEvent(pending_id=(1, 0), instruction='Precareer event'),
            Form(roll='9'),
            PreCareerEventHandler,
            'roll',
            9,
        ),
        (
            PendingPreCareerGraduation(pending_id=(1, 0), instruction='Graduation'),
            Form(roll='10'),
            PreCareerGraduationHandler,
            'roll',
            10,
        ),
        (PendingParoleRoll(pending_id=(1, 0), instruction='Parole'), Form(roll='4'), ParoleRollHandler, 'roll', 4),
    ],
)
def test_roll_pending_inputs_build_events_and_number_specs(pending, form, handler_type, field, expected):
    form_event = pending.event_from_form(form)
    specs = pending.input_specs(_projection())

    assert isinstance(form_event.handler, handler_type)
    assert getattr(form_event, field) == expected
    assert form_event.fulfills == pending.pending_id
    assert any(isinstance(spec, NumberEntry) for spec in specs)


def test_double_injury_pending_builds_two_roll_event_and_specs():
    pending = PendingDoubleInjuryRoll(pending_id=(1, 0), instruction='Double injury')
    event = pending.event_from_form(Form(roll1='4', roll2='2'))

    assert isinstance(event.handler, DoubleInjuryTableHandler)
    assert event.roll1 == 4
    assert event.roll2 == 2
    assert len(pending.input_specs(_projection())) == 2


def test_nearly_killed_pending_asks_for_characteristic_and_roll():
    pending = PendingNearlyKilled(pending_id=(1, 0), instruction='Nearly killed')
    event = pending.event_from_form(Form(characteristic='DEX', roll='4'))

    assert isinstance(event.handler, CharacteristicChoiceHandler)
    assert event.characteristic == Chars.DEX
    assert event.amount == 4
    assert event.fulfills == (1, 0)

    specs = pending.input_specs(_projection())
    assert any(isinstance(s, Select) for s in specs)
    assert any(isinstance(s, NumberEntry) for s in specs)
    select = next(s for s in specs if isinstance(s, Select))
    assert {v for _, v in select.options} == {Chars.STR, Chars.DEX, Chars.END}


@pytest.mark.parametrize(
    ('roll', 'expected_amount', 'pending_type'),
    [
        (5, 1, PendingCharacteristicChoice),
        (4, 2, PendingCharacteristicChoice),
        (3, 2, PendingCharacteristicChoice),
    ],
)
def test_injury_table_fixed_reductions_carry_correct_amount(roll, expected_amount, pending_type):
    projection = _projection()
    Event(id=5, handler=InjuryTableHandler(roll=roll)).apply(projection)
    pending = next(p for p in projection.pending_inputs if isinstance(p, pending_type))
    assert pending.amount == expected_amount
    event = pending.event_from_form(Form(characteristic='STR'))
    assert event.amount == expected_amount


def test_injury_table_roll_2_creates_severely_injured_pending():
    projection = _projection()
    Event(id=5, handler=InjuryTableHandler(roll=2)).apply(projection)
    assert any(isinstance(p, PendingSeverelyInjured) for p in projection.pending_inputs)


def test_severely_injured_pending_uses_roll_as_amount():
    pending = PendingSeverelyInjured(pending_id=(1, 0), instruction='Severely injured')
    event = pending.event_from_form(Form(characteristic='DEX', roll='4'))
    assert isinstance(event.handler, CharacteristicChoiceHandler)
    assert event.characteristic == Chars.DEX
    assert event.amount == 4


def test_injury_table_roll_2_reduces_single_characteristic_by_rolled_amount():
    projection = _projection(characteristics={Chars.STR: 8, Chars.DEX: 8, Chars.END: 8})
    Event(id=5, handler=InjuryTableHandler(roll=2)).apply(projection)
    Event(id=6, handler=CharacteristicChoiceHandler(characteristic=Chars.DEX, amount=3)).apply(projection)
    assert projection.summary.characteristics[Chars.DEX] == 5
    assert projection.summary.characteristics[Chars.STR] == 8
    assert projection.summary.characteristics[Chars.END] == 8


def test_injury_table_result_ordered_before_advancement():
    """
    Injury characteristic choice must appear before advancement after a stay_in_career mishap with from_table injury.
    """
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=1)
    Event(id=5, handler=MishapHandler(roll=6, stay_in_career=True)).apply(projection)

    assert isinstance(projection.pending_inputs[0], PendingInjuryTable)
    assert isinstance(projection.pending_inputs[1], PendingAdvancement)

    Event(id=6, fulfills=(5, 0), handler=InjuryTableHandler(roll=5)).apply(projection)

    inputs = projection.pending_inputs
    char_idx = next(i for i, p in enumerate(inputs) if isinstance(p, PendingCharacteristicChoice))
    adv_idx = next(i for i, p in enumerate(inputs) if isinstance(p, PendingAdvancement))
    assert char_idx < adv_idx


def test_decision_pending_inputs_build_events_and_specs():
    commission = PendingCommissionChoice(pending_id=(1, 0), instruction='Commission')
    assert commission.event_from_form(Form(choice='attempt', roll='9')) == Event(
        fulfills=(1, 0), handler=CommissionHandler(attempt=True, roll=9)
    )
    assert commission.event_from_form(Form(choice='skip')) == Event(
        fulfills=(1, 0), handler=CommissionHandler(attempt=False)
    )
    assert len(commission.input_specs(_projection())) == 2

    reenlist = PendingReenlist(pending_id=(2, 0), instruction='Reenlist')
    assert reenlist.event_from_form(Form(reenlist='yes')) == Event(
        fulfills=(2, 0), handler=ReenlistHandler(reenlist=True)
    )
    assert reenlist.input_specs(_projection()) == []

    assignment = PendingAssignmentChangeChoice(pending_id=(3, 0), muster_out=True)
    assert assignment.event_from_form(Form(choice='switch')) == Event(
        fulfills=(3, 0), handler=AssignmentChangeChoiceHandler(choice='switch')
    )
    assert assignment.event_from_form(Form(choice='same')) == Event(
        fulfills=(3, 0), handler=AssignmentChangeChoiceHandler(choice='same')
    )
    assert isinstance(assignment.input_specs(_projection())[0], Select)

    muster = PendingMusterOut(pending_id=(4, 0))
    assert muster.event_from_form(Form(table='not-valid', roll='7')) == Event(
        fulfills=(4, 0), handler=MusterOutHandler(table='benefits', roll=7)
    )
    assert len(muster.input_specs(_projection())) == 2


def test_skill_choice_pending_inputs_parse_skills_and_advancement_dm():
    projection = _projection()
    admin_json = character_skills.Admin().model_dump_json()

    # Types that support AdvancementDmOption alongside skill options
    adv_dm = AdvancementDmOption()
    opts: list[character_skills.AnySkill | AdvancementDmOption] = [character_skills.Admin(), adv_dm]
    for pending in (
        PendingInitialTrainingChoice(pending_id=(1, 0), instruction='Skill', options=opts),
        PendingSkillTableChoice(pending_id=(1, 0), instruction='Skill', options=opts),
        PendingRankBonusChoice(pending_id=(1, 0), instruction='Skill', options=opts, level=1),
    ):
        skill_event = pending.event_from_form(Form(skill=admin_json))
        dm_event = pending.event_from_form(Form(skill=adv_dm.model_dump_json()))
        specs = pending.input_specs(projection)

        assert isinstance(skill_event.handler, SkillChoiceHandler)
        assert isinstance(skill_event.skill, character_skills.Admin)
        assert isinstance(dm_event.handler, AdvancementDmChoiceHandler)
        assert isinstance(specs[0], Select)

    # PendingSkillChoice uses typed AnySkill options only (no advancement_dm_4)
    skill_pending = PendingSkillChoice(pending_id=(1, 0), instruction='Skill', options=[character_skills.Admin()])
    skill_event = skill_pending.event_from_form(Form(skill=admin_json))
    specs = skill_pending.input_specs(projection)
    assert isinstance(skill_event.handler, SkillChoiceHandler)
    assert isinstance(skill_event.skill, character_skills.Admin)
    assert isinstance(specs[0], Select)


def test_characteristic_benefit_life_and_connection_pending_inputs():
    for pending in (
        PendingCharacteristicChoice(pending_id=(1, 0), instruction='Characteristic', options=[Chars.STR, Chars.DEX]),
        PendingAgingChoice(pending_id=(1, 0), instruction='Aging', options=[Chars.STR, Chars.DEX]),
        PendingAgingChoiceMental(pending_id=(1, 0), instruction='Mental aging', options=[Chars.INT, Chars.SOC]),
    ):
        event = pending.event_from_form(Form(characteristic='DEX'))
        assert isinstance(event.handler, CharacteristicChoiceHandler)
        assert event.characteristic == Chars.DEX
        assert isinstance(pending.input_specs(_projection())[0], Select)

    crisis = PendingAgingCrisis(pending_id=(2, 0), instruction='Crisis')
    assert crisis.event_from_form(Form(paid='true', medical_roll='4')) == Event(
        fulfills=(2, 0), handler=AgingCrisisHandler(paid=True, medical_roll=4)
    )
    assert len(crisis.input_specs(_projection())) == 2

    life_choice = PendingLifeEventChoice(pending_id=(3, 0), instruction='Life choice', roll=4)
    assert life_choice.event_from_form(Form(connection_kind='connection_enemy')) == Event(
        fulfills=(3, 0), handler=ConnectionKindChoiceHandler(connection_kind=ConnectionKind.ENEMY)
    )
    assert isinstance(life_choice.input_specs(_projection())[0], Select)

    connections = PendingConnectionsRoll(
        pending_id=(4, 0), instruction='Connections', connection_type=ConnectionKind.RIVAL, options=[1, 2, 3]
    )
    assert connections.event_from_form(Form(connection_type='connection_enemy', count='3')) == Event(
        fulfills=(4, 0), handler=ConnectionsRollHandler(connection_type=ConnectionKind.ENEMY, count=3)
    )
    assert isinstance(connections.input_specs(_projection())[0], Reference)

    benefit = PendingBenefitChoice(
        pending_id=(5, 0),
        instruction='Benefit',
        benefit_options=[SHIP_SHARE, WEAPON],
    )
    assert benefit.event_from_form(Form(choice_index='1')) == Event(
        fulfills=(5, 0), handler=BenefitChoiceHandler(choice_index=1)
    )
    assert isinstance(benefit.input_specs(_projection())[0], Select)


def test_precareer_specific_pending_inputs():
    precareer_skill_0 = PendingPreCareerSkillChoice(
        pending_id=(4, 0), instruction='Precareer skill', options=[character_skills.LifeScience()], level=0
    )
    precareer_skill_1 = PendingPreCareerSkillChoice(
        pending_id=(5, 0), instruction='Precareer skill', options=[character_skills.LifeScience()], level=1
    )
    life_science_json = character_skills.LifeScience().model_dump_json()
    assert precareer_skill_0.event_from_form(Form(skill=life_science_json)) == Event(
        fulfills=(4, 0), handler=PreCareerSkillChoiceHandler(skill=character_skills.LifeScience())
    )
    level_0_specs = precareer_skill_0.input_specs(_projection())
    level_1_specs = precareer_skill_1.input_specs(_projection())
    assert isinstance(level_0_specs[0], Select)
    assert isinstance(level_1_specs[0], Select)
    assert any(label == 'Life Science' for label, _ in level_0_specs[0].options)
    assert any(label.startswith('Life Science (') for label, _ in level_1_specs[0].options)


# ── common_pending base class event_from_form / input_specs ──────────────────


def test_pending_choices_event_from_form_and_input_specs():
    from ceres.character.domain.career.career_events import PendingChoices
    from ceres.character.mechanism.pending_input import ChoiceBase

    class _FakeChoice(ChoiceBase):
        kind: str = 'test_opt_a'
        label: str = 'Option A'

        def handle(self, projection, event):
            pass

    choice_a = _FakeChoice()
    choice_b = _FakeChoice(kind='test_opt_b', label='Option B')
    pending = PendingChoices(pending_id=(6, 0), instruction='Choose', choices=[choice_a, choice_b])

    event = pending.event_from_form(Form(choice='test_opt_a'))
    assert isinstance(event.handler, CareerChoiceHandler)
    assert event.choice == 'test_opt_a'
    assert event.fulfills == (6, 0)

    specs = pending.input_specs(_projection())
    assert len(specs) == 1
    assert isinstance(specs[0], Select)
    option_values = [value for _, value in specs[0].options]
    assert 'test_opt_a' in option_values
    assert 'test_opt_b' in option_values


def test_career_skill_roll_pending_base_event_from_form_char_and_skill():
    from typing import Literal

    from ceres.character.domain.career.common_pending import CareerSkillRollPendingBase
    from ceres.character.domain.career.navy import PendingNavyMishap3SkillRoll

    pending = PendingNavyMishap3SkillRoll(
        pending_id=(7, 0),
        instruction='Roll',
        options=[character_skills.Electronics(), character_skills.Gunner()],
    )

    # Char option
    class _PendingWithChar(CareerSkillRollPendingBase):
        kind: Literal['_test_char_roll'] = '_test_char_roll'

    char_pending = _PendingWithChar(pending_id=(8, 0), instruction='Roll', options=[Chars.EDU])
    edu_event = char_pending.event_from_form(Form(skill='EDU', modified_roll='9'))
    assert isinstance(edu_event.handler, SkillRollHandler)
    assert edu_event.skill == Chars.EDU
    assert edu_event.modified_roll == 9
    assert edu_event.fulfills == (8, 0)

    # Skill option — form value is the discriminator (ELECTRONICS), not the display name
    skill_event = pending.event_from_form(Form(skill=character_skills.Electronics().type, modified_roll='8'))
    assert isinstance(skill_event.handler, SkillRollHandler)
    assert isinstance(skill_event.skill, character_skills.Electronics)
    assert skill_event.modified_roll == 8

    specs = pending.input_specs(_projection())
    assert len(specs) == 2
    assert isinstance(specs[0], Select)
    assert isinstance(specs[1], NumberEntry)
    labels = [lbl for lbl, _ in specs[0].options]
    assert 'Electronics' in labels
    assert 'Gunner' in labels


def test_career_skill_roll_pending_base_input_specs_includes_char_options():
    from typing import Literal

    from ceres.character.domain.career.common_pending import CareerSkillRollPendingBase

    class _PendingEduRoll(CareerSkillRollPendingBase):
        kind: Literal['_test_edu_roll'] = '_test_edu_roll'

    pending = _PendingEduRoll(pending_id=(1, 0), instruction='Roll', options=[Chars.EDU])
    specs = pending.input_specs(_projection())
    assert isinstance(specs[0], Select)
    labels = [lbl for lbl, _ in specs[0].options]
    assert 'EDU' in labels


def test_career_skill_choice_pending_base_event_from_form_and_input_specs():
    from ceres.character.domain.career.career_data import AdvancementDmOption
    from ceres.character.domain.career.scholar import PendingScholarScienceChoice
    from ceres.character.domain.skills import LifeScience

    adv_dm = AdvancementDmOption()
    science = LifeScience()
    science_json = science.model_dump_json()

    pending = PendingScholarScienceChoice(
        pending_id=(9, 0), instruction='Choose science', options=[science, adv_dm], advancement_precreated=True
    )

    # Skill choice
    skill_event = pending.event_from_form(Form(skill=science_json))
    assert isinstance(skill_event.handler, SkillChoiceHandler)

    # AdvancementDmOption choice
    dm_event = pending.event_from_form(Form(skill=adv_dm.model_dump_json()))
    assert isinstance(dm_event.handler, AdvancementDmChoiceHandler)
    assert dm_event.fulfills == (9, 0)

    specs = pending.input_specs(_projection())
    assert isinstance(specs[0], Select)
    labels = [lbl for lbl, _ in specs[0].options]
    assert any('Science' in lbl or 'science' in lbl.lower() for lbl in labels)


def test_career_skill_choice_pending_base_on_skill_chosen_grants_skill_and_queues_progress():
    from typing import Literal

    from ceres.character.domain.career.common_pending import CareerSkillChoicePendingBase
    from ceres.character.domain.career.loader import load_careers
    from ceres.character.domain.career.scholar import PendingScholarScienceChoice

    class _PendingSkillChoice(CareerSkillChoicePendingBase):
        kind: Literal['_test_skill_choice'] = '_test_skill_choice'

    class _FakeEvent:
        id = 10
        skill = character_skills.Admin()

    scout = load_careers()['Scout']

    # Without advancement_precreated — should queue career progress
    pending = _PendingSkillChoice(pending_id=(1, 0), instruction='Choose', options=[], advancement_precreated=False)
    proj = _projection(
        characteristics={Chars.STR: 7, Chars.DEX: 8, Chars.END: 6, Chars.INT: 9, Chars.EDU: 10, Chars.SOC: 5}
    )
    proj.summary.current_career = scout
    proj.summary.current_assignment = scout.assignment('Courier')
    before_count = len(proj.pending_inputs)
    pending.on_skill_chosen(proj, _FakeEvent())
    assert proj.summary.skill_level(character_skills.Admin) is not None
    assert len(proj.pending_inputs) > before_count

    # With advancement_precreated — should NOT queue career progress
    pending2 = PendingScholarScienceChoice(
        pending_id=(2, 0), instruction='Choose', options=[], advancement_precreated=True
    )
    proj2 = _projection()
    proj2.summary.current_career = scout
    proj2.summary.current_assignment = scout.assignment('Courier')
    before2 = len(proj2.pending_inputs)
    pending2.on_skill_chosen(proj2, _FakeEvent())
    assert len(proj2.pending_inputs) == before2


# ── CareerChoiceHandler error branches ────────────────────────────────────────


def test_career_choice_handler_error_branches():
    with pytest.raises(ReplayError, match='no matching pending input'):
        Event(handler=CareerChoiceHandler(choice='some_choice')).apply(_projection())

    wrong_pending = PendingSurvive(pending_id=(1, 0), instruction='Survive')
    with pytest.raises(ReplayError, match='unexpected pending type'):
        Event(handler=CareerChoiceHandler(choice='some_choice')).apply(_projection(), wrong_pending)

    empty_choices = PendingChoices(pending_id=(1, 0), instruction='Choose', choices=[])
    with pytest.raises(ReplayError, match='Unknown choice'):
        Event(handler=CareerChoiceHandler(choice='no_such')).apply(_projection(), empty_choices)


# ── ReenlistHandler paths ─────────────────────────────────────────────────────


def test_reenlist_handler_reenlist_true_queues_skill_table_for_new_term():
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=1)
    Event(id=7, handler=ReenlistHandler(reenlist=True)).apply(projection)

    assert len(projection.summary.career_terms) == 2
    assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)


def test_reenlist_handler_reenlist_false_sets_up_muster_out():
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=1)
    Event(id=7, handler=ReenlistHandler(reenlist=False)).apply(projection)

    assert projection.summary.current_career is None
    assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── AdvancementHandler forced flags ───────────────────────────────────────────


def test_advancement_handler_roll_12_prevents_muster_out():
    projection = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        term_count=1,
        characteristics={Chars.EDU: 0},
    )
    Event(id=7, handler=AdvancementHandler(roll=12)).apply(projection)

    assignment_change = next(
        (p for p in projection.pending_inputs if isinstance(p, PendingAssignmentChangeChoice)), None
    )
    reenlist = next((p for p in projection.pending_inputs if isinstance(p, PendingReenlist)), None)
    if assignment_change:
        assert assignment_change.muster_out is False
    elif reenlist:
        assert reenlist.can_muster_out is False
    else:
        pytest.fail('Expected PendingAssignmentChangeChoice or PendingReenlist')


def test_advancement_handler_roll_low_triggers_forced_leave():
    projection = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        term_count=2,
        characteristics={Chars.EDU: 0},
    )
    Event(id=7, handler=AdvancementHandler(roll=2)).apply(projection)

    # 2 prior terms + roll=2 → forced_leave → muster_out_setup
    assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── AssignmentChangeChoiceHandler switch branch ───────────────────────────────


def test_assignment_change_choice_handler_switch_creates_pending_switch():
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=1)
    Event(id=7, handler=AssignmentChangeChoiceHandler(choice='switch')).apply(projection)

    assert any(isinstance(p, PendingSwitchAssignment) for p in projection.pending_inputs)


def test_pending_switch_assignment_unknown_assignment_raises():
    courier = SCOUT.assignment('Courier')
    assert courier is not None
    pending = PendingSwitchAssignment(pending_id=(1, 0), instruction='Switch', options=[courier])
    with pytest.raises(ReplayError, match="Unknown assignment 'Bogus'"):
        pending.event_from_form(Form(assignment='Bogus', roll='8'))


# ── SwitchAssignmentHandler success and failure ───────────────────────────────


def test_switch_assignment_handler_success_sets_assignment_and_starts_term():
    explorer = SCOUT.assignment('Explorer')
    assert explorer is not None
    projection = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        term_count=1,
        characteristics={Chars.INT: 7},
    )
    Event(id=7, handler=SwitchAssignmentHandler(assignment=explorer, qualification_roll=8)).apply(projection)

    assert projection.summary.current_assignment == explorer
    assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)


def test_switch_assignment_handler_failure_queues_reenlist_with_current_name():
    explorer = SCOUT.assignment('Explorer')
    assert explorer is not None
    projection = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        term_count=1,
        characteristics={Chars.INT: 0},
    )
    Event(id=7, handler=SwitchAssignmentHandler(assignment=explorer, qualification_roll=2)).apply(projection)

    reenlist = next((p for p in projection.pending_inputs if isinstance(p, PendingReenlist)), None)
    assert reenlist is not None
    assert 'Courier' in reenlist.instruction
    assert 'AssignmentData' not in reenlist.instruction


# ── TermEventHandler effects ──────────────────────────────────────────────────


def test_term_event_handler_life_event_effect_queues_life_event_pending():
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=1)
    Event(id=5, handler=TermEventHandler(roll=7)).apply(projection)  # Scout event 7: LifeEventEffect

    assert any(isinstance(p, PendingLifeEvent) for p in projection.pending_inputs)


def test_term_event_handler_auto_advance_queues_skill_table_and_bumps_rank():
    projection = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        term_count=1,
        characteristics={Chars.EDU: 10},
    )
    Event(id=5, handler=TermEventHandler(roll=12)).apply(projection)  # Scout event 12: AutoAdvanceEffect

    assert projection.summary.rank == 1
    assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)


def test_term_event_handler_roll_mishap_stay_in_career_queues_mishap_with_flag():
    projection = _projection(current_career=ARMY, current_assignment='Infantry', term_count=1)
    Event(id=5, handler=TermEventHandler(roll=2)).apply(projection)  # Army event 2: RollMishapEffect(leave=False)

    mishap_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingMishap)]
    assert len(mishap_pendings) == 1
    assert mishap_pendings[0].stay_in_career is True


def test_term_event_handler_skill_choice_effect_queues_skill_choice():
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=1)
    Event(id=5, handler=TermEventHandler(roll=6)).apply(projection)  # Scout event 6: SkillChoiceEffect

    assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)
    assert not any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── MishapHandler effects not yet covered ─────────────────────────────────────


def test_mishap_handler_gain_connections_effect_queues_two_connection_rolls():
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=1)
    Event(id=5, handler=MishapHandler(roll=3)).apply(projection)  # Scout mishap 3: two GainConnectionsRolledEffect

    rolls = [p for p in projection.pending_inputs if isinstance(p, PendingConnectionsRoll)]
    assert len(rolls) == 2


def test_mishap_handler_skill_choice_effect_queues_pending_skill_choice():
    projection = _projection(current_career=ARMY, current_assignment='Infantry', term_count=1)
    Event(id=5, handler=MishapHandler(roll=3)).apply(projection)  # Army mishap 3: SkillChoiceEffect + GainEnemyEffect

    assert any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)
    assert any(c.kind == 'connection_enemy' for c in projection.summary.connections)


# ── ConnectionKindChoiceHandler narrative ─────────────────────────────────────


@pytest.mark.parametrize(
    ('roll', 'connection_kind', 'expected_fragment'),
    [
        (4, ConnectionKind.RIVAL, 'rival'),
        (4, ConnectionKind.ENEMY, 'enemy'),
        (8, ConnectionKind.RIVAL, 'rival'),
        (8, ConnectionKind.ENEMY, 'enemy'),
    ],
)
def test_connection_kind_choice_handler_adds_narrative_for_life_event_rolls(roll, connection_kind, expected_fragment):
    projection = _projection()
    life_event_choice = PendingLifeEventChoice(pending_id=(1, 0), instruction='Choice', roll=roll)
    Event(id=2, handler=ConnectionKindChoiceHandler(connection_kind=connection_kind)).apply(
        projection, life_event_choice
    )

    assert any(expected_fragment in line.lower() for line in projection.summary.narrative)


# ── LifeEventCrime choice handlers ────────────────────────────────────────────


def test_life_event_crime_lose_benefit_roll_increments_lost_rolls():
    projection = _projection(term_count=1)
    LifeEventCrimeLoseBenefitRoll().handle(projection, Event(handler=CareerChoiceHandler(choice='x')))

    assert projection.summary.career_terms[-1].require_muster_out().lost_rolls == 1


def test_life_event_crime_take_prisoner_sets_forced_next_career():
    from ceres.character.domain.career.prisoner import PRISONER

    projection = _projection()
    LifeEventCrimeTakePrisoner().handle(projection, Event(handler=CareerChoiceHandler(choice='x')))

    assert projection.forced_next_career == PRISONER


# ── muster_out_setup with zero rolls ─────────────────────────────────────────


def test_muster_out_setup_zero_rolls_queues_career_choice():
    career = load_careers()['Scout']
    # term_count=0 and rank=0 → roll_count = 0 → career choice directly
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=0, rank=0)
    muster_out_setup(projection, career, source_event_id=9, pending_idx=0)

    assert any(isinstance(p, PendingCareerChoice) for p in projection.pending_inputs)
    assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── queue_reenlist_or_aging forced_leave ──────────────────────────────────────


def test_queue_reenlist_or_aging_forced_leave_triggers_muster_out():
    projection = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        term_count=1,
        age=26,
    )
    projection.forced_leave = True
    queue_reenlist_or_aging(projection, event_id=7, idx=0)

    assert projection.forced_leave is False
    assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── on_skill_chosen methods ───────────────────────────────────────────────────


def test_pending_initial_training_choice_on_skill_chosen_queues_survive():
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=1)

    class _FakeEvent:
        id = 5
        skill = character_skills.Admin()

    pending = PendingInitialTrainingChoice(
        pending_id=(1, 0), instruction='Training', options=[character_skills.Admin()]
    )
    pending.on_skill_chosen(projection, _FakeEvent())

    assert projection.summary.skill_level(character_skills.Admin) is not None
    assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


def test_pending_skill_table_choice_on_skill_chosen_without_reenlist_queues_survive():
    projection = _projection(current_career=SCOUT, current_assignment='Courier', term_count=1)

    class _FakeEvent:
        id = 5
        skill = character_skills.Admin()

    pending = PendingSkillTableChoice(
        pending_id=(1, 0), instruction='Choose skill', reenlist_queued=False, options=[character_skills.Admin()]
    )
    pending.on_skill_chosen(projection, _FakeEvent())

    assert projection.summary.skill_level(character_skills.Admin) is not None
    assert any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


def test_pending_rank_bonus_choice_on_skill_chosen_queues_skill_table_and_reenlist():
    projection = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        term_count=1,
        characteristics={Chars.EDU: 10},
        rank=1,
    )

    class _FakeEvent:
        id = 5
        skill = character_skills.Admin()

    pending = PendingRankBonusChoice(
        pending_id=(1, 0), instruction='Rank bonus', level=1, options=[character_skills.Admin()]
    )
    pending.on_skill_chosen(projection, _FakeEvent())

    assert any(isinstance(p, PendingSkillTable) for p in projection.pending_inputs)
    assert any(isinstance(p, (PendingAssignmentChangeChoice, PendingReenlist)) for p in projection.pending_inputs)
