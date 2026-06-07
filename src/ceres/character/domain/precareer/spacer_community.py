from typing import Any

from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.skills import AnySkill, JackOfAllTrades, Level, Pilot
from ceres.character.mechanism.character_state import CharacterProjection


class SpacerCommunityPreCareer(PreCareerData):
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
