from pydantic import TypeAdapter, ValidationError
import pytest

from ceres.character.domain.career.advancement import PendingRankBonusChoice
from ceres.character.domain.career.career_events import (
    PendingCareerChoice,
    PendingInitialTrainingChoice,
    PendingSkillTableChoice,
)
from ceres.character.domain.character_start import CharacterStartedHandler, UcpHandler
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.loader import precareer_of_type
from ceres.character.domain.precareer.precareer_events import PreCareerEntryHandler
from ceres.character.domain.precareer.psionic_community import PsionicCommunityPreCareer
from ceres.character.domain.psionics import (
    PSIONIC_TALENT_LEARNING_DMS,
    Awareness,
    Clairvoyance,
    FinishPsionicInstituteTrainingHandler,
    InitialPsiTestAcceptedHandler,
    InitialPsiTestDeclinedHandler,
    InitialPsiTestHandler,
    PendingInitialPsiStrengthRoll,
    PendingInitialPsiTest,
    PendingPsionicInstituteTraining,
    PendingPsionicTalentLevelChoice,
    Psi,
    Psionics,
    PsionicTalentLevelHandler,
    PsionicTalentTrainingHandler,
    PsiStrengthTestHandler,
    Telekinesis,
    Telepathy,
    Teleportation,
    initial_psi_test_is_available,
    psionic_talent_classes,
    psionic_talent_instances,
    queue_psionic_institute_training,
)
from ceres.character.domain.skills import AnySkill, Level, _skill_classes
from ceres.character.domain.sophont import VILANI, Sophont
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.unit.character.helpers import MOCK_WORLD


def _summary() -> CharacterSummary:
    return CharacterSummary(name='Psi', sophont=VILANI, homeworld=MOCK_WORLD)


def _psionic_projection(psi: int = 9, psionics: Psionics | None = None) -> CharacterProjection:
    summary = _summary()
    summary.characteristics[Chars.PSI] = psi
    summary.psionics = psionics or Psionics()
    return CharacterProjection(character_id=1, summary=summary)


def test_psionic_talents_are_not_ordinary_skills() -> None:
    assert Telepathy not in _skill_classes(AnySkill)
    with pytest.raises(ValidationError):
        TypeAdapter(AnySkill).validate_python(Telepathy().model_dump())


def test_psi_wraps_a_psionic_talent_for_use_in_career_tables() -> None:
    entry = Psi(Telepathy())

    assert isinstance(entry.talent, Telepathy)


def test_character_without_psi_has_no_psionics_state() -> None:
    summary = _summary()

    assert Chars.PSI not in summary.characteristics
    assert summary.psionics is None


def test_psi_test_uses_terms_served_and_creates_psionics_state() -> None:
    summary = _summary()

    psi = summary.test_psionic_strength(raw_roll=10, terms_served=2)

    assert psi == 8
    assert summary.characteristics[Chars.PSI] == 8
    assert summary.psionics == Psionics()


def test_zero_psi_leaves_character_without_psionics() -> None:
    summary = _summary()

    psi = summary.test_psionic_strength(raw_roll=2, terms_served=2)

    assert psi == 0
    assert Chars.PSI not in summary.characteristics
    assert summary.psionics is None


def test_first_telepathy_attempt_is_automatic_and_counts_as_an_attempt() -> None:
    psionics = Psionics()

    result = psionics.attempt_talent_acquisition(Telepathy, psi=3, raw_roll=2)

    assert result.success
    assert result.automatic
    assert psionics.talent_acquisition_checks == 1
    assert psionics.talent_level(Telepathy) == 0


def test_acquisition_uses_psi_dm_learning_dm_and_previous_attempts() -> None:
    psionics = Psionics(talent_acquisition_checks=1)

    failed = psionics.attempt_talent_acquisition(Telekinesis, psi=9, raw_roll=4)
    succeeded = psionics.attempt_talent_acquisition(Clairvoyance, psi=9, raw_roll=5)

    assert failed.total == 6  # 4 + PSI DM 1 + learning DM 2 - one previous check
    assert not failed.success
    assert succeeded.total == 7  # 5 + 1 + 3 - two previous checks
    assert not succeeded.success
    assert psionics.talent_acquisition_checks == 3
    assert psionics.talent_level(Telekinesis) is None
    assert psionics.talent_level(Clairvoyance) is None


