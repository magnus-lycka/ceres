from dataclasses import dataclass
import random
import re
from typing import Annotated, Any, Literal, cast, overload

from pydantic import BaseModel, Field

from ceres.character.benefits import AnyBenefit, ItemBenefit
from ceres.character.careers.career_data import CareerData
from ceres.character.characteristics import Chars, ConnectionKind
from ceres.character.events import (
    AdvancementDmChoiceEvent,
    AdvancementEvent,
    AgingCrisisEvent,
    AgingRollEvent,
    AnyEvent,
    AssignmentChangeChoiceEvent,
    BackgroundSkillsEvent,
    BenefitChoiceEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacteristicChoiceEvent,
    CommissionEvent,
    ConnectionKindChoiceEvent,
    ConnectionsRollEvent,
    DoubleInjuryTableEvent,
    DraftAssignmentEvent,
    DraftEvent,
    FinishCreationEvent,
    InjuryTableEvent,
    LifeEventEvent,
    LifeEventUnusualEvent,
    MishapEvent,
    MusterOutEvent,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.skills import AnySkill, Level, Skill, skill_class_by_name
from ceres.shared import CeresModel

_CHOOSE_COUNT_RE = re.compile(r'Choose (\d+)')


def _roll2d(rng: random.Random) -> int:
    return rng.randint(1, 6) + rng.randint(1, 6)


def _roll1d(rng: random.Random) -> int:
    return rng.randint(1, 6)


@dataclass(frozen=True)
class AutoFillContext:
    career: str
    assignment: str | None
    max_terms: int
    careers: dict[str, CareerData]


class PendingInputBase(BaseModel):
    id: str
    kind: str
    instruction: str
    options: list[str] = Field(default_factory=list)
    blocking: bool = True


class PendingUcp(PendingInputBase):
    kind: Literal['ucp'] = 'ucp'


class PendingBackgroundSkills(PendingInputBase):
    kind: Literal['background_skills'] = 'background_skills'


class PendingCareerChoice(PendingInputBase):
    kind: Literal['career_choice'] = 'career_choice'


class PendingDraftChoice(PendingInputBase):
    kind: Literal['draft_choice'] = 'draft_choice'


class PendingDraftAssignmentChoice(PendingInputBase):
    kind: Literal['draft_assignment_choice'] = 'draft_assignment_choice'
    career: str


class PendingSurvive(PendingInputBase):
    kind: Literal['survive'] = 'survive'


class PendingTermEvent(PendingInputBase):
    kind: Literal['term_event'] = 'term_event'


class PendingMishap(PendingInputBase):
    kind: Literal['mishap'] = 'mishap'


class PendingAdvancement(PendingInputBase):
    kind: Literal['advancement'] = 'advancement'


class PendingCommissionChoice(PendingInputBase):
    kind: Literal['commission_choice'] = 'commission_choice'


class PendingSkillTable(PendingInputBase):
    kind: Literal['skill_table'] = 'skill_table'


class PendingReenlist(PendingInputBase):
    kind: Literal['reenlist'] = 'reenlist'


class PendingAssignmentChangeChoice(PendingInputBase):
    """End-of-term choice for careers that allow intra-career assignment changes.

    options: ['same', 'muster_out', *other_assignment_names]
    Resolved by AssignmentChangeChoiceEvent.
    """

    kind: Literal['assignment_change_choice'] = 'assignment_change_choice'


class PendingMusterOut(PendingInputBase):
    kind: Literal['muster_out'] = 'muster_out'


class PendingSkillChoice(PendingInputBase):
    kind: Literal['skill_choice'] = 'skill_choice'


class PendingInitialTrainingChoice(PendingInputBase):
    kind: Literal['initial_training_choice'] = 'initial_training_choice'


class PendingSkillTableChoice(PendingInputBase):
    kind: Literal['skill_table_choice'] = 'skill_table_choice'
    reenlist_queued: bool = False  # True when reenlist/aging already queued (end-of-term path)


class PendingRankBonusChoice(PendingInputBase):
    kind: Literal['rank_bonus_choice'] = 'rank_bonus_choice'
    level: int


class PendingCharacteristicChoice(PendingInputBase):
    kind: Literal['characteristic_choice'] = 'characteristic_choice'


class PendingNearlyKilled(PendingInputBase):
    kind: Literal['nearly_killed'] = 'nearly_killed'


class PendingInjuryTable(PendingInputBase):
    kind: Literal['injury_table'] = 'injury_table'


class PendingDoubleInjuryRoll(PendingInputBase):
    """Roll 1D twice; system takes the lower result and applies Injury table."""

    kind: Literal['double_injury_roll'] = 'double_injury_roll'


class PendingBenefitChoice(PendingInputBase):
    """Player must pick one option from a ChoiceBenefit muster-out row."""

    kind: Literal['benefit_choice_pending'] = 'benefit_choice_pending'
    benefit_options: list[AnyBenefit]


class PendingAgingRoll(PendingInputBase):
    kind: Literal['aging_roll'] = 'aging_roll'


class PendingAgingChoice(PendingInputBase):
    kind: Literal['aging_choice'] = 'aging_choice'


class PendingAgingChoiceMental(PendingInputBase):
    kind: Literal['aging_choice_mental'] = 'aging_choice_mental'


class PendingAgingCrisis(PendingInputBase):
    kind: Literal['aging_crisis'] = 'aging_crisis'


class PendingLifeEvent(PendingInputBase):
    kind: Literal['life_event'] = 'life_event'


class PendingLifeEventChoice(PendingInputBase):
    """Life event that requires a connection kind choice (rolls 4 and 8)."""

    kind: Literal['life_event_choice'] = 'life_event_choice'
    roll: int


class PendingLifeEventUnusual(PendingInputBase):
    kind: Literal['life_event_unusual'] = 'life_event_unusual'


class PendingConnectionsRoll(PendingInputBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind = ConnectionKind.CONTACT


class PendingCareerEvent(PendingInputBase):
    """Career-specific event requiring player input; career+roll identifies the exact event."""

    kind: Literal['career_event'] = 'career_event'
    career: str
    roll: int


class PendingCareerMishap(PendingInputBase):
    """Career-specific mishap requiring player input; career+roll identifies the exact mishap."""

    kind: Literal['career_mishap'] = 'career_mishap'
    career: str
    roll: int


class PendingCareerSkillChoice(PendingInputBase):
    """Skill choice triggered by a career event or mishap."""

    kind: Literal['career_skill_choice'] = 'career_skill_choice'
    career: str
    roll: int
    mishap: bool = False
    advancement_precreated: bool = False


class PendingCareerSkillRoll(PendingInputBase):
    """Skill roll required by a specific career event; context matches SkillRollEvent.context."""

    kind: Literal['career_skill_roll'] = 'career_skill_roll'
    career: str
    roll: int
    context: str


class PendingPreCareerSkillChoice(PendingInputBase):
    """University: choose one skill at the given level (0 or 1) from the pre-career skill list."""

    kind: Literal['precareer_skill_choice'] = 'precareer_skill_choice'
    level: int


class PendingPreCareerEvent(PendingInputBase):
    """Roll 2D on the Pre-career Events table."""

    kind: Literal['precareer_event'] = 'precareer_event'


class PendingPreCareerGraduation(PendingInputBase):
    """Roll 2D for graduation from pre-career education."""

    kind: Literal['precareer_graduation'] = 'precareer_graduation'


type AnyPending = Annotated[
    PendingUcp
    | PendingBackgroundSkills
    | PendingCareerChoice
    | PendingDraftChoice
    | PendingDraftAssignmentChoice
    | PendingSurvive
    | PendingTermEvent
    | PendingMishap
    | PendingAdvancement
    | PendingCommissionChoice
    | PendingSkillTable
    | PendingReenlist
    | PendingAssignmentChangeChoice
    | PendingMusterOut
    | PendingSkillChoice
    | PendingInitialTrainingChoice
    | PendingSkillTableChoice
    | PendingRankBonusChoice
    | PendingCharacteristicChoice
    | PendingNearlyKilled
    | PendingInjuryTable
    | PendingDoubleInjuryRoll
    | PendingBenefitChoice
    | PendingAgingRoll
    | PendingAgingChoice
    | PendingAgingChoiceMental
    | PendingAgingCrisis
    | PendingLifeEvent
    | PendingLifeEventChoice
    | PendingLifeEventUnusual
    | PendingConnectionsRoll
    | PendingCareerEvent
    | PendingCareerMishap
    | PendingCareerSkillChoice
    | PendingCareerSkillRoll
    | PendingPreCareerSkillChoice
    | PendingPreCareerEvent
    | PendingPreCareerGraduation,
    Field(discriminator='kind'),
]


class ScheduledEffect(BaseModel):
    trigger: str
    source_event_id: int
    effect: dict = Field(default_factory=dict)
    expires: str | None = None
    consume: bool = True


class Connection(CeresModel):
    """Base class for character connections (contacts, allies, rivals, enemies)."""

    source: str = ''  # how/when this person entered the character's life
    power: int | None = None  # 1-6: degree of power or influence
    affinity: int | None = None  # 0-6: degree of affinity towards the Traveller
    enmity: int | None = None  # 0 to -6: degree of enmity towards the Traveller


class Contact(Connection):
    kind: Literal['contact'] = 'contact'


class Ally(Connection):
    kind: Literal['ally'] = 'ally'


class Rival(Connection):
    kind: Literal['rival'] = 'rival'


class Enemy(Connection):
    kind: Literal['enemy'] = 'enemy'


type AnyConnection = Annotated[
    Contact | Ally | Rival | Enemy,
    Field(discriminator='kind'),
]


def _affinity_enmity_value(roll: int, *, enmity: bool = False) -> int:
    if roll <= 2:
        value = 0
    elif roll <= 4:
        value = 1
    elif roll <= 6:
        value = 2
    elif roll <= 8:
        value = 3
    elif roll <= 10:
        value = 4
    elif roll == 11:
        value = 5
    else:
        value = 6
    return -value if enmity else value


def _connection_affinity_enmity(
    kind: ConnectionKind,
    affinity_roll: int | None,
    enmity_roll: int | None,
) -> tuple[int | None, int | None]:
    if affinity_roll is None and enmity_roll is None:
        return None, None

    match kind:
        case ConnectionKind.ALLY:
            affinity = _affinity_enmity_value(affinity_roll) if affinity_roll is not None else None
            return affinity, 0
        case ConnectionKind.CONTACT:
            affinity = _affinity_enmity_value(affinity_roll) if affinity_roll is not None else None
            enmity = _affinity_enmity_value(enmity_roll, enmity=True) if enmity_roll is not None else None
            return affinity, enmity
        case ConnectionKind.RIVAL:
            affinity = _affinity_enmity_value(affinity_roll) if affinity_roll is not None else None
            enmity = _affinity_enmity_value(enmity_roll, enmity=True) if enmity_roll is not None else None
            return affinity, enmity
        case ConnectionKind.ENEMY:
            enmity = _affinity_enmity_value(enmity_roll, enmity=True) if enmity_roll is not None else None
            return 0, enmity


def make_connection(
    kind: ConnectionKind,
    source: str = '',
    power: int | None = None,
    affinity_roll: int | None = None,
    enmity_roll: int | None = None,
) -> AnyConnection:
    affinity, enmity = _connection_affinity_enmity(kind, affinity_roll, enmity_roll)
    match kind:
        case ConnectionKind.CONTACT:
            return Contact(source=source, power=power, affinity=affinity, enmity=enmity)
        case ConnectionKind.ALLY:
            return Ally(source=source, power=power, affinity=affinity, enmity=enmity)
        case ConnectionKind.RIVAL:
            return Rival(source=source, power=power, affinity=affinity, enmity=enmity)
        case ConnectionKind.ENEMY:
            return Enemy(source=source, power=power, affinity=affinity, enmity=enmity)


class CareerTerm(BaseModel):
    career: str
    assignment: str
    commission: bool = False
    rank_after_term: int = 0


class CharacterSummary(BaseModel):
    name: str | None = None
    age: int = 18
    species: str | None = None
    characteristics: dict[Chars, int] = Field(default_factory=dict)
    current_career: str | None = None
    current_assignment: str | None = None
    last_career: str | None = None  # career name after muster-out
    last_assignment: str | None = None  # assignment name after muster-out
    rank: int | None = None
    term_count: int = 0
    career_terms: list[CareerTerm] = Field(default_factory=list)
    drafted: bool = False
    skills: list[AnySkill] = Field(default_factory=list)
    connections: list[AnyConnection] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    narrative: list[str] = Field(default_factory=list)
    cash: int = 0
    benefits: list[ItemBenefit] = Field(default_factory=list)
    muster_out_cash_count: int = 0
    dead: bool = False
    precareer: str | None = None  # pre-career currently in progress
    precareer_completed: str | None = None  # pre-career that was attended (whether graduated or not)
    precareer_skills: list[str] = Field(default_factory=list)  # skills chosen during university (for graduation boost)

    @overload
    def skill_level(self, name: str, default: int) -> int: ...
    @overload
    def skill_level(self, name: str, default: None = None) -> int | None: ...
    def skill_level(self, name: str, default: int | None = None) -> int | None:
        for skill in self.skills:
            if type(skill).name() == name:
                fields = _level_fields(type(skill))
                if not fields:
                    return 0
                return max(getattr(skill, f).value for f in fields)
        return default


def _level_fields(skill_cls: type[Skill]) -> list[str]:
    return [
        name
        for name, field in skill_cls.model_fields.items()
        if name not in {'type', 'display_label'} and field.annotation is Level
    ]


class CharacterProjection(BaseModel):
    character_id: int
    summary: CharacterSummary = Field(default_factory=CharacterSummary)
    pending_inputs: list[AnyPending] = Field(default_factory=list)
    scheduled_effects: list[ScheduledEffect] = Field(default_factory=list)
    pending_reenlist: bool | None = None  # stores reenlist decision during aging chain
    muster_out_career: str | None = None  # career name used to look up benefit table

    def skill_choices(
        self,
        skill_types: list[type[Skill]],
        level: int | None,
    ) -> list[AnySkill]:
        choices: list[AnySkill] = []
        for skill_cls in skill_types:
            existing = next((s for s in self.summary.skills if type(s) is skill_cls), None)
            fields = _level_fields(skill_cls)
            _cls: Any = skill_cls
            if len(fields) == 1 and fields[0] == 'level':
                # Non-specialised skill
                current = getattr(existing, 'level').value if existing is not None else None
                if level is None:
                    if current is None or current < 4:
                        new_level = 1 if current is None else current + 1
                        choices.append(cast(AnySkill, _cls(level=Level(value=new_level))))
                else:
                    actual = current if current is not None else -1
                    if actual < level:
                        choices.append(cast(AnySkill, _cls(level=Level(value=level))))
            else:
                # Specialised skill
                if level == 0:
                    # Level-0 grant adds the whole type if absent
                    if existing is None:
                        choices.append(cast(AnySkill, _cls()))
                elif level is None:
                    # Increment — one choice per specialization field
                    for field in fields:
                        current = getattr(existing, field).value if existing is not None else 0
                        if current < 4:
                            choices.append(cast(AnySkill, _cls(**{field: Level(value=current + 1)})))
                else:
                    # Fixed level > 0 — one choice per spec currently below target
                    for field in fields:
                        current = getattr(existing, field).value if existing is not None else 0
                        if current < level:
                            choices.append(cast(AnySkill, _cls(**{field: Level(value=level)})))
        return choices

    def check_skill_choice(
        self,
        skill_types: list[type[Skill]],
        level: int | None,
        choice: AnySkill,
    ) -> bool:
        return choice in self.skill_choices(skill_types, level)

    def _pick_skill_auto(self, options: list[str], rng: random.Random, level: int | None) -> AnySkill | None:
        valid = [o for o in options if o != 'advancement_dm_4']
        rng.shuffle(valid)
        for name in valid:
            try:
                cls = skill_class_by_name(name)
            except ValueError:
                continue
            choices = self.skill_choices([cls], level)
            if choices:
                return rng.choice(choices)
        return None

    def auto_event(self, pi: AnyPending, ctx: AutoFillContext, rng: random.Random) -> AnyEvent:
        """Generate a random event to auto-fulfill a pending input."""
        match pi:
            case PendingUcp():
                ucp = ''.join(f'{_roll2d(rng):X}' for _ in range(6))
                return UcpEvent(ucp=ucp, fulfills=pi.id)

            case PendingBackgroundSkills():
                m = _CHOOSE_COUNT_RE.search(pi.instruction)
                count = int(m.group(1)) if m else 3
                shuffled = list(pi.options)
                rng.shuffle(shuffled)
                skills: list[AnySkill] = []
                for name in shuffled:
                    if len(skills) >= count:
                        break
                    try:
                        cls = skill_class_by_name(name)
                        skills.append(cast(AnySkill, cls()))
                    except ValueError:
                        pass
                return BackgroundSkillsEvent(skills=skills, fulfills=pi.id)

            case PendingCareerChoice():
                if self.summary.term_count >= ctx.max_terms:
                    return FinishCreationEvent(fulfills=pi.id)
                career_data = ctx.careers.get(ctx.career)
                if career_data is None:
                    career_data = ctx.careers[rng.choice(sorted(ctx.careers.keys()))]
                if ctx.assignment and any(a.name == ctx.assignment for a in career_data.assignments):
                    assignment = ctx.assignment
                else:
                    assignment = rng.choice([a.name for a in career_data.assignments])
                return CareerEvent(
                    career=career_data.name,
                    assignment=assignment,
                    qualification_roll=12,
                    fulfills=pi.id,
                )

            case PendingDraftChoice():
                draft_careers = [career for career in ctx.careers.values() if career.does_draft()]
                career = rng.choice(draft_careers)
                return DraftEvent(career=career.name, fulfills=pi.id)

            case PendingDraftAssignmentChoice():
                return DraftAssignmentEvent(
                    career=pi.career,
                    assignment=rng.choice(pi.options),
                    fulfills=pi.id,
                )

            case PendingSurvive():
                return SurviveEvent(roll=_roll2d(rng), fulfills=pi.id)

            case PendingTermEvent():
                return TermEventEvent(roll=_roll2d(rng), fulfills=pi.id)

            case PendingMishap():
                return MishapEvent(roll=_roll1d(rng), fulfills=pi.id)

            case PendingAdvancement():
                return AdvancementEvent(roll=_roll2d(rng), fulfills=pi.id)

            case PendingCommissionChoice():
                return CommissionEvent(attempt=False, fulfills=pi.id)

            case PendingSkillTable():
                table = rng.choice(pi.options) if pi.options else 'service_skills'
                return SkillTableEvent(table=table, roll=_roll1d(rng), fulfills=pi.id)

            case PendingInitialTrainingChoice():
                skill = self._pick_skill_auto(pi.options, rng, 0)
                if skill is not None:
                    return SkillChoiceEvent(skill=skill, fulfills=pi.id)
                return AdvancementDmChoiceEvent(fulfills=pi.id)

            case PendingSkillTableChoice() | PendingSkillChoice():
                skill = self._pick_skill_auto(pi.options, rng, None)
                if skill is not None:
                    return SkillChoiceEvent(skill=skill, fulfills=pi.id)
                return AdvancementDmChoiceEvent(fulfills=pi.id)

            case PendingRankBonusChoice():
                skill = self._pick_skill_auto(pi.options, rng, pi.level)
                if skill is not None:
                    return SkillChoiceEvent(skill=skill, fulfills=pi.id)
                return AdvancementDmChoiceEvent(fulfills=pi.id)

            case PendingCareerSkillChoice():
                skill = self._pick_skill_auto(pi.options, rng, None)
                if skill is not None:
                    return SkillChoiceEvent(skill=skill, fulfills=pi.id)
                return AdvancementDmChoiceEvent(fulfills=pi.id)

            case PendingReenlist():
                return ReenlistEvent(reenlist=self.summary.term_count < ctx.max_terms, fulfills=pi.id)

            case PendingAssignmentChangeChoice():
                if self.summary.term_count < ctx.max_terms:
                    return AssignmentChangeChoiceEvent(choice='same', fulfills=pi.id)
                return AssignmentChangeChoiceEvent(choice='muster_out', fulfills=pi.id)

            case PendingMusterOut():
                tables: list[Literal['cash', 'benefits']] = ['cash', 'benefits']
                return MusterOutEvent(table=rng.choice(tables), roll=_roll1d(rng), fulfills=pi.id)

            case PendingAgingRoll():
                return AgingRollEvent(roll=_roll2d(rng), fulfills=pi.id)

            case PendingNearlyKilled() | PendingInjuryTable():
                return InjuryTableEvent(roll=_roll1d(rng), fulfills=pi.id)

            case PendingDoubleInjuryRoll():
                return DoubleInjuryTableEvent(roll1=_roll1d(rng), roll2=_roll1d(rng), fulfills=pi.id)

            case PendingBenefitChoice():
                return BenefitChoiceEvent(
                    choice_index=rng.randint(0, len(pi.benefit_options) - 1),
                    fulfills=pi.id,
                )

            case PendingLifeEvent():
                return LifeEventEvent(roll=_roll2d(rng), fulfills=pi.id)

            case PendingLifeEventUnusual():
                return LifeEventUnusualEvent(roll=_roll1d(rng), fulfills=pi.id)

            case PendingConnectionsRoll():
                return ConnectionsRollEvent(
                    connection_type=pi.connection_type,
                    count=_roll1d(rng),
                    fulfills=pi.id,
                )

            case PendingCharacteristicChoice() | PendingAgingChoice() | PendingAgingChoiceMental():
                char = rng.choice(pi.options) if pi.options else 'STR'
                return CharacteristicChoiceEvent(characteristic=Chars(char), fulfills=pi.id)

            case PendingLifeEventChoice():
                return ConnectionKindChoiceEvent(connection_kind=rng.choice(list(ConnectionKind)), fulfills=pi.id)

            case PendingAgingCrisis():
                return AgingCrisisEvent(paid=False, medical_roll=0, fulfills=pi.id)

            case PendingCareerEvent():
                context = f'{pi.career.lower()}_event_{pi.roll}'
                choice = rng.choice(list(pi.options)) if pi.options else ''
                return CareerChoiceEvent(context=context, choice=choice, fulfills=pi.id)

            case PendingCareerMishap():
                context = f'{pi.career.lower()}_mishap_{pi.roll}'
                choice = rng.choice(list(pi.options)) if pi.options else ''
                return CareerChoiceEvent(context=context, choice=choice, fulfills=pi.id)

            case PendingCareerSkillRoll():
                skill_str = rng.choice(pi.options) if pi.options else 'Admin'
                try:
                    auto_skill: AnySkill | Chars = Chars(skill_str)
                except ValueError:
                    auto_skill = cast(AnySkill, skill_class_by_name(skill_str)())
                return SkillRollEvent(context=pi.context, skill=auto_skill, modified_roll=_roll2d(rng), fulfills=pi.id)

            case _:
                raise ValueError(f'No auto_event handler for {type(pi).__name__!r}')


__all__ = [
    'Ally',
    'AnyConnection',
    'AnyPending',
    'AutoFillContext',
    'CareerTerm',
    'CharacterProjection',
    'CharacterSummary',
    'Connection',
    'Contact',
    'Enemy',
    'make_connection',
    'PendingAdvancement',
    'PendingAssignmentChangeChoice',
    'Rival',
    'PendingAgingChoice',
    'PendingAgingChoiceMental',
    'PendingAgingCrisis',
    'PendingAgingRoll',
    'PendingBackgroundSkills',
    'PendingBenefitChoice',
    'PendingCareerChoice',
    'PendingCommissionChoice',
    'PendingCareerEvent',
    'PendingCareerMishap',
    'PendingCareerSkillChoice',
    'PendingCareerSkillRoll',
    'PendingCharacteristicChoice',
    'PendingConnectionsRoll',
    'PendingDoubleInjuryRoll',
    'PendingDraftAssignmentChoice',
    'PendingDraftChoice',
    'PendingInitialTrainingChoice',
    'PendingInputBase',
    'PendingInjuryTable',
    'PendingLifeEvent',
    'PendingLifeEventChoice',
    'PendingLifeEventUnusual',
    'PendingMishap',
    'PendingMusterOut',
    'PendingNearlyKilled',
    'PendingRankBonusChoice',
    'PendingReenlist',
    'PendingSkillChoice',
    'PendingSkillTable',
    'PendingSkillTableChoice',
    'PendingSurvive',
    'PendingTermEvent',
    'PendingUcp',
    'ScheduledEffect',
]
