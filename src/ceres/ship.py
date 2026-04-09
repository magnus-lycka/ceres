from enum import StrEnum
from typing import Any

from pydantic import Field

from . import hull as hull_model
from .base import CeresModel, NoteCategory, ShipBase
from .bridge import CommandSection
from .computer import ComputerSection, SoftwarePackage
from .crafts import InternalDockingSpace
from .drives import (
    DriveSection,
    PowerSection,
)
from .habitation import HabitationSection
from .parts import ShipPart
from .sensors import SensorsSection
from .spec import CrewRow as SpecCrewRow, ExpenseRow, ShipSpec, SpecRow, SpecSection
from .storage import CargoSection, FuelScoops, FuelSection
from .systems import SystemsSection
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


class CrewRole(CeresModel):
    role: str
    count: int
    monthly_salary: int

    @property
    def total_salary(self) -> int:
        return self.count * self.monthly_salary


class Ship(ShipBase):
    ship_class: str | None = None
    ship_type: str | None = None
    design_type: ShipDesignType = ShipDesignType.CUSTOM
    hull: hull_model.Hull
    drives: DriveSection | None = None
    power: PowerSection | None = None
    fuel: FuelSection | None = None
    command: CommandSection | None = None
    computer: ComputerSection | None = None
    sensors: SensorsSection = Field(default_factory=SensorsSection)
    docking_space: InternalDockingSpace | None = None
    cargo: CargoSection | None = None
    habitation: HabitationSection | None = None
    systems: SystemsSection | None = None
    weapons: WeaponsSection | None = None

    @property
    def armour_volume_modifier(self) -> float:
        return self.hull.configuration.armour_volume_modifier

    @property
    def hull_cost(self) -> float:
        return float(self.hull.configuration.cost(self.displacement))

    @property
    def hull_points(self) -> float:
        return float(self.hull.configuration.points(self.displacement))

    @property
    def available_power(self) -> float:
        if self.power is None or self.power.fusion_plant is None:
            return 0.0
        return float(self.power.fusion_plant.output)

    @property
    def basic_hull_power_load(self) -> float:
        if self.command is not None and self.command.bridge is not None:
            return self.displacement * 0.2
        if self.hull.configuration.non_gravity:
            return 0.5
        return 1.0

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
        if self.drives is None or self.drives.jump_drive is None:
            return 0.0
        return self.drives.jump_drive.power

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
        jump_drive = None if self.drives is None else self.drives.jump_drive
        non_drive_power_load = sum(
            part.power for part in self._all_parts() if part is not m_drive and part is not jump_drive
        )
        return self.basic_hull_power_load + max(self.maneuver_power_load, self.jump_power_load) + non_drive_power_load

    @property
    def production_cost(self) -> float:
        craft_cost = 0.0
        if self.docking_space is not None:
            craft_cost += self.docking_space.craft.cost
        cargo_holds = [] if self.cargo is None else self.cargo.cargo_holds
        cargo_hold_cost = sum(cargo_hold.crane_cost(self) for cargo_hold in cargo_holds)
        software_cost = 0.0
        if self.computer is not None:
            software_cost = sum(package.cost for package in self.computer.software_packages.values())
        return (
            self.hull_cost + sum(part.cost for part in self._all_parts()) + software_cost + craft_cost + cargo_hold_cost
        )

    @property
    def sales_price_new(self) -> float:
        return self.production_cost * self.design_type.cost_multiplier

    def _crew_salary_cost(self) -> float:
        return float(sum(role.total_salary for role in self.crew_roles))

    def _mortgage_cost(self) -> float:
        return round(self.sales_price_new / 240, 2)

    def _maintenance_cost(self) -> float:
        return float(round(self.sales_price_new / 12_000))

    def _life_support_cost(self) -> float:
        if self.command is not None and self.command.cockpit is not None:
            return 0.0
        if self.habitation is not None and self.habitation.staterooms is not None:
            return self.habitation.staterooms.life_support_cost
        return 0.0

    def _fuel_cost(self) -> float:
        if self.fuel is None or self.fuel.jump_fuel is None:
            return 0.0
        fuel_cost_per_ton = 100 if self.fuel.fuel_processor is not None else 500
        return float(self.fuel.jump_fuel.tons * 2 * fuel_cost_per_ton)

    def _total_expenses(self) -> float:
        return (
            self._mortgage_cost()
            + self._maintenance_cost()
            + self._life_support_cost()
            + self._crew_salary_cost()
            + self._fuel_cost()
        )

    @property
    def crew_roles(self) -> list[CrewRole]:
        if self.displacement <= 100 and self.drives is not None and self.drives.jump_drive is not None:
            return [
                CrewRole(role='PILOT', count=1, monthly_salary=6_000),
                CrewRole(role='ASTROGATOR', count=1, monthly_salary=5_000),
                CrewRole(role='ENGINEER', count=1, monthly_salary=4_000),
            ]
        # Small craft without jump drives typically operate with a single pilot.
        if self.displacement <= 100:
            return [CrewRole(role='PILOT', count=1, monthly_salary=6_000)]
        return []

    def _all_parts(self) -> list[ShipPart]:
        parts = list(self.hull._all_parts())
        if self.drives is not None:
            parts.extend(self.drives._all_parts())
        if self.power is not None:
            parts.extend(self.power._all_parts())
        if self.fuel is not None:
            parts.extend(self.fuel._all_parts())
        if self.command is not None:
            parts.extend(self.command._all_parts())
        if self.computer is not None:
            parts.extend(self.computer._all_parts())
        parts.extend(self.sensors._all_parts())
        if self.habitation is not None:
            parts.extend(self.habitation._all_parts())
        for part in (self.docking_space,):
            if part is not None:
                parts.append(part)
        if self.systems is not None:
            parts.extend(self.systems._all_parts())
        if self.weapons is not None:
            parts.extend(self.weapons._all_parts())
        return parts

    def _remaining_cargo_space_without_default_holds(self) -> float:
        cargo = self.displacement * self.hull.configuration.usage_factor
        for part in self._all_parts():
            cargo -= part.tons
        cargo_holds = [] if self.cargo is None else self.cargo.cargo_holds
        for cargo_hold in cargo_holds:
            if cargo_hold.tons is not None:
                cargo -= cargo_hold.tons
        return cargo

    def parts_of_type(self, part_cls: type) -> list[ShipPart]:
        return [part for part in self._all_parts() if isinstance(part, part_cls)]

    def cargo_space_for(self, hold) -> float:
        return self._remaining_cargo_space_without_default_holds()

    def _item_text(self, obj, fallback: str) -> str:
        for note in obj.notes:
            if note.category is NoteCategory.ITEM:
                return note.message
        return fallback

    def _display_notes(self, obj) -> list:
        return [note for note in obj.notes if note.category is not NoteCategory.ITEM]

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
        groups: list[tuple[str, list[ShipPart]]] = []
        for part in parts:
            item = self._item_text(part, getattr(part, 'description', part.__class__.__name__))
            if groups and groups[-1][0] == item:
                groups[-1][1].append(part)
            else:
                groups.append((item, [part]))

        rows: list[SpecRow] = []
        for item, group in groups:
            label = f'{len(group)}x {item}' if len(group) > 1 else item
            total_tons = sum(part.tons for part in group) or None
            total_cost = sum(part.cost for part in group) or None
            total_power = sum(part.power for part in group)
            rows.append(
                SpecRow(
                    section=section,
                    item=label,
                    tons=total_tons,
                    power=(-total_power) if total_power else None,
                    cost=total_cost,
                    notes=[note for part in group for note in self._display_notes(part)],
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

        spec.add_row(
            SpecRow(
                section=SpecSection.HULL,
                item=self._item_text(self.hull, 'Hull'),
                tons=float(self.displacement),
                cost=self.hull_cost,
                emphasize_tons=True,
                notes=self._display_notes(self.hull),
            ),
        )
        spec.add_row(
            SpecRow(
                section=SpecSection.HULL,
                item='Basic Ship Systems',
                power=self.basic_hull_power_load,
            ),
        )
        if self.hull.armour is not None:
            spec.add_row(self._spec_row_for_part(SpecSection.HULL, self.hull.armour))
        if self.hull.stealth is not None:
            spec.add_row(self._spec_row_for_part(SpecSection.HULL, self.hull.stealth))
        for row in self._grouped_spec_rows(
            SpecSection.HULL, [*self.hull.airlocks, *([self.hull.aerofins] if self.hull.aerofins is not None else [])]
        ):
            spec.add_row(row)

        if self.drives is not None:
            self.drives.add_spec_rows(self, spec)
        if self.power is not None:
            self.power.add_spec_rows(self, spec)
        if self.fuel is not None:
            self.fuel.add_spec_rows(self, spec)
        if self.command is not None:
            self.command.add_spec_rows(self, spec)
        if self.computer is not None:
            self.computer.add_spec_rows(self, spec)
        self.sensors.add_spec_rows(self, spec)

        if self.weapons is not None:
            for row in self._grouped_spec_rows(
                SpecSection.WEAPONS, [*self.weapons.turrets, *self.weapons.fixed_firmpoints]
            ):
                spec.add_row(row)
            if self.weapons.missile_storage is not None:
                spec.add_row(self._spec_row_for_part(SpecSection.WEAPONS, self.weapons.missile_storage))

        if self.docking_space is not None:
            spec.add_row(self._spec_row_for_part(SpecSection.CRAFT, self.docking_space))
            craft = self.docking_space.craft
            spec.add_row(
                SpecRow(
                    section=SpecSection.CRAFT,
                    item=craft.build_item() or craft.__class__.__name__,
                    cost=craft.cost,
                ),
            )

        if self.habitation is not None:
            self.habitation.add_spec_rows(self, spec)
        if self.systems is not None:
            self.systems.add_spec_rows(self, spec)
        if self.cargo is not None:
            self.cargo.add_spec_rows(self, spec)
        else:
            spec.add_row(
                SpecRow(
                    section=SpecSection.CARGO,
                    item='Cargo Hold',
                    tons=self.cargo_tons or None,
                ),
            )

        # Ship-level notes (e.g. hull overloaded) appended to the last row
        for note in self.notes:
            spec.rows_for_section(SpecSection.CARGO)[-1].notes.append(note)

        expenses = [
            ExpenseRow('Production Cost', self.production_cost),
            ExpenseRow('Sales Price New', self.sales_price_new),
            ExpenseRow('Mortgage', self._mortgage_cost()),
            ExpenseRow('Maintenance', self._maintenance_cost()),
            ExpenseRow('Life Support', self._life_support_cost()),
            ExpenseRow('Fuel', self._fuel_cost()),
            ExpenseRow('Crew Salaries', self._crew_salary_cost()),
            ExpenseRow('Total Expenses', self._total_expenses()),
        ]

        crew = [SpecCrewRow(role=r.role, salary=r.total_salary) for r in self.crew_roles]

        spec.expenses = expenses
        spec.crew = crew
        return spec

    def markdown_table(self) -> str:
        spec = self.build_spec()
        last_section: str | None = None

        heading_bits: list[str] = []
        if spec.ship_class is not None and spec.ship_type is not None:
            heading_bits.append(f'*{spec.ship_class}* {spec.ship_type}')
        elif spec.ship_class is not None:
            heading_bits.append(f'*{spec.ship_class}*')
        elif spec.ship_type is not None:
            heading_bits.append(spec.ship_type)
        if spec.tl is not None:
            heading_bits.append(f'TL{spec.tl}')
        if spec.hull_points is not None:
            heading_bits.append(f'Hull {spec.hull_points:.0f}')
        heading = f'## {" | ".join(heading_bits)}'

        def fmt_row(row: SpecRow) -> list[str]:
            nonlocal last_section
            tons_text = '' if row.tons is None or row.tons == 0 else f'{row.tons:.2f}'
            if row.emphasize_tons and tons_text:
                tons_text = f'**{tons_text}**'
            if row.power is None or row.power == 0:
                power_text = ''
            else:
                power_text = f'{abs(row.power):.2f}'
            if row.emphasize_power and power_text:
                power_text = f'**{power_text}**'
            cost_text = '' if row.cost is None or row.cost == 0 else f'{row.cost / 1000:.2f}'
            section_text = '' if row.section == last_section else row.section.value
            last_section = row.section
            lines = [f'| {section_text} | {row.item} | {tons_text} | {power_text} | {cost_text} |']
            for note in row.notes:
                if note.category is NoteCategory.INFO:
                    msg = f'• {note.message}'
                elif note.category is NoteCategory.ERROR:
                    msg = f'**ERROR:** {note.message}'
                elif note.category is NoteCategory.WARNING:
                    msg = f'*WARNING:* {note.message}'
                else:
                    msg = note.message
                lines.append(f'|  | {msg} |  |  |  |')
            return lines

        lines = [
            heading,
            '',
            '| Section | Item | Tons | Power | Cost (kCr) |',
            '| ------- | --------------- | ---: | ---: | ---: |',
        ]
        for row in spec.rows:
            lines.extend(fmt_row(row))

        lines.extend(
            [
                '',
                '| Cost | Amount |',
                '| ------------ | ---: |',
            ]
        )
        for exp in spec.expenses:
            lines.append(f'| {exp.label} | {round(exp.amount):,} |')

        if spec.crew:
            lines.extend(['', '| Crew | Salary |', '| ------------ | ---: |'])
            for c in spec.crew:
                lines.append(f'| {c.role} | {round(c.salary):,} |')

        return '\n'.join(lines)

    @property
    def cargo_tons(self):
        if self.cargo is not None and self.cargo.cargo_holds:
            return sum(cargo_hold.usable_tons(self) for cargo_hold in self.cargo.cargo_holds)
        return self._remaining_cargo_space_without_default_holds()

    def model_post_init(self, __context: Any) -> None:
        if self.hull.configuration.streamlined == hull_model.Streamlined.YES:
            if self.fuel is None:
                object.__setattr__(self, 'fuel', FuelSection(fuel_scoops=FuelScoops(free=True)))
            elif self.fuel.fuel_scoops is None or not self.fuel.fuel_scoops.free:
                object.__setattr__(self, 'fuel', self.fuel.model_copy(update={'fuel_scoops': FuelScoops(free=True)}))
        for part in self._all_parts():
            part.bind(self)
        if self.habitation is not None:
            self.habitation.validate_common_area()
        if self.computer is not None:
            self.computer.refresh_software_packages()
            self.computer.validate_software(self.tl)
            self.computer.validate_jump_drive(self.drives)
        if self.drives is not None:
            software_packages: dict[type[SoftwarePackage], SoftwarePackage]
            if self.computer is None:
                software_packages = {}
            else:
                software_packages = self.computer.software_packages
            self.drives.validate_jump_control(software_packages)
        if self.cargo_tons < 0:
            self.error(f'Hull overloaded by {-self.cargo_tons:.2f} tons')
        if self.command is not None and self.command.bridge is not None and not self.hull.airlocks:
            self.error('No airlock installed')
