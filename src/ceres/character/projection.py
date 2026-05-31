from dataclasses import dataclass
import random
import re
from typing import Annotated, Any, Literal, cast, overload

from pydantic import BaseModel, Field

from ceres.adapters.travellermap import TravellerMapWorld
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
    ParoleRollEvent,
    ReenlistEvent,
    SkillChoiceEvent,
    SkillRollEvent,
    SkillTableEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.skills import AnySkill, Level, Skill, _level_fields, field_for_spec, skill_class_by_name
from ceres.character.sophonts import Sophont
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


class ReplayError(Exception):
    pass


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


class PendingParoleRoll(PendingInputBase):
    """Roll 1D to determine initial Parole Threshold when entering Prisoner career."""

    kind: Literal['parole_roll'] = 'parole_roll'


_CAREER_PHASE_PENDING_TYPES = (
    PendingSurvive,
    PendingTermEvent,
    PendingMishap,
    PendingAdvancement,
    PendingCommissionChoice,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingRankBonusChoice,
    PendingReenlist,
    PendingAssignmentChangeChoice,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillChoice,
    PendingCareerSkillRoll,
)


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
    | PendingPreCareerGraduation
    | PendingParoleRoll,
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
    name: str
    age: int = 18
    sophont: Sophont
    homeworld: TravellerMapWorld
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
    parole_threshold: int | None = None  # Prisoner career: current Parole Threshold (3-12)

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


