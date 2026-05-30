from ceres.character.characteristics import Chars
from ceres.character.events import PreCareerEntryEvent, PreCareerGraduationEvent
from ceres.character.precareers.precareer_data import PreCareerData
from ceres.character.projection import CharacterProjection, PendingPreCareerSkillChoice, ScheduledEffect
from ceres.character.skills import skill_names_for_category


class UniversityPreCareer(PreCareerData):
    def apply_entry(
        self,
        projection: CharacterProjection,
        event: PreCareerEntryEvent,
        pending_idx: int,
    ) -> int:
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        skill_opts = _precareer_skill_options(self)
        projection.pending_inputs.append(
            PendingPreCareerSkillChoice(
                id=f'{event.id}.{pending_idx}',
                level=0,
                instruction='University: choose one skill at level 0',
                options=skill_opts,
            )
        )
        pending_idx += 1
        projection.pending_inputs.append(
            PendingPreCareerSkillChoice(
                id=f'{event.id}.{pending_idx}',
                level=1,
                instruction='University: choose one skill at level 1',
                options=skill_opts,
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
        for skill_name in projection.summary.precareer_skills:
            projection.increment_skill(skill_name)
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        dm_amount = 2 if honours else 1
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='qualification',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': dm_amount},
                consume=True,
            )
        )
        projection.summary.problems.append(
            'University graduation: entitled to a commission roll before first military career'
            + (' (DM+2 with honours)' if honours else '')
            + '. Apply manually.'
        )
        return 0


def _precareer_skill_options(precareer: PreCareerData) -> list[str]:
    opts: list[str] = []
    for entry in precareer.skill_choices:
        if entry.choices:
            opts.extend(entry.choices)
        elif entry.skill:
            expanded = skill_names_for_category(entry.skill)
            if expanded:
                opts.extend(expanded)
            else:
                opts.append(entry.skill)
    return sorted(set(opts))
