from typing import Literal

from ceres.character.benefits import (
    ALLY,
    SHIP_SHARE,
    TAS_MEMBERSHIP,
    WEAPON,
    CharacteristicIncrease,
)
from ceres.character.careers.career_data import (
    AdvancementDmEffect,
    AssignmentData,
    AutoAdvanceEffect,
    BenefitDmEffect,
    Career,
    CareerData,
    CareerEventEntry,
    CareerHandlerBase,
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
from ceres.character.careers.common import handle_advanced_training
from ceres.character.careers.common_pending import CareerSkillRollPendingBase
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingChoices,
    PendingSkillChoice,
    SkillRollEvent,
    career_progress_pending,
)
from ceres.character.skills import (
    Admin,
    Advocate,
    Animals,
    ArtSkill,
    Athletics,
    Broker,
    Carouse,
    Deception,
    Diplomat,
    Drive,
    Electronics,
    Engineer,
    Explosives,
    Flyer,
    Gambler,
    GunCombat,
    JackOfAllTrades,
    LanguageSkill,
    Leadership,
    Level,
    Mechanic,
    Medic,
    Melee,
    Navigation,
    Persuade,
    ProfessionSkill,
    Recon,
    ScienceSkill,
    Steward,
    Streetwise,
    Survival,
    skill_instances,
)
from ceres.character.state import (
    CharacterProjection,
    ChoiceBase,
    Contact,
    EffectTrigger,
    EffectType,
    Rival,
    ScheduledEffect,
)

CITIZEN = Career(
    name='Citizen',
    description=(
        'Individuals serving in a corporation, bureaucracy or '
        'industry, or who are making a new life on an untamed planet.'
    ),
)


# ── Career-specific choice and pending types ──────────────────────────────────


class CitizenMishap4Cooperate(ChoiceBase):
    kind: Literal['citizen_mishap_4_cooperate'] = 'citizen_mishap_4_cooperate'
    label: str = 'Co-operate (gain Contact, keep Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.events import _apply_mishap_ejection

        career = projection.get_current_career()
        projection.summary.connections.append(Contact(source='The investigator who questioned you'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=False)


class CitizenMishap4Resist(ChoiceBase):
    kind: Literal['citizen_mishap_4_resist'] = 'citizen_mishap_4_resist'
    label: str = 'Resist (gain Rival, lose Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.events import _apply_mishap_ejection

        career = projection.get_current_career()
        projection.summary.connections.append(Rival(source='The investigator who came after you'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class PendingCitizenMishap5SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['citizen_mishap_5_skill_roll'] = 'citizen_mishap_5_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.events import PendingHomeworldChangeRequired, _apply_mishap_ejection

        career = projection.get_current_career()
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.0',
                    instruction='Forced to flee: increase any existing skill by one level',
                    options=[type(s)() for s in projection.summary.skills],
                )
            )
            next_idx = _apply_mishap_ejection(projection, career, event.id, 1, lose_current_term=True)
        else:
            next_idx = _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)
        projection.pending_inputs.append(
            PendingHomeworldChangeRequired(
                id=f'{event.id}.{next_idx}',
                instruction='Forced to leave the planet. Select your new homeworld.',
                reason='Citizen mishap 5: forcing you to leave the planet.',
                source_kind='career_mishap',
                source_career='Citizen',
            )
        )


class CitizenEvent8GainStreetwise(ChoiceBase):
    kind: Literal['citizen_event_8_gain_streetwise'] = 'citizen_event_8_gain_streetwise'
    label: str = 'Streetwise 1'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.grant_skill(Streetwise(level=Level(value=1)))


class CitizenEvent8GainDeception(ChoiceBase):
    kind: Literal['citizen_event_8_gain_deception'] = 'citizen_event_8_gain_deception'
    label: str = 'Deception 1'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.grant_skill(Deception(level=Level(value=1)))


class CitizenEvent8GainContact(ChoiceBase):
    kind: Literal['citizen_event_8_gain_contact'] = 'citizen_event_8_gain_contact'
    label: str = 'Criminal contact'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.summary.connections.append(Contact(source='A shady contact from your time working in the city'))


class CitizenEvent8DoSo(ChoiceBase):
    kind: Literal['citizen_event_8_do_so'] = 'citizen_event_8_do_so'
    label: str = 'Use it (gain DM+1 Benefit roll + choose a reward)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger=EffectTrigger.MUSTER_OUT_ADD,
                source_event_id=event.id,
                effect={'type': EffectType.ADD, 'value': 1},
            )
        )
        choices = []
        if (projection.summary.skill_level(Streetwise) or 0) < 1:
            choices.append(CitizenEvent8GainStreetwise())
        if (projection.summary.skill_level(Deception) or 0) < 1:
            choices.append(CitizenEvent8GainDeception())
        choices.append(CitizenEvent8GainContact())
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event.id}.0',
                instruction='Choose your reward',
                choices=choices,
            )
        )
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id, 1))


class CitizenEvent8Refuse(ChoiceBase):
    kind: Literal['citizen_event_8_refuse'] = 'citizen_event_8_refuse'
    label: str = 'Refuse'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger=EffectTrigger.ADVANCEMENT,
                source_event_id=event.id,
                effect={'type': EffectType.DM, 'amount': 2},
            )
        )
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