class CharacterProjection(BaseModel):
    character_id: int
    summary: CharacterSummary
    pending_inputs: list[AnyPending] = Field(default_factory=list)
    scheduled_effects: list[ScheduledEffect] = Field(default_factory=list)
    pending_reenlist: bool | None = None  # stores reenlist decision during aging chain
    muster_out_career: str | None = None  # career name used to look up benefit table
    forced_next_career: str | None = None  # set by prison-sending events; consumed by next career choice
    prisoner_freed: bool = False  # set by _apply_prisoner_advancement when parole granted

    def has_blocking_pending(self) -> bool:
        return any(p.blocking for p in self.pending_inputs)

    def purge_career_pendings(self) -> None:
        """Remove pending inputs that require an active career and can no longer be fulfilled.

        Called when a career ends (mishap or reenlist=False) to clear inputs that were queued
        by prior career-phase processing and are now orphaned.
        """
        self.pending_inputs[:] = [p for p in self.pending_inputs if not isinstance(p, _CAREER_PHASE_PENDING_TYPES)]

    def clear_current_career(self) -> None:
        if self.summary.current_career is not None:
            self.summary.last_career = self.summary.current_career
            self.summary.last_assignment = self.summary.current_assignment
        self.summary.current_career = None
        self.summary.current_assignment = None

    def get_current_career(self) -> CareerData:
        from ceres.character.careers.loader import load_careers

        career_name = self.summary.current_career
        if career_name is None:
            raise ReplayError('No active career')
        careers = load_careers()
        career = careers.get(career_name)
        if career is None:
            raise ReplayError(f'Unknown career: {career_name!r}')
        return career

    def fulfill_pending(self, event: Any) -> None:
        fulfills = event.fulfills
        matched = next((p for p in self.pending_inputs if p.id == fulfills), None)
        if matched is None:
            raise ReplayError(f'Event {event.id} ({event.kind!r}) references unknown pending input {fulfills!r}')
        self.pending_inputs.remove(matched)

    def queue_career_choice_indexed(
        self, event_id: int, idx: int, instruction: str = 'Choose a career'
    ) -> None:
        from ceres.character.careers.loader import selectable_careers

        if self.forced_next_career:
            career_name = self.forced_next_career
            self.forced_next_career = None
            self.pending_inputs.append(
                PendingCareerChoice(
                    id=f'{event_id}.{idx}',
                    instruction=f'Next career: {career_name} (mandatory)',
                    options=[career_name],
                )
            )
        else:
            career_options = sorted(selectable_careers(self).keys())
            self.pending_inputs.append(
                PendingCareerChoice(
                    id=f'{event_id}.{idx}',
                    instruction=instruction,
                    options=career_options,
                )
            )

    def queue_career_choice(self, event_id: int, instruction: str = 'Choose a career') -> None:
        self.queue_career_choice_indexed(event_id, 0, instruction)

    def queue_reenlist_or_aging(self, event_id: int, idx: int) -> None:
        from ceres.character.careers.loader import load_careers

        if self.prisoner_freed:
            self.prisoner_freed = False
            self.summary.age += 4
            career_name = self.summary.current_career
            careers = load_careers()
            career = careers.get(career_name) if career_name else None
            if self.summary.age >= 34:
                if career:
                    self.muster_out_career = career.name
                self.pending_reenlist = False
                self.clear_current_career()
                self.pending_inputs.append(
                    PendingAgingRoll(id=f'{event_id}.{idx}', instruction='Roll 2D on Aging table')
                )
            elif career:
                self.muster_out_setup(career, event_id, idx, lose_current_term=False)
            return

        self.summary.age += 4
        if self.summary.age >= 34:
            self.pending_inputs.append(PendingAgingRoll(id=f'{event_id}.{idx}', instruction='Roll 2D on Aging table'))
        else:
            career = self.get_current_career() if self.summary.current_career else None
            if career and career.allows_assignment_change and len(career.assignments) > 1:
                current = self.summary.current_assignment or ''
                others = [a.name for a in career.assignments if a.name != current]
                options = ['same', *others]
                if career.name != 'Prisoner':
                    options.append('muster_out')
                self.pending_inputs.append(
                    PendingAssignmentChangeChoice(
                        id=f'{event_id}.{idx}',
                        instruction='Reenlist same assignment, switch assignment, or muster out?',
                        options=options,
                    )
                )
            else:
                self.pending_inputs.append(
                    PendingReenlist(
                        id=f'{event_id}.{idx}',
                        instruction='Reenlist or muster out?',
                        options=['true', 'false'],
                    )
                )

    def muster_out_setup(
        self,
        career: CareerData,
        source_event_id: int,
        pending_idx: int = 0,
        lose_current_term: bool = False,
        clear_career: bool = True,
    ) -> int:
        roll_count = self.summary.term_count + (self.summary.rank or 0) // 2
        if lose_current_term:
            roll_count = max(0, roll_count - 1)
        reduce_effects = [se for se in self.scheduled_effects if se.trigger == 'muster_out_reduce' and se.consume]
        for se in reduce_effects:
            roll_count = max(0, roll_count - se.effect.get('value', 1))
            self.scheduled_effects.remove(se)
        add_effects = [se for se in self.scheduled_effects if se.trigger == 'muster_out_add' and se.consume]
        for se in add_effects:
            roll_count += se.effect.get('value', 1)
            self.scheduled_effects.remove(se)
        if clear_career:
            self.clear_current_career()
        if roll_count > 0:
            self.muster_out_career = career.name
            for _ in range(roll_count):
                self.pending_inputs.append(
                    PendingMusterOut(
                        id=f'{source_event_id}.{pending_idx}',
                        instruction='Muster out: choose cash or benefits table',
                        options=['cash', 'benefits'],
                    )
                )
                pending_idx += 1
        else:
            self.queue_career_choice_indexed(source_event_id, pending_idx)
            pending_idx += 1
        return pending_idx

    def complete_aging(self, source_event_id: int) -> None:
        from ceres.character.careers.loader import load_careers

        if self.muster_out_career is not None:
            careers = load_careers()
            career = careers.get(self.muster_out_career)
            lose = self.pending_reenlist is None
            self.muster_out_career = None
            if career:
                self.muster_out_setup(career, source_event_id, 0, lose_current_term=lose, clear_career=False)
        else:
            career = self.get_current_career() if self.summary.current_career else None
            if career and career.allows_assignment_change and len(career.assignments) > 1:
                current = self.summary.current_assignment or ''
                others = [a.name for a in career.assignments if a.name != current]
                self.pending_inputs.append(
                    PendingAssignmentChangeChoice(
                        id=f'{source_event_id}.0',
                        instruction='Reenlist same assignment, switch assignment, or muster out?',
                        options=['same', *others, 'muster_out'],
                    )
                )
            else:
                self.pending_inputs.append(
                    PendingReenlist(
                        id=f'{source_event_id}.0',
                        instruction='Reenlist or muster out?',
                        options=['true', 'false'],
                    )
                )
        self.pending_reenlist = None

    def check_aging_crisis(self, source_event_id: int) -> bool:
        if any(v == 0 for v in self.summary.characteristics.values()):
            self.pending_inputs = [
                p
                for p in self.pending_inputs
                if not isinstance(p, (PendingAgingChoice, PendingAgingChoiceMental))
            ]
            self.pending_inputs.append(
                PendingAgingCrisis(
                    id=f'{source_event_id}.crisis',
                    instruction='Aging crisis: pay for medical care or die?',
                    options=['pay', 'die'],
                )
            )
            return True
        return False

    def career_progress_pending(
        self, career: CareerData, event_id: int, pending_idx: int = 0
    ) -> PendingAdvancement | PendingCommissionChoice:
        if career.can_attempt_commission(self):
            commission = career.commission
            if commission is None:
                raise ReplayError(f'{career.name} can attempt commission without commission rules')
            return PendingCommissionChoice(
                id=f'{event_id}.{pending_idx}',
                instruction=f'Attempt commission ({commission.characteristic} {commission.target}+) or roll advancement?',
                options=['attempt', 'skip'],
            )
        assignment_name = self.summary.current_assignment or ''
        assignment = career.assignment(assignment_name)
        if assignment is None:
            raise ReplayError(f'Unknown assignment {assignment_name!r}')
        char = assignment.advancement.characteristic
        target = assignment.advancement.target
        return PendingAdvancement(id=f'{event_id}.{pending_idx}', instruction=f'Advancement: {char} {target}+')

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
                current = getattr(existing, fields[0]).value if existing is not None else None
                if level is None:
                    if current is None or current < 4:
                        new_level = 1 if current is None else current + 1
                        choices.append(cast(AnySkill, _cls(level=Level(value=new_level))))
                else:
                    actual = current if current is not None else -1
                    if actual < level:
                        choices.append(cast(AnySkill, _cls(level=Level(value=level))))
            # Specialised skill
            elif level == 0:
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

    def grant_skill(self, skill: AnySkill) -> None:
        skill_cls = type(skill)
        existing = next((s for s in self.summary.skills if type(s) is skill_cls), None)
        if existing is None:
            self.summary.skills.append(skill_cls())
            existing = self.summary.skills[-1]
        for field in _level_fields(skill_cls):
            given = getattr(skill, field).value
            if given > 0:
                current = getattr(existing, field).value
                getattr(existing, field).set(max(current, given))

    def increment_skill(self, skill_name: str, spec: str | None = None) -> None:
        from typing import cast as _cast

        skill_cls = skill_class_by_name(skill_name)
        existing = next((s for s in self.summary.skills if type(s) is skill_cls), None)
        fields = _level_fields(skill_cls)
        target_field = field_for_spec(skill_cls, spec) if spec is not None else (fields[0] if fields else None)
        if existing is None:
            new_skill = skill_cls()
            if target_field:
                getattr(new_skill, target_field).set(1)
            self.summary.skills.append(_cast(AnySkill, new_skill))
            return
        if (spec is not None or len(fields) == 1) and target_field:
            current = getattr(existing, target_field).value
            if current < 4:
                getattr(existing, target_field).set(current + 1)

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
                sophont = self.summary.sophont
                n = len(sophont.ucp_stats) if sophont is not None else 6
                ucp = ''.join(f'{_roll2d(rng):X}' for _ in range(n))
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
                # If options is restricted (e.g. forced career), respect it
                available = pi.options or sorted(ctx.careers.keys())
                career_data = None
                if ctx.career in available:
                    career_data = ctx.careers.get(ctx.career)
                if career_data is None:
                    from ceres.character.careers.loader import load_careers as _load_careers

                    all_careers = _load_careers()
                    chosen_name = rng.choice(available) if available else rng.choice(sorted(ctx.careers.keys()))
                    career_data = all_careers.get(chosen_name) or ctx.careers.get(chosen_name)
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
                if 'muster_out' in pi.options:
                    return AssignmentChangeChoiceEvent(choice='muster_out', fulfills=pi.id)
                return AssignmentChangeChoiceEvent(choice='same', fulfills=pi.id)

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

            case PendingParoleRoll():
                return ParoleRollEvent(roll=_roll1d(rng), fulfills=pi.id)

            case PendingPreCareerSkillChoice():
                skill_name = rng.choice(pi.options) if pi.options else 'Admin'
                from ceres.character.events import PreCareerSkillChoiceEvent

                return PreCareerSkillChoiceEvent(skill=skill_name, fulfills=pi.id)

            case PendingPreCareerEvent():
                from ceres.character.events import PreCareerEventEvent

                return PreCareerEventEvent(roll=_roll2d(rng), fulfills=pi.id)

            case PendingPreCareerGraduation():
                from ceres.character.events import PreCareerGraduationEvent

                return PreCareerGraduationEvent(roll=_roll2d(rng), fulfills=pi.id)

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
    'PendingAdvancement',
    'PendingAgingChoice',
    'PendingAgingChoiceMental',
    'PendingAgingCrisis',
    'PendingAgingRoll',
    'PendingAssignmentChangeChoice',
    'PendingBackgroundSkills',
    'PendingBenefitChoice',
    'PendingCareerChoice',
    'PendingCareerEvent',
    'PendingCareerMishap',
    'PendingCareerSkillChoice',
    'PendingCareerSkillRoll',
    'PendingCharacteristicChoice',
    'PendingCommissionChoice',
    'PendingConnectionsRoll',
    'PendingDoubleInjuryRoll',
    'PendingDraftAssignmentChoice',
    'PendingDraftChoice',
    'PendingInitialTrainingChoice',
    'PendingInjuryTable',
    'PendingInputBase',
    'PendingLifeEvent',
    'PendingLifeEventChoice',
    'PendingLifeEventUnusual',
    'PendingMishap',
    'PendingMusterOut',
    'PendingNearlyKilled',
    'PendingParoleRoll',
    'PendingRankBonusChoice',
    'PendingReenlist',
    'PendingSkillChoice',
    'PendingSkillTable',
    'PendingSkillTableChoice',
    'PendingSurvive',
    'PendingTermEvent',
    'PendingUcp',
    'Rival',
    'ScheduledEffect',
    'make_connection',
]
