from typing import ClassVar, Literal

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
    CareerEventEntry,
    CareerHandlerBase,
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
from ceres.character.careers.common_pending import CareerSkillRollPendingBase
from ceres.character.characteristics import Chars
from ceres.character.effect_enums import EffectType
from ceres.character.events import (
    PendingChoices,
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
    ChoiceBase,
    EffectTrigger,
    Enemy,
    Rival,
    ScheduledEffect,
)

# ── Career-specific pending input types ──────────────────────────────────────


class PendingDrifterMishap5SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['drifter_mishap_5_skill_roll'] = 'drifter_mishap_5_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.careers.prisoner import PRISONER
        from ceres.character.events import _apply_mishap_ejection

        career = projection.get_current_career()
        projection.summary.connections.append(Rival(source='A friend who turned on you'))
        if event.modified_roll == 2:
            projection.forced_next_career = PRISONER
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class DrifterEvent3Accept(ChoiceBase):
    kind: Literal['drifter_event_3_accept'] = 'drifter_event_3_accept'
    label: str = 'Accept (DM+4 to next qualification roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger=EffectTrigger.QUALIFICATION,
                source_event_id=event.id,
                effect={'type': EffectType.DM, 'amount': 4},
            )
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class DrifterEvent3Decline(ChoiceBase):
    kind: Literal['drifter_event_3_decline'] = 'drifter_event_3_decline'
    label: str = 'Decline'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PendingDrifterEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['drifter_event_8_skill_roll'] = 'drifter_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.0',
                    instruction='Attack survived: increase Melee or Gun Combat by one level',
                    options=[Melee(), GunCombat()],
                )
            )
        else:
            projection.summary.problems.append(
                'Attacked by enemies: you are injured — roll on the Injury table and apply the result.'
            )


class DrifterEvent9Injury(ChoiceBase):
    kind: Literal['drifter_event_9_injury'] = 'drifter_event_9_injury'
    label: str = 'Roll on Injury table'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            PendingInjuryTable(
                id=f'{event.id}.0',
                instruction='Risky adventure outcome: roll 1D on Injury table',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )


class DrifterEvent9Prison(ChoiceBase):
    kind: Literal['drifter_event_9_prison'] = 'drifter_event_9_prison'
    label: str = 'Be sent to Prisoner career'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.careers.prisoner import PRISONER

        projection.forced_next_career = PRISONER


class PendingDrifterEvent9RollSkillRoll(CareerSkillRollPendingBase):
    kind: Literal['drifter_event_9_roll_skill_roll'] = 'drifter_event_9_roll_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        career = projection.get_current_career()
        roll = event.modified_roll
        if roll <= 2:
            projection.pending_inputs.append(
                PendingChoices(
                    id=f'{event.id}.0',
                    instruction='Risky adventure (1-2): choose — roll on Injury table, or be sent to Prisoner career?',
                    choices=[DrifterEvent9Injury(), DrifterEvent9Prison()],
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
                    trigger=EffectTrigger.MUSTER_OUT_ADD,
                    source_event_id=event.id,
                    effect={'type': EffectType.ADD, 'value': 1},
                )
            )
            # _apply_skill_roll auto-queues advancement


class DrifterEvent9Accept(ChoiceBase):
    kind: Literal['drifter_event_9_accept'] = 'drifter_event_9_accept'
    label: str = 'Accept the adventure'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            PendingDrifterEvent9RollSkillRoll(
                id=f'{event.id}.0',
                instruction='Risky adventure: roll 1D (1-2: injured or arrested, 3: injured, 4-6: bonus Benefit roll)',
                options=[],
            )
        )


class DrifterEvent9Decline(ChoiceBase):
    kind: Literal['drifter_event_9_decline'] = 'drifter_event_9_decline'
    label: str = 'Decline'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


# ── mishap 5: betrayed by a friend ───────────────────────────────────────────


class DrifterMishap5Handler(CareerHandlerBase):
    type: Literal['drifter_mishap_5'] = 'drifter_mishap_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingDrifterMishap5SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Betrayed by a friend: gain a Rival. Roll 2D — on a natural 2, must take Prisoner next term',
                options=[],
            )
        )
        return pending_idx + 1


# ── event 3: patron job offer ─────────────────────────────────────────────────


