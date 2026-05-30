from typing import Literal

from pydantic import BaseModel

from ceres.character.benefits import AnyBenefit
from ceres.character.characteristics import Chars, ConnectionKind, characteristic_dm


class CharCheck(BaseModel):
    characteristic: Chars
    target: int


class SkillTableEntry(BaseModel):
    skill: str | None = None
    spec: str | None = None  # specific specialisation to grant (e.g. 'Computers' for Electronics)
    characteristic: Chars | None = None  # for +1 characteristic entries
    level: int = 1
    choices: list[str] | None = None  # if multiple skill options (e.g. "Drive or Flyer")


class SkillTable(BaseModel):
    min_edu: int | None = None
    entries: dict[int, SkillTableEntry]


class RankBonus(BaseModel):
    skill: str | None = None
    characteristic: Chars | None = None
    level: int = 1
    choices: list[str] | None = None  # if player picks which broad skill to gain

    def resolve_choices(self) -> list[str] | None:
        from ceres.character.skills import skill_names_for_category

        if self.choices:
            return self.choices
        if self.skill:
            return skill_names_for_category(self.skill)
        return None


class RankEntry(BaseModel):
    rank: int
    title: str | None = None
    bonus: RankBonus | None = None


class GainSkillEffect(BaseModel):
    type: Literal['gain_skill'] = 'gain_skill'
    skill: str
    level: int = 1


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


class SkillChoiceEffect(BaseModel):
    type: Literal['skill_choice'] = 'skill_choice'
    options: list[str]
    level: int = 1


class InjuryEffect(BaseModel):
    type: Literal['injury'] = 'injury'
    severity: Literal['normal', 'severe', 'from_table'] = 'normal'


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


class CareerDispatchEffect(BaseModel):
    """Career-specific effect; dispatched via EFFECT_HANDLERS registry in the career's .py module."""

    type: str


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
    | CareerDispatchEffect
)


class CareerEventEntry(BaseModel):
    text: str
    effects: list[AnyEffect] = []


class MishapEntry(BaseModel):
    text: str
    stay_in_career: bool = False
    defer_ejection: bool = False  # handler owns ejection flow; no auto-purge or advancement pending
    effects: list[AnyEffect] = []


class AssignmentData(BaseModel):
    name: str
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


