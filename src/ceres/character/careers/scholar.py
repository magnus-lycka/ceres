from typing import ClassVar, Literal, cast

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
from ceres.character.careers.common_pending import (
    CareerSkillChoicePendingBase,
    CareerSkillRollPendingBase,
)
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingChoices,
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
    ChoiceBase,
    Enemy,
)

_SCIENCES = skill_instances(ScienceSkill)


# ── mishap 3: planetary interference ─────────────────────────────────────────


class PendingScholarScienceChoice(CareerSkillChoicePendingBase):
    kind: Literal['scholar_science_choice'] = 'scholar_science_choice'


def _append_scholar_science_choice(projection: CharacterProjection, event_id: int, idx: int = 0) -> None:
    projection.pending_inputs.append(
        PendingScholarScienceChoice(
            pending_id=(event_id, idx),
            instruction='Increase Science by one level: choose which broad science',
            options=cast(list[AnySkill | AdvancementDmOption], skill_instances(ScienceSkill)),
            advancement_precreated=True,
        )
    )


class ScholarMishap3Openly(ChoiceBase):
    kind: Literal['scholar_mishap_3_openly'] = 'scholar_mishap_3_openly'
    label: str = 'Continue openly (Science +1, gain Enemy)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.summary.connections.append(Enemy(source='Government officials who interfered with your research'))
        _append_scholar_science_choice(projection, event.id)


class ScholarMishap3Secretly(ChoiceBase):
    kind: Literal['scholar_mishap_3_secretly'] = 'scholar_mishap_3_secretly'
    label: str = 'Continue secretly (Science +1, SOC −2)'

    def handle(self, projection: CharacterProjection, event) -> None:
        soc = projection.summary.characteristics.get(Chars.SOC, 0)
        projection.summary.characteristics[Chars.SOC] = max(0, soc - 2)
        _append_scholar_science_choice(projection, event.id)


class ScholarMishap3Handler(CareerHandlerBase):
    type: Literal['scholar_mishap_3'] = 'scholar_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Continue openly (Science +1, Enemy) or secretly (Science +1, SOC -2)?',
                choices=[ScholarMishap3Openly(), ScholarMishap3Secretly()],
            )
        )
        return pending_idx + 1


# ── mishap 5: work sabotaged ──────────────────────────────────────────────────


class ScholarMishap5GiveUp(ChoiceBase):
    kind: Literal['scholar_mishap_5_give_up'] = 'scholar_mishap_5_give_up'
    label: str = 'Give up (leave career)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.events import PendingAdvancement, PendingAgingRoll

        career = projection.get_current_career()
        projection.pending_inputs = [p for p in projection.pending_inputs if not isinstance(p, PendingAdvancement)]
        projection.summary.age += 4
        if projection.summary.age >= 34:
            projection.muster_out_career = career
            projection.clear_current_career()
            projection.pending_inputs.append(
                PendingAgingRoll(pending_id=(event.id, 0), instruction='Roll 2D on Aging table')
            )
        else:
            muster_out_setup(projection, career, event.id, 0, lose_current_term=True)


class ScholarMishap5StartAgain(ChoiceBase):
    kind: Literal['scholar_mishap_5_start_again'] = 'scholar_mishap_5_start_again'
    label: str = 'Start again (stay, lose benefit rolls)'

    def handle(self, projection: CharacterProjection, event) -> None:
        pass  # advancement already queued by _apply_mishap (stay_in_career=True)


class ScholarMishap5Handler(CareerHandlerBase):
    type: Literal['scholar_mishap_5'] = 'scholar_mishap_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Give up (leave career) or start again (stay, lose benefit rolls)?',
                choices=[ScholarMishap5GiveUp(), ScholarMishap5StartAgain()],
            )
        )
        return pending_idx + 1


# ── event 3: research against conscience ─────────────────────────────────────


class PendingScholarScienceChoicePreCreated(CareerSkillChoicePendingBase):
    kind: Literal['scholar_science_choice_precreated'] = 'scholar_science_choice_precreated'


class ScholarEvent3Accept(ChoiceBase):
    kind: Literal['scholar_event_3_accept'] = 'scholar_event_3_accept'
    label: str = 'Accept (2 Science specialties + D3 Enemies + extra Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.events import PendingConnectionsRoll, PendingMusterOut, _advancement_pending

        projection.pending_inputs.append(
            PendingConnectionsRoll(
                pending_id=(event.id, 0),
                instruction='Roll D3 for number of Enemies gained',
                options=['1', '2', '3'],
            )
        )
        for i, label in enumerate(['first', 'second'], start=1):
            projection.pending_inputs.append(
                PendingScholarScienceChoicePreCreated(
                    pending_id=(event.id, i),
                    instruction=f'Choose {label} Science specialty to increase by one level',
                    options=cast(list[AnySkill | AdvancementDmOption], skill_instances(ScienceSkill)),
                    advancement_precreated=True,
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
                pending_id=(event.id, 4),
                instruction='Extra Benefit roll (accepted research against conscience)',
                options=['cash', 'benefits'],
            )
        )


class ScholarEvent3Decline(ChoiceBase):
    kind: Literal['scholar_event_3_decline'] = 'scholar_event_3_decline'
    label: str = 'Decline'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.events import _advancement_pending

        if projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id)
            )


