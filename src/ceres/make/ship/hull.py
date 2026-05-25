from enum import Enum
from typing import Annotated, ClassVar, Literal

from pydantic import Field, model_serializer

from ceres.shared import CeresModel, NoteList, _Note

from .armour import (
    BondedSuperdenseArmour,
    CrystalironArmour,
    MolecularBondedArmour,
    TitaniumSteelArmour,
)
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

    def automation_basis_cost(self, ton: float) -> float:
        """Hull cost contribution for automation — includes config/reinforced/light/military but NOT non-gravity.

        Non-gravity is an economic discount on hull structure, not a technology choice, so it is
        excluded from the automation basis per the Traveller Companion rule.
        """
        modifier = self.hull_cost_modifier
        if self.reinforced:
            modifier *= 1.5
        if self.light:
            modifier *= 0.75
        if self.military:
            modifier *= 1.25
        return 50000 * ton * modifier

    def points(self, ton):
        if ton >= 100_000:
            divisor = 1.5
        elif ton >= 25_000:
            divisor = 2.0
        else:
            divisor = 2.5
        return (ton * self.effective_hull_points_modifier) // divisor


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
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    cost_per_ton: ClassVar[int] = 0
    tonnage: ClassVar[float] = 0
    sensors_dm: ClassVar[int] = 0

    @property
    def cost(self) -> float:
        return self.assembly.displacement * self.cost_per_ton

    @property
    def tons(self) -> float:
        return self.assembly.displacement * self.tonnage

    @property
    def power(self) -> float:
        return 0.0


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
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    protected_tonnage: float
    protected_item: str | None = None
    from_ship_part: bool = False

    def item_description(self) -> str:
        if self.protected_item is not None:
            return f'Armoured Bulkhead for {self.protected_item}'
        return 'Armoured Bulkhead'

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Critical hit severity reduced by 1 if critical hit severity >1')
        if not self.from_ship_part:
            notes.warning('Prefer armoured_bulkhead=True on the protected ShipPart over manual ArmouredBulkhead')
        return notes

    @property
    def tons(self) -> float:
        return self.protected_tonnage * 0.1

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0

    @property
    def power(self) -> float:
        return 0.0


class AdjustableHull(ShipPart):
    description: Literal['Adjustable Hull'] = 'Adjustable Hull'
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    tl: Literal[12, 15] = 12

    @property
    def tons(self) -> float:
        rate = 0.05 if self.tl == 12 else 0.01
        return self.assembly.displacement * rate

    @property
    def cost(self) -> float:
        hull = getattr(self.assembly, 'hull', None)
        if hull is None:
            return 0.0
        multiplier = 0.10 if self.tl == 12 else 1.0
        return hull.configuration.cost(self.assembly.displacement) * multiplier

    @property
    def power(self) -> float:
        return 0.0

    def item_description(self) -> str:
        return f'Adjustable Hull (TL{self.tl})'

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Can mimic ships of the same tonnage, hull configuration, hull options, and external systems')
        notes.info('All weapons have pop-up mountings at no additional cost')
        return notes


class Hull(CeresModel):
    configuration: HullConfiguration
    armour: HullArmour | None = None
    stealth: HullStealth | None = None
    pressure_hull: bool = False
    adjustable_hull: AdjustableHull | None = None
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

    def reflec_cost(self, displacement: float) -> float:
        if not self.reflec:
            return 0.0
        return displacement * 100_000.0

    def pressure_hull_tons(self, displacement: float) -> float:
        if not self.pressure_hull:
            return 0.0
        return displacement * 0.25

    def heat_shielding_cost(self, displacement: float) -> float:
        if not self.heat_shielding:
            return 0.0
        return displacement * 100_000.0

    def breakaway_tons(self, displacement: float) -> float:
        if not self.configuration.breakaway:
            return 0.0
        return displacement * 0.02

    def breakaway_cost(self, displacement: float) -> float:
        return self.breakaway_tons(displacement) * 2_000_000.0

    def total_cost(self, displacement: float) -> float:
        base_cost = self.configuration.cost(displacement)
        if self.pressure_hull:
            return base_cost * 10
        return base_cost

    def item_description(self) -> str:
        item = self.configuration.build_item()
        if item is not None and self.pressure_hull:
            return f'{item}, Pressure Hull'
        return item or ''

    def build_notes(self):
        notes = NoteList()
        if self.reflec and self.stealth is not None:
            notes.error('Reflec cannot be combined with stealth')
        return notes

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        if (a := self.armour) is not None:
            parts.append(a)
        if (s := self.stealth) is not None:
            parts.append(s)
        if (ah := self.adjustable_hull) is not None:
            parts.append(ah)
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
                    tons=self.pressure_hull_tons(ship.displacement),
                )
            )
        if self.stealth is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.HULL, self.stealth))
        if self.adjustable_hull is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.HULL, self.adjustable_hull))
        if self.configuration.breakaway:
            notes = NoteList()
            notes.info('Consumes 2% of combined hull tonnage for extra bulkheads and connections')
            notes.info('Each breakaway section needs an appropriate bridge and power plant')
            notes.info('Section drives, power plants, and weapons can be combined while sections are together')
            spec.add_row(
                SpecRow(
                    section=SpecSection.HULL,
                    item='Breakaway Hull Connections',
                    tons=self.breakaway_tons(ship.displacement) or None,
                    cost=self.breakaway_cost(ship.displacement) or None,
                    notes=notes,
                )
            )
        if self.heat_shielding:
            spec.add_row(
                SpecRow(
                    section=SpecSection.HULL,
                    item='Heat Shielding',
                    tons=None,
                    cost=self.heat_shielding_cost(ship.displacement) or None,
                )
            )
        if self.radiation_shielding:
            spec.add_row(
                SpecRow(
                    section=SpecSection.HULL,
                    item='Radiation Shielding: Reduce Rads by 1,000',
                    tons=0.0,
                    cost=self.radiation_shielding_cost(ship.displacement) or None,
                )
            )
        if self.reflec:
            notes = NoteList()
            notes.info('+3 armour protection against lasers')
            spec.add_row(
                SpecRow(
                    section=SpecSection.HULL,
                    item='Reflec',
                    tons=None,
                    cost=self.reflec_cost(ship.displacement) or None,
                    notes=notes,
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
