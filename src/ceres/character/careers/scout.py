from ceres.character.careers.career_data import EventEffect
from ceres.character.events import SkillRollEvent
from ceres.character.projection import CharacterProjection, Connection, PendingInput, ScheduledEffect

# ── event 3: ambush ──────────────────────────────────────────────────────────

_AMBUSH_TARGETS = {'Pilot': 8, 'Persuade': 10}


def _handle_scout_event_3(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scout_event_3',
            instruction='Roll Pilot 8+ to escape or Persuade 10+ to bargain',
            options=list(_AMBUSH_TARGETS),
        )
    )
    return pending_idx + 1


def _resolve_scout_event_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    """Advancement pending is created by the replay engine after this returns."""
    target = _AMBUSH_TARGETS[event.skill]
    if event.modified_roll >= target:
        current = projection.summary.skills.get('Electronics', -1)
        if current < 1:
            projection.summary.skills['Electronics'] = 1
    else:
        projection.summary.problems.append('Ship destroyed; may not re-enlist in Scouts at the end of this term.')


# ── event 8: alien intelligence ──────────────────────────────────────────────


def _handle_scout_event_8(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scout_event_8',
            instruction='Roll Electronics 8+ or Deception 8+',
            options=['Electronics', 'Deception'],
        )
    )
    return pending_idx + 1


def _resolve_scout_event_8(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.connections.append(Connection(kind='ally', source='Alien intelligence contact'))
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
    else:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='mishap',
                instruction='Roll 1D Mishap (you are not ejected from this career)',
            )
        )


# ── event 9: disaster rescue ─────────────────────────────────────────────────


def _handle_scout_event_9(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scout_event_9',
            instruction='Roll Medic 8+ or Engineer 8+',
            options=['Medic', 'Engineer'],
        )
    )
    return pending_idx + 1


def _resolve_scout_event_9(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.connections.append(Connection(kind='contact', source='Disaster survivor'))
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
    else:
        projection.summary.connections.append(Connection(kind='enemy', source='Disaster relief gone wrong'))


# ── event 10: fringes of Charted Space ───────────────────────────────────────


def _handle_scout_event_10(
    projection: CharacterProjection,
    effect: EventEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingInput(
            id=f'{event_id}.{pending_idx}',
            kind='scout_event_10',
            instruction='Roll Survival 8+ or Pilot 8+',
            options=['Survival', 'Pilot'],
        )
    )
    return pending_idx + 1


def _resolve_scout_event_10(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.connections.append(
            Connection(kind='contact', source='Alien contact from the fringes of Charted Space')
        )
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='skill_choice',
                instruction='Choose any skill +1 (alien contact)',
                options=[],
            )
        )
    else:
        projection.pending_inputs.append(
            PendingInput(
                id=f'{event.id}.0',
                kind='mishap',
                instruction='Roll 1D Mishap (you are not ejected from this career)',
            )
        )


# ── handler registries ───────────────────────────────────────────────────────

EFFECT_HANDLERS: dict[str, object] = {
    'scout_event_3': _handle_scout_event_3,
    'scout_event_8': _handle_scout_event_8,
    'scout_event_9': _handle_scout_event_9,
    'scout_event_10': _handle_scout_event_10,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'scout_event_3': _resolve_scout_event_3,
    'scout_event_8': _resolve_scout_event_8,
    'scout_event_9': _resolve_scout_event_9,
    'scout_event_10': _resolve_scout_event_10,
}
