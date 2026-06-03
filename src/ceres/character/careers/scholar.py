from typing import Literal, cast

from ceres.character.benefits import (
    LAB_SHIP,
    SCIENTIFIC_EQUIPMENT,
    SHIP_SHARE,
    CharacteristicIncrease,
)
from ceres.character.careers.career_data import (
    AdvancementDmEffect,
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
    GainAllyEffect,
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
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
    PendingSkillChoice,
    SkillRollEvent,
    muster_out_setup,
)
from ceres.character.skills import (
    Admin,
    Advocate,
    AnySkill,
    ArtSkill,
    Athletics,
    Deception,
    Diplomat,
    Drive,
    Electronics,
    Engineer,
    Flyer,
    Investigate,
    LanguageSkill,
    Medic,
    Navigation,
    Persuade,
    ScienceSkill,
    Survival,
    VaccSuit,
    skill_instances,
)
from ceres.character.state import (
    CharacterProjection,
    Enemy,
)

_SCIENCES = skill_instances(ScienceSkill)

SCHOLAR = Career(
    name='Scholar',
    description=(
        'Individuals trained in technological or research sciences who conduct scientific '
        'investigations into materials, situations and phenomena, or who practise medicine.'
    ),
)


# ── mishap 3: planetary interference ─────────────────────────────────────────


class ScholarMishap3Handler(CareerHandlerBase):
    type: Literal['scholar_mishap_3'] = 'scholar_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingCareerMishap(
                id=f'{event_id}.{pending_idx}',
                career='Scholar',
                roll=3,
                instruction='Continue openly (Science +1, Enemy) or secretly (Science +1, SOC -2)?',
                options=['openly', 'secretly'],
            )
        )
        return pending_idx + 1

    @staticmethod
    def on_choice(projection: CharacterProjection, event) -> None:
        if event.choice == 'openly':
            projection.summary.connections.append(Enemy(source='Planetary government interference'))
        else:
            soc = projection.summary.characteristics.get(Chars.SOC, 0)
            projection.summary.characteristics[Chars.SOC] = max(0, soc - 2)
        projection.pending_inputs.append(
            PendingCareerSkillChoice(
                id=f'{event.id}.0',
                career='Scholar',
                roll=3,
                mishap=True,
                advancement_precreated=True,
                instruction='Increase Science by one level: choose which broad science',
                options=cast(list[AnySkill | AdvancementDmOption], skill_instances(ScienceSkill)),
            )
        )
        # advancement was already created by _apply_mishap (stay_in_career=True)


# ── mishap 5: work sabotaged ──────────────────────────────────────────────────


class ScholarMishap5Handler(CareerHandlerBase):
    type: Literal['scholar_mishap_5'] = 'scholar_mishap_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingCareerMishap(
                id=f'{event_id}.{pending_idx}',
                career='Scholar',
                roll=5,
                instruction='Give up (leave career) or start again (stay, lose benefit rolls)?',
                options=['give_up', 'start_again'],
            )
        )
        return pending_idx + 1

    @staticmethod
    def on_choice(projection: CharacterProjection, event) -> None:
        from ceres.character.events import PendingAdvancement, PendingAgingRoll

        if event.choice == 'give_up':
            career = projection.get_current_career()
            projection.pending_inputs = [p for p in projection.pending_inputs if not isinstance(p, PendingAdvancement)]
            projection.summary.age += 4
            if projection.summary.age >= 34:
                projection.muster_out_career = career.career
                projection.clear_current_career()
                projection.pending_inputs.append(
                    PendingAgingRoll(id=f'{event.id}.0', instruction='Roll 2D on Aging table')
                )
            else:
                muster_out_setup(projection, career, event.id, 0, lose_current_term=True)
        # 'start_again': advancement is already there from _apply_mishap, career stays


# ── event 3: research against conscience ─────────────────────────────────────


class ScholarEvent3Handler(CareerHandlerBase):
    type: Literal['scholar_event_3'] = 'scholar_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingCareerEvent(
                id=f'{event_id}.{pending_idx}',
                career='Scholar',
                roll=3,
                instruction='Accept (2 Science specialties + D3 Enemies + extra Benefit roll) or Decline?',
                options=['accept', 'decline'],
            )
        )
        return pending_idx + 1

    @staticmethod
    def on_choice(projection: CharacterProjection, event) -> None:
        from ceres.character.events import PendingConnectionsRoll, PendingMusterOut, _advancement_pending

        if event.choice == 'accept':
            projection.pending_inputs.append(
                PendingConnectionsRoll(
                    id=f'{event.id}.0',
                    instruction='Roll D3 for number of Enemies gained',
                    options=['1', '2', '3'],
                )
            )
            for i, label in enumerate(['first', 'second'], start=1):
                projection.pending_inputs.append(
                    PendingCareerSkillChoice(
                        id=f'{event.id}.{i}',
                        career='Scholar',
                        roll=3,
                        mishap=False,
                        advancement_precreated=True,
                        instruction=f'Choose {label} Science specialty to increase by one level',
                        options=cast(list[AnySkill | AdvancementDmOption], skill_instances(ScienceSkill)),
                    )
                )
            if projection.summary.current_career is not None:
                career = projection.get_current_career()
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id, 3)
                )
            projection.muster_out_career = projection.summary.current_career
            projection.pending_inputs.append(
                PendingMusterOut(
                    id=f'{event.id}.4',
                    instruction='Extra Benefit roll (accepted research against conscience)',
                    options=['cash', 'benefits'],
                )
            )
        elif projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id)
            )


