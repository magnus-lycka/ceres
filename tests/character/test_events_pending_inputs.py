import random
from typing import Any, cast

from pydantic import TypeAdapter, ValidationError
import pytest

from ceres.character import skills as character_skills
from ceres.character.benefits import SHIP_SHARE, WEAPON
from ceres.character.careers import ARMY, PRISONER, SCOUT
from ceres.character.careers.career_data import (
    AdvancementDmEffect,
    AdvancementDmOption,
    AssignmentData,
    BenefitDmEffect,
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
)
from ceres.character.careers.loader import load_careers
from ceres.character.characteristics import Chars, ConnectionKind
from ceres.character.events import (
    AdvancementDmChoiceEvent,
    AdvancementEvent,
    AgingCrisisEvent,
    AgingRollEvent,
    AssignmentChangeChoiceEvent,
    BackgroundSkillsEvent,
    BenefitChoiceEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CharacterStartedEvent,
    CommissionEvent,
    ConnectionKindChoiceEvent,
    ConnectionsRollEvent,
    DoubleInjuryTableEvent,
    DraftAssignmentEvent,
    DraftEvent,
    EventBase,
    FinishCreationEvent,
    InjuryTableEvent,
    LifeEventEvent,
    LifeEventUnusualEvent,
    MishapEvent,
    MusterOutEvent,
    ParoleRollEvent,
    PendingAdvancement,
    PendingAgingChoice,
    PendingAgingChoiceMental,
    PendingAgingCrisis,
    PendingAgingRoll,
    PendingAssignmentChangeChoice,
    PendingBackgroundSkills,
    PendingBenefitChoice,
    PendingCareerChoice,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
    PendingCharacteristicChoice,
    PendingCommissionChoice,
    PendingConnectionsRoll,
    PendingDoubleInjuryRoll,
    PendingDraftAssignmentChoice,
    PendingDraftChoice,
    PendingInitialTrainingChoice,
    PendingInjuryTable,
    PendingLifeEvent,
    PendingLifeEventChoice,
    PendingLifeEventUnusual,
    PendingMishap,
    PendingMusterOut,
    PendingNearlyKilled,
    PendingParoleRoll,
    PendingPreCareerEvent,
    PendingPreCareerGraduation,
    PendingPreCareerSkillChoice,
    PendingRankBonusChoice,
    PendingReenlist,
    PendingSkillChoice,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingSurvive,
    PendingTermEvent,
    PreCareerEntryEvent,
    PreCareerEventEvent,
    PreCareerGraduationEvent,
    PreCareerSkillChoiceEvent,
    ReenlistEvent,
    ReplayError,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
    _advancement_pending,
    _apply_auto_advance,
    _apply_mishap_ejection,
    _apply_prisoner_advancement,
    _apply_simple_effect,
    _apply_skill_table_entry,
    _spec_name_for_field,
    _start_new_career_term,
    _survive_pending,
    career_progress_pending,
    complete_aging,
    muster_out_setup,
    queue_reenlist_or_aging,
)
from ceres.character.input_specs import NumberEntry, Reference, Select
from ceres.character.sophonts import VILANI
from ceres.character.state import AutoFillContext, CareerTerm, CharacterProjection, CharacterSummary, ScheduledEffect
from tests.character.helpers import MOCK_WORLD


class Form(dict[str, str]):
    def getlist(self, key: str) -> list[str]:
        value = self.get(key, '')
        return [] if value == '' else value.split('|')


def _projection(**summary_kwargs: Any) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **summary_kwargs),
    )


def _ctx(max_terms: int = 4) -> AutoFillContext:
    return AutoFillContext(career='Scout', assignment='Courier', max_terms=max_terms, careers=load_careers())


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

    def available_tables(self, edu: int, assignment_index: int) -> list[str]:
        return ['service_skills']

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


def test_base_event_and_character_started_validation():
    with pytest.raises(NotImplementedError):
        EventBase().apply(_projection())

    adapter = TypeAdapter(CharacterStartedEvent)
    event = adapter.validate_python({'sophont': 'Vilani', 'homeworld': MOCK_WORLD, 'name': 'Test'})

    assert event.sophont is VILANI
    assert event.model_dump()['sophont'] == 'Vilani'
    with pytest.raises(ValidationError, match='Unknown sophont'):
        adapter.validate_python({'sophont': 'Unknown', 'homeworld': MOCK_WORLD, 'name': 'Test'})
    with pytest.raises(ValidationError, match='Expected Sophont or sophont name'):
        adapter.validate_python({'sophont': object(), 'homeworld': MOCK_WORLD, 'name': 'Test'})


def test_ucp_event_rejects_wrong_length():
    with pytest.raises(ReplayError, match='expected 6 hex digits'):
        UcpEvent(ucp='77777').apply(_projection())


