from ceres.character.careers.career_data import EventEffect
from ceres.character.events import SkillRollEvent
from ceres.character.projection import CharacterProjection, PendingInput

# ── event 6: advanced training ───────────────────────────────────────────────


def _handle_scholar_event_6(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scholar_event_6',
            instruction='Roll EDU 8+ to gain any skill of your choice at level 1',
            options=['EDU'],
        )
    )
    return pending_idx + 1


def _resolve_scholar_event_6(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='skill_choice',
                instruction='Choose any skill to gain at level 1',
                options=[],
            )
        )
    # failure: _apply_skill_roll creates advancement pending


# ── handler registries ───────────────────────────────────────────────────────

EFFECT_HANDLERS: dict[str, object] = {
    'scholar_event_6': _handle_scholar_event_6,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'scholar_event_6': _resolve_scholar_event_6,
}
