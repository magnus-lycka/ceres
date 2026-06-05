from typing import ClassVar, Literal, cast

from ceres.character.benefits import (
    ALLY,
    BLADE,
    CONTACT,
    DECEPTION_ITEM,
    MELEE_ITEM,
    PERSUADE_ITEM,
    RECON_ITEM,
    STEALTH_ITEM,
    STREETWISE_ITEM,
    CharacteristicIncrease,
    ChoiceBenefit,
    CombinedBenefit,
)
from ceres.character.careers.career_data import (
    AssignmentData,
    Career,
    CareerData,
    CareerEventEntry,
    CareerHandlerBase,
    CareerSkillTables,
    CharCheck,
    DecreaseCharacteristicEffect,
    GainEnemyEffect,
    InjuryEffect,
    MishapEntry,
    MusterOutData,
    MusterOutRow,
    ParoleThresholdChangeEffect,
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
    PendingDoubleInjuryRoll,
    PendingInjuryTable,
    PendingParoleRoll,
    PendingSkillChoice,
    SkillRollEvent,
    career_progress_pending,
    muster_out_setup,
)
from ceres.character.skills import (
    Admin,
    Advocate,
    Athletics,
    Broker,
    Deception,
    Electronics,
    Gambler,
    Investigate,
    JackOfAllTrades,
    Mechanic,
    Melee,
    Persuade,
    ProfessionSkill,
    Stealth,
    Steward,
    Streetwise,
    Survival,
    skill_instances,
)
from ceres.character.state import (
    Ally,
    CharacterProjection,
    ChoiceBase,
    Enemy,
)

# ── mishap 3: prison gang ─────────────────────────────────────────────────────


class PrisonerMishap3Submit(ChoiceBase):
    kind: Literal['prisoner_mishap_3_submit'] = 'prisoner_mishap_3_submit'
    label: str = 'Submit (lose Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.events import _advancement_pending

        career = projection.get_current_career()
        projection.summary.problems.append(
            'Prison gang (Prisoner mishap 3): submitted — lose your Benefit roll for this term.'
        )
        projection.pending_inputs.append(
            _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id)
        )


class PrisonerMishap3Fight(ChoiceBase):
    kind: Literal['prisoner_mishap_3_fight'] = 'prisoner_mishap_3_fight'
    label: str = 'Fight back (roll Melee 8+: success = Enemy + PT+1; fail = double injury)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            PendingPrisonerMishap3FightSkillRoll(
                id=f'{event.id}.0',
                instruction='Roll Melee 8+: success = gain Enemy + PT+1; fail = roll twice on Injury table',
                options=[Melee()],
            )
        )


class PendingPrisonerMishap3FightSkillRoll(CareerSkillRollPendingBase):
    kind: Literal['prisoner_mishap_3_fight_skill_roll'] = 'prisoner_mishap_3_fight_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.events import _advancement_pending

        career = projection.get_current_career()
        if event.modified_roll >= 8:
            projection.summary.connections.append(Enemy(source='The prison gang leader you stood up to'))
            projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 1)
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id)
            )
        else:
            projection.pending_inputs.append(
                PendingDoubleInjuryRoll(
                    id=f'{event.id}.0',
                    instruction='Gang fight: roll twice on the Injury table, apply lower result',
                    options=['1', '2', '3', '4', '5', '6'],
                )
            )
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id, 1)
            )


class PrisonerMishap3Handler(CareerHandlerBase):
    type: Literal['prisoner_mishap_3'] = 'prisoner_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction='Prison gang attack: fight back (roll Melee 8+) or submit (lose Benefit roll)?',
                choices=[PrisonerMishap3Fight(), PrisonerMishap3Submit()],
            )
        )
        return pending_idx + 1


# ── event 3: escape opportunity ───────────────────────────────────────────────


class PrisonerEvent3Stay(ChoiceBase):
    kind: Literal['prisoner_event_3_stay'] = 'prisoner_event_3_stay'
    label: str = 'Stay (no action)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PrisonerEvent3Attempt(ChoiceBase):
    kind: Literal['prisoner_event_3_attempt'] = 'prisoner_event_3_attempt'
    label: str = 'Attempt escape (Stealth or Deception 10+)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            PendingPrisonerEvent3EscapeSkillRoll(
                id=f'{event.id}.0',
                instruction='Roll Stealth or Deception 10+: success = escape (freed); fail = PT+2',
                options=[Stealth(), Deception()],
            )
        )


