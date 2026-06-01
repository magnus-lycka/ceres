from ceres.character.benefits import (
    ALLY,
    BLADE,
    CONTACT,
    DECEPTION,
    MELEE,
    PERSUADE,
    RECON,
    STEALTH,
    STREETWISE,
    CharacteristicIncrease,
    ChoiceBenefit,
    CombinedBenefit,
)
from ceres.character.careers.career_data import (
    AssignmentData,
    CareerData,
    CareerDispatchEffect,
    CareerEventEntry,
    CareerSkillTables,
    CharCheck,
    DecreaseCharacteristicEffect,
    GainEnemyEffect,
    InjuryEffect,
    MishapEntry,
    MusterOutData,
    MusterOutRow,
    ParoleThresholdChangeEffect,
    RankBonus,
    RankEntry,
    RollMishapEffect,
    SkillChoiceEffect,
    SkillTable,
)
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
from ceres.character.skills import (
    Admin,
    Advocate,
    Athletics,
    Broker,
    Deception,
    Gambler,
    Investigate,
    JackOfAllTrades,
    Mechanic,
    Melee,
    Persuade,
    ProfessionSkill,
    Stealth,
    Streetwise,
    Survival,
    skill_instances,
)
from ceres.character.state import (
    Ally,
    CharacterProjection,
    Enemy,
)


class PrisonerCareerData(CareerData):
    def advancement_is_special(self) -> bool:
        return True

    def start_career(
        self,
        projection: CharacterProjection,
        assignment: AssignmentData,
        event_id: int,
        qualification_roll: int,
    ) -> None:
        projection.summary.current_career = self.name
        projection.summary.current_assignment = assignment.name
        projection.summary.current_assignment_index = self.assignment_index(assignment)
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


