from typing import Any, ClassVar, Literal

from ceres.character.domain.benefits import (
    BLADE,
    FREE_TRADER,
    GUN,
    SHIP_SHARE,
    CharacteristicIncrease,
)
from ceres.character.domain.career.career_data import (
    AssignmentData,
    AutoAdvanceEffect,
    AutoQualifyCareerEffect,
    BenefitDmEffect,
    CareerData,
    CareerEventEntry,
    CareerHandlerBase,
    CareerSkillTables,
    CharCheck,
    GainAllyEffect,
    GainContactEffect,
    GainEnemyEffect,
    GainRivalEffect,
    InjuryEffect,
    LifeEventEffect,
    LoseAllCareerBenefitsEffect,
    MishapEntry,
    MusterOutData,
    MusterOutRow,
    RankBonus,
    RankEntry,
    RollMishapEffect,
    SkillChoiceEffect,
    SkillTable,
)
from ceres.character.domain.career.career_events import (
    PendingChoices,
    PendingSkillChoice,
    _apply_mishap_ejection,
    _set_forced_prison_career,
    career_progress_pending,
)
from ceres.character.domain.career.common import CommonMishap1Handler, handle_advanced_training
from ceres.character.domain.career.common_pending import CareerSkillRollPendingBase
from ceres.character.domain.career.rogue import Rogue
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.skills import (
    Admin,
    Advocate,
    Animals,
    Astrogation,
    Athletics,
    Broker,
    Deception,
    Diplomat,
    Drive,
    Electronics,
    Engineer,
    GunCombat,
    Gunner,
    Investigate,
    JackOfAllTrades,
    LanguageSkill,
    Level,
    Mechanic,
    Persuade,
    Pilot,
    ProfessionSkill,
    ScienceSkill,
    Steward,
    Streetwise,
    VaccSuit,
    skill_instances,
)
from ceres.character.mechanism.pending_input import ChoiceBase

# ── event 3: smuggling opportunity ───────────────────────────────────────────


class MerchantEvent3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['merchant_event_3_skill_roll'] = 'merchant_event_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:

        if event.modified_roll >= 8:
            projection.summary.career_terms[-1].require_muster_out().extra_rolls += 1
            # no pending added — _apply_skill_roll auto-queues advancement
        else:
            projection.get_current_career()
            projection.add_connection(ConnectionKind.ENEMY, origin='Someone who caught you running contraband')
            _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class MerchantEvent3Accept(ChoiceBase):
    kind: Literal['merchant_event_3_accept'] = 'merchant_event_3_accept'
    label: str = 'Accept (roll Deception or Persuade 8+)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            MerchantEvent3SkillRoll(
                pending_id=(event.id, 0),
                instruction='Roll Deception or Persuade 8+: success = extra Benefit roll; fail = ejected, gain Enemy',
                options=[Deception(), Persuade()],
            )
        )


class MerchantEvent3Refuse(ChoiceBase):
    kind: Literal['merchant_event_3_refuse'] = 'merchant_event_3_refuse'
    label: str = 'Refuse (gain Rival)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.add_connection(ConnectionKind.RIVAL, origin='A merchant contact who wanted you to run contraband')
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class MerchantEvent3Handler(CareerHandlerBase):
    type: Literal['merchant_event_3'] = 'merchant_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction=(
                    'Accept the smuggling job (roll Deception or Persuade 8+: '
                    'success = extra Benefit roll, fail = ejected with Enemy) '
                    'or refuse (gain a Rival)?'
                ),
                choices=[MerchantEvent3Accept(), MerchantEvent3Refuse()],
            )
        )
        return pending_idx + 1


# ── event 5: gambling opportunity ────────────────────────────────────────────


class MerchantEvent5Handler(CareerHandlerBase):
    type: Literal['merchant_event_5'] = 'merchant_event_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        career = projection.get_current_career()
        projection.summary.problems.append(
            'Merchant event 5: gambling opportunity — decide how many Benefit rolls to wager, '
            'then roll Gambler 8+ or Broker 8+. '
            'Success: gain half the wagered rolls (round up). '
            'Fail: lose all the wagered rolls. Apply the result manually.'
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event_id))
        return pending_idx