def test_acquired_talent_is_kept_out_of_character_skills() -> None:
    summary = _summary()
    summary.test_psionic_strength(raw_roll=10, terms_served=0)
    assert summary.psionics is not None

    summary.psionics.attempt_talent_acquisition(Telepathy, psi=10, raw_roll=2)

    assert summary.psionics.talent_level(Telepathy) == 0
    assert summary.skills == []


@pytest.mark.parametrize(
    'pending',
    [
        PendingInitialTrainingChoice(pending_id=(1, 0), instruction='Choose', options=[Psi(Telepathy())]),
        PendingSkillTableChoice(pending_id=(1, 0), instruction='Choose', options=[Psi(Telepathy())]),
        PendingRankBonusChoice(pending_id=(1, 0), instruction='Choose', options=[Psi(Telepathy())], level=1),
    ],
)
def test_possessed_psionic_talent_choice_does_not_request_an_acquisition_roll(pending) -> None:
    projection = _psionic_projection(psionics=Psionics(psionic_talent_skills=[Telepathy()]))

    specs = pending.input_specs(projection)

    assert not any(isinstance(spec, NumberEntry) for spec in specs)


@pytest.mark.parametrize(
    'pending',
    [
        PendingInitialTrainingChoice(pending_id=(1, 0), instruction='Choose', options=[Psi(Telepathy())]),
        PendingSkillTableChoice(pending_id=(1, 0), instruction='Choose', options=[Psi(Telepathy())]),
        PendingRankBonusChoice(pending_id=(1, 0), instruction='Choose', options=[Psi(Telepathy())], level=1),
    ],
)
def test_untrained_psionic_talent_choice_requests_an_acquisition_roll(pending) -> None:
    specs = pending.input_specs(_psionic_projection())

    assert any(isinstance(spec, NumberEntry) for spec in specs)


def test_possessed_psionic_talent_choice_improves_without_a_submitted_roll() -> None:
    projection = _psionic_projection(psionics=Psionics(psionic_talent_skills=[Telepathy()]))
    pending = PendingInitialTrainingChoice(pending_id=(1, 0), instruction='Choose', options=[Psi(Telepathy())])

    event = pending.event_from_form({'skill': Psi(Telepathy()).model_dump_json()})
    event.apply(projection, pending)

    assert projection.summary.psionics is not None
    assert projection.summary.psionics.talent_level(Telepathy) == 1
    assert projection.summary.psionics.talent_acquisition_checks == 0


def test_talent_level_reward_raises_possessed_talent_to_requested_level() -> None:
    summary = _summary()
    summary.characteristics[Chars.PSI] = 9
    summary.psionics = Psionics(psionic_talent_skills=[Telepathy()])
    projection = CharacterProjection(character_id=1, summary=summary)
    handler = PsionicTalentLevelHandler(talent=Telepathy(), level=2)

    handler.apply(projection, Event(handler=handler))

    assert summary.psionics.talent_level(Telepathy) == 2


def test_talent_level_choice_only_offers_possessed_talents_below_requested_level() -> None:
    summary = _summary()
    summary.characteristics[Chars.PSI] = 9
    summary.psionics = Psionics(psionic_talent_skills=[Telepathy(), Clairvoyance(level=Level(value=1))])
    projection = CharacterProjection(character_id=1, summary=summary)
    pending = PendingPsionicTalentLevelChoice(
        pending_id=(1, 0),
        instruction='Choose talent',
        level=1,
    )

    specs = pending.input_specs(projection)

    assert len(specs) == 1
    assert isinstance(specs[0], Select)
    assert [label for label, _ in specs[0].options] == ['Telepathy']


def test_psi_strength_test_establishes_psionics_without_starting_training() -> None:
    projection = CharacterProjection(character_id=1, summary=_summary())
    handler = PsiStrengthTestHandler(roll=10)

    handler.apply(projection, Event(handler=handler))

    assert projection.summary.characteristics[Chars.PSI] == 10
    assert projection.summary.psionics == Psionics()
    assert not any(isinstance(pending, PendingPsionicInstituteTraining) for pending in projection.pending_inputs)


def test_institute_training_offers_each_talent_only_once_even_after_failure() -> None:
    summary = _summary()
    summary.test_psionic_strength(raw_roll=9, terms_served=0)
    projection = CharacterProjection(character_id=1, summary=summary)
    pending = PendingPsionicInstituteTraining(
        pending_id=(1, 0),
        instruction='Train',
        remaining_talents=[Telekinesis(), Clairvoyance()],
    )
    projection.pending_inputs.append(pending)
    event = Event(fulfills=pending.pending_id, handler=PsionicTalentTrainingHandler(talent=Telekinesis(), roll=2))

    projection.fulfill_pending(event)
    event.apply(projection, pending)

    next_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingPsionicInstituteTraining))
    assert [type(talent) for talent in next_pending.remaining_talents] == [Clairvoyance]
    assert projection.summary.psionics is not None
    assert projection.summary.psionics.talent_acquisition_checks == 1


