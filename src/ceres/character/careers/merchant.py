from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.characteristics import Chars
from ceres.character.events import SkillRollEvent
from ceres.character.projection import (
    CharacterProjection,
    Enemy,
    PendingCareerEvent,
    PendingCareerSkillRoll,
    PendingSkillChoice,
    Rival,
    ScheduledEffect,
)

# ── event 3: smuggling opportunity ───────────────────────────────────────────


def _handle_merchant_event_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Merchant',
            roll=3,
            instruction=(
                'Accept the smuggling job (roll Deception or Persuade 8+: '
                'success = extra Benefit roll, fail = ejected with Enemy) '
                'or refuse (gain a Rival)?'
            ),
            options=['accept', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_merchant_event_3(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _career_progress_pending, _current_career

    career = _current_career(projection)
    if event.choice == 'refuse':
        projection.summary.connections.append(Rival(source='Merchant who offered smuggling job (Merchant event 3)'))
        projection.pending_inputs.append(_career_progress_pending(career, projection, event.id))
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Merchant',
                roll=3,
                context='merchant_event_3_skill',
                instruction='Roll Deception or Persuade 8+: success = extra Benefit roll; fail = ejected, gain Enemy',
                options=['Deception', 'Persuade'],
            )
        )


def _resolve_merchant_event_3_skill(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

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
        career = _current_career(projection)
        projection.summary.connections.append(Enemy(source='Smuggling job failed (Merchant event 3)'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── event 5: gambling opportunity ────────────────────────────────────────────


def _handle_merchant_event_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    from ceres.character.replay import _career_progress_pending, _current_career

    career = _current_career(projection)
    projection.summary.problems.append(
        'Merchant event 5: gambling opportunity — decide how many Benefit rolls to wager, '
        'then roll Gambler 8+ or Broker 8+. '
        'Success: gain half the wagered rolls (round up). '
        'Fail: lose all the wagered rolls. Apply the result manually.'
    )
    projection.pending_inputs.append(_career_progress_pending(career, projection, event_id))
    return pending_idx


# ── event 9: advanced training ────────────────────────────────────────────────


def _handle_merchant_event_9(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Merchant',
            roll=9,
            context='merchant_event_9',
            instruction='Roll EDU 8+ to increase any one skill you already have by one level',
            options=[Chars.EDU],
        )
    )
    return pending_idx + 1


def _resolve_merchant_event_9(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        existing_skills = [type(s).name() for s in projection.summary.skills]
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Advanced training: increase any existing skill by one level',
                options=existing_skills,
            )
        )


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = CareerData

EFFECT_HANDLERS: dict[str, object] = {
    'merchant_event_3': _handle_merchant_event_3,
    'merchant_event_5': _handle_merchant_event_5,
    'merchant_event_9': _handle_merchant_event_9,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'merchant_event_3_skill': _resolve_merchant_event_3_skill,
    'merchant_event_9': _resolve_merchant_event_9,
}

CHOICE_HANDLERS: dict[str, object] = {
    'merchant_event_3': _choice_merchant_event_3,
}
