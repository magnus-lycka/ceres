from typing import ClassVar, Literal

from ceres.character.benefits import (
    CONTACT,
    SHIP_SHARE,
    CharacteristicIncrease,
    CombinedBenefit,
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
    GainConnectionsRolledEffect,
    GainContactEffect,
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
from ceres.character.characteristics import Chars, ConnectionKind, characteristic_dm
from ceres.character.effect_enums import EffectType
from ceres.character.events import (
    PendingChoices,
    SkillRollEvent,
    career_progress_pending,
)
from ceres.character.skills import (
    Advocate,
    ArtSkill,
    Athletics,
    Broker,
    Carouse,
    Deception,
    Diplomat,
    Drive,
    Electronics,
    Gambler,
    Investigate,
    JackOfAllTrades,
    LanguageSkill,
    Level,
    PerformingArt,
    Persuade,
    Pilot,
    PresentationArt,
    ProfessionSkill,
    Recon,
    ScienceSkill,
    Stealth,
    Steward,
    Streetwise,
    Survival,
    skill_instances,
)
from ceres.character.state import (
    CharacterProjection,
    ChoiceBase,
    EffectTrigger,
    Enemy,
    ScheduledEffect,
)

# ── Career-specific pending input types ──────────────────────────────────────


class PendingEntertainerEvent3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['entertainer_event_3_skill_roll'] = 'entertainer_event_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.summary.characteristics[Chars.SOC] = projection.summary.characteristics.get(Chars.SOC, 0) + 1
        else:
            projection.summary.characteristics[Chars.SOC] = max(
                0, projection.summary.characteristics.get(Chars.SOC, 0) - 1
            )
        # no pending added — _apply_skill_roll auto-queues advancement


class EntertainerEvent8Accept(ChoiceBase):
    kind: Literal['entertainer_event_8_accept'] = 'entertainer_event_8_accept'
    label: str = 'Criticise (roll Art or Investigate 8+: success = DM+2 advancement; fail = powerful Enemy)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            PendingEntertainerEvent8SkillRoll(
                id=f'{event.id}.0',
                instruction='Roll Art or Investigate 8+: success = DM+2 to next advancement; fail = gain powerful Enemy',
                options=[*skill_instances(ArtSkill), Investigate()],
            )
        )


class EntertainerEvent8Refuse(ChoiceBase):
    kind: Literal['entertainer_event_8_refuse'] = 'entertainer_event_8_refuse'
    label: str = 'Refuse (no action)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PendingEntertainerEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['entertainer_event_8_skill_roll'] = 'entertainer_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.scheduled_effects.append(
                ScheduledEffect(
                    trigger=EffectTrigger.ADVANCEMENT,
                    source_event_id=event.id,
                    effect={'type': EffectType.DM, 'amount': 2},
                )
            )
        else:
            projection.summary.connections.append(
                Enemy(source='A powerful politician who became your enemy after your public criticism')
            )
        # no pending added — _apply_skill_roll auto-queues advancement


# ── event 3: controversial exhibition ────────────────────────────────────────


class EntertainerEvent3Handler(CareerHandlerBase):
    type: Literal['entertainer_event_3'] = 'entertainer_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingEntertainerEvent3SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll Art or Investigate 8+: success = SOC +1; fail = SOC -1',
                options=[*skill_instances(ArtSkill), Investigate()],
            )
        )
        return pending_idx + 1


# ── event 8: criticise political leader ──────────────────────────────────────


class EntertainerEvent8Handler(CareerHandlerBase):
    type: Literal['entertainer_event_8'] = 'entertainer_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction=(
                    'Criticise the political leader (roll Art or Investigate 8+: '
                    'success = DM+2 to next advancement, fail = gain powerful Enemy) or refuse?'
                ),
                choices=[EntertainerEvent8Accept(), EntertainerEvent8Refuse()],
            )
        )
        return pending_idx + 1