def _started_on(world) -> Event:
    return Event(handler=CharacterStartedHandler(sophont=VILANI, homeworld=world, player='NPC', name='Psi'))


def test_initial_psi_test_is_not_offered_on_an_imperial_birthworld() -> None:
    started = _started_on(MOCK_WORLD)
    projection = replay(1, [started, Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='777707'))])

    assert not any(isinstance(pending, PendingInitialPsiTest) for pending in projection.pending_inputs)


def test_initial_psi_test_is_offered_on_a_non_imperial_birthworld() -> None:
    non_imperial = MOCK_WORLD.model_copy(update={'allegiance': 'NaHu'})

    started = _started_on(non_imperial)
    projection = replay(1, [started, Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='777707'))])

    assert any(isinstance(pending, PendingInitialPsiTest) for pending in projection.pending_inputs)
    assert not any(isinstance(pending, PendingCareerChoice) for pending in projection.pending_inputs)


def test_initial_psi_test_offer_only_asks_whether_to_test() -> None:
    projection = CharacterProjection(character_id=1, summary=_summary())
    pending = PendingInitialPsiTest(pending_id=(1, 0))

    specs = pending.input_specs(projection)

    assert len(specs) == 1
    assert isinstance(specs[0], Select)
    assert [label for label, _ in specs[0].options] == ['Test Psionic Strength', 'Decline']


def test_accepting_initial_psi_test_asks_for_roll_before_career_choice() -> None:
    non_imperial = MOCK_WORLD.model_copy(update={'allegiance': 'NaHu'})
    started = _started_on(non_imperial)
    ucp = Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='777707'))
    events = [
        started,
        ucp,
        Event(fulfills=(ucp.id, 0), handler=InitialPsiTestAcceptedHandler()),
    ]

    projection = replay(1, events)

    assert any(isinstance(pending, PendingInitialPsiStrengthRoll) for pending in projection.pending_inputs)
    assert not any(isinstance(pending, PendingCareerChoice) for pending in projection.pending_inputs)


def test_declining_initial_psi_test_offers_career_choice_without_a_roll() -> None:
    non_imperial = MOCK_WORLD.model_copy(update={'allegiance': 'NaHu'})
    started = _started_on(non_imperial)
    ucp = Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='777707'))
    events = [
        started,
        ucp,
        Event(fulfills=(ucp.id, 0), handler=InitialPsiTestDeclinedHandler()),
    ]

    projection = replay(1, events)

    assert not any(isinstance(pending, PendingInitialPsiStrengthRoll) for pending in projection.pending_inputs)
    assert any(isinstance(pending, PendingCareerChoice) for pending in projection.pending_inputs)


def test_initial_psi_test_establishes_psionics_then_offers_career_choice() -> None:
    non_imperial = MOCK_WORLD.model_copy(update={'allegiance': 'NaHu'})
    started = _started_on(non_imperial)
    ucp = Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='777707'))
    accepted = Event(fulfills=(ucp.id, 0), handler=InitialPsiTestAcceptedHandler())
    events = [
        started,
        ucp,
        accepted,
        Event(fulfills=(accepted.id, 0), handler=InitialPsiTestHandler(roll=9)),
    ]

    projection = replay(1, events)

    assert projection.summary.characteristics[Chars.PSI] == 9
    assert projection.summary.psionics == Psionics()
    assert any(isinstance(pending, PendingCareerChoice) for pending in projection.pending_inputs)


def test_psionic_community_requires_established_psionic_strength() -> None:
    events = [
        (started := _started_on(MOCK_WORLD)),
        Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='777707')),
        Event(handler=PreCareerEntryHandler(precareer=precareer_of_type(PsionicCommunityPreCareer), roll=12)),
    ]

    with pytest.raises(ReplayError, match='not available'):
        replay(1, events)


def test_psionic_community_starts_institute_training_for_an_untrained_psion() -> None:
    projection = CharacterProjection(character_id=1, summary=_summary())
    projection.summary.characteristics[Chars.PSI] = 9
    projection.summary.psionics = Psionics()
    handler = PreCareerEntryHandler(precareer=precareer_of_type(PsionicCommunityPreCareer), roll=12)

    handler.apply(projection, Event(handler=handler))

    assert isinstance(projection.pending_inputs[0], PendingPsionicInstituteTraining)


