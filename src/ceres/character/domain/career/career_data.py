from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.functional_validators import ModelWrapValidatorHandler

from ceres.character.domain.benefits import AnyBenefit, ItemBenefit
from ceres.character.domain.characteristics import Chars, ConnectionKind, characteristic_dm
from ceres.character.domain.dice import DiceRoll
from ceres.character.domain.psionics import Psi
from ceres.character.domain.skills import AnySkill, level_fields
from ceres.character.mechanism.errors import ReplayError

if TYPE_CHECKING:
    from ceres.character.domain.character_state import CharacterProjection


type CareerSkillOption = AnySkill | Psi
type SkillTableEntry = CareerSkillOption | Chars | list[AnySkill] | list[Psi]


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
    choices: Sequence[CareerSkillOption] | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def resolve_choices(self) -> Sequence[CareerSkillOption] | None:
        if self.choices:
            return self.choices
        if self.skill:
            fields = level_fields(type(self.skill))
            if len(fields) > 1 and not any(getattr(self.skill, field).value > 0 for field in fields):
                return [self.skill]
        return None


class RankEntry(BaseModel):
    rank: int
    title: str | None = None
    bonus: RankBonus | None = None


def _blank_ranks() -> dict[int, RankEntry]:
    """Ranks 0–6 with no titles or bonuses, for careers that track rank but grant nothing for it."""
    return {i: RankEntry(rank=i) for i in range(7)}


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
        projection.decrease_characteristic(self.characteristic, self.amount)


class DecreaseCharacteristicChoiceEffect(BaseModel):
    type: Literal['decrease_characteristic_choice'] = 'decrease_characteristic_choice'
    options: list[Chars]
    amount: int = 1


class GainContactEffect(BaseModel):
    type: Literal['gain_contact'] = 'gain_contact'

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        from ceres.character.domain.characteristics import ConnectionKind

        projection.add_connection(ConnectionKind.CONTACT, origin=source)


class GainAllyEffect(BaseModel):
    type: Literal['gain_ally'] = 'gain_ally'

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        from ceres.character.domain.characteristics import ConnectionKind

        projection.add_connection(ConnectionKind.ALLY, origin=source)


class GainRivalEffect(BaseModel):
    type: Literal['gain_rival'] = 'gain_rival'

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        from ceres.character.domain.characteristics import ConnectionKind

        projection.add_connection(ConnectionKind.RIVAL, origin=source)


class GainEnemyEffect(BaseModel):
    type: Literal['gain_enemy'] = 'gain_enemy'

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        from ceres.character.domain.characteristics import ConnectionKind

        projection.add_connection(ConnectionKind.ENEMY, origin=source)


class GainConnectionsRolledEffect(BaseModel):
    type: Literal['gain_connections_rolled'] = 'gain_connections_rolled'
    connection_type: ConnectionKind
    dice: DiceRoll


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
        projection.add_advancement_dm(self.amount)


class QualificationDmEffect(BaseModel):
    type: Literal['qualification_dm'] = 'qualification_dm'
    amount: int

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        projection.add_qualification_dm(self.amount)


class BenefitDmEffect(BaseModel):
    type: Literal['benefit_dm'] = 'benefit_dm'
    amount: int

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        projection.add_benefit_dm(self.amount)


class ParoleThresholdChangeEffect(BaseModel):
    type: Literal['parole_threshold_change'] = 'parole_threshold_change'
    amount: int  # positive = increase PT, negative = decrease PT

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        projection.adjust_parole_threshold(self.amount)


class AutoQualifyCareerEffect(BaseModel):
    type: Literal['auto_qualify_career'] = 'auto_qualify_career'
    # Pydantic cannot use `type[CareerData]` here: the field named `type` shadows the builtin
    # during annotation evaluation. Any is used; the value is always a CareerData subclass.
    career: Any

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        projection.auto_qualify(self.career)


class LoseAllCareerBenefitsEffect(BaseModel):
    type: Literal['lose_all_career_benefits'] = 'lose_all_career_benefits'

    def apply(self, projection: Any, source: str = '', source_event_id: int = 0) -> None:
        projection.forfeit_current_career_benefits()


