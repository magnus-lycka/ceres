from ceres.character.careers.career_data import AssignmentData, CareerData, CareerDispatchEffect
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    PendingDoubleInjuryRoll,
    PendingInjuryTable,
    PendingParoleRoll,
    PendingSkillChoice,
    SkillRollEvent,
    career_progress_pending,
    muster_out_setup,
)
from ceres.character.state import (
    Ally,
    CharacterProjection,
    Enemy,
)


class PrisonerCareerData(CareerData):
    def start_career(
        self,
        projection: CharacterProjection,
        assignment: AssignmentData,
        event_id: int,
        qualification_roll: int,
    ) -> None:
        projection.summary.current_career = self.name
        projection.summary.current_assignment = assignment.name
        count_before = len(projection.pending_inputs)
        self.start_new_term(projection, assignment, event_id)
        pending_added = len(projection.pending_inputs) - count_before
        projection.pending_inputs.append(
            PendingParoleRoll(
                id=f'{event_id}.{pending_added}',
                instruction='Roll 1D to determine your Parole Threshold (result + 2)',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )


# ── mishap 3: prison gang ─────────────────────────────────────────────────────


def _handle_prisoner_mishap_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Prisoner',
            roll=3,
            instruction='Prison gang attack: fight back (roll Melee 8+) or submit (lose Benefit roll)?',
            options=['fight', 'submit'],
        )
    )
    return pending_idx + 1


def _choice_prisoner_mishap_3(projection: CharacterProjection, event) -> None:
    from ceres.character.events import _advancement_pending

    career = projection.get_current_career()
    if event.choice == 'submit':
        projection.summary.problems.append(
            'Prison gang (Prisoner mishap 3): submitted — lose your Benefit roll for this term.'
        )
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id)
        )
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Prisoner',
                roll=3,
                context='prisoner_mishap_3_fight',
                instruction='Roll Melee 8+: success = gain Enemy + PT+1; fail = roll twice on Injury table',
                options=['Melee'],
            )
        )


def _resolve_prisoner_mishap_3_fight(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.events import _advancement_pending

    career = projection.get_current_career()
    if event.modified_roll >= 8:
        projection.summary.connections.append(Enemy(source='Prison gang leader (Prisoner mishap 3)'))
        projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 1)
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id)
        )
    else:
        projection.pending_inputs.append(
            PendingDoubleInjuryRoll(
                id=f'{event.id}.0',
                instruction='Gang fight: roll twice on the Injury table, apply lower result',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id, 1)
        )


# ── event 3: escape opportunity ───────────────────────────────────────────────


def _handle_prisoner_event_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Prisoner',
            roll=3,
            instruction='Attempt to escape the prison (Stealth or Deception 10+) or stay?',
            options=['attempt', 'stay'],
        )
    )
    return pending_idx + 1


def _choice_prisoner_event_3(projection: CharacterProjection, event) -> None:
    career = projection.get_current_career()
    if event.choice == 'stay':
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Prisoner',
                roll=3,
                context='prisoner_event_3_escape',
                instruction='Roll Stealth or Deception 10+: success = escape (freed); fail = PT+2',
                options=['Stealth', 'Deception'],
            )
        )


def _resolve_prisoner_event_3_escape(projection: CharacterProjection, event: SkillRollEvent) -> None:
    career = projection.get_current_career()
    if event.modified_roll >= 10:
        projection.summary.narrative.append('Prisoner event 3: escaped from prison — career ends.')
        muster_out_setup(projection, career, event.id, 0, lose_current_term=False)
    else:
        projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 2)
        projection.summary.narrative.append('Prisoner event 3: escape failed — Parole Threshold +2.')
        # _apply_skill_roll auto-queues advancement since no pending was added


# ── event 4: hard labour ──────────────────────────────────────────────────────


def _handle_prisoner_event_4(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Prisoner',
            roll=4,
            context='prisoner_event_4',
            instruction='Roll END 8+: success = PT-1 + skill choice; fail = PT+1',
            options=[Chars.END],
        )
    )
    return pending_idx + 1


