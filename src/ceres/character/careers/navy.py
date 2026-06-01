from ceres.character.benefits import parse_benefit
from ceres.character.careers.career_data import (
    AdvancementDmEffect,
    AssignmentData,
    AutoAdvanceEffect,
    BenefitDmEffect,
    CareerData,
    CareerDispatchEffect,
    CareerEventEntry,
    CareerSkillTables,
    CharCheck,
    DecreaseCharacteristicChoiceEffect,
    GainContactEffect,
    GainEnemyEffect,
    GainRivalEffect,
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
from ceres.character.careers.common import handle_advanced_training, resolve_advanced_training
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    SkillRollEvent,
    career_progress_pending,
)
from ceres.character.skills import (
    Admin,
    Astrogation,
    Athletics,
    Electronics,
    Engineer,
    Flyer,
    GunCombat,
    Gunner,
    Leadership,
    Level,
    Mechanic,
    Medic,
    Melee,
    Pilot,
    Tactics,
    VaccSuit,
)
from ceres.character.state import (
    CharacterProjection,
    Enemy,
    ScheduledEffect,
)

CAREER_DATA = CareerData(
    name='Navy',
    description=(
        'Members of the interstellar navy that patrols space between the stars. The navy has the responsibility for '
        'the protection of society from foreign powers and lawless elements in the interstellar trade channels.'
    ),
    source='Core',
    allows_assignment_change=True,
    qualification=CharCheck(characteristic=Chars.INT, target=6),
    commission=CharCheck(characteristic=Chars.SOC, target=8),
    assignments=[
        AssignmentData(
            name='Line/Crew',
            description='You serve as a general crewman or officer on a ship of the line.',
            survival=CharCheck(characteristic=Chars.INT, target=5),
            advancement=CharCheck(characteristic=Chars.EDU, target=7),
        ),
        AssignmentData(
            name='Engineer/Gunner',
            description='You serve as a specialist technician on a starship.',
            survival=CharCheck(characteristic=Chars.INT, target=6),
            advancement=CharCheck(characteristic=Chars.EDU, target=6),
        ),
        AssignmentData(
            name='Flight',
            description='You are a pilot of a shuttle, fighter or other light craft.',
            survival=CharCheck(characteristic=Chars.DEX, target=7),
            advancement=CharCheck(characteristic=Chars.EDU, target=5),
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
                Chars.SOC,
            ]
        ),
        service_skills=SkillTable(
            [
                Pilot(),
                VaccSuit(),
                Athletics(),
                Gunner(),
                Mechanic(),
                GunCombat(),
            ]
        ),
        advanced_education=SkillTable(
            [
                Electronics(),
                Astrogation(),
                Engineer(),
                Flyer(),
                Medic(),
                Admin(),
            ],
            min_edu=8,
        ),
        officer=SkillTable(
            [
                Leadership(),
                Electronics(),
                Pilot(),
                Melee(blade=Level(value=1)),
                Admin(),
                Tactics(naval=Level(value=1)),
            ]
        ),
        assignment1=SkillTable(
            [  # Line/Crew
                Electronics(),
                Mechanic(),
                GunCombat(),
                Flyer(),
                Melee(),
                VaccSuit(),
            ]
        ),
        assignment2=SkillTable(
            [  # Engineer/Gunner
                Engineer(),
                Mechanic(),
                Electronics(),
                Engineer(),
                Gunner(),
                Flyer(),
            ]
        ),
        assignment3=SkillTable(
            [  # Flight
                Pilot(),
                Flyer(),
                Gunner(),
                Pilot(small_craft=Level(value=1)),
                Astrogation(),
                Electronics(),
            ]
        ),
    ),
    ranks={
        0: RankEntry(rank=0, title='Crewman'),
        1: RankEntry(rank=1, title='Able Spacehand', bonus=RankBonus(skill=Mechanic(), level=1)),
        2: RankEntry(rank=2, title='Petty Officer, 3rd class', bonus=RankBonus(skill=VaccSuit(), level=1)),
        3: RankEntry(rank=3, title='Petty Officer, 2nd class'),
        4: RankEntry(rank=4, title='Petty Officer, 1st class', bonus=RankBonus(characteristic=Chars.END, level=1)),
        5: RankEntry(rank=5, title='Chief Petty Officer'),
        6: RankEntry(rank=6, title='Master Chief'),
    },
    officer_ranks={
        1: RankEntry(rank=1, title='Ensign', bonus=RankBonus(skill=Melee(), level=1)),
        2: RankEntry(rank=2, title='Sublieutenant', bonus=RankBonus(skill=Leadership(), level=1)),
        3: RankEntry(rank=3, title='Lieutenant'),
        4: RankEntry(rank=4, title='Commander', bonus=RankBonus(skill=Tactics(), level=1)),
        5: RankEntry(rank=5, title='Captain', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        6: RankEntry(rank=6, title='Admiral', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
    },
    muster_out=MusterOutData(
        rows={
            1: MusterOutRow(cash=1000, benefit=parse_benefit(['personal_vehicle', 'ship_share'])),
            2: MusterOutRow(cash=5000, benefit=parse_benefit('int_plus_1')),
            3: MusterOutRow(cash=5000, benefit=parse_benefit(['edu_plus_1', 'ship_share'])),
            4: MusterOutRow(cash=10000, benefit=parse_benefit('weapon')),
            5: MusterOutRow(cash=20000, benefit=parse_benefit('tas_membership')),
            6: MusterOutRow(cash=50000, benefit=parse_benefit(['ships_boat', 'ship_share'])),
            7: MusterOutRow(cash=50000, benefit=parse_benefit('soc_plus_2')),
        }
    ),
    mishaps={
        1: MishapEntry(
            text='Severely injured in action.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='Placed in the frozen watch and revived improperly. Reduce STR, DEX or END. You are not ejected.',
            stay_in_career=True,
            effects=[DecreaseCharacteristicChoiceEffect(options=['STR', 'DEX', 'END'], amount=1)],
        ),
        3: MishapEntry(
            text='During a battle, defeat or victory depends on your actions.',
            defer_ejection=True,
            effects=[CareerDispatchEffect(type='navy_mishap_3')],
        ),
        4: MishapEntry(
            text='Blamed for an accident that causes the death of several crew members.',
            defer_ejection=True,
            effects=[CareerDispatchEffect(type='navy_mishap_4')],
        ),
        5: MishapEntry(
            text='You quarrel with an officer or fellow crewman. Gain a Rival.',
            effects=[GainRivalEffect()],
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
            text='You join a gambling circle on board.',
            effects=[SkillChoiceEffect(options=['Gambler', 'Deception'], level=1)],
        ),
        4: CareerEventEntry(
            text='Given a special assignment or duty on board ship.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        5: CareerEventEntry(
            text='Advanced training in a specialist field.',
            effects=[CareerDispatchEffect(type='navy_event_5')],
        ),
        6: CareerEventEntry(
            text='Your vessel participates in a notable military engagement.',
            effects=[SkillChoiceEffect(options=['Electronics', 'Engineer', 'Gunner', 'Pilot'], level=1)],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='Your vessel participates in a diplomatic mission.',
            effects=[SkillChoiceEffect(options=['Recon', 'Diplomat', 'Steward'], level=1), GainContactEffect()],
        ),
        9: CareerEventEntry(
            text='You foil an attempted crime on board. Gain an Enemy and DM+2 to next advancement.',
            effects=[GainEnemyEffect(), AdvancementDmEffect(amount=2)],
        ),
        10: CareerEventEntry(
            text='Opportunity to abuse your position for profit.',
            effects=[CareerDispatchEffect(type='navy_event_10')],
        ),
        11: CareerEventEntry(
            text='Your commanding officer takes an interest in your career.',
            effects=[SkillChoiceEffect(options=['Tactics', 'advancement_dm_4'], level=1)],
        ),
        12: CareerEventEntry(
            text='You display heroism in battle, saving the whole ship.',
            effects=[AutoAdvanceEffect()],
        ),
    },
    draft_assignments=['Line/Crew', 'Engineer/Gunner', 'Flight'],
)


# ── mishap 3: battle skill check ─────────────────────────────────────────────

_MISHAP_3_SKILLS: dict[str, list[str]] = {
    'Line/Crew': ['Electronics', 'Gunner'],
    'Engineer/Gunner': ['Mechanic', 'Vacc Suit'],
    'Flight': ['Pilot', 'Tactics'],
}


def _handle_navy_mishap_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    assignment = projection.summary.current_assignment or 'Line/Crew'
    options = _MISHAP_3_SKILLS.get(assignment, ['Electronics', 'Gunner'])
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Navy',
            roll=3,
            context='navy_mishap_3',
            instruction=(
                f'Roll {" or ".join(options)} 8+ — success: honourable discharge (keep Benefit); '
                'fail: court-martialled (lose Benefit)'
            ),
            options=options,
        )
    )
    return pending_idx + 1