def test_event_helpers_apply_simple_effects_and_skill_entries():
    projection = _projection(characteristics={Chars.STR: 1, Chars.SOC: 7})

    _apply_simple_effect(projection, DecreaseCharacteristicEffect(characteristic=Chars.STR, amount=3))
    _apply_simple_effect(projection, GainContactEffect(), source='contact source')
    _apply_simple_effect(projection, GainAllyEffect(), source='ally source')
    _apply_simple_effect(projection, GainRivalEffect(), source='rival source')
    _apply_simple_effect(projection, GainEnemyEffect(), source='enemy source')
    _apply_simple_effect(projection, GainSkillEffect(skill=character_skills.Admin()))
    _apply_simple_effect(projection, AdvancementDmEffect(amount=2), source_event_id=10)
    _apply_simple_effect(projection, BenefitDmEffect(amount=1), source_event_id=11)
    projection.summary.parole_threshold = 11
    _apply_simple_effect(projection, ParoleThresholdChangeEffect(amount=5))
    _apply_simple_effect(projection, ParoleThresholdChangeEffect(amount=-20))
    _apply_skill_table_entry(projection, character_skills.Electronics(comms=character_skills.Level(value=1)))

    assert projection.summary.characteristics[Chars.STR] == 0
    assert [connection.kind for connection in projection.summary.connections] == ['contact', 'ally', 'rival', 'enemy']
    assert projection.summary.parole_threshold == 0
    assert projection.summary.skill_level(character_skills.Admin) == 0
    assert projection.summary.skill_level(character_skills.Electronics) == 1
    assert [effect.trigger for effect in projection.scheduled_effects] == ['advancement', 'muster_out']
    assert _spec_name_for_field(character_skills.Admin, 'level') == 'Level'


def test_auto_advance_can_apply_characteristic_rank_bonus():
    projection = _projection(characteristics={Chars.SOC: 7}, current_assignment_index=1)
    career = FakeCareer(RankBonus(characteristic=Chars.SOC, level=2))

    _apply_auto_advance(projection, career, 5)

    assert projection.summary.rank == 1
    assert projection.summary.characteristics[Chars.SOC] == 9
    assert any(isinstance(pending, PendingSkillTable) for pending in projection.pending_inputs)
    assert any(isinstance(pending, PendingReenlist) for pending in projection.pending_inputs)


def test_assignment_helper_errors_are_reported():
    projection = _projection(current_assignment_index=99)
    career = FakeCareer()

    with pytest.raises(ReplayError, match='Unknown assignment index 99 in career'):
        _start_new_career_term(projection, career, 1)
    with pytest.raises(ReplayError, match='Unknown assignment index 99 in career'):
        _survive_pending(career, 99, 1)
    with pytest.raises(ReplayError, match='Unknown assignment index 99'):
        _advancement_pending(career, 99, 1)


def test_mishap_ejection_queues_aging_for_older_character():
    projection = _projection(age=30, current_career=SCOUT, current_assignment='Courier', current_assignment_index=1)
    career = load_careers()['Scout']

    next_idx = _apply_mishap_ejection(projection, career, source_event_id=7, pending_idx=2)

    assert next_idx == 3
    assert projection.summary.age == 34
    assert projection.muster_out_career is not None
    assert projection.muster_out_career.name == 'Scout'
    assert projection.summary.current_career is None
    assert any(isinstance(pending, PendingAgingRoll) and pending.id == '7.2' for pending in projection.pending_inputs)


def test_basic_event_error_branches():
    projection = _projection(drafted=True)
    with pytest.raises(ReplayError, match='may only enter the draft once'):
        DraftEvent(career='Army').apply(projection)

    with pytest.raises(ReplayError, match="Unknown career: 'Nope'"):
        DraftEvent(career='Nope').apply(_projection())
    with pytest.raises(ReplayError, match="Unknown career: 'Nope'"):
        DraftAssignmentEvent(career='Nope', assignment='Infantry').apply(_projection())

    active = _projection(current_career=SCOUT, current_assignment='Courier', current_assignment_index=99)
    with pytest.raises(ReplayError, match='Unknown assignment index 99'):
        SurviveEvent(roll=8).apply(active)

    with pytest.raises(ReplayError, match='Injury table roll must be 1-6'):
        InjuryTableEvent(roll=0).apply(_projection())
    with pytest.raises(ReplayError, match='Double injury roll must be 1-6'):
        DoubleInjuryTableEvent(roll1=1, roll2=7).apply(_projection())


