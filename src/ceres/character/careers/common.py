"""Shared helpers for career event and mishap handlers."""

from ceres.character.careers.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.characteristics import Chars
from ceres.character.state import CharacterProjection


def handle_advanced_training(
    career: str,
    roll: int,
    context: str,
    projection: CharacterProjection,
    event_id: int,
    pending_idx: int,
    threshold: int = 8,
) -> int:
    instruction = f'Roll EDU {threshold}+ to increase any one skill you already have by one level'
    projection.pending_inputs.append(
        PendingAdvancedTrainingSkillRoll(
            id=f'{event_id}.{pending_idx}',
            instruction=instruction,
            options=[Chars.EDU],
            threshold=threshold,
        )
    )
    return pending_idx + 1