class CareerTableEntry(BaseModel):
    text: str
    stay_in_career: bool = False
    defer_ejection: bool = False

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        return pending_idx

    def continues_career_progress(self) -> bool:
        return True


class NoEffectEntry(CareerTableEntry):
    pass


def _queue_injury(
    projection: CharacterProjection,
    event: Any,
    pending_idx: int,
    severity: Literal['normal', 'severe', 'from_table'],
) -> None:
    from ceres.character.domain.health.health_events import PendingCharacteristicChoice, PendingInjuryTable

    if severity == 'normal':
        projection.pending_inputs.append(
            PendingCharacteristicChoice(
                pending_id=(event.id, pending_idx),
                instruction='Injured: choose STR, DEX, or END to reduce by 1',
                options=[Chars.STR, Chars.DEX, Chars.END],
                amount=1,
            )
        )
    elif severity == 'severe':
        projection.pending_inputs.append(
            PendingCharacteristicChoice(
                pending_id=(event.id, pending_idx),
                instruction='Severely injured: choose STR, DEX, or END to reduce by 2',
                options=[Chars.STR, Chars.DEX, Chars.END],
                amount=2,
            )
        )
    elif severity == 'from_table':
        projection.pending_inputs.append(
            PendingInjuryTable(
                pending_id=(event.id, pending_idx),
                instruction='Roll 1D on Injury table',
            )
        )


class GainSkillEntry(CareerTableEntry):
    skill: AnySkill

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.grant_skill(self.skill)
        return pending_idx


class CharacteristicLossEntry(CareerTableEntry):
    characteristic: Chars
    amount: int = 1

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.decrease_characteristic(self.characteristic, self.amount)
        return pending_idx


class CharacteristicLossOutcome(BaseModel):
    characteristic: Chars
    amount: int = 1


class CharacteristicLossesAndConnectionEntry(CareerTableEntry):
    connection: ConnectionKind
    losses: list[CharacteristicLossOutcome]

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.add_connection(self.connection, origin=self.text)
        for loss in self.losses:
            projection.decrease_characteristic(loss.characteristic, loss.amount)
        return pending_idx


class CharacteristicLossChoiceEntry(CareerTableEntry):
    options: list[Chars]
    amount: int = 1

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.health.health_events import PendingCharacteristicChoice

        characteristic = ', '.join(c.value for c in self.options)
        projection.pending_inputs.append(
            PendingCharacteristicChoice(
                pending_id=(event.id, pending_idx),
                instruction=f'Choose characteristic to decrease by {self.amount}: {characteristic}',
                options=self.options,
                amount=self.amount,
            )
        )
        return pending_idx + 1


class GainConnectionEntry(CareerTableEntry):
    connection: ConnectionKind

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.add_connection(self.connection, origin=self.text)
        return pending_idx


class RolledConnectionsEntry(CareerTableEntry):
    connection: ConnectionKind
    dice: DiceRoll

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.connection_events import PendingConnectionsRoll

        projection.pending_inputs.append(
            PendingConnectionsRoll(
                pending_id=(event.id, pending_idx),
                connection_type=self.connection,
                instruction=f'Roll {self.dice} for number of {self.connection}s',
                options=self.dice.roll_options(),
                origin=self.text,
            )
        )
        return pending_idx + 1


class RolledConnectionOutcome(BaseModel):
    connection: ConnectionKind
    dice: DiceRoll


class RolledConnectionsGroupEntry(CareerTableEntry):
    rolls: list[RolledConnectionOutcome]

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.connection_events import PendingConnectionsRoll

        for offset, roll in enumerate(self.rolls):
            projection.pending_inputs.append(
                PendingConnectionsRoll(
                    pending_id=(event.id, pending_idx + offset),
                    connection_type=roll.connection,
                    instruction=f'Roll {roll.dice} for number of {roll.connection}s',
                    options=roll.dice.roll_options(),
                    origin=self.text,
                )
            )
        return pending_idx + len(self.rolls)


class SkillChoiceEntry(CareerTableEntry):
    options: list[AnySkill | AdvancementDmOption]
    level: int = 1

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.skill_events import PendingSkillChoice

        projection.pending_inputs.append(
            PendingSkillChoice(
                pending_id=(event.id, pending_idx),
                instruction=f'Choose one skill at level {self.level}',
                options=cast(Any, self.options),
                level=self.level,
            )
        )
        return pending_idx + 1

    def continues_career_progress(self) -> bool:
        return False