class TestPsionicTalentDefinition:
    def test_common_talents_and_learning_dms_match_core(self) -> None:
        assert psionic_talent_classes() == (Telepathy, Clairvoyance, Telekinesis, Awareness, Teleportation)
        assert {
            Telepathy: 4,
            Clairvoyance: 3,
            Telekinesis: 2,
            Awareness: 1,
            Teleportation: 0,
        } == PSIONIC_TALENT_LEARNING_DMS
        assert [type(talent) for talent in psionic_talent_instances()] == list(psionic_talent_classes())

    def test_psi_wrapper_round_trips_each_talent_type(self) -> None:
        adapter = TypeAdapter(Psi)

        for talent in psionic_talent_instances():
            restored = adapter.validate_json(adapter.dump_json(Psi(talent)))
            assert type(restored.talent) is type(talent)


class TestPsionicStrength:
    @pytest.mark.parametrize('raw_roll', [1, 13])
    def test_strength_test_rejects_rolls_outside_two_to_twelve(self, raw_roll: int) -> None:
        with pytest.raises(ValueError, match='must be 2-12'):
            Psionics.from_strength_test(raw_roll=raw_roll, terms_served=0)

    @pytest.mark.parametrize(
        ('raw_roll', 'terms_served', 'expected_psi'),
        [(12, 0, 12), (12, 3, 9), (7, 6, 1), (7, 7, 0), (7, 12, 0)],
    )
    def test_strength_is_raw_roll_minus_terms_with_floor_at_zero(
        self, raw_roll: int, terms_served: int, expected_psi: int
    ) -> None:
        psi, psionics = Psionics.from_strength_test(raw_roll=raw_roll, terms_served=terms_served)

        assert psi == expected_psi
        assert (psionics is not None) is (expected_psi > 0)

    def test_retesting_to_zero_removes_existing_psi_and_talents(self) -> None:
        summary = _summary()
        summary.characteristics[Chars.PSI] = 9
        summary.psionics = Psionics(psionic_talent_skills=[Telepathy()])

        summary.test_psionic_strength(raw_roll=2, terms_served=2)

        assert Chars.PSI not in summary.characteristics
        assert summary.psionics is None


class TestTalentAcquisition:
    @pytest.mark.parametrize(
        ('talent_cls', 'expected_total'),
        [
            (Telepathy, 8),
            (Clairvoyance, 7),
            (Telekinesis, 6),
            (Awareness, 5),
            (Teleportation, 4),
        ],
    )
    def test_each_learning_dm_and_previous_check_penalty_is_applied(self, talent_cls, expected_total: int) -> None:
        psionics = Psionics(talent_acquisition_checks=1)

        result = psionics.attempt_talent_acquisition(talent_cls, psi=6, raw_roll=5)

        assert result.total == expected_total
        assert result.success is (expected_total >= 8)
        assert not result.automatic
        assert psionics.talent_acquisition_checks == 2

    def test_non_telepathy_talent_succeeds_at_exactly_eight(self) -> None:
        psionics = Psionics()

        result = psionics.attempt_talent_acquisition(Teleportation, psi=12, raw_roll=6)

        assert result.total == 8
        assert result.success
        assert not result.automatic
        assert psionics.talent_level(Teleportation) == 0

    def test_first_telepathy_attempt_is_automatic_even_when_total_is_below_eight(self) -> None:
        psionics = Psionics()

        result = psionics.attempt_talent_acquisition(Telepathy, psi=0, raw_roll=2)

        assert result.total == 3
        assert result.success
        assert result.automatic

    def test_telepathy_is_not_automatic_after_another_acquisition_check(self) -> None:
        psionics = Psionics(talent_acquisition_checks=1)

        result = psionics.attempt_talent_acquisition(Telepathy, psi=0, raw_roll=2)

        assert result.total == 2
        assert not result.success
        assert not result.automatic

    def test_failed_attempt_counts_but_does_not_add_talent(self) -> None:
        psionics = Psionics()

        result = psionics.attempt_talent_acquisition(Teleportation, psi=6, raw_roll=2)

        assert not result.success
        assert psionics.talent_acquisition_checks == 1
        assert psionics.talent_level(Teleportation) is None

    def test_cannot_attempt_an_already_trained_talent(self) -> None:
        psionics = Psionics(psionic_talent_skills=[Telepathy()])

        with pytest.raises(ValueError, match='Already trained'):
            psionics.attempt_talent_acquisition(Telepathy, psi=9, raw_roll=8)

    @pytest.mark.parametrize('raw_roll', [1, 13])
    def test_acquisition_rejects_rolls_outside_two_to_twelve(self, raw_roll: int) -> None:
        with pytest.raises(ValueError, match='must be 2-12'):
            Psionics().attempt_talent_acquisition(Telekinesis, psi=9, raw_roll=raw_roll)


