from ceres.character.benefits import (
    CYBERNETIC_IMPLANT,
    SCIENTIFIC_EQUIPMENT,
    SHIP_SHARE,
    TAS_MEMBERSHIP,
    WEAPON,
    CharacteristicIncrease,
    ChoiceBenefit,
)
from ceres.character.careers.career_data import (
    AdvancementDmEffect,
    AssignmentData,
    AutoAdvanceEffect,
    BenefitDmEffect,
    CareerData,
    CareerDispatchEffect,
    CareerEventEntry,
    CareerSkillTables,
    CharCheck,
    GainConnectionsRolledEffect,
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
from ceres.character.careers.common import handle_advanced_training, resolve_advanced_training
from ceres.character.characteristics import Chars, ConnectionKind
from ceres.character.events import (
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
    PendingDoubleInjuryRoll,
    PendingMishap,
    PendingSkillChoice,
    SkillRollEvent,
    muster_out_setup,
)
from ceres.character.skills import (
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
    Investigate,
    LanguageSkill,
    Level,
    Medic,
    Melee,
    Persuade,
    Recon,
    Stealth,
    Streetwise,
    VaccSuit,
    skill_instances,
)
from ceres.character.state import (
    CharacterProjection,
    Enemy,
)


class AgentCareerData(CareerData):
    def prior_terms(self, terms, assignment: AssignmentData) -> list:
        idx = self.assignment_index(assignment)
        return [term for term in terms if term.career == self.name and term.assignment_index == idx]


CAREER_DATA = AgentCareerData(
    name='Agent',
    description='Law enforcement agencies, corporate operatives, spies and others who work in the shadows.',
    source='Core',
    allows_assignment_change=False,
    qualification=CharCheck(characteristic=Chars.INT, target=6),
    assignments=[
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
    ],
    skill_tables=CareerSkillTables(
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
    ),
    ranks={
        0: RankEntry(rank=0),
        1: RankEntry(rank=1, title='Agent', bonus=RankBonus(skill=Deception(), level=1)),
        2: RankEntry(rank=2, title='Field Agent', bonus=RankBonus(skill=Investigate(), level=1)),
        3: RankEntry(rank=3),
        4: RankEntry(rank=4, title='Special Agent', bonus=RankBonus(skill=GunCombat(), level=1)),
        5: RankEntry(rank=5, title='Assistant Director'),
        6: RankEntry(rank=6, title='Director'),
    },
    ranks_by_assignment={
        1: {  # Law Enforcement
            0: RankEntry(rank=0, title='Rookie'),
            1: RankEntry(rank=1, title='Corporal', bonus=RankBonus(skill=Streetwise(), level=1)),
            2: RankEntry(rank=2, title='Sergeant'),
            3: RankEntry(rank=3, title='Detective'),
            4: RankEntry(rank=4, title='Lieutenant', bonus=RankBonus(skill=Investigate(), level=1)),
            5: RankEntry(rank=5, title='Chief', bonus=RankBonus(skill=Admin(), level=1)),
            6: RankEntry(rank=6, title='Commissioner', bonus=RankBonus(characteristic=Chars.SOC, level=1)),
        },
    },
    muster_out=MusterOutData(
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
    ),
    mishaps={
        1: MishapEntry(
            text='Severely injured. Alternatively, roll twice on the Injury table and take the lower result.',
            effects=[InjuryEffect(severity='severe')],
        ),
        2: MishapEntry(
            text=(
                'A criminal or other figure under investigation offers you a deal. Accept and you leave this career '
                'without further penalty (although you lose the Benefit roll as normal). Refuse and you must roll '
                'twice on the Injury table and take the lower result. You gain an Enemy and one level in any skill '
                'you choose.'
            ),
            defer_ejection=True,
            effects=[CareerDispatchEffect(type='agent_mishap_2_choice')],
        ),
        3: MishapEntry(
            text=(
                'An investigation goes critically wrong or leads to the top, ruining your career. Roll Advocate 8+. '
                'If you succeed, you may keep the Benefit roll from this term. If you roll 2, you must take the '
                'Prisoner career in your next term.'
            ),
            defer_ejection=True,
            effects=[CareerDispatchEffect(type='agent_mishap_3')],
        ),
        4: MishapEntry(
            text='You learn something you should not know and people want to kill you for it. Gain an Enemy and Deception 1.',
            effects=[GainEnemyEffect(), GainSkillEffect(skill=Deception(level=Level(value=1)))],
        ),
        5: MishapEntry(
            text=(
                'Your work ends up coming home with you and someone gets hurt. Choose one of your Contacts, Allies '
                'or family members and roll twice on the Injury table for them, taking the lower result.'
            ),
            defer_ejection=True,
            effects=[CareerDispatchEffect(type='agent_mishap_5_choice')],
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
            text=(
                'An investigation takes on a dangerous turn. Roll Investigate 8+ or Streetwise 8+. If you fail, '
                'roll on the Mishap table. If you succeed, increase one of these skills by one level — Deception, '
                'Jack-of-all-Trades, Persuade or Tactics.'
            ),
            effects=[CareerDispatchEffect(type='agent_event_3')],
        ),
        4: CareerEventEntry(
            text='You complete a mission for your superiors and are suitably rewarded. Gain DM+1 to any one Benefit roll from this career.',
            effects=[BenefitDmEffect(amount=1)],
        ),
        5: CareerEventEntry(
            text='You establish a network of contacts. Gain D3 Contacts.',
            effects=[GainConnectionsRolledEffect(connection_type=ConnectionKind.CONTACT, dice='d3')],
        ),
        6: CareerEventEntry(
            text='You are given advanced training in a specialist field. Roll EDU 8+ to increase any one skill you already have by one level.',
            effects=[CareerDispatchEffect(type='agent_event_6')],
        ),
        7: CareerEventEntry(
            text='Life Event. Roll on the Life Events table.',
            effects=[LifeEventEffect()],
        ),
        8: CareerEventEntry(
            text=(
                'You go undercover to investigate an enemy. Roll Deception 8+. If you succeed, roll immediately on '
                'the Rogue or Citizen Events table and make one roll on any Specialist skill table for that career. '
                'If you fail, roll immediately on the Rogue or Citizen Mishap table.'
            ),
            effects=[CareerDispatchEffect(type='agent_event_8')],
        ),
        9: CareerEventEntry(
            text='You go above and beyond the call of duty. Gain DM+2 to your next advancement roll.',
            effects=[AdvancementDmEffect(amount=2)],
        ),
        10: CareerEventEntry(
            text='You are given specialist training in vehicles. Gain one of Drive 1, Flyer 1, Pilot 1 or Gunner 1.',
            effects=[SkillChoiceEffect(options=['Drive', 'Flyer', 'Pilot', 'Gunner'], level=1)],
        ),
        11: CareerEventEntry(
            text='You are befriended by a senior agent. Either increase Investigate by one level or DM+4 to an advancement roll thanks to their aid.',
            effects=[CareerDispatchEffect(type='agent_event_11')],
        ),
        12: CareerEventEntry(
            text='Your efforts uncover a major conspiracy against your employers. You are automatically promoted.',
            effects=[AutoAdvanceEffect()],
        ),
    },
    draft_assignments=['Law Enforcement'],
)


# ── mishap 2: criminal deal ───────────────────────────────────────────────────


def _handle_agent_mishap_2(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=2,
            instruction=(
                'Accept (leave without further penalty, lose Benefit roll as normal) or Refuse '
                '(roll twice on Injury table take lower, gain Enemy, choose skill)?'
            ),
            options=['accept', 'refuse'],
        )
    )
    return pending_idx + 1


