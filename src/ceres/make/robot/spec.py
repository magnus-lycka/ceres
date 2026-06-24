from enum import StrEnum

from pydantic import BaseModel, Field, PrivateAttr, computed_field

from ceres.shared import NoteList


class RobotSpecSection(StrEnum):
    ROBOT = 'Robot'
    SKILLS = 'Skills'
    ATTACKS = 'Attacks'
    MANIPULATORS = 'Manipulators'
    ENDURANCE = 'Endurance'
    TRAITS = 'Traits'
    PROGRAMMING = 'Programming'
    OPTIONS = 'Options'


class RobotSpecRow(BaseModel):
    section: RobotSpecSection
    label: str
    value: str = ''
    columns: list[tuple[str, str]] = Field(default_factory=list)
    notes: NoteList = Field(default_factory=NoteList)


class RobotDetailRow(BaseModel):
    name: str
    col2: str = '—'
    col3: str = '—'
    cost: str = '—'


class RobotDetailSection(BaseModel):
    title: str
    col2_header: str = 'Slots'
    col3_header: str = 'Bandwidth'
    rows: list[RobotDetailRow] = Field(default_factory=list)


class RobotSpec(BaseModel):
    name: str
    tl: int
    robot_notes: NoteList = Field(default_factory=NoteList)
    detail_sections: list[RobotDetailSection] = Field(default_factory=list)
    _rows: list[RobotSpecRow] = PrivateAttr(default_factory=list)

    def add_row(self, row: RobotSpecRow) -> None:
        self._rows.append(row)

    @computed_field
    @property
    def rows(self) -> list[RobotSpecRow]:
        order = list(RobotSpecSection)
        return sorted(self._rows, key=lambda r: order.index(r.section))

    def rows_for_section(self, section: RobotSpecSection) -> list[RobotSpecRow]:
        return [r for r in self._rows if r.section is section]
