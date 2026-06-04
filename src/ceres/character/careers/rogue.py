from typing import Literal

from ceres.character.benefits import (
    ARMOR,
    SHIP_SHARE,
    WEAPON,
    CharacteristicIncrease,
)
from ceres.character.careers.career_data import (
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
    GainSkillEffect,
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
from ceres.character.events import (
    PendingChoices,
    SkillRollEvent,
    career_progress_pending,
    muster_out_setup,
)
from ceres.character.skills import (
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
from ceres.character.state import (
    Ally,
    CharacterProjection,
    ChoiceBase,
    Contact,
    EffectTrigger,
    EffectType,
    Enemy,
    Rival,
    ScheduledEffect,
)

ROGUE = Career(
    name='Rogue',
    description=('Criminal elements familiar with the rougher or more illegal methods of attaining goals.'),
)


# ── mishap 2: arrested ────────────────────────────────────────────────────────


class RogueMishap2Handler(CareerHandlerBase):
    type: Literal['rogue_mishap_2'] = 'rogue_mishap_2'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        from ceres.character.careers.prisoner import PRISONER

        projection.forced_next_career = PRISONER
        return pending_idx


# ── mishap 3: betrayed by a friend ───────────────────────────────────────────


class RogueMishap3RollTwo(ChoiceBase):
    kind: Literal['rogue_mishap_3_roll_two'] = 'rogue_mishap_3_roll_two'
    label: str = '2 (sent to Prisoner career next term)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.careers.loader import load_careers
        from ceres.character.careers.prisoner import PRISONER

        projection.forced_next_career = PRISONER
        career_obj = projection.summary.current_career
        career = load_careers().get(career_obj.name if career_obj else '')
        if career is None:
            return
        muster_out_setup(projection, career, event.id, 0, lose_current_term=True)


class RogueMishap3RollOther(ChoiceBase):
    kind: Literal['rogue_mishap_3_roll_other'] = 'rogue_mishap_3_roll_other'
    label: str = '3–12'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.careers.loader import load_careers

        career_obj = projection.summary.current_career
        career = load_careers().get(career_obj.name if career_obj else '')
        if career is None:
            return
        muster_out_setup(projection, career, event.id, 0, lose_current_term=True)


class RogueMishap3Handler(CareerHandlerBase):
    type: Literal['rogue_mishap_3'] = 'rogue_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        friends = [c for c in projection.summary.connections if isinstance(c, (Contact, Ally))]
        if friends:
            betrayer = friends[-1]
            projection.summary.connections.remove(betrayer)
            projection.summary.connections.append(
                Rival(source=f'A friend who turned on you (formerly {betrayer.display_name})')
            )
        else:
            projection.summary.connections.append(Rival(source='An unknown betrayer'))

        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll 2D: on a result of exactly 2, you must take the Prisoner career next term',
                choices=[RogueMishap3RollTwo(), RogueMishap3RollOther()],
            )
        )
        return pending_idx + 1


# ── event 3: arrested and charged ────────────────────────────────────────────


class RogueEvent3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['rogue_event_3_skill_roll'] = 'rogue_event_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.careers.prisoner import PRISONER
        from ceres.character.events import _apply_mishap_ejection

        if event.modified_roll >= 8:
            pass  # cleared — _apply_skill_roll auto-queues advancement
        else:
            career = projection.get_current_career()
            projection.forced_next_career = PRISONER
            _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


class RogueEvent3Defend(ChoiceBase):
    kind: Literal['rogue_event_3_defend'] = 'rogue_event_3_defend'
    label: str = 'Defend yourself (roll Advocate 8+)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            RogueEvent3SkillRoll(
                id=f'{event.id}.0',
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
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger=EffectTrigger.MUSTER_OUT_REDUCE,
                source_event_id=event.id,
                effect={'type': EffectType.REDUCE, 'value': 1},
            )
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class RogueEvent3Handler(CareerHandlerBase):
    type: Literal['rogue_event_3'] = 'rogue_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction=(
                    'Defend yourself (roll Advocate 8+: success = cleared, fail = ejected + must take Prisoner next term) '
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
        projection.summary.connections.append(Enemy(source='A fellow rogue you betrayed'))
        projection.scheduled_effects.append(
            ScheduledEffect(
                trigger=EffectTrigger.ADVANCEMENT,
                source_event_id=event.id,
                effect={'type': EffectType.DM, 'amount': 2},
            )
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class RogueEvent6Refuse(ChoiceBase):
    kind: Literal['rogue_event_6_refuse'] = 'rogue_event_6_refuse'
    label: str = 'Refuse (gain Contact)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.connections.append(Contact(source='A fellow rogue you worked alongside'))
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class RogueEvent6Handler(CareerHandlerBase):
    type: Literal['rogue_event_6'] = 'rogue_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction='Backstab the fellow rogue (DM+2 to next advancement, gain Enemy) or refuse (gain a Contact instead)?',
                choices=[RogueEvent6Backstab(), RogueEvent6Refuse()],
            )
        )
        return pending_idx + 1


