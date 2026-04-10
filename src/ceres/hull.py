from enum import Enum
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from .armour import (
    BondedSuperdenseArmour,
    CrystalironArmour,
    MolecularBondedArmour,
    TitaniumSteelArmour,
)
from .base import CeresModel, Note, NoteCategory
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
    minimum_tl: ClassVar[int] = 0
    description: str
    cost_per_ton: ClassVar[int] = 0
    tonnage: ClassVar[float] = 0
    sensors_dm: ClassVar[int] = 0

    def compute_cost(self):
        return self.owner.displacement * self.cost_per_ton

    def compute_tons(self):
        return self.owner.displacement * self.tonnage


class BasicStealth(Stealth):
    description: Literal['Basic Stealth'] = 'Basic Stealth'
    minimum_tl = 7
    cost_per_ton = 40_000
    sensors_dm = -2
    tonnage = 0.02


class ImprovedStealth(Stealth):
    description: Literal['Improved Stealth'] = 'Improved Stealth'
    minimum_tl = 10
    cost_per_ton = 100_000
    sensors_dm = -2


class EnhancedStealth(Stealth):
    description: Literal['Enhanced Stealth'] = 'Enhanced Stealth'
    minimum_tl = 12
    cost_per_ton = 500_000
    sensors_dm = -4


class AdvancedStealth(Stealth):
    description: Literal['Advanced Stealth'] = 'Advanced Stealth'
    minimum_tl = 14
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

    def build_item(self) -> str | None:
        return 'Armoured Bulkhead'

    def build_notes(self) -> list[Note]:
        if self.protected_item is None:
            return []
        return [Note(category=NoteCategory.INFO, message=f'Protects {self.protected_item}')]

    def compute_tons(self) -> float:
        return self.protected_tonnage * 0.1

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0


class Hull(CeresModel):
    configuration: HullConfiguration
    armour: HullArmour | None = None
    stealth: HullStealth | None = None
    armoured_bulkheads: list[ArmouredBulkhead] = Field(default_factory=list)
    airlocks: list[Airlock] = Field(default_factory=list)
    aerofins: Aerofins | None = None
    heat_shielding: bool = False
    radiation_shielding: bool = False
    reflec: bool = False

    def build_item(self) -> str | None:
        return self.configuration.build_item()

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
        if self.stealth is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.HULL, self.stealth))
        for bulkhead in self.armoured_bulkheads:
            spec.add_row(ship._spec_row_for_part(SpecSection.HULL, bulkhead))
        for row in ship._grouped_spec_rows(
            SpecSection.HULL,
            [*self.airlocks, *([self.aerofins] if self.aerofins is not None else [])],
        ):
            spec.add_row(row)
