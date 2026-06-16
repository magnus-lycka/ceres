from typing import Any, ClassVar, Literal

from ceres.character.domain.benefits import (
    PERSONAL_VEHICLE,
    SHIP_SHARE,
    SHIPS_BOAT,
    TAS_MEMBERSHIP,
    WEAPON,
    CharacteristicIncrease,
    ChoiceBenefit,
)
from ceres.character.domain.career.career_data import (
    AdvancementDmEffect,
    AdvancementDmOption,
    AssignmentData,
    AutoAdvanceEffect,
    BenefitDmEffect,
    CareerData,
    CareerEventEntry,
    CareerHandlerBase,
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
from ceres.character.domain.career.career_events import (
    PendingChoices,
    _apply_mishap_ejection,
    career_progress_pending,
)
from ceres.character.domain.career.common import CommonMishap1Handler, handle_advanced_training
from ceres.character.domain.career.common_pending import CareerSkillRollPendingBase
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.skills import (
    Admin,
    Astrogation,
    Athletics,
    Deception,
    Diplomat,
    Electronics,
    Engineer,
    Flyer,
    Gambler,
    GunCombat,
    Gunner,
    Leadership,
    Level,
    Mechanic,
    Medic,
    Melee,
    Pilot,
    Recon,
    Steward,
    Tactics,
    VaccSuit,
)
from ceres.character.mechanism.pending_input import ChoiceBase

_MISHAP_3_SKILLS: dict[str, list] = {
    'Line/Crew': [Electronics(), Gunner()],
    'Engineer/Gunner': [Mechanic(), VaccSuit()],
    'Flight': [Pilot(), Tactics()],
}


# ── Career-specific pending input types ──────────────────────────────────────


class PendingNavyMishap3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['navy_mishap_3_skill_roll'] = 'navy_mishap_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:

        projection.get_current_career()
        lose = event.modified_roll < 8
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=lose)


class NavyMishap4Responsible(ChoiceBase):
    kind: Literal['navy_mishap_4_responsible'] = 'navy_mishap_4_responsible'
    label: str = 'Accept responsibility (gain one free skill roll, ejected, lose Benefit)'

    def handle(self, projection: CharacterProjection, event) -> None:

        projection.get_current_career()
        projection.summary.problems.append(
            'Navy mishap 4 (responsible): you gain one free roll on the Skills and Training tables '
            'before ejection — apply a skill table roll manually to this character.'
        )
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class NavyMishap4NotResponsible(ChoiceBase):
    kind: Literal['navy_mishap_4_not_responsible'] = 'navy_mishap_4_not_responsible'
    label: str = 'Deny blame (gain Enemy, keep Benefit)'

    def handle(self, projection: CharacterProjection, event) -> None:

        projection.get_current_career()
        projection.add_connection(ConnectionKind.ENEMY, origin='The officer who falsely blamed you for the accident')
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=False)


class NavyEvent10Profit(ChoiceBase):
    kind: Literal['navy_event_10_profit'] = 'navy_event_10_profit'
    label: str = 'Take the profit (gain extra Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.career_terms[-1].require_muster_out().extra_rolls += 1
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class NavyEvent10Refuse(ChoiceBase):
    kind: Literal['navy_event_10_refuse'] = 'navy_event_10_refuse'
    label: str = 'Refuse (gain DM+2 to next advancement)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_advancement_dm += 2
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


# ── mishap 3: battle skill check ─────────────────────────────────────────────


class NavyMishap3Handler(CareerHandlerBase):
    type: Literal['navy_mishap_3'] = 'navy_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        assignment_obj = projection.summary.current_assignment
        assignment = assignment_obj.name if assignment_obj else 'Line/Crew'
        options = _MISHAP_3_SKILLS.get(assignment, [Electronics(), Gunner()])
        projection.pending_inputs.append(
            PendingNavyMishap3SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction=(
                    f'Roll {" or ".join(type(o).name() for o in options)} '
                    '8+ — success: honourable discharge (keep Benefit); '
                    'fail: court-martialled (lose Benefit)'
                ),
                options=options,
            )
        )
        return pending_idx + 1


# ── mishap 4: blamed for accident ────────────────────────────────────────────


class NavyMishap4Handler(CareerHandlerBase):
    type: Literal['navy_mishap_4'] = 'navy_mishap_4'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction=(
                    'Were you responsible for the accident? '
                    'Accept responsibility (gain one free skill roll, lose Benefit) '
                    'or deny blame (gain Enemy officer, keep Benefit)?'
                ),
                choices=[NavyMishap4Responsible(), NavyMishap4NotResponsible()],
            )
        )
        return pending_idx + 1


# ── event 5: advanced training ───────────────────────────────────────────────


class NavyEvent5Handler(CareerHandlerBase):
    type: Literal['navy_event_5'] = 'navy_event_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        return handle_advanced_training(projection, event_id, pending_idx)


# ── event 10: abuse position for profit ──────────────────────────────────────


class NavyEvent10Handler(CareerHandlerBase):
    type: Literal['navy_event_10'] = 'navy_event_10'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Abuse your position for profit (gain extra Benefit roll) '
                'or refuse (DM+2 to next advancement)?',
                choices=[NavyEvent10Profit(), NavyEvent10Refuse()],
            )
        )
        return pending_idx + 1


