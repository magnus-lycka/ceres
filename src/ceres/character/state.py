from typing import TYPE_CHECKING, Annotated, Any, Literal, cast, overload

from pydantic import BaseModel, Field, SerializeAsAny

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.benefits import ItemBenefit
from ceres.character.characteristics import Chars, ConnectionKind

if TYPE_CHECKING:
    from ceres.character.careers.career_data import CareerData
from ceres.character.careers.career_data import Career
from ceres.character.input_specs import InputSpec
from ceres.character.skills import AnySkill, Level, Skill, _level_fields
from ceres.character.sophonts import Sophont
from ceres.shared import CeresModel


class ReplayError(Exception):
    pass


class PendingInputBase(BaseModel):
    id: str
    kind: str
    instruction: str
    options: list[str] = Field(default_factory=list)
    blocking: bool = True

    def event_from_form(self, form: Any) -> Any:
        """Construct the appropriate AnyEvent from submitted form data. All subclasses must implement."""
        raise NotImplementedError(f'{type(self).__name__}.event_from_form() not implemented')

    def input_specs(self, projection: CharacterProjection) -> list[InputSpec]:
        """Return web-agnostic InputSpec descriptors for rendering this pending input. All subclasses must implement."""
        raise NotImplementedError(f'{type(self).__name__}.input_specs() not implemented')

    def on_choice(self, projection: Any, event: Any) -> None:
        """Called by CareerChoiceEvent.apply() when this pending is fulfilled. Override in career-specific subclasses."""

    def resolve(self, projection: Any, event: Any) -> None:
        """Called by SkillRollEvent.apply() when this pending is fulfilled. Override in career-specific subclasses."""


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
    career: Career
    assignment: str
    assignment_index: int = 0
    commission: bool = False
    rank_after_term: int = 0


class CharacterSummary(BaseModel):
    name: str
    age: int = 18
    sophont: Sophont
    homeworld: TravellerMapWorld
    characteristics: dict[Chars, int] = Field(default_factory=dict)
    current_career: Career | None = None
    current_assignment: str | None = None
    current_assignment_index: int | None = None
    last_career: Career | None = None
    last_assignment: str | None = None  # assignment name after muster-out
    last_assignment_index: int | None = None
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
    precareer_skills: list[SerializeAsAny[AnySkill]] = Field(
        default_factory=list
    )  # skills chosen during university (for graduation boost)
    parole_threshold: int | None = None  # Prisoner career: current Parole Threshold (3-12)

    @overload
    def skill_level(self, skill_cls: type[Skill], default: int) -> int: ...
    @overload
    def skill_level(self, skill_cls: type[Skill], default: None = None) -> int | None: ...
    def skill_level(self, skill_cls: type[Skill], default: int | None = None) -> int | None:
        for skill in self.skills:
            if type(skill) is skill_cls:
                fields = _level_fields(skill_cls)
                if not fields:
                    return 0
                return max(getattr(skill, f).value for f in fields)
        return default


class CharacterProjection(BaseModel):
    character_id: int
    summary: CharacterSummary
    pending_inputs: list[SerializeAsAny[PendingInputBase]] = Field(default_factory=list)
    scheduled_effects: list[ScheduledEffect] = Field(default_factory=list)
    pending_reenlist: bool | None = None  # stores reenlist decision during aging chain
    muster_out_career: Career | None = None
    forced_next_career: Career | None = None  # set by prison-sending events; consumed by next career choice
    prisoner_freed: bool = False  # set by _apply_prisoner_advancement when parole granted

    def has_blocking_pending(self) -> bool:
        return any(p.blocking for p in self.pending_inputs)

    def clear_current_career(self) -> None:
        if self.summary.current_career is not None:
            self.summary.last_career = self.summary.current_career
            self.summary.last_assignment = self.summary.current_assignment
            self.summary.last_assignment_index = self.summary.current_assignment_index
        self.summary.current_career = None
        self.summary.current_assignment = None
        self.summary.current_assignment_index = None

    def get_current_career(self) -> CareerData:
        from ceres.character.careers.loader import load_careers

        current = self.summary.current_career
        if current is None:
            raise ReplayError('No active career')
        careers = load_careers()
        career = careers.get(current.name)
        if career is None:
            raise ReplayError(f'Unknown career: {current.name!r}')
        return career

    def fulfill_pending(self, event: Any) -> None:
        fulfills = event.fulfills
        matched = next((p for p in self.pending_inputs if p.id == fulfills), None)
        if matched is None:
            raise ReplayError(f'Event {event.id} ({event.kind!r}) references unknown pending input {fulfills!r}')
        self.pending_inputs.remove(matched)

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

    def increment_skill(self, skill: AnySkill) -> None:
        skill_cls = type(skill)
        existing = next((s for s in self.summary.skills if type(s) is skill_cls), None)
        fields = _level_fields(skill_cls)
        active_field = next((f for f in fields if getattr(skill, f).value > 0), None)
        target_field = active_field or (fields[0] if fields else None)
        if existing is None:
            new_skill = skill_cls()
            if target_field:
                getattr(new_skill, target_field).set(1)
            self.summary.skills.append(new_skill)
            return
        if (active_field is not None or len(fields) == 1) and target_field:
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


def diff_summaries(before: CharacterSummary, after: CharacterSummary) -> list[str]:
    """Human-readable strings describing mechanical changes between two summaries."""
    changes: list[str] = []

    changes.extend(after.narrative[len(before.narrative) :])

    if after.current_career != before.current_career and after.current_career:
        line = f'Joined {after.current_career.name}'
        if after.current_assignment:
            line += f' ({after.current_assignment})'
        changes.append(line)

    if after.rank is not None and after.rank != before.rank:
        changes.append(f'Rank {before.rank or 0} → {after.rank}')

    all_chars = set(before.characteristics) | set(after.characteristics)
    for char in sorted(all_chars, key=lambda c: c.value):
        b_val = before.characteristics.get(char, 0)
        a_val = after.characteristics.get(char, 0)
        if a_val != b_val:
            changes.append(f'{char.value} {b_val} → {a_val}')

    before_by_type = {type(s): s for s in before.skills}
    after_by_type = {type(s): s for s in after.skills}
    new_types = sorted(set(after_by_type) - set(before_by_type), key=lambda cls: cls.name())
    changes.extend(f'Gained {cls.name()} {after.skill_level(cls, 0)}' for cls in new_types)
    for cls in sorted(set(after_by_type) & set(before_by_type), key=lambda cls: cls.name()):
        b_lvl = before.skill_level(cls, 0)
        a_lvl = after.skill_level(cls, 0)
        if a_lvl != b_lvl:
            changes.append(f'{cls.name()} {b_lvl} → {a_lvl}')

    if after.cash != before.cash:
        delta = after.cash - before.cash
        sign = '+' if delta > 0 else ''
        changes.append(f'Cash {sign}Cr{delta:,}')

    changes.extend(f'Benefit: {b.display_label}' for b in after.benefits[len(before.benefits) :])
    changes.extend(f'New {c.kind}: {c.source or "unknown"}' for c in after.connections[len(before.connections) :])
    changes.extend(f'Problem: {p}' for p in after.problems[len(before.problems) :])

    return changes


__all__ = [
    'Ally',
    'AnyConnection',
    'CareerTerm',
    'CharacterProjection',
    'CharacterSummary',
    'Connection',
    'Contact',
    'Enemy',
    'PendingInputBase',
    'ReplayError',
    'Rival',
    'ScheduledEffect',
    'diff_summaries',
    'make_connection',
]