def test_muster_out_and_benefit_choice_error_branches():
    with pytest.raises(ReplayError, match='No muster out career set'):
        MusterOutEvent(table='cash', roll=1).apply(_projection())

    from ceres.character.careers.career_data import Career

    projection = _projection()
    projection.muster_out_career = Career(name='Nope')
    with pytest.raises(ReplayError, match="Career 'Nope' has no muster out table"):
        MusterOutEvent(table='cash', roll=1).apply(projection)

    with pytest.raises(ReplayError, match='must fulfill a PendingBenefitChoice'):
        BenefitChoiceEvent(choice_index=0).apply(_projection())

    pending = PendingBenefitChoice(
        id='1.0',
        instruction='Benefit',
        options=['Ship Share'],
        benefit_options=[SHIP_SHARE],
    )
    with pytest.raises(ReplayError, match='choice_index 2 out of range'):
        BenefitChoiceEvent(choice_index=2).apply(_projection(), pending)


def test_aging_roll_extreme_results():
    effective_minus_4 = _projection(term_count=6, characteristics={Chars.STR: 7, Chars.DEX: 7, Chars.END: 7})
    AgingRollEvent(id=1, roll=2).apply(effective_minus_4)
    minus_4_choices = [p for p in effective_minus_4.pending_inputs if isinstance(p, PendingAgingChoice)]
    assert [p.instruction for p in minus_4_choices] == [
        'Aging: choose STR, DEX, or END to reduce by 2',
        'Aging: choose STR, DEX, or END to reduce by 2',
        'Aging: choose STR, DEX, or END to reduce by 1',
    ]

    effective_minus_5 = _projection(term_count=7, characteristics={Chars.STR: 7, Chars.DEX: 7, Chars.END: 7})
    AgingRollEvent(id=2, roll=2).apply(effective_minus_5)
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
    AgingRollEvent(id=3, roll=2).apply(effective_minus_6)
    assert any(isinstance(p, PendingAgingChoiceMental) for p in effective_minus_6.pending_inputs)


def test_commission_event_skip_failure_success_and_unsupported_career():
    scout = _projection(current_career=SCOUT, current_assignment='Courier', current_assignment_index=1)
    with pytest.raises(ReplayError, match='Scout does not support commission'):
        CommissionEvent(attempt=True, roll=12).apply(scout)

    skipped = _projection(current_career=ARMY, current_assignment='Support', current_assignment_index=1)
    CommissionEvent(id=1, attempt=False).apply(skipped)
    assert any(isinstance(p, PendingAdvancement) and p.id == '1.0' for p in skipped.pending_inputs)

    failed = _projection(
        current_career=ARMY,
        current_assignment='Support',
        current_assignment_index=1,
        characteristics={Chars.SOC: 2},
    )
    failed.scheduled_effects.append(
        ScheduledEffect(trigger='advancement', source_event_id=99, effect={'type': 'dm', 'amount': 1})
    )
    CommissionEvent(id=2, attempt=True, roll=2).apply(failed)
    assert failed.scheduled_effects == []
    assert any(isinstance(p, PendingAdvancement) and p.id == '2.0' for p in failed.pending_inputs)

    succeeded = _projection(
        current_career=ARMY,
        current_assignment='Support',
        current_assignment_index=1,
        characteristics={Chars.SOC: 12, Chars.EDU: 10},
        career_terms=[CareerTerm(career=ARMY, assignment='Support', assignment_index=1)],
    )
    CommissionEvent(id=3, attempt=True, roll=12).apply(succeeded)
    assert succeeded.summary.rank == 1
    assert succeeded.summary.career_terms[-1].commission is True
    assert succeeded.summary.skill_level(character_skills.Leadership) == 1
    assert any(isinstance(p, PendingSkillTable) and p.id == '3.0' for p in succeeded.pending_inputs)


def test_precareer_entry_error_and_failure_branches():
    with pytest.raises(ReplayError, match="Unknown pre-career: 'Nope'"):
        PreCareerEntryEvent(precareer='Nope', roll=7).apply(_projection())
    with pytest.raises(ReplayError, match='only available in terms'):
        PreCareerEntryEvent(precareer='University', roll=7).apply(_projection(term_count=3))
    with pytest.raises(ReplayError, match='may only attend one pre-career'):
        PreCareerEntryEvent(precareer='University', roll=7).apply(_projection(precareer_completed='University'))

    failed = _projection(characteristics={Chars.EDU: 0})
    PreCareerEntryEvent(id=4, precareer='University', roll=2).apply(failed)
    assert any(isinstance(p, PendingCareerChoice) for p in failed.pending_inputs)
    assert failed.summary.precareer is None

    soc_bonus = _projection(characteristics={Chars.INT: 12, Chars.SOC: 12})
    PreCareerEntryEvent(id=5, precareer='Merchant Academy (Business)', roll=7).apply(soc_bonus)
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
    PreCareerEventEvent(id=roll, roll=roll).apply(projection)
    assert any(isinstance(p, pending_type) for p in projection.pending_inputs)


