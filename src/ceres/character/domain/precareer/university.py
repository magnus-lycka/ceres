from typing import Any

from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.skills import AnySkill
from ceres.character.mechanism.character_state import CharacterProjection


class UniversityPreCareer(PreCareerData):
    def apply_entry(
        self,
        projection: CharacterProjection,
        event: Any,
        pending_idx: int,
    ) -> int:
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        skill_opts = _precareer_skill_options(self)
        projection.pending_inputs.append(
            PendingPreCareerSkillChoice(
                pending_id=(event.id, pending_idx),
                level=0,
                instruction='University: choose one skill at level 0',
                options=skill_opts,
            )
        )
        pending_idx += 1
        projection.pending_inputs.append(
            PendingPreCareerSkillChoice(
                pending_id=(event.id, pending_idx),
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
        event: Any,
        honours: bool,
    ) -> int:
        for skill in projection.summary.precareer_skills:
            projection.increment_skill(skill)
        projection.summary.characteristics[Chars.EDU] = projection.summary.characteristics.get(Chars.EDU, 0) + 1
        dm_amount = 2 if honours else 1
        projection.pending_qualification_dm += dm_amount
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
