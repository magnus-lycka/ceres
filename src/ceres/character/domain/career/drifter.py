from typing import ClassVar, Literal

from ceres.character.domain.benefits import (
    ALLY,
    CONTACT,
    SHIP_SHARE,
    WEAPON,
    CharacteristicIncrease,
)
from ceres.character.domain.career.career_data import (
    AssignmentData,
    AutoAdvanceEntry,
    BenefitDmEntry,
    CareerData,
    CareerHandlerBase,
    CareerSkillTables,
    CareerTableEntry,
    CharacteristicLossEntry,
    CharCheck,
    GainConnectionEntry,
    InjuryEntry,
    LifeEventEntry,
    MusterOutData,
    MusterOutRow,
    NoEffectEntry,
    RankBonus,
    RankEntry,
    RollMishapEntry,
    SkillChoiceEntry,
    SkillTable,
    _blank_ranks,
)
from ceres.character.domain.career.career_events import (
    PendingChoices,
    PendingSkillChoice,
    career_progress_pending,
)
from ceres.character.domain.career.common import CommonMishap1Handler
from ceres.character.domain.career.common_pending import (
    CareerSkillRollPendingBase,
    append_increment_existing_skill_pending,
)
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.health.health_events import PendingInjuryTable
from ceres.character.domain.skills import (
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
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.pending_input import ChoiceBase

# ── Career-specific pending input types ──────────────────────────────────────


class PendingDrifterMishap5SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['drifter_mishap_5_skill_roll'] = 'drifter_mishap_5_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        from ceres.character.domain.career.career_events import (
            _apply_mishap_ejection,
            _set_forced_prison_career,
        )

        projection.get_current_career()
        projection.add_connection(ConnectionKind.RIVAL, origin='A friend who turned on you')
        if event.modified_roll == 2:
            _set_forced_prison_career(projection, 'Betrayed — rolled 2, sent to Prisoner career.')
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class DrifterEvent3Accept(ChoiceBase):
    kind: Literal['drifter_event_3_accept'] = 'drifter_event_3_accept'
    label: str = 'Accept (DM+4 to next qualification roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_qualification_dm += 4
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class DrifterEvent3Decline(ChoiceBase):
    kind: Literal['drifter_event_3_decline'] = 'drifter_event_3_decline'
    label: str = 'Decline'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PendingDrifterEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['drifter_event_8_skill_roll'] = 'drifter_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, 0),
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
                pending_id=(event.id, 0),
                instruction='Risky adventure outcome: roll 1D on Injury table',
            )
        )


class DrifterEvent9Prison(ChoiceBase):
    kind: Literal['drifter_event_9_prison'] = 'drifter_event_9_prison'
    label: str = 'Be sent to Prisoner career'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.domain.career.career_events import _set_forced_prison_career

        _set_forced_prison_career(projection, 'Sent to Prisoner career after a risky adventure.')


class PendingDrifterEvent9RollSkillRoll(CareerSkillRollPendingBase):
    kind: Literal['drifter_event_9_roll_skill_roll'] = 'drifter_event_9_roll_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        career = projection.get_current_career()
        roll = event.modified_roll
        if roll <= 2:
            projection.pending_inputs.append(
                PendingChoices(
                    pending_id=(event.id, 0),
                    instruction='Risky adventure (1-2): choose — roll on Injury table, or be sent to Prisoner career?',
                    choices=[DrifterEvent9Injury(), DrifterEvent9Prison()],
                )
            )
            projection.pending_inputs.append(career_progress_pending(projection, career, event.id, 1))
        elif roll == 3:
            projection.pending_inputs.append(
                PendingInjuryTable(
                    pending_id=(event.id, 0),
                    instruction='Risky adventure (3): roll 1D on Injury table',
                )
            )
            projection.pending_inputs.append(career_progress_pending(projection, career, event.id, 1))
        else:  # 4-6
            projection.summary.career_terms[-1].require_muster_out().extra_rolls += 1
            # _apply_skill_roll auto-queues advancement


class DrifterEvent9Accept(ChoiceBase):
    kind: Literal['drifter_event_9_accept'] = 'drifter_event_9_accept'
    label: str = 'Accept the adventure'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            PendingDrifterEvent9RollSkillRoll(
                pending_id=(event.id, 0),
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
    kind: Literal['drifter_mishap_5'] = 'drifter_mishap_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingDrifterMishap5SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Betrayed by a friend: gain a Rival. '
                'Roll 2D — on a natural 2, must take Prisoner next term',
                options=[],
            )
        )
        return pending_idx + 1


# ── event 3: patron job offer ─────────────────────────────────────────────────