class TestTalentImprovement:
    def test_increment_improves_possessed_talent_and_caps_at_four(self) -> None:
        psionics = Psionics(psionic_talent_skills=[Telepathy(level=Level(value=3))])

        psionics.increment_talent(Telepathy)
        psionics.increment_talent(Telepathy)

        assert psionics.talent_level(Telepathy) == 4

    def test_increment_rejects_untrained_talent(self) -> None:
        with pytest.raises(ValueError, match='Cannot improve untrained'):
            Psionics().increment_talent(Telepathy)

    def test_raise_talent_never_reduces_existing_level(self) -> None:
        psionics = Psionics(psionic_talent_skills=[Telepathy(level=Level(value=3))])

        psionics.raise_talent_to(Telepathy, 1)

        assert psionics.talent_level(Telepathy) == 3

    @pytest.mark.parametrize('level', [-1, 5])
    def test_raise_talent_rejects_levels_outside_zero_to_four(self, level: int) -> None:
        psionics = Psionics(psionic_talent_skills=[Telepathy()])

        with pytest.raises(ValueError, match='must be 0-4'):
            psionics.raise_talent_to(Telepathy, level)


class TestPsionicHandlers:
    def test_training_handler_acquires_unknown_talent_and_records_result(self) -> None:
        projection = _psionic_projection(psi=9)
        handler = PsionicTalentTrainingHandler(talent=Telekinesis(), roll=5)

        handler.apply(projection, Event(handler=handler))

        assert projection.summary.psionics is not None
        assert projection.summary.psionics.talent_level(Telekinesis) == 0
        assert projection.summary.psionics.talent_acquisition_checks == 1
        assert projection.summary.narrative == ['Psionic training: learned Telekinesis (roll 5, total 8)']

    def test_training_handler_improves_known_talent_without_an_acquisition_check(self) -> None:
        projection = _psionic_projection(psionics=Psionics(psionic_talent_skills=[Telepathy()]))
        handler = PsionicTalentTrainingHandler(talent=Telepathy(), roll=2)

        handler.apply(projection, Event(handler=handler))

        assert projection.summary.psionics is not None
        assert projection.summary.psionics.talent_level(Telepathy) == 1
        assert projection.summary.psionics.talent_acquisition_checks == 0
        assert projection.summary.narrative == ['Psionic training: Telepathy 0 → 1']

    @pytest.mark.parametrize(
        'handler',
        [
            PsionicTalentTrainingHandler(talent=Telepathy(), roll=8),
            PsionicTalentLevelHandler(talent=Telepathy(), level=1),
        ],
    )
    def test_talent_handlers_reject_character_without_psionic_strength(self, handler) -> None:
        projection = CharacterProjection(character_id=1, summary=_summary())

        with pytest.raises(ReplayError, match='without Psionic Strength'):
            handler.apply(projection, Event(handler=handler))


