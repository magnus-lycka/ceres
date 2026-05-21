from ceres.character.careers.career_data import EventEffect
from ceres.character.events import SkillRollEvent
from ceres.character.projection import CharacterProjection, Connection, PendingInput

_SCIENCES = sorted(['Life Science', 'Physical Science', 'Robotic Science', 'Social Science', 'Space Science'])

# ── event 3: research against conscience ─────────────────────────────────────


def _handle_scholar_event_3(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scholar_event_3',
            instruction='Accept (2 Science specialties + D3 Enemies + extra Benefit roll) or Decline?',
            options=['accept', 'decline'],
        )
    )
    return pending_idx + 1


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


# ── event 8: opportunity to cheat ────────────────────────────────────────────


def _handle_scholar_event_8(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scholar_event_8',
            instruction='Refuse (nothing) or Accept (roll Deception/Admin 8+)?',
            options=['accept', 'refuse'],
        )
    )
    return pending_idx + 1


def _resolve_scholar_event_8_roll(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.connections.append(Connection(kind='enemy', source='Cheating in the field'))
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='skill_choice',
                instruction='Cheat succeeded: choose any skill to gain +1',
                options=[],
            )
        )
    else:
        projection.summary.connections.append(Connection(kind='enemy', source='Cheating discovered'))
    # _apply_skill_roll creates advancement if no new pending (failure), or after skill_choice (success)


# ── event 11: brilliant mentor ────────────────────────────────────────────────


def _handle_scholar_event_11(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scholar_event_11',
            instruction='Gain Space Science +1, or DM+4 to your next advancement roll',
            options=['Space Science', 'advancement_dm_4'],
        )
    )
    return pending_idx + 1


# ── mishap 3: planetary interference ─────────────────────────────────────────


def _handle_scholar_mishap_3(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scholar_mishap_3',
            instruction='Continue openly (Space Science +1, Enemy) or secretly (Space Science +1, SOC -2)?',
            options=['openly', 'secretly'],
        )
    )
    return pending_idx + 1


# ── mishap 5: work sabotaged ──────────────────────────────────────────────────


def _handle_scholar_mishap_5(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scholar_mishap_5',
            instruction='Give up (leave career) or start again (stay, lose benefit rolls)?',
            options=['give_up', 'start_again'],
        )
    )
    return pending_idx + 1


# ── handler registries ───────────────────────────────────────────────────────

EFFECT_HANDLERS: dict[str, object] = {
    'scholar_event_3': _handle_scholar_event_3,
    'scholar_event_6': _handle_scholar_event_6,
    'scholar_event_8': _handle_scholar_event_8,
    'scholar_event_11': _handle_scholar_event_11,
    'scholar_mishap_3_choice': _handle_scholar_mishap_3,
    'scholar_mishap_5_choice': _handle_scholar_mishap_5,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'scholar_event_6': _resolve_scholar_event_6,
    'scholar_event_8_roll': _resolve_scholar_event_8_roll,
}
