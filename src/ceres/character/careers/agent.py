from ceres.character.careers.career_data import AssignmentData, CareerData, CareerDispatchEffect
from ceres.character.characteristics import Chars
from ceres.character.events import SkillRollEvent
from ceres.character.projection import (
    CharacterProjection,
    Enemy,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
    PendingDoubleInjuryRoll,
    PendingMishap,
    PendingSkillChoice,
)


class AgentCareerData(CareerData):
    def prior_terms(self, terms, assignment: AssignmentData) -> list:
        return [term for term in terms if term.career == self.name and term.assignment == assignment.name]


# ── mishap 2: criminal deal ───────────────────────────────────────────────────


def _handle_agent_mishap_2(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=2,
            instruction=(
                'Accept (leave without further penalty, lose Benefit roll as normal) or Refuse '
                '(roll twice on Injury table take lower, gain Enemy, choose skill)?'
            ),
            options=['accept', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_agent_mishap_2(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    career = _current_career(projection)
    pending_idx = 0
    if event.choice == 'refuse':
        projection.summary.connections.append(Enemy(source='Refused criminal deal (Agent mishap)'))
        projection.pending_inputs.append(
            PendingDoubleInjuryRoll(
                id=f'{event.id}.{pending_idx}',
                instruction='Refused: roll twice on the Injury table and provide both results — lower applies',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        pending_idx += 1
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.{pending_idx}',
                instruction='Refused criminal deal: choose any skill to gain at level 1',
                options=[],
            )
        )
        pending_idx += 1
    _apply_mishap_ejection(projection, career, event.id, pending_idx, lose_current_term=True)


# ── mishap 3: investigation gone wrong ───────────────────────────────────────


def _handle_agent_mishap_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=3,
            context='agent_mishap_3',
            instruction='Roll Advocate 8+ to keep the Benefit roll from this term',
            options=['Advocate'],
        )
    )
    return pending_idx + 1


def _resolve_agent_mishap_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.careers.loader import load_careers
    from ceres.character.replay import _apply_muster_out_setup

    career_name = projection.summary.current_career
    career = load_careers().get(career_name or '')
    if career is None:
        return

    succeed = event.modified_roll >= 8
    if event.modified_roll <= 2:
        projection.forced_next_career = 'Prisoner'
    _apply_muster_out_setup(projection, career, event.id, 0, lose_current_term=not succeed)


# ── mishap 5: someone close gets hurt ────────────────────────────────────────


def _handle_agent_mishap_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=5,
            instruction='Choose who was hurt: a Contact, an Ally, or a family member?',
            options=['contact', 'ally', 'family'],
        )
    )
    return pending_idx + 1


def _choice_agent_mishap_5(projection: CharacterProjection, event) -> None:
    from ceres.character.replay import _apply_mishap_ejection, _current_career

    career = _current_career(projection)
    projection.summary.problems.append(
        f'Agent mishap 5: your {event.choice} was hurt — roll twice on the Injury table for them '
        'and apply the lower result (NPC injury; no mechanical effect on your character).'
    )
    _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── event 3: dangerous investigation ─────────────────────────────────────────


def _handle_agent_event_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=3,
            context='agent_event_3',
            instruction='Roll Investigate 8+ or Streetwise 8+',
            options=['Investigate', 'Streetwise'],
        )
    )
    return pending_idx + 1


def _resolve_agent_event_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction=(
                    'Investigation success: increase one skill by one level — Deception, '
                    'Jack-of-all-Trades, Persuade or Tactics'
                ),
                options=['Deception', 'Jack-of-all-Trades', 'Persuade', 'Tactics'],
            )
        )
    else:
        projection.pending_inputs.append(
            PendingMishap(
                id=f'{event.id}.0',
                instruction='Investigation went wrong: roll 1D on Mishap table (you are not ejected from this career)',
            )
        )


# ── event 6: advanced training ───────────────────────────────────────────────


def _handle_agent_event_6(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=6,
            context='agent_event_6',
            instruction='Roll EDU 8+ to increase any one skill you already have by one level',
            options=[Chars.EDU],
        )
    )
    return pending_idx + 1


def _resolve_agent_event_6(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        existing_skills = [type(s).name() for s in projection.summary.skills]
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Advanced training: increase any existing skill by one level',
                options=existing_skills,
            )
        )


# ── event 8: undercover mission ──────────────────────────────────────────────


def _handle_agent_event_8(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=8,
            context='agent_event_8',
            instruction='Roll Deception 8+ for the undercover mission',
            options=['Deception'],
        )
    )
    return pending_idx + 1


def _resolve_agent_event_8(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.problems.append(
            'Undercover mission success: roll on Rogue or Citizen Events table and '
            'make one roll on any Specialist skill table for that career (apply manually — '
            'cross-career table automation not yet implemented).'
        )
    else:
        projection.summary.problems.append(
            'Undercover mission failed: roll on Rogue or Citizen Mishap table '
            '(apply manually — cross-career table automation not yet implemented).'
        )


# ── event 11: senior agent mentor ────────────────────────────────────────────


def _handle_agent_event_11(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillChoice(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=11,
            advancement_precreated=False,
            instruction='Senior agent mentor: increase Investigate by one level or DM+4 to your next advancement roll',
            options=['Investigate', 'advancement_dm_4'],
        )
    )
    return pending_idx + 1


# ── handler registries ────────────────────────────────────────────────────────

EFFECT_HANDLERS: dict[str, object] = {
    'agent_mishap_2_choice': _handle_agent_mishap_2,
    'agent_mishap_3': _handle_agent_mishap_3,
    'agent_mishap_5_choice': _handle_agent_mishap_5,
    'agent_event_3': _handle_agent_event_3,
    'agent_event_6': _handle_agent_event_6,
    'agent_event_8': _handle_agent_event_8,
    'agent_event_11': _handle_agent_event_11,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'agent_mishap_3': _resolve_agent_mishap_3,
    'agent_event_3': _resolve_agent_event_3,
    'agent_event_6': _resolve_agent_event_6,
    'agent_event_8': _resolve_agent_event_8,
}

CHOICE_HANDLERS: dict[str, object] = {
    'agent_mishap_2': _choice_agent_mishap_2,
    'agent_mishap_5': _choice_agent_mishap_5,
}

CAREER_DATA_CLASS = AgentCareerData