class InjuryEntry(CareerTableEntry):
    severity: Literal['normal', 'severe', 'from_table'] = Field(default='normal')

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        _queue_injury(projection, event, pending_idx, self.severity)
        return pending_idx + 1


class RollMishapEntry(CareerTableEntry):
    leave: bool = True

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.career.career_events import PendingMishap

        instruction = (
            'Roll 1D on Mishap table (you are not ejected from this career)'
            if not self.leave
            else 'Roll 1D on Mishap table'
        )
        projection.pending_inputs.append(
            PendingMishap(
                pending_id=(event.id, pending_idx),
                instruction=instruction,
                stay_in_career=not self.leave,
            )
        )
        return pending_idx + 1

    def continues_career_progress(self) -> bool:
        return False


class LifeEventEntry(CareerTableEntry):
    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.life_events import PendingLifeEvent

        projection.pending_inputs.append(
            PendingLifeEvent(pending_id=(event.id, pending_idx), instruction='Roll 2D on Life Events table')
        )
        return pending_idx + 1

    def continues_career_progress(self) -> bool:
        return False


class AutoAdvanceEntry(CareerTableEntry):
    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.career.advancement import apply_auto_advance

        career = projection.summary.current_career
        if career is None and projection.summary.career_terms:
            career = projection.summary.career_terms[-1].career
        apply_auto_advance(projection, career, event.id)
        return pending_idx

    def continues_career_progress(self) -> bool:
        return False


class GainSkillAndConnectionEntry(CareerTableEntry):
    skill: AnySkill
    connection: ConnectionKind

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.grant_skill(self.skill)
        projection.add_connection(self.connection, origin=self.text)
        return pending_idx


class GainConnectionAndAdvancementDmEntry(CareerTableEntry):
    connection: ConnectionKind
    amount: int

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.add_connection(self.connection, origin=self.text)
        projection.add_advancement_dm(self.amount)
        return pending_idx


class GainConnectionAndBenefitDmEntry(CareerTableEntry):
    connection: ConnectionKind
    amount: int

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.add_connection(self.connection, origin=self.text)
        projection.add_benefit_dm(self.amount)
        return pending_idx


class GainConnectionAndParoleThresholdChangeEntry(CareerTableEntry):
    connection: ConnectionKind
    amount: int

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.add_connection(self.connection, origin=self.text)
        projection.adjust_parole_threshold(self.amount)
        return pending_idx


class GainConnectionAndSkillChoiceEntry(CareerTableEntry):
    connection: ConnectionKind
    options: list[AnySkill | AdvancementDmOption]
    level: int = 1

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.skill_events import PendingSkillChoice

        projection.add_connection(self.connection, origin=self.text)
        projection.pending_inputs.append(
            PendingSkillChoice(
                pending_id=(event.id, pending_idx),
                instruction=f'Choose one skill at level {self.level}',
                options=cast(Any, self.options),
                level=self.level,
            )
        )
        return pending_idx + 1

    def continues_career_progress(self) -> bool:
        return False


class GainConnectionsAndSkillChoiceEntry(CareerTableEntry):
    connections: list[ConnectionKind]
    options: list[AnySkill | AdvancementDmOption]
    level: int = 1

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.skill_events import PendingSkillChoice

        for connection in self.connections:
            projection.add_connection(connection, origin=self.text)
        projection.pending_inputs.append(
            PendingSkillChoice(
                pending_id=(event.id, pending_idx),
                instruction=f'Choose one skill at level {self.level}',
                options=cast(Any, self.options),
                level=self.level,
            )
        )
        return pending_idx + 1

    def continues_career_progress(self) -> bool:
        return False