# ── event 8: legal trouble ────────────────────────────────────────────────────


class PendingMerchantEvent8Roll(CareerSkillRollPendingBase):
    kind: Literal['merchant_event_8_roll'] = 'merchant_event_8_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:

        if event.modified_roll == 2:
            _set_forced_prison_career(projection, 'Legal trouble — rolled 2, sent to Prisoner career.')


class MerchantEvent8Handler(CareerHandlerBase):
    type: Literal['merchant_event_8'] = 'merchant_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingSkillChoice(
                pending_id=(event_id, pending_idx),
                instruction='Legal trouble: gain one of Advocate, Admin, Diplomat or Investigate at level 1',
                options=[Advocate(), Admin(), Diplomat(), Investigate()],
            )
        )
        pending_idx += 1
        projection.pending_inputs.append(
            PendingMerchantEvent8Roll(
                pending_id=(event_id, pending_idx),
                instruction='Legal trouble: roll 2D — on a natural 2 you must take the Prisoner career next term',
                options=[],
            )
        )
        return pending_idx + 1


# ── event 9: advanced training ────────────────────────────────────────────────


class MerchantEvent9Handler(CareerHandlerBase):
    type: Literal['merchant_event_9'] = 'merchant_event_9'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        return handle_advanced_training(projection, event_id, pending_idx)


