from typing import TYPE_CHECKING

from pydantic import BaseModel

from ceres.character.careers.career_data import AnyEffect, CareerEventEntry, CharCheck, SkillTableEntry
from ceres.character.events import PendingPreCareerSkillChoice
from ceres.character.state import (
    CharacterProjection,
    CharacterSummary,
)

if TYPE_CHECKING:
    from ceres.character.events import PreCareerEntryEvent, PreCareerGraduationEvent


class PreCareerData(BaseModel):
    name: str
    source: str
    duration_years: int = 4
    entry: CharCheck | None = None
    entry_requirement: str | None = None
    entry_term_dms: dict[int, int] = {}
    entry_soc_bonus_min: int | None = None
    entry_soc_bonus: int = 0
    curriculum_table: str | None = None
    skill_choices: list[SkillTableEntry] = []
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
    events: dict[int, CareerEventEntry]

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
        from ceres.character.skills import skill_from_str, skill_names_for_category

        if self.entry_pick_count == 0:
            for entry in self.skill_choices:
                if not entry.skill:
                    continue
                expanded = skill_names_for_category(entry.skill)
                if expanded:
                    instr = f'{self.name}: choose one {entry.skill} specialisation at level {entry.level}'
                    projection.pending_inputs.append(
                        PendingPreCareerSkillChoice(
                            id=f'{event.id}.{pending_idx}',
                            level=entry.level,
                            instruction=instr,
                            options=expanded,
                        )
                    )
                    pending_idx += 1
                else:
                    projection.grant_skill(skill_from_str(entry.skill, entry.level))
        else:
            choice_pool: list[str] = []
            for entry in self.skill_choices:
                if not entry.skill:
                    continue
                expanded = skill_names_for_category(entry.skill)
                names = expanded if expanded is not None else [entry.skill]
                if entry.level >= 1:
                    if expanded:
                        instr = f'{self.name}: choose one {entry.skill} specialisation at level {entry.level}'
                        projection.pending_inputs.append(
                            PendingPreCareerSkillChoice(
                                id=f'{event.id}.{pending_idx}',
                                level=entry.level,
                                instruction=instr,
                                options=expanded,
                            )
                        )
                        pending_idx += 1
                    else:
                        projection.grant_skill(skill_from_str(entry.skill, entry.level))
                else:
                    choice_pool.extend(names)
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


__all__ = ['AnyEffect', 'PreCareerData']
