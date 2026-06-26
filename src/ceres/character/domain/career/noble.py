from typing import ClassVar, Literal

from ceres.character.domain.benefits import (
    BLADE,
    SHIP_SHARE,
    TAS_MEMBERSHIP,
    YACHT,
    CharacteristicIncrease,
    CombinedBenefit,
)
from ceres.character.domain.career.career_data import (
    AdvancementDmOption,
    AssignmentData,
    AutoAdvanceEntry,
    BenefitDmEntry,
    CareerData,
    CareerHandlerBase,
    CareerSkillTables,
    CareerTableEntry,
    CareerTerm,
    CharacteristicLossEntry,
    CharCheck,
    GainConnectionAndAdvancementDmEntry,
    GainConnectionAndSkillChoiceEntry,
    GainConnectionsAndSkillChoiceEntry,
    InjuryEntry,
    LifeEventEntry,
    MusterOutData,
    MusterOutRow,
    RankBonus,
    RankEntry,
    RollMishapEntry,
    SkillChoiceEntry,
    SkillTable,
)
from ceres.character.domain.career.career_events import (
    PendingChoices,
    _apply_mishap_ejection,
    career_progress_pending,
)
from ceres.character.domain.career.common import CommonMishap1Handler
from ceres.character.domain.career.common_pending import CareerSkillRollPendingBase
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.skills import (
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
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.pending_input import ChoiceBase

# ── mishap 3: disaster or war ─────────────────────────────────────────────────


class PendingNobleMishap3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['noble_mishap_3_skill_roll'] = 'noble_mishap_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:

        projection.get_current_career()
        if event.modified_roll >= 8:
            _apply_mishap_ejection(projection, event.id, 0, lose_current_term=False)
        else:
            projection.summary.problems.append(
                'Noble mishap 3: failed to escape — roll on the Injury table and apply the result.'
            )
            _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class NobleMishap3Handler(CareerHandlerBase):
    kind: Literal['noble_mishap_3'] = 'noble_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingNobleMishap3SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Stealth or Deception 8+: success = escape unhurt '
                '(keep Benefit); fail = injury + lose Benefit',
                options=[Stealth(), Deception()],
            )
        )
        return pending_idx + 1


# ── mishap 5: assassin attempt ────────────────────────────────────────────────


class PendingNobleMishap5SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['noble_mishap_5_skill_roll'] = 'noble_mishap_5_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:

        projection.get_current_career()
        if event.modified_roll < 8:
            projection.summary.problems.append(
                'Noble mishap 5: assassin — roll on the Injury table and apply the result.'
            )
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class NobleMishap5Handler(CareerHandlerBase):
    kind: Literal['noble_mishap_5'] = 'noble_mishap_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingNobleMishap5SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll END 8+: success = escape unhurt (ejected); fail = roll on Injury table (ejected)',
                options=[Chars.END],
            )
        )
        return pending_idx + 1


# ── event 8: conspiracy recruitment ──────────────────────────────────────────


class NobleEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['noble_event_8_skill_roll'] = 'noble_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:

        if event.modified_roll >= 8:
            projection.summary.career_terms[-1].require_muster_out().extra_rolls += 1
            # no pending added — _apply_skill_roll auto-queues advancement
        else:
            projection.get_current_career()
            projection.add_connection(ConnectionKind.ENEMY, origin='A noble who caught you in a conspiracy')
            _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class NobleEvent8Accept(ChoiceBase):
    kind: Literal['noble_event_8_accept'] = 'noble_event_8_accept'
    label: str = 'Join (roll Deception or Persuade 8+)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            NobleEvent8SkillRoll(
                pending_id=(event.id, 0),
                instruction='Roll Deception or Persuade 8+: success = extra Benefit roll; fail = ejected, gain Enemy',
                options=[Deception(), Persuade()],
            )
        )


class NobleEvent8Refuse(ChoiceBase):
    kind: Literal['noble_event_8_refuse'] = 'noble_event_8_refuse'
    label: str = 'Refuse (gain Rival)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.add_connection(ConnectionKind.RIVAL, origin='A noble conspirator you declined to join')
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class NobleEvent8Handler(CareerHandlerBase):
    kind: Literal['noble_event_8'] = 'noble_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction=(
                    'Join the noble conspiracy (roll Deception or Persuade 8+: '
                    'success = extra Benefit roll, fail = ejected with Enemy) '
                    'or refuse (gain a Rival)?'
                ),
                choices=[NobleEvent8Accept(), NobleEvent8Refuse()],
            )
        )
        return pending_idx + 1