class PendingPrisonerEvent3EscapeSkillRoll(CareerSkillRollPendingBase):
    kind: Literal['prisoner_event_3_escape_skill_roll'] = 'prisoner_event_3_escape_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        career = projection.get_current_career()
        if event.modified_roll >= 10:
            projection.summary.narrative.append('Prisoner event 3: escaped from prison — career ends.')
            muster_out_setup(projection, career, event.id, 0, lose_current_term=False)
        else:
            projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 2)
            projection.summary.narrative.append('Prisoner event 3: escape failed — Parole Threshold +2.')
            # _apply_skill_roll auto-queues advancement since no pending was added


class PrisonerEvent3Handler(CareerHandlerBase):
    type: Literal['prisoner_event_3'] = 'prisoner_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction='Attempt to escape the prison (Stealth or Deception 10+) or stay?',
                choices=[PrisonerEvent3Attempt(), PrisonerEvent3Stay()],
            )
        )
        return pending_idx + 1


# ── event 4: hard labour ──────────────────────────────────────────────────────


class PendingPrisonerEvent4SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['prisoner_event_4_skill_roll'] = 'prisoner_event_4_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 1)
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.0',
                    instruction='Hard labour endured: choose Athletics, Mechanic, or Melee (unarmed)',
                    options=[Athletics(), Mechanic(), Melee()],
                )
            )
        else:
            projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 1)
        # _apply_skill_roll auto-queues advancement when no pending added (fail case)
        # For success: skill choice is pending; advancement queued after it resolves via _apply_skill_choice


class PrisonerEvent4Handler(CareerHandlerBase):
    type: Literal['prisoner_event_4'] = 'prisoner_event_4'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingPrisonerEvent4SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll END 8+: success = PT-1 + skill choice; fail = PT+1',
                options=[Chars.END],
            )
        )
        return pending_idx + 1


# ── event 5: gang opportunity ─────────────────────────────────────────────────


class PendingPrisonerEvent5SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['prisoner_event_5_skill_roll'] = 'prisoner_event_5_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 1)
            projection.summary.problems.append(
                'Prisoner event 5: joined a gang — gain DM+1 to survival rolls while in this career.'
            )
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.0',
                    instruction='Joined gang: choose Persuade, Melee, or Stealth',
                    options=[Persuade(), Melee(), Stealth()],
                )
            )
        else:
            projection.summary.connections.append(Enemy(source='The prison gang you refused to join'))
        # Fail: _apply_skill_roll auto-queues advancement (no pending added)
        # Success: skill choice queued; advancement queued after it resolves


class PrisonerEvent5Handler(CareerHandlerBase):
    type: Literal['prisoner_event_5'] = 'prisoner_event_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingPrisonerEvent5SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll Persuade or Melee 8+ to join the gang: success = PT+1 + skill; fail = gain Enemy',
                options=[Persuade(), Melee()],
            )
        )
        return pending_idx + 1


# ── event 6: vocational training ─────────────────────────────────────────────


class PendingPrisonerEvent6SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['prisoner_event_6_skill_roll'] = 'prisoner_event_6_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll >= 8:
            from ceres.character.skills import AnySkill, _skill_classes

            all_skills: list[AnySkill] = cast(
                list[AnySkill],
                sorted(
                    [cls() for cls in _skill_classes(AnySkill) if cls is not JackOfAllTrades],
                    key=lambda s: type(s).name(),
                ),
            )
            projection.pending_inputs.append(
                PendingSkillChoice(
                    id=f'{event.id}.0',
                    instruction='Vocational training: choose any skill at level 1',
                    options=all_skills,
                )
            )
        # Fail or success-with-pending: _apply_skill_roll handles advancement correctly


