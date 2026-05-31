from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.events import SkillRollEvent
from ceres.character.projection import (
    CharacterProjection,
    Enemy,
    PendingCareerEvent,
    PendingCareerSkillRoll,
    PendingInjuryTable,
    PendingSkillChoice,
    Rival,
    ScheduledEffect,
)


class DrifterCareerData(CareerData):
    def _basic_training_table_name(self, assignment) -> str:
        return assignment.name.lower()


# ── mishap 5: betrayed by a friend ───────────────────────────────────────────


def _handle_drifter_mishap_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Drifter',
            roll=5,
            context='drifter_mishap_5',
            instruction=('Betrayed by a friend: gain a Rival. Roll 2D — on a natural 2, must take Prisoner next term'),
            options=[],
        )
    )
    return pending_idx + 1


def _resolve_drifter_mishap_5(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
    projection.summary.connections.append(Rival(source='Former friend who betrayed you (Drifter mishap 5)'))
    if event.modified_roll == 2:
        projection.forced_next_career = 'Prisoner'
    _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── event 3: patron job offer ─────────────────────────────────────────────────


def _handle_drifter_event_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Drifter',
            roll=3,
            instruction="Accept the patron's job offer (DM+4 to next Qualification roll) or decline?",
            options=['accept', 'decline'],
        )
    )
    return pending_idx + 1


def _choice_drifter_event_3(projection: CharacterProjection, event) -> None:
    career = projection.get_current_career()
    if event.choice == 'accept':
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='qualification',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 4},
            )
        )
    projection.pending_inputs.append(projection.career_progress_pending(career, event.id))


# ── event 8: attacked by enemies ─────────────────────────────────────────────


def _handle_drifter_event_8(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.summary.connections.append(Enemy(source='Attacker (Drifter event 8)'))
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Drifter',
            roll=8,
            context='drifter_event_8',
            instruction='Roll Melee or Gun Combat 8+: success = increase that skill; fail = injured',
            options=['Melee', 'Gun Combat'],
        )
    )
    return pending_idx + 1


def _resolve_drifter_event_8(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Attack survived: increase Melee or Gun Combat by one level',
                options=['Melee', 'Gun Combat'],
            )
        )
    else:
        projection.summary.problems.append(
            'Attacked by enemies: you are injured — roll on the Injury table and apply the result.'
        )


# ── event 9: risky adventure ──────────────────────────────────────────────────


def _handle_drifter_event_9(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Drifter',
            roll=9,
            instruction='Accept the risky adventure (roll 1D for outcome) or decline?',
            options=['accept', 'decline'],
        )
    )
    return pending_idx + 1


def _choice_drifter_event_9(projection: CharacterProjection, event) -> None:
    career = projection.get_current_career()
    if event.choice == 'decline':
        projection.pending_inputs.append(projection.career_progress_pending(career, event.id))
    elif event.choice == 'injury':
        # outcome choice: injury
        projection.pending_inputs.append(
            PendingInjuryTable(
                id=f'{event.id}.0',
                instruction='Risky adventure outcome: roll 1D on Injury table',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
    elif event.choice == 'prison':
        # outcome choice: prison
        projection.forced_next_career = 'Prisoner'
    else:  # 'accept'
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Drifter',
                roll=9,
                context='drifter_event_9_roll',
                instruction='Risky adventure: roll 1D (1-2: injured or arrested, 3: injured, 4-6: bonus Benefit roll)',
                options=[],
            )
        )


def _resolve_drifter_event_9_roll(projection: CharacterProjection, event: SkillRollEvent) -> None:
    career = projection.get_current_career()
    roll = event.modified_roll
    if roll <= 2:
        # Choice: injury or prison
        projection.pending_inputs.append(
            PendingCareerEvent(
                id=f'{event.id}.0',
                career='Drifter',
                roll=9,
                instruction='Risky adventure (1-2): choose — roll on Injury table, or be sent to Prisoner career?',
                options=['injury', 'prison'],
            )
        )
        projection.pending_inputs.append(projection.career_progress_pending(career, event.id, 1))
    elif roll == 3:
        projection.pending_inputs.append(
            PendingInjuryTable(
                id=f'{event.id}.0',
                instruction='Risky adventure (3): roll 1D on Injury table',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        projection.pending_inputs.append(projection.career_progress_pending(career, event.id, 1))
    else:  # 4-6
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out_add',
                source_event_id=event.id,
                effect={'type': 'add', 'value': 1},
            )
        )
        # _apply_skill_roll auto-queues advancement


# ── event 11: forcibly drafted ────────────────────────────────────────────────


def _handle_drifter_event_11(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    career = projection.get_current_career()
    projection.summary.problems.append(
        'Drifter event 11: forcibly drafted — roll 1D: 1-2 Army, 3-4 Marines, 5-6 Navy. '
        'Leave this career and enter the rolled career next term (no qualification roll needed). Apply manually.'
    )
    projection.pending_inputs.append(projection.career_progress_pending(career, event_id))
    return pending_idx


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = DrifterCareerData

EFFECT_HANDLERS: dict[str, object] = {
    'drifter_mishap_5': _handle_drifter_mishap_5,
    'drifter_event_3': _handle_drifter_event_3,
    'drifter_event_8': _handle_drifter_event_8,
    'drifter_event_9': _handle_drifter_event_9,
    'drifter_event_11': _handle_drifter_event_11,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'drifter_mishap_5': _resolve_drifter_mishap_5,
    'drifter_event_8': _resolve_drifter_event_8,
    'drifter_event_9_roll': _resolve_drifter_event_9_roll,
}

CHOICE_HANDLERS: dict[str, object] = {
    'drifter_event_3': _choice_drifter_event_3,
    'drifter_event_9': _choice_drifter_event_9,
}
