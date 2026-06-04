from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from ceres.character.benefits import AnyBenefit
from ceres.character.characteristics import Chars, ConnectionKind, characteristic_dm
from ceres.character.effect_enums import EffectTrigger
from ceres.character.skills import AnySkill, Level, _level_fields

if TYPE_CHECKING:
    from ceres.character.state import CharacterProjection


@dataclass(frozen=True)
class Career:
    name: str
    source: str = 'Core'
    description: str = ''


type SkillTableEntry = AnySkill | Chars | list[AnySkill]


@dataclass
class SkillTable:
    entries: list[SkillTableEntry]  # length 6, index 0 = die roll 1
    min_edu: int | None = None


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


class DecreaseCharacteristicEffect(BaseModel):
    type: Literal['decrease_characteristic'] = 'decrease_characteristic'
    characteristic: Chars
    amount: int = 1


class DecreaseCharacteristicChoiceEffect(BaseModel):
    type: Literal['decrease_characteristic_choice'] = 'decrease_characteristic_choice'
    options: list[str]
    amount: int = 1


class GainContactEffect(BaseModel):
    type: Literal['gain_contact'] = 'gain_contact'


class GainAllyEffect(BaseModel):
    type: Literal['gain_ally'] = 'gain_ally'


class GainRivalEffect(BaseModel):
    type: Literal['gain_rival'] = 'gain_rival'


class GainEnemyEffect(BaseModel):
    type: Literal['gain_enemy'] = 'gain_enemy'


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


class BenefitDmEffect(BaseModel):
    type: Literal['benefit_dm'] = 'benefit_dm'
    amount: int


