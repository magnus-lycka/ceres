from typing import ClassVar, Literal

from ceres.character.domain.benefits import (
    CYBERNETIC_IMPLANT,
    SCIENTIFIC_EQUIPMENT,
    SHIP_SHARE,
    TAS_MEMBERSHIP,
    WEAPON,
    CharacteristicIncrease,
    ChoiceBenefit,
)
from ceres.character.domain.career.career_data import (
    AdvancementDmEntry,
    AdvancementDmOption,
    AssignmentData,
    AutoAdvanceEntry,
    BenefitDmEntry,
    CareerData,
    CareerHandlerBase,
    CareerSkillTables,
    CareerTableEntry,
    CareerTerm,
    CharCheck,
    GainSkillAndConnectionEntry,
    InjuryEntry,
    LifeEventEntry,
    MusterOutData,
    MusterOutRow,
    RankBonus,
    RankEntry,
    RolledConnectionsEntry,
    RollMishapEntry,
    SkillChoiceEntry,
    SkillTable,
)
from ceres.character.domain.career.career_events import (
    PendingChoices,
    PendingMishap,
    PendingSkillChoice,
    muster_out_setup,
)
from ceres.character.domain.career.common import CommonMishap1Handler, handle_advanced_training
from ceres.character.domain.career.common_pending import (
    CareerSkillChoicePendingBase,
    CareerSkillRollPendingBase,
)
from ceres.character.domain.character_state import CharacterProjection
from ceres.character.domain.characteristics import Chars, ConnectionKind
from ceres.character.domain.dice import DiceRoll
from ceres.character.domain.health.health_events import PendingDoubleInjuryRoll
from ceres.character.domain.skills import (
    Admin,
    Advocate,
    Athletics,
    Carouse,
    Deception,
    Drive,
    Electronics,
    Explosives,
    Flyer,
    GunCombat,
    Gunner,
    Investigate,
    JackOfAllTrades,
    LanguageSkill,
    Level,
    Medic,
    Melee,
    Persuade,
    Pilot,
    Recon,
    Stealth,
    Streetwise,
    Tactics,
    VaccSuit,
    skill_instances,
)
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.pending_input import ChoiceBase

# ── Career-specific pending input types ──────────────────────────────────────


class AgentMishap2Accept(ChoiceBase):
    kind: Literal['agent_mishap_2_accept'] = 'agent_mishap_2_accept'
    label: str = 'Accept (leave without further penalty, lose Benefit roll)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.domain.career.career_events import _apply_mishap_ejection

        projection.get_current_career()
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class AgentMishap2Refuse(ChoiceBase):
    kind: Literal['agent_mishap_2_refuse'] = 'agent_mishap_2_refuse'
    label: str = 'Refuse (roll twice on Injury table, gain Enemy, choose any skill)'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.domain.career.career_events import _apply_mishap_ejection

        projection.get_current_career()
        pending_idx = 0
        projection.add_connection(
            ConnectionKind.ENEMY,
            origin="The criminal figure who offered you a deal and didn't take kindly to your refusal",
        )
        projection.pending_inputs.append(
            PendingDoubleInjuryRoll(
                pending_id=(event.id, pending_idx),
                instruction='Refused: roll twice on the Injury table and provide both results — lower applies',
            )
        )
        pending_idx += 1
        projection.pending_inputs.append(
            PendingSkillChoice(
                pending_id=(event.id, pending_idx),
                instruction='Refused criminal deal: choose any skill to gain at level 1',
                options=[],
            )
        )
        pending_idx += 1
        _apply_mishap_ejection(projection, event.id, pending_idx, lose_current_term=True)


class PendingAgentMishap3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['agent_mishap_3_skill_roll'] = 'agent_mishap_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        projection.get_current_career()

        from ceres.character.domain.career.prisoner_events import set_forced_prison_career

        succeed = event.modified_roll >= 8
        if event.modified_roll <= 2:
            set_forced_prison_career(projection, 'Exposed as an agent — sent to Prisoner career.')
        if not succeed and projection.summary.career_terms:
            projection.summary.career_terms[-1].require_muster_out().lost_rolls += 1
        muster_out_setup(projection, event.id, 0)


