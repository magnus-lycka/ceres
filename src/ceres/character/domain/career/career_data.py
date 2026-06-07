from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.functional_validators import ModelWrapValidatorHandler

from ceres.character.domain.benefits import AnyBenefit, ItemBenefit
from ceres.character.domain.characteristics import Chars, ConnectionKind, characteristic_dm
from ceres.character.domain.skills import AnySkill, Level, _level_fields
from ceres.character.mechanism.errors import ReplayError

if TYPE_CHECKING:
    from ceres.character.domain.character_state import CharacterProjection


type SkillTableEntry = AnySkill | Chars | list[AnySkill]


@dataclass
class SkillTable:
    entries: list[SkillTableEntry]  # length 6, index 0 = die roll 1
    min_edu: int | None = None


class SkillTableOption(BaseModel):
    label: str
    key: str


@dataclass
class CareerSkillTables:
    personal_development: SkillTable
    service_skills: SkillTable
    assignment1: SkillTable
    assignment2: SkillTable
    assignment3: SkillTable
    advanced_education: SkillTable | None = None
    officer: SkillTable | None = None


class CharCheck(BaseModel):
    characteristic: Chars
    target: int


class RankBonus(BaseModel):
    skill: AnySkill | None = None
    characteristic: Chars | None = None
    level: int = 1
    choices: list[AnySkill] | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def resolve_choices(self) -> list[AnySkill] | None:
        return self.choices or None


class RankEntry(BaseModel):
    rank: int
    title: str | None = None
    bonus: RankBonus | None = None


class GainSkillEffect(BaseModel):
    type: Literal['gain_skill'] = 'gain_skill'
    skill: AnySkill

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        projection.grant_skill(self.skill)


class DecreaseCharacteristicEffect(BaseModel):
    type: Literal['decrease_characteristic'] = 'decrease_characteristic'
    characteristic: Chars
    amount: int = 1

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        current = projection.summary.characteristics.get(self.characteristic, 0)
        projection.summary.characteristics[self.characteristic] = max(0, current - self.amount)


class DecreaseCharacteristicChoiceEffect(BaseModel):
    type: Literal['decrease_characteristic_choice'] = 'decrease_characteristic_choice'
    options: list[Chars]
    amount: int = 1


class GainContactEffect(BaseModel):
    type: Literal['gain_contact'] = 'gain_contact'

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        from ceres.character.domain.characteristics import ConnectionKind
        from ceres.character.domain.connection import make_connection

        projection.summary.connections.append(make_connection(ConnectionKind.CONTACT, source=source))


class GainAllyEffect(BaseModel):
    type: Literal['gain_ally'] = 'gain_ally'

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        from ceres.character.domain.characteristics import ConnectionKind
        from ceres.character.domain.connection import make_connection

        projection.summary.connections.append(make_connection(ConnectionKind.ALLY, source=source))


class GainRivalEffect(BaseModel):
    type: Literal['gain_rival'] = 'gain_rival'

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        from ceres.character.domain.characteristics import ConnectionKind
        from ceres.character.domain.connection import make_connection

        projection.summary.connections.append(make_connection(ConnectionKind.RIVAL, source=source))


class GainEnemyEffect(BaseModel):
    type: Literal['gain_enemy'] = 'gain_enemy'

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        from ceres.character.domain.characteristics import ConnectionKind
        from ceres.character.domain.connection import make_connection

        projection.summary.connections.append(make_connection(ConnectionKind.ENEMY, source=source))


class GainConnectionsRolledEffect(BaseModel):
    type: Literal['gain_connections_rolled'] = 'gain_connections_rolled'
    connection_type: ConnectionKind
    dice: str


class AdvancementDmOption(BaseModel):
    model_config = ConfigDict(extra='forbid')

    kind: Literal['advancement_dm'] = 'advancement_dm'
    amount: int = 4

    def label(self) -> str:
        return f'DM+{self.amount} to next advancement roll'


