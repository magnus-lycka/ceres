from typing import Any, Literal, cast, overload

from pydantic import BaseModel, Field

from ceres.character.benefits import ItemBenefit
from ceres.character.skills import AnySkill, Level, Skill


class PendingInput(BaseModel):
    id: str
    kind: str
    instruction: str
    options: list[str] = Field(default_factory=list)
    blocking: bool = True


class ScheduledEffect(BaseModel):
    trigger: str
    source_event_id: int
    effect: dict = Field(default_factory=dict)
    expires: str | None = None
    consume: bool = True


class Connection(BaseModel):
    kind: Literal['contact', 'ally', 'rival', 'enemy']
    source: str = ''  # how/when this person entered the character's life


class CharacterSummary(BaseModel):
    name: str | None = None
    age: int = 18
    species: str | None = None
    characteristics: dict[str, int] = Field(default_factory=dict)
    current_career: str | None = None
    current_assignment: str | None = None
    last_career: str | None = None  # career name after muster-out
    last_assignment: str | None = None  # assignment name after muster-out
    rank: int | None = None
    term_count: int = 0
    skills: list[AnySkill] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    narrative: list[str] = Field(default_factory=list)
    cash: int = 0
    benefits: list[ItemBenefit] = Field(default_factory=list)
    muster_out_cash_count: int = 0
    dead: bool = False

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
    pending_inputs: list[PendingInput] = Field(default_factory=list)
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


__all__ = [
    'CharacterProjection',
    'CharacterSummary',
    'Connection',
    'PendingInput',
    'ScheduledEffect',
]
