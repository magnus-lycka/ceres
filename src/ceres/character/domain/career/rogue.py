from typing import ClassVar, Literal

from ceres.character.domain.benefits import (
    ARMOR,
    SHIP_SHARE,
    WEAPON,
    CharacteristicIncrease,
)
from ceres.character.domain.career.career_data import (
    AdvancementDmOption,
    AssignmentData,
    AutoAdvanceEntry,
    CareerData,
    CareerHandlerBase,
    CareerSkillTables,
    CareerTableEntry,
    CareerTerm,
    CharCheck,
    GainConnectionAndBenefitDmEntry,
    GainConnectionEntry,
    GainSkillEntry,
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
    career_progress_pending,
    muster_out_setup,
)
from ceres.character.domain.career.common import CommonMishap1Handler
from ceres.character.domain.career.common_pending import CareerSkillRollPendingBase
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.connection import (
    Ally,
    Contact,
)
from ceres.character.domain.skills import (
    Advocate,
    Astrogation,
    Athletics,
    Broker,
    Carouse,
    Deception,
    Drive,
    Electronics,
    Engineer,
    Gambler,
    GunCombat,
    Gunner,
    Investigate,
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
    Tactics,
    VaccSuit,
)
from ceres.character.mechanism.event_base import ChoiceBase, Event

# ── mishap 2: arrested ────────────────────────────────────────────────────────


class RogueMishap2Handler(CareerHandlerBase):
    kind: Literal['rogue_mishap_2'] = 'rogue_mishap_2'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        from ceres.character.domain.career.prisoner_events import set_forced_prison_career

        set_forced_prison_career(projection, 'Arrested. You must take the Prisoner career in your next term.')
        return pending_idx


# ── mishap 3: betrayed by a friend ───────────────────────────────────────────


class RogueMishap3RollTwo(ChoiceBase):
    kind: Literal['rogue_mishap_3_roll_two'] = 'rogue_mishap_3_roll_two'
    label: str = '2 (sent to Prisoner career next term)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.domain.career.prisoner_events import set_forced_prison_career

        set_forced_prison_career(
            projection,
            'Betrayed by a friend. Rolled 2 — must take the Prisoner career next term.',
        )
        if projection.summary.career_terms:
            projection.summary.career_terms[-1].require_muster_out().lost_rolls += 1
        muster_out_setup(projection, event.id, 0)


class RogueMishap3RollOther(ChoiceBase):
    kind: Literal['rogue_mishap_3_roll_other'] = 'rogue_mishap_3_roll_other'
    label: str = '3–12'

    def handle(self, projection: CharacterProjection, event) -> None:
        if projection.summary.career_terms:
            projection.summary.career_terms[-1].require_muster_out().lost_rolls += 1
        muster_out_setup(projection, event.id, 0)


class RogueMishap3Handler(CareerHandlerBase):
    kind: Literal['rogue_mishap_3'] = 'rogue_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        friends = [c for c in projection.summary.connections if isinstance(c, (Contact, Ally))]
        if friends:
            betrayer = friends[-1]
            projection.summary.connections.remove(betrayer)
            projection.add_connection(
                ConnectionKind.RIVAL, origin=f'A friend who turned on you (formerly {betrayer.display_name})'
            )
        else:
            projection.add_connection(ConnectionKind.RIVAL, origin='An unknown betrayer')

        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Roll 2D: on a result of exactly 2, you must take the Prisoner career next term',
                choices=[RogueMishap3RollTwo(), RogueMishap3RollOther()],
            )
        )
        return pending_idx + 1


# ── event 3: arrested and charged ────────────────────────────────────────────


class RogueEvent3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['rogue_event_3_skill_roll'] = 'rogue_event_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        from ceres.character.domain.career.career_events import _apply_mishap_ejection
        from ceres.character.domain.career.prisoner_events import set_forced_prison_career

        if event.modified_roll >= 8:
            pass  # cleared — _apply_skill_roll auto-queues advancement
        else:
            projection.get_current_career()
            set_forced_prison_career(
                projection, 'Arrested and charged. Failed to avoid conviction — sent to Prisoner career.'
            )
            _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class RogueEvent3Defend(ChoiceBase):
    kind: Literal['rogue_event_3_defend'] = 'rogue_event_3_defend'
    label: str = 'Defend yourself (roll Advocate 8+)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            RogueEvent3SkillRoll(
                pending_id=(event.id, 0),
                instruction=(
                    'Roll Advocate 8+: success = cleared, career continues; '
                    'fail = ejected, must take Prisoner next term'
                ),
                options=[Advocate()],
            )
        )


