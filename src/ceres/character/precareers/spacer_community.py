from ceres.character.characteristics import Chars
from ceres.character.events import PendingPreCareerSkillChoice, PreCareerGraduationEvent
from ceres.character.precareers.precareer_data import PreCareerData
from ceres.character.skills import AnySkill, JackOfAllTrades, Level, Pilot
from ceres.character.state import (
    CharacterProjection,
    ScheduledEffect,
)


class SpacerCommunityPreCareer(PreCareerData):
    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
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
                    id=f'{event.id}.{pending_idx}',
                    level=0,
                    instruction=f'Spacer Community graduation: choose skill {i + 1} of 2 at level 0',
                    options=choice_pool,
                )
            )
            pending_idx += 1
        projection.pending_inputs.append(
            PendingPreCareerSkillChoice(
                id=f'{event.id}.{pending_idx}',
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
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='qualification',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 1, 'career': 'Merchant', 'assignment': 'Free Trader'},
                consume=True,
            )
        )
        projection.summary.problems.append(
            'Spacer Community graduation: DM+1 to enlist, commission, and promotion '
            'in Merchant (Free Trader). Apply manually.'
        )
        return pending_idx
