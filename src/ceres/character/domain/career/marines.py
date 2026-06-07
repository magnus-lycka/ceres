from typing import Any, ClassVar, Literal

from ceres.character.domain.benefits import (
    ARMOR,
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
    CareerData,
    CareerEventEntry,
    CareerHandlerBase,
    CareerSkillTables,
    CharCheck,
    DecreaseCharacteristicEffect,
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
    PendingSkillChoice,
    career_progress_pending,
)
from ceres.character.domain.career.common import handle_advanced_training
from ceres.character.domain.career.common_pending import CareerSkillRollPendingBase
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import (
    Ally,
    Contact,
    Enemy,
)
from ceres.character.domain.skills import (
    Admin,
    Advocate,
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
    Leadership,
    Level,
    Mechanic,
    Medic,
    Melee,
    Navigation,
    Persuade,
    Pilot,
    Recon,
    Stealth,
    Streetwise,
    Survival,
    Tactics,
    VaccSuit,
)
from ceres.character.mechanism.character_state import CharacterProjection
from ceres.character.mechanism.pending_input import ChoiceBase

# ── Career-specific pending input types ──────────────────────────────────────


class MarinesMishap4Refuse(ChoiceBase):
    kind: Literal['marines_mishap_4_refuse'] = 'marines_mishap_4_refuse'
    label: str = 'Refuse (ejected, lose Benefit, gain Contact)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.domain.career.career_events import _apply_mishap_ejection

        career = projection.get_current_career()
        projection.summary.connections.append(Contact(source='A fellow soldier who was part of that black ops mission'))
        _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class MarinesMishap4Accept(ChoiceBase):
    kind: Literal['marines_mishap_4_accept'] = 'marines_mishap_4_accept'
    label: str = 'Accept (roll Deception or Persuade 8+: success = stay, fail = ejected, lose Benefit)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            PendingMarinesMishap4SkillRoll(
                pending_id=(event.id, 0),
                instruction='Roll Deception or Persuade 8+: success = stay in career; fail = ejected, lose Benefit',
                options=[Deception(), Persuade()],
            )
        )


class PendingMarinesMishap4SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['marines_mishap_4_skill_roll'] = 'marines_mishap_4_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:
        from ceres.character.domain.career.career_events import _apply_mishap_ejection

        career = projection.get_current_career()
        if event.modified_roll < 8:
            _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)
        # success: do nothing — _apply_skill_roll auto-queues advancement


class PendingMarinesEvent6SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['marines_event_6_skill_roll'] = 'marines_event_6_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, 0),
                    instruction='Fortress assault success: gain one level in Tactics or Leadership',
                    options=[Tactics(), Leadership()],
                )
            )
        else:
            projection.summary.problems.append(
                'Fortress assault: you are injured — roll on the Injury table and apply the result.'
            )


class MarinesEvent9Report(ChoiceBase):
    kind: Literal['marines_event_9_report'] = 'marines_event_9_report'
    label: str = 'Report the commander (DM+2 to next advancement, commander becomes Enemy)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.connections.append(
            Enemy(source='Your commanding officer, whom you reported for the mission failure')
        )
        projection.pending_advancement_dm += 2
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class MarinesEvent9Protect(ChoiceBase):
    kind: Literal['marines_event_9_protect'] = 'marines_event_9_protect'
    label: str = 'Protect the commander (DM+1 to next advancement, commander becomes Ally)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.connections.append(
            Ally(source='Your commanding officer, whom you protected from the fallout')
        )
        projection.pending_advancement_dm += 1
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


# ── mishap 4: black ops mission ───────────────────────────────────────────────


class MarinesMishap4Handler(CareerHandlerBase):
    type: Literal['marines_mishap_4'] = 'marines_mishap_4'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction=(
                    'Refuse (ejected, lose Benefit, gain Contact among other soldiers) '
                    'or accept (roll Deception or Persuade 8+: success = stay, fail = ejected, lose Benefit)?'
                ),
                choices=[MarinesMishap4Refuse(), MarinesMishap4Accept()],
            )
        )
        return pending_idx + 1


