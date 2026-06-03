"""Shared base classes for career-specific pending input types.

Career modules should subclass these and implement the abstract logic.
"""

from typing import Any, Literal

from pydantic import Field

from ceres.character.characteristics import Chars
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.skills import AnySkill, _level_fields
from ceres.character.state import CharacterProjection, PendingInputBase


def _build_career_skill_select_options(
    options: list[AnySkill | Chars],
) -> list[tuple[str, str]]:
    """Build (display_label, form_value) pairs for skill-roll pending inputs."""
    return [
        (
            opt.value if isinstance(opt, Chars) else type(opt).name(),
            opt.value if isinstance(opt, Chars) else type(opt).name(),
        )
        for opt in options
    ]


def _build_skill_choice_select_options(
    projection: CharacterProjection,
    options: list[Any],  # list[AnySkill | AdvancementDmOption]
    level: int | None,
) -> list[tuple[str, str]]:
    """Build (display_label, form_value) pairs for career skill-choice pending inputs.

    Replicates the logic of events._build_skill_select_options without importing private names.
    """
    from ceres.character.careers.career_data import AdvancementDmOption

    results: list[tuple[str, str]] = []
    for opt in options:
        if isinstance(opt, AdvancementDmOption):
            results.append((opt.label(), opt.model_dump_json()))
            continue
        skill_cls = type(opt)
        skill_name = skill_cls.name()
        if level == 0:
            skill = skill_cls()
            from pydantic import TypeAdapter

            adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)
            results.append((skill_name, adapter.dump_json(skill).decode()))
        else:
            choices = projection.skill_choices([skill_cls], level)
            for skill in choices:
                label = skill_name
                fields = _level_fields(skill_cls)
                if len(fields) > 1:
                    spec_names = skill_cls.specialities() if hasattr(skill_cls, 'specialities') else fields
                    for fname, sname in zip(fields, spec_names, strict=False):
                        given = getattr(skill, fname).value
                        if given > 0:
                            label = f'{skill_name} ({sname})'
                            break
                from pydantic import TypeAdapter as _TA

                _adapter: _TA[AnySkill] = _TA(AnySkill)
                results.append((label, _adapter.dump_json(skill).decode()))
    return results


class CareerChoicePendingBase(PendingInputBase):
    """Base for career event/mishap choice pendings.

    Subclass and set kind, instruction, options, and override on_choice().
    """

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.events import CareerChoiceEvent
        from ceres.character.input_specs import form_str

        return CareerChoiceEvent(choice=form_str(form, 'choice', ''), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[Any]:
        return []


class CareerSkillRollPendingBase(PendingInputBase):
    """Base for career skill roll pendings.

    Subclass and set kind, instruction, options (AnySkill | Chars), and override resolve().
    """

    options: list[AnySkill | Chars] = Field(default_factory=list)  # type: ignore[assignment]

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from ceres.character.events import SkillRollEvent
        from ceres.character.input_specs import form_int, form_str

        skill_str = form_str(form, 'skill')
        modified_roll = form_int(form, 'modified_roll', 8)
        try:
            skill: AnySkill | Chars = Chars(skill_str)
        except ValueError:
            from pydantic import TypeAdapter

            adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)
            skill = adapter.validate_python({'type': skill_str})
        return SkillRollEvent(skill=skill, modified_roll=modified_roll, fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[Any]:
        skill_options = _build_career_skill_select_options(self.options)
        return [
            Select(name='skill', label='Skill to roll', options=skill_options),
            NumberEntry(
                name='modified_roll',
                label='Modified roll (2D + skill level + DMs)',
                default=8,
                min=2,
                max=20,
            ),
        ]


class PendingAdvancedTrainingSkillRoll(CareerSkillRollPendingBase):
    """Shared pending for 'advanced training: roll EDU 8+ to increase an existing skill' events."""

    kind: Literal['advanced_training_skill_roll'] = 'advanced_training_skill_roll'
    threshold: int = 8

    def resolve(self, projection: CharacterProjection, event: Any) -> None:
        if event.modified_roll >= self.threshold:
            from ceres.character.events import PendingSkillChoice

            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.0',
                    instruction='Advanced training: increase any existing skill by one level',
                    options=list(projection.summary.skills),
                )
            )


class CareerSkillChoicePendingBase(PendingInputBase):
    """Base for career skill choice pendings (from events/mishaps).

    Subclass and set kind, instruction, options (AnySkill | AdvancementDmOption),
    advancement_precreated, and optionally override on_skill_chosen().
    """

    options: list[Any] = Field(default_factory=list)  # list[AnySkill | AdvancementDmOption]
    advancement_precreated: bool = False

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Any) -> Any:
        from typing import Annotated, cast

        from pydantic import Field as _Field, TypeAdapter

        from ceres.character.careers.career_data import AdvancementDmOption
        from ceres.character.events import AdvancementDmChoiceEvent, SkillChoiceEvent
        from ceres.character.input_specs import form_str
        from ceres.character.skills import AnySkill as _AnySkill

        adv_dm_or_skill_adapter: TypeAdapter[AdvancementDmOption | _AnySkill] = TypeAdapter(
            Annotated[AdvancementDmOption | _AnySkill, _Field(union_mode='left_to_right')]
        )
        parsed = adv_dm_or_skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        if isinstance(parsed, AdvancementDmOption):
            return AdvancementDmChoiceEvent(fulfills=self.id)
        return SkillChoiceEvent(skill=cast(_AnySkill, parsed), fulfills=self.id)

    def input_specs(self, projection: CharacterProjection) -> list[Any]:
        opts = _build_skill_choice_select_options(projection, self.options, None)
        return [Select(name='skill', label='Choose a skill', options=opts)]

    def on_skill_chosen(self, projection: CharacterProjection, event: Any) -> None:
        """Called when a SkillChoiceEvent fulfills this pending input."""
        projection.grant_skill(event.skill)
        if not self.advancement_precreated and projection.summary.current_career is not None:
            from ceres.character.events import career_progress_pending

            career = projection.get_current_career()
            projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
