from collections.abc import Mapping
from typing import Literal

from pydantic import Field, SerializeAsAny

from ceres.character.domain.character_state import CharacterProjection
from ceres.character.input_specs import InputSpec, Select, form_str
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import ChoiceBase, Event, EventHandlerBase, PendingInputBase


class ChoiceHandler(EventHandlerBase):
    kind: Literal['career_decision'] = 'career_decision'
    choice: str

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        if fulfilled_pending is None:
            raise ReplayError('Choice event has no matching pending input')
        if not isinstance(fulfilled_pending, PendingChoices):
            raise ReplayError(f'Choice event fulfilled by unexpected pending type {type(fulfilled_pending).__name__!r}')
        selected = next((choice for choice in fulfilled_pending.choices if choice.kind == self.choice), None)
        if selected is None:
            raise ReplayError(f'Unknown choice {self.choice!r}')
        selected.handle(projection, event)


class PendingChoices(PendingInputBase):
    kind: Literal['choices'] = 'choices'
    choices: list[SerializeAsAny[ChoiceBase]] = Field(default_factory=list)

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        return Event(fulfills=self.pending_id, handler=ChoiceHandler(choice=form_str(form, 'choice', '')))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = [(choice.label, choice.kind) for choice in self.choices]
        return [Select(name='choice', label=self.instruction, options=options)]
