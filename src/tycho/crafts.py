import math
from typing import Annotated, Literal

from pydantic import Field

from .base import CeresModel
from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection

type VehicleSpec = dict[str, int | float | str]
type SpaceCraftSpec = dict[str, int | float | str]

_VEHICLE_SPECS: dict[str, VehicleSpec] = {
    'Air/Raft': {'tl': 8, 'shipping_size': 4, 'cost': 250_000.0},
    'ATV': {'tl': 12, 'shipping_size': 10, 'cost': 155_000.0},
    'G/Carrier': {'tl': 15, 'shipping_size': 15, 'cost': 11_580_000.0},
    'Prospector Buggy': {'tl': 12, 'shipping_size': 4, 'cost': 270_000.0},
}

_SPACECRAFT_SPECS: dict[str, SpaceCraftSpec] = {
    'Gig': {'tl': 12, 'shipping_size': 20, 'cost': 6_480_000.0, 'engineering_tonnage': 3.2, 'crew': 1},
    'Heavy Fighter': {'tl': 15, 'shipping_size': 50, 'cost': 76_570_000.0, 'engineering_tonnage': 8.0, 'crew': 2},
    'Launch': {'tl': 12, 'shipping_size': 20, 'cost': 2_630_000.0, 'engineering_tonnage': 1.2, 'crew': 1},
    'Light Fighter': {'tl': 12, 'shipping_size': 10, 'cost': 10_480_000.0, 'engineering_tonnage': 1.6, 'crew': 1},
    'Military Gig': {'tl': 14, 'shipping_size': 20, 'cost': 15_187_000.0, 'engineering_tonnage': 3.6, 'crew': 1},
    'Modular Cutter': {'tl': 12, 'shipping_size': 50, 'cost': 11_930_000.0, 'engineering_tonnage': 4.0, 'crew': 1},
    'Passenger Shuttle': {
        'tl': 9,
        'shipping_size': 95,
        'cost': 14_305_000.0,
        'engineering_tonnage': 3.95,
        'crew': 1,
    },
    'Pinnace': {'tl': 12, 'shipping_size': 40, 'cost': 9_680_000.0, 'engineering_tonnage': 4.0, 'crew': 1},
    "Ship's Boat": {'tl': 12, 'shipping_size': 30, 'cost': 7_580_000.0, 'engineering_tonnage': 3.0, 'crew': 1},
    'Shuttle': {'tl': 10, 'shipping_size': 95, 'cost': 16_305_000.0, 'engineering_tonnage': 5.85, 'crew': 1},
    'Slow Boat': {'tl': 12, 'shipping_size': 30, 'cost': 5_580_000.0, 'engineering_tonnage': 1.9, 'crew': 1},
    'Slow Pinnace': {'tl': 12, 'shipping_size': 40, 'cost': 6_630_000.0, 'engineering_tonnage': 3.2, 'crew': 1},
    'Torpedo Bomber': {'tl': 12, 'shipping_size': 70, 'cost': 46_008_000.0, 'engineering_tonnage': 8.6, 'crew': 2},
    'Troop Transport': {'tl': 15, 'shipping_size': 50, 'cost': 50_500_000.0, 'engineering_tonnage': 7.5, 'crew': 2},
    'Ultralight Fighter': {'tl': 12, 'shipping_size': 6, 'cost': 6_332_400.0, 'engineering_tonnage': 1.36, 'crew': 1},
}


class CarriedOccupant(CeresModel):
    kind: str
    tl: int = 0
    shipping_size: int
    cost: float
    render_in_spec: bool = True
    model_config = {'frozen': True}

    @property
    def requires_pilot(self) -> bool:
        return False

    def build_item(self) -> str | None:
        return self.kind


class Vehicle(CarriedOccupant):
    occupant_type: Literal['VEHICLE'] = 'VEHICLE'

    @classmethod
    def from_catalog(cls, kind: str) -> Vehicle:
        spec = _VEHICLE_SPECS[kind]
        return cls(
            kind=kind,
            tl=int(spec['tl']),
            shipping_size=int(spec['shipping_size']),
            cost=float(spec['cost']),
        )


