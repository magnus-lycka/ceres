from enum import Enum
from typing import Annotated, ClassVar, Literal

from pydantic import Field, model_serializer

from .armour import (
    BondedSuperdenseArmour,
    CrystalironArmour,
    MolecularBondedArmour,
    TitaniumSteelArmour,
)
from .base import CeresModel, NoteList, _Note
from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection
from .systems import Aerofins, Airlock


class Streamlined(Enum):
    YES = 1
    PARTIAL = 2
    NO = 3


class HullConfiguration(CeresModel):
    description: str = 'Standard Hull'
    streamlined: Streamlined
    armour_volume_modifier: float = 1
    hull_points_modifier: float = 1
    hull_cost_modifier: float = 1
    reinforced: bool = False
    light: bool = False
    military: bool = False
    non_gravity: bool = False
    double: bool = False
    hamster_cage: bool = False
    breakaway: bool = False
    protection: int = 0
    usage_factor: float = 1

    @property
    def effective_hull_cost_modifier(self) -> float:
        modifier = self.hull_cost_modifier
        if self.reinforced:
            modifier *= 1.5
        if self.light:
            modifier *= 0.75
        if self.military:
            modifier *= 1.25
        if self.non_gravity:
            modifier *= 0.5
        return modifier

    @property
    def effective_hull_points_modifier(self) -> float:
        modifier = self.hull_points_modifier
        if self.reinforced:
            modifier *= 1.1
        if self.light:
            modifier *= 0.9
        return modifier

    def cost(self, ton):
        return 50000 * ton * self.effective_hull_cost_modifier

    def points(self, ton):
        return (ton * self.effective_hull_points_modifier) // 2.5

    def build_item(self) -> str | None:
        return self.description


standard_hull = HullConfiguration(description='Standard Hull', streamlined=Streamlined.PARTIAL)

streamlined_hull = HullConfiguration(
    description='Streamlined Hull',
    streamlined=Streamlined.YES,
    armour_volume_modifier=1.2,
    hull_cost_modifier=1.2,
)

sphere = HullConfiguration(
    description='Sphere Hull',
    streamlined=Streamlined.PARTIAL,
    armour_volume_modifier=0.9,
    hull_cost_modifier=1.1,
)

close_structure = HullConfiguration(
    description='Close Structure Hull',
    streamlined=Streamlined.PARTIAL,
    armour_volume_modifier=1.5,
    hull_cost_modifier=0.8,
)

dispersed_structure = HullConfiguration(
    description='Dispersed Structure Hull',
    streamlined=Streamlined.NO,
    armour_volume_modifier=2,
    hull_points_modifier=0.9,
    hull_cost_modifier=0.5,
)

planetoid = HullConfiguration(
    description='Planetoid Hull',
    streamlined=Streamlined.NO,
    hull_points_modifier=1.25,
    hull_cost_modifier=0.08,
    usage_factor=0.8,
    protection=2,
)

buffered_planetoid = HullConfiguration(
    description='Buffered Planetoid Hull',
    streamlined=Streamlined.NO,
    hull_points_modifier=1.5,
    hull_cost_modifier=0.08,
    usage_factor=0.65,
    protection=4,
)


class Stealth(ShipPart):
    description: str
    cost_per_ton: ClassVar[int] = 0
    tonnage: ClassVar[float] = 0
    sensors_dm: ClassVar[int] = 0

    def compute_cost(self):
        return self.assembly.displacement * self.cost_per_ton

    def compute_tons(self):
        return self.assembly.displacement * self.tonnage


class BasicStealth(Stealth):
    description: Literal['Basic Stealth'] = 'Basic Stealth'
    tl: int = 7
    cost_per_ton = 40_000
    sensors_dm = -2
    tonnage = 0.02


class ImprovedStealth(Stealth):
    description: Literal['Improved Stealth'] = 'Improved Stealth'
    tl: int = 10
    cost_per_ton = 100_000
    sensors_dm = -2


class EnhancedStealth(Stealth):
    description: Literal['Enhanced Stealth'] = 'Enhanced Stealth'
    tl: int = 12
    cost_per_ton = 500_000
    sensors_dm = -4


class AdvancedStealth(Stealth):
    description: Literal['Advanced Stealth'] = 'Advanced Stealth'
    tl: int = 14
    cost_per_ton = 1_000_000
    sensors_dm = -6