class ScholarEvent3Handler(CareerHandlerBase):
    type: Literal['scholar_event_3'] = 'scholar_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Accept (2 Science specialties + D3 Enemies + extra Benefit roll) or Decline?',
                choices=[ScholarEvent3Accept(), ScholarEvent3Decline()],
            )
        )
        return pending_idx + 1


# ── event 6: advanced training ───────────────────────────────────────────────


class PendingScholarEvent6SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['scholar_event_6_skill_roll'] = 'scholar_event_6_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, 0),
                    instruction='Choose any skill to gain at level 1',
                    options=[],
                )
            )
        # failure: _apply_skill_roll creates advancement pending


class ScholarEvent6Handler(CareerHandlerBase):
    type: Literal['scholar_event_6'] = 'scholar_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingScholarEvent6SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll EDU 8+ to gain any skill of your choice at level 1',
                options=[Chars.EDU],
            )
        )
        return pending_idx + 1


# ── event 8: opportunity to cheat ────────────────────────────────────────────


class ScholarEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['scholar_event_8_skill_roll'] = 'scholar_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.summary.connections.append(Enemy(source='A colleague who knows you cheated your way to results'))
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, 0),
                    instruction='Cheat succeeded: choose any skill to gain +1',
                    options=[],
                )
            )
        else:
            projection.summary.connections.append(Enemy(source='Someone who caught you falsifying research'))
        # _apply_skill_roll creates advancement if no new pending (failure), or after skill_choice (success)


class ScholarEvent8Accept(ChoiceBase):
    kind: Literal['scholar_event_8_accept'] = 'scholar_event_8_accept'
    label: str = 'Accept (roll Deception/Admin 8+)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            ScholarEvent8SkillRoll(
                pending_id=(event.id, 0),
                instruction='Roll Deception 8+ or Admin 8+ to cheat successfully',
                options=[Deception(), Admin()],
            )
        )


class ScholarEvent8Refuse(ChoiceBase):
    kind: Literal['scholar_event_8_refuse'] = 'scholar_event_8_refuse'
    label: str = 'Refuse'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.events import _advancement_pending

        if projection.summary.current_career is not None:
            career = projection.get_current_career()
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id)
            )


class ScholarEvent8Handler(CareerHandlerBase):
    type: Literal['scholar_event_8'] = 'scholar_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Refuse (nothing) or Accept (roll Deception/Admin 8+)?',
                choices=[ScholarEvent8Accept(), ScholarEvent8Refuse()],
            )
        )
        return pending_idx + 1


# ── event 11: brilliant mentor ────────────────────────────────────────────────


class PendingScholarEvent11(CareerSkillChoicePendingBase):
    kind: Literal['scholar_event_11'] = 'scholar_event_11'


class ScholarEvent11Handler(CareerHandlerBase):
    type: Literal['scholar_event_11'] = 'scholar_event_11'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingScholarEvent11(
                pending_id=(event_id, pending_idx),
                instruction='Increase Science by one level (choose which), or DM+4 to your next advancement roll',
                options=[*_SCIENCES, AdvancementDmOption()],
                advancement_precreated=False,
            )
        )
        return pending_idx + 1


class Scholar(CareerData):
    type: Literal['SCHOLAR_CAREER'] = 'SCHOLAR_CAREER'

    name: ClassVar[str] = 'Scholar'
    description: ClassVar[str] = (
        'Individuals trained in technological or research sciences who conduct scientific investigations into materials, situations and phenomena, or who practise medicine.'
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=6)
    allows_assignment_change: ClassVar[bool] = True

    assignments: ClassVar[list[AssignmentData]] = [
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
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
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
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, bonus=RankBonus(choices=_SCIENCES, level=1)),
        2: RankEntry(rank=2, bonus=RankBonus(skill=Electronics(), level=1)),
        3: RankEntry(rank=3, bonus=RankBonus(skill=Investigate(), level=1)),
        4: RankEntry(rank=4),
        5: RankEntry(rank=5, bonus=RankBonus(choices=_SCIENCES, level=2)),
        6: RankEntry(rank=6),
    }

    ranks_by_assignment: ClassVar[dict[int, dict[int, RankEntry]]] = {
        3: {  # Physician
            0: RankEntry(rank=0),
            1: RankEntry(rank=1, bonus=RankBonus(skill=Medic(), level=1)),
            2: RankEntry(rank=2),
            3: RankEntry(rank=3, bonus=RankBonus(choices=_SCIENCES, level=1)),
            4: RankEntry(rank=4),
            5: RankEntry(rank=5, bonus=RankBonus(choices=_SCIENCES, level=2)),
            6: RankEntry(rank=6),
        },
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=5000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            2: MusterOutRow(cash=10000, benefit=CharacteristicIncrease(char=Chars.EDU, amount=1)),
            3: MusterOutRow(cash=20000, benefit=SHIP_SHARE, count=2),
            4: MusterOutRow(cash=30000, benefit=CharacteristicIncrease(char=Chars.SOC, amount=1)),
            5: MusterOutRow(cash=40000, benefit=SCIENTIFIC_EQUIPMENT),
            6: MusterOutRow(cash=60000, benefit=LAB_SHIP),
            7: MusterOutRow(cash=100000, benefit=LAB_SHIP),
        }
    )

    mishaps: ClassVar[dict[int, MishapEntry]] = {
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
    }

    events: ClassVar[dict[int, CareerEventEntry]] = {
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
    }


SCHOLAR = Scholar()
