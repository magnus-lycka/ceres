from enum import StrEnum

from pydantic import BaseModel, Field, PrivateAttr, computed_field

from ceres.shared import NoteList


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
    SCREENS = 'Screens'
    CRAFT = 'Craft'
    HABITATION = 'Habitation'
    SYSTEMS = 'Systems'
    CARGO = 'Cargo'


class SpecRow(BaseModel):
    section: SpecSection
    item: str
    quantity: int | None = None
    tons: float | None = None
    power: float | None = None  # positive = produces power, negative = consumes power
    cost: float | None = None
    emphasize_tons: bool = False
    emphasize_power: bool = False
    notes: NoteList = Field(default_factory=NoteList)


class ExpenseRow(BaseModel):
    label: str
    amount: float


class CrewRow(BaseModel):
    role: str
    salary: int
    quantity: int | None = None


class PassengerRow(BaseModel):
    kind: str
    quantity: int


class ShipSpec(BaseModel):
    ship_class: str | None = None
    ship_type: str | None = None
    tl: int | None = None
    hull_points: float | None = None
    ship_notes: NoteList = Field(default_factory=NoteList)
    crew_notes: NoteList = Field(default_factory=NoteList)
    expenses: list[ExpenseRow] = Field(default_factory=list)
    crew: list[CrewRow] = Field(default_factory=list)
    passengers: list[PassengerRow] = Field(default_factory=list)
    _sections: dict[SpecSection, list[SpecRow]] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context) -> None:
        for section in SpecSection:
            self._sections.setdefault(section, [])

    def add_row(self, row: SpecRow, section: SpecSection | str | None = None) -> None:
        target = SpecSection(section) if section is not None else row.section
        self._sections[target].append(row)

    @computed_field
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
