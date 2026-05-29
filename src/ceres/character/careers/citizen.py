from ceres.character.careers.career_data import CareerData, CareerDispatchEffect
from ceres.character.characteristics import Chars
from ceres.character.events import SkillRollEvent
from ceres.character.projection import (
    CharacterProjection,
    Contact,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    PendingSkillChoice,
    Rival,
    ScheduledEffect,
)


class CitizenCareerData(CareerData):
    def _basic_training_table_name(self, assignment) -> str:
        return assignment.name.lower()


# ── mishap 4: investigation by authorities ────────────────────────────────────


def _handle_citizen_mishap_4(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Citizen',
            roll=4,
            instruction=(
                'Co-operate with the investigation (gain investigators as a Contact, keep Benefit roll) '
                'or resist (gain a Rival, lose Benefit roll)?'
            ),
            options=['cooperate', 'resist'],
        )
    )
    return pending_idx + 1


def _choice_citizen_mishap_4(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    career = _current_career(projection)
    if event.choice == 'cooperate':
        projection.summary.connections.append(Contact(source='Investigator (Citizen mishap 4)'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=False)
    else:
        projection.summary.connections.append(Rival(source='Investigator (Citizen mishap 4)'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── mishap 5: revolution or attack ───────────────────────────────────────────


def _handle_citizen_mishap_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Citizen',
            roll=5,
            context='citizen_mishap_5',
            instruction='Roll Streetwise 8+: success = increase any existing skill by one level (ejected either way)',
            options=['Streetwise'],
        )
    )
    return pending_idx + 1


def _resolve_citizen_mishap_5(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    career = _current_career(projection)
    if event.modified_roll >= 8:
        existing_skills = [type(s).name() for s in projection.summary.skills]
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Forced to flee: increase any existing skill by one level',
                options=existing_skills,
            )
        )
        _apply_mishap_ejection(projection, career, event.id, 1, lose_current_term=True)
    else:
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── event 6: advanced training ────────────────────────────────────────────────


def _handle_citizen_event_6(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Citizen',
            roll=6,
            context='citizen_event_6',
            instruction='Roll EDU 10+ to increase any one skill you already have by one level',
            options=[Chars.EDU],
        )
    )
    return pending_idx + 1


def _resolve_citizen_event_6(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 10:
        existing_skills = [type(s).name() for s in projection.summary.skills]
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Advanced training: increase any existing skill by one level',
                options=existing_skills,
            )
        )


# ── event 8: illegal information ─────────────────────────────────────────────


def _handle_citizen_event_8(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Citizen',
            roll=8,
            instruction=(
                'Use the illegal information (roll Streetwise 8+: success = extra Benefit roll, '
                'fail = ejected, gain Rival) or refuse (DM+2 to next advancement)?'
            ),
            options=['use_it', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_citizen_event_8(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _career_progress_pending, _current_career

    career = _current_career(projection)
    if event.choice == 'refuse':
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
        projection.pending_inputs.append(_career_progress_pending(career, projection, event.id))
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Citizen',
                roll=8,
                context='citizen_event_8_skill',
                instruction='Roll Streetwise 8+: success = extra Benefit roll; fail = ejected, gain Rival',
                options=['Streetwise'],
            )
        )


def _resolve_citizen_event_8_skill(projection: CharacterProjection, event: SkillRollEvent) -> None:
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
        projection.summary.connections.append(Rival(source='Illegal information leak (Citizen event 8)'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = CitizenCareerData

EFFECT_HANDLERS: dict[str, object] = {
    'citizen_mishap_4': _handle_citizen_mishap_4,
    'citizen_mishap_5': _handle_citizen_mishap_5,
    'citizen_event_6': _handle_citizen_event_6,
    'citizen_event_8': _handle_citizen_event_8,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'citizen_mishap_5': _resolve_citizen_mishap_5,
    'citizen_event_6': _resolve_citizen_event_6,
    'citizen_event_8_skill': _resolve_citizen_event_8_skill,
}

CHOICE_HANDLERS: dict[str, object] = {
    'citizen_mishap_4': _choice_citizen_mishap_4,
    'citizen_event_8': _choice_citizen_event_8,
}