class TestInstituteTraining:
    def test_queue_requires_unattempted_training_and_at_least_one_unknown_talent(self) -> None:
        no_psionics = CharacterProjection(character_id=1, summary=_summary())
        attempted = _psionic_projection(psionics=Psionics(talent_acquisition_checks=1))
        fully_trained = _psionic_projection(psionics=Psionics(psionic_talent_skills=psionic_talent_instances()))
        untrained = _psionic_projection()

        assert not queue_psionic_institute_training(no_psionics, event_id=1)
        assert not queue_psionic_institute_training(attempted, event_id=1)
        assert not queue_psionic_institute_training(fully_trained, event_id=1)
        assert queue_psionic_institute_training(untrained, event_id=1)
        pending = next(p for p in untrained.pending_inputs if isinstance(p, PendingPsionicInstituteTraining))
        assert [type(talent) for talent in pending.remaining_talents] == list(psionic_talent_classes())

    def test_attempt_removes_talent_from_later_choices_and_keeps_other_talents(self) -> None:
        projection = _psionic_projection()
        pending = PendingPsionicInstituteTraining(
            pending_id=(1, 0),
            instruction='Train',
            remaining_talents=[Telepathy(), Telekinesis(), Awareness()],
        )
        projection.pending_inputs.append(pending)
        event = Event(
            id=2,
            fulfills=pending.pending_id,
            handler=PsionicTalentTrainingHandler(talent=Telekinesis(), roll=2),
        )

        projection.fulfill_pending(event)
        event.apply(projection, pending)

        next_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingPsionicInstituteTraining))
        assert [type(talent) for talent in next_pending.remaining_talents] == [Telepathy, Awareness]

    def test_training_attempt_keeps_the_remaining_training_before_other_pending_work(self) -> None:
        projection = _psionic_projection()
        pending = PendingPsionicInstituteTraining(
            pending_id=(1, 0),
            instruction='Train',
            remaining_talents=[Telepathy(), Telekinesis()],
        )
        career_choice = PendingCareerChoice(pending_id=(1, 1), instruction='Choose a career')
        projection.pending_inputs.extend([pending, career_choice])
        event = Event(
            id=2,
            fulfills=pending.pending_id,
            handler=PsionicTalentTrainingHandler(talent=Telepathy(), roll=2),
        )

        projection.fulfill_pending(event)
        event.apply(projection, pending)

        assert isinstance(projection.pending_inputs[0], PendingPsionicInstituteTraining)
        assert projection.pending_inputs[1] is career_choice

        next_training = projection.pending_inputs[0]
        final_event = Event(
            id=3,
            fulfills=next_training.pending_id,
            handler=PsionicTalentTrainingHandler(talent=Telekinesis(), roll=2),
        )
        projection.fulfill_pending(final_event)
        final_event.apply(projection, next_training)

        assert projection.pending_inputs == [career_choice]

    def test_queued_training_precedes_work_already_pending(self) -> None:
        projection = _psionic_projection()
        career_choice = PendingCareerChoice(pending_id=(1, 0), instruction='Choose a career')
        projection.pending_inputs.append(career_choice)

        assert queue_psionic_institute_training(projection, event_id=1, pending_idx=1)

        assert isinstance(projection.pending_inputs[0], PendingPsionicInstituteTraining)
        assert projection.pending_inputs[1] is career_choice

    def test_attempting_final_talent_finishes_sequence_without_another_pending(self) -> None:
        projection = _psionic_projection()
        pending = PendingPsionicInstituteTraining(
            pending_id=(1, 0),
            instruction='Train',
            remaining_talents=[Teleportation()],
        )
        projection.pending_inputs.append(pending)
        event = Event(
            id=2,
            fulfills=pending.pending_id,
            handler=PsionicTalentTrainingHandler(talent=Teleportation(), roll=2),
        )

        projection.fulfill_pending(event)
        event.apply(projection, pending)

        assert not any(isinstance(p, PendingPsionicInstituteTraining) for p in projection.pending_inputs)

    def test_finishing_early_ends_sequence_without_an_acquisition_check(self) -> None:
        projection = _psionic_projection()
        pending = PendingPsionicInstituteTraining(
            pending_id=(1, 0),
            instruction='Train',
            remaining_talents=psionic_talent_instances(),
        )
        projection.pending_inputs.append(pending)
        handler = FinishPsionicInstituteTrainingHandler()
        event = Event(fulfills=pending.pending_id, handler=handler)

        projection.fulfill_pending(event)
        event.apply(projection, pending)

        assert projection.summary.psionics is not None
        assert projection.summary.psionics.talent_acquisition_checks == 0
        assert projection.summary.narrative == ['Psionic institute training complete']
        assert not any(isinstance(p, PendingPsionicInstituteTraining) for p in projection.pending_inputs)


class TestInitialPsionicTesting:
    def test_availability_uses_birthworld_instead_of_current_homeworld(self) -> None:
        non_imperial = MOCK_WORLD.model_copy(update={'allegiance': 'NaHu'})
        summary = CharacterSummary(
            name='Psi',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            birthworld=non_imperial,
        )

        assert initial_psi_test_is_available(CharacterProjection(character_id=1, summary=summary))

    def test_availability_rejects_unsupported_sophont(self) -> None:
        non_imperial = MOCK_WORLD.model_copy(update={'allegiance': 'NaHu'})
        unsupported = Sophont(name='Aslan', ucp_stats=VILANI.ucp_stats)
        summary = CharacterSummary(name='Psi', sophont=unsupported, homeworld=non_imperial)

        assert not initial_psi_test_is_available(CharacterProjection(character_id=1, summary=summary))