def _resolve_prisoner_event_4(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 1)
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Hard labour endured: choose Athletics, Mechanic, or Melee (unarmed)',
                options=['Athletics', 'Mechanic', 'Melee'],
            )
        )
    else:
        projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 1)
    # _apply_skill_roll auto-queues advancement when no pending added (fail case)
    # For success: skill choice is pending; advancement queued after it resolves via _apply_skill_choice


# ── event 5: gang opportunity ─────────────────────────────────────────────────


def _handle_prisoner_event_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Prisoner',
            roll=5,
            context='prisoner_event_5',
            instruction='Roll Persuade or Melee 8+ to join the gang: success = PT+1 + skill; fail = gain Enemy',
            options=['Persuade', 'Melee'],
        )
    )
    return pending_idx + 1


def _resolve_prisoner_event_5(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 1)
        projection.summary.problems.append(
            'Prisoner event 5: joined a gang — gain DM+1 to survival rolls while in this career.'
        )
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Joined gang: choose Persuade, Melee, or Stealth',
                options=['Persuade', 'Melee', 'Stealth'],
            )
        )
    else:
        projection.summary.connections.append(Enemy(source='Prison gang (Prisoner event 5)'))
    # Fail: _apply_skill_roll auto-queues advancement (no pending added)
    # Success: skill choice queued; advancement queued after it resolves


# ── event 6: vocational training ─────────────────────────────────────────────


def _handle_prisoner_event_6(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Prisoner',
            roll=6,
            context='prisoner_event_6',
            instruction='Roll EDU 8+ to gain any skill at level 1',
            options=[Chars.EDU],
        )
    )
    return pending_idx + 1


def _resolve_prisoner_event_6(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        from ceres.character.skills import AnySkill, _skill_classes

        all_skills = sorted(
            cls.name()
            for cls in _skill_classes(AnySkill)
            if cls.name() not in {'Jack-of-all-Trades', 'Jack-of-All-Trades'}
        )
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Vocational training: choose any skill at level 1',
                options=all_skills,
            )
        )
    # Fail or success-with-pending: _apply_skill_roll handles advancement correctly


# ── event 7: prison event sub-table ──────────────────────────────────────────


def _handle_prisoner_event_7(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Prisoner',
            roll=7,
            instruction=(
                'Prison Event: roll 1D (1=Riot, 2=Gang, 3=Transfer, 4=Visitation, 5=Parole Hearing, 6=Good Behaviour)'
            ),
            options=['1', '2', '3', '4', '5', '6'],
        )
    )
    return pending_idx + 1


def _choice_prisoner_event_7(projection: CharacterProjection, event) -> None:
    career = projection.get_current_career()
    sub = event.choice
    if sub == '1':
        # Riot — roll END 8+
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Prisoner',
                roll=7,
                context='prisoner_event_7_riot',
                instruction='Riot: roll END 8+: success = survive unhurt; fail = roll on Injury table',
                options=[Chars.END],
            )
        )
    elif sub == '2':
        # Forced into gang — PT +1, gain Enemy
        projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 1)
        projection.summary.connections.append(Enemy(source='Prison gang (Prisoner event 7, forced)'))
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
    elif sub == '3':
        # Transfer to another prison
        projection.summary.problems.append(
            'Prisoner event 7: transferred to another prison — no mechanical effect. Apply manually if needed.'
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
    elif sub == '4':
        # Visitation rights restored — gain Ally
        projection.summary.connections.append(Ally(source='Visitor (Prisoner event 7)'))
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
    elif sub == '5':
        # Parole hearing — PT -1
        projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 1)
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
    else:  # '6'
        # Good behaviour — PT -1
        projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 1)
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


def _resolve_prisoner_event_7_riot(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.events import _advancement_pending

    career = projection.get_current_career()
    if event.modified_roll < 8:
        projection.pending_inputs.append(
            PendingInjuryTable(
                id=f'{event.id}.0',
                instruction='Riot injury: roll 1D on Injury table',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id, 1)
        )
    # Success: _apply_skill_roll auto-queues advancement


# ── event 9: hire lawyer ──────────────────────────────────────────────────────


def _handle_prisoner_event_9(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Prisoner',
            roll=9,
            instruction=(
                'Hire a lawyer? Level 1 (Cr1000), Level 2 (Cr2000), Level 3 (Cr3000), or decline? '
                'Success (2D + level vs 8+) = PT-1.'
            ),
            options=['level_1', 'level_2', 'level_3', 'decline'],
        )
    )
    return pending_idx + 1


