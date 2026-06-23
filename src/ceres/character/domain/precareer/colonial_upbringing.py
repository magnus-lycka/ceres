from typing import ClassVar

from ceres.character.domain import skills as character_skills
from ceres.character.domain.career.career_data import CharCheck
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import PreCareerData, PrecareerSkillEntry
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.skills import AnySkill, JackOfAllTrades, Leadership, Level, ProfessionSkill, skill_instances
from ceres.character.mechanism.event_base import Event


class ColonialUprbringingPreCareer(PreCareerData):
    name: ClassVar[str] = 'Colonial Upbringing'
    source: ClassVar[str] = 'Companion'
    entry_requirement: ClassVar[str] = 'Automatic if homeworld is TL8-'
    skill_choices: ClassVar[list[PrecareerSkillEntry]] = [
        PrecareerSkillEntry(skill=character_skills.Animals(), level=0),
        PrecareerSkillEntry(skill=character_skills.Athletics(), level=0),
        PrecareerSkillEntry(skill=character_skills.Drive(), level=0),
        PrecareerSkillEntry(skill=character_skills.GunCombat(), level=0),
        PrecareerSkillEntry(skill=character_skills.Mechanic(), level=0),
        PrecareerSkillEntry(skill=character_skills.Medic(), level=0),
        PrecareerSkillEntry(skill=character_skills.Navigation(), level=0),
        PrecareerSkillEntry(skill=character_skills.Recon(), level=0),
        PrecareerSkillEntry(skill=skill_instances(ProfessionSkill), level=0),
        PrecareerSkillEntry(skill=character_skills.Seafarer(), level=0),
        PrecareerSkillEntry(skill=character_skills.Survival(), level=1),
    ]
    graduation: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=8)
    graduation_dms: ClassVar[dict[str, int]] = {'END_8+': 1}
    honours_target: ClassVar[int] = 12
    graduation_benefits: ClassVar[list[str]] = [
        'Increase one skill already gained at level 0 to level 1',
        'Gain any two other listed skills at level 1 or increase one skill already possessed',
        'Gain Jack-of-all-Trades 1',
        'Honours graduates gain Leadership 1 and may increase another level 0 skill to level 1',
        'Increase END by +1 and decrease EDU by -D3',
        'Age is 22+2D3 when entering the first career',
    ]

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: Event,
        honours: bool,
    ) -> int:
        pending_idx = 0
        skill_pool: list[AnySkill] = []
        for entry in self.skill_choices:
            if entry.skill:
                skill_pool.extend(entry.skill_options)
        for i in range(3):
            projection.pending_inputs.append(
                PendingPreCareerSkillChoice(
                    pending_id=(event.id, pending_idx),
                    level=1,
                    instruction=f'Colonial graduation: choose skill {i + 1} of 3 at level 1',
                    options=skill_pool,
                )
            )
            pending_idx += 1
        projection.grant_skill(JackOfAllTrades(level=Level(value=1)))
        if honours:
            projection.grant_skill(Leadership(level=Level(value=1)))
            projection.pending_inputs.append(
                PendingPreCareerSkillChoice(
                    pending_id=(event.id, pending_idx),
                    level=1,
                    instruction='Colonial graduation (honours): choose one additional skill at level 1',
                    options=skill_pool,
                )
            )
            pending_idx += 1
        projection.summary.characteristics[Chars.END] = projection.summary.characteristics.get(Chars.END, 0) + 1
        projection.summary.problems.append('Colonial Upbringing graduation: decrease EDU by D3. Apply manually.')
        projection.summary.problems.append(
            'Colonial Upbringing graduation: total starting age is 22+2D3; '
            'add 2D3 extra years to current age. Apply manually.'
        )
        return pending_idx
