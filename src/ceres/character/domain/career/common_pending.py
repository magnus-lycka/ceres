"""Shared base classes for career-specific pending input types.

Career modules should subclass these and implement the abstract logic.
"""

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import Field

from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skill_events import PendingSkillChoice
from ceres.character.domain.skills import AnySkill, Level, level_fields, skill_instances
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.event_base import Event, PendingInputBase


def append_increment_existing_skill_pending(
    projection: CharacterProjection,
    pending_id: tuple[int, int],
    instruction: str,
) -> None:
    projection.pending_inputs.append(
        PendingSkillChoice(
            pending_id=pending_id,
            instruction=instruction,
            options=list(projection.summary.skills),
        )
    )


def _build_career_skill_select_options(
    options: list[AnySkill | Chars],
) -> list[tuple[str, str]]:
    """Build (display_label, form_value) pairs for skill-roll pending inputs."""
    return [
        (
            opt.value if isinstance(opt, Chars) else type(opt).name(),
            opt.value if isinstance(opt, Chars) else type(opt).model_fields['kind'].default,
        )
        for opt in options
    ]


def _build_skill_choice_select_options(
    projection: CharacterProjection,
    options: list[Any],  # list[AnySkill | AdvancementDmOption]
    level: int | None,
) -> list[tuple[str, str]]:
    """Build (display_label, form_value) pairs for career skill-choice pending inputs.

    If an option has preset specialty fields (non-zero values), only those specialties
    are offered at the preset level (or the given level if provided).
    """
    from pydantic import TypeAdapter as _TA

    from ceres.character.domain.career.career_data import AdvancementDmOption

    _adapter: _TA[AnySkill] = _TA(AnySkill)
    results: list[tuple[str, str]] = []
    for opt in options:
        if isinstance(opt, AdvancementDmOption):
            results.append((opt.label(), opt.model_dump_json()))
            continue
        skill_cls = type(opt)
        skill_name = skill_cls.name()
        fields = level_fields(skill_cls)
        active_fields = [f for f in fields if getattr(opt, f).value > 0]
        if active_fields:
            existing = next((s for s in projection.summary.skills if type(s) is skill_cls), None)
            spec_names = skill_cls.specialities() if hasattr(skill_cls, 'specialities') else fields
            for fname, sname in zip(fields, spec_names, strict=False):
                if fname not in active_fields:
                    continue
                preset_level = getattr(opt, fname).value
                current = getattr(existing, fname).value if existing else 0
                target = level if level is not None else preset_level
                if current < target:
                    skill = skill_cls(**{fname: Level(value=target)})
                    label = f'{skill_name} ({sname})' if len(fields) > 1 else skill_name
                    results.append((label, _adapter.dump_json(skill).decode()))
        else:
            choices = projection.skill_choices([skill_cls], level)
            for skill in choices:
                label = skill_name
                if len(fields) > 1:
                    spec_names = skill_cls.specialities() if hasattr(skill_cls, 'specialities') else fields
                    for fname, sname in zip(fields, spec_names, strict=False):
                        given = getattr(skill, fname).value
                        if given > 0:
                            label = f'{skill_name} ({sname})'
                            break
                results.append((label, _adapter.dump_json(skill).decode()))
    return results


class CareerSkillRollPendingBase(PendingInputBase):
    """Base for career skill roll pendings.

    Subclass and set kind, instruction, options (AnySkill | Chars), and override resolve().
    """

    options: list[AnySkill | Chars] = Field(default_factory=list)

    model_config = {'arbitrary_types_allowed': True}

    def event_from_form(self, form: Mapping[str, str]) -> Any:
        from ceres.character.domain.career.career_events import SkillRollHandler
        from ceres.character.input_specs import form_int, form_str

        skill_str = form_str(form, 'skill')
        modified_roll = form_int(form, 'modified_roll', 8)
        try:
            skill: AnySkill | Chars = Chars(skill_str)
        except ValueError:
            from pydantic import TypeAdapter

            adapter: TypeAdapter[AnySkill] = TypeAdapter(AnySkill)
            skill = adapter.validate_python({'kind': skill_str})
        return Event(fulfills=self.pending_id, handler=SkillRollHandler(skill=skill, modified_roll=modified_roll))

    def input_specs(self, projection: CharacterProjection) -> list[Any]:
        skill_options = _build_career_skill_select_options(self.options)
        return [
            Select(name='skill', label='Skill to roll', options=skill_options),
            NumberEntry(
                name='modified_roll',
                label='Modified roll (2D + skill level + DMs)',
                min=2,
                max=20,
            ),
        ]


class PendingAdvancedTrainingSkillRoll(CareerSkillRollPendingBase):
    """Shared pending for 'advanced training: roll EDU 8+ to increase an existing skill' events."""

    kind: Literal['advanced_training_skill_roll'] = 'advanced_training_skill_roll'
    threshold: int = 8

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        if event.modified_roll >= self.threshold:
            append_increment_existing_skill_pending(
                projection,
                (event.id, 0),
                'Advanced training: increase any existing skill by one level',
            )


class PendingAnySkillAtLevelOnSuccessRoll(CareerSkillRollPendingBase):
    """Shared pending for 'roll EDU N+ to gain any one skill of your choice at level 1' events."""

    kind: Literal['any_skill_at_level_on_success_roll'] = 'any_skill_at_level_on_success_roll'
    threshold: int = 8
    success_instruction: str

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        if event.modified_roll >= self.threshold:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, 0),
                    instruction=self.success_instruction,
                    options=skill_instances(AnySkill),
                    level=1,
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

    def event_from_form(self, form: Mapping[str, str]) -> Any:
        from typing import Annotated, cast

        from pydantic import Field as _Field, TypeAdapter

        from ceres.character.domain.career.career_data import AdvancementDmOption
        from ceres.character.domain.career.career_events import AdvancementDmChoiceHandler, SkillChoiceHandler
        from ceres.character.domain.skills import AnySkill as _AnySkill
        from ceres.character.input_specs import form_str

        adv_dm_or_skill_adapter: TypeAdapter[AdvancementDmOption | _AnySkill] = TypeAdapter(
            Annotated[AdvancementDmOption | _AnySkill, _Field(union_mode='left_to_right')]
        )
        parsed = adv_dm_or_skill_adapter.validate_json(form_str(form, 'skill', '{}'))
        if isinstance(parsed, AdvancementDmOption):
            return Event(fulfills=self.pending_id, handler=AdvancementDmChoiceHandler())
        return Event(fulfills=self.pending_id, handler=SkillChoiceHandler(skill=cast(_AnySkill, parsed)))

    def input_specs(self, projection: CharacterProjection) -> list[Any]:
        opts = _build_skill_choice_select_options(projection, self.options, None)
        return [Select(name='skill', label='Choose a skill', options=opts)]

    def on_skill_chosen(self, projection: CharacterProjection, event: Event) -> None:
        """Called when a SkillChoiceEvent fulfills this pending input."""
        projection.grant_skill(event.skill)
        if not self.advancement_precreated and projection.summary.current_career is not None:
            from ceres.character.domain.career.career_events import career_progress_pending

            career = projection.get_current_career()
            projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