def _resolve_navy_mishap_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
    lose = event.modified_roll < 8
    _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=lose)


# ── mishap 4: blamed for accident ────────────────────────────────────────────


def _handle_navy_mishap_4(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Navy',
            roll=4,
            instruction=(
                'Were you responsible for the accident? '
                'Responsible: gain one free skill table roll before ejection. '
                'Not responsible: gain the officer who blamed you as an Enemy, but keep your Benefit roll.'
            ),
            options=['responsible', 'not_responsible'],
        )
    )
    return pending_idx + 1


def _choice_navy_mishap_4(projection: CharacterProjection, event) -> None:
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
    if event.choice == 'responsible':
        projection.summary.problems.append(
            'Navy mishap 4 (responsible): you gain one free roll on the Skills and Training tables '
            'before ejection — apply a skill table roll manually to this character.'
        )
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)
    else:
        projection.summary.connections.append(Enemy(source='Officer who blamed you (Navy mishap 4)'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=False)


# ── event 5: advanced training ───────────────────────────────────────────────


def _handle_navy_event_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    return handle_advanced_training('Navy', 5, 'navy_event_5', projection, effect, event_id, pending_idx)


def _resolve_navy_event_5(projection: CharacterProjection, event: SkillRollEvent) -> None:
    resolve_advanced_training(projection, event)


# ── event 10: abuse position for profit ──────────────────────────────────────


def _handle_navy_event_10(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerEvent(
            id=f'{event_id}.{pending_idx}',
            career='Navy',
            roll=10,
            instruction=(
                'Abuse your position for profit (gain extra Benefit roll) or refuse (DM+2 to next advancement)?'
            ),
            options=['profit', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_navy_event_10(projection: CharacterProjection, event) -> None:
    career = projection.get_current_career()
    if event.choice == 'profit':
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='muster_out_add',
                source_event_id=event.id,
                effect={'type': 'add', 'value': 1},
            )
        )
    else:
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
    projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = CareerData

EFFECT_HANDLERS: dict[str, object] = {
    'navy_mishap_3': _handle_navy_mishap_3,
    'navy_mishap_4': _handle_navy_mishap_4,
    'navy_event_5': _handle_navy_event_5,
    'navy_event_10': _handle_navy_event_10,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'navy_mishap_3': _resolve_navy_mishap_3,
    'navy_event_5': _resolve_navy_event_5,
}

CHOICE_HANDLERS: dict[str, object] = {
    'navy_mishap_4': _choice_navy_mishap_4,
    'navy_event_10': _choice_navy_event_10,
}
