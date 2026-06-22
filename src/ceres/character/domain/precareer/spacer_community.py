from typing import Any, ClassVar

from ceres.character.domain.career.career_data import CharCheck
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import PreCareerData, PrecareerSkillEntry
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.skills import (
    AnySkill,
    Astrogation,
    Electronics,
    Engineer,
    JackOfAllTrades,
    Level,
    Pilot,
    ProfessionSkill,
    VaccSuit,
    skill_instances,
)


class SpacerCommunityPreCareer(PreCareerData):
    name: ClassVar[str] = 'Spacer Community'
    source: ClassVar[str] = 'Companion'
    entry_requirement: ClassVar[str] = 'Automatic if homeworld size code 0; INT 4+, DM+1 if DEX 8+'
    skill_choices: ClassVar[list[PrecareerSkillEntry]] = [
        PrecareerSkillEntry(skill=VaccSuit(), level=1),
        PrecareerSkillEntry(skill=Astrogation(), level=0),
        PrecareerSkillEntry(skill=Electronics(), level=0),
        PrecareerSkillEntry(skill=Engineer(), level=0),
        PrecareerSkillEntry(skill=skill_instances(ProfessionSkill), level=0),
    ]
    entry_pick_count: ClassVar[int] = 2
    graduation: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=8)
    graduation_dms: ClassVar[dict[str, int]] = {'DEX_6+': 1}
    honours_target: ClassVar[int] = 12
    graduation_benefits: ClassVar[list[str]] = [
        'Gain any two other listed skills at level 0',
        'Gain any listed skill at level 1',
        'Gain Pilot 0',
        'Honours graduates gain Jack-of-all-Trades 1',
        'Increase DEX by +1 and decrease SOC by -2',
        'DM+1 to enlist, gain commission or promotion in Merchant (Free Trader)',
    ]

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: Any,
        honours: bool,
    ) -> int:
        pending_idx = 0
        choice_pool: list[AnySkill] = []
        for entry in self.skill_choices:
            if entry.skill and entry.level == 0:
                choice_pool.extend(entry.skill_options)
        for i in range(2):
            projection.pending_inputs.append(
                PendingPreCareerSkillChoice(
                    pending_id=(event.id, pending_idx),
                    level=0,
                    instruction=f'Spacer Community graduation: choose skill {i + 1} of 2 at level 0',
                    options=choice_pool,
                )
            )
            pending_idx += 1
        projection.pending_inputs.append(
            PendingPreCareerSkillChoice(
                pending_id=(event.id, pending_idx),
                level=1,
                instruction='Spacer Community graduation: choose one listed skill at level 1',
                options=choice_pool,
            )
        )
        pending_idx += 1
        projection.grant_skill(Pilot())
        if honours:
            projection.grant_skill(JackOfAllTrades(level=Level(value=1)))
        projection.summary.characteristics[Chars.DEX] = projection.summary.characteristics.get(Chars.DEX, 0) + 1
        projection.summary.characteristics[Chars.SOC] = max(0, projection.summary.characteristics.get(Chars.SOC, 0) - 2)
        projection.pending_qualification_dm += 1
        projection.summary.problems.append(
            'Spacer Community graduation: DM+1 to enlist, commission, and promotion '
            'in Merchant (Free Trader). Apply manually.'
        )
        return pending_idx
