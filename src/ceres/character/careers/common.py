"""Shared helpers for career event and mishap handlers."""

from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingCareerSkillRoll,
    PendingSkillChoice,
    SkillRollEvent,
)
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
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career=career,
            roll=roll,
            context=context,
            instruction=instruction,
            options=[Chars.EDU],
        )
    )
    return pending_idx + 1


def resolve_advanced_training(projection: CharacterProjection, event: SkillRollEvent, threshold: int = 8) -> None:
    if event.modified_roll >= threshold:
        existing_skills = [type(s).name() for s in projection.summary.skills]
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Advanced training: increase any existing skill by one level',
                options=existing_skills,
            )
        )