class AgentMishap5Contact(ChoiceBase):
    kind: Literal['agent_mishap_5_contact'] = 'agent_mishap_5_contact'
    label: str = 'A Contact was hurt'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.domain.career.career_events import _apply_mishap_ejection

        projection.get_current_career()
        projection.summary.problems.append(
            'Agent mishap 5: a Contact was hurt — roll twice on the Injury table for them '
            'and apply the lower result (NPC injury; no mechanical effect on your character).'
        )
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class AgentMishap5Ally(ChoiceBase):
    kind: Literal['agent_mishap_5_ally'] = 'agent_mishap_5_ally'
    label: str = 'An Ally was hurt'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.domain.career.career_events import _apply_mishap_ejection

        projection.get_current_career()
        projection.summary.problems.append(
            'Agent mishap 5: an Ally was hurt — roll twice on the Injury table for them '
            'and apply the lower result (NPC injury; no mechanical effect on your character).'
        )
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class AgentMishap5Family(ChoiceBase):
    kind: Literal['agent_mishap_5_family'] = 'agent_mishap_5_family'
    label: str = 'A family member was hurt'

    def handle(self, projection: CharacterProjection, event) -> None:
        from ceres.character.domain.career.career_events import _apply_mishap_ejection

        projection.get_current_career()
        projection.summary.problems.append(
            'Agent mishap 5: a family member was hurt — roll twice on the Injury table for them '
            'and apply the lower result (NPC injury; no mechanical effect on your character).'
        )
        _apply_mishap_ejection(projection, event.id, 0, lose_current_term=True)


class PendingAgentEvent3SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['agent_event_3_skill_roll'] = 'agent_event_3_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        if event.modified_roll >= 8:
            projection.pending_inputs.append(
                PendingSkillChoice(
                    pending_id=(event.id, 0),
                    instruction=(
                        'Investigation success: increase one skill by one level — Deception, '
                        'Jack-of-all-Trades, Persuade or Tactics'
                    ),
                    options=[Deception(), JackOfAllTrades(), Persuade(), Tactics()],
                )
            )
        else:
            projection.pending_inputs.append(
                PendingMishap(
                    pending_id=(event.id, 0),
                    instruction='Investigation went wrong: roll 1D on Mishap table '
                    '(you are not ejected from this career)',
                )
            )


class PendingAgentEvent8SkillRoll(CareerSkillRollPendingBase):
    kind: Literal['agent_event_8_skill_roll'] = 'agent_event_8_skill_roll'

    def resolve(self, projection: CharacterProjection, event: Event) -> None:
        if event.modified_roll >= 8:
            projection.summary.problems.append(
                'Undercover mission success: roll on Rogue or Citizen Events table and '
                'make one roll on any Specialist skill table for that career (apply manually — '
                'cross-career table automation not yet implemented).'
            )
        else:
            projection.summary.problems.append(
                'Undercover mission failed: roll on Rogue or Citizen Mishap table '
                '(apply manually — cross-career table automation not yet implemented).'
            )


class PendingAgentEvent11SkillChoice(CareerSkillChoicePendingBase):
    kind: Literal['agent_event_11_skill_choice'] = 'agent_event_11_skill_choice'
    advancement_precreated: bool = False


# ── mishap 2: criminal deal ───────────────────────────────────────────────────


class AgentMishap2Handler(CareerHandlerBase):
    kind: Literal['agent_mishap_2'] = 'agent_mishap_2'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction=(
                    'Accept (leave without further penalty, lose Benefit roll as normal) or Refuse '
                    '(roll twice on Injury table take lower, gain Enemy, choose skill)?'
                ),
                choices=[AgentMishap2Accept(), AgentMishap2Refuse()],
            )
        )
        return pending_idx + 1


# ── mishap 3: investigation gone wrong ───────────────────────────────────────


class AgentMishap3Handler(CareerHandlerBase):
    kind: Literal['agent_mishap_3'] = 'agent_mishap_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingAgentMishap3SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Advocate 8+ to keep the Benefit roll from this term',
                options=[Advocate()],
            )
        )
        return pending_idx + 1


# ── mishap 5: someone close gets hurt ────────────────────────────────────────


class AgentMishap5Handler(CareerHandlerBase):
    kind: Literal['agent_mishap_5'] = 'agent_mishap_5'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingChoices(
                pending_id=(event_id, pending_idx),
                instruction='Choose who was hurt: a Contact, an Ally, or a family member?',
                choices=[AgentMishap5Contact(), AgentMishap5Ally(), AgentMishap5Family()],
            )
        )
        return pending_idx + 1


# ── event 3: dangerous investigation ─────────────────────────────────────────


class AgentEvent3Handler(CareerHandlerBase):
    kind: Literal['agent_event_3'] = 'agent_event_3'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingAgentEvent3SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Investigate 8+ or Streetwise 8+',
                options=[Investigate(), Streetwise()],
            )
        )
        return pending_idx + 1


# ── event 6: advanced training ───────────────────────────────────────────────


class AgentEvent6Handler(CareerHandlerBase):
    kind: Literal['agent_event_6'] = 'agent_event_6'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        return handle_advanced_training(projection, event_id, pending_idx)


# ── event 8: undercover mission ──────────────────────────────────────────────


