from typing import Any, ClassVar, Literal

from ceres.character.domain.benefits import (
    SCOUT_SHIP,
    SHIP_SHARE,
    WEAPON,
    CharacteristicIncrease,
)
from ceres.character.domain.career.career_data import (
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
    GainConnectionsRolledEffect,
    GainEnemyEffect,
    GainRivalEffect,
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
from ceres.character.domain.career.career_events import (
    PendingMishap,
    PendingSkillChoice,
)
from ceres.character.domain.career.common import CommonMishap1Handler
from ceres.character.domain.career.common_pending import CareerSkillChoicePendingBase, CareerSkillRollPendingBase
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.homeworld.homeworld_events import (
    PendingHomeworldChangeOffered,
    PendingHomeworldChangeRequired,
)
from ceres.character.domain.skills import (
    Animals,
    Astrogation,
    Athletics,
    Deception,
    Diplomat,
    Electronics,
    Engineer,
    Explosives,
    Flyer,
    GunCombat,
    JackOfAllTrades,
    LanguageSkill,
    Level,
    Mechanic,
    Medic,
    Navigation,
    Persuade,
    Pilot,
    Recon,
    ScienceSkill,
    Seafarer,
    SpaceScience,
    Stealth,
    Streetwise,
    Survival,
    VaccSuit,
    skill_instances,
)

_AMBUSH_TARGETS: dict[str, int] = {'Pilot': 8, 'Persuade': 10}


# ── event 3: ambush ──────────────────────────────────────────────────────────


class PendingScoutEvent3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['scout_event_3_skill_roll'] = 'scout_event_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:
        skill_name = event.skill if isinstance(event.skill, str) else type(event.skill).name()
        target = _AMBUSH_TARGETS[skill_name]
        if event.modified_roll >= target:
            projection.grant_skill(
                Electronics(
                    comms=Level(value=1),
                    computers=Level(value=1),
                    remote_ops=Level(value=1),
                    sensors=Level(value=1),
                )
            )
        else:
            projection.summary.problems.append('Ship destroyed; may not re-enlist in Scouts at the end of this term.')
            projection.forced_leave = True


class ScoutEvent3Handler(CareerHandlerBase):
    type: Literal['scout_event_3'] = 'scout_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingScoutEvent3SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Pilot 8+ to escape or Persuade 10+ to bargain',
                options=[Pilot(), Persuade()],
            )
        )
        return pending_idx + 1


# ── event 8: alien intelligence ──────────────────────────────────────────────


class PendingScoutEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['scout_event_8_skill_roll'] = 'scout_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:
        if event.modified_roll >= 8:
            projection.add_connection(ConnectionKind.ALLY, origin='Alien intelligence contact')
            projection.pending_advancement_dm += 2
        else:
            projection.pending_inputs.append(
                PendingMishap(
                    pending_id=(event.id, 0),
                    instruction='Roll 1D Mishap (you are not ejected from this career)',
                    stay_in_career=True,
                )
            )


class ScoutEvent8Handler(CareerHandlerBase):
    type: Literal['scout_event_8'] = 'scout_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingScoutEvent8SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Electronics 8+ or Deception 8+',
                options=[Electronics(), Deception()],
            )
        )
        return pending_idx + 1


# ── event 9: disaster rescue ─────────────────────────────────────────────────


class PendingScoutEvent9SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['scout_event_9_skill_roll'] = 'scout_event_9_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:
        if event.modified_roll >= 8:
            projection.add_connection(ConnectionKind.CONTACT, origin='Disaster survivor')
            projection.pending_advancement_dm += 2
        else:
            projection.add_connection(ConnectionKind.ENEMY, origin='Disaster relief gone wrong')


class ScoutEvent9Handler(CareerHandlerBase):
    type: Literal['scout_event_9'] = 'scout_event_9'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingScoutEvent9SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Medic 8+ or Engineer 8+',
                options=[Medic(), Engineer()],
            )
        )
        return pending_idx + 1


# ── event 10: fringes of Charted Space ───────────────────────────────────────


class PendingScoutEvent10SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['scout_event_10_skill_roll'] = 'scout_event_10_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Any) -> None:
        if event.modified_roll >= 8:
            projection.add_connection(ConnectionKind.CONTACT, origin='Alien contact from the fringes of Charted Space')
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, 0),
                    instruction='Choose any skill +1 (alien contact)',
                    options=[],
                )
            )
        else:
            projection.pending_inputs.append(
                PendingMishap(
                    pending_id=(event.id, 0),
                    instruction='Roll 1D Mishap (you are not ejected from this career)',
                    stay_in_career=True,
                )
            )