class Noble(CareerData):
    kind: Literal['NOBLE_CAREER'] = 'NOBLE_CAREER'

    name: ClassVar[str] = 'Noble'
    description: ClassVar[str] = (
        'Individuals of the upper class who perform little consistent '
        'function but often have large amounts of ready money.'
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.SOC, target=10)
    allows_assignment_change: ClassVar[bool] = True

    assignments: ClassVar[list[AssignmentData]] = [
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
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
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
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, bonus=RankBonus(skill=Admin(), level=1)),
        2: RankEntry(rank=2),
        3: RankEntry(rank=3, bonus=RankBonus(skill=Advocate(), level=1)),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5, bonus=RankBonus(skill=Leadership(), level=1)),
        6: RankEntry(rank=6),
    }

    ranks_by_assignment: ClassVar[dict[int, dict[int, RankEntry]]] = {
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
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
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
    )

    mishaps: ClassVar[dict[int, CareerTableEntry]] = {
        1: CommonMishap1Handler(
            text='Severely injured.',
            defer_ejection=True,
        ),
        2: CharacteristicLossEntry(
            text='A family scandal forces you out of your position. Lose one SOC.',
            characteristic=Chars.SOC,
            amount=1,
        ),
        3: NobleMishap3Handler(
            text='A disaster or war strikes. Roll Stealth 8+ or Deception 8+ to escape unhurt.',
            defer_ejection=True,
        ),
        4: GainConnectionAndSkillChoiceEntry(
            text='Political manoeuvrings usurp your position. Increase Diplomat or Advocate and gain a Rival.',
            connection=ConnectionKind.RIVAL,
            options=[Diplomat(), Advocate()],
            level=1,
        ),
        5: NobleMishap5Handler(
            text='An assassin attempts to end your life. Roll END 8+ or roll on the Injury table.',
            defer_ejection=True,
        ),
        6: InjuryEntry(
            text='Injured. Roll on the Injury table.',
            severity='from_table',
        ),
    }

    events: ClassVar[dict[int, CareerTableEntry]] = {
        2: RollMishapEntry(
            text='Disaster! Roll on the Mishap table, but you are not ejected from this career.',
            leave=False,
        ),
        3: SkillChoiceEntry(
            text='You are challenged to a duel for your honour and standing.',
            options=[Melee(), Leadership(), Tactics(), Deception()],
            level=1,
        ),
        4: SkillChoiceEntry(
            text='Your time as a ruler or playboy gives you a wide range of experiences.',
            options=[Animals(), *skill_instances(ArtSkill), Carouse(), Streetwise()],
            level=1,
        ),
        5: BenefitDmEntry(
            text='You inherit a gift from a rich relative.',
            amount=1,
        ),
        6: GainConnectionAndSkillChoiceEntry(
            text='You become deeply involved in politics.',
            connection=ConnectionKind.RIVAL,
            options=[Advocate(), Admin(), Diplomat(), Persuade()],
            level=1,
        ),
        7: LifeEventEntry(
            text='Life Event.',
        ),
        8: NobleEvent8Handler(
            text='A conspiracy of nobles attempts to recruit you.',
        ),
        9: GainConnectionAndAdvancementDmEntry(
            text='Your reign is acclaimed as fair and wise.',
            connection=ConnectionKind.ENEMY,
            amount=2,
        ),
        10: GainConnectionsAndSkillChoiceEntry(
            text='You manipulate and charm your way through high society.',
            connections=[ConnectionKind.RIVAL, ConnectionKind.ALLY],
            options=[Carouse(), Diplomat(), Persuade(), Steward()],
            level=1,
        ),
        11: GainConnectionAndSkillChoiceEntry(
            text='You make an alliance with a powerful noble.',
            connection=ConnectionKind.ALLY,
            options=[Leadership(), AdvancementDmOption()],
            level=1,
        ),
        12: AutoAdvanceEntry(
            text='Your efforts do not go unnoticed by the Imperium. You are automatically promoted.',
        ),
    }


NOBLE = Noble()


class NobleTerm(CareerTerm):
    kind: Literal['noble_term'] = 'noble_term'
    career: Noble


Noble.term_class = NobleTerm
