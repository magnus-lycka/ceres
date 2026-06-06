from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.skills import AnySkill, Carouse, GunCombat, Level
from ceres.character.events import PendingPreCareerSkillChoice, PreCareerGraduationEvent
from ceres.character.state import CharacterProjection


class SchoolOfHardKnocksPreCareer(PreCareerData):
    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
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