def test_precareer_event_error_manual_note_and_ending_branches():
    with pytest.raises(ReplayError, match='No active pre-career'):
        PreCareerEventEvent(roll=7).apply(_projection())
    with pytest.raises(ReplayError, match="Unknown pre-career: 'Nope'"):
        PreCareerEventEvent(roll=7).apply(_projection(precareer='Nope'))
    with pytest.raises(ReplayError, match='No pre-career event entry for roll 13'):
        PreCareerEventEvent(roll=13).apply(_projection(precareer='University'))

    for roll, problem_text in ((2, 'attempt to enter the Psion career'), (4, 'Prisoner career next term')):
        projection = _projection(precareer='University')
        PreCareerEventEvent(id=roll, roll=roll).apply(projection)
        assert any(problem_text in problem for problem in projection.summary.problems)

    ended = _projection(precareer='University')
    ended.pending_inputs.append(PendingPreCareerGraduation(id='11.0', instruction='Graduation'))
    PreCareerEventEvent(id=11, roll=11).apply(ended)
    assert ended.summary.precareer is None
    assert ended.summary.precareer_completed == 'University'
    assert not any(isinstance(p, PendingPreCareerGraduation) for p in ended.pending_inputs)
    assert any(isinstance(p, PendingCareerChoice) for p in ended.pending_inputs)

    recognised = _projection(precareer='University', characteristics={Chars.SOC: 7})
    PreCareerEventEvent(id=12, roll=12).apply(recognised)
    assert recognised.summary.characteristics[Chars.SOC] == 8


def test_precareer_graduation_error_and_failure_branches():
    with pytest.raises(ReplayError, match='No active pre-career for graduation'):
        PreCareerGraduationEvent(roll=7).apply(_projection())
    with pytest.raises(ReplayError, match="Unknown pre-career: 'Nope'"):
        PreCareerGraduationEvent(roll=7).apply(_projection(precareer='Nope'))

    failed = _projection(precareer='University', characteristics={Chars.INT: 2})
    PreCareerGraduationEvent(id=1, roll=2).apply(failed)
    assert failed.summary.precareer is None
    assert failed.summary.precareer_completed == 'University'
    assert failed.summary.precareer_skills == []
    assert any('Did not graduate from University.' in line for line in failed.summary.narrative)
    assert any(isinstance(p, PendingCareerChoice) for p in failed.pending_inputs)


def test_prisoner_advancement_special_cases():
    missing_assignment = _projection(current_assignment_index=99)
    with pytest.raises(ReplayError, match='Unknown assignment index 99'):
        _apply_prisoner_advancement(missing_assignment, AdvancementEvent(id=1, roll=12), FakePrisonerCareer())

    choice_bonus = _projection(
        current_assignment_index=1,
        characteristics={Chars.INT: 12, Chars.EDU: 10},
        parole_threshold=6,
    )
    choice_bonus.scheduled_effects.append(
        ScheduledEffect(trigger='advancement', source_event_id=1, effect={'type': 'dm', 'amount': 1})
    )
    _apply_prisoner_advancement(
        choice_bonus,
        AdvancementEvent(id=2, roll=12),
        FakePrisonerCareer(RankBonus(choices=[character_skills.Admin()], level=1)),
    )
    assert choice_bonus.scheduled_effects == []
    assert choice_bonus.prisoner_freed is True
    assert any(
        isinstance(p, PendingRankBonusChoice) and p.options == [character_skills.Admin()]
        for p in choice_bonus.pending_inputs
    )

    characteristic_bonus = _projection(
        current_assignment_index=1,
        characteristics={Chars.INT: 12, Chars.SOC: 7, Chars.EDU: 10},
        parole_threshold=20,
    )
    _apply_prisoner_advancement(
        characteristic_bonus,
        AdvancementEvent(id=3, roll=12),
        FakePrisonerCareer(RankBonus(characteristic=Chars.SOC, level=2)),
    )
    assert characteristic_bonus.summary.characteristics[Chars.SOC] == 9
    assert any(isinstance(p, PendingSkillTable) for p in characteristic_bonus.pending_inputs)


