from collections.abc import Mapping, Sequence
from typing import Any, Literal, cast

from pydantic import Field, TypeAdapter

from ceres.character.domain.career.advancement import AdvancementDmChoiceHandler
from ceres.character.domain.career.career_data import AdvancementDmOption, CareerSkillOption
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.psionics import Psi
from ceres.character.domain.skills import AnySkill, level_fields
from ceres.character.input_specs import InputSpec, Select, form_str
from ceres.character.mechanism.event_base import Event, EventHandlerBase
from ceres.character.mechanism.pending_input import PendingInputBase

_skill_adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)
_advancement_dm_or_skill_adapter: TypeAdapter[AdvancementDmOption | AnySkill] = TypeAdapter(
    AdvancementDmOption | AnySkill
)


def skill_option_label(option: Any) -> str:
    if isinstance(option, AdvancementDmOption):
        return option.label()
    if isinstance(option, Psi):
        return type(option.talent).name()
    skill_cls = type(option)
    fields = level_fields(skill_cls)
    if len(fields) > 1:
        active = next((field for field in fields if getattr(option, field).value > 0), None)
        if active is not None:
            extra = skill_cls.model_fields[active].json_schema_extra or {}
            specialisation = str(extra.get('name') or active.replace('_', ' ').title())
            return f'{skill_cls.name()} ({specialisation})'
    return skill_cls.name()


def build_skill_select_options(
    projection: CharacterProjection,
    options: Sequence[CareerSkillOption | AdvancementDmOption],
    level: int | None,
) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for option in options:
        if isinstance(option, AdvancementDmOption):
            results.append((option.label(), option.model_dump_json()))
            continue
        if isinstance(option, Psi):
            results.append((type(option.talent).name(), option.model_dump_json()))
            continue
        skill_cls = type(option)
        skill_name = skill_cls.name()
        if level == 0:
            results.append((skill_name, _skill_adapter.dump_json(skill_cls()).decode()))
            continue
        fields = level_fields(skill_cls)
        restricted_fields = {field for field in fields if getattr(option, field).value > 0}
        for skill in projection.skill_choices([skill_cls], level):
            if restricted_fields and not any(getattr(skill, field).value > 0 for field in restricted_fields):
                continue
            label = skill_name
            if len(fields) > 1:
                for field, specialisation in zip(fields, skill_cls.specialities(), strict=False):
                    if getattr(skill, field).value > 0:
                        label = f'{skill_name} ({specialisation})'
                        break
            results.append((label, _skill_adapter.dump_json(skill).decode()))
    return results


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

            projection.pending_inputs.append(
                career_progress_pending(projection, projection.get_current_career(), event.id)
            )


class PendingSkillChoice(PendingInputBase):
    kind: Literal['skill_choice'] = 'skill_choice'
    options: list[AnySkill] = Field(default_factory=list)
    level: int | None = None

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Mapping[str, str]) -> Event:
        parsed = _advancement_dm_or_skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        if isinstance(parsed, AdvancementDmOption):
            return Event(fulfills=self.pending_id, handler=AdvancementDmChoiceHandler())
        return Event(fulfills=self.pending_id, handler=SkillChoiceHandler(skill=cast(AnySkill, parsed)))

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        options = build_skill_select_options(projection, self.options, self.level)
        return [Select(name='skill', label='Choose a skill', options=options)]
