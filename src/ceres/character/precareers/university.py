from ceres.character.characteristics import Chars
from ceres.character.effect_enums import EffectType
from ceres.character.events import PendingPreCareerSkillChoice, PreCareerEntryEvent, PreCareerGraduationEvent
from ceres.character.precareers.precareer_data import PreCareerData
from ceres.character.skills import AnySkill, _level_fields
from ceres.character.state import (
    CharacterProjection,
    EffectTrigger,
    ScheduledEffect,
)


class UniversityPreCareer(PreCareerData):
    def apply_entry(
        self,
        projection: CharacterProjection,
        event: PreCareerEntryEvent,
        pending_idx: int,
    ) -> int:
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        skill_opts_0 = _precareer_skill_options(self)
        skill_opts_1 = _precareer_skill_options_level1(self)
        projection.pending_inputs.append(
            PendingPreCareerSkillChoice(
                id=f'{event.id}.{pending_idx}',
                level=0,
                instruction='University: choose one skill at level 0',
                options=skill_opts_0,
            )
        )
        pending_idx += 1
        projection.pending_inputs.append(
            PendingPreCareerSkillChoice(
                id=f'{event.id}.{pending_idx}',
                level=1,
                instruction='University: choose one skill at level 1',
                options=skill_opts_1,
            )
        )
        pending_idx += 1
        return pending_idx

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
        honours: bool,
    ) -> int:
        for skill in projection.summary.precareer_skills:
            projection.increment_skill(skill)
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        dm_amount = 2 if honours else 1
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger=EffectTrigger.QUALIFICATION,
                source_event_id=event.id,
                effect={'type': EffectType.DM, 'amount': dm_amount},
                consume=True,
            )
        )
        projection.summary.problems.append(
            'University graduation: entitled to a commission roll before first military career'
            + (' (DM+2 with honours)' if honours else '')
            + '. Apply manually.'
        )
        return 0


def _precareer_skill_options(precareer: PreCareerData) -> list[AnySkill]:
    seen: set[str] = set()
    result: list[AnySkill] = []
    for entry in precareer.skill_choices:
        for skill in entry.skill_options:
            key = type(skill).name()
            if key not in seen:
                seen.add(key)
                result.append(skill)
    return sorted(result, key=lambda s: type(s).name())


def _precareer_skill_options_level1(precareer: PreCareerData) -> list[AnySkill]:
    """Like _precareer_skill_options but expands specialised skills to per-spec instances at Level(1)."""
    from ceres.character.events import _expand_skill_to_spec_instances

    seen: set[str] = set()
    result: list[AnySkill] = []
    for skill in _precareer_skill_options(precareer):
        for expanded in _expand_skill_to_spec_instances(skill):
            key = _skill_instance_key(expanded)
            if key not in seen:
                seen.add(key)
                result.append(expanded)
    return sorted(result, key=_skill_instance_key)


def _skill_instance_key(skill: AnySkill) -> str:
    skill_cls = type(skill)
    fields = _level_fields(skill_cls)
    active = next((f for f in fields if getattr(skill, f).value > 0), None)
    base = skill_cls.name()
    if active is None:
        return base
    extra = skill_cls.model_fields[active].json_schema_extra or {}
    spec_label = str(extra.get('name') or active.replace('_', ' ').title())
    return f'{base} ({spec_label})'
