from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.characteristics import Chars
from ceres.character.events import SkillRollEvent
from ceres.character.projection import (
    Ally,
    CharacterProjection,
    Contact,
    Enemy,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    PendingSkillChoice,
    ScheduledEffect,
)

# ── mishap 4: black ops mission ───────────────────────────────────────────────


def _handle_marines_mishap_4(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Marines',
            roll=4,
            instruction=(
                'Refuse (ejected, no Benefit, gain Contact among other soldiers) '
                'or accept (roll Deception or Persuade 8+: success = stay, fail = ejected, no Benefit)?'
            ),
            options=['refuse', 'accept'],
        )
    )
    return pending_idx + 1


def _choice_marines_mishap_4(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    career = _current_career(projection)
    if event.choice == 'refuse':
        projection.summary.connections.append(Contact(source='Soldier from black ops mission (Marines mishap 4)'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Marines',
                roll=4,
                context='marines_mishap_4_skill',
                instruction='Roll Deception or Persuade 8+: success = stay in career; fail = ejected, lose Benefit',
                options=['Deception', 'Persuade'],
            )
        )


def _resolve_marines_mishap_4_skill(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    career = _current_career(projection)
    if event.modified_roll < 8:
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)
    # success: do nothing — _apply_skill_roll auto-queues advancement


# ── event 5: advanced training ───────────────────────────────────────────────


def _handle_marines_event_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Marines',
            roll=5,
            context='marines_event_5',
            instruction='Roll EDU 8+ to increase any one skill you already have by one level',
            options=[Chars.EDU],
        )
    )
    return pending_idx + 1


def _resolve_marines_event_5(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        existing_skills = [type(s).name() for s in projection.summary.skills]
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Advanced training: increase any existing skill by one level',
                options=existing_skills,
            )
        )


# ── event 6: assault on an enemy fortress ────────────────────────────────────


def _handle_marines_event_6(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Marines',
            roll=6,
            context='marines_event_6',
            instruction='Roll Melee or Gun Combat 8+: success = gain Tactics or Leadership; fail = injured',
            options=['Melee', 'Gun Combat'],
        )
    )
    return pending_idx + 1


def _resolve_marines_event_6(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Fortress assault success: gain one level in Tactics or Leadership',
                options=['Tactics', 'Leadership'],
            )
        )
    else:
        projection.summary.problems.append(
            'Fortress assault: you are injured — roll on the Injury table and apply the result.'
        )


# ── event 9: mission goes wrong ───────────────────────────────────────────────


def _handle_marines_event_9(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Marines',
            roll=9,
            instruction=(
                'Report the commander (DM+2 to next advancement, commander becomes Enemy) '
                'or protect them (DM+1 to next advancement, commander becomes Ally)?'
            ),
            options=['report', 'protect'],
        )
    )
    return pending_idx + 1


def _choice_marines_event_9(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _career_progress_pending, _current_career

    career = _current_career(projection)
    if event.choice == 'report':
        projection.summary.connections.append(Enemy(source='Commander (Marines event 9)'))
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
    else:
        projection.summary.connections.append(Ally(source='Commander (Marines event 9)'))
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 1},
            )
        )
    projection.pending_inputs.append(_career_progress_pending(career, projection, event.id))


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = CareerData

EFFECT_HANDLERS: dict[str, object] = {
    'marines_mishap_4': _handle_marines_mishap_4,
    'marines_event_5': _handle_marines_event_5,
    'marines_event_6': _handle_marines_event_6,
    'marines_event_9': _handle_marines_event_9,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'marines_mishap_4_skill': _resolve_marines_mishap_4_skill,
    'marines_event_5': _resolve_marines_event_5,
    'marines_event_6': _resolve_marines_event_6,
}

CHOICE_HANDLERS: dict[str, object] = {
    'marines_mishap_4': _choice_marines_mishap_4,
    'marines_event_9': _choice_marines_event_9,
}