class SkillChoiceEffect(BaseModel):
    type: Literal['skill_choice'] = 'skill_choice'
    options: list[AnySkill | AdvancementDmOption] = []
    level: int = 1

    model_config = ConfigDict(arbitrary_types_allowed=True)


class InjuryEffect(BaseModel):
    type: Literal['injury'] = 'injury'
    severity: Literal['normal', 'severe', 'from_table'] = Field(default='normal')


class RollMishapEffect(BaseModel):
    type: Literal['roll_mishap'] = 'roll_mishap'
    leave: bool = True


class AutoAdvanceEffect(BaseModel):
    type: Literal['auto_advance'] = 'auto_advance'


class LifeEventEffect(BaseModel):
    type: Literal['life_event'] = 'life_event'


class AdvancementDmEffect(BaseModel):
    type: Literal['advancement_dm'] = 'advancement_dm'
    amount: int

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        projection.pending_advancement_dm += self.amount


class BenefitDmEffect(BaseModel):
    type: Literal['benefit_dm'] = 'benefit_dm'
    amount: int

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        if projection.summary.career_terms:
            projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms.append(
                BenefitRollDm(amount=self.amount)
            )


class ParoleThresholdChangeEffect(BaseModel):
    type: Literal['parole_threshold_change'] = 'parole_threshold_change'
    amount: int  # positive = increase PT, negative = decrease PT

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        if projection.summary.parole_threshold is not None:
            new_pt = projection.summary.parole_threshold + self.amount
            projection.summary.parole_threshold = max(0, min(12, new_pt))


class CareerHandlerBase(BaseModel):
    """Base for career-specific event/mishap effect handlers.

    Subclasses declare ``type: Literal['handler_key'] = 'handler_key'`` and implement
    ``handle()`` to append career-specific pending inputs.
    """

    type: str

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        return pending_idx


type AnyEffect = (
    GainSkillEffect
    | DecreaseCharacteristicEffect
    | DecreaseCharacteristicChoiceEffect
    | GainContactEffect
    | GainAllyEffect
    | GainRivalEffect
    | GainEnemyEffect
    | GainConnectionsRolledEffect
    | SkillChoiceEffect
    | InjuryEffect
    | RollMishapEffect
    | AutoAdvanceEffect
    | LifeEventEffect
    | AdvancementDmEffect
    | BenefitDmEffect
    | ParoleThresholdChangeEffect
    | CareerHandlerBase
)


class CareerEventEntry(BaseModel):
    text: str
    effects: list[AnyEffect] = []


class TermData(BaseModel):
    """Base class for both CareerData and PreCareerData, capturing their common interface."""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MishapEntry(BaseModel):
    text: str
    stay_in_career: bool = False
    defer_ejection: bool = False  # handler owns ejection flow; no auto-purge or advancement pending
    effects: list[AnyEffect] = []


class AssignmentData(BaseModel):
    name: str
    description: str
    survival: CharCheck
    advancement: CharCheck


class MusterOutRow(BaseModel):
    cash: int
    benefit: AnyBenefit
    count: int = 1


class MusterOutData(BaseModel):
    rows: dict[int, MusterOutRow]  # 1D roll (1-7) → row


class BasicTrainingPlan(BaseModel):
    table_name: str
    grant_all: bool


