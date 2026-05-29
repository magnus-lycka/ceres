from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.characteristics import Chars
from ceres.character.events import SkillRollEvent
from ceres.character.projection import (
    Ally,
    CharacterProjection,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    PendingSkillChoice,
)

# ── mishap 4: illegal activity ────────────────────────────────────────────────


def _handle_army_mishap_4(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Army',
            roll=4,
            instruction=(
                'Join their ring (gain commanding officer as Ally, lose Benefit roll) '
                'or co-operate with MPs (keep Benefit roll from this term)?'
            ),
            options=['join_ring', 'cooperate'],
        )
    )
    return pending_idx + 1


def _choice_army_mishap_4(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    career = _current_career(projection)
    if event.choice == 'join_ring':
        projection.summary.connections.append(Ally(source='Commanding officer (Army mishap 4)'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)
    else:
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=False)


# ── event 6: brutal ground war ───────────────────────────────────────────────


def _handle_army_event_6(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Army',
            roll=6,
            context='army_event_6',
            instruction='Roll EDU 8+ to avoid injury in the brutal ground war',
            options=[Chars.EDU],
        )
    )
    return pending_idx + 1


def _resolve_army_event_6(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Ground war success: gain one level in Gun Combat or Leadership',
                options=['Gun Combat', 'Leadership'],
            )
        )
    else:
        projection.summary.problems.append(
            'Brutal ground war: you are injured — roll on the Injury table and apply the result.'
        )


# ── event 8: advanced training ───────────────────────────────────────────────


def _handle_army_event_8(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Army',
            roll=8,
            context='army_event_8',
            instruction='Roll EDU 8+ to increase any one skill you already have by one level',
            options=[Chars.EDU],
        )
    )
    return pending_idx + 1


def _resolve_army_event_8(projection: CharacterProjection, event: SkillRollEvent) -> None:
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
    'army_mishap_4': _handle_army_mishap_4,
    'army_event_6': _handle_army_event_6,
    'army_event_8': _handle_army_event_8,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'army_event_6': _resolve_army_event_6,
    'army_event_8': _resolve_army_event_8,
}

CHOICE_HANDLERS: dict[str, object] = {
    'army_mishap_4': _choice_army_mishap_4,
}