class ScoutEvent10Handler(CareerHandlerBase):
    type: Literal['scout_event_10'] = 'scout_event_10'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingScoutEvent10SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Survival 8+ or Pilot 8+',
                options=[Survival(), Pilot()],
            )
        )
        return pending_idx + 1


# ── event 11: imperial courier ───────────────────────────────────────────────


class PendingScoutEvent11(CareerSkillChoicePendingBase):
    kind: Literal['scout_event_11'] = 'scout_event_11'


class ScoutEvent11Handler(CareerHandlerBase):
    type: Literal['scout_event_11'] = 'scout_event_11'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingScoutEvent11(
                pending_id=(event_id, pending_idx),
                instruction='Gain Diplomat 1, or DM+4 to your next advancement roll',
                options=[Diplomat(), AdvancementDmOption()],
                advancement_precreated=False,
            )
        )
        return pending_idx + 1


class Scout(CareerData):
    type: Literal['SCOUT_CAREER'] = 'SCOUT_CAREER'

    def start_new_term(
        self,
        projection: CharacterProjection,
        assignment: AssignmentData,
        event_id: int,
        is_continuation: bool = False,
    ) -> None:
        insert_at = len(projection.pending_inputs)
        super().start_new_term(projection, assignment, event_id, is_continuation)
        homeworld = projection.summary.homeworld
        used_sub_ids = {int(p.pending_id[1]) for p in projection.pending_inputs if p.pending_id[0] == event_id}
        homeworld_idx = max(used_sub_ids, default=-1) + 1
        if 'S' in homeworld.bases or 'W' in homeworld.bases:
            homeworld_pending = PendingHomeworldChangeOffered(
                pending_id=(event_id, homeworld_idx),
                instruction='You may relocate to a Scout base world. Select a new homeworld (optional).',
                reason='Scout career: you may choose a world with an Imperial Scout Base (S) '
                'or Way Station (W) as your homeworld.',
                source_kind='career_entry',
                source_career='Scout',
                target_constraints='world_with_scout_base',
            )
        else:
            homeworld_pending = PendingHomeworldChangeRequired(
                pending_id=(event_id, homeworld_idx),
                instruction='Your career requires a Scout base world. Select your new homeworld.',
                reason='Scout career: your homeworld must have an Imperial Scout Base (S) or Way Station (W).',
                source_kind='career_entry',
                source_career='Scout',
                target_constraints='world_with_scout_base',
            )
        projection.pending_inputs.insert(insert_at, homeworld_pending)

    name: ClassVar[str] = 'Scout'
    description: ClassVar[str] = (
        'Members of the exploratory service. Scouts explore new areas, map and survey known or newly discovered areas '
        'and maintain communication ships which carry information and messages between the worlds of the galaxy.'
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=5)
    allows_assignment_change: ClassVar[bool] = True
    draft_assignments: ClassVar[list[str]] = ['Courier', 'Surveyor', 'Explorer']

    assignments: ClassVar[list[AssignmentData]] = [
        AssignmentData(
            name='Courier',
            description='You are responsible for shuttling messages and high value packages around the galaxy.',
            survival=CharCheck(characteristic=Chars.END, target=5),
            advancement=CharCheck(characteristic=Chars.EDU, target=9),
        ),
        AssignmentData(
            name='Surveyor',
            description='You visit border worlds and assess their worth.',
            survival=CharCheck(characteristic=Chars.END, target=6),
            advancement=CharCheck(characteristic=Chars.INT, target=8),
        ),
        AssignmentData(
            name='Explorer',
            description='You go wherever the map is blank, exploring unknown worlds and uncharted space.',
            survival=CharCheck(characteristic=Chars.END, target=7),
            advancement=CharCheck(characteristic=Chars.EDU, target=7),
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
                JackOfAllTrades(),
            ]
        ),
        service_skills=SkillTable(
            [
                [
                    Pilot(small_craft=Level(value=1)),
                    Pilot(spacecraft=Level(value=1)),
                ],
                Survival(),
                Mechanic(),
                Astrogation(),
                VaccSuit(),
                GunCombat(),
            ]
        ),
        advanced_education=SkillTable(
            [
                Medic(),
                skill_instances(LanguageSkill),
                Seafarer(),
                Explosives(),
                skill_instances(ScienceSkill),
                JackOfAllTrades(),
            ],
            min_edu=8,
        ),
        assignment1=SkillTable(
            [  # Courier
                Electronics(),
                Flyer(),
                Pilot(),
                Engineer(),
                Athletics(),
                Astrogation(),
            ]
        ),
        assignment2=SkillTable(
            [  # Surveyor
                Electronics(),
                Persuade(),
                Pilot(),
                Navigation(),
                Diplomat(),
                Streetwise(),
            ]
        ),
        assignment3=SkillTable(
            [  # Explorer
                Electronics(),
                Pilot(),
                Engineer(),
                skill_instances(ScienceSkill),
                Stealth(),
                Recon(),
            ]
        ),
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, title='Scout', bonus=RankBonus(skill=VaccSuit(), level=1)),
        2: RankEntry(rank=2),
        3: RankEntry(rank=3, title='Senior Scout', bonus=RankBonus(skill=Pilot(), level=1)),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5),
        6: RankEntry(rank=6),
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=20000, benefit=SHIP_SHARE),
            2: MusterOutRow(cash=20000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            3: MusterOutRow(cash=30000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            4: MusterOutRow(cash=30000, benefit=WEAPON),
            5: MusterOutRow(cash=50000, benefit=WEAPON),
            6: MusterOutRow(cash=50000, benefit=SCOUT_SHIP),
            7: MusterOutRow(cash=50000, benefit=SCOUT_SHIP),
        }
    )

    mishaps: ClassVar[dict[int, MishapEntry]] = {
        1: MishapEntry(
            text='Severely injured.',
            effects=[CommonMishap1Handler()],
            defer_ejection=True,
        ),
        2: MishapEntry(
            text='Psychologically damaged by your time in the scouts. Reduce your INT or SOC by 1.',
            effects=[DecreaseCharacteristicChoiceEffect(options=[Chars.INT, Chars.SOC], amount=1)],
        ),
        3: MishapEntry(
            text=(
                'Your ship is damaged and you have to hitch-hike your way back across the stars. '
                'Gain 1D Contacts and D3 Enemies.'
            ),
            effects=[
                GainConnectionsRolledEffect(connection_type=ConnectionKind.CONTACT, dice='1d6'),
                GainConnectionsRolledEffect(connection_type=ConnectionKind.ENEMY, dice='d3'),
            ],
        ),
        4: MishapEntry(
            text=(
                'You inadvertently cause a conflict between the Imperium and a minor world or species. '
                'Gain a Rival and Diplomat 1.'
            ),
            effects=[
                GainSkillEffect(skill=Diplomat(level=Level(value=1))),
                GainRivalEffect(),
            ],
        ),
        5: MishapEntry(
            text='You have no idea what happened to you — they found '
            'your ship drifting on the fringes of friendly space.',
            effects=[],
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
            text=(
                'Your ship is ambushed by enemy vessels. Either run and roll Pilot 8+ to escape, or treat with them '
                'and roll Persuade 10+ to bargain with them. If you fail the check, then your ship is destroyed and '
                'you may not re-enlist in the Scouts at the end of this term. If you succeed, you survive and gain '
                'Electronics (sensors) 1. Either way, gain an Enemy.'
            ),
            effects=[ScoutEvent3Handler(), GainEnemyEffect()],
        ),
        4: CareerEventEntry(
            text='You survey an alien world.',
            effects=[SkillChoiceEffect(options=[Animals(), Survival(), Recon(), SpaceScience()], level=1)],
        ),
        5: CareerEventEntry(
            text='You perform an exemplary service for the scouts.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        6: CareerEventEntry(
            text=(
                'You spend several years jumping from world to world in your scout ship. Gain one of Astrogation 1, '
                'Electronics 1, Navigation 1, Pilot (small craft) 1 or Mechanic 1.'
            ),
            effects=[
                SkillChoiceEffect(
                    options=[
                        Astrogation(),
                        Electronics(),
                        Navigation(),
                        Pilot(small_craft=Level(value=1)),
                        Mechanic(),
                    ],
                    level=1,
                )
            ],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='When dealing with an alien species, you have an opportunity to gather extra intelligence.',
            effects=[ScoutEvent8Handler()],
        ),
        9: CareerEventEntry(
            text='Your scout ship is one of the first on the scene to rescue the survivors of a disaster.',
            effects=[ScoutEvent9Handler()],
        ),
        10: CareerEventEntry(
            text='You spend a great deal of time on the fringes of Charted Space.',
            effects=[ScoutEvent10Handler()],
        ),
        11: CareerEventEntry(
            text='You serve as the courier for an important message from the Imperium.',
            effects=[ScoutEvent11Handler()],
        ),
        12: CareerEventEntry(
            text='You discover a world, item or information of worth to the Imperium. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    }


SCOUT = Scout()
