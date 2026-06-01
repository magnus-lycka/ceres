from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingCareerEvent,
    PendingCareerSkillRoll,
    SkillRollEvent,
    career_progress_pending,
)
from ceres.character.state import (
    CharacterProjection,
    Enemy,
    Rival,
    ScheduledEffect,
)


class NobleCareerData(CareerData):
    pass


# ── mishap 3: disaster or war ─────────────────────────────────────────────────


def _handle_noble_mishap_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Noble',
            roll=3,
            context='noble_mishap_3',
            instruction=(
                'Roll Stealth or Deception 8+: success = escape unhurt (keep Benefit); fail = injury + lose Benefit'
            ),
            options=['Stealth', 'Deception'],
        )
    )
    return pending_idx + 1


def _resolve_noble_mishap_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
    if event.modified_roll >= 8:
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=False)
    else:
        projection.summary.problems.append(
            'Noble mishap 3: failed to escape — roll on the Injury table and apply the result.'
        )
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── mishap 5: assassin attempt ────────────────────────────────────────────────


def _handle_noble_mishap_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Noble',
            roll=5,
            context='noble_mishap_5',
            instruction='Roll END 8+: success = escape unhurt (ejected); fail = roll on Injury table (ejected)',
            options=[Chars.END],
        )
    )
    return pending_idx + 1


def _resolve_noble_mishap_5(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
    if event.modified_roll < 8:
        projection.summary.problems.append('Noble mishap 5: assassin — roll on the Injury table and apply the result.')
    _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── event 8: conspiracy recruitment ──────────────────────────────────────────


def _handle_noble_event_8(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Noble',
            roll=8,
            instruction=(
                'Join the noble conspiracy (roll Deception or Persuade 8+: '
                'success = extra Benefit roll, fail = ejected with Enemy) '
                'or refuse (gain a Rival)?'
            ),
            options=['accept', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_noble_event_8(projection: CharacterProjection, event) -> None:
    career = projection.get_current_career()
    if event.choice == 'refuse':
        projection.summary.connections.append(Rival(source='Conspiracy leader (Noble event 8)'))
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Noble',
                roll=8,
                context='noble_event_8_skill',
                instruction='Roll Deception or Persuade 8+: success = extra Benefit roll; fail = ejected, gain Enemy',
                options=['Deception', 'Persuade'],
            )
        )


def _resolve_noble_event_8_skill(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.events import _apply_mishap_ejection

    if event.modified_roll >= 8:
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out_add',
                source_event_id=event.id,
                effect={'type': 'add', 'value': 1},
            )
        )
        # no pending added — _apply_skill_roll auto-queues advancement
    else:
        career = projection.get_current_career()
        projection.summary.connections.append(Enemy(source='Noble conspiracy (Noble event 8)'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = NobleCareerData

EFFECT_HANDLERS: dict[str, object] = {
    'noble_mishap_3': _handle_noble_mishap_3,
    'noble_mishap_5': _handle_noble_mishap_5,
    'noble_event_8': _handle_noble_event_8,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'noble_mishap_3': _resolve_noble_mishap_3,
    'noble_mishap_5': _resolve_noble_mishap_5,
    'noble_event_8_skill': _resolve_noble_event_8_skill,
}

CHOICE_HANDLERS: dict[str, object] = {
    'noble_event_8': _choice_noble_event_8,
}