class InjuryAndGainConnectionEntry(CareerTableEntry):
    severity: Literal['normal', 'severe', 'from_table'] = Field(default='normal')
    connection: ConnectionKind

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        from ceres.character.domain.health.health_events import PendingCharacteristicChoice, PendingInjuryTable

        if self.severity == 'normal':
            projection.pending_inputs.append(
                PendingCharacteristicChoice(
                    pending_id=(event.id, pending_idx),
                    instruction='Injured: choose STR, DEX, or END to reduce by 1',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                    amount=1,
                )
            )
        elif self.severity == 'severe':
            projection.pending_inputs.append(
                PendingCharacteristicChoice(
                    pending_id=(event.id, pending_idx),
                    instruction='Severely injured: choose STR, DEX, or END to reduce by 2',
                    options=[Chars.STR, Chars.DEX, Chars.END],
                    amount=2,
                )
            )
        elif self.severity == 'from_table':
            projection.pending_inputs.append(
                PendingInjuryTable(
                    pending_id=(event.id, pending_idx),
                    instruction='Roll 1D on Injury table',
                )
            )
        projection.add_connection(self.connection, origin=self.text)
        return pending_idx + 1


class AdvancementDmEntry(CareerTableEntry):
    amount: int

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.add_advancement_dm(self.amount)
        return pending_idx


class QualificationDmEntry(CareerTableEntry):
    amount: int

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.add_qualification_dm(self.amount)
        return pending_idx


class BenefitDmEntry(CareerTableEntry):
    amount: int

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.add_benefit_dm(self.amount)
        return pending_idx


class ParoleThresholdChangeEntry(CareerTableEntry):
    amount: int

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.adjust_parole_threshold(self.amount)
        return pending_idx


class AutoQualifyCareerEntry(CareerTableEntry):
    # Pydantic cannot use `type[CareerData]` here: the field named `type` shadows the builtin
    # during annotation evaluation. Any is used; the value is always a CareerData subclass.
    career: Any

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.auto_qualify(self.career)
        return pending_idx


class LoseAllCareerBenefitsEntry(CareerTableEntry):
    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.forfeit_current_career_benefits()
        return pending_idx


class LoseAllCareerBenefitsAndGainConnectionEntry(CareerTableEntry):
    connection: ConnectionKind

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        projection.forfeit_current_career_benefits()
        projection.add_connection(self.connection, origin=self.text)
        return pending_idx


class CareerHandlerBase(CareerTableEntry):
    """Base for career-specific event/mishap table rows.

    Subclasses declare ``type: Literal['handler_key'] = 'handler_key'`` and implement
    ``handle()`` to append career-specific pending inputs.
    """

    text: str = ''
    type: str

    @staticmethod
    def handle(projection: CharacterProjection, event_id: int, pending_idx: int) -> int:
        return pending_idx

    def apply(self, projection: CharacterProjection, event: Any, pending_idx: int) -> int:
        return self.handle(projection, event.id, pending_idx)

    def continues_career_progress(self) -> bool:
        return False


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
    | QualificationDmEffect
    | BenefitDmEffect
    | ParoleThresholdChangeEffect
    | AutoQualifyCareerEffect
    | LoseAllCareerBenefitsEffect
    | CareerHandlerBase
)


class CareerEventEntry(CareerTableEntry):
    text: str
    effects: list[AnyEffect] = []


