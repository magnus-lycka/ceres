from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.careers.common import handle_advanced_training, resolve_advanced_training
from ceres.character.events import SkillRollEvent
from ceres.character.projection import (
    CharacterProjection,
    Enemy,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    ScheduledEffect,
)

# ── mishap 3: battle skill check ─────────────────────────────────────────────

_MISHAP_3_SKILLS: dict[str, list[str]] = {
    'Line/Crew': ['Electronics', 'Gunner'],
    'Engineer/Gunner': ['Mechanic', 'Vacc Suit'],
    'Flight': ['Pilot', 'Tactics'],
}


def _handle_navy_mishap_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    assignment = projection.summary.current_assignment or 'Line/Crew'
    options = _MISHAP_3_SKILLS.get(assignment, ['Electronics', 'Gunner'])
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Navy',
            roll=3,
            context='navy_mishap_3',
            instruction=(
                f'Roll {" or ".join(options)} 8+ — success: honourable discharge (keep Benefit); '
                'fail: court-martialled (lose Benefit)'
            ),
            options=options,
        )
    )
    return pending_idx + 1


def _resolve_navy_mishap_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    career = _current_career(projection)
    lose = event.modified_roll < 8
    _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=lose)


# ── mishap 4: blamed for accident ────────────────────────────────────────────


def _handle_navy_mishap_4(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Navy',
            roll=4,
            instruction=(
                'Were you responsible for the accident? '
                'Responsible: gain one free skill table roll before ejection. '
                'Not responsible: gain the officer who blamed you as an Enemy, but keep your Benefit roll.'
            ),
            options=['responsible', 'not_responsible'],
        )
    )
    return pending_idx + 1


def _choice_navy_mishap_4(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    career = _current_career(projection)
    if event.choice == 'responsible':
        projection.summary.problems.append(
            'Navy mishap 4 (responsible): you gain one free roll on the Skills and Training tables '
            'before ejection — apply a skill table roll manually to this character.'
        )
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)
    else:
        projection.summary.connections.append(Enemy(source='Officer who blamed you (Navy mishap 4)'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=False)


# ── event 5: advanced training ───────────────────────────────────────────────


def _handle_navy_event_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    return handle_advanced_training('Navy', 5, 'navy_event_5', projection, effect, event_id, pending_idx)


def _resolve_navy_event_5(projection: CharacterProjection, event: SkillRollEvent) -> None:
    resolve_advanced_training(projection, event)


# ── event 10: abuse position for profit ──────────────────────────────────────


def _handle_navy_event_10(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Navy',
            roll=10,
            instruction=(
                'Abuse your position for profit (gain extra Benefit roll) or refuse (DM+2 to next advancement)?'
            ),
            options=['profit', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_navy_event_10(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _career_progress_pending, _current_career

    career = _current_career(projection)
    if event.choice == 'profit':
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out_add',
                source_event_id=event.id,
                effect={'type': 'add', 'value': 1},
            )
        )
    else:
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
    projection.pending_inputs.append(_career_progress_pending(career, projection, event.id))


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = CareerData

EFFECT_HANDLERS: dict[str, object] = {
    'navy_mishap_3': _handle_navy_mishap_3,
    'navy_mishap_4': _handle_navy_mishap_4,
    'navy_event_5': _handle_navy_event_5,
    'navy_event_10': _handle_navy_event_10,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'navy_mishap_3': _resolve_navy_mishap_3,
    'navy_event_5': _resolve_navy_event_5,
}

CHOICE_HANDLERS: dict[str, object] = {
    'navy_mishap_4': _choice_navy_mishap_4,
    'navy_event_10': _choice_navy_event_10,
}
