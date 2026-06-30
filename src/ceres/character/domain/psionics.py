from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import Field, TypeAdapter

from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.psionics_data import (
    PSIONIC_TALENT_LEARNING_DMS,
    Awareness,
    Clairvoyance,
    Psi,
    Psionics,
    PsionicTalentSkillClass,
    PsionicTalentSkillModels,
    PsionicTalentSkills,
    TalentAcquisitionResult,
    Telekinesis,
    Telepathy,
    Teleportation,
    psionic_talent_classes,
    psionic_talent_instances,
)
from ceres.character.input_specs import InputSpec, NumberEntry, Select, form_int, form_str
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase, PendingInputBase

__all__ = [
    'PSIONIC_TALENT_LEARNING_DMS',
    'Awareness',
    'Clairvoyance',
    'FinishPsionicInstituteTrainingHandler',
    'InitialPsiTestAcceptedHandler',
    'InitialPsiTestDeclinedHandler',
    'InitialPsiTestHandler',
    'PendingInitialPsiStrengthRoll',
    'PendingInitialPsiTest',
    'PendingLifeEventPsionicsRoll',
    'PendingPsionicInstituteTraining',
    'PendingPsionicTalentLevelChoice',
    'Psi',
    'PsiStrengthTestHandler',
    'PsionicTalentLevelHandler',
    'PsionicTalentSkillClass',
    'PsionicTalentSkillModels',
    'PsionicTalentSkills',
    'PsionicTalentTrainingHandler',
    'Psionics',
    'TalentAcquisitionResult',
    'Telekinesis',
    'Telepathy',
    'Teleportation',
    'initial_psi_test_is_available',
    'psionic_talent_classes',
    'psionic_talent_instances',
    'queue_initial_psi_test_if_available',
    'queue_initial_psi_test_or_career_choice',
    'queue_psionic_institute_training',
    'talent_acquisition_roll_required',
]


def talent_acquisition_roll_required(projection: CharacterProjection, options: Sequence[Any]) -> bool:
    psionics = projection.summary.psionics
    return any(
        isinstance(option, Psi) and (psionics is None or psionics.talent_level(type(option.talent)) is None)
        for option in options
    )


class PsionicTalentTrainingHandler(EventHandlerBase):
    kind: Literal['psionic_talent_training'] = 'psionic_talent_training'
    talent: PsionicTalentSkills
    roll: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        psionics = projection.summary.psionics
        if psionics is None:
            raise ReplayError('Cannot train a psionic talent without Psionic Strength')
        talent_cls = type(self.talent)
        existing_level = psionics.talent_level(talent_cls)
        if existing_level is None:
            psi = projection.summary.characteristics.get(Chars.PSI, 0)
            result = psionics.attempt_talent_acquisition(talent_cls, psi=psi, raw_roll=self.roll)
            outcome = 'learned' if result.success else 'failed to learn'
            projection.summary.narrative.append(
                f'Psionic training: {outcome} {talent_cls.name()} (roll {self.roll}, total {result.total})'
            )
        else:
            psionics.increment_talent(talent_cls)
            projection.summary.narrative.append(
                f'Psionic training: {talent_cls.name()} {existing_level} → {psionics.talent_level(talent_cls)}'
            )
        on_psi_chosen = getattr(fulfilled_pending, 'on_psi_chosen', None)
        if on_psi_chosen is not None:
            on_psi_chosen(projection, event)


class PsionicTalentLevelHandler(EventHandlerBase):
    kind: Literal['psionic_talent_level'] = 'psionic_talent_level'
    talent: PsionicTalentSkills
    level: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        psionics = projection.summary.psionics
        if psionics is None:
            raise ReplayError('Cannot improve a psionic talent without Psionic Strength')
        psionics.raise_talent_to(type(self.talent), self.level)