def test_queue_reenlist_or_aging_handles_freed_prisoner_paths():
    older = _projection(
        age=30,
        current_career=PRISONER,
        current_assignment='Inmate',
        current_assignment_index=1,
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
        current_assignment_index=1,
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
        current_assignment_index=1,
        term_count=1,
        rank=2,
    )
    projection.scheduled_effects = [
        ScheduledEffect(trigger='muster_out_reduce', source_event_id=1, effect={'value': 1}),
        ScheduledEffect(trigger='muster_out_add', source_event_id=2, effect={'value': 2}),
    ]

    next_idx = muster_out_setup(projection, career, source_event_id=6, pending_idx=0)

    assert next_idx == 3
    assert projection.scheduled_effects == []
    assert projection.summary.current_career is None
    assert len([p for p in projection.pending_inputs if isinstance(p, PendingMusterOut)]) == 3

    assignment_change = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        current_assignment_index=1,
    )
    complete_aging(assignment_change, source_event_id=7)
    pending = next(p for p in assignment_change.pending_inputs if isinstance(p, PendingAssignmentChangeChoice))
    assert pending.options == ['same', 'Surveyor', 'Explorer', 'muster_out']


def test_career_progress_pending_reports_invalid_career_shape():
    class BadCommissionCareer(FakeCareer):
        commission = None

        def can_attempt_commission(self, projection: CharacterProjection) -> bool:
            return True

    with pytest.raises(ReplayError, match='can attempt commission without commission rules'):
        career_progress_pending(_projection(), cast(Any, BadCommissionCareer()), event_id=1)


def test_skill_choice_auto_events_fall_back_to_advancement_dm_when_no_skill_can_be_chosen():
    projection = _projection(skills=[character_skills.Admin(level=character_skills.Level(value=4))])

    for pending in (
        PendingInitialTrainingChoice(id='1.0', instruction='Skill', options=[character_skills.Admin()]),
        PendingSkillTableChoice(id='2.0', instruction='Skill', options=[character_skills.Admin()]),
        PendingRankBonusChoice(id='3.0', instruction='Skill', options=[character_skills.Admin()], level=1),
        PendingCareerSkillChoice(
            id='4.0', instruction='Skill', career='Scout', roll=6, options=[character_skills.Admin()]
        ),
    ):
        assert isinstance(pending.auto_event(projection, _ctx(), random.Random(1)), AdvancementDmChoiceEvent)


def test_pending_background_skills_builds_form_auto_event_and_specs():
    pending = PendingBackgroundSkills(
        id='2.0',
        instruction='Choose 2 background skills',
        options=[character_skills.Admin(), character_skills.Medic()],
    )
    form = Form(skill='{"type":"Admin","level":{"value":0}}|{"type":"Medic","level":{"value":0}}')

    form_event = pending.event_from_form(form)
    auto_event = pending.auto_event(_projection(), _ctx(), random.Random(1))
    specs = pending.input_specs(_projection())

    assert isinstance(form_event, BackgroundSkillsEvent)
    assert [skill.name() for skill in form_event.skills] == ['Admin', 'Medic']
    assert isinstance(auto_event, BackgroundSkillsEvent)
    assert len(auto_event.skills) == 2
    assert isinstance(specs[0], Select)
    assert specs[0].min_select == 2
    assert specs[0].max_select == 2
    assert [label for label, _value in specs[0].options] == ['Admin', 'Medic']


def test_pending_career_choice_form_auto_event_and_specs():
    projection = _projection(term_count=4)
    pending = PendingCareerChoice(id='3.0', instruction='Choose career', options=['Scout'])

    assert isinstance(pending.auto_event(projection, _ctx(max_terms=4), random.Random(1)), FinishCreationEvent)
    assert isinstance(pending.event_from_form(Form(kind='finish_creation')), FinishCreationEvent)

    pre_career = pending.event_from_form(Form(kind='precareer_entry', precareer='University', roll='9'))
    assert isinstance(pre_career, PreCareerEntryEvent)
    assert pre_career.precareer == 'University'
    assert pre_career.roll == 9

    career = pending.event_from_form(Form(career='Scout', assignment='Courier', roll='12'))
    assert isinstance(career, CareerEvent)
    assert career.career == 'Scout'
    assert career.assignment == 'Courier'
    assert career.qualification_roll == 12

    projection.summary.term_count = 0
    auto_career = pending.auto_event(projection, _ctx(), random.Random(1))
    assert isinstance(auto_career, CareerEvent)
    assert auto_career.career == 'Scout'
    assert auto_career.assignment == 'Courier'
    assert pending.input_specs(projection) == []