def _choice_agent_mishap_2(projection: CharacterProjection, event) -> None:
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
    pending_idx = 0
    if event.choice == 'refuse':
        projection.summary.connections.append(Enemy(source='Refused criminal deal (Agent mishap)'))
        projection.pending_inputs.append(
            PendingDoubleInjuryRoll(
                id=f'{event.id}.{pending_idx}',
                instruction='Refused: roll twice on the Injury table and provide both results — lower applies',
                options=['1', '2', '3', '4', '5', '6'],
            )
        )
        pending_idx += 1
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.{pending_idx}',
                instruction='Refused criminal deal: choose any skill to gain at level 1',
                options=[],
            )
        )
        pending_idx += 1
    _apply_mishap_ejection(projection, career, event.id, pending_idx, lose_current_term=True)


# ── mishap 3: investigation gone wrong ───────────────────────────────────────


def _handle_agent_mishap_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=3,
            context='agent_mishap_3',
            instruction='Roll Advocate 8+ to keep the Benefit roll from this term',
            options=['Advocate'],
        )
    )
    return pending_idx + 1


def _resolve_agent_mishap_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    from ceres.character.careers.loader import load_careers

    career_name = projection.summary.current_career
    career = load_careers().get(career_name or '')
    if career is None:
        return

    succeed = event.modified_roll >= 8
    if event.modified_roll <= 2:
        projection.forced_next_career = 'Prisoner'
    muster_out_setup(projection, career, event.id, 0, lose_current_term=not succeed)