class RogueEvent3Lawyer(ChoiceBase):
    kind: Literal['rogue_event_3_lawyer'] = 'rogue_event_3_lawyer'
    label: str = 'Hire a lawyer (lose one Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.career_terms[-1].require_muster_out().lost_rolls += 1
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class RogueEvent3Handler(CareerHandlerBase):
    kind: Literal['rogue_event_3'] = 'rogue_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction=(
                    'Defend yourself (roll Advocate 8+: success = cleared, '
                    'fail = ejected + must take Prisoner next term) '
                    'or hire a lawyer (lose one Benefit roll, career continues)?'
                ),
                choices=[RogueEvent3Defend(), RogueEvent3Lawyer()],
            )
        )
        return pending_idx + 1


# ── event 6: backstab fellow rogue ───────────────────────────────────────────


class RogueEvent6Backstab(ChoiceBase):
    kind: Literal['rogue_event_6_backstab'] = 'rogue_event_6_backstab'
    label: str = 'Backstab (DM+2 advancement, gain Enemy)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.add_connection(ConnectionKind.ENEMY, origin='A fellow rogue you betrayed')
        projection.pending_advancement_dm += 2
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class RogueEvent6Refuse(ChoiceBase):
    kind: Literal['rogue_event_6_refuse'] = 'rogue_event_6_refuse'
    label: str = 'Refuse (gain Contact)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.add_connection(ConnectionKind.CONTACT, origin='A fellow rogue you worked alongside')
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class RogueEvent6Handler(CareerHandlerBase):
    kind: Literal['rogue_event_6'] = 'rogue_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Backstab the fellow rogue (DM+2 to next advancement, gain Enemy) '
                'or refuse (gain a Contact instead)?',
                choices=[RogueEvent6Backstab(), RogueEvent6Refuse()],
            )
        )
        return pending_idx + 1


# ── event 9: feud with rival organisation ────────────────────────────────────


class PendingRogueEvent9SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['rogue_event_9_skill_roll'] = 'rogue_event_9_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        if event.modified_roll >= 8:
            projection.summary.career_terms[-1].require_muster_out().extra_rolls += 1
            # no pending added — _apply_skill_roll auto-queues advancement
        else:
            projection.summary.problems.append(
                'Criminal feud: you are injured — roll on the Injury table and apply the result.'
            )


class RogueEvent9Handler(CareerHandlerBase):
    kind: Literal['rogue_event_9'] = 'rogue_event_9'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingRogueEvent9SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Stealth or Gun Combat 8+: success = extra Benefit roll; fail = injured',
                options=[Stealth(), GunCombat()],
            )
        )
        return pending_idx + 1


