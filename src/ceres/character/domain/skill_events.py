from collections.abc import Mapping, Sequence
from typing import Literal, cast

from pydantic import Field, TypeAdapter

from ceres.character.domain.career.career_data import AdvancementDmOption, SkillTableItem
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.skills import AnySkill
from ceres.character.input_specs import InputSpec, Select, form_str
from ceres.character.mechanism.event_base import Event, EventHandlerBase, PendingInputBase

_skill_adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)
_advancement_dm_or_skill_adapter: TypeAdapter[AdvancementDmOption | AnySkill] = TypeAdapter(
    AdvancementDmOption | AnySkill
)


def build_skill_select_options(
    projection: CharacterProjection,
    options: Sequence[SkillTableItem | AdvancementDmOption],
    level: int | None,
) -> list[tuple[str, str]]:
    """Flatten each option's own (label, form_value) pairs into one select list."""
    return [pair for option in options for pair in option.select_options(projection, level)]


class SkillChoiceHandler(EventHandlerBase):
    kind: Literal['skill_choice'] = 'skill_choice'
    skill: AnySkill

    model_config = {'arbitrary_types_allowed': True}

    def apply(
        self, projection: CharacterProjection, event: Event, fulfilled_pending: PendingInputBase | None = None
    ) -> None:
        on_skill_chosen = getattr(fulfilled_pending, 'on_skill_chosen', None)
        if on_skill_chosen is not None:
            on_skill_chosen(projection, event)
            return
        projection.grant_skill(self.skill)
        if projection.summary.current_career is not None:
            from ceres.character.domain.career.career_events import career_progress_pending

            projection.queue_deferred(career_progress_pending(projection, projection.get_current_career(), event.id))


class PendingSkillChoice(PendingInputBase):
    kind: Literal['skill_choice'] = 'skill_choice'
    options: list[AnySkill] = Field(default_factory=list)
    level: int | None = None

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        parsed = _advancement_dm_or_skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        if isinstance(parsed, AdvancementDmOption):
            return Event(fulfills=self.pending_id, handler=parsed.chosen_handler())
        return Event(fulfills=self.pending_id, handler=SkillChoiceHandler(skill=cast(AnySkill, parsed)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = build_skill_select_options(projection, self.options, self.level)
        return [Select(name='skill', label='Choose a skill', options=options)]
