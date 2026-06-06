from ceres.character.characteristics import Chars, ConnectionKind
from ceres.character.events import PendingPreCareerSkillChoice, PreCareerGraduationEvent
from ceres.character.precareers.precareer_data import PreCareerData
from ceres.character.skills import ScienceSkill, skill_instances
from ceres.character.state import (
    CharacterProjection,
    CharacterSummary,
    make_connection,
)


class PsionicCommunityPreCareer(PreCareerData):
    def is_available(self, summary: CharacterSummary) -> bool:
        return Chars.PSI in summary.characteristics

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
        honours: bool,
    ) -> int:

        pending_idx = 0
        projection.summary.problems.append('Psionic Community graduation: increase PSI by +1. Apply manually.')
        projection.summary.problems.append(
            'Psionic Community graduation: gain level 1 in any one psionic talent possessed. Apply manually.'
        )
        science_options = skill_instances(ScienceSkill)
        if science_options:
            projection.pending_inputs.append(
                PendingPreCareerSkillChoice(
                    pending_id=(event.id, pending_idx),
                    level=1,
                    instruction='Psionic Community graduation: choose one Science specialisation at level 1',
                    options=science_options,
                )
            )
            pending_idx += 1
        if honours:
            projection.summary.problems.append(
                'Psionic Community graduation (honours): all acquired talents at level 1; '
                'advance one to level 2. Apply manually.'
            )
        projection.summary.problems.append(
            'Psionic Community graduation: automatic enlistment in Psion career '
            '(even after other careers). Apply manually.'
        )
        source = 'Psionic Community graduation'
        if honours:
            projection.summary.connections.append(make_connection(ConnectionKind.ENEMY, source=source))
        else:
            projection.summary.connections.append(make_connection(ConnectionKind.RIVAL, source=source))
        return pending_idx