# ── mishap 5: someone close gets hurt ────────────────────────────────────────


def _handle_agent_mishap_5(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerMishap(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=5,
            instruction='Choose who was hurt: a Contact, an Ally, or a family member?',
            options=['contact', 'ally', 'family'],
        )
    )
    return pending_idx + 1


def _choice_agent_mishap_5(projection: CharacterProjection, event) -> None:
    from ceres.character.events import _apply_mishap_ejection

    career = projection.get_current_career()
    projection.summary.problems.append(
        f'Agent mishap 5: your {event.choice} was hurt — roll twice on the Injury table for them '
        'and apply the lower result (NPC injury; no mechanical effect on your character).'
    )
    _apply_mishap_ejection(projection, career, event.id, 0, lose_current_term=True)


# ── event 3: dangerous investigation ─────────────────────────────────────────


def _handle_agent_event_3(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=3,
            context='agent_event_3',
            instruction='Roll Investigate 8+ or Streetwise 8+',
            options=['Investigate', 'Streetwise'],
        )
    )
    return pending_idx + 1


def _resolve_agent_event_3(projection: CharacterProjection, event: SkillRollEvent) -> None:
    if event.modified_roll >= 8:
        projection.pending_inputs.append(
            PendingSkillChoice(
                id=f'{event.id}.0',
                instruction=(
                    'Investigation success: increase one skill by one level — Deception, '
                    'Jack-of-all-Trades, Persuade or Tactics'
                ),
                options=['Deception', 'Jack-of-all-Trades', 'Persuade', 'Tactics'],
            )
        )
    else:
        projection.pending_inputs.append(
            PendingMishap(
                id=f'{event.id}.0',
                instruction='Investigation went wrong: roll 1D on Mishap table (you are not ejected from this career)',
            )
        )


# ── event 6: advanced training ───────────────────────────────────────────────


def _handle_agent_event_6(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    return handle_advanced_training('Agent', 6, 'agent_event_6', projection, effect, event_id, pending_idx)


def _resolve_agent_event_6(projection: CharacterProjection, event: SkillRollEvent) -> None:
    resolve_advanced_training(projection, event)


# ── event 8: undercover mission ──────────────────────────────────────────────


def _handle_agent_event_8(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillRoll(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=8,
            context='agent_event_8',
            instruction='Roll Deception 8+ for the undercover mission',
            options=['Deception'],
        )
    )
    return pending_idx + 1


def _resolve_agent_event_8(projection: CharacterProjection, event: SkillRollEvent) -> None:
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


# ── event 11: senior agent mentor ────────────────────────────────────────────


def _handle_agent_event_11(
    projection: CharacterProjection,
    effect: CareerDispatchEffect,
    event_id: int,
    pending_idx: int,
) -> int:
    projection.pending_inputs.append(
        PendingCareerSkillChoice(
            id=f'{event_id}.{pending_idx}',
            career='Agent',
            roll=11,
            advancement_precreated=False,
            instruction='Senior agent mentor: increase Investigate by one level or DM+4 to your next advancement roll',
            options=['Investigate', 'advancement_dm_4'],
        )
    )
    return pending_idx + 1


# ── handler registries ────────────────────────────────────────────────────────

CAREER_DATA_CLASS = AgentCareerData

EFFECT_HANDLERS: dict[str, object] = {
    'agent_mishap_2_choice': _handle_agent_mishap_2,
    'agent_mishap_3': _handle_agent_mishap_3,
    'agent_mishap_5_choice': _handle_agent_mishap_5,
    'agent_event_3': _handle_agent_event_3,
    'agent_event_6': _handle_agent_event_6,
    'agent_event_8': _handle_agent_event_8,
    'agent_event_11': _handle_agent_event_11,
}

SKILL_ROLL_HANDLERS: dict[str, object] = {
    'agent_mishap_3': _resolve_agent_mishap_3,
    'agent_event_3': _resolve_agent_event_3,
    'agent_event_6': _resolve_agent_event_6,
    'agent_event_8': _resolve_agent_event_8,
}

CHOICE_HANDLERS: dict[str, object] = {
    'agent_mishap_2': _choice_agent_mishap_2,
    'agent_mishap_5': _choice_agent_mishap_5,
}