class SpaceCraft(CarriedOccupant):
    occupant_type: Literal['SPACECRAFT'] = 'SPACECRAFT'
    engineering_tonnage: float = 0.0
    crew: int = 0

    # Today a carried spacecraft is lightweight metadata. If Tycho later needs
    # fully modeled scout ships or other subcraft, this class is the natural
    # place to evolve toward a wrapped Ship/JSON representation.
    @property
    def requires_pilot(self) -> bool:
        return self.crew > 0

    @classmethod
    def from_catalog(cls, kind: str) -> SpaceCraft:
        spec = _SPACECRAFT_SPECS[kind]
        return cls(
            kind=kind,
            tl=int(spec['tl']),
            shipping_size=int(spec['shipping_size']),
            cost=float(spec['cost']),
            engineering_tonnage=float(spec['engineering_tonnage']),
            crew=int(spec['crew']),
        )


class EmptyOccupant(CarriedOccupant):
    occupant_type: Literal['EMPTY'] = 'EMPTY'
    kind: str = 'Empty'
    tl: int = 0
    cost: float = 0.0
    render_in_spec: bool = False

    def __init__(self, docking_space: int | None = None, **data):
        if docking_space is not None and 'shipping_size' not in data:
            data['shipping_size'] = docking_space
        super().__init__(**data)

    def build_item(self) -> str | None:
        return f'Docking Space ({self.shipping_size:g} tons)'


type AnyCarriedOccupant = Annotated[
    Vehicle | SpaceCraft | EmptyOccupant,
    Field(discriminator='occupant_type'),
]


class DockingClamp(ShipPart):
    _specs = {
        'I': dict(tons=1.0, cost=500_000.0),
        'II': dict(tons=5.0, cost=1_000_000.0),
        'III': dict(tons=10.0, cost=2_000_000.0),
        'IV': dict(tons=20.0, cost=4_000_000.0),
        'V': dict(tons=50.0, cost=8_000_000.0),
    }
    kind: str
    craft: AnyCarriedOccupant | None = None

    def build_item(self) -> str | None:
        return f'Docking Clamp, Type {self.kind}'

    def compute_tons(self) -> float:
        return float(self._specs[self.kind]['tons'])

    def compute_cost(self) -> float:
        return float(self._specs[self.kind]['cost'])


class InternalDockingSpace(ShipPart):
    housing_type: Literal['DOCKING_SPACE'] = 'DOCKING_SPACE'
    craft: AnyCarriedOccupant

    def build_item(self) -> str | None:
        if not self.craft.render_in_spec:
            return self.craft.build_item()
        return f'Internal Docking Space: {self.craft.build_item()}'

    def compute_tons(self) -> float:
        return float(math.ceil(self.craft.shipping_size * 1.1))

    def compute_cost(self) -> float:
        return self.compute_tons() * 250_000.0


class FullHangar(ShipPart):
    housing_type: Literal['FULL_HANGAR'] = 'FULL_HANGAR'
    craft: AnyCarriedOccupant

    def build_item(self) -> str | None:
        if not self.craft.render_in_spec:
            return f'Full Hangar ({self.craft.shipping_size:g} tons)'
        return f'Full Hangar: {self.craft.build_item()}'

    def compute_tons(self) -> float:
        return float(math.ceil(self.craft.shipping_size * 2.0))

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0


type InternalCraftHousing = Annotated[
    FullHangar | InternalDockingSpace,
    Field(discriminator='housing_type'),
]


class CraftSection(CeresModel):
    docking_clamps: list[DockingClamp] = Field(default_factory=list)
    # Internal craft housing covers all "stored inside the hull" cases such as
    # docking spaces and full hangars. Future launch tubes / recovery decks
    # belong in this same list-shaped family rather than as bespoke attributes.
    internal_housing: list[InternalCraftHousing] = Field(default_factory=list)

    def _all_parts(self) -> list[ShipPart]:
        return [*self.docking_clamps, *self.internal_housing]

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for part in self._all_parts():
            spec.add_row(ship._spec_row_for_part(SpecSection.CRAFT, part))
            craft = getattr(part, 'craft', None)
            if craft is None:
                continue
            if not craft.render_in_spec:
                continue
            spec.add_row(
                SpecRow(
                    section=SpecSection.CRAFT,
                    item=craft.build_item() or craft.__class__.__name__,
                    cost=craft.cost,
                )
            )