class Merchant(CareerData):
    type: Literal['MERCHANT_CAREER'] = 'MERCHANT_CAREER'

    name: ClassVar[str] = 'Merchant'
    description: ClassVar[str] = (
        'Members of a commercial enterprise. Merchants may crew the ships of the huge trading corporations or they '
        'may work for independent free traders who carry chance cargoes and passengers between worlds.'
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=4)
    allows_assignment_change: ClassVar[bool] = False
    draft_assignments: ClassVar[list[str]] = ['Merchant Marine']

    assignments: ClassVar[list[AssignmentData]] = [
        AssignmentData(
            name='Merchant Marine',
            description='You work on one of the massive cargo haulers run by the Imperium or a megacorporation.',
            survival=CharCheck(characteristic=Chars.EDU, target=5),
            advancement=CharCheck(characteristic=Chars.INT, target=7),
        ),
        AssignmentData(
            name='Free Trader',
            description='You are part of the crew of a tramp trader.',
            survival=CharCheck(characteristic=Chars.DEX, target=6),
            advancement=CharCheck(characteristic=Chars.INT, target=6),
        ),
        AssignmentData(
            name='Broker',
            description='You work in a planetside brokerage or starport.',
            survival=CharCheck(characteristic=Chars.EDU, target=5),
            advancement=CharCheck(characteristic=Chars.INT, target=7),
        ),
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.STR,
                Chars.DEX,
                Chars.END,
                Chars.INT,
                skill_instances(LanguageSkill),
                Streetwise(),
            ]
        ),
        service_skills=SkillTable(
            [
                Drive(),
                VaccSuit(),
                Broker(),
                Steward(),
                Electronics(),
                Persuade(),
            ]
        ),
        advanced_education=SkillTable(
            [
                Engineer(),
                Astrogation(),
                Electronics(),
                Pilot(),
                Admin(),
                Advocate(),
            ],
            min_edu=8,
        ),
        assignment1=SkillTable(
            [  # Merchant Marine
                Pilot(),
                VaccSuit(),
                Athletics(),
                Mechanic(),
                Engineer(),
                Electronics(),
            ]
        ),
        assignment2=SkillTable(
            [  # Free Trader
                Pilot(spacecraft=Level(value=1)),
                VaccSuit(),
                Deception(),
                Mechanic(),
                Streetwise(),
                Gunner(),
            ]
        ),
        assignment3=SkillTable(
            [  # Broker
                Admin(),
                Advocate(),
                Broker(),
                Streetwise(),
                Deception(),
                Persuade(),
            ]
        ),
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, title='Senior Crewman', bonus=RankBonus(skill=Mechanic(), level=1)),
        2: RankEntry(rank=2, title='4th Officer'),
        3: RankEntry(rank=3, title='3rd Officer'),
        4: RankEntry(rank=4, title='2nd Officer', bonus=RankBonus(skill=Pilot(), level=1)),
        5: RankEntry(rank=5, title='1st Officer', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        6: RankEntry(rank=6, title='Captain'),
    }

    ranks_by_assignment: ClassVar[dict[int, dict[int, RankEntry]]] = {
        2: {  # Free Trader
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(skill=Persuade(), level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, title='Experienced Trader', bonus=RankBonus(skill=JackOfAllTrades(), level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6),
        },
        3: {  # Broker
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(skill=Broker(), level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, title='Experienced Broker', bonus=RankBonus(skill=Streetwise(), level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5),
            6: RankEntry(rank=6),
        },
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=1000, benefit=BLADE),
            2: MusterOutRow(cash=5000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            3: MusterOutRow(cash=10000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            4: MusterOutRow(cash=20000, benefit=GUN),
            5: MusterOutRow(cash=20000, benefit=SHIP_SHARE),
            6: MusterOutRow(cash=40000, benefit=FREE_TRADER),
            7: MusterOutRow(cash=40000, benefit=FREE_TRADER),
        }
    )

    mishaps: ClassVar[dict[int, MishapEntry]] = {
        1: MishapEntry(
            text='Severely injured.',
            effects=[CommonMishap1Handler()],
            defer_ejection=True,
        ),
        2: MishapEntry(
            text='You are bankrupted by a rival. You lose all Benefits from '
            'this career and gain the other trader as a Rival.',
            effects=[LoseAllCareerBenefitsEffect(), GainRivalEffect()],
        ),
        3: MishapEntry(
            text='A sudden war destroys your trade routes and contacts, forcing you to '
            'flee that region of space. Gain Gun Combat 1 or Pilot 1.',
            effects=[SkillChoiceEffect(options=[GunCombat(), Pilot()], level=1)],
        ),
        4: MishapEntry(
            text='Your ship or starport is destroyed by criminals. Gain them as an Enemy.',
            effects=[GainEnemyEffect()],
        ),
        5: MishapEntry(
            text='Imperial trade restrictions force you out of business. '
            'You may take the Rogue career for your next term without needing to roll for qualification.',
            effects=[AutoQualifyCareerEffect(career=Rogue)],
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
            text='You are offered the opportunity to smuggle illegal items onto a planet.',
            effects=[MerchantEvent3Handler()],
        ),
        4: CareerEventEntry(
            text='Gain any one of these skills, reflecting your time spent dealing with suppliers and spacers.',
            effects=[
                SkillChoiceEffect(
                    options=[
                        *skill_instances(ProfessionSkill),
                        Electronics(),
                        Engineer(),
                        Animals(),
                        *skill_instances(ScienceSkill),
                    ],
                    level=1,
                )
            ],
        ),
        5: CareerEventEntry(
            text='You have a chance to risk your fortune on a possibly lucrative deal.',
            effects=[MerchantEvent5Handler()],
        ),
        6: CareerEventEntry(
            text='You make an unexpected connection outside your normal circles. Gain a Contact.',
            effects=[GainContactEffect()],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='You are embroiled in legal trouble. Gain a skill; roll 2D — '
            'on a natural 2 you must take Prisoner next term.',
            effects=[MerchantEvent8Handler()],
        ),
        9: CareerEventEntry(
            text='You are given advanced training in a specialist field.',
            effects=[MerchantEvent9Handler()],
        ),
        10: CareerEventEntry(
            text='A good deal ensures you are living the high life for a few years. Gain DM+1 to any one Benefit roll.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        11: CareerEventEntry(
            text='You befriend a useful ally in one sphere.',
            effects=[GainAllyEffect()],
        ),
        12: CareerEventEntry(
            text='Your business or ship thrives. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    }


MERCHANT = Merchant()
