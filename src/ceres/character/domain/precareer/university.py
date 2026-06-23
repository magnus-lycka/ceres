from typing import ClassVar

from ceres.character.domain import skills as character_skills
from ceres.character.domain.career.career_data import CharCheck
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import PreCareerData, PrecareerSkillEntry
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.skills import (
    AnySkill,
    ArtSkill,
    LanguageSkill,
    ProfessionSkill,
    ScienceSkill,
    skill_instances,
)
from ceres.character.mechanism.event_base import Event


class UniversityPreCareer(PreCareerData):
    name: ClassVar[str] = 'University'
    source: ClassVar[str] = 'Core'
    entry: ClassVar[CharCheck] = CharCheck(characteristic=Chars.EDU, target=6)
    entry_term_dms: ClassVar[dict[int, int]] = {2: -1, 3: -2}
    entry_soc_bonus_min: ClassVar[int] = 9
    entry_soc_bonus: ClassVar[int] = 1
    skill_choices: ClassVar[list[PrecareerSkillEntry]] = [
        PrecareerSkillEntry(skill=character_skills.Admin()),
        PrecareerSkillEntry(skill=character_skills.Advocate()),
        PrecareerSkillEntry(skill=character_skills.Animals()),
        PrecareerSkillEntry(skill=skill_instances(ArtSkill)),
        PrecareerSkillEntry(skill=character_skills.Astrogation()),
        PrecareerSkillEntry(skill=character_skills.Electronics()),
        PrecareerSkillEntry(skill=character_skills.Engineer()),
        PrecareerSkillEntry(skill=skill_instances(LanguageSkill)),
        PrecareerSkillEntry(skill=character_skills.Medic()),
        PrecareerSkillEntry(skill=character_skills.Navigation()),
        PrecareerSkillEntry(skill=skill_instances(ProfessionSkill)),
        PrecareerSkillEntry(skill=skill_instances(ScienceSkill)),
    ]
    graduation: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=6)
    honours_target: ClassVar[int] = 10
    graduation_benefits: ClassVar[list[str]] = [
        'Increase both chosen skills by one level',
        'Increase EDU by an additional +1',
        'DM+1, or DM+2 with honours, to qualify for listed careers',
        'Commission roll before first term of a military career after university',
    ]

    def apply_entry(
        self,
        projection: CharacterProjection,
        event: Event,
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
        event: Event,
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
