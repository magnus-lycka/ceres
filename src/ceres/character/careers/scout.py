from ceres.character.benefits import (
    SCOUT_SHIP,
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
    DecreaseCharacteristicChoiceEffect,
    GainConnectionsRolledEffect,
    GainEnemyEffect,
    GainRivalEffect,
    GainSkillEffect,
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
from ceres.character.characteristics import Chars, ConnectionKind
from ceres.character.events import (
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
    PendingMishap,
    PendingSkillChoice,
    SkillRollEvent,
)
from ceres.character.skills import (
    Astrogation,
    Athletics,
    Diplomat,
    Electronics,
    Engineer,
    Explosives,
    Flyer,
    GunCombat,
    JackOfAllTrades,
    LanguageSkill,
    Level,
    Mechanic,
    Medic,
    Navigation,
    Persuade,
    Pilot,
    Recon,
    ScienceSkill,
    Seafarer,
    Stealth,
    Streetwise,
    Survival,
    VaccSuit,
    skill_instances,
)
from ceres.character.state import (
    Ally,
    CharacterProjection,
    Contact,
    Enemy,
    ScheduledEffect,
)

SCOUT = Career(
    name='Scout',
    description=(
        'Members of the exploratory service. Scouts explore new areas, map and survey known or newly discovered'
        'areas and maintain communication ships which carry information and messages between the worlds of the galaxy.'
    ),
)


class ScoutCareerData(CareerData):
    pass


CAREER_DATA = ScoutCareerData(
    career=SCOUT,
    allows_assignment_change=True,
    qualification=CharCheck(characteristic=Chars.INT, target=5),
    assignments=[
        AssignmentData(
            name='Courier',
            description='You are responsible for shuttling messages and high value packages around the galaxy.',
            survival=CharCheck(characteristic=Chars.END, target=5),
            advancement=CharCheck(characteristic=Chars.EDU, target=9),
        ),
        AssignmentData(
            name='Surveyor',
            description='You visit border worlds and assess their worth.',
            survival=CharCheck(characteristic=Chars.END, target=6),
            advancement=CharCheck(characteristic=Chars.INT, target=8),
        ),
        AssignmentData(
            name='Explorer',
            description='You go wherever the map is blank, exploring unknown worlds and uncharted space.',
            survival=CharCheck(characteristic=Chars.END, target=7),
            advancement=CharCheck(characteristic=Chars.EDU, target=7),
        ),
    ],
    skill_tables=CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.STR,
                Chars.DEX,
                Chars.END,
                Chars.INT,
                Chars.EDU,
                JackOfAllTrades(),
            ]
        ),
        service_skills=SkillTable(
            [
                Pilot(),
                Survival(),
                Mechanic(),
                Astrogation(),
                VaccSuit(),
                GunCombat(),
            ]
        ),
        advanced_education=SkillTable(
            [
                Medic(),
                skill_instances(LanguageSkill),
                Seafarer(),
                Explosives(),
                skill_instances(ScienceSkill),
                JackOfAllTrades(),
            ],
            min_edu=8,
        ),
        assignment1=SkillTable(
            [  # Courier
                Electronics(),
                Flyer(),
                Pilot(),
                Engineer(),
                Athletics(),
                Astrogation(),
            ]
        ),
        assignment2=SkillTable(
            [  # Surveyor
                Electronics(),
                Persuade(),
                Pilot(),
                Navigation(),
                Diplomat(),
                Streetwise(),
            ]
        ),
        assignment3=SkillTable(
            [  # Explorer
                Electronics(),
                Pilot(),
                Engineer(),
                skill_instances(ScienceSkill),
                Stealth(),
                Recon(),
            ]
        ),
    ),
    ranks={
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, title='Scout', bonus=RankBonus(skill=VaccSuit(), level=1)),
        2: RankEntry(rank=2),
        3: RankEntry(rank=3, title='Senior Scout', bonus=RankBonus(skill=Pilot(), level=1)),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5),
        6: RankEntry(rank=6),
    },
    muster_out=MusterOutData(
        rows={
            1: MusterOutRow(cash=20000, benefit=SHIP_SHARE),
            2: MusterOutRow(cash=20000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            3: MusterOutRow(cash=30000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            4: MusterOutRow(cash=30000, benefit=WEAPON),
            5: MusterOutRow(cash=50000, benefit=WEAPON),
            6: MusterOutRow(cash=50000, benefit=SCOUT_SHIP),
            7: MusterOutRow(cash=50000, benefit=SCOUT_SHIP),
        }
    ),
    mishaps={
        1: MishapEntry(
            text='Severely injured.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='Psychologically damaged by your time in the scouts. Reduce your INT or SOC by 1.',
            effects=[DecreaseCharacteristicChoiceEffect(options=['INT', 'SOC'], amount=1)],
        ),
        3: MishapEntry(
            text=(
                'Your ship is damaged and you have to hitch-hike your way back across the stars. '
                'Gain 1D Contacts and D3 Enemies.'
            ),
            effects=[
                GainConnectionsRolledEffect(connection_type=ConnectionKind.CONTACT, dice='1d6'),
                GainConnectionsRolledEffect(connection_type=ConnectionKind.ENEMY, dice='d3'),
            ],
        ),
        4: MishapEntry(
            text=(
                'You inadvertently cause a conflict between the Imperium and a minor world or species. '
                'Gain a Rival and Diplomat 1.'
            ),
            effects=[
                GainSkillEffect(skill=Diplomat(level=Level(value=1))),
                GainRivalEffect(),
            ],
        ),
        5: MishapEntry(
            text='You have no idea what happened to you — they found your ship drifting on the fringes of friendly space.',
            effects=[],
        ),
        6: MishapEntry(
            text='Injured. Roll on the Injury table.',
            effects=[InjuryEffect(severity='from_table')],
        ),
    },
    events={
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text=(
                'Your ship is ambushed by enemy vessels. Either run and roll Pilot 8+ to escape, or treat with them '
                'and roll Persuade 10+ to bargain with them. If you fail the check, then your ship is destroyed and '
                'you may not re-enlist in the Scouts at the end of this term. If you succeed, you survive and gain '
                'Electronics (sensors) 1. Either way, gain an Enemy.'
            ),
            effects=[CareerDispatchEffect(type='scout_event_3'), GainEnemyEffect()],
        ),
        4: CareerEventEntry(
            text='You survey an alien world.',
            effects=[SkillChoiceEffect(options=['Animals', 'Survival', 'Recon', 'Space Science'], level=1)],
        ),
        5: CareerEventEntry(
            text='You perform an exemplary service for the scouts.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        6: CareerEventEntry(
            text='You spend several years jumping from world to world in your scout ship.',
            effects=[
                SkillChoiceEffect(options=['Astrogation', 'Electronics', 'Navigation', 'Pilot', 'Mechanic'], level=1)
            ],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='When dealing with an alien species, you have an opportunity to gather extra intelligence.',
            effects=[CareerDispatchEffect(type='scout_event_8')],
        ),
        9: CareerEventEntry(
            text='Your scout ship is one of the first on the scene to rescue the survivors of a disaster.',
            effects=[CareerDispatchEffect(type='scout_event_9')],
        ),
        10: CareerEventEntry(
            text='You spend a great deal of time on the fringes of Charted Space.',
            effects=[CareerDispatchEffect(type='scout_event_10')],
        ),
        11: CareerEventEntry(
            text='You serve as the courier for an important message from the Imperium.',
            effects=[CareerDispatchEffect(type='scout_event_11')],
        ),
        12: CareerEventEntry(
            text='You discover a world, item or information of worth to the Imperium. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    },
    draft_assignments=['Courier', 'Surveyor', 'Explorer'],
)


# ── event 3: ambush ──────────────────────────────────────────────────────────

_AMBUSH_TARGETS = {'Pilot': 8, 'Persuade': 10}


def _handle_scout_event_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Scout',
            roll=3,
            context='scout_event_3',
            instruction='Roll Pilot 8+ to escape or Persuade 10+ to bargain',
            options=list(_AMBUSH_TARGETS),
        )
    )
    return pending_idx + 1