class DrifterEvent3Handler(CareerHandlerBase):
    kind: Literal['drifter_event_3'] = 'drifter_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction="Accept the patron's job offer (DM+4 to next Qualification roll) or decline?",
                choices=[DrifterEvent3Accept(), DrifterEvent3Decline()],
            )
        )
        return pending_idx + 1


# ── event 8: attacked by enemies ─────────────────────────────────────────────


class DrifterEvent8Handler(CareerHandlerBase):
    kind: Literal['drifter_event_8'] = 'drifter_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.add_connection(ConnectionKind.ENEMY, origin='Someone who attacked you on your travels')
        projection.pending_inputs.append(
            PendingDrifterEvent8SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Melee or Gun Combat 8+: success = increase that skill; fail = injured',
                options=[Melee(), GunCombat()],
            )
        )
        return pending_idx + 1


# ── event 9: risky adventure ──────────────────────────────────────────────────


class DrifterEvent9Handler(CareerHandlerBase):
    kind: Literal['drifter_event_9'] = 'drifter_event_9'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Accept the risky adventure (roll 1D for outcome) or decline?',
                choices=[DrifterEvent9Accept(), DrifterEvent9Decline()],
            )
        )
        return pending_idx + 1


# ── event 10: honed abilities ────────────────────────────────────────────────


class DrifterEvent10Handler(CareerHandlerBase):
    kind: Literal['drifter_event_10'] = 'drifter_event_10'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        append_increment_existing_skill_pending(
            projection,
            (event_id, pending_idx),
            'Increase any skill you already have by one level',
        )
        return pending_idx + 1


# ── event 11: forcibly drafted ────────────────────────────────────────────────


class DrifterEvent11Handler(CareerHandlerBase):
    kind: Literal['drifter_event_11'] = 'drifter_event_11'

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
    kind: Literal['DRIFTER_CAREER'] = 'DRIFTER_CAREER'

    name: ClassVar[str] = 'Drifter'
    description: ClassVar[str] = (
        'Wanderers, hitchhikers and travellers, drifters are those '
        'who roam the stars without obvious purpose or direction.'
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

    ranks: ClassVar[dict[int, RankEntry]] = _blank_ranks()

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

    mishaps: ClassVar[dict[int, CareerTableEntry]] = {
        1: CommonMishap1Handler(
            text='Severely injured.',
            defer_ejection=True,
        ),
        2: InjuryEntry(
            text='Injured. Roll on the Injury table.',
            severity='from_table',
        ),
        3: GainConnectionEntry(
            text='You run afoul of a criminal gang, corrupt bureaucrat or other foe. Gain an Enemy.',
            connection=ConnectionKind.ENEMY,
        ),
        4: CharacteristicLossEntry(
            text='You suffer from a life-threatening illness. Reduce your END by 1.',
            characteristic=Chars.END,
            amount=1,
        ),
        5: DrifterMishap5Handler(
            text='Betrayed by a friend. Gain a Rival. Roll 2D — on a natural 2, '
            'you must take the Prisoner career next term.',
            defer_ejection=True,
        ),
        6: NoEffectEntry(
            text='You do not know what happened to you. There is a gap in your memory.',
        ),
    }

    events: ClassVar[dict[int, CareerTableEntry]] = {
        2: RollMishapEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            leave=False,
        ),
        3: DrifterEvent3Handler(
            text='A patron offers you a chance at a job.',
        ),
        4: SkillChoiceEntry(
            text='You pick up a few useful skills here and there.',
            options=[JackOfAllTrades(), Survival(), Streetwise(), Melee()],
            level=1,
        ),
        5: BenefitDmEntry(
            text='You manage to scavenge something of use.',
            amount=1,
        ),
        6: LifeEventEntry(
            text='You encounter something unusual.',
        ),
        7: LifeEventEntry(
            text='Life Event.',
        ),
        8: DrifterEvent8Handler(
            text='You are attacked by enemies.',
        ),
        9: DrifterEvent9Handler(
            text='You are offered a chance to take part in a risky but rewarding adventure.',
        ),
        10: DrifterEvent10Handler(
            text='Life on the edge hones your abilities. Increase any skill you already have by one level.',
        ),
        11: DrifterEvent11Handler(
            text='You are forcibly drafted.',
        ),
        12: AutoAdvanceEntry(
            text='You thrive on adversity. You are automatically promoted.',
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

    def is_draft_alternative(self, summary) -> bool:
        return True

    def _basic_training_table_name(self, assignment) -> str:
        return f'assignment{self.assignment_index(assignment)}'


DRIFTER = Drifter()
