"""Shared helpers for career event and mishap handlers."""

from ceres.character.domain.career.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars


def handle_advanced_training(
    projection: CharacterProjection,
    event_id: int,
    pending_idx: int,
    threshold: int = 8,
) -> int:
    instruction = f'Roll EDU {threshold}+ to increase any one skill you already have by one level'
    projection.pending_inputs.append(
        PendingAdvancedTrainingSkillRoll(
            pending_id=(event_id, pending_idx),
            instruction=instruction,
            options=[Chars.EDU],
            threshold=threshold,
        )
    )
    return pending_idx + 1
