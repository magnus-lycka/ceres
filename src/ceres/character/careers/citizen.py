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
    DecreaseCharacteristicEffect,
    GainAllyEffect,
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
from ceres.character.careers.common import handle_advanced_training, resolve_advanced_training
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    PendingSkillChoice,
    SkillRollEvent,
    career_progress_pending,
)
from ceres.character.skills import (
    Admin,
    Advocate,
    Animals,
    Athletics,
    Broker,
    Carouse,
    Diplomat,
    Drive,
    Electronics,
    Engineer,
    Flyer,
    Gambler,
    GunCombat,
    JackOfAllTrades,
    Leadership,
    Level,
    Mechanic,
    Medic,
    Melee,
    Navigation,
    Recon,
    Steward,
    Streetwise,
    Survival,
    skill_category_instances,
    skill_names_for_category,
)
from ceres.character.state import (
    CharacterProjection,
    Contact,
    Rival,
    ScheduledEffect,
)


class CitizenCareerData(CareerData):
    def _basic_training_table_name(self, assignment) -> str:
        return assignment.name.lower()


CAREER_DATA = CitizenCareerData(
    name='Citizen',
    description=(
        'Individuals serving in a corporation, bureaucracy or industry, or who are making a new life on an untamed '
        'planet.'
    ),
    source='Core',
    allows_assignment_change=False,
    qualification=CharCheck(characteristic=Chars.EDU, target=5),
    assignments=[
        AssignmentData(
            name='Corporate',
            description='You are an executive or manager in a large corporation.',
            survival=CharCheck(characteristic=Chars.SOC, target=6),
            advancement=CharCheck(characteristic=Chars.INT, target=6),
        ),
        AssignmentData(
            name='Worker',
            description='You are a blue collar worker on an industrial world.',
            survival=CharCheck(characteristic=Chars.END, target=4),
            advancement=CharCheck(characteristic=Chars.EDU, target=8),
        ),
        AssignmentData(
            name='Colonist',
            description='You are building a new life on a recently settled world that still needs taming.',
            survival=CharCheck(characteristic=Chars.INT, target=7),
            advancement=CharCheck(characteristic=Chars.END, target=5),
        ),
    ],
    skill_tables=CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.EDU,
                Chars.INT,
                Carouse(),
                Gambler(),
                Drive(),
                JackOfAllTrades(),
            ]
        ),
        service_skills=SkillTable(
            [
                Drive(),
                Flyer(),
                Streetwise(),
                Melee(),
                Steward(),
                skill_category_instances('Profession'),
            ]
        ),
        advanced_education=SkillTable(
            [
                skill_category_instances('Art'),
                Advocate(),
                Diplomat(),
                skill_category_instances('Language'),
                Electronics(computers=Level(value=1)),
                Medic(),
            ],
            min_edu=10,
        ),
        assignment1=SkillTable(
            [  # Corporate
                Advocate(),
                Admin(),
                Broker(),
                Electronics(computers=Level(value=1)),
                Diplomat(),
                Leadership(),
            ]
        ),
        assignment2=SkillTable(
            [  # Worker
                Drive(),
                Mechanic(),
                Electronics(),
                Engineer(),
                skill_category_instances('Profession'),
                skill_category_instances('Science'),
            ]
        ),
        assignment3=SkillTable(
            [  # Colonist
                Animals(),
                Athletics(),
                JackOfAllTrades(),
                Drive(),
                Survival(),
                Recon(),
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
        'Corporate': {
            0: RankEntry(rank=0),
            1: RankEntry(rank=1),
            2: RankEntry(rank=2, title='Manager', bonus=RankBonus(skill=Admin(), level=1)),
            3: RankEntry(rank=3),
            4: RankEntry(rank=4, title='Senior Manager', bonus=RankBonus(skill=Advocate(), level=1)),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6, title='Director', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        },
        'Worker': {
            0: RankEntry(rank=0),
            1: RankEntry(rank=1),
            2: RankEntry(
                rank=2, title='Technician', bonus=RankBonus(choices=skill_names_for_category('Profession'), level=1)
            ),
            3: RankEntry(rank=3),
            4: RankEntry(rank=4, title='Craftsman', bonus=RankBonus(skill=Mechanic(), level=1)),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6, title='Master Technician', bonus=RankBonus(skill=Engineer(), level=1)),
        },
        'Colonist': {
            0: RankEntry(rank=0),
            1: RankEntry(rank=1),
            2: RankEntry(rank=2, title='Settler', bonus=RankBonus(skill=Survival(), level=1)),
            3: RankEntry(rank=3),
            4: RankEntry(rank=4, title='Explorer', bonus=RankBonus(skill=Navigation(), level=1)),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6, bonus=RankBonus(skill=GunCombat(), level=1)),
        },
    },
    muster_out=MusterOutData(
        rows={
            1: MusterOutRow(cash=2000, benefit=parse_benefit('ship_share')),
            2: MusterOutRow(cash=5000, benefit=parse_benefit('ally')),
            3: MusterOutRow(cash=10000, benefit=parse_benefit('int_plus_1')),
            4: MusterOutRow(cash=10000, benefit=parse_benefit('weapon')),
            5: MusterOutRow(cash=10000, benefit=parse_benefit('edu_plus_1')),
            6: MusterOutRow(cash=50000, benefit=parse_benefit('ship_share'), count=2),
            7: MusterOutRow(cash=100000, benefit=parse_benefit('tas_membership')),
        }
    ),
    mishaps={
        1: MishapEntry(
            text='Severely injured.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='Harassed and your life ruined by a criminal gang. Gain the gang as an Enemy.',
            effects=[GainEnemyEffect()],
        ),
        3: MishapEntry(
            text='Hard times caused by a lack of interstellar trade costs you your job. Lose one SOC.',
            effects=[DecreaseCharacteristicEffect(characteristic=Chars.SOC, amount=1)],
        ),
        4: MishapEntry(
            text='Your business or colony is investigated or interfered with.',
            defer_ejection=True,
            effects=[CareerDispatchEffect(type='citizen_mishap_4')],
        ),
        5: MishapEntry(
            text='A revolution, attack or unusual event throws life into chaos, forcing you to leave the planet.',
            defer_ejection=True,
            effects=[CareerDispatchEffect(type='citizen_mishap_5')],
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
            text='Political upheaval strikes your homeworld or colony.',
            effects=[SkillChoiceEffect(options=['Advocate', 'Persuade', 'Explosives', 'Streetwise'], level=1)],
        ),
        4: CareerEventEntry(
            text='You spend time maintaining and using heavy vehicles.',
            effects=[SkillChoiceEffect(options=['Mechanic', 'Drive', 'Electronics', 'Flyer', 'Engineer'], level=1)],
        ),
        5: CareerEventEntry(
            text='Your business expands, your corporation grows, or your colony thrives.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        6: CareerEventEntry(
            text='You are given advanced training in a specialist field.',
            effects=[CareerDispatchEffect(type='citizen_event_6')],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='You learn something illegal but profitable.',
            effects=[CareerDispatchEffect(type='citizen_event_8')],
        ),
        9: CareerEventEntry(
            text='You are rewarded for your diligence or cunning.',
            effects=[AdvancementDmEffect(amount=2)],
        ),
        10: CareerEventEntry(
            text='You gain experience in a technical field.',
            effects=[SkillChoiceEffect(options=['Electronics', 'Engineer'], level=1)],
        ),
        11: CareerEventEntry(
            text='You befriend a superior in the corporation, bureaucracy or colony.',
            effects=[GainAllyEffect()],
        ),
        12: CareerEventEntry(
            text='You rise to a position of power. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    },
)


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
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
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
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
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
    return handle_advanced_training(
        'Citizen', 6, 'citizen_event_6', projection, effect, event_id, pending_idx, threshold=10
    )


def _resolve_citizen_event_6(projection: CharacterProjection, event: SkillRollEvent) -> None:
    resolve_advanced_training(projection, event, threshold=10)


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
    career = projection.get_current_career()
    if event.choice == 'refuse':
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger='advancement',
                source_event_id=event.id,
                effect={'type': 'dm', 'amount': 2},
            )
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))
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
    from ceres.character.events import _apply_mishap_ejection

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
        career = projection.get_current_career()
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
