from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.events import (
    PendingCareerEvent,
    PendingCareerSkillRoll,
    SkillRollEvent,
    career_progress_pending,
    muster_out_setup,
)
from ceres.character.state import (
    Ally,
    CharacterProjection,
    Contact,
    Enemy,
    Rival,
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
    projection.forced_next_career = 'Prisoner'
    return pending_idx


# ── mishap 3: betrayed by a friend ───────────────────────────────────────────


def _handle_rogue_mishap_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    friends = [c for c in projection.summary.connections if isinstance(c, (Contact, Ally))]
    if friends:
        betrayer = friends[-1]
        projection.summary.connections.remove(betrayer)
        projection.summary.connections.append(Rival(source=f'Betrayed you (was {betrayer.kind}, Rogue mishap 3)'))
    else:
        projection.summary.connections.append(Rival(source='Betrayal by unknown (Rogue mishap 3)'))

    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Rogue',
            roll=3,
            context='rogue_mishap_3_prisoner_check',
            instruction='Roll 2D: on a result of exactly 2, you must take the Prisoner career next term',
            options=[str(i) for i in range(2, 13)],
        )
    )
    return pending_idx + 1


def _resolve_rogue_mishap_3_prisoner_check(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.careers.loader import load_careers

    if event.modified_roll == 2:
        projection.forced_next_career = 'Prisoner'

    career_name = projection.summary.current_career
    career = load_careers().get(career_name or '')
    if career is None:
        return
    muster_out_setup(projection, career, event.id, 0, lose_current_term=True)


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
    career = projection.get_current_career()
    if event.choice == 'lawyer':
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out_reduce',
                source_event_id=event.id,
                effect={'type': 'reduce', 'value': 1},
            )
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
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
    from ceres.character.events import _apply_mishap_ejection

    if event.modified_roll >= 8:
        pass  # cleared — _apply_skill_roll auto-queues advancement
    else:
        career = projection.get_current_career()
        projection.forced_next_career = 'Prisoner'
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
    career = projection.get_current_career()
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
    projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


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
    'rogue_mishap_3': _handle_rogue_mishap_3,
    'rogue_event_3': _handle_rogue_event_3,
    'rogue_event_6': _handle_rogue_event_6,
    'rogue_event_9': _handle_rogue_event_9,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'rogue_mishap_3_prisoner_check': _resolve_rogue_mishap_3_prisoner_check,
    'rogue_event_3_skill': _resolve_rogue_event_3_skill,
    'rogue_event_9': _resolve_rogue_event_9,
}

CHOICE_HANDLERS: dict[str, object] = {
    'rogue_event_3': _choice_rogue_event_3,
    'rogue_event_6': _choice_rogue_event_6,
}