def _choice_prisoner_event_9(projection: CharacterProjection, event) -> None:
    career = projection.get_current_career()
    if event.choice == 'decline':
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
        return
    level = int(event.choice[-1])
    projection.summary.problems.append(
        f'Prisoner event 9: lawyer level {level} hired — deduct Cr{level * 1000} from cash. Apply manually.'
    )
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event.id}.0',
            career='Prisoner',
            roll=9,
            context=f'prisoner_event_9_level_{level}',
            instruction=f'Roll 2D + {level} vs 8+: success = PT-1',
            options=[],
        )
    )


def _resolve_prisoner_event_9(projection: CharacterProjection, event: SkillRollEvent) -> None:
    level = int(event.context[-1])
    if event.modified_roll + level >= 8:
        projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 1)
    # _apply_skill_roll auto-queues advancement


# ── event 12: heroism ─────────────────────────────────────────────────────────


def _handle_prisoner_event_12(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Prisoner',
            roll=12,
            instruction='An act of heroism: take the risk (roll 2D — 7-: injury; 8+: Ally + PT-2) or refuse?',
            options=['take_risk', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_prisoner_event_12(projection: CharacterProjection, event) -> None:
    career = projection.get_current_career()
    if event.choice == 'refuse':
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
    else:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event.id}.0',
                career='Prisoner',
                roll=12,
                context='prisoner_event_12_heroism',
                instruction='Roll 2D: 8+ = Ally + PT-2; 7 or less = roll on Injury table',
                options=[],
            )
        )


def _resolve_prisoner_event_12_heroism(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.events import _advancement_pending

    career = projection.get_current_career()
    if event.modified_roll >= 8:
        projection.summary.connections.append(Ally(source='Saved fellow prisoner (Prisoner event 12)'))
        projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 2)
        # _apply_skill_roll auto-queues advancement (no pending added)
    else:
        projection.pending_inputs.append(
            PendingInjuryTable(
                id=f'{event.id}.0',
                instruction='Heroism failed: roll 1D on Injury table',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment or '', event.id, 1)
        )


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = PrisonerCareerData

EFFECT_HANDLERS: dict[str, object] = {
    'prisoner_mishap_3': _handle_prisoner_mishap_3,
    'prisoner_event_3': _handle_prisoner_event_3,
    'prisoner_event_4': _handle_prisoner_event_4,
    'prisoner_event_5': _handle_prisoner_event_5,
    'prisoner_event_6': _handle_prisoner_event_6,
    'prisoner_event_7': _handle_prisoner_event_7,
    'prisoner_event_9': _handle_prisoner_event_9,
    'prisoner_event_12': _handle_prisoner_event_12,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'prisoner_mishap_3_fight': _resolve_prisoner_mishap_3_fight,
    'prisoner_event_3_escape': _resolve_prisoner_event_3_escape,
    'prisoner_event_4': _resolve_prisoner_event_4,
    'prisoner_event_5': _resolve_prisoner_event_5,
    'prisoner_event_6': _resolve_prisoner_event_6,
    'prisoner_event_7_riot': _resolve_prisoner_event_7_riot,
    'prisoner_event_9_level_1': _resolve_prisoner_event_9,
    'prisoner_event_9_level_2': _resolve_prisoner_event_9,
    'prisoner_event_9_level_3': _resolve_prisoner_event_9,
    'prisoner_event_12_heroism': _resolve_prisoner_event_12_heroism,
}

CHOICE_HANDLERS: dict[str, object] = {
    'prisoner_mishap_3': _choice_prisoner_mishap_3,
    'prisoner_event_3': _choice_prisoner_event_3,
    'prisoner_event_7': _choice_prisoner_event_7,
    'prisoner_event_9': _choice_prisoner_event_9,
    'prisoner_event_12': _choice_prisoner_event_12,
}
