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
    columns: list[tuple[str, str]] = field(default_factory=list)  # (header, value) for multi-column rows
    notes: NoteList = field(default_factory=NoteList)


@dataclass
class RobotDetailRow:
    name: str
    col2: str = '—'
    cost: str = '—'


@dataclass
class RobotDetailSection:
    title: str
    col2_header: str = 'Slots'
    rows: list[RobotDetailRow] = field(default_factory=list)


@dataclass
class RobotSpec:
    name: str
    tl: int
    _rows: list[RobotSpecRow] = field(default_factory=list)
    robot_notes: NoteList = field(default_factory=NoteList)
    detail_sections: list[RobotDetailSection] = field(default_factory=list)

    def add_row(self, row: RobotSpecRow) -> None:
        self._rows.append(row)

    @property
    def rows(self) -> list[RobotSpecRow]:
        order = list(RobotSpecSection)
        return sorted(self._rows, key=lambda r: order.index(r.section))

    def rows_for_section(self, section: RobotSpecSection) -> list[RobotSpecRow]:
        return [r for r in self._rows if r.section is section]


__all__ = ['RobotSpecSection', 'RobotSpecRow', 'RobotSpec', 'RobotDetailRow', 'RobotDetailSection']
