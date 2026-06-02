from ceres.character.benefits import (
    ALLY,
    CONTACT,
    SHIP_SHARE,
    WEAPON,
    CharacteristicIncrease,
)
from ceres.character.careers.career_data import (
    AssignmentData,
    AutoAdvanceEffect,
    BenefitDmEffect,
    Career,
    CareerData,
    CareerDispatchEffect,
    CareerEventEntry,
    CareerSkillTables,
    CharCheck,
    DecreaseCharacteristicEffect,
    GainEnemyEffect,
    InjuryEffect,
    LifeEventEffect,
    MishapEntry,
    MusterOutData,
    MusterOutRow,
    RankBonus,
    RankEntry,
    RollMishapEffect,
    SkillChoiceEffect,
    SkillTable,
)
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingCareerEvent,
    PendingCareerSkillRoll,
    PendingInjuryTable,
    PendingSkillChoice,
    SkillRollEvent,
    career_progress_pending,
)
from ceres.character.skills import (
    Animals,
    Astrogation,
    Athletics,
    Carouse,
    Deception,
    Drive,
    GunCombat,
    JackOfAllTrades,
    LanguageSkill,
    Leadership,
    Mechanic,
    Melee,
    Pilot,
    ProfessionSkill,
    Recon,
    Seafarer,
    Stealth,
    Streetwise,
    Survival,
    VaccSuit,
    skill_instances,
)
from ceres.character.state import (
    CharacterProjection,
    Enemy,
    Rival,
    ScheduledEffect,
)


class DrifterCareerData(CareerData):
    def _basic_training_table_name(self, assignment) -> str:
        return assignment.name.lower()


DRIFTER = Career(
    name='Drifter',
    description=(
        'Wanderers, hitchhikers and travellers, drifters are'
        'those who roam the stars without obvious purpose or direction.'
    ),
)