class ParoleThresholdChangeEffect(BaseModel):
    type: Literal['parole_threshold_change'] = 'parole_threshold_change'
    amount: int  # positive = increase PT, negative = decrease PT


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

    events: dict[int, CareerEventEntry]


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
    career: Career
    qualification: CharCheck

    @property
    def name(self) -> str:
        return self.career.name

    @property
    def description(self) -> str:
        return self.career.description

    @property
    def source(self) -> str:
        return self.career.source

    assignments: list[AssignmentData]
    skill_tables: CareerSkillTables
    ranks: dict[int, RankEntry]  # default rank table (used when no per-assignment override)
    ranks_by_assignment: dict[int, dict[int, RankEntry]] = {}  # assignment index → rank table override
    commission: CharCheck | None = None
    officer_ranks: dict[int, RankEntry] = {}
    mishaps: dict[int, MishapEntry]  # 1D roll → mishap
    muster_out: MusterOutData
    allows_assignment_change: bool
    selectable: bool = True
    draft_assignments: list[str] = []

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
        for i, a in enumerate(self.assignments, 1):
            if a.name.lower() == name.lower():
                return getattr(self.skill_tables, f'assignment{i}')
        return None

    def assignment_ranks(self, index: int) -> dict[int, RankEntry]:
        return self.ranks_by_assignment.get(index, self.ranks)

    def current_ranks(self, projection) -> dict[int, RankEntry]:
        if projection.summary.career_terms and projection.summary.career_terms[-1].commission:
            return self.officer_ranks
        return self.assignment_ranks(projection.summary.current_assignment_index or 0)

    def is_selectable(self, projection=None) -> bool:
        return self.selectable

    def does_draft(self) -> bool:
        return bool(self.draft_assignments)

    def start_draft(self, projection, event_id: int, assignment_name: str | None = None) -> None:
        from ceres.character.events import PendingDraftAssignmentChoice

        if assignment_name is None and len(self.draft_assignments) > 1:
            projection.pending_inputs.append(
                PendingDraftAssignmentChoice(
                    id=f'{event_id}.0',
                    career=self.name,
                    instruction=f'Choose your {self.name} assignment',
                    options=list(self.draft_assignments),
                )
            )
            return

        selected = assignment_name or self.draft_assignments[0]
        assignment = self.assignment(selected)
        if assignment is None:
            raise ValueError(f'Unknown draft assignment {selected!r} for {self.name}')

        projection.summary.drafted = True
        projection.summary.current_career = self.career
        projection.summary.current_assignment = assignment.name
        projection.summary.current_assignment_index = self.assignment_index(assignment)
        self.start_new_term(projection, assignment, event_id)

    def prior_terms(self, terms, assignment: AssignmentData) -> list:
        return [term for term in terms if term.career == self.career]

    def is_commissioned(self, terms) -> bool:
        prior = [term for term in terms if term.career == self.career]
        return bool(prior and prior[-1].commission)

    def current_rank(self, terms, assignment: AssignmentData) -> int:
        prior = self.prior_terms(terms, assignment)
        if not prior:
            return 0
        commissioned = prior[-1].commission
        same_track = [term for term in prior if term.commission == commissioned]
        return same_track[-1].rank_after_term if same_track else 0

    def append_term(self, projection, assignment: AssignmentData) -> None:
        from ceres.character.state import CareerTerm

        projection.summary.career_terms.append(
            CareerTerm(
                career=self.career,
                assignment=assignment.name,
                assignment_index=self.assignment_index(assignment),
                commission=self.is_commissioned(projection.summary.career_terms),
                rank_after_term=projection.summary.rank or 0,
            )
        )

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

        # Check for auto-qualify from pre-career graduation
        auto_effects = [
            se
            for se in projection.scheduled_effects
            if se.trigger == EffectTrigger.AUTO_QUALIFY and se.effect.get('career') == self.name
        ]
        if auto_effects:
            for se in auto_effects:
                projection.scheduled_effects.remove(se)
            projection.summary.current_career = self.career
            projection.summary.current_assignment = assignment.name
            projection.summary.current_assignment_index = self.assignment_index(assignment)
            self.start_new_term(projection, assignment, event_id)
            return

        target = self.qualification.target
        dm = self.qualification_dm(projection)
        qual_effects = [
            se for se in projection.scheduled_effects if se.trigger == EffectTrigger.QUALIFICATION and se.consume
        ]
        for se in qual_effects:
            dm += se.effect.get('amount', 0)
            projection.scheduled_effects.remove(se)
        if qualification_roll + dm < target:
            from ceres.character.events import PendingDraftChoice

            projection.summary.problems.append(f'Failed to qualify for {self.name}.')
            options = ['drifter'] if projection.summary.drafted else ['draft', 'drifter']
            projection.pending_inputs.append(
                PendingDraftChoice(
                    id=f'{event_id}.0',
                    instruction='Qualification failed — submit to the draft or become a Drifter',
                    options=options,
                )
            )
            return

        projection.summary.current_career = self.career
        projection.summary.current_assignment = assignment.name
        projection.summary.current_assignment_index = self.assignment_index(assignment)
        self.start_new_term(projection, assignment, event_id)

    def start_new_term(self, projection, assignment: AssignmentData, event_id: int) -> None:
        training = self._basic_training_plan(projection, assignment)
        projection.summary.rank = self.current_rank(projection.summary.career_terms, assignment)
        if not self.prior_terms(projection.summary.career_terms, assignment):
            self._apply_fixed_rank_bonus(projection, 0)
        projection.summary.term_count += 1
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

    def _basic_training_plan(self, projection, assignment: AssignmentData) -> BasicTrainingPlan | None:
        if self.prior_terms(projection.summary.career_terms, assignment):
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
            from ceres.character.events import PendingInitialTrainingChoice

            choice_idx = 0
            for entry in table.entries:
                choices = self._training_pending_choices(projection, entry)
                if len(choices) > 1:
                    projection.pending_inputs.append(
                        PendingInitialTrainingChoice(
                            id=f'{event_id}.{choice_idx}',
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

        from ceres.character.events import PendingInitialTrainingChoice

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
                    id=f'{event_id}.0',
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
        from ceres.character.events import PendingSkillTable

        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = self.available_tables(edu, self.assignment_index(assignment))
        projection.pending_inputs.append(
            PendingSkillTable(id=f'{event_id}.0', instruction='Choose a skill table and roll 1D', options=tables)
        )

    def survival_pending(self, assignment: AssignmentData, event_id: int, pending_idx: int = 0):
        from ceres.character.events import PendingSurvive

        char = assignment.survival.characteristic
        target = assignment.survival.target
        return PendingSurvive(id=f'{event_id}.{pending_idx}', instruction=f'Survive: {char} {target}+')

    def available_tables(self, edu: int, assignment_index: int) -> list[str]:
        result = ['personal_development', 'service_skills']
        adv_edu = self.skill_tables.advanced_education
        if adv_edu is not None and edu >= (adv_edu.min_edu or 0):
            result.append('advanced_education')
        if self.skill_tables.officer is not None:
            result.append('officer')
        assignment = self.assignment_by_index(assignment_index)
        if assignment is not None:
            result.append(assignment.name.lower())
        return sorted(result)