# ── event 5: advanced training ───────────────────────────────────────────────


class MarinesEvent5Handler(CareerHandlerBase):
    type: Literal['marines_event_5'] = 'marines_event_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        return handle_advanced_training(projection, event_id, pending_idx)


# ── event 6: assault on an enemy fortress ────────────────────────────────────


class MarinesEvent6Handler(CareerHandlerBase):
    type: Literal['marines_event_6'] = 'marines_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingMarinesEvent6SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Melee or Gun Combat 8+: success = gain Tactics or Leadership; fail = injured',
                options=[Melee(), GunCombat()],
            )
        )
        return pending_idx + 1


# ── event 9: mission goes wrong ───────────────────────────────────────────────


class MarinesEvent9Handler(CareerHandlerBase):
    type: Literal['marines_event_9'] = 'marines_event_9'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction=(
                    'Report the commander (DM+2 to next advancement, commander becomes Enemy) '
                    'or protect them (DM+1 to next advancement, commander becomes Ally)?'
                ),
                choices=[MarinesEvent9Report(), MarinesEvent9Protect()],
            )
        )
        return pending_idx + 1


class Marines(CareerData):
    type: Literal['MARINES_CAREER'] = 'MARINES_CAREER'

    name: ClassVar[str] = 'Marines'
    description: ClassVar[str] = (
        'Members of the armed fighting forces carried aboard starships, marines deal with piracy and boarding actions in space, defend the starports and bases belonging to the navy and supplement ground forces such as the army.'
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.END, target=6)
    allows_assignment_change: ClassVar[bool] = True
    commission: ClassVar[CharCheck | None] = CharCheck(characteristic=Chars.SOC, target=8)
    draft_assignments: ClassVar[list[str]] = ['Support', 'Star Marine', 'Ground Assault']

    assignments: ClassVar[list[AssignmentData]] = [
        AssignmentData(
            name='Support',
            description='You are a quartermaster, engineer or battlefield medic in the marines.',
            survival=CharCheck(characteristic=Chars.END, target=5),
            advancement=CharCheck(characteristic=Chars.EDU, target=7),
        ),
        AssignmentData(
            name='Star Marine',
            description='You are trained to fight boarding actions and capture enemy vessels.',
            survival=CharCheck(characteristic=Chars.END, target=6),
            advancement=CharCheck(characteristic=Chars.EDU, target=6),
        ),
        AssignmentData(
            name='Ground Assault',
            description="You are kicked out of a spacecraft in high orbit and told to 'capture that planet'.",
            survival=CharCheck(characteristic=Chars.END, target=7),
            advancement=CharCheck(characteristic=Chars.EDU, target=5),
        ),
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.STR,
                Chars.DEX,
                Chars.END,
                Gambler(),
                Melee(unarmed=Level(value=1)),
                Melee(blade=Level(value=1)),
            ]
        ),
        service_skills=SkillTable(
            [
                Athletics(),
                VaccSuit(),
                Tactics(),
                HeavyWeapons(),
                GunCombat(),
                Stealth(),
            ]
        ),
        advanced_education=SkillTable(
            [
                Medic(),
                Survival(),
                Explosives(),
                Engineer(),
                Pilot(),
                Navigation(),
            ],
            min_edu=8,
        ),
        officer=SkillTable(
            [
                Electronics(),
                Tactics(),
                Admin(),
                Advocate(),
                Diplomat(),
                Leadership(),
            ]
        ),
        assignment1=SkillTable(
            [  # Support
                Electronics(),
                Mechanic(),
                [Drive(), Flyer()],
                Medic(),
                HeavyWeapons(),
                GunCombat(),
            ]
        ),
        assignment2=SkillTable(
            [  # Star Marine
                VaccSuit(),
                Athletics(),
                Recon(),
                Melee(blade=Level(value=1)),
                Electronics(),
                GunCombat(),
            ]
        ),
        assignment3=SkillTable(
            [  # Ground Assault
                VaccSuit(),
                HeavyWeapons(),
                Recon(),
                Melee(blade=Level(value=1)),
                Tactics(military=Level(value=1)),
                GunCombat(),
            ]
        ),
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0, title='Marine'),
        1: RankEntry(rank=1, title='Lance Corporal', bonus=RankBonus(skill=GunCombat(), level=1)),
        2: RankEntry(rank=2, title='Corporal'),
        3: RankEntry(rank=3, title='Lance Sergeant', bonus=RankBonus(skill=Leadership(), level=1)),
        4: RankEntry(rank=4, title='Sergeant'),
        5: RankEntry(rank=5, title='Gunnery Sergeant', bonus=RankBonus(characteristic=Chars.END, level=1)),
        6: RankEntry(rank=6, title='Sergeant Major'),
    }

    officer_ranks: ClassVar[dict[int, RankEntry]] = {
        1: RankEntry(rank=1, title='Lieutenant', bonus=RankBonus(skill=Leadership(), level=1)),
        2: RankEntry(rank=2, title='Captain'),
        3: RankEntry(rank=3, title='Force Commander', bonus=RankBonus(skill=Tactics(), level=1)),
        4: RankEntry(rank=4, title='Lieutenant Colonel'),
        5: RankEntry(rank=5, title='Colonel', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        6: RankEntry(rank=6, title='Brigadier'),
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=2000, benefit=ARMOR),
            2: MusterOutRow(cash=5000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            3: MusterOutRow(cash=5000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            4: MusterOutRow(cash=10000, benefit=WEAPON),
            5: MusterOutRow(cash=20000, benefit=TAS_MEMBERSHIP),
            6: MusterOutRow(
                cash=30000, benefit=ChoiceBenefit(options=[ARMOR, CharacteristicIncrease(char=Chars.END, amount=1)])
            ),
            7: MusterOutRow(cash=40000, benefit=CharacteristicIncrease(char=Chars.SOC, amount=2)),
        }
    )

    mishaps: ClassVar[dict[int, MishapEntry]] = {
        1: MishapEntry(
            text='Severely injured.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='Captured and mistreated by the enemy. Gain your jailer as an Enemy and reduce STR and DEX by one.',
            effects=[
                GainEnemyEffect(),
                DecreaseCharacteristicEffect(characteristic=Chars.STR, amount=1),
                DecreaseCharacteristicEffect(characteristic=Chars.DEX, amount=1),
            ],
        ),
        3: MishapEntry(
            text='Stranded behind enemy lines. Increase Stealth or Survival but you are ejected.',
            effects=[SkillChoiceEffect(options=[Stealth(), Survival()], level=1)],
        ),
        4: MishapEntry(
            text='Ordered to take part in a black ops mission that goes against your conscience.',
            defer_ejection=True,
            effects=[MarinesMishap4Handler()],
        ),
        5: MishapEntry(
            text='You quarrel with an officer or fellow marine. Gain a Rival.',
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
            text='Trapped behind enemy lines.',
            effects=[SkillChoiceEffect(options=[Survival(), Stealth(), Deception(), Streetwise()], level=1)],
        ),
        4: CareerEventEntry(
            text='Assigned to the security staff of a space station.',
            effects=[SkillChoiceEffect(options=[VaccSuit(), Athletics()], level=1)],
        ),
        5: CareerEventEntry(
            text='Advanced training in a specialist field.',
            effects=[MarinesEvent5Handler()],
        ),
        6: CareerEventEntry(
            text='Assault on an enemy fortress.',
            effects=[MarinesEvent6Handler()],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='Front lines of a planetary assault and occupation.',
            effects=[SkillChoiceEffect(options=[Recon(), GunCombat(), Leadership(), Electronics()], level=1)],
        ),
        9: CareerEventEntry(
            text="A mission goes disastrously wrong due to your commander's error.",
            effects=[MarinesEvent9Handler()],
        ),
        10: CareerEventEntry(
            text='Assigned to a black ops mission.',
            effects=[AdvancementDmEffect(amount=2)],
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


MARINES = Marines()
