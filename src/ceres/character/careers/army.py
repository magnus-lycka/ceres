from typing import ClassVar, Literal

from ceres.character.benefits import (
    ARMOR,
    CYBERNETIC_IMPLANT,
    WEAPON,
    CharacteristicIncrease,
    ChoiceBenefit,
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
from ceres.character.careers.common import handle_advanced_training
from ceres.character.careers.common_pending import CareerSkillRollPendingBase
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingChoices,
    PendingSkillChoice,
    SkillRollEvent,
)
from ceres.character.skills import (
    Admin,
    Advocate,
    Animals,
    Athletics,
    Deception,
    Diplomat,
    Drive,
    Electronics,
    Engineer,
    Explosives,
    Flyer,
    Gambler,
    GunCombat,
    HeavyWeapons,
    Investigate,
    Leadership,
    Level,
    Mechanic,
    Medic,
    Melee,
    Navigation,
    Persuade,
    ProfessionSkill,
    Recon,
    Stealth,
    Streetwise,
    Survival,
    Tactics,
    VaccSuit,
    skill_instances,
)
from ceres.character.state import (
    Ally,
    CharacterProjection,
    ChoiceBase,
)

# ── Career-specific pending input types ──────────────────────────────────────


class ArmyMishap4JoinRing(ChoiceBase):
    kind: Literal['army_mishap_4_join_ring'] = 'army_mishap_4_join_ring'
    label: str = 'Join their ring (Ally, lose Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.events import _apply_mishap_ejection

        career = projection.get_current_career()
        projection.summary.connections.append(Ally(source='Your commanding officer who brought you into the ring'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class ArmyMishap4Cooperate(ChoiceBase):
    kind: Literal['army_mishap_4_cooperate'] = 'army_mishap_4_cooperate'
    label: str = 'Co-operate with MPs (keep Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.events import _apply_mishap_ejection

        career = projection.get_current_career()
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=False)


class PendingArmyEvent6SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['army_event_6_skill_roll'] = 'army_event_6_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.0',
                    instruction='Ground war success: gain one level in Gun Combat or Leadership',
                    options=[GunCombat(), Leadership()],
                )
            )
        else:
            projection.summary.problems.append(
                'Brutal ground war: you are injured — roll on the Injury table and apply the result.'
            )


# ── mishap 4: illegal activity ────────────────────────────────────────────────


class ArmyMishap4Handler(CareerHandlerBase):
    type: Literal['army_mishap_4'] = 'army_mishap_4'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction=(
                    'Join their ring (gain commanding officer as Ally, lose Benefit roll) '
                    'or co-operate with MPs (keep Benefit roll from this term)?'
                ),
                choices=[ArmyMishap4JoinRing(), ArmyMishap4Cooperate()],
            )
        )
        return pending_idx + 1


# ── event 6: brutal ground war ───────────────────────────────────────────────


class ArmyEvent6Handler(CareerHandlerBase):
    type: Literal['army_event_6'] = 'army_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingArmyEvent6SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll EDU 8+ to avoid injury in the brutal ground war',
                options=[Chars.EDU],
            )
        )
        return pending_idx + 1


# ── event 8: advanced training ───────────────────────────────────────────────


class ArmyEvent8Handler(CareerHandlerBase):
    type: Literal['army_event_8'] = 'army_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        return handle_advanced_training(projection, event_id, pending_idx)