class CareerData(TermData):
    type: str = ''  # discriminator; set in concrete subclasses as Literal['X_CAREER']

    _registry: ClassVar[dict[str, type[CareerData]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        type_val = cls.__dict__.get('type')
        if isinstance(type_val, str) and type_val:
            CareerData._registry[type_val] = cls

    @model_validator(mode='wrap')
    @classmethod
    def _from_registry(cls, data: Any, handler: ModelWrapValidatorHandler) -> CareerData:
        if isinstance(data, CareerData):
            return data
        if isinstance(data, dict) and 'type' in data:
            from ceres.character.domain.career.loader import load_careers

            load_careers()
            concrete = CareerData._registry.get(data['type'])
            if concrete is not None:
                return concrete()
        return handler(data)

    events: ClassVar[dict[int, CareerEventEntry]]
    name: ClassVar[str]
    source: ClassVar[str] = 'Core'
    description: ClassVar[str]
    qualification: ClassVar[CharCheck]
    assignments: ClassVar[list[AssignmentData]]
    skill_tables: ClassVar[CareerSkillTables]
    ranks: ClassVar[dict[int, RankEntry]]
    ranks_by_assignment: ClassVar[dict[int, dict[int, RankEntry]]] = {}
    commission: ClassVar[CharCheck | None] = None
    officer_ranks: ClassVar[dict[int, RankEntry]] = {}
    mishaps: ClassVar[dict[int, MishapEntry]]
    muster_out: ClassVar[MusterOutData]
    allows_assignment_change: ClassVar[bool]
    selectable: ClassVar[bool] = True
    draft_assignments: ClassVar[list[str]] = []

    def advancement_is_special(self) -> bool:
        return False

    def assignment(self, name: str) -> AssignmentData | None:
        return next((a for a in self.assignments if a.name == name), None)

    def assignment_by_index(self, index: int) -> AssignmentData | None:
        if index < 1 or index > len(self.assignments):
            return None
        return self.assignments[index - 1]

    def assignment_index(self, assignment: AssignmentData) -> int:
        return self.assignments.index(assignment) + 1

    def skill_table(self, name: str) -> SkillTable | None:
        match name:
            case 'personal_development':
                return self.skill_tables.personal_development
            case 'service_skills':
                return self.skill_tables.service_skills
            case 'advanced_education':
                return self.skill_tables.advanced_education
            case 'officer':
                return self.skill_tables.officer
            case 'assignment1' | 'assignment2' | 'assignment3':
                return getattr(self.skill_tables, name, None)
        return None

    def assignment_ranks(self, index: int) -> dict[int, RankEntry]:
        return self.ranks_by_assignment.get(index, self.ranks)

    def current_ranks(self, projection) -> dict[int, RankEntry]:
        if projection.summary.career_terms and projection.summary.career_terms[-1].commission:
            return self.officer_ranks
        assignment = projection.summary.current_assignment
        index = self.assignment_index(assignment) if assignment is not None else 0
        return self.assignment_ranks(index)

    def rank_title(self, commissioned: bool, rank: int) -> tuple[str, str]:
        if commissioned and self.officer_ranks:
            entry = self.officer_ranks.get(rank)
            return (f'O{rank}', entry.title or '' if entry else '')
        entry = self.ranks.get(rank)
        title = entry.title if entry else ''
        code = f'E{rank}' if self.commission is not None else str(rank)
        return (code, title or '')

    def is_selectable(self, projection=None) -> bool:
        return self.selectable

    def does_draft(self) -> bool:
        return bool(self.draft_assignments)

    def start_draft(self, projection, event_id: int, assignment: AssignmentData | None = None) -> None:
        from ceres.character.domain.career.career_events import PendingDraftAssignmentChoice

        if assignment is None and len(self.draft_assignments) > 1:
            projection.pending_inputs.append(
                PendingDraftAssignmentChoice(
                    pending_id=(event_id, 0),
                    career=self,
                    instruction=f'Choose your {self.name} assignment',
                )
            )
            return

        resolved = assignment or self.assignment(self.draft_assignments[0])
        if resolved is None:
            raise ValueError(f'Unknown draft assignment for {self.name}')

        projection.summary.drafted = True
        projection.summary.current_career = self
        projection.summary.current_assignment = resolved
        self.start_new_term(projection, resolved, event_id)

    def prior_terms(self, terms, assignment: AssignmentData) -> list:
        return [term for term in terms if type(term.career) is type(self)]

    def is_commissioned(self, terms) -> bool:
        prior = [term for term in terms if type(term.career) is type(self)]
        return bool(prior and prior[-1].commission)

    def current_rank(self, terms, assignment: AssignmentData) -> int:
        prior = self.prior_terms(terms, assignment)
        if not prior:
            return 0
        commissioned = prior[-1].commission
        same_track = [term for term in prior if term.commission == commissioned]
        return same_track[-1].rank_after_term if same_track else 0

    def append_term(self, projection, assignment: AssignmentData) -> None:
        term = CareerTerm(
            career=self,
            assignment=assignment,
            commission=self.is_commissioned(projection.summary.career_terms),
            rank_after_term=projection.summary.rank or 0,
        )
        if projection.summary.career_terms:
            previous = projection.summary.career_terms[-1]
            if term.continue_career_run_from(previous):
                pass
        projection.summary.career_terms.append(term)

    def update_current_term_rank(self, projection) -> None:
        if projection.summary.career_terms:
            projection.summary.career_terms[-1].rank_after_term = projection.summary.rank or 0

    def can_attempt_commission(self, projection) -> bool:
        if self.commission is None:
            return False
        if projection.summary.career_terms and projection.summary.career_terms[-1].commission:
            return False
        terms = self.prior_terms(projection.summary.career_terms, self.assignments[0])
        if len(terms) <= 1:
            return True
        return projection.summary.characteristics.get(Chars.SOC, 0) >= 9

    def commission_dm(self, projection) -> int:
        if self.commission is None:
            return 0
        dm = characteristic_dm(projection.summary.characteristics.get(self.commission.characteristic, 0))
        dm -= max(0, len(self.prior_terms(projection.summary.career_terms, self.assignments[0])) - 1)
        return dm

    def qualification_dm(self, projection) -> int:
        char = self.qualification.characteristic
        return characteristic_dm(projection.summary.characteristics.get(char, 0))

    def start_career(
        self,
        projection,
        assignment: AssignmentData,
        event_id: int,
        qualification_roll: int,
    ) -> None:
        from ceres.character.mechanism.replay import ReplayError

        last = projection.summary.last_career
        if last is not None and type(last) is type(self):
            if projection.summary.last_career_ejected:
                raise ReplayError(f'Cannot re-enter {self.name} — ejected from this career last term')
            if last.allows_assignment_change:
                raise ReplayError(f'Cannot re-enter {self.name} — voluntary departure last term')
            if projection.summary.last_assignment == assignment:
                raise ReplayError(f'Cannot re-enter {self.name}/{assignment.name} — voluntary departure last term')

        # Check for auto-qualify from pre-career graduation
        if self.name in projection.auto_qualify_careers:
            projection.auto_qualify_careers.remove(self.name)
            projection.summary.current_career = self
            projection.summary.current_assignment = assignment
            self.start_new_term(projection, assignment, event_id)
            return

        target = self.qualification.target
        dm = self.qualification_dm(projection)
        dm += projection.pending_qualification_dm
        projection.pending_qualification_dm = 0
        if qualification_roll + dm < target:
            from ceres.character.domain.career.career_events import PendingDraftChoice

            projection.summary.problems.append(f'Failed to qualify for {self.name}.')
            projection.pending_inputs.append(
                PendingDraftChoice(
                    pending_id=(event_id, 0),
                    instruction='Qualification failed — submit to the draft or become a Drifter',
                    can_draft=not projection.summary.drafted,
                )
            )
            return

        projection.summary.current_career = self
        projection.summary.current_assignment = assignment
        self.start_new_term(projection, assignment, event_id)

    def start_new_term(
        self,
        projection,
        assignment: AssignmentData,
        event_id: int,
        is_continuation: bool = False,
    ) -> None:
        training = self._basic_training_plan(projection, assignment, is_continuation)
        projection.summary.rank = self.current_rank(projection.summary.career_terms, assignment)
        if not self.prior_terms(projection.summary.career_terms, assignment):
            self._apply_fixed_rank_bonus(projection, 0)
        self.append_term(projection, assignment)

        if training is not None:
            self._apply_basic_training(projection, assignment, training.table_name, training.grant_all, event_id)
        else:
            self._queue_skill_table_before_survival(projection, assignment, event_id)

    def _basic_training_table_name(self, assignment: AssignmentData) -> str:
        return 'service_skills'

    def _apply_fixed_rank_bonus(self, projection, rank: int) -> None:
        rank_entry = self.current_ranks(projection).get(rank)
        if not rank_entry or not rank_entry.bonus:
            return
        bonus = rank_entry.bonus
        if bonus.skill:
            skill_cls = type(bonus.skill)
            fields = _level_fields(skill_cls)
            existing = next((s for s in projection.summary.skills if type(s) is skill_cls), None)
            if existing is None:
                existing = skill_cls()
                projection.summary.skills.append(existing)
            for field in fields:
                level = getattr(existing, field)
                if isinstance(level, Level):
                    level.set(max(level.value, bonus.level))
        elif bonus.characteristic:
            current = projection.summary.characteristics.get(bonus.characteristic, 0)
            projection.summary.characteristics[bonus.characteristic] = current + bonus.level

    def _basic_training_plan(
        self,
        projection,
        assignment: AssignmentData,
        is_continuation: bool = False,
    ) -> BasicTrainingPlan | None:
        if is_continuation:
            return None
        return BasicTrainingPlan(
            table_name=self._basic_training_table_name(assignment),
            grant_all=not projection.summary.career_terms,
        )

    def _apply_basic_training(
        self,
        projection,
        assignment: AssignmentData,
        table_name: str,
        grant_all: bool,
        event_id: int,
    ) -> None:

        table = self.skill_table(table_name)
        if table is None:
            raise ValueError(f'Unknown skill table: {table_name!r}')
        if grant_all:
            from ceres.character.domain.career.career_events import PendingInitialTrainingChoice

            choice_idx = 0
            for entry in table.entries:
                choices = self._training_pending_choices(projection, entry)
                if len(choices) > 1:
                    projection.pending_inputs.append(
                        PendingInitialTrainingChoice(
                            pending_id=(event_id, choice_idx),
                            instruction=f'Initial training: choose one of {", ".join(type(s).name() for s in choices)}',
                            options=cast(list[AnySkill | AdvancementDmOption], choices),
                        )
                    )
                    choice_idx += 1
                else:
                    self._apply_initial_training_entry(projection, entry)
            if choice_idx == 0:
                projection.pending_inputs.append(self.survival_pending(assignment, event_id))
            return

        from ceres.character.domain.career.career_events import PendingInitialTrainingChoice

        raw: list[AnySkill] = []
        for entry in table.entries:
            raw.extend(self._training_selectable_skills(projection, entry))
        by_name: dict[str, AnySkill] = {}
        for s in raw:
            by_name.setdefault(type(s).name(), s)
        deduped: list[AnySkill] = sorted(by_name.values(), key=lambda s: type(s).name())
        if deduped:
            projection.pending_inputs.append(
                PendingInitialTrainingChoice(
                    pending_id=(event_id, 0),
                    instruction=f'Basic training: choose one skill at level 0 from {table_name}',
                    options=cast(list[AnySkill | AdvancementDmOption], deduped),
                )
            )
        else:
            projection.pending_inputs.append(self.survival_pending(assignment, event_id))

    def _apply_initial_training_entry(self, projection, entry: SkillTableEntry) -> None:
        if isinstance(entry, Chars):
            return  # characteristic boosts are not granted during basic training
        if isinstance(entry, list):
            # Choice entry: add all unknown skills at level 0
            for skill in entry:
                skill_cls = type(skill)
                if projection.summary.skill_level(skill_cls) is None:
                    projection.summary.skills.append(skill_cls())
        else:
            # Single AnySkill entry
            skill_cls = type(entry)
            if projection.summary.skill_level(skill_cls) is None:
                projection.summary.skills.append(skill_cls())

    def _training_pending_choices(self, projection, entry: SkillTableEntry) -> list[AnySkill]:
        if isinstance(entry, Chars):
            return []
        if isinstance(entry, list):
            return [s for s in entry if projection.summary.skill_level(type(s)) is None]
        skill_cls = type(entry)
        fields = _level_fields(skill_cls)
        spec_field = next((f for f in fields if getattr(entry, f).value > 0), None)
        if spec_field is not None:
            return []
        if projection.summary.skill_level(skill_cls) is None:
            return [skill_cls()]
        return []

    def _training_selectable_skills(self, projection, entry: SkillTableEntry) -> list[AnySkill]:
        if isinstance(entry, Chars):
            return []
        if isinstance(entry, list):
            return [s for s in entry if projection.summary.skill_level(type(s)) is None]
        skill_cls = type(entry)
        if projection.summary.skill_level(skill_cls) is None:
            return [skill_cls()]
        return []

    def _queue_skill_table_before_survival(self, projection, assignment: AssignmentData, event_id: int) -> None:
        from ceres.character.domain.career.career_events import PendingSkillTable

        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = self.available_tables(edu, assignment)
        projection.pending_inputs.append(
            PendingSkillTable(pending_id=(event_id, 0), instruction='Choose a skill table and roll 1D', options=tables)
        )

    def survival_pending(self, assignment: AssignmentData, event_id: int, pending_idx: int = 0):
        from ceres.character.domain.career.career_events import PendingSurvive

        char = assignment.survival.characteristic
        target = assignment.survival.target
        return PendingSurvive(pending_id=(event_id, pending_idx), instruction=f'Survive: {char} {target}+')

    def available_tables(self, edu: int, assignment: AssignmentData | None) -> list[SkillTableOption]:
        result = [
            SkillTableOption(label='Personal Development', key='personal_development'),
            SkillTableOption(label='Service Skills', key='service_skills'),
        ]
        adv_edu = self.skill_tables.advanced_education
        if adv_edu is not None and edu >= (adv_edu.min_edu or 0):
            result.append(SkillTableOption(label='Advanced Education', key='advanced_education'))
        if self.skill_tables.officer is not None:
            result.append(SkillTableOption(label='Officer', key='officer'))
        if assignment is not None:
            idx = self.assignment_index(assignment)
            result.append(SkillTableOption(label=assignment.name, key=f'assignment{idx}'))
        return sorted(result, key=lambda o: o.key)


# ── Muster-out and career term state ────────────────────────────────────────


class BenefitRollDm(BaseModel):
    amount: int


class MusterOut(BaseModel):
    terms: int = 1
    cash_count: int = 0
    benefits: list[ItemBenefit] = Field(default_factory=list)
    extra_rolls: int = 0
    lost_rolls: int = 0
    benefit_roll_dms: list[BenefitRollDm] = Field(default_factory=list)
    used: bool = False


class CareerTerm(BaseModel):
    career: CareerData
    assignment: AssignmentData
    commission: bool = False
    rank_after_term: int = 0
    muster_out: MusterOut | None = Field(default_factory=MusterOut)
    event: str | None = None
    mishap: str | None = None
    prison: str | None = None

    def continue_career_run_from(self, previous: CareerTerm) -> bool:
        if not previous.muster_out:
            return False
        if previous.muster_out.used:
            return False
        career_continue = self.career.allows_assignment_change and (self.career == previous.career)
        assignment_continue = (
            not self.career.allows_assignment_change
            and self.career == previous.career
            and self.assignment == previous.assignment
        )
        if career_continue or assignment_continue:
            if not previous.muster_out:
                raise ValueError('Previous career should have Muster Out information.')
            self.muster_out = previous.muster_out
            self.muster_out.terms += 1
            previous.muster_out = None
            return True
        return False

    def require_muster_out(self) -> MusterOut:
        if self.muster_out is None:
            raise ReplayError('Career term has no active muster-out state')
        return self.muster_out

    @property
    def rank_title(self) -> tuple[str, str]:
        return self.career.rank_title(self.commission, self.rank_after_term)
