from pydantic import BaseModel


class CharCheck(BaseModel):
    characteristic: str
    target: int


class SkillTableEntry(BaseModel):
    skill: str | None = None
    characteristic: str | None = None  # for +1 characteristic entries
    level: int = 1
    choices: list[str] | None = None  # if multiple skill options (e.g. "Drive or Flyer")


class SkillTable(BaseModel):
    min_edu: int | None = None
    entries: dict[int, SkillTableEntry]


class RankBonus(BaseModel):
    skill: str | None = None
    characteristic: str | None = None
    level: int = 1


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
    effects: list[EventEffect] = []


class AssignmentData(BaseModel):
    name: str
    survival: CharCheck
    advancement: CharCheck


class CareerData(BaseModel):
    name: str
    source: str
    qualification: CharCheck
    assignments: list[AssignmentData]
    skill_tables: dict[str, SkillTable]  # keyed by table name, e.g. 'service_skills' or assignment name
    ranks: dict[int, RankEntry]  # rank number → rank entry
    events: dict[int, CareerEventEntry]  # 2D roll → event
    mishaps: dict[int, MishapEntry]  # 1D roll → mishap

    def assignment(self, name: str) -> AssignmentData | None:
        return next((a for a in self.assignments if a.name == name), None)

    def skill_table(self, name: str) -> SkillTable | None:
        return self.skill_tables.get(name)