class TermData(BaseModel):
    """Base class for both CareerData and PreCareerData, capturing their common interface."""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MishapEntry(CareerTableEntry):
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

    def rank_title(self, commissioned: bool, rank: int, assignment: AssignmentData | None = None) -> tuple[str, str]:
        if commissioned and self.officer_ranks:
            return (f'O{rank}', self._latest_rank_title(self.officer_ranks, rank))
        ranks = self.assignment_ranks(self.assignment_index(assignment)) if assignment is not None else self.ranks
        code = f'E{rank}' if self.commission is not None else str(rank)
        return (code, self._latest_rank_title(ranks, rank))

    @staticmethod
    def _latest_rank_title(ranks: dict[int, RankEntry], rank: int) -> str:
        return next(
            (
                entry.title
                for entry_rank, entry in sorted(ranks.items(), reverse=True)
                if entry_rank <= rank and entry.title
            ),
            '',
        )

    def is_selectable(self, projection=None) -> bool:
        return self.selectable

    def is_in_draft(self, summary) -> int:
        """Return positive weight if this career is in the draft table, 0 otherwise.

        Default: non-empty draft_assignments → weight 1.  Override to return a
        different weight (e.g. for sophont-specific draft tables per RIC-003).
        """
        return 1 if self.draft_assignments else 0

    def is_draft_alternative(self, summary) -> bool:
        """Return True if this career is offered as an alternative to the draft."""
        return False

    def does_draft(self) -> bool:
        return self.is_in_draft(None) > 0

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

        # Check for auto-qualify from pre-career graduation or career mishap
        if type(self) in projection.auto_qualify_careers:
            projection.auto_qualify_careers.remove(type(self))
            self.start_new_term(projection, assignment, event_id)
            return

        target = self.qualification.target
        dm = self.qualification_dm(projection)
        dm += projection.pending_qualification_dm
        projection.pending_qualification_dm = 0
        if qualification_roll + dm < target:
            self.qualification_failed(projection, event_id)
            return

        self.start_new_term(projection, assignment, event_id)

    def qualification_failed(self, projection, event_id: int) -> None:
        from ceres.character.domain.career.career_events import PendingDraftChoice

        projection.summary.problems.append(f'Failed to qualify for {self.name}.')
        projection.pending_inputs.append(
            PendingDraftChoice(
                pending_id=(event_id, 0),
                instruction='Qualification failed — submit to the draft or become a Drifter',
                can_draft=not projection.summary.drafted,
            )
        )

    def start_new_term(
        self,
        projection,
        assignment: AssignmentData,
        event_id: int,
        is_continuation: bool = False,
    ) -> None:
        training = self._basic_training_plan(projection, assignment, is_continuation)
        projection.summary.rank = self.current_rank(projection.summary.career_terms, assignment)
        first_term_in_run = not self.prior_terms(projection.summary.career_terms, assignment)
        self.append_term(projection, assignment)

        if training is not None:
            self._apply_basic_training(projection, assignment, training.table_name, training.grant_all, event_id)
        else:
            self._queue_skill_table_before_survival(projection, assignment, event_id)
        if first_term_in_run:
            self._apply_fixed_rank_bonus(projection, 0, event_id)

    def _basic_training_table_name(self, assignment: AssignmentData) -> str:
        return 'service_skills'

    def _apply_fixed_rank_bonus(self, projection, rank: int, event_id: int = 0) -> None:
        rank_entry = self.current_ranks(projection).get(rank)
        if not rank_entry or not rank_entry.bonus:
            return
        bonus = rank_entry.bonus
        choices = bonus.resolve_choices()
        if choices:
            from ceres.character.domain.career.career_events import PendingRankBonusChoice

            valid_choices = [
                choice
                for choice in choices
                if (isinstance(choice, Psi) or projection.skill_choices([type(choice)], bonus.level))
            ]
            if valid_choices:
                used_sub_ids = {p.pending_id[1] for p in projection.pending_inputs if p.pending_id[0] == event_id}
                projection.pending_inputs.append(
                    PendingRankBonusChoice(
                        pending_id=(event_id, max(used_sub_ids, default=-1) + 1),
                        level=bonus.level,
                        instruction=f'Rank {rank} bonus: choose skill at level {bonus.level}',
                        options=cast(list[CareerSkillOption | AdvancementDmOption], valid_choices),
                        continue_career_progress=False,
                    )
                )
            return
        if bonus.skill:
            from ceres.character.domain.career.career_events import _rank_bonus_skill

            projection.grant_skill(_rank_bonus_skill(bonus))
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
                if not choices and isinstance(entry, Psi):
                    continue
                if len(choices) > 1 or isinstance(entry, Psi):
                    skills = ', '.join(self._training_option_name(s) for s in choices)
                    projection.pending_inputs.append(
                        PendingInitialTrainingChoice(
                            pending_id=(event_id, choice_idx),
                            instruction=f'Initial training: choose one of {skills}',
                            options=cast(list[CareerSkillOption | AdvancementDmOption], choices),
                        )
                    )
                    choice_idx += 1
                else:
                    self._apply_initial_training_entry(projection, entry)
            if choice_idx == 0:
                projection.pending_inputs.append(self.survival_pending(assignment, event_id))
            return

        from ceres.character.domain.career.career_events import PendingInitialTrainingChoice

        raw: list[CareerSkillOption] = []
        for entry in table.entries:
            raw.extend(self._training_selectable_skills(projection, entry))
        by_name: dict[str, CareerSkillOption] = {}
        for s in raw:
            by_name.setdefault(self._training_option_name(s), s)
        deduped: list[CareerSkillOption] = sorted(by_name.values(), key=self._training_option_name)
        if deduped:
            projection.pending_inputs.append(
                PendingInitialTrainingChoice(
                    pending_id=(event_id, 0),
                    instruction=f'Basic training: choose one skill at level 0 from {table_name}',
                    options=cast(list[CareerSkillOption | AdvancementDmOption], deduped),
                )
            )
        else:
            projection.pending_inputs.append(self.survival_pending(assignment, event_id))

    def _apply_initial_training_entry(self, projection, entry: SkillTableEntry) -> None:
        if isinstance(entry, Chars):
            return  # characteristic boosts are not granted during basic training
        if isinstance(entry, Psi):
            return  # basic training neither acquires nor improves psionic talents
        if isinstance(entry, list):
            # Choice entry: add all unknown skills at level 0
            for skill in entry:
                if isinstance(skill, Psi):
                    continue
                skill_cls = type(skill)
                if projection.summary.skill_level(skill_cls) is None:
                    projection.summary.skills.append(skill_cls())
        else:
            # Single AnySkill entry
            skill_cls = type(entry)
            if projection.summary.skill_level(skill_cls) is None:
                projection.summary.skills.append(skill_cls())

    def _training_pending_choices(self, projection, entry: SkillTableEntry) -> list[CareerSkillOption]:
        if isinstance(entry, Chars):
            return []
        if isinstance(entry, Psi):
            return []
        if isinstance(entry, list):
            return self._unknown_training_skills(projection, entry)
        skill_cls = type(entry)
        fields = level_fields(skill_cls)
        spec_field = next((f for f in fields if getattr(entry, f).value > 0), None)
        if spec_field is not None:
            return []
        if projection.summary.skill_level(skill_cls) is None:
            return [skill_cls()]
        return []

    def _training_selectable_skills(self, projection, entry: SkillTableEntry) -> list[CareerSkillOption]:
        if isinstance(entry, Chars):
            return []
        if isinstance(entry, Psi):
            return []
        if isinstance(entry, list):
            return self._unknown_training_skills(projection, entry)
        skill_cls = type(entry)
        if projection.summary.skill_level(skill_cls) is None:
            return [skill_cls()]
        return []

    @staticmethod
    def _training_option_name(option: CareerSkillOption) -> str:
        return type(option.talent).name() if isinstance(option, Psi) else type(option).name()

    def _training_option_is_unknown(self, projection, option: CareerSkillOption) -> bool:
        if isinstance(option, Psi):
            return False
        return projection.summary.skill_level(type(option)) is None

    def _unknown_training_skills(self, projection, options: list[AnySkill] | list[Psi]) -> list[CareerSkillOption]:
        by_type: dict[type[Any], CareerSkillOption] = {}
        for option in options:
            if isinstance(option, Psi) or not self._training_option_is_unknown(projection, option):
                continue
            skill_cls = type(option)
            by_type.setdefault(skill_cls, skill_cls())
        return list(by_type.values())

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

    def skill_table_option_is_available(
        self,
        projection: CharacterProjection,
        table_name: str,
        option: CareerSkillOption,
    ) -> bool:
        return True


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
    rolls_remaining: int = 0
    pending_setup: bool = False

    def setup(self, rank: int) -> None:
        self.pending_setup = False
        self.rolls_remaining = max(0, self.terms + (rank + 1) // 2 + self.extra_rolls - self.lost_rolls)
        if self.rolls_remaining == 0:
            self.used = True

    def forfeit_all_rolls(self) -> None:
        self.lost_rolls = 9999


class CareerTerm(BaseModel):
    career: CareerData
    assignment: AssignmentData
    commission: bool = False
    rank_after_term: int = 0
    muster_out: MusterOut | None = Field(default_factory=MusterOut)
    event: str | None = None
    mishap: str | None = None
    prison: str | None = None

    @property
    def rank_title(self) -> tuple[str, str]:
        return self.career.rank_title(self.commission, self.rank_after_term, self.assignment)

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
