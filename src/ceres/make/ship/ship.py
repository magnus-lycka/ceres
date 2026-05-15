from enum import StrEnum
from math import ceil

from pydantic import Field

from ceres.gear.software import SoftwarePackage
from ceres.shared import NoteList

from .automation import AnyAutomation, StandardAutomation
from .base import ShipBase
from .bridge import CommandSection
from .computer import ComputerSection
from .crafts import CraftSection
from .crew import (
    CrewRole,
    ShipCrew,
)
from .drives import (
    DriveSection,
    PowerSection,
)
from .expense import (
    ShipExpenses,
)
from .habitation import HabitationSection
from .hull import ArmouredBulkhead, Hull, Streamlined
from .occupants import ShipOccupant
from .parts import ShipPart
from .sensors import SensorsSection
from .spec import PassengerRow, ShipSpec, SpecRow, SpecSection
from .storage import CargoSection, FuelScoops, FuelSection
from .systems import Airlock, Armoury, SystemsSection
from .text import optional_count
from .weapons import WeaponsSection

__all__ = ['CrewRole', 'Ship', 'ShipDesignType']


class ShipDesignType(StrEnum):
    STANDARD = 'STANDARD'
    CUSTOM = 'CUSTOM'
    NEW = 'NEW'

    @property
    def cost_multiplier(self) -> float:
        return {
            ShipDesignType.STANDARD: 0.9,
            ShipDesignType.CUSTOM: 1.0,
            ShipDesignType.NEW: 1.01,
        }[self]


