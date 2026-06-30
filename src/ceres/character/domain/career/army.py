from typing import ClassVar, Literal

from ceres.character.domain.benefits import (
    ARMOR,
    CYBERNETIC_IMPLANT,
    WEAPON,
    CharacteristicIncrease,
    ChoiceBenefit,
)
from ceres.character.domain.career.advancement import apply_auto_advance, apply_forced_commission
from ceres.character.domain.career.career_data import (
    AdvancementDmEntry,
    AdvancementDmOption,
    AssignmentData,
    BenefitDmEntry,
    CareerData,
    CareerHandlerBase,
    CareerSkillTables,
    CareerTableEntry,
    CareerTerm,
    CharCheck,
    GainConnectionAndSkillChoiceEntry,
    GainConnectionEntry,
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
    PendingSkillChoice,
    _apply_mishap_ejection,
)
from ceres.character.domain.career.common import CommonMishap1Handler, handle_advanced_training
from ceres.character.domain.career.common_pending import (
    CareerSkillChoicePendingBase,
    CareerSkillRollPendingBase,
)
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.skills import (
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
from ceres.character.mechanism.event_base import ChoiceBase, Event

# ── Career-specific pending input types ──────────────────────────────────────


class ArmyMishap4JoinRing(ChoiceBase):
    kind: Literal['army_mishap_4_join_ring'] = 'army_mishap_4_join_ring'
    label: str = 'Join their ring (Ally, lose Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.get_current_career()
        projection.add_connection(ConnectionKind.ALLY, origin='Your commanding officer who brought you into the ring')
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class ArmyMishap4Cooperate(ChoiceBase):
    kind: Literal['army_mishap_4_cooperate'] = 'army_mishap_4_cooperate'
    label: str = 'Co-operate with MPs (keep Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.get_current_career()
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=False)


class PendingArmyEvent6SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['army_event_6_skill_roll'] = 'army_event_6_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, 0),
                    instruction='Ground war success: gain one level in Gun Combat or Leadership',
                    options=[GunCombat(), Leadership()],
                )
            )
        else:
            from ceres.character.domain.career.advancement import advancement_pending
            from ceres.character.domain.health.health_events import PendingInjuryTable

            career = projection.get_current_career()
            projection.pending_inputs.append(
                PendingInjuryTable(
                    pending_id=(event.id, 0),
                    instruction='Brutal ground war: roll on the Injury table',
                )
            )
            projection.pending_inputs.append(
                advancement_pending(career, projection.summary.current_assignment, event.id, 1)
            )


class PendingArmyEvent11SkillChoice(CareerSkillChoicePendingBase):
    kind: Literal['army_event_11_skill_choice'] = 'army_event_11_skill_choice'


# ── event 12: heroism in battle — commission or promotion ─────────────────────


class ArmyEvent12CommissionChoice(ChoiceBase):
    kind: Literal['army_event_12_commission'] = 'army_event_12_commission'
    label: str = 'Commission (become an officer, rank reset to O1)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        apply_forced_commission(projection, career, event.id)


class ArmyEvent12PromoteChoice(ChoiceBase):
    kind: Literal['army_event_12_promote'] = 'army_event_12_promote'
    label: str = 'Promotion (automatic rank increase)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        apply_auto_advance(projection, career, event.id)


# ── mishap 1: severely injured ────────────────────────────────────────────────


class ArmyMishap4Handler(CareerHandlerBase):
    kind: Literal['army_mishap_4'] = 'army_mishap_4'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
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
    kind: Literal['army_event_6'] = 'army_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingArmyEvent6SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll EDU 8+ to avoid injury in the brutal ground war',
                options=[Chars.EDU],
            )
        )
        return pending_idx + 1


# ── event 8: advanced training ───────────────────────────────────────────────


class ArmyEvent8Handler(CareerHandlerBase):
    kind: Literal['army_event_8'] = 'army_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        return handle_advanced_training(projection, event_id, pending_idx)


# ── event 11: commanding officer interest ────────────────────────────────────


class ArmyEvent11Handler(CareerHandlerBase):
    kind: Literal['army_event_11'] = 'army_event_11'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingArmyEvent11SkillChoice(
                pending_id=(event_id, pending_idx),
                instruction='Commanding officer interest: gain Tactics (military) 1 or DM+4 to next advancement roll',
                options=[Tactics(military=Level(value=1)), AdvancementDmOption()],
            )
        )
        return pending_idx + 1


# ── event 12: heroism ────────────────────────────────────────────────────────