class AgentEvent8Handler(CareerHandlerBase):
    kind: Literal['agent_event_8'] = 'agent_event_8'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingAgentEvent8SkillRoll(
                pending_id=(event_id, pending_idx),
                instruction='Roll Deception 8+ for the undercover mission',
                options=[Deception()],
            )
        )
        return pending_idx + 1


# ── event 11: senior agent mentor ────────────────────────────────────────────


class AgentEvent11Handler(CareerHandlerBase):
    kind: Literal['agent_event_11'] = 'agent_event_11'

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        projection.pending_inputs.append(
            PendingAgentEvent11SkillChoice(
                pending_id=(event_id, pending_idx),
                instruction='Senior agent mentor: increase Investigate by one '
                'level or DM+4 to your next advancement roll',
                options=[Investigate(), AdvancementDmOption()],
            )
        )
        return pending_idx + 1


class Agent(CareerData):
    kind: Literal['AGENT_CAREER'] = 'AGENT_CAREER'

    name: ClassVar[str] = 'Agent'
    description: ClassVar[str] = (
        'Law enforcement agencies, corporate operatives, spies and others who work in the shadows.'
    )
    qualification: ClassVar[CharCheck] = CharCheck(characteristic=Chars.INT, target=6)
    allows_assignment_change: ClassVar[bool] = False
    draft_assignments: ClassVar[list[str]] = ['Law Enforcement']

    assignments: ClassVar[list[AssignmentData]] = [
        AssignmentData(
            name='Law Enforcement',
            description='You are a police officer or detective.',
            survival=CharCheck(characteristic=Chars.END, target=6),
            advancement=CharCheck(characteristic=Chars.INT, target=6),
        ),
        AssignmentData(
            name='Intelligence',
            description='You work as a spy or saboteur.',
            survival=CharCheck(characteristic=Chars.INT, target=7),
            advancement=CharCheck(characteristic=Chars.INT, target=5),
        ),
        AssignmentData(
            name='Corporate',
            description='You work for a corporation, spying on rival organisations.',
            survival=CharCheck(characteristic=Chars.INT, target=5),
            advancement=CharCheck(characteristic=Chars.INT, target=7),
        ),
    ]

    skill_tables: ClassVar[CareerSkillTables] = CareerSkillTables(
        personal_development=SkillTable(
            [
                GunCombat(),
                Chars.DEX,
                Chars.END,
                Melee(),
                Chars.INT,
                Athletics(),
            ]
        ),
        service_skills=SkillTable(
            [
                Streetwise(),
                Drive(),
                Investigate(),
                Flyer(),
                Recon(),
                GunCombat(),
            ]
        ),
        advanced_education=SkillTable(
            [
                Advocate(),
                skill_instances(LanguageSkill),
                Explosives(),
                Medic(),
                VaccSuit(),
                Electronics(),
            ],
            min_edu=8,
        ),
        assignment1=SkillTable(
            [  # Law Enforcement
                Investigate(),
                Recon(),
                Streetwise(),
                Stealth(),
                Melee(),
                Advocate(),
            ]
        ),
        assignment2=SkillTable(
            [  # Intelligence
                Investigate(),
                Recon(),
                Electronics(),
                Stealth(),
                Persuade(),
                Deception(),
            ]
        ),
        assignment3=SkillTable(
            [  # Corporate
                Investigate(),
                Electronics(),
                Stealth(),
                Carouse(),
                Deception(),
                Streetwise(),
            ]
        ),
    )

    ranks: ClassVar[dict[int, RankEntry]] = {
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, title='Agent', bonus=RankBonus(skill=Deception(), level=1)),
        2: RankEntry(rank=2, title='Field Agent', bonus=RankBonus(skill=Investigate(), level=1)),
        3: RankEntry(rank=3),
        4: RankEntry(rank=4, title='Special Agent', bonus=RankBonus(skill=GunCombat(), level=1)),
        5: RankEntry(rank=5, title='Assistant Director'),
        6: RankEntry(rank=6, title='Director'),
    }

    ranks_by_assignment: ClassVar[dict[int, dict[int, RankEntry]]] = {
        1: {  # Law Enforcement
            0: RankEntry(rank=0, title='Rookie'),
            1: RankEntry(rank=1, title='Corporal', bonus=RankBonus(skill=Streetwise(), level=1)),
            2: RankEntry(rank=2, title='Sergeant'),
            3: RankEntry(rank=3, title='Detective'),
            4: RankEntry(rank=4, title='Lieutenant', bonus=RankBonus(skill=Investigate(), level=1)),
            5: RankEntry(rank=5, title='Chief', bonus=RankBonus(skill=Admin(), level=1)),
            6: RankEntry(rank=6, title='Commissioner', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        },
    }

    muster_out: ClassVar[MusterOutData] = MusterOutData(
        rows={
            1: MusterOutRow(cash=1000, benefit=SCIENTIFIC_EQUIPMENT),
            2: MusterOutRow(cash=2000, benefit=CharacteristicIncrease(char=Chars.INT, amount=1)),
            3: MusterOutRow(cash=5000, benefit=SHIP_SHARE),
            4: MusterOutRow(cash=7500, benefit=WEAPON),
            5: MusterOutRow(cash=10000, benefit=CYBERNETIC_IMPLANT),
            6: MusterOutRow(
                cash=25000,
                benefit=ChoiceBenefit(options=[CharacteristicIncrease(char=Chars.SOC, amount=1), CYBERNETIC_IMPLANT]),
            ),
            7: MusterOutRow(cash=50000, benefit=TAS_MEMBERSHIP),
        }
    )

    mishaps: ClassVar[dict[int, CareerTableEntry]] = {
        1: CommonMishap1Handler(
            text='Severely injured (this is the same as a result of 2 on the Injury table). '
            'Alternatively, roll twice on the Injury table and take the lower result.',
            defer_ejection=True,
        ),
        2: AgentMishap2Handler(
            text=(
                'A criminal or other figure under investigation offers you a deal. Accept and you leave this career '
                'without further penalty (although you lose the Benefit roll as normal). Refuse and you must roll '
                'twice on the Injury table and take the lower result. You gain an Enemy and one level in any skill '
                'you choose.'
            ),
            defer_ejection=True,
        ),
        3: AgentMishap3Handler(
            text=(
                'An investigation goes critically wrong or leads to the top, ruining your career. Roll Advocate 8+. '
                'If you succeed, you may keep the Benefit roll from this term. If you roll 2, you must take the '
                'Prisoner career in your next term.'
            ),
            defer_ejection=True,
        ),
        4: GainSkillAndConnectionEntry(
            text='You learn something you should not know and people want to kill you for it. '
            'Gain an Enemy and Deception 1.',
            skill=Deception(level=Level(value=1)),
            connection=ConnectionKind.ENEMY,
        ),
        5: AgentMishap5Handler(
            text=(
                'Your work ends up coming home with you and someone gets hurt. Choose one of your Contacts, Allies '
                'or family members and roll twice on the Injury table for them, taking the lower result.'
            ),
            defer_ejection=True,
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
        3: AgentEvent3Handler(
            text=(
                'An investigation takes on a dangerous turn. Roll Investigate 8+ or Streetwise 8+. If you fail, '
                'roll on the Mishap table. If you succeed, increase one of these skills by one level: Deception, '
                'Jack-of-all-Trades, Persuade or Tactics.'
            ),
        ),
        4: BenefitDmEntry(
            text='You complete a mission for your superiors and are suitably rewarded. '
            'Gain DM+1 to any one Benefit roll from this career.',
            amount=1,
        ),
        5: RolledConnectionsEntry(
            text='You establish a network of contacts. Gain D3 Contacts.',
            connection=ConnectionKind.CONTACT,
            dice=DiceRoll.parse('d3'),
        ),
        6: AgentEvent6Handler(
            text='You are given advanced training in a specialist field. '
            'Roll EDU 8+ to increase any one skill you already have by one level.',
        ),
        7: LifeEventEntry(
            text='Life Event. Roll on the Life Events table.',
        ),
        8: AgentEvent8Handler(
            text=(
                'You go undercover to investigate an enemy. Roll Deception 8+. If you succeed, roll immediately on '
                'the Rogue or Citizen Events table and make one roll on any Specialist skill table for that career. '
                'If you fail, roll immediately on the Rogue or Citizen Mishap table.'
            ),
        ),
        9: AdvancementDmEntry(
            text='You go above and beyond the call of duty. Gain DM+2 to your next advancement roll.',
            amount=2,
        ),
        10: SkillChoiceEntry(
            text='You are given specialist training in vehicles. Gain one of Drive 1, Flyer 1, Pilot 1 or Gunner 1.',
            options=[Drive(), Flyer(), Pilot(), Gunner()],
            level=1,
        ),
        11: AgentEvent11Handler(
            text='You are befriended by a senior agent. Either increase Investigate by one level or DM+4 to an '
            'advancement roll thanks to their aid.',
        ),
        12: AutoAdvanceEntry(
            text='Your efforts uncover a major conspiracy against your employers. You are automatically promoted.',
        ),
    }

    def prior_terms(self, terms, assignment: AssignmentData) -> list:
        return [term for term in terms if type(term.career) is type(self) and term.assignment == assignment]


AGENT = Agent()


class AgentTerm(CareerTerm):
    kind: Literal['agent_term'] = 'agent_term'
    career: Agent


Agent.term_class = AgentTerm