class Rogue(CareerData):
    kind: Literal['ROGUE_CAREER'] = 'ROGUE_CAREER'

    name: ClassVar[str] = 'Rogue'
    description: ClassVar[str] = (
        'Criminal elements familiar with the rougher or more illegal methods of attaining goals.'
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.DEX, target=6)
    allows_assignment_change: ClassVar[bool] = True

    assignments: ClassVar[list[AssignmentData]] = [
        AssignmentData(
            name='Thief',
            description='You steal from the rich and give to… well, yourself, actually.',
            survival=CharCheck(characteristic=Chars.INT, target=6),
            advancement=CharCheck(characteristic=Chars.DEX, target=6),
        ),
        AssignmentData(
            name='Enforcer',
            description='You are a leg breaker, thug or assassin for a criminal group.',
            survival=CharCheck(characteristic=Chars.END, target=6),
            advancement=CharCheck(characteristic=Chars.STR, target=6),
        ),
        AssignmentData(
            name='Pirate',
            description='You are a space-going corsair.',
            survival=CharCheck(characteristic=Chars.DEX, target=6),
            advancement=CharCheck(characteristic=Chars.INT, target=6),
        ),
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
        personal_development=SkillTable(
            [
                Carouse(),
                Chars.DEX,
                Chars.END,
                Gambler(),
                Melee(),
                GunCombat(),
            ]
        ),
        service_skills=SkillTable(
            [
                Deception(),
                Recon(),
                Athletics(),
                GunCombat(),
                Stealth(),
                Streetwise(),
            ]
        ),
        advanced_education=SkillTable(
            [
                Electronics(),
                Navigation(),
                Medic(),
                Investigate(),
                Broker(),
                Advocate(),
            ],
            min_edu=10,
        ),
        assignment1=SkillTable(
            [  # Thief
                Stealth(),
                Electronics(),
                Recon(),
                Streetwise(),
                Deception(),
                Athletics(),
            ]
        ),
        assignment2=SkillTable(
            [  # Enforcer
                GunCombat(),
                Melee(),
                Streetwise(),
                Persuade(),
                Athletics(),
                Drive(),
            ]
        ),
        assignment3=SkillTable(
            [  # Pirate
                Pilot(),
                Astrogation(),
                Gunner(),
                Engineer(),
                VaccSuit(),
                Melee(),
            ]
        ),
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, bonus=RankBonus(skill=Stealth(), level=1)),
        2: RankEntry(rank=2),
        3: RankEntry(rank=3, bonus=RankBonus(skill=Streetwise(), level=1)),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5, bonus=RankBonus(skill=Recon(), level=1)),
        6: RankEntry(rank=6),
    }

    ranks_by_assignment: ClassVar[dict[int, dict[int, RankEntry]]] = {
        1: {  # Thief
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(skill=Stealth(), level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, bonus=RankBonus(skill=Streetwise(), level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5, bonus=RankBonus(skill=Recon(), level=1)),
            6: RankEntry(rank=6),
        },
        2: {  # Enforcer
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(skill=Persuade(), level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, bonus=RankBonus(choices=[GunCombat(), Melee()], level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5, bonus=RankBonus(skill=Streetwise(), level=1)),
            6: RankEntry(rank=6),
        },
        3: {  # Pirate
            0: RankEntry(rank=0, title='Lackey'),
            1: RankEntry(rank=1, title='Henchman', bonus=RankBonus(choices=[Pilot(), Gunner()], level=1)),
            2: RankEntry(rank=2, title='Corporal'),
            3: RankEntry(rank=3, title='Sergeant', bonus=RankBonus(choices=[GunCombat(), Melee()], level=1)),
            4: RankEntry(rank=4, title='Lieutenant'),
            5: RankEntry(rank=5, title='Leader', bonus=RankBonus(skill=Leadership(), level=1)),
            6: RankEntry(rank=6, title='Captain'),
        },
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=0, benefit=SHIP_SHARE),
            2: MusterOutRow(cash=0, benefit=WEAPON),
            3: MusterOutRow(cash=10000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            4: MusterOutRow(cash=10000, benefit=SHIP_SHARE, count=1),
            5: MusterOutRow(cash=50000, benefit=ARMOR),
            6: MusterOutRow(cash=100000, benefit=CharacteristicIncrease(char=Chars.DEX, amount=1)),
            7: MusterOutRow(cash=100000, benefit=SHIP_SHARE, count=2),
        }
    )

    mishaps: ClassVar[dict[int, CareerTableEntry]] = {
        1: CommonMishap1Handler(
            text='Severely injured.',
            defer_ejection=True,
        ),
        2: RogueMishap2Handler(
            text='Arrested. You must take the Prisoner career in your next term.',
        ),
        3: RogueMishap3Handler(
            text=(
                'Betrayed by a friend. One of your Contacts or Allies betrays you, ending your career. '
                'That Contact or Ally becomes a Rival or Enemy. If you have no Contacts or Allies, you still '
                'gain a Rival or Enemy. Roll 2D — on a 2, you must take the Prisoner career next term.'
            ),
            defer_ejection=True,
        ),
        4: SkillChoiceEntry(
            text='A job goes wrong, forcing you to flee off-planet.',
            options=[Deception(), Pilot(), Athletics(), Gunner()],
            level=1,
        ),
        5: GainConnectionEntry(
            text='A police detective or rival criminal forces you to flee and vows to hunt you down.',
            connection=ConnectionKind.ENEMY,
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
        3: RogueEvent3Handler(
            text='You are arrested and charged.',
        ),
        4: SkillChoiceEntry(
            text='You are involved in the planning of an impressive heist.',
            options=[Electronics(), Mechanic()],
            level=1,
        ),
        5: GainConnectionAndBenefitDmEntry(
            text='One of your crimes pays off.',
            connection=ConnectionKind.ENEMY,
            amount=2,
        ),
        6: RogueEvent6Handler(
            text='You have the opportunity to backstab a fellow rogue for personal gain.',
        ),
        7: LifeEventEntry(
            text='Life Event.',
        ),
        8: SkillChoiceEntry(
            text='You spend months in the dangerous criminal underworld.',
            options=[Streetwise(), Stealth(), Melee(), GunCombat()],
            level=1,
        ),
        9: RogueEvent9Handler(
            text='You become involved in a feud with a rival criminal organisation.',
        ),
        10: GainSkillEntry(
            text='You are involved in a gambling ring. Gain Gambler 1.',
            skill=Gambler(level=Level(value=1)),
        ),
        11: SkillChoiceEntry(
            text='A crime lord considers you his protege.',
            options=[Tactics(), AdvancementDmOption()],
            level=1,
        ),
        12: AutoAdvanceEntry(
            text='You commit a legendary crime. You are automatically promoted.',
        ),
    }


ROGUE = Rogue()


class RogueTerm(CareerTerm):
    kind: Literal['rogue_term'] = 'rogue_term'
    career: Rogue


Rogue.term_class = RogueTerm