class PendingPsionicTalentLevelChoice(PendingInputBase):
    kind: Literal['psionic_talent_level_choice'] = 'psionic_talent_level_choice'
    level: int

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        talent = _talent_adapter.validate_json(form_str(form, 'talent', '{}'))
        return Event(
            fulfills=self.pending_id,
            handler=PsionicTalentLevelHandler(talent=talent, level=self.level),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        psionics = projection.summary.psionics
        if psionics is None:
            return []
        options = [
            (type(talent).name(), _talent_adapter.dump_json(talent).decode())
            for talent in psionics.psionic_talent_skills
            if talent.level.value < self.level
        ]
        return [Select(name='talent', label='Talent', options=options)]


class FinishPsionicInstituteTrainingHandler(EventHandlerBase):
    kind: Literal['finish_psionic_institute_training'] = 'finish_psionic_institute_training'

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        projection.summary.narrative.append('Psionic institute training complete')


_talent_adapter: TypeAdapter[PsionicTalentSkills] = TypeAdapter(PsionicTalentSkills)


class PendingPsionicInstituteTraining(PendingInputBase):
    kind: Literal['psionic_institute_training'] = 'psionic_institute_training'
    remaining_talents: list[PsionicTalentSkills] = Field(default_factory=list)

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        choice = form_str(form, 'talent', 'finish')
        if choice == 'finish':
            return Event(fulfills=self.pending_id, handler=FinishPsionicInstituteTrainingHandler())
        talent = _talent_adapter.validate_json(choice)
        return Event(
            fulfills=self.pending_id,
            handler=PsionicTalentTrainingHandler(talent=talent, roll=form_int(form, 'roll', 2)),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        psionics = projection.summary.psionics
        if psionics is None:
            return []
        options = [
            (type(talent).name(), _talent_adapter.dump_json(talent).decode()) for talent in self.remaining_talents
        ]
        options.append(('Finish training', 'finish'))
        return [
            Select(name='talent', label='Talent to attempt', options=options),
            NumberEntry(name='roll', label='Psionic talent acquisition roll (2D)', min=2, max=12),
        ]

    def on_psi_chosen(self, projection: CharacterProjection, event: Event) -> None:
        attempted_cls = type(event.talent)
        remaining = [talent for talent in self.remaining_talents if type(talent) is not attempted_cls]
        if remaining:
            projection.pending_inputs.insert(
                0,
                PendingPsionicInstituteTraining(
                    pending_id=(event.id, 0),
                    instruction='Choose a psionic talent to attempt, or finish institute training',
                    remaining_talents=remaining,
                ),
            )


class PsiStrengthTestHandler(EventHandlerBase):
    kind: Literal['psi_strength_test'] = 'psi_strength_test'
    roll: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        psi = projection.summary.test_psionic_strength(
            raw_roll=self.roll,
            terms_served=projection.summary.terms_started_in_pre_and_careers,
        )
        if psi >= 9:
            projection.summary.narrative.append(f'Psionic experience: PSI {psi} — qualifies to take the Psion career')
        elif psi > 0:
            projection.summary.narrative.append(f'Psionic experience: PSI {psi} — no significant psionic talent')
        else:
            projection.summary.narrative.append('Psionic experience: no Psionic Strength remaining')


class PendingLifeEventPsionicsRoll(PendingInputBase):
    kind: Literal['life_event_psionics_roll'] = 'life_event_psionics_roll'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(fulfills=self.pending_id, handler=PsiStrengthTestHandler(roll=form_int(form, 'roll', 2)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll for Psionic Strength test (minus terms served)', min=2, max=12)]


class InitialPsiTestDeclinedHandler(EventHandlerBase):
    kind: Literal['initial_psi_test_declined'] = 'initial_psi_test_declined'

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        from ceres.character.domain.career.career_events import queue_career_choice

        queue_career_choice(projection, event.id, 'Choose a career')


class InitialPsiTestAcceptedHandler(EventHandlerBase):
    kind: Literal['initial_psi_test_accepted'] = 'initial_psi_test_accepted'

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        projection.pending_inputs.append(
            PendingInitialPsiStrengthRoll(
                pending_id=(event.id, 0),
                instruction='Roll 2D for Psionic Strength',
            )
        )


class InitialPsiTestHandler(EventHandlerBase):
    kind: Literal['initial_psi_test'] = 'initial_psi_test'
    roll: int

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        from ceres.character.domain.career.career_events import queue_career_choice

        projection.summary.test_psionic_strength(raw_roll=self.roll, terms_served=0)
        queue_career_choice(projection, event.id, 'Choose a career')


class PendingInitialPsiTest(PendingInputBase):
    kind: Literal['initial_psi_test_pending'] = 'initial_psi_test_pending'
    instruction: str = 'Psionic testing is available. Test Psionic Strength?'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        if form_str(form, 'test', 'no') == 'yes':
            return Event(fulfills=self.pending_id, handler=InitialPsiTestAcceptedHandler())
        return Event(fulfills=self.pending_id, handler=InitialPsiTestDeclinedHandler())

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Select(name='test', label='Psionic testing', options=[('Test Psionic Strength', 'yes'), ('Decline', 'no')]),
        ]


class PendingInitialPsiStrengthRoll(PendingInputBase):
    kind: Literal['initial_psi_strength_roll'] = 'initial_psi_strength_roll'

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(fulfills=self.pending_id, handler=InitialPsiTestHandler(roll=form_int(form, 'roll', 2)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [NumberEntry(name='roll', label='2D roll for Psionic Strength test', min=2, max=12)]


def initial_psi_test_is_available(projection: CharacterProjection) -> bool:
    sophont = projection.summary.sophont
    birthworld = projection.summary.birthworld or projection.summary.homeworld
    if sophont is None or birthworld is None:
        return False
    return sophont.name in {'Humaniti', 'Vilani'} and not birthworld.allegiance.startswith('Im')


def queue_initial_psi_test_or_career_choice(projection: CharacterProjection, event_id: int) -> None:
    if queue_initial_psi_test_if_available(projection, event_id):
        return
    from ceres.character.domain.career.career_events import queue_career_choice

    queue_career_choice(projection, event_id, 'Choose a career')


def queue_initial_psi_test_if_available(projection: CharacterProjection, event_id: int) -> bool:
    if not initial_psi_test_is_available(projection):
        return False
    projection.pending_inputs.append(PendingInitialPsiTest(pending_id=(event_id, 0)))
    return True


def queue_psionic_institute_training(
    projection: CharacterProjection,
    event_id: int,
    pending_idx: int = 0,
) -> bool:
    psionics = projection.summary.psionics
    if psionics is None or psionics.talent_acquisition_checks > 0:
        return False
    if all(psionics.talent_level(talent_cls) is not None for talent_cls in psionic_talent_classes()):
        return False
    projection.pending_inputs.insert(
        0,
        PendingPsionicInstituteTraining(
            pending_id=(event_id, pending_idx),
            instruction='Choose a psionic talent to attempt, or finish institute training',
            remaining_talents=psionic_talent_instances(),
        ),
    )
    return True