def test_pending_draft_choices_build_expected_events_and_specs():
    draft = PendingDraftChoice(id='3.0', instruction='Draft or drift')
    draft_event = draft.event_from_form(Form(choice='draft', roll='2'))
    drifter_event = draft.event_from_form(Form(choice='drifter', assignment='Scavenger'))

    assert isinstance(draft_event, DraftEvent)
    assert draft_event.career == 'Army'
    assert isinstance(drifter_event, CareerEvent)
    assert drifter_event.career == 'Drifter'
    assert drifter_event.assignment == 'Scavenger'
    assert isinstance(draft.auto_event(_projection(), _ctx(), random.Random(1)), DraftEvent)
    assert draft.input_specs(_projection()) == []

    assignment = PendingDraftAssignmentChoice(id='4.0', instruction='Assignment', career='Army', options=['Support'])
    form_event = assignment.event_from_form(Form(assignment='Support'))
    auto_event = assignment.auto_event(_projection(), _ctx(), random.Random(1))
    specs = assignment.input_specs(_projection())

    assert isinstance(form_event, DraftAssignmentEvent)
    assert form_event.career == 'Army'
    assert form_event.assignment == 'Support'
    assert isinstance(auto_event, DraftAssignmentEvent)
    assert isinstance(specs[0], Reference)
    assert specs[0].value == 'Army'
    assert isinstance(specs[1], Select)


@pytest.mark.parametrize(
    ('pending', 'form', 'event_type', 'field', 'expected'),
    [
        (PendingSurvive(id='1.0', instruction='Survive'), Form(roll='9'), SurviveEvent, 'roll', 9),
        (PendingTermEvent(id='1.0', instruction='Event'), Form(roll='8'), TermEventEvent, 'roll', 8),
        (PendingMishap(id='1.0', instruction='Mishap'), Form(roll='4'), MishapEvent, 'roll', 4),
        (PendingAdvancement(id='1.0', instruction='Advance'), Form(roll='10'), AdvancementEvent, 'roll', 10),
        (
            PendingSkillTable(id='1.0', instruction='Skill table', options=['service_skills']),
            Form(table='service_skills', roll='5'),
            SkillTableEvent,
            'roll',
            5,
        ),
        (PendingNearlyKilled(id='1.0', instruction='Nearly killed'), Form(roll='3'), InjuryTableEvent, 'roll', 3),
        (PendingInjuryTable(id='1.0', instruction='Injury'), Form(roll='2'), InjuryTableEvent, 'roll', 2),
        (PendingAgingRoll(id='1.0', instruction='Aging'), Form(roll='7'), AgingRollEvent, 'roll', 7),
        (PendingLifeEvent(id='1.0', instruction='Life event'), Form(roll='6'), LifeEventEvent, 'roll', 6),
        (
            PendingLifeEventUnusual(id='1.0', instruction='Unusual'),
            Form(roll='5'),
            LifeEventUnusualEvent,
            'roll',
            5,
        ),
        (
            PendingPreCareerEvent(id='1.0', instruction='Precareer event'),
            Form(roll='9'),
            PreCareerEventEvent,
            'roll',
            9,
        ),
        (
            PendingPreCareerGraduation(id='1.0', instruction='Graduation'),
            Form(roll='10'),
            PreCareerGraduationEvent,
            'roll',
            10,
        ),
        (PendingParoleRoll(id='1.0', instruction='Parole'), Form(roll='4'), ParoleRollEvent, 'roll', 4),
    ],
)
def test_roll_pending_inputs_build_events_and_number_specs(pending, form, event_type, field, expected):
    form_event = pending.event_from_form(form)
    auto_event = pending.auto_event(_projection(), _ctx(), random.Random(1))
    specs = pending.input_specs(_projection())

    assert isinstance(form_event, event_type)
    assert getattr(form_event, field) == expected
    assert form_event.fulfills == pending.id
    assert isinstance(auto_event, event_type)
    assert any(isinstance(spec, NumberEntry) for spec in specs)


def test_double_injury_pending_builds_two_roll_event_and_specs():
    pending = PendingDoubleInjuryRoll(id='1.0', instruction='Double injury')
    event = pending.event_from_form(Form(roll1='4', roll2='2'))

    assert isinstance(event, DoubleInjuryTableEvent)
    assert event.roll1 == 4
    assert event.roll2 == 2
    assert isinstance(pending.auto_event(_projection(), _ctx(), random.Random(1)), DoubleInjuryTableEvent)
    assert len(pending.input_specs(_projection())) == 2