HullArmour = Annotated[
    TitaniumSteelArmour | CrystalironArmour | BondedSuperdenseArmour | MolecularBondedArmour,
    Field(discriminator='description'),
]

HullStealth = Annotated[
    BasicStealth | ImprovedStealth | EnhancedStealth | AdvancedStealth,
    Field(discriminator='description'),
]


class ArmouredBulkhead(ShipPart):
    protected_tonnage: float
    protected_item: str | None = None
    from_ship_part: bool = False

    def build_item(self) -> str | None:
        if self.protected_item is not None:
            return f'Armoured Bulkhead for {self.protected_item}'
        return 'Armoured Bulkhead'

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Critical hit severity reduced by 1 if critical hit severity >1')
        if not self.from_ship_part:
            notes.warning('Prefer armoured_bulkhead=True on the protected ShipPart over manual ArmouredBulkhead')
        return notes

    def compute_tons(self) -> float:
        return self.protected_tonnage * 0.1

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0


class Hull(CeresModel):
    configuration: HullConfiguration
    armour: HullArmour | None = None
    stealth: HullStealth | None = None
    pressure_hull: bool = False
    armoured_bulkheads: list[ArmouredBulkhead] = Field(default_factory=list)
    airlocks: list[Airlock] = Field(default_factory=list)
    aerofins: Aerofins | None = None
    heat_shielding: bool = False
    radiation_shielding: bool = False
    reflec: bool = False

    def radiation_shielding_cost(self, displacement: float) -> float:
        if not self.radiation_shielding:
            return 0.0
        return displacement * 25_000.0

    def pressure_hull_tons(self, displacement: float) -> float:
        if not self.pressure_hull:
            return 0.0
        return displacement * 0.25

    def total_cost(self, displacement: float) -> float:
        base_cost = self.configuration.cost(displacement)
        if self.pressure_hull:
            return base_cost * 10
        return base_cost

    def build_item(self) -> str | None:
        item = self.configuration.build_item()
        if item is not None and self.pressure_hull:
            return f'{item}, Pressure Hull'
        return item

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        if (a := self.armour) is not None:
            parts.append(a)
        if (s := self.stealth) is not None:
            parts.append(s)
        parts.extend(self.armoured_bulkheads)
        parts.extend(self.airlocks)
        if (af := self.aerofins) is not None:
            parts.append(af)
        return parts

    @model_serializer(mode='wrap')
    def _serialize_without_empty_armoured_bulkheads(self, handler):
        data = handler(self)
        if data.get('armoured_bulkheads') == []:
            data.pop('armoured_bulkheads', None)
        return data

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        spec.add_row(
            SpecRow(
                section=SpecSection.HULL,
                item=ship._item_text(self, 'Hull'),
                tons=float(ship.displacement),
                cost=ship.hull_cost,
                emphasize_tons=True,
                notes=ship._display_notes(self),
            )
        )
        spec.add_row(
            SpecRow(
                section=SpecSection.HULL,
                item='Basic Ship Systems',
                power=ship.basic_hull_power_load,
            )
        )
        if self.armour is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.HULL, self.armour))
        elif self.pressure_hull:
            spec.add_row(
                SpecRow(
                    section=SpecSection.HULL,
                    item='Armour: 4',
                )
            )
        if self.stealth is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.HULL, self.stealth))
        if self.radiation_shielding:
            spec.add_row(
                SpecRow(
                    section=SpecSection.HULL,
                    item='Radiation Shielding: Reduce Rads by 1,000',
                    tons=0.0,
                    cost=self.radiation_shielding_cost(ship.displacement) or None,
                )
            )
        bulkheads = ship.armoured_bulkhead_parts()
        if bulkheads:
            notes = NoteList()
            notes.info('Critical hit severity reduced by 1 if critical hit severity >1')
            spec.add_row(
                SpecRow(
                    section=SpecSection.HULL,
                    item='Armoured Bulkheads',
                    tons=sum(bulkhead.tons for bulkhead in bulkheads) or None,
                    cost=sum(bulkhead.cost for bulkhead in bulkheads) or None,
                    notes=notes,
                )
            )
        for row in ship._grouped_spec_rows(
            SpecSection.HULL,
            [*self.airlocks, *([self.aerofins] if self.aerofins is not None else [])],
        ):
            spec.add_row(row)
