from typing import Any

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.connection import make_connection
from ceres.character.domain.precareer.precareer_data import PreCareerData
from ceres.character.domain.psionics import PendingPsionicTalentLevelChoice, queue_psionic_institute_training
from ceres.character.domain.skills import Level, LifeScience


class PsionicCommunityPreCareer(PreCareerData):
    def is_available(self, summary: CharacterSummary) -> bool:
        return summary.psionics is not None

    def apply_entry(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        pending_idx = super().apply_entry(projection, event, pending_idx)
        if queue_psionic_institute_training(projection, event.id, pending_idx):
            pending_idx += 1
        return pending_idx

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: Any,
        honours: bool,
    ) -> int:

        pending_idx = 0
        if projection.summary.psionics is None:
            raise ValueError('Psionic Community graduation requires Psionic Strength')
        projection.summary.characteristics[Chars.PSI] = projection.summary.characteristics.get(Chars.PSI, 0) + 1
        psionics = projection.summary.psionics
        if honours:
            for talent in psionics.psionic_talent_skills:
                psionics.raise_talent_to(type(talent), 1)
            target_level = 2
        else:
            target_level = 1
        if any(talent.level.value < target_level for talent in psionics.psionic_talent_skills):
            projection.pending_inputs.append(
                PendingPsionicTalentLevelChoice(
                    pending_id=(event.id, pending_idx),
                    level=target_level,
                    instruction=f'Psionic Community graduation: choose one possessed talent at level {target_level}',
                )
            )
            pending_idx += 1
        projection.grant_skill(LifeScience(psionicology=Level(value=1)))
        if 'Psion' not in projection.auto_qualify_careers:
            projection.auto_qualify_careers.append('Psion')
        source = 'Psionic Community graduation'
        if honours:
            projection.summary.connections.append(make_connection(ConnectionKind.ENEMY, source=source))
        else:
            projection.summary.connections.append(make_connection(ConnectionKind.RIVAL, source=source))
        return pending_idx
