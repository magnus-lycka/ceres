from ceres.character.characteristics import Chars
from ceres.character.events import PendingPreCareerSkillChoice, PreCareerGraduationEvent
from ceres.character.precareers.precareer_data import PreCareerData
from ceres.character.skills import JackOfAllTrades, Leadership, Level
from ceres.character.state import CharacterProjection


class ColonialUprbringingPreCareer(PreCareerData):
    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
        honours: bool,
    ) -> int:
        pending_idx = 0
        skill_pool: list[str] = []
        for entry in self.skill_choices:
            if entry.skill:
                skill_pool.extend(entry.option_names)
        for i in range(3):
            projection.pending_inputs.append(
                PendingPreCareerSkillChoice(
                    id=f'{event.id}.{pending_idx}',
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
                    id=f'{event.id}.{pending_idx}',
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