class PrisonerEvent6Handler(CareerHandlerBase):
    type: Literal['prisoner_event_6'] = 'prisoner_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingPrisonerEvent6SkillRoll(
                id=f'{event_id}.{pending_idx}',
                instruction='Roll EDU 8+ to gain any skill at level 1',
                options=[Chars.EDU],
            )
        )
        return pending_idx + 1


# ── event 7: prison event sub-table ──────────────────────────────────────────


class PrisonerEvent7Riot(ChoiceBase):
    kind: Literal['prisoner_event_7_riot'] = 'prisoner_event_7_riot'
    label: str = '1 — Prison Riot'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            PendingPrisonerEvent7RiotSkillRoll(
                id=f'{event.id}.0',
                instruction='Riot: roll END 8+: success = survive unhurt; fail = roll on Injury table',
                options=[Chars.END],
            )
        )


class PrisonerEvent7Gang(ChoiceBase):
    kind: Literal['prisoner_event_7_gang'] = 'prisoner_event_7_gang'
    label: str = '2 — Gang Attack (PT+1, gain Enemy)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.parole_threshold = min(12, (projection.summary.parole_threshold or 0) + 1)
        projection.summary.connections.append(Enemy(source='A prison gang that forced itself on you'))
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PrisonerEvent7Transfer(ChoiceBase):
    kind: Literal['prisoner_event_7_transfer'] = 'prisoner_event_7_transfer'
    label: str = '3 — Transferred to Another Prison'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.problems.append(
            'Prisoner event 7: transferred to another prison — no mechanical effect. Apply manually if needed.'
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PrisonerEvent7Visitation(ChoiceBase):
    kind: Literal['prisoner_event_7_visitation'] = 'prisoner_event_7_visitation'
    label: str = '4 — Visitation (gain Ally)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.connections.append(
            Ally(source='A visitor who became a loyal friend during your imprisonment')
        )
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PrisonerEvent7ParoleHearing(ChoiceBase):
    kind: Literal['prisoner_event_7_parole_hearing'] = 'prisoner_event_7_parole_hearing'
    label: str = '5 — Parole Hearing (PT-1)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 1)
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PrisonerEvent7GoodBehaviour(ChoiceBase):
    kind: Literal['prisoner_event_7_good_behaviour'] = 'prisoner_event_7_good_behaviour'
    label: str = '6 — Good Behaviour (PT-1)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 1)
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PendingPrisonerEvent7RiotSkillRoll(CareerSkillRollPendingBase):
    kind: Literal['prisoner_event_7_riot_skill_roll'] = 'prisoner_event_7_riot_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.events import _advancement_pending

        career = projection.get_current_career()
        if event.modified_roll < 8:
            projection.pending_inputs.append(
                PendingInjuryTable(
                    id=f'{event.id}.0',
                    instruction='Riot injury: roll 1D on Injury table',
                    options=['1', '2', '3', '4', '5', '6'],
                )
            )
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id, 1)
            )
        # Success: _apply_skill_roll auto-queues advancement


class PrisonerEvent7Handler(CareerHandlerBase):
    type: Literal['prisoner_event_7'] = 'prisoner_event_7'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction='Prison Event: roll 1D and select the matching result',
                choices=[
                    PrisonerEvent7Riot(),
                    PrisonerEvent7Gang(),
                    PrisonerEvent7Transfer(),
                    PrisonerEvent7Visitation(),
                    PrisonerEvent7ParoleHearing(),
                    PrisonerEvent7GoodBehaviour(),
                ],
            )
        )
        return pending_idx + 1


# ── event 9: hire lawyer ──────────────────────────────────────────────────────


class PrisonerEvent9Level1(ChoiceBase):
    kind: Literal['prisoner_event_9_level_1'] = 'prisoner_event_9_level_1'
    label: str = 'Hire level 1 lawyer (Cr1000)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.summary.problems.append(
            'Prisoner event 9: lawyer level 1 hired — deduct Cr1000 from cash. Apply manually.'
        )
        projection.pending_inputs.append(
            PendingPrisonerEvent9LawyerSkillRoll(
                id=f'{event.id}.0',
                instruction='Roll 2D + 1 vs 8+: success = PT-1',
                options=[],
                lawyer_level=1,
            )
        )