CAREER_DATA = DrifterCareerData(
    career=DRIFTER,
    allows_assignment_change=True,
    qualification=CharCheck(characteristic=Chars.END, target=0),
    assignments=[
        AssignmentData(
            name='Barbarian',
            description='You live on a primitive world without the benefits of technology.',
            survival=CharCheck(characteristic=Chars.END, target=7),
            advancement=CharCheck(characteristic=Chars.STR, target=7),
        ),
        AssignmentData(
            name='Wanderer',
            description='You are a space bum, living hand-to-mouth in slums and spaceports across the galaxy.',
            survival=CharCheck(characteristic=Chars.END, target=7),
            advancement=CharCheck(characteristic=Chars.INT, target=7),
        ),
        AssignmentData(
            name='Scavenger',
            description='You work as a belter (asteroid miner) or on a salvage crew.',
            survival=CharCheck(characteristic=Chars.DEX, target=7),
            advancement=CharCheck(characteristic=Chars.END, target=7),
        ),
    ],
    skill_tables=CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.STR,
                Chars.END,
                Chars.DEX,
                skill_instances(LanguageSkill),
                skill_instances(ProfessionSkill),
                JackOfAllTrades(),
            ]
        ),
        service_skills=SkillTable(
            [
                Athletics(),
                [Melee()],
                Recon(),
                Streetwise(),
                Stealth(),
                Survival(),
            ]
        ),
        assignment1=SkillTable(
            [  # Barbarian
                Animals(),
                Carouse(),
                [Melee()],
                Stealth(),
                [Seafarer()],
                Survival(),
            ]
        ),
        assignment2=SkillTable(
            [  # Wanderer
                Drive(),
                Deception(),
                Recon(),
                Stealth(),
                Streetwise(),
                Survival(),
            ]
        ),
        assignment3=SkillTable(
            [  # Scavenger
                [Pilot()],
                Mechanic(),
                Astrogation(),
                VaccSuit(),
                skill_instances(ProfessionSkill),
                GunCombat(),
            ]
        ),
    ),
    ranks={
        0: RankEntry(rank=0),
        1: RankEntry(rank=1),
        2: RankEntry(rank=2),
        3: RankEntry(rank=3),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5),
        6: RankEntry(rank=6),
    },
    ranks_by_assignment={
        1: {  # Barbarian
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(skill=Survival(), level=1)),
            2: RankEntry(rank=2, title='Warrior', bonus=RankBonus(skill=Melee(), level=1)),
            3: RankEntry(rank=3),
            4: RankEntry(rank=4, title='Chieftain', bonus=RankBonus(skill=Leadership(), level=1)),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6, title='Warlord'),
        },
        2: {  # Wanderer
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(skill=Streetwise(), level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, bonus=RankBonus(skill=Deception(), level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6),
        },
        3: {  # Scavenger
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(skill=VaccSuit(), level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, bonus=RankBonus(skill=Mechanic(), level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6),
        },
    },
    muster_out=MusterOutData(
        rows={
            1: MusterOutRow(cash=0, benefit=CONTACT),
            2: MusterOutRow(cash=0, benefit=WEAPON),
            3: MusterOutRow(cash=1000, benefit=ALLY),
            4: MusterOutRow(cash=2000, benefit=WEAPON),
            5: MusterOutRow(cash=3000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            6: MusterOutRow(cash=4000, benefit=SHIP_SHARE),
            7: MusterOutRow(cash=8000, benefit=SHIP_SHARE, count=2),
        }
    ),
    mishaps={
        1: MishapEntry(
            text='Severely injured.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='Injured. Roll on the Injury table.',
            effects=[InjuryEffect(severity='from_table')],
        ),
        3: MishapEntry(
            text='You run afoul of a criminal gang, corrupt bureaucrat or other foe. Gain an Enemy.',
            effects=[GainEnemyEffect()],
        ),
        4: MishapEntry(
            text='You suffer from a life-threatening illness. Reduce your END by 1.',
            effects=[DecreaseCharacteristicEffect(characteristic=Chars.END, amount=1)],
        ),
        5: MishapEntry(
            text='Betrayed by a friend. Gain a Rival. Roll 2D — on a natural 2, you must take the Prisoner career next term.',
            defer_ejection=True,
            effects=[CareerDispatchEffect(type='drifter_mishap_5')],
        ),
        6: MishapEntry(
            text='You do not know what happened to you. There is a gap in your memory.',
            effects=[],
        ),
    },
    events={
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='A patron offers you a chance at a job.',
            effects=[CareerDispatchEffect(type='drifter_event_3')],
        ),
        4: CareerEventEntry(
            text='You pick up a few useful skills here and there.',
            effects=[SkillChoiceEffect(options=['Jack-of-All-Trades', 'Survival', 'Streetwise', 'Melee'], level=1)],
        ),
        5: CareerEventEntry(
            text='You manage to scavenge something of use.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        6: CareerEventEntry(
            text='You encounter something unusual.',
            effects=[LifeEventEffect()],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='You are attacked by enemies.',
            effects=[CareerDispatchEffect(type='drifter_event_8')],
        ),
        9: CareerEventEntry(
            text='You are offered a chance to take part in a risky but rewarding adventure.',
            effects=[CareerDispatchEffect(type='drifter_event_9')],
        ),
        10: CareerEventEntry(
            text='Life on the edge hones your abilities.',
            effects=[SkillChoiceEffect(options=[], level=1)],
        ),
        11: CareerEventEntry(
            text='You are forcibly drafted.',
            effects=[CareerDispatchEffect(type='drifter_event_11')],
        ),
        12: CareerEventEntry(
            text='You thrive on adversity. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    },
)


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
    from ceres.character.careers.prisoner import PRISONER
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
    projection.summary.connections.append(Rival(source='Former friend who betrayed you (Drifter mishap 5)'))
    if event.modified_roll == 2:
        projection.forced_next_career = PRISONER
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
    projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


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
    from ceres.character.careers.prisoner import PRISONER

    career = projection.get_current_career()
    if event.choice == 'decline':
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
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
        projection.forced_next_career = PRISONER
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
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id, 1))
    elif roll == 3:
        projection.pending_inputs.append(
            PendingInjuryTable(
                id=f'{event.id}.0',
                instruction='Risky adventure (3): roll 1D on Injury table',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id, 1))
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
    projection.pending_inputs.append(career_progress_pending(projection, career, event_id))
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
