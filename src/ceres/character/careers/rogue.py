from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.events import SkillRollEvent
from ceres.character.projection import (
    CharacterProjection,
    Contact,
    Enemy,
    PendingCareerEvent,
    PendingCareerSkillRoll,
    ScheduledEffect,
)


class RogueCareerData(CareerData):
    pass


# ── mishap 2: arrested ────────────────────────────────────────────────────────


def _handle_rogue_mishap_2(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.summary.problems.append(
        'Rogue mishap 2: arrested — you must take the Prisoner career in your next term. Apply manually.'
    )
    return pending_idx


# ── event 3: arrested and charged ────────────────────────────────────────────


def _handle_rogue_event_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Rogue',
            roll=3,
            instruction=(
                'Defend yourself (roll Advocate 8+: success = cleared, fail = ejected + must take Prisoner next term) '
                'or hire a lawyer (lose one Benefit roll, career continues)?'
            ),
            options=['defend', 'lawyer'],
        )
    )
    return pending_idx + 1


def _choice_rogue_event_3(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _career_progress_pending, _current_career

    career = _current_career(projection)
    if event.choice == 'lawyer':
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out_reduce',
                source_event_id=event.id,
                effect={'type': 'reduce', 'value': 1},
            )
        )
        projection.pending_inputs.append(_career_progress_pending(career, projection, event.id))
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Rogue',
                roll=3,
                context='rogue_event_3_skill',
                instruction=(
                    'Roll Advocate 8+: success = cleared, career continues; '
                    'fail = ejected, must take Prisoner next term'
                ),
                options=['Advocate'],
            )
        )


def _resolve_rogue_event_3_skill(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    if event.modified_roll >= 8:
        pass  # cleared — _apply_skill_roll auto-queues advancement
    else:
        career = _current_career(projection)
        projection.summary.problems.append(
            'Rogue event 3: charges failed — you are ejected and must take the Prisoner career next term. '
            'Apply manually.'
        )
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── event 6: backstab fellow rogue ───────────────────────────────────────────


def _handle_rogue_event_6(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Rogue',
            roll=6,
            instruction=(
                'Backstab the fellow rogue (DM+2 to next advancement, gain Enemy) or refuse (gain a Contact instead)?'
            ),
            options=['backstab', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_rogue_event_6(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _career_progress_pending, _current_career

    career = _current_career(projection)
    if event.choice == 'backstab':
        projection.summary.connections.append(Enemy(source='Backstabbed rogue (Rogue event 6)'))
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
    else:
        projection.summary.connections.append(Contact(source='Fellow rogue (Rogue event 6)'))
    projection.pending_inputs.append(_career_progress_pending(career, projection, event.id))


# ── event 9: feud with rival organisation ────────────────────────────────────


def _handle_rogue_event_9(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Rogue',
            roll=9,
            context='rogue_event_9',
            instruction='Roll Stealth or Gun Combat 8+: success = extra Benefit roll; fail = injured',
            options=['Stealth', 'Gun Combat'],
        )
    )
    return pending_idx + 1


def _resolve_rogue_event_9(projection: CharacterProjection, event: SkillRollEvent) -> None:
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
        projection.summary.problems.append(
            'Criminal feud: you are injured — roll on the Injury table and apply the result.'
        )


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = RogueCareerData

EFFECT_HANDLERS: dict[str, object] = {
    'rogue_mishap_2': _handle_rogue_mishap_2,
    'rogue_event_3': _handle_rogue_event_3,
    'rogue_event_6': _handle_rogue_event_6,
    'rogue_event_9': _handle_rogue_event_9,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'rogue_event_3_skill': _resolve_rogue_event_3_skill,
    'rogue_event_9': _resolve_rogue_event_9,
}

CHOICE_HANDLERS: dict[str, object] = {
    'rogue_event_3': _choice_rogue_event_3,
    'rogue_event_6': _choice_rogue_event_6,
}
