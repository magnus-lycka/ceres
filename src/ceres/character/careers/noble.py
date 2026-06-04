from typing import Literal

from ceres.character.benefits import (
    BLADE,
    SHIP_SHARE,
    TAS_MEMBERSHIP,
    YACHT,
    CharacteristicIncrease,
    CombinedBenefit,
)
from ceres.character.careers.career_data import (
    AdvancementDmEffect,
    AdvancementDmOption,
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
from ceres.character.careers.common_pending import CareerSkillRollPendingBase
from ceres.character.characteristics import Chars
from ceres.character.effect_enums import EffectType
from ceres.character.events import (
    PendingChoices,
    SkillRollEvent,
    career_progress_pending,
)
from ceres.character.skills import (
    Admin,
    Advocate,
    Animals,
    ArtSkill,
    Broker,
    Carouse,
    Deception,
    Diplomat,
    Electronics,
    Flyer,
    Gambler,
    GunCombat,
    Investigate,
    JackOfAllTrades,
    LanguageSkill,
    Leadership,
    Melee,
    Persuade,
    ScienceSkill,
    Stealth,
    Steward,
    Streetwise,
    Tactics,
    skill_instances,
)
from ceres.character.state import (
    CharacterProjection,
    ChoiceBase,
    EffectTrigger,
    Enemy,
    Rival,
    ScheduledEffect,
)

NOBLE = Career(
    name='Noble',
    description=(
        'Individuals of the upper class who perform little '
        'consistent function but often have large amounts of ready money.'
    ),
)


# ── mishap 3: disaster or war ─────────────────────────────────────────────────


class PendingNobleMishap3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['noble_mishap_3_skill_roll'] = 'noble_mishap_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.events import _apply_mishap_ejection

        career = projection.get_current_career()
        if event.modified_roll >= 8:
            _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=False)
        else:
            projection.summary.problems.append(
                'Noble mishap 3: failed to escape — roll on the Injury table and apply the result.'
            )
            _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class NobleMishap3Handler(CareerHandlerBase):
    type: Literal['noble_mishap_3'] = 'noble_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingNobleMishap3SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll Stealth or Deception 8+: success = escape unhurt (keep Benefit); fail = injury + lose Benefit',
                options=[Stealth(), Deception()],
            )
        )
        return pending_idx + 1


# ── mishap 5: assassin attempt ────────────────────────────────────────────────


class PendingNobleMishap5SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['noble_mishap_5_skill_roll'] = 'noble_mishap_5_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.events import _apply_mishap_ejection

        career = projection.get_current_career()
        if event.modified_roll < 8:
            projection.summary.problems.append(
                'Noble mishap 5: assassin — roll on the Injury table and apply the result.'
            )
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class NobleMishap5Handler(CareerHandlerBase):
    type: Literal['noble_mishap_5'] = 'noble_mishap_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingNobleMishap5SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll END 8+: success = escape unhurt (ejected); fail = roll on Injury table (ejected)',
                options=[Chars.END],
            )
        )
        return pending_idx + 1


# ── event 8: conspiracy recruitment ──────────────────────────────────────────


class NobleEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['noble_event_8_skill_roll'] = 'noble_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.events import _apply_mishap_ejection

        if event.modified_roll >= 8:
            projection.scheduled_effects.append(
                ScheduledEffect(
                    trigger=EffectTrigger.MUSTER_OUT_ADD,
                    source_event_id=event.id,
                    effect={'type': EffectType.ADD, 'value': 1},
                )
            )
            # no pending added — _apply_skill_roll auto-queues advancement
        else:
            career = projection.get_current_career()
            projection.summary.connections.append(Enemy(source='A noble who caught you in a conspiracy'))
            _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class NobleEvent8Accept(ChoiceBase):
    kind: Literal['noble_event_8_accept'] = 'noble_event_8_accept'
    label: str = 'Join (roll Deception or Persuade 8+)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            NobleEvent8SkillRoll(
                id=f'{event.id}.0',
                instruction='Roll Deception or Persuade 8+: success = extra Benefit roll; fail = ejected, gain Enemy',
                options=[Deception(), Persuade()],
            )
        )


