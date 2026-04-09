from dataclasses import dataclass, field
from enum import StrEnum

from .base import Note


# Update the sections to merge jump and propulsion into drive
# See docs/plan-ship-sections.md and docs/todo_maybe.md
class SpecSection(StrEnum):
    HULL = 'Hull'
    JUMP = 'Jump'
    PROPULSION = 'Propulsion'
    POWER = 'Power'
    FUEL = 'Fuel'
    COMMAND = 'Command'
    COMPUTER = 'Computer'
    SENSORS = 'Sensors'
    WEAPONS = 'Weapons'
    CRAFT = 'Craft'
    HABITATION = 'Habitation'
    SYSTEMS = 'Systems'
    CARGO = 'Cargo'


@dataclass
class SpecRow:
    section: SpecSection
    item: str
    quantity: int | None = None
    tons: float | None = None
    power: float | None = None  # positive = produces power, negative = consumes power
    cost: float | None = None
    emphasize_tons: bool = False
    emphasize_power: bool = False
    notes: list[Note] = field(default_factory=list)


@dataclass
class ExpenseRow:
    label: str
    amount: float


@dataclass
class CrewRow:
    role: str
    salary: int
    quantity: int | None = None


@dataclass
class ShipSpec:
    ship_class: str | None = None
    ship_type: str | None = None
    tl: int | None = None
    hull_points: float | None = None
    _sections: dict[SpecSection, list[SpecRow]] = field(default_factory=dict)
    expenses: list[ExpenseRow] = field(default_factory=list)
    crew: list[CrewRow] = field(default_factory=list)

    def __post_init__(self) -> None:
        for section in SpecSection:
            self._sections.setdefault(section, [])

    def add_row(self, row: SpecRow, section: SpecSection | str | None = None) -> None:
        target = SpecSection(section) if section is not None else row.section
        self._sections[target].append(row)

    @property
    def rows(self) -> list[SpecRow]:
        rows: list[SpecRow] = []
        for section in SpecSection:
            rows.extend(self._sections.get(section, []))
        return rows

    def rows_for_section(self, section: SpecSection | str) -> list[SpecRow]:
        wanted = SpecSection(section)
        return list(self._sections.get(wanted, []))

    def row(self, item: str, section: SpecSection | str | None = None) -> SpecRow:
        wanted = SpecSection(section) if section is not None else None
        for r in self.rows:
            if r.item != item:
                continue
            if wanted is not None and r.section != wanted:
                continue
            return r
        if section is None:
            raise KeyError(f'No spec row with item={item!r}')
        raise KeyError(f'No spec row with item={item!r} in section={section!r}')

    def rows_matching(self, item: str) -> list[SpecRow]:
        return [r for r in self.rows if r.item == item]