class PrisonerEvent9Level2(ChoiceBase):
    kind: Literal['prisoner_event_9_level_2'] = 'prisoner_event_9_level_2'
    label: str = 'Hire level 2 lawyer (Cr2000)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.summary.problems.append(
            'Prisoner event 9: lawyer level 2 hired — deduct Cr2000 from cash. Apply manually.'
        )
        projection.pending_inputs.append(
            PendingPrisonerEvent9LawyerSkillRoll(
                id=f'{event.id}.0',
                instruction='Roll 2D + 2 vs 8+: success = PT-1',
                options=[],
                lawyer_level=2,
            )
        )


class PrisonerEvent9Level3(ChoiceBase):
    kind: Literal['prisoner_event_9_level_3'] = 'prisoner_event_9_level_3'
    label: str = 'Hire level 3 lawyer (Cr3000)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.summary.problems.append(
            'Prisoner event 9: lawyer level 3 hired — deduct Cr3000 from cash. Apply manually.'
        )
        projection.pending_inputs.append(
            PendingPrisonerEvent9LawyerSkillRoll(
                id=f'{event.id}.0',
                instruction='Roll 2D + 3 vs 8+: success = PT-1',
                options=[],
                lawyer_level=3,
            )
        )


class PrisonerEvent9Decline(ChoiceBase):
    kind: Literal['prisoner_event_9_decline'] = 'prisoner_event_9_decline'
    label: str = 'Decline (no action)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PendingPrisonerEvent9LawyerSkillRoll(CareerSkillRollPendingBase):
    kind: Literal['prisoner_event_9_lawyer_skill_roll'] = 'prisoner_event_9_lawyer_skill_roll'
    lawyer_level: int = 1

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        if event.modified_roll + self.lawyer_level >= 8:
            projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 1)
        # _apply_skill_roll auto-queues advancement


class PrisonerEvent9Handler(CareerHandlerBase):
    type: Literal['prisoner_event_9'] = 'prisoner_event_9'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction=(
                    'Hire a lawyer? Level 1 (Cr1000), Level 2 (Cr2000), Level 3 (Cr3000), or decline? '
                    'Success (2D + level vs 8+) = PT-1.'
                ),
                choices=[
                    PrisonerEvent9Level1(),
                    PrisonerEvent9Level2(),
                    PrisonerEvent9Level3(),
                    PrisonerEvent9Decline(),
                ],
            )
        )
        return pending_idx + 1


# ── event 12: heroism ─────────────────────────────────────────────────────────


class PrisonerEvent12TakeRisk(ChoiceBase):
    kind: Literal['prisoner_event_12_take_risk'] = 'prisoner_event_12_take_risk'
    label: str = 'Take the risk (roll 2D — 7-: injury; 8+: Ally + PT-2)'

    def handle(self, projection: CharacterProjection, event) -> None:
        projection.pending_inputs.append(
            PendingPrisonerEvent12HeroismSkillRoll(
                id=f'{event.id}.0',
                instruction='Roll 2D: 8+ = Ally + PT-2; 7 or less = roll on Injury table',
                options=[],
            )
        )


class PrisonerEvent12Refuse(ChoiceBase):
    kind: Literal['prisoner_event_12_refuse'] = 'prisoner_event_12_refuse'
    label: str = 'Refuse (no action)'

    def handle(self, projection: CharacterProjection, event) -> None:
        career = projection.get_current_career()
        projection.pending_inputs.append(career_progress_pending(projection, career, event.id))


class PendingPrisonerEvent12HeroismSkillRoll(CareerSkillRollPendingBase):
    kind: Literal['prisoner_event_12_heroism_skill_roll'] = 'prisoner_event_12_heroism_skill_roll'

    def resolve(self, projection: CharacterProjection, event: SkillRollEvent) -> None:
        from ceres.character.events import _advancement_pending

        career = projection.get_current_career()
        if event.modified_roll >= 8:
            projection.summary.connections.append(Ally(source='A fellow prisoner whose life you saved'))
            projection.summary.parole_threshold = max(0, (projection.summary.parole_threshold or 0) - 2)
            # _apply_skill_roll auto-queues advancement (no pending added)
        else:
            projection.pending_inputs.append(
                PendingInjuryTable(
                    id=f'{event.id}.0',
                    instruction='Heroism failed: roll 1D on Injury table',
                    options=['1', '2', '3', '4', '5', '6'],
                )
            )
            projection.pending_inputs.append(
                _advancement_pending(career, projection.summary.current_assignment_index or 0, event.id, 1)
            )