def test_decision_pending_inputs_build_events_and_specs():
    commission = PendingCommissionChoice(id='1.0', instruction='Commission')
    assert commission.event_from_form(Form(choice='attempt', roll='9')) == CommissionEvent(
        attempt=True, roll=9, fulfills='1.0'
    )
    assert commission.event_from_form(Form(choice='skip')) == CommissionEvent(attempt=False, fulfills='1.0')
    assert commission.auto_event(_projection(), _ctx(), random.Random(1)) == CommissionEvent(
        attempt=False, fulfills='1.0'
    )
    assert len(commission.input_specs(_projection())) == 2

    reenlist = PendingReenlist(id='2.0', instruction='Reenlist')
    assert reenlist.event_from_form(Form(reenlist='yes')) == ReenlistEvent(reenlist=True, fulfills='2.0')
    assert reenlist.auto_event(_projection(term_count=3), _ctx(max_terms=4), random.Random(1)) == ReenlistEvent(
        reenlist=True, fulfills='2.0'
    )
    assert reenlist.auto_event(_projection(term_count=4), _ctx(max_terms=4), random.Random(1)) == ReenlistEvent(
        reenlist=False, fulfills='2.0'
    )
    assert reenlist.input_specs(_projection()) == []

    assignment = PendingAssignmentChangeChoice(
        id='3.0', instruction='Assignment', options=['same', 'Surveyor', 'muster_out']
    )
    assert assignment.event_from_form(Form(choice='Surveyor', roll='11')) == AssignmentChangeChoiceEvent(
        choice='Surveyor', qualification_roll=11, fulfills='3.0'
    )
    assert assignment.event_from_form(Form(choice='same')) == AssignmentChangeChoiceEvent(
        choice='same', qualification_roll=None, fulfills='3.0'
    )
    assert assignment.auto_event(_projection(term_count=4), _ctx(max_terms=4), random.Random(1)) == (
        AssignmentChangeChoiceEvent(choice='muster_out', fulfills='3.0')
    )
    assert isinstance(assignment.input_specs(_projection())[0], Select)

    muster = PendingMusterOut(id='4.0', instruction='Muster', options=['cash', 'benefits'])
    assert muster.event_from_form(Form(table='not-valid', roll='7')) == MusterOutEvent(
        table='benefits', roll=7, fulfills='4.0'
    )
    assert isinstance(muster.auto_event(_projection(), _ctx(), random.Random(1)), MusterOutEvent)
    assert len(muster.input_specs(_projection())) == 2


def test_skill_choice_pending_inputs_parse_skills_and_advancement_dm():
    projection = _projection()
    admin_json = character_skills.Admin().model_dump_json()

    # Types that support AdvancementDmOption alongside skill options
    adv_dm = AdvancementDmOption()
    opts: list[character_skills.AnySkill | AdvancementDmOption] = [character_skills.Admin(), adv_dm]
    for pending in (
        PendingInitialTrainingChoice(id='1.0', instruction='Skill', options=opts),
        PendingSkillTableChoice(id='1.0', instruction='Skill', options=opts),
        PendingRankBonusChoice(id='1.0', instruction='Skill', options=opts, level=1),
        PendingCareerSkillChoice(
            id='1.0',
            instruction='Skill',
            career='Scout',
            roll=6,
            options=[character_skills.Admin(), adv_dm],
        ),
    ):
        skill_event = pending.event_from_form(Form(skill=admin_json))
        dm_event = pending.event_from_form(Form(skill=adv_dm.model_dump_json()))
        specs = pending.input_specs(projection)

        assert isinstance(skill_event, SkillChoiceEvent)
        assert isinstance(skill_event.skill, character_skills.Admin)
        assert isinstance(dm_event, AdvancementDmChoiceEvent)
        assert isinstance(specs[0], Select)
        auto_event = pending.auto_event(projection, _ctx(), random.Random(1))
        assert isinstance(auto_event, SkillChoiceEvent | AdvancementDmChoiceEvent)

    # PendingSkillChoice uses typed AnySkill options only (no advancement_dm_4)
    skill_pending = PendingSkillChoice(id='1.0', instruction='Skill', options=[character_skills.Admin()])
    skill_event = skill_pending.event_from_form(Form(skill=admin_json))
    specs = skill_pending.input_specs(projection)
    assert isinstance(skill_event, SkillChoiceEvent)
    assert isinstance(skill_event.skill, character_skills.Admin)
    assert isinstance(specs[0], Select)
    auto_event = skill_pending.auto_event(projection, _ctx(), random.Random(1))
    assert isinstance(auto_event, SkillChoiceEvent)