def _resolve_scout_event_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    """Advancement pending is created by the replay engine after this returns."""
    skill_name = event.skill if isinstance(event.skill, str) else type(event.skill).name()
    target = _AMBUSH_TARGETS[skill_name]
    if event.modified_roll >= target:
        projection.grant_skill(
            Electronics(
                comms=Level(value=1),
                computers=Level(value=1),
                remote_ops=Level(value=1),
                sensors=Level(value=1),
            )
        )
    else:
        projection.summary.problems.append('Ship destroyed; may not re-enlist in Scouts at the end of this term.')


# ── event 8: alien intelligence ──────────────────────────────────────────────


def _handle_scout_event_8(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Scout',
            roll=8,
            context='scout_event_8',
            instruction='Roll Electronics 8+ or Deception 8+',
            options=['Electronics', 'Deception'],
        )
    )
    return pending_idx + 1


def _resolve_scout_event_8(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.connections.append(Ally(source='Alien intelligence contact'))
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
    else:
        projection.pending_inputs.append(
            PendingMishap(
                id=f'{event.id}.0',
                instruction='Roll 1D Mishap (you are not ejected from this career)',
            )
        )


# ── event 9: disaster rescue ─────────────────────────────────────────────────


def _handle_scout_event_9(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Scout',
            roll=9,
            context='scout_event_9',
            instruction='Roll Medic 8+ or Engineer 8+',
            options=['Medic', 'Engineer'],
        )
    )
    return pending_idx + 1


def _resolve_scout_event_9(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.connections.append(Contact(source='Disaster survivor'))
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
    else:
        projection.summary.connections.append(Enemy(source='Disaster relief gone wrong'))


# ── event 10: fringes of Charted Space ───────────────────────────────────────


def _handle_scout_event_10(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Scout',
            roll=10,
            context='scout_event_10',
            instruction='Roll Survival 8+ or Pilot 8+',
            options=['Survival', 'Pilot'],
        )
    )
    return pending_idx + 1


def _resolve_scout_event_10(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.summary.connections.append(Contact(source='Alien contact from the fringes of Charted Space'))
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction='Choose any skill +1 (alien contact)',
                options=[],
            )
        )
    else:
        projection.pending_inputs.append(
            PendingMishap(
                id=f'{event.id}.0',
                instruction='Roll 1D Mishap (you are not ejected from this career)',
            )
        )


# ── event 11: imperial courier ───────────────────────────────────────────────


def _handle_scout_event_11(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillChoice(
            id=f'{event_id}.{pending_idx}',
            career='Scout',
            roll=11,
            advancement_precreated=False,
            instruction='Gain Diplomat 1, or DM+4 to your next advancement roll',
            options=['Diplomat', 'advancement_dm_4'],
        )
    )
    return pending_idx + 1


# ── handler registries ───────────────────────────────────────────────────────

EFFECT_HANDLERS: dict[str, object] = {
    'scout_event_3': _handle_scout_event_3,
    'scout_event_8': _handle_scout_event_8,
    'scout_event_9': _handle_scout_event_9,
    'scout_event_10': _handle_scout_event_10,
    'scout_event_11': _handle_scout_event_11,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'scout_event_3': _resolve_scout_event_3,
    'scout_event_8': _resolve_scout_event_8,
    'scout_event_9': _resolve_scout_event_9,
    'scout_event_10': _resolve_scout_event_10,
}
