from typing import Annotated, ClassVar, Literal

from ceres.shared import NoteList, _Note

from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection

"""
This code implements the Starship Automation rules
in Traveller Companion Update 2024.
"""


class Automation(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    level: str

    label: ClassVar[str]
    cost_percent: ClassVar[float]
    crew_factor: ClassVar[float]
    effect_note: ClassVar[str | None]

    def build_item(self) -> str | None:
        return self.label

    def _basis(self) -> float:
        """Hull-config + drives + power basis for the automation cost modifier."""
        ship = self.assembly
        hull = getattr(ship, 'hull', None)
        hull_basis = hull.configuration.automation_basis_cost(ship.displacement) if hull is not None else 0.0
        drives = getattr(ship, 'drives', None)
        drive_cost = sum(part.cost for part in drives._all_parts()) if drives is not None else 0.0
        power = getattr(ship, 'power', None)
        plant = None if power is None else power.plant
        power_cost = plant.cost if plant is not None else 0.0
        return hull_basis + drive_cost + power_cost

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        return self._basis() * self.cost_percent

    @property
    def power(self) -> float:
        return 0.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        if self.effect_note is not None:
            notes.info(self.effect_note)
        return notes

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        cost = self.cost
        spec.add_row(
            SpecRow(
                section=SpecSection.HULL,
                item=self.build_item() or '',
                tons=None,
                cost=cost if cost != 0.0 else None,
                notes=self.notes,
            )
        )


class CrewIntensiveAutomation(Automation):
    level: Literal['crew_intensive'] = 'crew_intensive'
    label: ClassVar[str] = 'Crew-Intensive'
    cost_percent: ClassVar[float] = -0.40
    crew_factor: ClassVar[float] = 2.0
    effect_note: ClassVar[str | None] = 'DM-4 on all shipboard tasks'


class LowAutomation(Automation):
    level: Literal['low'] = 'low'
    label: ClassVar[str] = 'Low Automation'
    cost_percent: ClassVar[float] = -0.20
    crew_factor: ClassVar[float] = 1.4
    effect_note: ClassVar[str | None] = 'DM-1 on all shipboard tasks after 1 week in space'


class StandardAutomation(Automation):
    level: Literal['standard'] = 'standard'
    label: ClassVar[str] = 'Standard Automation'
    cost_percent: ClassVar[float] = 0.0
    crew_factor: ClassVar[float] = 1.0
    effect_note: ClassVar[str | None] = None

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        pass


class EnhancedAutomation(Automation):
    level: Literal['enhanced'] = 'enhanced'
    label: ClassVar[str] = 'Enhanced Automation'
    cost_percent: ClassVar[float] = 0.25
    crew_factor: ClassVar[float] = 0.9
    effect_note: ClassVar[str | None] = None


class AdvancedAutomation(Automation):
    level: Literal['advanced'] = 'advanced'
    label: ClassVar[str] = 'Advanced Automation'
    cost_percent: ClassVar[float] = 0.50
    crew_factor: ClassVar[float] = 0.75
    effect_note: ClassVar[str | None] = 'DM+1 on all shipboard tasks'


class HighAutomation(Automation):
    level: Literal['high'] = 'high'
    label: ClassVar[str] = 'High Automation'
    cost_percent: ClassVar[float] = 1.00
    crew_factor: ClassVar[float] = 0.6
    effect_note: ClassVar[str | None] = 'DM+2 on all shipboard tasks'


type AnyAutomation = Annotated[
    CrewIntensiveAutomation
    | LowAutomation
    | StandardAutomation
    | EnhancedAutomation
    | AdvancedAutomation
    | HighAutomation,
    'automation',
]