class Entertainer(CareerData):
    type: Literal['ENTERTAINER_CAREER'] = 'ENTERTAINER_CAREER'

    career: ClassVar[Career] = Career(
        name='Entertainer',
        description='Individuals who are involved with the media, whether as reporters, artists or celebrities.',
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=5)
    allows_assignment_change: ClassVar[bool] = False

    assignments: ClassVar[list[AssignmentData]] = [
        AssignmentData(
            name='Artist',
            description='You are a writer, holographer or other creative.',
            survival=CharCheck(characteristic=Chars.SOC, target=6),
            advancement=CharCheck(characteristic=Chars.INT, target=6),
        ),
        AssignmentData(
            name='Journalist',
            description='You report on local or galactic events for a news feed, the TAS or other organisation.',
            survival=CharCheck(characteristic=Chars.EDU, target=7),
            advancement=CharCheck(characteristic=Chars.INT, target=5),
        ),
        AssignmentData(
            name='Performer',
            description='You are an actor, dancer, acrobat, professional athlete or other public performer.',
            survival=CharCheck(characteristic=Chars.INT, target=5),
            advancement=CharCheck(characteristic=Chars.DEX, target=7),
        ),
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.DEX,
                Chars.INT,
                Chars.SOC,
                skill_instances(LanguageSkill),
                Carouse(),
                JackOfAllTrades(),
            ]
        ),
        service_skills=SkillTable(
            [
                skill_instances(ArtSkill),
                Carouse(),
                Deception(),
                Drive(),
                Persuade(),
                Steward(),
            ]
        ),
        advanced_education=SkillTable(
            [
                Advocate(),
                Broker(),
                Deception(),
                skill_instances(ScienceSkill),
                Streetwise(),
                Diplomat(),
            ],
            min_edu=10,
        ),
        assignment1=SkillTable(
            [  # Artist
                skill_instances(ArtSkill),
                Carouse(),
                Electronics(computers=Level(value=1)),
                Gambler(),
                Persuade(),
                skill_instances(ProfessionSkill),
            ]
        ),
        assignment2=SkillTable(
            [  # Journalist
                PresentationArt(),
                Electronics(),
                Drive(),
                Investigate(),
                Recon(),
                Streetwise(),
            ]
        ),
        assignment3=SkillTable(
            [  # Performer
                PerformingArt(),
                Athletics(),
                Carouse(),
                Deception(),
                Stealth(),
                Streetwise(),
            ]
        ),
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, bonus=RankBonus(choices=skill_instances(ArtSkill), level=1)),
        2: RankEntry(rank=2),
        3: RankEntry(rank=3, bonus=RankBonus(skill=Investigate(), level=1)),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5, title='Famous Artist', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        6: RankEntry(rank=6),
    }

    ranks_by_assignment: ClassVar[dict[int, dict[int, RankEntry]]] = {
        1: {  # Artist
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(choices=skill_instances(ArtSkill), level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, bonus=RankBonus(skill=Investigate(), level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5, title='Famous Artist', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
            6: RankEntry(rank=6),
        },
        2: {  # Journalist
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, title='Freelancer', bonus=RankBonus(skill=Electronics(), level=1)),
            2: RankEntry(rank=2, title='Staff Writer', bonus=RankBonus(skill=Investigate(), level=1)),
            3: RankEntry(rank=3),
            4: RankEntry(rank=4, title='Correspondent', bonus=RankBonus(skill=Persuade(), level=1)),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6, title='Senior Correspondent', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        },
        3: {  # Performer
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(characteristic=Chars.DEX, level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, bonus=RankBonus(characteristic=Chars.STR, level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5, title='Famous Performer', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
            6: RankEntry(rank=6),
        },
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=0, benefit=CONTACT),
            2: MusterOutRow(cash=0, benefit=CharacteristicIncrease(char=Chars.SOC, amount=1)),
            3: MusterOutRow(cash=10000, benefit=CONTACT),
            4: MusterOutRow(cash=10000, benefit=CharacteristicIncrease(char=Chars.SOC, amount=1)),
            5: MusterOutRow(cash=40000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            6: MusterOutRow(cash=40000, benefit=SHIP_SHARE, count=2),
            7: MusterOutRow(
                cash=80000,
                benefit=CombinedBenefit(
                    benefits=[
                        CharacteristicIncrease(char=Chars.SOC, amount=1),
                        CharacteristicIncrease(char=Chars.EDU, amount=1),
                    ]
                ),
            ),
        }
    )

    mishaps: ClassVar[dict[int, MishapEntry]] = {
        1: MishapEntry(
            text='Severely injured.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='You expose or are involved in a scandal of some sort.',
            effects=[],
        ),
        3: MishapEntry(
            text='Public opinion turns on you. Reduce SOC by 1.',
            effects=[DecreaseCharacteristicEffect(characteristic=Chars.SOC, amount=1)],
        ),
        4: MishapEntry(
            text='You are betrayed by a peer. Gain a Rival or Enemy.',
            effects=[GainRivalEffect()],
        ),
        5: MishapEntry(
            text='A project goes wrong, stranding you far from home.',
            effects=[SkillChoiceEffect(options=[Survival(), Pilot(), Persuade(), Streetwise()], level=1)],
        ),
        6: MishapEntry(
            text='You are forced out because of censorship or controversy.',
            effects=[AdvancementDmEffect(amount=2)],
        ),
    }

    events: ClassVar[dict[int, CareerEventEntry]] = {
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='You are invited to take part in a controversial event or exhibition.',
            effects=[EntertainerEvent3Handler()],
        ),
        4: CareerEventEntry(
            text="You are part of your homeworld's celebrity circles.",
            effects=[SkillChoiceEffect(options=[Carouse(), Persuade(), Steward()], level=1), GainContactEffect()],
        ),
        5: CareerEventEntry(
            text='One of your works is especially well received and popular.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        6: CareerEventEntry(
            text='You gain a patron in the arts.',
            effects=[AdvancementDmEffect(amount=2), GainAllyEffect()],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='You have the opportunity to criticise or bring down a questionable political leader.',
            effects=[EntertainerEvent8Handler()],
        ),
        9: CareerEventEntry(
            text='You go on a tour of the sector, visiting several worlds.',
            effects=[GainConnectionsRolledEffect(connection_type=ConnectionKind.CONTACT, dice='d3')],
        ),
        10: CareerEventEntry(
            text='One of your pieces of art is stolen and the investigation brings you into the criminal underworld.',
            effects=[SkillChoiceEffect(options=[Streetwise(), Investigate(), Recon(), Stealth()], level=1)],
        ),
        11: CareerEventEntry(
            text='As an artist, you lead a strange and charmed life.',
            effects=[LifeEventEffect()],
        ),
        12: CareerEventEntry(
            text='You win a prestigious prize. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    }

    def qualification_dm(self, projection) -> int:
        dex_dm = characteristic_dm(projection.summary.characteristics.get(Chars.DEX, 0))
        int_dm = characteristic_dm(projection.summary.characteristics.get(Chars.INT, 0))
        return max(dex_dm, int_dm)


ENTERTAINER = Entertainer()