class NobleEvent8Refuse(ChoiceBase):
    kind: Literal['noble_event_8_refuse'] = 'noble_event_8_refuse'
    label: str = 'Refuse (gain Rival)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.connections.append(Rival(source='A noble conspirator you declined to join'))
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class NobleEvent8Handler(CareerHandlerBase):
    type: Literal['noble_event_8'] = 'noble_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction=(
                    'Join the noble conspiracy (roll Deception or Persuade 8+: '
                    'success = extra Benefit roll, fail = ejected with Enemy) '
                    'or refuse (gain a Rival)?'
                ),
                choices=[NobleEvent8Accept(), NobleEvent8Refuse()],
            )
        )
        return pending_idx + 1


class NobleCareerData(CareerData):
    pass


CAREER_DATA = NobleCareerData(
    career=NOBLE,
    allows_assignment_change=True,
    qualification=CharCheck(characteristic=Chars.SOC, target=10),
    assignments=[
        AssignmentData(
            name='Administrator',
            description='You serve in the planetary government or even ruled over a fiefdom or other domain.',
            survival=CharCheck(characteristic=Chars.INT, target=4),
            advancement=CharCheck(characteristic=Chars.EDU, target=6),
        ),
        AssignmentData(
            name='Diplomat',
            description='You are a diplomat or other state official.',
            survival=CharCheck(characteristic=Chars.INT, target=5),
            advancement=CharCheck(characteristic=Chars.SOC, target=7),
        ),
        AssignmentData(
            name='Dilettante',
            description='You are known for being known and have absolutely no useful function in society.',
            survival=CharCheck(characteristic=Chars.SOC, target=5),
            advancement=CharCheck(characteristic=Chars.INT, target=7),
        ),
    ],
    skill_tables=CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.STR,
                Chars.DEX,
                Chars.END,
                Gambler(),
                GunCombat(),
                Melee(),
            ]
        ),
        service_skills=SkillTable(
            [
                Admin(),
                Advocate(),
                Electronics(),
                Diplomat(),
                Investigate(),
                Persuade(),
            ]
        ),
        advanced_education=SkillTable(
            [
                skill_instances(ScienceSkill),
                Advocate(),
                skill_instances(LanguageSkill),
                Leadership(),
                Diplomat(),
                skill_instances(ArtSkill),
            ],
            min_edu=8,
        ),
        assignment1=SkillTable(
            [  # Administrator
                Admin(),
                Advocate(),
                Broker(),
                Diplomat(),
                Leadership(),
                Persuade(),
            ]
        ),
        assignment2=SkillTable(
            [  # Diplomat
                Advocate(),
                Carouse(),
                Electronics(),
                Steward(),
                Diplomat(),
                Deception(),
            ]
        ),
        assignment3=SkillTable(
            [  # Dilettante
                Carouse(),
                Deception(),
                Flyer(),
                Streetwise(),
                Gambler(),
                JackOfAllTrades(),
            ]
        ),
    ),
    ranks={
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, bonus=RankBonus(skill=Admin(), level=1)),
        2: RankEntry(rank=2),
        3: RankEntry(rank=3, bonus=RankBonus(skill=Advocate(), level=1)),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5, bonus=RankBonus(skill=Leadership(), level=1)),
        6: RankEntry(rank=6),
    },
    ranks_by_assignment={
        1: {  # Administrator
            0: RankEntry(rank=0, title='Assistant'),
            1: RankEntry(rank=1, title='Clerk', bonus=RankBonus(skill=Admin(), level=1)),
            2: RankEntry(rank=2, title='Supervisor'),
            3: RankEntry(rank=3, title='Manager', bonus=RankBonus(skill=Advocate(), level=1)),
            4: RankEntry(rank=4, title='Chief'),
            5: RankEntry(rank=5, title='Director', bonus=RankBonus(skill=Leadership(), level=1)),
            6: RankEntry(rank=6, title='Minister'),
        },
        2: {  # Diplomat
            0: RankEntry(rank=0, title='Intern'),
            1: RankEntry(rank=1, title='3rd Secretary', bonus=RankBonus(skill=Admin(), level=1)),
            2: RankEntry(rank=2, title='2nd Secretary'),
            3: RankEntry(rank=3, title='1st Secretary', bonus=RankBonus(skill=Advocate(), level=1)),
            4: RankEntry(rank=4, title='Counsellor'),
            5: RankEntry(rank=5, title='Minister', bonus=RankBonus(skill=Diplomat(), level=1)),
            6: RankEntry(rank=6, title='Ambassador'),
        },
        3: {  # Dilettante
            0: RankEntry(rank=0, title='Wastrel'),
            1: RankEntry(rank=1),
            2: RankEntry(rank=2, title='Ingrate', bonus=RankBonus(skill=Carouse(), level=1)),
            3: RankEntry(rank=3),
            4: RankEntry(rank=4, title='Black Sheep', bonus=RankBonus(skill=Persuade(), level=1)),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6, title='Scoundrel', bonus=RankBonus(skill=JackOfAllTrades(), level=1)),
        },
    },
    muster_out=MusterOutData(
        rows={
            1: MusterOutRow(cash=10000, benefit=SHIP_SHARE),
            2: MusterOutRow(cash=10000, benefit=SHIP_SHARE, count=2),
            3: MusterOutRow(cash=50000, benefit=BLADE),
            4: MusterOutRow(cash=50000, benefit=CharacteristicIncrease(char=Chars.SOC, amount=1)),
            5: MusterOutRow(cash=100000, benefit=TAS_MEMBERSHIP),
            6: MusterOutRow(cash=100000, benefit=YACHT),
            7: MusterOutRow(
                cash=200000, benefit=CombinedBenefit(benefits=[CharacteristicIncrease(char=Chars.SOC, amount=1), YACHT])
            ),
        }
    ),
    mishaps={
        1: MishapEntry(
            text='Severely injured.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='A family scandal forces you out of your position. Lose one SOC.',
            effects=[DecreaseCharacteristicEffect(characteristic=Chars.SOC, amount=1)],
        ),
        3: MishapEntry(
            text='A disaster or war strikes. Roll Stealth 8+ or Deception 8+ to escape unhurt.',
            defer_ejection=True,
            effects=[NobleMishap3Handler()],
        ),
        4: MishapEntry(
            text='Political manoeuvrings usurp your position. Increase Diplomat or Advocate and gain a Rival.',
            effects=[SkillChoiceEffect(options=[Diplomat(), Advocate()], level=1), GainRivalEffect()],
        ),
        5: MishapEntry(
            text='An assassin attempts to end your life. Roll END 8+ or roll on the Injury table.',
            defer_ejection=True,
            effects=[NobleMishap5Handler()],
        ),
        6: MishapEntry(
            text='Injured. Roll on the Injury table.',
            effects=[InjuryEffect(severity='from_table')],
        ),
    },
    events={
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table, but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='You are challenged to a duel for your honour and standing.',
            effects=[SkillChoiceEffect(options=[Melee(), Leadership(), Tactics(), Deception()], level=1)],
        ),
        4: CareerEventEntry(
            text='Your time as a ruler or playboy gives you a wide range of experiences.',
            effects=[
                SkillChoiceEffect(options=[Animals(), *skill_instances(ArtSkill), Carouse(), Streetwise()], level=1)
            ],
        ),
        5: CareerEventEntry(
            text='You inherit a gift from a rich relative.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        6: CareerEventEntry(
            text='You become deeply involved in politics.',
            effects=[
                SkillChoiceEffect(options=[Advocate(), Admin(), Diplomat(), Persuade()], level=1),
                GainRivalEffect(),
            ],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='A conspiracy of nobles attempts to recruit you.',
            effects=[NobleEvent8Handler()],
        ),
        9: CareerEventEntry(
            text='Your reign is acclaimed as fair and wise.',
            effects=[GainEnemyEffect(), AdvancementDmEffect(amount=2)],
        ),
        10: CareerEventEntry(
            text='You manipulate and charm your way through high society.',
            effects=[
                SkillChoiceEffect(options=[Carouse(), Diplomat(), Persuade(), Steward()], level=1),
                GainRivalEffect(),
                GainAllyEffect(),
            ],
        ),
        11: CareerEventEntry(
            text='You make an alliance with a powerful noble.',
            effects=[GainAllyEffect(), SkillChoiceEffect(options=[Leadership(), AdvancementDmOption()], level=1)],
        ),
        12: CareerEventEntry(
            text='Your efforts do not go unnoticed by the Imperium. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    },
)