# ── event 6: advanced training ───────────────────────────────────────────────


class ScholarEvent6Handler(CareerHandlerBase):
    type: Literal['scholar_event_6'] = 'scholar_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingCareerSkillRoll(
                id=f'{event_id}.{pending_idx}',
                career='Scholar',
                roll=6,
                context='scholar_event_6',
                instruction='Roll EDU 8+ to gain any skill of your choice at level 1',
                options=[Chars.EDU],
            )
        )
        return pending_idx + 1

    @staticmethod
    def resolve(projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.0',
                    instruction='Choose any skill to gain at level 1',
                    options=[],
                )
            )
        # failure: _apply_skill_roll creates advancement pending


# ── event 8: opportunity to cheat ────────────────────────────────────────────


class ScholarEvent8Handler(CareerHandlerBase):
    type: Literal['scholar_event_8'] = 'scholar_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingCareerEvent(
                id=f'{event_id}.{pending_idx}',
                career='Scholar',
                roll=8,
                instruction='Refuse (nothing) or Accept (roll Deception/Admin 8+)?',
                options=['accept', 'refuse'],
            )
        )
        return pending_idx + 1

    @staticmethod
    def on_choice(projection: CharacterProjection, event) -> None:
        from ceres.character.events import _advancement_pending

        if event.choice == 'refuse':
            if projection.summary.current_career is not None:
                career = projection.get_current_career()
                projection.pending_inputs.append(
                    _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id)
                )
        else:
            projection.pending_inputs.append(
                PendingCareerSkillRoll(
                    id=f'{event.id}.0',
                    career='Scholar',
                    roll=8,
                    context='scholar_event_8_roll',
                    instruction='Roll Deception 8+ or Admin 8+ to cheat successfully',
                    options=[Deception(), Admin()],
                )
            )


class ScholarEvent8RollHandler(CareerHandlerBase):
    type: Literal['scholar_event_8_roll'] = 'scholar_event_8_roll'

    @staticmethod
    def resolve(projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.summary.connections.append(Enemy(source='Cheating in the field'))
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.0',
                    instruction='Cheat succeeded: choose any skill to gain +1',
                    options=[],
                )
            )
        else:
            projection.summary.connections.append(Enemy(source='Cheating discovered'))
        # _apply_skill_roll creates advancement if no new pending (failure), or after skill_choice (success)


# ── event 11: brilliant mentor ────────────────────────────────────────────────


class ScholarEvent11Handler(CareerHandlerBase):
    type: Literal['scholar_event_11'] = 'scholar_event_11'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingCareerSkillChoice(
                id=f'{event_id}.{pending_idx}',
                career='Scholar',
                roll=11,
                advancement_precreated=False,
                instruction='Increase Science by one level (choose which), or DM+4 to your next advancement roll',
                options=[*_SCIENCES, AdvancementDmOption()],
            )
        )
        return pending_idx + 1


class ScholarCareerData(CareerData):
    pass