class DrifterEvent3Handler(CareerHandlerBase):
    type: Literal['drifter_event_3'] = 'drifter_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction="Accept the patron's job offer (DM+4 to next Qualification roll) or decline?",
                choices=[DrifterEvent3Accept(), DrifterEvent3Decline()],
            )
        )
        return pending_idx + 1


# ── event 8: attacked by enemies ─────────────────────────────────────────────


class DrifterEvent8Handler(CareerHandlerBase):
    type: Literal['drifter_event_8'] = 'drifter_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.summary.connections.append(Enemy(source='Someone who attacked you on your travels'))
        projection.pending_inputs.append(
            PendingDrifterEvent8SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll Melee or Gun Combat 8+: success = increase that skill; fail = injured',
                options=[Melee(), GunCombat()],
            )
        )
        return pending_idx + 1


# ── event 9: risky adventure ──────────────────────────────────────────────────


class DrifterEvent9Handler(CareerHandlerBase):
    type: Literal['drifter_event_9'] = 'drifter_event_9'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction='Accept the risky adventure (roll 1D for outcome) or decline?',
                choices=[DrifterEvent9Accept(), DrifterEvent9Decline()],
            )
        )
        return pending_idx + 1


# ── event 11: forcibly drafted ────────────────────────────────────────────────


class DrifterEvent11Handler(CareerHandlerBase):
    type: Literal['drifter_event_11'] = 'drifter_event_11'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        career = projection.get_current_career()
        projection.summary.problems.append(
            'Drifter event 11: forcibly drafted — roll 1D: 1-2 Army, 3-4 Marines, 5-6 Navy. '
            'Leave this career and enter the rolled career next term (no qualification roll needed). Apply manually.'
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event_id))
        return pending_idx


# ── Career class ──────────────────────────────────────────────────────────────


class Drifter(CareerData):
    type: Literal['DRIFTER_CAREER'] = 'DRIFTER_CAREER'

    career: ClassVar[Career] = Career(
        name='Drifter',
        description='Wanderers, hitchhikers and travellers, drifters are those who roam the stars without obvious purpose or direction.',
    )

    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.END, target=0)
    allows_assignment_change: ClassVar[bool] = True

    assignments: ClassVar[list[AssignmentData]] = [
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
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
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
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0),
        1: RankEntry(rank=1),
        2: RankEntry(rank=2),
        3: RankEntry(rank=3),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5),
        6: RankEntry(rank=6),
    }

    ranks_by_assignment: ClassVar[dict[int, dict[int, RankEntry]]] = {
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
    }

    mishaps: ClassVar[dict[int, MishapEntry]] = {
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
            effects=[DrifterMishap5Handler()],
        ),
        6: MishapEntry(
            text='You do not know what happened to you. There is a gap in your memory.',
            effects=[],
        ),
    }

    events: ClassVar[dict[int, CareerEventEntry]] = {
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='A patron offers you a chance at a job.',
            effects=[DrifterEvent3Handler()],
        ),
        4: CareerEventEntry(
            text='You pick up a few useful skills here and there.',
            effects=[SkillChoiceEffect(options=[JackOfAllTrades(), Survival(), Streetwise(), Melee()], level=1)],
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
            effects=[DrifterEvent8Handler()],
        ),
        9: CareerEventEntry(
            text='You are offered a chance to take part in a risky but rewarding adventure.',
            effects=[DrifterEvent9Handler()],
        ),
        10: CareerEventEntry(
            text='Life on the edge hones your abilities.',
            effects=[SkillChoiceEffect(options=[], level=1)],
        ),
        11: CareerEventEntry(
            text='You are forcibly drafted.',
            effects=[DrifterEvent11Handler()],
        ),
        12: CareerEventEntry(
            text='You thrive on adversity. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=0, benefit=CONTACT),
            2: MusterOutRow(cash=0, benefit=WEAPON),
            3: MusterOutRow(cash=1000, benefit=ALLY),
            4: MusterOutRow(cash=2000, benefit=WEAPON),
            5: MusterOutRow(cash=3000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            6: MusterOutRow(cash=4000, benefit=SHIP_SHARE),
            7: MusterOutRow(cash=8000, benefit=SHIP_SHARE, count=2),
        }
    )

    def _basic_training_table_name(self, assignment) -> str:
        return assignment.name.lower()


DRIFTER = Drifter()