class Ship(ShipBase):
    ship_class: str | None = None
    ship_type: str | None = None
    military: bool = False
    # Crew is a first-class sub-object so crew-specific notes and explicit input
    # live with the crew model instead of being stored on the ship and filtered
    # back into the crew table later.
    crew: ShipCrew = Field(default_factory=ShipCrew)
    occupants: list[ShipOccupant] | None = None
    design_type: ShipDesignType = ShipDesignType.CUSTOM
    hull: Hull
    drives: DriveSection | None = None
    power: PowerSection | None = None
    fuel: FuelSection | None = None
    command: CommandSection | None = None
    computer: ComputerSection | None = None
    sensors: SensorsSection = Field(default_factory=SensorsSection)
    craft: CraftSection | None = None
    automation: AnyAutomation = Field(default_factory=StandardAutomation)
    cargo: CargoSection | None = None
    habitation: HabitationSection | None = None
    systems: SystemsSection | None = None
    weapons: WeaponsSection | None = None

    def build_notes(self) -> list:
        notes = NoteList()
        residual_tonnage = self.remaining_usable_tonnage()
        if residual_tonnage < -0.005:
            notes.error(f'Hull overloaded by {-residual_tonnage:.2f} tons')

        power_shortfall = self.total_power_load - self.available_power
        if power_shortfall > 0.005 and (self.power is None or self.power.plant is None):
            notes.warning(f'Power: capacity {power_shortfall:.2f} less than max use')

        minimum_airlocks = ceil(self.displacement / 500) if self.displacement >= 100 else 0
        installed_airlocks = len(self.hull.airlocks)
        if minimum_airlocks and installed_airlocks < minimum_airlocks:
            notes.warning(f'Installed airlocks below minimum recommendation: {installed_airlocks} < {minimum_airlocks}')

        if self.command is not None and self.command.bridge is not None and not self.hull.airlocks:
            notes.error('No airlock installed')

        recommended_armouries = _recommended_armouries(self)
        installed_armouries = 0 if self.systems is None else len(self.systems.internal_systems_of_type(Armoury))
        if self.military and installed_armouries < recommended_armouries:
            notes.warning(f'Installed armouries below recommendation: {installed_armouries} < {recommended_armouries}')

        return notes

    @property
    def armour_volume_modifier(self) -> float:
        return self.hull.configuration.armour_volume_modifier

    @property
    def hull_cost(self) -> float:
        return float(self.hull.total_cost(self.displacement))

    @property
    def hull_points(self) -> float:
        return float(self.hull.configuration.points(self.displacement))

    @property
    def available_power(self) -> float:
        if self.power is None or self.power.plant is None:
            return 0.0
        return float(self.power.plant.output)

    @property
    def basic_hull_power_load(self) -> float:
        base = self.displacement * 0.2
        if self.hull.configuration.non_gravity:
            base *= 0.5
        return float(ceil(base))

    @property
    def maneuver_power_load(self) -> float:
        if self.drives is None or self.drives.m_drive is None:
            return 0.0
        return self.drives.m_drive.power

    @property
    def sensor_power_load(self) -> float:
        return sum(p.power for p in self.sensors._all_parts())

    @property
    def jump_power_load(self) -> float:
        if self.drives is None or self.drives.j_drive is None:
            return 0.0
        return self.drives.j_drive.power

    @property
    def fuel_power_load(self) -> float:
        if self.fuel is None or self.fuel.fuel_processor is None:
            return 0.0
        return self.fuel.fuel_processor.power

    @property
    def weapon_power_load(self) -> float:
        if self.weapons is None:
            return 0.0
        return sum(part.power for part in self.weapons._all_parts())

    @property
    def total_power_load(self) -> float:
        m_drive = None if self.drives is None else self.drives.m_drive
        jump_drive = None if self.drives is None else self.drives.j_drive
        non_drive_power_load = sum(
            part.power for part in self._all_parts() if part is not m_drive and part is not jump_drive
        )
        return self.basic_hull_power_load + max(self.maneuver_power_load, self.jump_power_load) + non_drive_power_load

    @property
    def production_cost(self) -> float:
        return self.expenses.production_cost

    @property
    def sales_price_new(self) -> float:
        return self.expenses.sales_price_new

    @property
    def expenses(self) -> ShipExpenses:
        return ShipExpenses(self)

    def _crew_salary_cost(self) -> float:
        return self.crew.total_salary

    def _base_parts(self) -> list[ShipPart]:
        parts = list(self.hull._all_parts())
        if self.drives is not None:
            parts.extend(self.drives._all_parts())
        if self.power is not None:
            parts.extend(self.power._all_parts())
        if self.fuel is not None:
            parts.extend(self.fuel._all_parts())
        parts.append(self.automation)
        if self.command is not None:
            parts.extend(self.command._all_parts())
        if self.computer is not None:
            parts.extend(self.computer._all_parts())
        parts.extend(self.sensors._all_parts())
        if self.habitation is not None:
            parts.extend(self.habitation._all_parts())
        if self.craft is not None:
            parts.extend(self.craft._all_parts())
        if self.systems is not None:
            parts.extend(self.systems._all_parts())
        if self.cargo is not None:
            parts.extend(self.cargo._all_parts())
        if self.weapons is not None:
            parts.extend(self.weapons._all_parts())
        return parts

    def armoured_bulkhead_parts(self) -> list[ArmouredBulkhead]:
        auto_bulkheads: list[ArmouredBulkhead] = []
        manual_bulkheads: list[ArmouredBulkhead] = []
        for part in self._base_parts():
            if isinstance(part, ArmouredBulkhead):
                manual_bulkheads.append(part)
                continue
            auto_bulkhead = part.armoured_bulkhead_part
            if isinstance(auto_bulkhead, ArmouredBulkhead):
                auto_bulkheads.append(auto_bulkhead)
        return [*auto_bulkheads, *manual_bulkheads]

    def _all_parts(self) -> list[ShipPart]:
        parts = self._base_parts()
        parts.extend(self.armoured_bulkhead_parts())
        return parts

    @property
    def performance_displacement(self) -> float:
        base = float(self.displacement)
        if self.craft is not None:
            base += sum(c.performance_displacement_contribution for c in self.craft.docking_clamps)
        return base

    def remaining_usable_tonnage(self) -> float:
        remaining = self.displacement * self.hull.configuration.usage_factor
        remaining -= self.hull.pressure_hull_tons(self.displacement)
        for part in self._all_parts():
            remaining -= part.tons
        cargo_holds = [] if self.cargo is None else self.cargo.cargo_holds
        for cargo_hold in cargo_holds:
            if cargo_hold.tons is not None:
                remaining -= cargo_hold.tons
        return remaining

    def parts_of_type(self, part_cls: type) -> list[ShipPart]:
        return [part for part in self._all_parts() if isinstance(part, part_cls)]

    def _item_text(self, obj, fallback: str) -> str:
        return obj.notes.item_message or fallback

    def _display_notes(self, obj) -> NoteList:
        return obj.notes.details

    def _spec_row_for_part(
        self,
        section: SpecSection,
        part: ShipPart,
        *,
        item: str | None = None,
        power: float | None = None,
        emphasize_power: bool = False,
    ) -> SpecRow:
        resolved_item = item or self._item_text(part, getattr(part, 'description', part.__class__.__name__))
        resolved_power = power
        if resolved_power is None and part.power:
            resolved_power = -part.power
        return SpecRow(
            section=section,
            item=resolved_item,
            tons=part.tons or None,
            power=resolved_power,
            cost=part.cost or None,
            emphasize_power=emphasize_power,
            notes=self._display_notes(part),
        )

    def _grouped_spec_rows(self, section: SpecSection, parts: list[ShipPart]) -> list[SpecRow]:
        groups: list[tuple[str, str, list[ShipPart]]] = []  # (group_key, display_item, parts)
        for part in parts:
            display_item = self._item_text(part, getattr(part, 'description', part.__class__.__name__))
            key = part.group_key if hasattr(part, 'group_key') else display_item
            if groups and groups[-1][0] == key:
                groups[-1][2].append(part)
            else:
                groups.append((key, display_item, [part]))

        rows: list[SpecRow] = []
        for _key, display_item, group in groups:
            total_tons = sum(part.tons for part in group) or None
            total_cost = sum(part.cost for part in group) or None
            total_power = sum(part.power for part in group)
            seen: set[tuple] = set()
            notes = NoteList()
            for part in group:
                for note in self._display_notes(part):
                    k = (note.category, note.message)
                    if k not in seen:
                        seen.add(k)
                        notes.append(note)
            rows.append(
                SpecRow(
                    section=section,
                    item=display_item,
                    quantity=optional_count(len(group)),
                    tons=total_tons,
                    power=(-total_power) if total_power else None,
                    cost=total_cost,
                    notes=notes,
                )
            )
        return rows

    def build_spec(self) -> ShipSpec:
        spec = ShipSpec(
            ship_class=self.ship_class,
            ship_type=self.ship_type,
            tl=self.tl,
            hull_points=self.hull_points,
        )
        self.hull.add_spec_rows(self, spec)

        if self.drives is not None:
            self.drives.add_spec_rows(self, spec)
        if self.power is not None:
            self.power.add_spec_rows(self, spec)
        if self.fuel is not None:
            self.fuel.add_spec_rows(self, spec)
        self.automation.add_spec_rows(self, spec)
        if self.command is not None:
            self.command.add_spec_rows(self, spec)
        if self.computer is not None:
            self.computer.add_spec_rows(self, spec)
        self.sensors.add_spec_rows(self, spec)

        if self.weapons is not None:
            self.weapons.add_spec_rows(self, spec)

        if self.craft is not None:
            self.craft.add_spec_rows(self, spec)

        if self.habitation is not None:
            self.habitation.add_spec_rows(self, spec)
        if self.systems is not None:
            self.systems.add_spec_rows(self, spec)
        CargoSection.add_spec_rows_for_ship(self, spec)

        spec.crew_notes = self.crew.notes.advisories
        spec.ship_notes = self._display_notes(self)

        spec.expenses = self.expenses.rows
        spec.crew = self.crew.spec_rows()
        if self.habitation is not None:
            passenger_counts = self.habitation.passenger_counts(self)
            spec.passengers = [
                PassengerRow(kind=kind.upper(), quantity=count) for kind, count in passenger_counts.items() if count > 0
            ]
        return spec

    def model_post_init(self, __context: object) -> None:
        super().model_post_init(__context)
        if self.tl > 16:
            raise ValueError(f'Ceres currently supports TL16 and lower, got TL{self.tl}')
        if not self.hull.airlocks and self.displacement >= 100:
            minimum_airlocks = ceil(self.displacement / 500)
            self.hull = self.hull.model_copy(update={'airlocks': [Airlock() for _ in range(minimum_airlocks)]})
        if self.hull.configuration.streamlined == Streamlined.YES:
            if self.fuel is None:
                self.fuel = FuelSection(fuel_scoops=FuelScoops(free=True))
            elif self.fuel.fuel_scoops is None or not self.fuel.fuel_scoops.free:
                self.fuel = self.fuel.model_copy(update={'fuel_scoops': FuelScoops(free=True)})
        self.crew.bind(self)
        for part in self._base_parts():
            part.bind(self)
        if self.habitation is not None:
            self.habitation.validate_common_area()
            self.habitation.validate_passenger_capacity(self)
        if self.computer is not None:
            self.computer.validate_software()
            self.computer.validate_jump_drive(self.drives)
        if self.drives is not None:
            software_packages: list[SoftwarePackage]
            if self.computer is None:
                software_packages = []
            else:
                software_packages = self.computer.software_packages
            self.drives.validate_jump_control(software_packages)
        if self.power is not None:
            self.power.validate_emergency_power_system()
        if self.weapons is not None:
            self.weapons.validate_mounting(self)
        power_shortfall = self.total_power_load - self.available_power
        if power_shortfall > 0.005 and self.power is not None and self.power.plant is not None:
            message = f'Capacity {power_shortfall:.2f} less than max use'
            self.power.plant.warning(message)


def _recommended_armouries(ship: Ship) -> int:
    if not ship.military:
        return 0
    marine_count = sum(1 for role in ship.crew.effective_roles if role.role == 'MARINE')
    non_marine_count = ship.crew.count - marine_count
    required = (non_marine_count / 25) + (marine_count / 5)
    return int(required + 0.5)