CAREER_DATA = ScholarCareerData(
    career=SCHOLAR,
    allows_assignment_change=True,
    qualification=CharCheck(characteristic=Chars.INT, target=6),
    assignments=[
        AssignmentData(
            name='Field Researcher',
            description='You are an explorer or field researcher, equally at home in the laboratory or wilderness.',
            survival=CharCheck(characteristic=Chars.END, target=6),
            advancement=CharCheck(characteristic=Chars.INT, target=6),
        ),
        AssignmentData(
            name='Scientist',
            description=(
                'You are a researcher in some corporation or research institution or a mad scientist in an '
                'orbiting laboratory.'
            ),
            survival=CharCheck(characteristic=Chars.EDU, target=4),
            advancement=CharCheck(characteristic=Chars.INT, target=8),
        ),
        AssignmentData(
            name='Physician',
            description='You are a doctor, healer or medical researcher.',
            survival=CharCheck(characteristic=Chars.EDU, target=4),
            advancement=CharCheck(characteristic=Chars.EDU, target=8),
        ),
    ],
    skill_tables=CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.INT,
                Chars.EDU,
                Chars.SOC,
                Chars.DEX,
                Chars.END,
                skill_instances(LanguageSkill),
            ]
        ),
        service_skills=SkillTable(
            [
                [Drive(), Flyer()],
                Electronics(),
                Diplomat(),
                Medic(),
                Investigate(),
                skill_instances(ScienceSkill),
            ]
        ),
        advanced_education=SkillTable(
            [
                skill_instances(ArtSkill),
                Advocate(),
                Electronics(),
                skill_instances(LanguageSkill),
                Engineer(),
                skill_instances(ScienceSkill),
            ],
            min_edu=10,
        ),
        assignment1=SkillTable(
            [  # Field Researcher
                Electronics(),
                VaccSuit(),
                Navigation(),
                Survival(),
                Investigate(),
                skill_instances(ScienceSkill),
            ]
        ),
        assignment2=SkillTable(
            [  # Scientist
                Admin(),
                Engineer(),
                skill_instances(ScienceSkill),
                skill_instances(ScienceSkill),
                Electronics(),
                skill_instances(ScienceSkill),
            ]
        ),
        assignment3=SkillTable(
            [  # Physician
                Medic(),
                Electronics(),
                Investigate(),
                Medic(),
                Persuade(),
                skill_instances(ScienceSkill),
            ]
        ),
    ),
    ranks={
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, bonus=RankBonus(choices=_SCIENCES, level=1)),
        2: RankEntry(rank=2, bonus=RankBonus(skill=Electronics(), level=1)),
        3: RankEntry(rank=3, bonus=RankBonus(skill=Investigate(), level=1)),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5, bonus=RankBonus(choices=_SCIENCES, level=2)),
        6: RankEntry(rank=6),
    },
    ranks_by_assignment={
        3: {  # Physician
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(skill=Medic(), level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, bonus=RankBonus(choices=_SCIENCES, level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5, bonus=RankBonus(choices=_SCIENCES, level=2)),
            6: RankEntry(rank=6),
        },
    },
    muster_out=MusterOutData(
        rows={
            1: MusterOutRow(cash=5000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            2: MusterOutRow(cash=10000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            3: MusterOutRow(cash=20000, benefit=SHIP_SHARE, count=2),
            4: MusterOutRow(cash=30000, benefit=CharacteristicIncrease(char=Chars.SOC, amount=1)),
            5: MusterOutRow(cash=40000, benefit=SCIENTIFIC_EQUIPMENT),
            6: MusterOutRow(cash=60000, benefit=LAB_SHIP),
            7: MusterOutRow(cash=100000, benefit=LAB_SHIP),
        }
    ),
    mishaps={
        1: MishapEntry(
            text='Severely injured.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='A disaster leaves several injured and others blame you, forcing you to leave your career. Gain a Rival.',
            effects=[InjuryEffect(severity='from_table'), GainRivalEffect()],
        ),
        3: MishapEntry(
            text='The planetary government interferes with your research for political or religious reasons.',
            stay_in_career=True,
            effects=[ScholarMishap3Handler()],
        ),
        4: MishapEntry(
            text='An expedition or voyage goes wrong, leaving you stranded in the wilderness.',
            effects=[SkillChoiceEffect(options=[Survival(), Athletics()], level=1)],
        ),
        5: MishapEntry(
            text='Your work is sabotaged by unknown parties.',
            stay_in_career=True,
            effects=[ScholarMishap5Handler()],
        ),
        6: MishapEntry(
            text=(
                'A rival researcher blackens your name or steals your research. Gain a Rival but you do not have to '
                'leave this career.'
            ),
            stay_in_career=True,
            effects=[GainRivalEffect()],
        ),
    },
    events={
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='You are called upon to perform research that goes against your conscience.',
            effects=[ScholarEvent3Handler()],
        ),
        4: CareerEventEntry(
            text='You are assigned to work on a secret project for a patron or organisation.',
            effects=[
                SkillChoiceEffect(
                    options=[Medic(), *skill_instances(ScienceSkill), Engineer(), Electronics(), Investigate()],
                    level=1,
                )
            ],
        ),
        5: CareerEventEntry(
            text='You win a prestigious prize for your work.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        6: CareerEventEntry(
            text='You are given advanced training in a specialist field.',
            effects=[ScholarEvent6Handler()],
        ),
        7: CareerEventEntry(
            text='Life Event.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text='You have the opportunity to cheat in some fashion.',
            effects=[ScholarEvent8Handler()],
        ),
        9: CareerEventEntry(
            text='You make a breakthrough in your field.',
            effects=[AdvancementDmEffect(amount=2)],
        ),
        10: CareerEventEntry(
            text='You become entangled in a bureaucratic or legal morass.',
            effects=[SkillChoiceEffect(options=[Admin(), Advocate(), Persuade(), Diplomat()], level=1)],
        ),
        11: CareerEventEntry(
            text='You work for an eccentric but brilliant mentor, who becomes an Ally.',
            effects=[GainAllyEffect(), ScholarEvent11Handler()],
        ),
        12: CareerEventEntry(
            text='Your work leads to a considerable breakthrough. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    },
)