CAREER_DATA = PrisonerCareerData(
    name='Prisoner',
    description=(
        'Every society has its bad apples and even in the far future punishments usually take place within '
        'faceless institutions where criminals can be conveniently forgotten.'
    ),
    source='Core',
    selectable=False,
    allows_assignment_change=True,
    qualification=CharCheck(characteristic=Chars.END, target=0),
    assignments=[
        AssignmentData(
            name='Inmate',
            description='You just try to get through your time in prison without getting into trouble.',
            survival=CharCheck(characteristic=Chars.END, target=7),
            advancement=CharCheck(characteristic=Chars.STR, target=7),
        ),
        AssignmentData(
            name='Thug',
            description='You are part of a gang in prison, terrorising the other inmates.',
            survival=CharCheck(characteristic=Chars.STR, target=8),
            advancement=CharCheck(characteristic=Chars.END, target=6),
        ),
        AssignmentData(
            name='Fixer',
            description='You can arrange anything – for the right price.',
            survival=CharCheck(characteristic=Chars.INT, target=9),
            advancement=CharCheck(characteristic=Chars.END, target=5),
        ),
    ],
    skill_tables=CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.STR,
                [Melee()],
                Chars.END,
                JackOfAllTrades(),
                Chars.EDU,
                Gambler(),
            ]
        ),
        service_skills=SkillTable(
            [
                Athletics(),
                Deception(),
                skill_instances(ProfessionSkill),
                Streetwise(),
                [Melee()],
                Persuade(),
            ]
        ),
        assignment1=SkillTable(
            [  # Inmate
                Stealth(),
                [Melee()],
                Streetwise(),
                Survival(),
                [Athletics()],
                Mechanic(),
            ]
        ),
        assignment2=SkillTable(
            [  # Thug
                Persuade(),
                [Melee()],
                [Melee()],
                [Melee()],
                [Athletics()],
                [Athletics()],
            ]
        ),
        assignment3=SkillTable(
            [  # Fixer
                Investigate(),
                Broker(),
                Deception(),
                Streetwise(),
                Stealth(),
                Admin(),
            ]
        ),
    ),
    ranks={
        0: RankEntry(rank=0, bonus=RankBonus(skill=Melee(), level=1)),
        1: RankEntry(rank=1),
        2: RankEntry(rank=2, bonus=RankBonus(skill=Athletics(), level=1)),
        3: RankEntry(rank=3),
        4: RankEntry(rank=4, bonus=RankBonus(skill=Advocate(), level=1)),
        5: RankEntry(rank=5),
        6: RankEntry(rank=6, bonus=RankBonus(characteristic=Chars.END, level=1)),
    },
    muster_out=MusterOutData(
        rows={
            1: MusterOutRow(cash=0, benefit=CONTACT),
            2: MusterOutRow(cash=0, benefit=BLADE),
            3: MusterOutRow(cash=100, benefit=ChoiceBenefit(options=[DECEPTION, PERSUADE, STEALTH])),
            4: MusterOutRow(cash=200, benefit=ALLY),
            5: MusterOutRow(cash=500, benefit=ChoiceBenefit(options=[MELEE, RECON, STREETWISE])),
            6: MusterOutRow(
                cash=1000,
                benefit=ChoiceBenefit(
                    options=[
                        CharacteristicIncrease(char=Chars.STR, amount=1),
                        CharacteristicIncrease(char=Chars.END, amount=1),
                    ]
                ),
            ),
            7: MusterOutRow(cash=2500, benefit=CombinedBenefit(benefits=[DECEPTION, PERSUADE, STEALTH])),
        }
    ),
    mishaps={
        1: MishapEntry(
            text='Severely injured.',
            stay_in_career=True,
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='You are accused of assaulting a prison guard. Parole Threshold +2.',
            stay_in_career=True,
            effects=[ParoleThresholdChangeEffect(amount=2)],
        ),
        3: MishapEntry(
            text='A prison gang persecutes you.',
            stay_in_career=True,
            defer_ejection=True,
            effects=[CareerDispatchEffect(type='prisoner_mishap_3')],
        ),
        4: MishapEntry(
            text='A guard takes a dislike to you. Gain an Enemy and raise your Parole Threshold by +1.',
            stay_in_career=True,
            effects=[GainEnemyEffect(), ParoleThresholdChangeEffect(amount=1)],
        ),
        5: MishapEntry(
            text='Disgraced. Word of your criminal past reaches your homeworld. Lose 1 SOC.',
            stay_in_career=True,
            effects=[DecreaseCharacteristicEffect(characteristic=Chars.SOC, amount=1)],
        ),
        6: MishapEntry(
            text='Injured. Roll on the Injury table.',
            stay_in_career=True,
            effects=[InjuryEffect(severity='from_table')],
        ),
    },
    events={
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='You have the opportunity to escape the prison.',
            effects=[CareerDispatchEffect(type='prisoner_event_3')],
        ),
        4: CareerEventEntry(
            text='You are assigned to difficult or backbreaking labour.',
            effects=[CareerDispatchEffect(type='prisoner_event_4')],
        ),
        5: CareerEventEntry(
            text='You have the opportunity to join a gang.',
            effects=[CareerDispatchEffect(type='prisoner_event_5')],
        ),
        6: CareerEventEntry(
            text='Vocational Training.',
            effects=[CareerDispatchEffect(type='prisoner_event_6')],
        ),
        7: CareerEventEntry(
            text='Prison Event.',
            effects=[CareerDispatchEffect(type='prisoner_event_7')],
        ),
        8: CareerEventEntry(
            text='Parole hearing. Reduce your Parole Threshold by -1.',
            effects=[ParoleThresholdChangeEffect(amount=-1)],
        ),
        9: CareerEventEntry(
            text='You have the opportunity to hire a new lawyer.',
            effects=[CareerDispatchEffect(type='prisoner_event_9')],
        ),
        10: CareerEventEntry(
            text='Special Duty.',
            effects=[SkillChoiceEffect(options=['Admin', 'Advocate', 'Electronics', 'Steward'], level=1)],
        ),
        11: CareerEventEntry(
            text='The warden takes an interest in your case. Reduce your Parole Threshold by -2.',
            effects=[ParoleThresholdChangeEffect(amount=-2)],
        ),
        12: CareerEventEntry(
            text='Heroism.',
            effects=[CareerDispatchEffect(type='prisoner_event_12')],
        ),
    },
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
            _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id)
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
            _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id)
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
            _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id, 1)
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
            _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id, 1)
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
            _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id, 1)
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