class Army(CareerData):
    type: Literal['ARMY_CAREER'] = 'ARMY_CAREER'

    career: ClassVar[Career] = Career(
        name='Army',
        description=(
            'Members of the planetary armed fighting forces. Soldiers deal with planetary '
            'surface actions, battles and campaigns. Such individuals may also be mercenaries for hire.'
        ),
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.END, target=5)
    allows_assignment_change: ClassVar[bool] = True
    commission: ClassVar[CharCheck | None] = CharCheck(characteristic=Chars.SOC, target=8)
    draft_assignments: ClassVar[list[str]] = ['Support', 'Infantry', 'Cavalry']

    assignments: ClassVar[list[AssignmentData]] = [
        AssignmentData(
            name='Support',
            description='You are an engineer, cook or in some other role behind the front lines.',
            survival=CharCheck(characteristic=Chars.END, target=5),
            advancement=CharCheck(characteristic=Chars.EDU, target=7),
        ),
        AssignmentData(
            name='Infantry',
            description='You are one of the Poor Bloody Infantry on the ground.',
            survival=CharCheck(characteristic=Chars.STR, target=6),
            advancement=CharCheck(characteristic=Chars.EDU, target=6),
        ),
        AssignmentData(
            name='Cavalry',
            description='You are one of the crew of a gunship or tank.',
            survival=CharCheck(characteristic=Chars.DEX, target=7),
            advancement=CharCheck(characteristic=Chars.INT, target=5),
        ),
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.STR,
                Chars.DEX,
                Chars.END,
                Gambler(),
                Medic(),
                Melee(),
            ]
        ),
        service_skills=SkillTable(
            [
                [Drive(), VaccSuit()],
                Athletics(),
                GunCombat(),
                Recon(),
                Melee(),
                HeavyWeapons(),
            ]
        ),
        advanced_education=SkillTable(
            [
                Tactics(military=Level(value=1)),
                Electronics(),
                Navigation(),
                Explosives(),
                Engineer(),
                Survival(),
            ],
            min_edu=8,
        ),
        officer=SkillTable(
            [
                Tactics(military=Level(value=1)),
                Leadership(),
                Advocate(),
                Diplomat(),
                Electronics(),
                Admin(),
            ]
        ),
        assignment1=SkillTable(
            [  # Support
                Mechanic(),
                [Drive(), Flyer()],
                skill_instances(ProfessionSkill),
                Explosives(),
                Electronics(comms=Level(value=1)),
                Medic(),
            ]
        ),
        assignment2=SkillTable(
            [  # Infantry
                GunCombat(),
                Melee(),
                HeavyWeapons(),
                Stealth(),
                Athletics(),
                Recon(),
            ]
        ),
        assignment3=SkillTable(
            [  # Cavalry
                Mechanic(),
                Drive(),
                Flyer(),
                Recon(),
                HeavyWeapons(vehicle=Level(value=1)),
                Electronics(sensors=Level(value=1)),
            ]
        ),
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0, title='Private', bonus=RankBonus(skill=GunCombat(), level=1)),
        1: RankEntry(rank=1, title='Lance Corporal', bonus=RankBonus(skill=Recon(), level=1)),
        2: RankEntry(rank=2, title='Corporal'),
        3: RankEntry(rank=3, title='Lance Sergeant', bonus=RankBonus(skill=Leadership(), level=1)),
        4: RankEntry(rank=4, title='Sergeant'),
        5: RankEntry(rank=5, title='Gunnery Sergeant'),
        6: RankEntry(rank=6, title='Sergeant Major'),
    }

    officer_ranks: ClassVar[dict[int, RankEntry]] = {
        1: RankEntry(rank=1, title='Lieutenant', bonus=RankBonus(skill=Leadership(), level=1)),
        2: RankEntry(rank=2, title='Captain'),
        3: RankEntry(rank=3, title='Major', bonus=RankBonus(skill=Tactics(), level=1)),
        4: RankEntry(rank=4, title='Lieutenant Colonel'),
        5: RankEntry(rank=5, title='Colonel'),
        6: RankEntry(rank=6, title='General', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=2000, benefit=CYBERNETIC_IMPLANT),
            2: MusterOutRow(cash=5000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            3: MusterOutRow(cash=10000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            4: MusterOutRow(cash=10000, benefit=WEAPON),
            5: MusterOutRow(cash=10000, benefit=ARMOR),
            6: MusterOutRow(
                cash=20000,
                benefit=ChoiceBenefit(options=[CharacteristicIncrease(char=Chars.END, amount=1), CYBERNETIC_IMPLANT]),
            ),
            7: MusterOutRow(cash=30000, benefit=CharacteristicIncrease(char=Chars.SOC, amount=1)),
        }
    )

    mishaps: ClassVar[dict[int, MishapEntry]] = {
        1: MishapEntry(
            text='Severely injured in action.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='Your unit is slaughtered in a disastrous battle. Gain the commander as an Enemy.',
            effects=[GainEnemyEffect()],
        ),
        3: MishapEntry(
            text='You are discharged after a brutal campaign. Increase Recon or Survival and gain an Enemy.',
            effects=[GainEnemyEffect(), SkillChoiceEffect(options=[Recon(), Survival()], level=1)],
        ),
        4: MishapEntry(
            text='You uncover illegal activity by your commanding officer.',
            defer_ejection=True,
            effects=[ArmyMishap4Handler()],
        ),
        5: MishapEntry(
            text='You quarrel with an officer or fellow soldier. Gain a Rival.',
            effects=[GainRivalEffect()],
        ),
        6: MishapEntry(
            text='Injured. Roll on the Injury table.',
            effects=[InjuryEffect(severity='from_table')],
        ),
    }

    events: ClassVar[dict[int, CareerEventEntry]] = {
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='You are assigned to a hostile or wild environment.',
            effects=[SkillChoiceEffect(options=[VaccSuit(), Engineer(), Animals(), Recon()], level=1)],
        ),
        4: CareerEventEntry(
            text='You are assigned to an urbanised planet torn by war.',
            effects=[SkillChoiceEffect(options=[Stealth(), Streetwise(), Persuade(), Recon()], level=1)],
        ),
        5: CareerEventEntry(
            text='You are given a special assignment or duty in your unit.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        6: CareerEventEntry(
            text='You are thrown into a brutal ground war.',
            effects=[ArmyEvent6Handler()],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='You are given advanced training in a specialist field.',
            effects=[ArmyEvent8Handler()],
        ),
        9: CareerEventEntry(
            text='Surrounded and outnumbered, you hold out until relief arrives.',
            effects=[AdvancementDmEffect(amount=2)],
        ),
        10: CareerEventEntry(
            text='You are assigned to a peacekeeping role.',
            effects=[SkillChoiceEffect(options=[Admin(), Investigate(), Deception(), Recon()], level=1)],
        ),
        11: CareerEventEntry(
            text='Your commanding officer takes an interest in your career.',
            effects=[SkillChoiceEffect(options=[Tactics(), AdvancementDmOption()], level=1)],
        ),
        12: CareerEventEntry(
            text='You display heroism in battle. You may gain a promotion or a commission automatically.',
            effects=[AutoAdvanceEffect()],
        ),
    }


ARMY = Army()
