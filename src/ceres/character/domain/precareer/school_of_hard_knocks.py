from typing import ClassVar, Literal

from ceres.character.domain.career.career_data import CharCheck
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import PreCareerData, PrecareerSkillEntry, PreCareerTerm
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.skills import (
    AnySkill,
    Athletics,
    Carouse,
    Deception,
    Drive,
    Gambler,
    GunCombat,
    Level,
    Melee,
    Persuade,
    Stealth,
    Streetwise,
)
from ceres.character.mechanism.event_base import Event


class SchoolOfHardKnocksPreCareer(PreCareerData):
    name: ClassVar[str] = 'School of Hard Knocks'
    source: ClassVar[str] = 'Companion'
    entry_requirement: ClassVar[str] = 'Automatic if SOC 6-'
    skill_choices: ClassVar[list[PrecareerSkillEntry]] = [
        PrecareerSkillEntry(skill=Streetwise(), level=1),
        PrecareerSkillEntry(skill=Athletics(), level=0),
        PrecareerSkillEntry(skill=Deception(), level=0),
        PrecareerSkillEntry(skill=Drive(), level=0),
        PrecareerSkillEntry(skill=Gambler(), level=0),
        PrecareerSkillEntry(skill=Melee(), level=0),
        PrecareerSkillEntry(skill=Persuade(), level=0),
        PrecareerSkillEntry(skill=Stealth(), level=0),
    ]
    entry_pick_count: ClassVar[int] = 2
    graduation: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=7)
    graduation_dms: ClassVar[dict[str, int]] = {'END_9+': 1}
    honours_target: ClassVar[int] = 11
    graduation_benefits: ClassVar[list[str]] = [
        'Gain any three other listed skills at level 0',
        'Gain Gun Combat 0',
        'Honours graduates gain Carouse 1 and may increase another level 0 skill to level 1',
        'Decrease SOC by -1',
        'DM-2 on promotion or commission checks in first career unless leaving by choice',
    ]

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: Event,
        honours: bool,
    ) -> int:
        pending_idx = 0
        choice_pool: list[AnySkill] = [
            skill for entry in self.skill_choices if entry.skill and entry.level == 0 for skill in entry.skill_options
        ]
        for i in range(3):
            projection.pending_inputs.append(
                PendingPreCareerSkillChoice(
                    pending_id=(event.id, pending_idx),
                    level=0,
                    instruction=f'School of Hard Knocks graduation: choose skill {i + 1} of 3 at level 0',
                    options=choice_pool,
                )
            )
            pending_idx += 1
        projection.grant_skill(GunCombat())
        if honours:
            projection.grant_skill(Carouse(level=Level(value=1)))
            projection.pending_inputs.append(
                PendingPreCareerSkillChoice(
                    pending_id=(event.id, pending_idx),
                    level=1,
                    instruction='School of Hard Knocks graduation (honours): raise one listed skill to level 1',
                    options=choice_pool,
                )
            )
            pending_idx += 1
        projection.summary.characteristics[Chars.SOC] = max(0, projection.summary.characteristics.get(Chars.SOC, 0) - 1)
        projection.summary.problems.append(
            'School of Hard Knocks graduation: DM-2 on all commission and promotion checks in first career '
            '(unless you leave that career by choice). Apply manually.'
        )
        return pending_idx


class SchoolOfHardKnocksTerm(PreCareerTerm):
    kind: Literal['school_of_hard_knocks'] = 'school_of_hard_knocks'


SchoolOfHardKnocksPreCareer.term_class = SchoolOfHardKnocksTerm