# ── event 9: feud with rival organisation ────────────────────────────────────


class PendingRogueEvent9SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['rogue_event_9_skill_roll'] = 'rogue_event_9_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.scheduled_effects.append(
                ScheduledEffect(
                    trigger=EffectTrigger.MUSTER_OUT_ADD,
                    source_event_id=event.id,
                    effect={'type': EffectType.ADD, 'value': 1},
                )
            )
            # no pending added — _apply_skill_roll auto-queues advancement
        else:
            projection.summary.problems.append(
                'Criminal feud: you are injured — roll on the Injury table and apply the result.'
            )


class RogueEvent9Handler(CareerHandlerBase):
    type: Literal['rogue_event_9'] = 'rogue_event_9'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingRogueEvent9SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll Stealth or Gun Combat 8+: success = extra Benefit roll; fail = injured',
                options=[Stealth(), GunCombat()],
            )
        )
        return pending_idx + 1


class RogueCareerData(CareerData):
    pass


CAREER_DATA = RogueCareerData(
    career=ROGUE,
    allows_assignment_change=True,
    qualification=CharCheck(characteristic=Chars.DEX, target=6),
    assignments=[
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
    ],
    skill_tables=CareerSkillTables(
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
    ),
    ranks={
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, bonus=RankBonus(skill=Stealth(), level=1)),
        2: RankEntry(rank=2),
        3: RankEntry(rank=3, bonus=RankBonus(skill=Streetwise(), level=1)),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5, bonus=RankBonus(skill=Recon(), level=1)),
        6: RankEntry(rank=6),
    },
    ranks_by_assignment={
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
    },
    muster_out=MusterOutData(
        rows={
            1: MusterOutRow(cash=0, benefit=SHIP_SHARE),
            2: MusterOutRow(cash=0, benefit=WEAPON),
            3: MusterOutRow(cash=10000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            4: MusterOutRow(cash=10000, benefit=SHIP_SHARE, count=1),
            5: MusterOutRow(cash=50000, benefit=ARMOR),
            6: MusterOutRow(cash=100000, benefit=CharacteristicIncrease(char=Chars.DEX, amount=1)),
            7: MusterOutRow(cash=100000, benefit=SHIP_SHARE, count=2),
        }
    ),
    mishaps={
        1: MishapEntry(
            text='Severely injured.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='Arrested. You must take the Prisoner career in your next term.',
            effects=[RogueMishap2Handler()],
        ),
        3: MishapEntry(
            text=(
                'Betrayed by a friend. One of your Contacts or Allies betrays you, ending your career. '
                'That Contact or Ally becomes a Rival or Enemy. If you have no Contacts or Allies, you still '
                'gain a Rival or Enemy. Roll 2D — on a 2, you must take the Prisoner career next term.'
            ),
            defer_ejection=True,
            effects=[RogueMishap3Handler()],
        ),
        4: MishapEntry(
            text='A job goes wrong, forcing you to flee off-planet.',
            effects=[SkillChoiceEffect(options=[Deception(), Pilot(), Athletics(), Gunner()], level=1)],
        ),
        5: MishapEntry(
            text='A police detective or rival criminal forces you to flee and vows to hunt you down.',
            effects=[GainEnemyEffect()],
        ),
        6: MishapEntry(
            text='Injured. Roll on the Injury table.',
            effects=[InjuryEffect(severity='from_table')],
        ),
    },
    events={
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='You are arrested and charged.',
            effects=[RogueEvent3Handler()],
        ),
        4: CareerEventEntry(
            text='You are involved in the planning of an impressive heist.',
            effects=[SkillChoiceEffect(options=[Electronics(), Mechanic()], level=1)],
        ),
        5: CareerEventEntry(
            text='One of your crimes pays off.',
            effects=[BenefitDmEffect(amount=2), GainEnemyEffect()],
        ),
        6: CareerEventEntry(
            text='You have the opportunity to backstab a fellow rogue for personal gain.',
            effects=[RogueEvent6Handler()],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='You spend months in the dangerous criminal underworld.',
            effects=[SkillChoiceEffect(options=[Streetwise(), Stealth(), Melee(), GunCombat()], level=1)],
        ),
        9: CareerEventEntry(
            text='You become involved in a feud with a rival criminal organisation.',
            effects=[RogueEvent9Handler()],
        ),
        10: CareerEventEntry(
            text='You are involved in a gambling ring. Gain Gambler 1.',
            effects=[GainSkillEffect(skill=Gambler(level=Level(value=1)))],
        ),
        11: CareerEventEntry(
            text='A crime lord considers you his protege.',
            effects=[SkillChoiceEffect(options=[Tactics(), AdvancementDmOption()], level=1)],
        ),
        12: CareerEventEntry(
            text='You commit a legendary crime. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    },
)
