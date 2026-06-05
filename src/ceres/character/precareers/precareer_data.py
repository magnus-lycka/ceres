from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel, ConfigDict

from ceres.character.careers.career_data import CareerEventEntry, CharCheck, TermData
from ceres.character.events import PendingPreCareerSkillChoice
from ceres.character.skills import AnySkill, Level, _level_fields
from ceres.character.state import (
    CharacterProjection,
    CharacterSummary,
)

if TYPE_CHECKING:
    from ceres.character.events import PreCareerEntryEvent, PreCareerGraduationEvent


class PrecareerSkillEntry(BaseModel):
    """Skill entry used in pre-career skill lists.

    A single skill is a fixed grant/choice. A list of skills represents a broad
    category choice, matching the career skill table pattern.
    """

    skill: AnySkill | list[AnySkill] | None = None
    level: int = 0
    spec: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def skill_options(self) -> list[AnySkill]:
        if self.skill is None:
            return []
        if isinstance(self.skill, list):
            return self.skill
        return [self.skill]

    @property
    def category_label(self) -> str:
        if self.skill is None:
            return 'skill'
        if isinstance(self.skill, list):
            return 'skill'
        return type(self.skill).name()

    def grant_skill(self) -> AnySkill | None:
        if self.skill is None or isinstance(self.skill, list):
            return None
        return _skill_at_level(self.skill, self.level)


def _skill_at_level(skill: AnySkill, level: int) -> AnySkill:
    skill_cls = type(skill)
    cls = cast(type[Any], skill_cls)
    fields = _level_fields(skill_cls)
    if level == 0:
        return cast(AnySkill, cls())
    if len(fields) == 1 and fields[0] == 'level':
        return cast(AnySkill, cls(level=Level(value=level)))
    active = [field for field in fields if getattr(skill, field).value > 0]
    selected = active or fields
    values = {field: Level(value=level if field in selected else 0) for field in fields}
    return cast(AnySkill, cls(**values))


class PreCareerData(TermData):
    events: dict[int, CareerEventEntry]
    name: str
    source: str
    duration_years: int = 4
    entry: CharCheck | None = None
    entry_requirement: str | None = None
    entry_term_dms: dict[int, int] = {}
    entry_soc_bonus_min: int | None = None
    entry_soc_bonus: int = 0
    curriculum_table: str | None = None
    skill_choices: list[PrecareerSkillEntry] = []
    # entry_pick_count > 0: level>=1 skills in skill_choices are auto-granted; player
    # picks entry_pick_count from the level==0 skills. If 0, all skill_choices are auto-granted.
    # University and military academies handle their own entry logic separately.
    entry_pick_count: int = 0
    service_skills_from: str | None = None
    tied_career: str | None = None
    graduation: CharCheck | None = None
    graduation_requirement: str | None = None
    graduation_dms: dict[str, int] = {}
    honours_target: int | None = None
    graduation_benefits: list[str] = []

    def is_available(self, summary: CharacterSummary) -> bool:
        """Return True if this precareer is available for the given character."""
        return True

    def apply_entry(
        self,
        projection: CharacterProjection,
        event: PreCareerEntryEvent,
        pending_idx: int,
    ) -> int:
        """Default: generic companion entry — auto-grant fixed skills, queue picks for categories."""

        if self.entry_pick_count == 0:
            for entry in self.skill_choices:
                if not entry.skill:
                    continue
                if isinstance(entry.skill, list):
                    options = entry.skill_options
                    instr = f'{self.name}: choose one {entry.category_label} specialisation at level {entry.level}'
                    projection.pending_inputs.append(
                        PendingPreCareerSkillChoice(
                            id=f'{event.id}.{pending_idx}',
                            level=entry.level,
                            instruction=instr,
                            options=options,
                        )
                    )
                    pending_idx += 1
                elif grant := entry.grant_skill():
                    projection.grant_skill(grant)
        else:
            choice_pool: list[AnySkill] = []
            for entry in self.skill_choices:
                if not entry.skill:
                    continue
                if entry.level >= 1:
                    if isinstance(entry.skill, list):
                        options = entry.skill_options
                        instr = f'{self.name}: choose one {entry.category_label} specialisation at level {entry.level}'
                        projection.pending_inputs.append(
                            PendingPreCareerSkillChoice(
                                id=f'{event.id}.{pending_idx}',
                                level=entry.level,
                                instruction=instr,
                                options=options,
                            )
                        )
                        pending_idx += 1
                    elif grant := entry.grant_skill():
                        projection.grant_skill(grant)
                else:
                    choice_pool.extend(entry.skill_options)
            for i in range(self.entry_pick_count):
                instr = f'{self.name}: choose skill {i + 1} of {self.entry_pick_count} at level 0'
                projection.pending_inputs.append(
                    PendingPreCareerSkillChoice(
                        id=f'{event.id}.{pending_idx}',
                        level=0,
                        instruction=instr,
                        options=choice_pool,
                    )
                )
                pending_idx += 1
        return pending_idx

    def apply_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
        honours: bool,
    ) -> int:
        """Default: no graduation effects. Returns pending_idx (0)."""
        return 0

    def apply_failed_graduation(
        self,
        projection: CharacterProjection,
        event: PreCareerGraduationEvent,
    ) -> None:
        """Default: no effects on failed graduation."""
