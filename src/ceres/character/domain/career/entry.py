from typing import Any, Literal

from pydantic import Field

from ceres.character.domain.career.career_data import AssignmentData, CareerData
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.input_specs import (
    AssignmentOption,
    CareerChoice,
    CareerOption,
    InfoText,
    InputSpec,
    NumberEntry,
    QualificationTarget,
    Reference,
    Select,
    form_int,
    form_str,
)
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import PendingInputBase


class CareerEntryHandler(EventHandlerBase):
    kind: Literal['career_event'] = 'career_event'
    career: CareerData
    assignment: AssignmentData
    qualification_roll: int

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        self.career.start_career(projection, self.assignment, event.id, self.qualification_roll)


class DraftHandler(EventHandlerBase):
    kind: Literal['draft_event'] = 'draft_event'
    career: CareerData
    assignment: AssignmentData | None = None

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        if projection.summary.drafted:
            raise ReplayError('A character may only enter the draft once')
        self.career.start_draft(projection, event.id, self.assignment)


class DraftAssignmentHandler(EventHandlerBase):
    kind: Literal['draft_assignment'] = 'draft_assignment'
    career: CareerData
    assignment: AssignmentData

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        self.career.start_draft(projection, event.id, self.assignment)


class PendingCareerChoice(PendingInputBase):
    kind: Literal['career_choice'] = 'career_choice'
    options: list[CareerData] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Event:
        from ceres.character.domain.character_start import FinishCreationHandler
        from ceres.character.domain.precareer.loader import precareer_from_user_input_name
        from ceres.character.domain.precareer.precareer_events import PreCareerEntryHandler

        kind = form_str(form, 'kind', '')
        if kind == 'finish_creation':
            return Event(fulfills=self.pending_id, handler=FinishCreationHandler())
        if kind == 'precareer_entry':
            precareer_name = form_str(form, 'precareer', 'University')
            precareer = precareer_from_user_input_name(precareer_name)
            if precareer is None:
                raise ReplayError(f'Unknown pre-career {precareer_name!r}')
            return Event(
                fulfills=self.pending_id,
                handler=PreCareerEntryHandler(
                    precareer=precareer,
                    roll=form_int(form, 'roll', 7),
                ),
            )
        career_name = form_str(form, 'career')
        assignment_name = form_str(form, 'assignment')
        career = next((career for career in self.options if career.name == career_name), None)
        if career is None:
            raise ReplayError(f'Unknown career {career_name!r}')
        assignment = career.assignment(assignment_name)
        if assignment is None:
            raise ReplayError(f'Unknown assignment {assignment_name!r} for career {career_name!r}')
        return Event(
            fulfills=self.pending_id,
            handler=CareerEntryHandler(
                career=career,
                assignment=assignment,
                qualification_roll=form_int(form, 'roll', 2),
            ),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            CareerChoice(
                career_options=[
                    CareerOption(
                        name=career.name,
                        description=career.description,
                        qualification=QualificationTarget(
                            characteristic=career.qualification.characteristic.value,
                            target=career.qualification.target,
                        ),
                        assignments=[
                            AssignmentOption(name=assignment.name, description=assignment.description)
                            for assignment in career.assignments
                        ],
                    )
                    for career in self.options
                ],
                can_finish=bool(projection.summary.career_terms),
            )
        ]


class PendingDraftChoice(PendingInputBase):
    kind: Literal['draft_choice'] = 'draft_choice'
    can_draft: bool = True

    def event_from_form(self, form: Any) -> Event:
        from ceres.character.domain.career.draft import build_draft_table, get_draft_alternative
        from ceres.character.domain.career.loader import load_careers

        careers = load_careers()
        if form_str(form, 'choice', 'alternative') == 'draft':
            table = build_draft_table(None, careers)
            roll = form_int(form, 'roll', 1)
            career = table[max(0, min(roll, len(table)) - 1)]
            return Event(fulfills=self.pending_id, handler=DraftHandler(career=career))

        alternative = get_draft_alternative(None, careers)
        if alternative is None:
            raise ReplayError('No draft alternative available')
        default_assignment = alternative.assignments[0].name
        assignment_name = form_str(form, 'assignment', default_assignment)
        assignment = alternative.assignment(assignment_name)
        if assignment is None:
            raise ReplayError(f'Unknown assignment {assignment_name!r} for {alternative.name!r}')
        return Event(
            fulfills=self.pending_id,
            handler=CareerEntryHandler(career=alternative, assignment=assignment, qualification_roll=2),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        from ceres.character.domain.career.draft import build_draft_table, get_draft_alternative
        from ceres.character.domain.career.loader import load_careers

        careers = load_careers()
        alternative = get_draft_alternative(projection.summary, careers)
        specs: list[InputSpec] = []

        if self.can_draft:
            table = build_draft_table(projection.summary, careers)
            table_text = ' · '.join(f'{i + 1} {c.name}' for i, c in enumerate(table))
            specs.append(InfoText(text=f'Draft table: {table_text}'))
            choice_options: list[tuple[str, str]] = [('Submit to the draft', 'draft')]
            if alternative is not None:
                choice_options.append((f'Become a {alternative.name}', 'alternative'))
            specs.append(Select(name='choice', label='Choice', options=choice_options))
            specs.append(NumberEntry(name='roll', label='1D roll', min=1, max=len(table)))

        if alternative is not None:
            specs.append(
                Select(
                    name='assignment',
                    label=f'{alternative.name} assignment',
                    options=[(a.name, a.name) for a in alternative.assignments],
                )
            )

        return specs


class PendingDraftAssignmentChoice(PendingInputBase):
    kind: Literal['draft_assignment_choice'] = 'draft_assignment_choice'
    career: CareerData

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Event:
        assignment_name = form_str(form, 'assignment')
        assignment = self.career.assignment(assignment_name)
        if assignment is None:
            raise ReplayError(f'Unknown assignment {assignment_name!r} for {self.career.name!r}')
        return Event(
            fulfills=self.pending_id,
            handler=DraftAssignmentHandler(career=self.career, assignment=assignment),
        )

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        return [
            Reference(name='career', value=self.career.name),
            Select(
                name='assignment',
                label='Assignment',
                options=[(assignment, assignment) for assignment in self.career.draft_assignments],
            ),
        ]


def queue_career_choice_indexed(
    projection: CharacterProjection,
    event_id: int,
    idx: int,
    instruction: str = 'Choose a career',
) -> None:
    from ceres.character.domain.career.loader import selectable_careers

    if projection.forced_next_career:
        forced = projection.forced_next_career
        projection.forced_next_career = None
        options = [forced]
        instruction = f'Next career: {forced.name} (mandatory)'
    else:
        options = sorted(selectable_careers(projection), key=lambda career: career.name)
    projection.pending_inputs.append(
        PendingCareerChoice(
            pending_id=(event_id, idx),
            instruction=instruction,
            options=options,
        )
    )


def queue_career_choice(projection: CharacterProjection, event_id: int, instruction: str = 'Choose a career') -> None:
    queue_career_choice_indexed(projection, event_id, 0, instruction)