class ArmyEvent12Handler(CareerHandlerBase):
    kind: Literal['army_event_12'] = 'army_event_12'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        career = projection.get_current_career()
        if career.can_attempt_commission(projection):
            projection.pending_inputs.append(
                PendingChoices(
                    pending_id=(event_id, pending_idx),
                    instruction='Heroism in battle: take a commission (O1) or an automatic promotion?',
                    choices=[ArmyEvent12CommissionChoice(), ArmyEvent12PromoteChoice()],
                )
            )
            return pending_idx + 1
        apply_auto_advance(projection, career, event_id)
        return pending_idx


class Army(CareerData):
    kind: Literal['ARMY_CAREER'] = 'ARMY_CAREER'

    name: ClassVar[str] = 'Army'
    description: ClassVar[str] = (
        'Members of the planetary armed fighting forces. Soldiers deal with planetary surface actions, '
        'battles and campaigns. Such individuals may also be mercenaries for hire.'
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

    mishaps: ClassVar[dict[int, CareerTableEntry]] = {
        1: CommonMishap1Handler(
            text='Severely injured in action (this is the same as a result of 2 on the Injury table). '
            'Alternatively, roll twice on the Injury table and take the lower result.',
            defer_ejection=True,
        ),
        2: GainConnectionEntry(
            text='Your unit is slaughtered in a disastrous battle, for which you blame your commander. '
            'Gain them as an Enemy as they have you removed from the service.',
            connection=ConnectionKind.ENEMY,
        ),
        3: GainConnectionAndSkillChoiceEntry(
            text='You are sent to a very unpleasant region (jungle, swamp, desert, icecap, urban) to battle against '
            'guerrilla fighters and rebels. You are discharged because of stress, injury or because the '
            'government wishes to bury the whole incident. Increase Recon or Survival by one level but also gain '
            'the rebels as an Enemy.',
            connection=ConnectionKind.ENEMY,
            options=[Recon(), Survival()],
            level=1,
        ),
        4: ArmyMishap4Handler(
            text='You discover that your commanding officer is engaged in some illegal activity, such as weapon '
            'smuggling. You can join their ring and gain them as an Ally before the inevitable investigation '
            'gets you discharged or you can co-operate with the military police – the official whitewash gets '
            'you discharged anyway but you may keep your Benefit roll from this term of service.',
            defer_ejection=True,
        ),
        5: GainConnectionEntry(
            text='You are tormented by or quarrel with an officer or fellow soldier. '
            'Gain that officer as a Rival as they drive you out of the service.',
            connection=ConnectionKind.RIVAL,
        ),
        6: InjuryEntry(
            text='Injured. Roll on the Injury table.',
            severity='from_table',
        ),
    }

    events: ClassVar[dict[int, CareerTableEntry]] = {
        2: RollMishapEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            leave=False,
        ),
        3: SkillChoiceEntry(
            text='You are assigned to a planet with a hostile or wild environment. '
            'Gain one of Vacc Suit 1, Engineer 1, Animals (riding or training) 1 or Recon 1.',
            options=[VaccSuit(), Engineer(), Animals(), Recon()],
            level=1,
        ),
        4: SkillChoiceEntry(
            text='You are assigned to an urbanised planet torn by war. '
            'Gain one of Stealth 1, Streetwise 1, Persuade 1 or Recon 1.',
            options=[Stealth(), Streetwise(), Persuade(), Recon()],
            level=1,
        ),
        5: BenefitDmEntry(
            text='You are given a special assignment or duty in your unit. Gain DM+1 to any one Benefit roll.',
            amount=1,
        ),
        6: ArmyEvent6Handler(
            text='You are thrown into a brutal ground war. Roll EDU 8+ to avoid injury; '
            'if you succeed, you gain one level in Gun Combat or Leadership.',
        ),
        7: LifeEventEntry(
            text='Life Event. Roll on the Life Events table.',
        ),
        8: ArmyEvent8Handler(
            text='You are given advanced training in a specialist field. '
            'Roll EDU 8+ to increase any one skill you already have by one level.',
        ),
        9: AdvancementDmEntry(
            text='Surrounded and outnumbered by the enemy, you hold out until relief arrives. '
            'Gain DM+2 to your next advancement roll.',
            amount=2,
        ),
        10: SkillChoiceEntry(
            text='You are assigned to a peacekeeping role. Gain one of Admin 1, Investigate 1, Deception 1 or Recon 1.',
            options=[Admin(), Investigate(), Deception(), Recon()],
            level=1,
        ),
        11: ArmyEvent11Handler(
            text='Your commanding officer takes an interest in your career. Either gain Tactics (military) 1 or '
            'DM+4 to your next advancement roll thanks to their aid.',
        ),
        12: ArmyEvent12Handler(
            text='You display heroism in battle. You may gain a promotion or a commission automatically.',
        ),
    }


ARMY = Army()


class ArmyTerm(CareerTerm):
    kind: Literal['army_term'] = 'army_term'
    career: Army


Army.term_class = ArmyTerm