class CareerData(BaseModel):
    name: str
    source: str
    qualification: CharCheck
    assignments: list[AssignmentData]
    skill_tables: dict[str, SkillTable]  # keyed by table name, e.g. 'service_skills' or assignment name
    ranks: dict[int, RankEntry]  # default rank table (used when no per-assignment override)
    ranks_by_assignment: dict[str, dict[int, RankEntry]] = {}  # assignment name → rank table override
    commission: CharCheck | None = None
    officer_ranks: dict[int, RankEntry] = {}
    events: dict[int, CareerEventEntry]  # 2D roll → event
    mishaps: dict[int, MishapEntry]  # 1D roll → mishap
    muster_out: MusterOutData | None = None
    allows_assignment_change: bool
    selectable: bool = True
    draft_assignments: list[str] = []

    def assignment(self, name: str) -> AssignmentData | None:
        return next((a for a in self.assignments if a.name == name), None)

    def skill_table(self, name: str) -> SkillTable | None:
        return self.skill_tables.get(name)

    def assignment_ranks(self, assignment_name: str) -> dict[int, RankEntry]:
        return self.ranks_by_assignment.get(assignment_name, self.ranks)

    def current_ranks(self, projection) -> dict[int, RankEntry]:
        if projection.summary.career_terms and projection.summary.career_terms[-1].commission:
            return self.officer_ranks
        return self.assignment_ranks(projection.summary.current_assignment or '')

    def is_selectable(self, projection=None) -> bool:
        return self.selectable

    def does_draft(self) -> bool:
        return bool(self.draft_assignments)

    def start_draft(self, projection, event_id: int, assignment_name: str | None = None) -> None:
        from ceres.character.projection import PendingDraftAssignmentChoice

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
        projection.summary.current_career = self.name
        projection.summary.current_assignment = assignment.name
        self.start_new_term(projection, assignment, event_id)

    def prior_terms(self, terms, assignment: AssignmentData) -> list:
        return [term for term in terms if term.career == self.name]

    def is_commissioned(self, terms) -> bool:
        prior = [term for term in terms if term.career == self.name]
        return bool(prior and prior[-1].commission)

    def current_rank(self, terms, assignment: AssignmentData) -> int:
        prior = self.prior_terms(terms, assignment)
        if not prior:
            return 0
        commissioned = prior[-1].commission
        same_track = [term for term in prior if term.commission == commissioned]
        return same_track[-1].rank_after_term if same_track else 0

    def append_term(self, projection, assignment: AssignmentData) -> None:
        from ceres.character.projection import CareerTerm

        projection.summary.career_terms.append(
            CareerTerm(
                career=self.name,
                assignment=assignment.name,
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
        from ceres.character.projection import PendingDraftChoice

        # Check for auto-qualify from pre-career graduation
        auto_effects = [
            se
            for se in projection.scheduled_effects
            if se.trigger == 'auto_qualify' and se.effect.get('career') == self.name
        ]
        if auto_effects:
            for se in auto_effects:
                projection.scheduled_effects.remove(se)
            projection.summary.current_career = self.name
            projection.summary.current_assignment = assignment.name
            self.start_new_term(projection, assignment, event_id)
            return

        target = self.qualification.target
        dm = self.qualification_dm(projection)
        qual_effects = [se for se in projection.scheduled_effects if se.trigger == 'qualification' and se.consume]
        for se in qual_effects:
            dm += se.effect.get('amount', 0)
            projection.scheduled_effects.remove(se)
        if qualification_roll + dm < target:
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

        projection.summary.current_career = self.name
        projection.summary.current_assignment = assignment.name
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
        from ceres.character.projection import _level_fields
        from ceres.character.skills import Level, skill_class_by_name

        rank_entry = self.current_ranks(projection).get(rank)
        if not rank_entry or not rank_entry.bonus:
            return
        bonus = rank_entry.bonus
        if bonus.skill:
            skill_cls = skill_class_by_name(bonus.skill)
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
        from ceres.character.projection import PendingInitialTrainingChoice

        table = self.skill_tables[table_name]
        if grant_all:
            choice_idx = 0
            for entry in table.entries.values():
                choices = self._training_pending_choices(projection, entry)
                if len(choices) > 1:
                    projection.pending_inputs.append(
                        PendingInitialTrainingChoice(
                            id=f'{event_id}.{choice_idx}',
                            instruction=f'Initial training: choose one of {", ".join(choices)}',
                            options=choices,
                        )
                    )
                    choice_idx += 1
                else:
                    self._apply_initial_training_entry(projection, entry)
            if choice_idx == 0:
                projection.pending_inputs.append(self.survival_pending(assignment, event_id))
            return

        choices = []
        for entry in table.entries.values():
            choices.extend(self._training_selectable_skills(projection, entry))
        if choices:
            projection.pending_inputs.append(
                PendingInitialTrainingChoice(
                    id=f'{event_id}.0',
                    instruction=f'Basic training: choose one skill at level 0 from {table_name}',
                    options=sorted(set(choices)),
                )
            )
        else:
            projection.pending_inputs.append(self.survival_pending(assignment, event_id))

    def _apply_initial_training_entry(self, projection, entry: SkillTableEntry) -> None:
        from ceres.character.skills import skill_class_by_name

        if entry.choices:
            choices = entry.choices
        elif entry.skill:
            choices = [entry.skill]
        else:
            choices = []
        for skill in choices:
            if projection.summary.skill_level(skill) is None:
                projection.summary.skills.append(skill_class_by_name(skill)())

    def _training_pending_choices(self, projection, entry: SkillTableEntry) -> list[str]:
        from ceres.character.skills import skill_names_for_category

        if entry.spec is not None:
            return []
        choices = entry.choices
        if choices is None and entry.skill is not None:
            choices = skill_names_for_category(entry.skill)
        return [skill for skill in choices or [] if projection.summary.skill_level(skill) is None]

    def _training_selectable_skills(self, projection, entry: SkillTableEntry) -> list[str]:
        from ceres.character.skills import skill_names_for_category

        choices = entry.choices
        if choices is None and entry.skill is not None:
            choices = skill_names_for_category(entry.skill)
        if choices is None and entry.skill is not None:
            choices = [entry.skill]
        return [skill for skill in choices or [] if projection.summary.skill_level(skill) is None]

    def _queue_skill_table_before_survival(self, projection, assignment: AssignmentData, event_id: int) -> None:
        from ceres.character.projection import PendingSkillTable

        edu = projection.summary.characteristics.get(Chars.EDU, 0)
        tables = self.available_tables(edu, assignment.name)
        projection.pending_inputs.append(
            PendingSkillTable(id=f'{event_id}.0', instruction='Choose a skill table and roll 1D', options=tables)
        )

    def survival_pending(self, assignment: AssignmentData, event_id: int, pending_idx: int = 0):
        from ceres.character.projection import PendingSurvive

        char = assignment.survival.characteristic
        target = assignment.survival.target
        return PendingSurvive(id=f'{event_id}.{pending_idx}', instruction=f'Survive: {char} {target}+')

    def available_tables(self, edu: int, current_assignment: str) -> list[str]:
        """Return skill table names available to this character.

        Excludes tables that belong to a different assignment, and tables whose min_edu
        the character does not meet.
        """
        assignment_names_lower = {a.name.lower() for a in self.assignments}
        current_lower = current_assignment.lower()
        result = []
        for name, table in self.skill_tables.items():
            if name in assignment_names_lower and name != current_lower:
                continue
            if table.min_edu is not None and edu < table.min_edu:
                continue
            result.append(name)
        return sorted(result)