def test_characteristic_benefit_life_and_connection_pending_inputs():
    for pending in (
        PendingCharacteristicChoice(id='1.0', instruction='Characteristic', options=['STR', 'DEX']),
        PendingAgingChoice(id='1.0', instruction='Aging', options=['STR', 'DEX']),
        PendingAgingChoiceMental(id='1.0', instruction='Mental aging', options=['INT', 'SOC']),
    ):
        event = pending.event_from_form(Form(characteristic='DEX'))
        assert isinstance(event, CharacteristicChoiceEvent)
        assert event.characteristic == Chars.DEX
        assert isinstance(pending.auto_event(_projection(), _ctx(), random.Random(1)), CharacteristicChoiceEvent)
        assert isinstance(pending.input_specs(_projection())[0], Select)

    crisis = PendingAgingCrisis(id='2.0', instruction='Crisis')
    assert crisis.event_from_form(Form(paid='true', medical_roll='4')) == AgingCrisisEvent(
        paid=True, medical_roll=4, fulfills='2.0'
    )
    assert crisis.auto_event(_projection(), _ctx(), random.Random(1)) == AgingCrisisEvent(
        paid=False, medical_roll=0, fulfills='2.0'
    )
    assert len(crisis.input_specs(_projection())) == 2

    life_choice = PendingLifeEventChoice(id='3.0', instruction='Life choice', roll=4)
    assert life_choice.event_from_form(Form(connection_kind='enemy')) == ConnectionKindChoiceEvent(
        connection_kind=ConnectionKind.ENEMY, fulfills='3.0'
    )
    assert isinstance(life_choice.auto_event(_projection(), _ctx(), random.Random(1)), ConnectionKindChoiceEvent)
    assert isinstance(life_choice.input_specs(_projection())[0], Select)

    connections = PendingConnectionsRoll(
        id='4.0', instruction='Connections', connection_type=ConnectionKind.RIVAL, options=['1', '2', '3']
    )
    assert connections.event_from_form(Form(connection_type='enemy', count='3')) == ConnectionsRollEvent(
        connection_type=ConnectionKind.ENEMY, count=3, fulfills='4.0'
    )
    assert isinstance(connections.auto_event(_projection(), _ctx(), random.Random(1)), ConnectionsRollEvent)
    assert isinstance(connections.input_specs(_projection())[0], Reference)

    benefit = PendingBenefitChoice(
        id='5.0',
        instruction='Benefit',
        options=['Ship Share', 'Weapon'],
        benefit_options=[SHIP_SHARE, WEAPON],
    )
    assert benefit.event_from_form(Form(choice_index='1')) == BenefitChoiceEvent(choice_index=1, fulfills='5.0')
    assert isinstance(benefit.auto_event(_projection(), _ctx(), random.Random(1)), BenefitChoiceEvent)
    assert isinstance(benefit.input_specs(_projection())[0], Select)


def test_career_and_precareer_specific_pending_inputs():
    career_event = PendingCareerEvent(id='1.0', instruction='Event', career='Scout', roll=6, options=['take_skill'])
    assert career_event.event_from_form(Form(choice='take_skill')) == CareerChoiceEvent(
        context='scout_event_6', choice='take_skill', fulfills='1.0'
    )
    assert isinstance(career_event.auto_event(_projection(), _ctx(), random.Random(1)), CareerChoiceEvent)
    assert career_event.input_specs(_projection()) == []

    mishap = PendingCareerMishap(id='2.0', instruction='Mishap', career='Scout', roll=4, options=['accept'])
    assert mishap.event_from_form(Form(choice='accept')) == CareerChoiceEvent(
        context='scout_mishap_4', choice='accept', fulfills='2.0'
    )
    assert isinstance(mishap.auto_event(_projection(), _ctx(), random.Random(1)), CareerChoiceEvent)
    assert mishap.input_specs(_projection()) == []

    skill_roll = PendingCareerSkillRoll(
        id='3.0',
        instruction='Skill roll',
        career='Scout',
        roll=6,
        context='scout_event_6',
        options=[Chars.STR, character_skills.Admin()],
    )
    char_event = skill_roll.event_from_form(Form(skill='STR', modified_roll='9'))
    skill_event = skill_roll.event_from_form(Form(skill='Admin', modified_roll='8'))
    assert isinstance(char_event, SkillRollEvent)
    assert char_event.skill == Chars.STR
    assert isinstance(skill_event, SkillRollEvent)
    assert isinstance(skill_event.skill, character_skills.Admin)
    assert isinstance(skill_roll.auto_event(_projection(), _ctx(), random.Random(1)), SkillRollEvent)
    assert len(skill_roll.input_specs(_projection())) == 2

    precareer_skill_0 = PendingPreCareerSkillChoice(
        id='4.0', instruction='Precareer skill', options=['Science'], level=0
    )
    precareer_skill_1 = PendingPreCareerSkillChoice(
        id='5.0', instruction='Precareer skill', options=['Life Science'], level=1
    )
    assert precareer_skill_0.event_from_form(Form(skill='Science')) == PreCareerSkillChoiceEvent(
        skill='Science', fulfills='4.0'
    )
    level_0_specs = precareer_skill_0.input_specs(_projection())
    level_1_specs = precareer_skill_1.input_specs(_projection())
    assert isinstance(level_0_specs[0], Select)
    assert isinstance(level_1_specs[0], Select)
    assert 'Science' in [value for _label, value in level_0_specs[0].options]
    assert any(value.startswith('Life Science (') for _label, value in level_1_specs[0].options)
    assert isinstance(precareer_skill_1.auto_event(_projection(), _ctx(), random.Random(1)), PreCareerSkillChoiceEvent)