class PrisonerEvent12Handler(CareerHandlerBase):
    type: Literal['prisoner_event_12'] = 'prisoner_event_12'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                id=f'{event_id}.{pending_idx}',
                instruction='An act of heroism: take the risk (roll 2D — 7-: injury; 8+: Ally + PT-2) or refuse?',
                choices=[PrisonerEvent12TakeRisk(), PrisonerEvent12Refuse()],
            )
        )
        return pending_idx + 1


class Prisoner(CareerData):
    type: Literal['PRISONER_CAREER'] = 'PRISONER_CAREER'

    career: ClassVar[Career] = Career(
        name='Prisoner',
        description=(
            'Every society has its bad apples and even in the far future punishments usually '
            'take place within faceless institutions where criminals can be conveniently forgotten.'
        ),
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.END, target=0)
    allows_assignment_change: ClassVar[bool] = True
    selectable: ClassVar[bool] = False

    assignments: ClassVar[list[AssignmentData]] = [
        AssignmentData(
            name='Inmate',
            description='You just try to get through your time in prison without getting into trouble.',
            survival=CharCheck(characteristic=Chars.END, target=7),
            advancement=CharCheck(characteristic=Chars.STR, target=7),
        ),
        AssignmentData(
            name='Thug',
            description='You are part of a gang in prison, terrorising the other inmates.',
            survival=CharCheck(characteristic=Chars.STR, target=8),
            advancement=CharCheck(characteristic=Chars.END, target=6),
        ),
        AssignmentData(
            name='Fixer',
            description='You can arrange anything – for the right price.',
            survival=CharCheck(characteristic=Chars.INT, target=9),
            advancement=CharCheck(characteristic=Chars.END, target=5),
        ),
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
        personal_development=SkillTable(
            [
                Chars.STR,
                [Melee()],
                Chars.END,
                JackOfAllTrades(),
                Chars.EDU,
                Gambler(),
            ]
        ),
        service_skills=SkillTable(
            [
                Athletics(),
                Deception(),
                skill_instances(ProfessionSkill),
                Streetwise(),
                [Melee()],
                Persuade(),
            ]
        ),
        assignment1=SkillTable(
            [  # Inmate
                Stealth(),
                [Melee()],
                Streetwise(),
                Survival(),
                [Athletics()],
                Mechanic(),
            ]
        ),
        assignment2=SkillTable(
            [  # Thug
                Persuade(),
                [Melee()],
                [Melee()],
                [Melee()],
                [Athletics()],
                [Athletics()],
            ]
        ),
        assignment3=SkillTable(
            [  # Fixer
                Investigate(),
                Broker(),
                Deception(),
                Streetwise(),
                Stealth(),
                Admin(),
            ]
        ),
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0, bonus=RankBonus(skill=Melee(), level=1)),
        1: RankEntry(rank=1),
        2: RankEntry(rank=2, bonus=RankBonus(skill=Athletics(), level=1)),
        3: RankEntry(rank=3),
        4: RankEntry(rank=4, bonus=RankBonus(skill=Advocate(), level=1)),
        5: RankEntry(rank=5),
        6: RankEntry(rank=6, bonus=RankBonus(characteristic=Chars.END, level=1)),
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=0, benefit=CONTACT),
            2: MusterOutRow(cash=0, benefit=BLADE),
            3: MusterOutRow(cash=100, benefit=ChoiceBenefit(options=[DECEPTION_ITEM, PERSUADE_ITEM, STEALTH_ITEM])),
            4: MusterOutRow(cash=200, benefit=ALLY),
            5: MusterOutRow(cash=500, benefit=ChoiceBenefit(options=[MELEE_ITEM, RECON_ITEM, STREETWISE_ITEM])),
            6: MusterOutRow(
                cash=1000,
                benefit=ChoiceBenefit(
                    options=[
                        CharacteristicIncrease(char=Chars.STR, amount=1),
                        CharacteristicIncrease(char=Chars.END, amount=1),
                    ]
                ),
            ),
            7: MusterOutRow(cash=2500, benefit=CombinedBenefit(benefits=[DECEPTION_ITEM, PERSUADE_ITEM, STEALTH_ITEM])),
        }
    )

    mishaps: ClassVar[dict[int, MishapEntry]] = {
        1: MishapEntry(
            text='Severely injured.',
            stay_in_career=True,
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text='You are accused of assaulting a prison guard. Parole Threshold +2.',
            stay_in_career=True,
            effects=[ParoleThresholdChangeEffect(amount=2)],
        ),
        3: MishapEntry(
            text='A prison gang persecutes you.',
            stay_in_career=True,
            defer_ejection=True,
            effects=[PrisonerMishap3Handler()],
        ),
        4: MishapEntry(
            text='A guard takes a dislike to you. Gain an Enemy and raise your Parole Threshold by +1.',
            stay_in_career=True,
            effects=[GainEnemyEffect(), ParoleThresholdChangeEffect(amount=1)],
        ),
        5: MishapEntry(
            text='Disgraced. Word of your criminal past reaches your homeworld. Lose 1 SOC.',
            stay_in_career=True,
            effects=[DecreaseCharacteristicEffect(characteristic=Chars.SOC, amount=1)],
        ),
        6: MishapEntry(
            text='Injured. Roll on the Injury table.',
            stay_in_career=True,
            effects=[InjuryEffect(severity='from_table')],
        ),
    }

    events: ClassVar[dict[int, CareerEventEntry]] = {
        2: CareerEventEntry(
            text='Disaster! Roll on the Mishap table but you are not ejected from this career.',
            effects=[RollMishapEffect(leave=False)],
        ),
        3: CareerEventEntry(
            text='You have the opportunity to escape the prison.',
            effects=[PrisonerEvent3Handler()],
        ),
        4: CareerEventEntry(
            text='You are assigned to difficult or backbreaking labour.',
            effects=[PrisonerEvent4Handler()],
        ),
        5: CareerEventEntry(
            text='You have the opportunity to join a gang.',
            effects=[PrisonerEvent5Handler()],
        ),
        6: CareerEventEntry(
            text='Vocational Training.',
            effects=[PrisonerEvent6Handler()],
        ),
        7: CareerEventEntry(
            text='Prison Event.',
            effects=[PrisonerEvent7Handler()],
        ),
        8: CareerEventEntry(
            text='Parole hearing. Reduce your Parole Threshold by -1.',
            effects=[ParoleThresholdChangeEffect(amount=-1)],
        ),
        9: CareerEventEntry(
            text='You have the opportunity to hire a new lawyer.',
            effects=[PrisonerEvent9Handler()],
        ),
        10: CareerEventEntry(
            text='Special Duty.',
            effects=[SkillChoiceEffect(options=[Admin(), Advocate(), Electronics(), Steward()], level=1)],
        ),
        11: CareerEventEntry(
            text='The warden takes an interest in your case. Reduce your Parole Threshold by -2.',
            effects=[ParoleThresholdChangeEffect(amount=-2)],
        ),
        12: CareerEventEntry(
            text='Heroism.',
            effects=[PrisonerEvent12Handler()],
        ),
    }

    def advancement_is_special(self) -> bool:
        return True

    def start_career(
        self,
        projection: CharacterProjection,
        assignment: AssignmentData,
        event_id: int,
        qualification_roll: int,
    ) -> None:
        projection.summary.current_career = self
        projection.summary.current_assignment = assignment.name
        projection.summary.current_assignment_index = self.assignment_index(assignment)
        count_before = len(projection.pending_inputs)
        self.start_new_term(projection, assignment, event_id)
        pending_added = len(projection.pending_inputs) - count_before
        projection.pending_inputs.append(
            PendingParoleRoll(
                id=f'{event_id}.{pending_added}',
                instruction='Roll 1D to determine your Parole Threshold (result + 2)',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )


PRISONER = Prisoner()