# ── mishap 4: investigation by authorities ────────────────────────────────────


class CitizenMishap4Handler(CareerHandlerBase):
    type: Literal['citizen_mishap_4'] = 'citizen_mishap_4'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction=(
                    'Co-operate with the investigation (gain investigators as a Contact, keep Benefit roll) '
                    'or resist (gain a Rival, lose Benefit roll)?'
                ),
                choices=[CitizenMishap4Cooperate(), CitizenMishap4Resist()],
            )
        )
        return pending_idx + 1


# ── mishap 5: revolution or attack ───────────────────────────────────────────


class CitizenMishap5Handler(CareerHandlerBase):
    type: Literal['citizen_mishap_5'] = 'citizen_mishap_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingCitizenMishap5SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll Streetwise 8+: success = increase any existing skill by one level (ejected either way)',
                options=[Streetwise()],
            )
        )
        return pending_idx + 1


# ── event 6: advanced training ────────────────────────────────────────────────


class CitizenEvent6Handler(CareerHandlerBase):
    type: Literal['citizen_event_6'] = 'citizen_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        return handle_advanced_training(projection, event_id, pending_idx, threshold=10)


# ── event 8: illegal information ─────────────────────────────────────────────


class CitizenEvent8Handler(CareerHandlerBase):
    type: Literal['citizen_event_8'] = 'citizen_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction=(
                    'You learn something you should not have – a corporate secret, a political scandal – '
                    'which you can profit from illegally. If you choose to do so, you gain DM+1 to a '
                    'Benefit roll from this career and gain Streetwise 1, Deception 1 or a criminal Contact. '
                    'If you refuse, you gain nothing.'
                ),
                choices=[CitizenEvent8DoSo(), CitizenEvent8Refuse()],
            )
        )
        return pending_idx + 1


class CitizenCareerData(CareerData):
    def _basic_training_table_name(self, assignment) -> str:
        return assignment.name.lower()


CAREER_DATA = CitizenCareerData(
    career=CITIZEN,
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
                skill_instances(ProfessionSkill),
            ]
        ),
        advanced_education=SkillTable(
            [
                skill_instances(ArtSkill),
                Advocate(),
                Diplomat(),
                skill_instances(LanguageSkill),
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
                skill_instances(ProfessionSkill),
                skill_instances(ScienceSkill),
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
        1: {  # Corporate
            0: RankEntry(rank=0),
            1: RankEntry(rank=1),
            2: RankEntry(rank=2, title='Manager', bonus=RankBonus(skill=Admin(), level=1)),
            3: RankEntry(rank=3),
            4: RankEntry(rank=4, title='Senior Manager', bonus=RankBonus(skill=Advocate(), level=1)),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6, title='Director', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        },
        2: {  # Worker
            0: RankEntry(rank=0),
            1: RankEntry(rank=1),
            2: RankEntry(
                rank=2, title='Technician', bonus=RankBonus(choices=skill_instances(ProfessionSkill), level=1)
            ),
            3: RankEntry(rank=3),
            4: RankEntry(rank=4, title='Craftsman', bonus=RankBonus(skill=Mechanic(), level=1)),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6, title='Master Technician', bonus=RankBonus(skill=Engineer(), level=1)),
        },
        3: {  # Colonist
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
            1: MusterOutRow(cash=2000, benefit=SHIP_SHARE),
            2: MusterOutRow(cash=5000, benefit=ALLY),
            3: MusterOutRow(cash=10000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            4: MusterOutRow(cash=10000, benefit=WEAPON),
            5: MusterOutRow(cash=10000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            6: MusterOutRow(cash=50000, benefit=SHIP_SHARE, count=2),
            7: MusterOutRow(cash=100000, benefit=TAS_MEMBERSHIP),
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
            effects=[CitizenMishap4Handler()],
        ),
        5: MishapEntry(
            text='A revolution, attack or unusual event throws life into chaos, forcing you to leave the planet.',
            defer_ejection=True,
            effects=[CitizenMishap5Handler()],
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
            effects=[SkillChoiceEffect(options=[Advocate(), Persuade(), Explosives(), Streetwise()], level=1)],
        ),
        4: CareerEventEntry(
            text='You spend time maintaining and using heavy vehicles.',
            effects=[SkillChoiceEffect(options=[Mechanic(), Drive(), Electronics(), Flyer(), Engineer()], level=1)],
        ),
        5: CareerEventEntry(
            text='Your business expands, your corporation grows, or your colony thrives.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        6: CareerEventEntry(
            text='You are given advanced training in a specialist field.',
            effects=[CitizenEvent6Handler()],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='You learn something illegal but profitable.',
            effects=[CitizenEvent8Handler()],
        ),
        9: CareerEventEntry(
            text='You are rewarded for your diligence or cunning.',
            effects=[AdvancementDmEffect(amount=2)],
        ),
        10: CareerEventEntry(
            text='You gain experience in a technical field.',
            effects=[SkillChoiceEffect(options=[Electronics(), Engineer()], level=1)],
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
