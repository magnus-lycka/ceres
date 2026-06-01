from ceres.character.careers.career_data import CareerDispatchEffect
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
    PendingSkillChoice,
    SkillRollEvent,
    muster_out_setup,
)
from ceres.character.skills import ScienceSkill, skill_list, skill_names_for_category
from ceres.character.state import (
    CharacterProjection,
    Enemy,
)

_SCIENCES = sorted(s.type for s in skill_list(ScienceSkill))

# ── event 3: research against conscience ─────────────────────────────────────


def _handle_scholar_event_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Scholar',
            roll=3,
            instruction='Accept (2 Science specialties + D3 Enemies + extra Benefit roll) or Decline?',
            options=['accept', 'decline'],
        )
    )
    return pending_idx + 1


def _choice_scholar_event_3(projection: CharacterProjection, event) -> None:
    from ceres.character.events import PendingConnectionsRoll, PendingMusterOut, _advancement_pending

    if event.choice == 'accept':
        projection.pending_inputs.append(
            PendingConnectionsRoll(
                id=f'{event.id}.0',
                instruction='Roll D3 for number of Enemies gained',
                options=['1', '2', '3'],
            )
        )
        for i, label in enumerate(['first', 'second'], start=1):
            projection.pending_inputs.append(
                PendingCareerSkillChoice(
                    id=f'{event.id}.{i}',
                    career='Scholar',
                    roll=3,
                    mishap=False,
                    advancement_precreated=True,
                    instruction=f'Choose {label} Science specialty to increase by one level',
                    options=skill_names_for_category('Science') or [],
                )
            )
        if projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id, 3)
            )
        # Extra benefit roll
        projection.muster_out_career = projection.summary.current_career
        projection.pending_inputs.append(
            PendingMusterOut(
                id=f'{event.id}.4',
                instruction='Extra Benefit roll (accepted research against conscience)',
                options=['cash', 'benefits'],
            )
        )
    elif projection.summary.current_career is not None:
        career = projection.get_current_career()
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id)
        )


# ── event 6: advanced training ───────────────────────────────────────────────


def _handle_scholar_event_6(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Scholar',
            roll=6,
            context='scholar_event_6',
            instruction='Roll EDU 8+ to gain any skill of your choice at level 1',
            options=[Chars.EDU],
        )
    )
    return pending_idx + 1


def _resolve_scholar_event_6(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Choose any skill to gain at level 1',
                options=[],
            )
        )
    # failure: _apply_skill_roll creates advancement pending


# ── event 8: opportunity to cheat ────────────────────────────────────────────


def _handle_scholar_event_8(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Scholar',
            roll=8,
            instruction='Refuse (nothing) or Accept (roll Deception/Admin 8+)?',
            options=['accept', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_scholar_event_8(projection: CharacterProjection, event) -> None:
    from ceres.character.events import _advancement_pending

    if event.choice == 'refuse':
        if projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment or '', event.id)
            )
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Scholar',
                roll=8,
                context='scholar_event_8_roll',
                instruction='Roll Deception 8+ or Admin 8+ to cheat successfully',
                options=['Deception', 'Admin'],
            )
        )


def _resolve_scholar_event_8_roll(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.connections.append(Enemy(source='Cheating in the field'))
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Cheat succeeded: choose any skill to gain +1',
                options=[],
            )
        )
    else:
        projection.summary.connections.append(Enemy(source='Cheating discovered'))
    # _apply_skill_roll creates advancement if no new pending (failure), or after skill_choice (success)


# ── event 11: brilliant mentor ────────────────────────────────────────────────


def _handle_scholar_event_11(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillChoice(
            id=f'{event_id}.{pending_idx}',
            career='Scholar',
            roll=11,
            advancement_precreated=False,
            instruction='Increase Science by one level (choose which), or DM+4 to your next advancement roll',
            options=[*_SCIENCES, 'advancement_dm_4'],
        )
    )
    return pending_idx + 1


# ── mishap 3: planetary interference ─────────────────────────────────────────


def _handle_scholar_mishap_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Scholar',
            roll=3,
            instruction='Continue openly (Science +1, Enemy) or secretly (Science +1, SOC -2)?',
            options=['openly', 'secretly'],
        )
    )
    return pending_idx + 1


def _choice_scholar_mishap_3(projection: CharacterProjection, event) -> None:
    if event.choice == 'openly':
        projection.summary.connections.append(Enemy(source='Planetary government interference'))
    else:
        soc = projection.summary.characteristics.get(Chars.SOC, 0)
        projection.summary.characteristics[Chars.SOC] = max(0, soc - 2)
    projection.pending_inputs.append(
        PendingCareerSkillChoice(
            id=f'{event.id}.0',
            career='Scholar',
            roll=3,
            mishap=True,
            advancement_precreated=True,
            instruction='Increase Science by one level: choose which broad science',
            options=skill_names_for_category('Science') or [],
        )
    )
    # advancement was already created by _apply_mishap (stay_in_career=True)


# ── mishap 5: work sabotaged ──────────────────────────────────────────────────


def _handle_scholar_mishap_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Scholar',
            roll=5,
            instruction='Give up (leave career) or start again (stay, lose benefit rolls)?',
            options=['give_up', 'start_again'],
        )
    )
    return pending_idx + 1


def _choice_scholar_mishap_5(projection: CharacterProjection, event) -> None:
    from ceres.character.events import PendingAdvancement, PendingAgingRoll

    if event.choice == 'give_up':
        career = projection.get_current_career()
        projection.pending_inputs = [p for p in projection.pending_inputs if not isinstance(p, PendingAdvancement)]
        projection.summary.age += 4
        if projection.summary.age >= 34:
            projection.muster_out_career = career.name
            projection.clear_current_career()
            projection.pending_inputs.append(PendingAgingRoll(id=f'{event.id}.0', instruction='Roll 2D on Aging table'))
        else:
            muster_out_setup(projection, career, event.id, 0, lose_current_term=True)
    # 'start_again': advancement is already there from _apply_mishap, career stays


# ── handler registries ───────────────────────────────────────────────────────

EFFECT_HANDLERS: dict[str, object] = {
    'scholar_event_3': _handle_scholar_event_3,
    'scholar_event_6': _handle_scholar_event_6,
    'scholar_event_8': _handle_scholar_event_8,
    'scholar_event_11': _handle_scholar_event_11,
    'scholar_mishap_3_choice': _handle_scholar_mishap_3,
    'scholar_mishap_5_choice': _handle_scholar_mishap_5,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'scholar_event_6': _resolve_scholar_event_6,
    'scholar_event_8_roll': _resolve_scholar_event_8_roll,
}

CHOICE_HANDLERS: dict[str, object] = {
    'scholar_event_3': _choice_scholar_event_3,
    'scholar_event_8': _choice_scholar_event_8,
    'scholar_mishap_3': _choice_scholar_mishap_3,
    'scholar_mishap_5': _choice_scholar_mishap_5,
}