class Navy(CareerData):
    type: Literal['NAVY_CAREER'] = 'NAVY_CAREER'

    name: ClassVar[str] = 'Navy'
    description: ClassVar[str] = (
        'Members of the interstellar navy that patrols space between the stars. The navy has the responsibility for '
        'the protection of society from foreign powers and lawless elements in the interstellar trade channels.'
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=6)
    allows_assignment_change: ClassVar[bool] = True
    commission: ClassVar[CharCheck | None] = CharCheck(characteristic=Chars.SOC, target=8)
    draft_assignments: ClassVar[list[str]] = ['Line/Crew', 'Engineer/Gunner', 'Flight']

    assignments: ClassVar[list[AssignmentData]] = [
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
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
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
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0, title='Crewman'),
        1: RankEntry(rank=1, title='Able Spacehand', bonus=RankBonus(skill=Mechanic(), level=1)),
        2: RankEntry(rank=2, title='Petty Officer, 3rd class', bonus=RankBonus(skill=VaccSuit(), level=1)),
        3: RankEntry(rank=3, title='Petty Officer, 2nd class'),
        4: RankEntry(rank=4, title='Petty Officer, 1st class', bonus=RankBonus(characteristic=Chars.END, level=1)),
        5: RankEntry(rank=5, title='Chief Petty Officer'),
        6: RankEntry(rank=6, title='Master Chief'),
    }

    officer_ranks: ClassVar[dict[int, RankEntry]] = {
        1: RankEntry(rank=1, title='Ensign', bonus=RankBonus(skill=Melee(), level=1)),
        2: RankEntry(rank=2, title='Sublieutenant', bonus=RankBonus(skill=Leadership(), level=1)),
        3: RankEntry(rank=3, title='Lieutenant'),
        4: RankEntry(rank=4, title='Commander', bonus=RankBonus(skill=Tactics(), level=1)),
        5: RankEntry(rank=5, title='Captain', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        6: RankEntry(rank=6, title='Admiral', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=1000, benefit=ChoiceBenefit(options=[PERSONAL_VEHICLE, SHIP_SHARE])),
            2: MusterOutRow(cash=5000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            3: MusterOutRow(
                cash=5000, benefit=ChoiceBenefit(options=[CharacteristicIncrease(char=Chars.EDU, amount=1), SHIP_SHARE])
            ),
            4: MusterOutRow(cash=10000, benefit=WEAPON),
            5: MusterOutRow(cash=20000, benefit=TAS_MEMBERSHIP),
            6: MusterOutRow(cash=50000, benefit=ChoiceBenefit(options=[SHIPS_BOAT, SHIP_SHARE])),
            7: MusterOutRow(cash=50000, benefit=CharacteristicIncrease(char=Chars.SOC, amount=2)),
        }
    )

    mishaps: ClassVar[dict[int, MishapEntry]] = {
        1: MishapEntry(
            text='Severely injured in action.',
            effects=[CommonMishap1Handler()],
            defer_ejection=True,
        ),
        2: MishapEntry(
            text='Placed in the frozen watch and revived improperly. Reduce STR, DEX or END. You are not ejected.',
            stay_in_career=True,
            effects=[DecreaseCharacteristicChoiceEffect(options=[Chars.STR, Chars.DEX, Chars.END], amount=1)],
        ),
        3: MishapEntry(
            text='During a battle, defeat or victory depends on your actions.',
            defer_ejection=True,
            effects=[NavyMishap3Handler()],
        ),
        4: MishapEntry(
            text='Blamed for an accident that causes the death of several crew members.',
            defer_ejection=True,
            effects=[NavyMishap4Handler()],
        ),
        5: MishapEntry(
            text='You quarrel with an officer or fellow crewman. Gain a Rival.',
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
            text='You join a gambling circle on board.',
            effects=[SkillChoiceEffect(options=[Gambler(), Deception()], level=1)],
        ),
        4: CareerEventEntry(
            text='Given a special assignment or duty on board ship.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        5: CareerEventEntry(
            text='Advanced training in a specialist field.',
            effects=[NavyEvent5Handler()],
        ),
        6: CareerEventEntry(
            text='Your vessel participates in a notable military engagement.',
            effects=[SkillChoiceEffect(options=[Electronics(), Engineer(), Gunner(), Pilot()], level=1)],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='Your vessel participates in a diplomatic mission.',
            effects=[SkillChoiceEffect(options=[Recon(), Diplomat(), Steward()], level=1), GainContactEffect()],
        ),
        9: CareerEventEntry(
            text='You foil an attempted crime on board. Gain an Enemy and DM+2 to next advancement.',
            effects=[GainEnemyEffect(), AdvancementDmEffect(amount=2)],
        ),
        10: CareerEventEntry(
            text='Opportunity to abuse your position for profit.',
            effects=[NavyEvent10Handler()],
        ),
        11: CareerEventEntry(
            text='Your commanding officer takes an interest in your career.',
            effects=[SkillChoiceEffect(options=[Tactics(), AdvancementDmOption()], level=1)],
        ),
        12: CareerEventEntry(
            text='You display heroism in battle, saving the whole ship.',
            effects=[AutoAdvanceEffect()],
        ),
    }


NAVY = Navy()
