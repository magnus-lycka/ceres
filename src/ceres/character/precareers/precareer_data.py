from pydantic import BaseModel

from ceres.character.careers.career_data import AnyEffect, CareerEventEntry, CharCheck, SkillTableEntry


class PreCareerData(BaseModel):
    name: str
    source: str
    duration_years: int = 4
    entry: CharCheck | None = None
    entry_requirement: str | None = None
    entry_term_dms: dict[int, int] = {}
    entry_soc_bonus_min: int | None = None
    entry_soc_bonus: int = 0
    curricula: list[str] = []
    skill_choices: list[SkillTableEntry] = []
    service_skills_from: str | None = None
    tied_career: str | None = None
    graduation: CharCheck | None = None
    graduation_requirement: str | None = None
    graduation_dms: dict[str, int] = {}
    honours_target: int | None = None
    graduation_benefits: list[str] = []
    events: dict[int, CareerEventEntry]


__all__ = ['AnyEffect', 'PreCareerData']
