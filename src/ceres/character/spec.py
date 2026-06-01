from pydantic import BaseModel, Field

from ceres.character.benefits import ItemBenefit
from ceres.character.characteristics import Chars
from ceres.character.skills import AnySkill, _level_fields
from ceres.character.state import CharacterSummary


class NpcSpec(BaseModel):
    name: str
    career: str | None = None
    assignment: str | None = None
    rank: int | None = None
    terms: int = 0
    sophont: str = 'Human'
    ucp: str = ''
    characteristics: dict[Chars, int] = Field(default_factory=dict)
    age: int = 18
    skills: list[AnySkill] = Field(default_factory=list)
    equipment: list[ItemBenefit] = Field(default_factory=list)
    cash: int = 0
    notes: str | None = None


def spec_from_summary(summary: CharacterSummary, notes: str | None = None) -> NpcSpec:
    from ceres.character.characteristics import UCP_STATS

    ucp = ''.join(f'{summary.characteristics.get(stat, 0):X}' for stat in UCP_STATS)
    career = summary.current_career or summary.last_career
    assignment = summary.current_assignment or summary.last_assignment
    return NpcSpec(
        name=summary.name or 'Unknown',
        career=career,
        assignment=assignment,
        rank=summary.rank,
        terms=summary.term_count,
        sophont=summary.sophont.name,
        ucp=ucp,
        characteristics=dict(summary.characteristics),
        age=summary.age,
        skills=list(summary.skills),
        equipment=list(summary.benefits),
        cash=summary.cash,
        notes=notes,
    )


def format_npc_skills(skills: list[AnySkill]) -> str:
    parts: list[str] = []
    for skill in sorted(skills, key=lambda s: type(s).name()):
        parts.extend(_format_npc_skill(skill))
    return ', '.join(parts)


_NBSP = ' '  # non-breaking space — keeps level number with preceding word/paren


def _format_npc_skill(skill: AnySkill) -> list[str]:
    fields = _level_fields(type(skill))
    if not fields:
        return []
    name = type(skill).name()
    if len(fields) == 1:
        lvl = getattr(skill, fields[0]).value
        return [f'{name}{_NBSP}{lvl}']
    spec_names = type(skill).specialities()
    levels = [getattr(skill, f).value for f in fields]
    non_zero = [(sname, lvl) for sname, lvl in zip(spec_names, levels, strict=False) if lvl > 0]
    if not non_zero:
        return [f'{name}{_NBSP}0']
    if len(set(levels)) == 1:
        return [f'{name} (all){_NBSP}{levels[0]}']
    return [f'{name} ({sname}){_NBSP}{lvl}' for sname, lvl in non_zero]


__all__ = ['NpcSpec', 'format_npc_skills', 'spec_from_summary']
