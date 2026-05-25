from pydantic import BaseModel

from ceres.character.benefits import AnyBenefit
from ceres.character.characteristics import Chars


class CharCheck(BaseModel):
    characteristic: Chars
    target: int


class SkillTableEntry(BaseModel):
    skill: str | None = None
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


class EventEffect(BaseModel):
    type: str
    # Fields vary by type; store extras in a flexible dict
    model_config = {'extra': 'allow'}


class CareerEventEntry(BaseModel):
    text: str
    effects: list[EventEffect] = []


class MishapEntry(BaseModel):
    text: str
    stay_in_career: bool = False
    defer_ejection: bool = False  # handler owns ejection flow; no auto-purge or advancement pending
    effects: list[EventEffect] = []


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


class CareerData(BaseModel):
    name: str
    source: str
    qualification: CharCheck
    assignments: list[AssignmentData]
    skill_tables: dict[str, SkillTable]  # keyed by table name, e.g. 'service_skills' or assignment name
    ranks: dict[int, RankEntry]  # default rank table (used when no per-assignment override)
    ranks_by_assignment: dict[str, dict[int, RankEntry]] = {}  # assignment name → rank table override
    events: dict[int, CareerEventEntry]  # 2D roll → event
    mishaps: dict[int, MishapEntry]  # 1D roll → mishap
    muster_out: MusterOutData | None = None
    allows_assignment_change: bool

    def assignment(self, name: str) -> AssignmentData | None:
        return next((a for a in self.assignments if a.name == name), None)

    def skill_table(self, name: str) -> SkillTable | None:
        return self.skill_tables.get(name)

    def assignment_ranks(self, assignment_name: str) -> dict[int, RankEntry]:
        return self.ranks_by_assignment.get(assignment_name, self.ranks)

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
