from dataclasses import dataclass, field
from enum import StrEnum

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


@dataclass
class RobotSpecRow:
    section: RobotSpecSection
    label: str
    value: str = ''
    notes: NoteList = field(default_factory=NoteList)


@dataclass
class RobotSpec:
    name: str
    tl: int
    _rows: list[RobotSpecRow] = field(default_factory=list)
    robot_notes: NoteList = field(default_factory=NoteList)

    def add_row(self, row: RobotSpecRow) -> None:
        self._rows.append(row)

    @property
    def rows(self) -> list[RobotSpecRow]:
        order = list(RobotSpecSection)
        return sorted(self._rows, key=lambda r: order.index(r.section))

    def rows_for_section(self, section: RobotSpecSection) -> list[RobotSpecRow]:
        return [r for r in self._rows if r.section is section]


__all__ = ['RobotSpecSection', 'RobotSpecRow', 'RobotSpec']
