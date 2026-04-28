import math

from pydantic import Field

from .base import CeresModel
from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection


class CarriedCraft(CeresModel):
    shipping_size: int
    cost: float
    requires_pilot: bool = True
    render_in_spec: bool = True
    model_config = {'frozen': True}

    def build_item(self) -> str | None:
        return self.__class__.__name__


class AirRaft(CarriedCraft):
    shipping_size: int = 4
    cost: float = 250_000.0
    requires_pilot: bool = False

    def build_item(self) -> str | None:
        return 'Air/Raft'


class SlowPinnace(CarriedCraft):
    shipping_size: int = 40
    cost: float = 6_630_000.0

    def build_item(self) -> str | None:
        return 'Slow Pinnace'


class PassengerShuttle(CarriedCraft):
    shipping_size: int = 95
    cost: float = 14_305_000.0

    def build_item(self) -> str | None:
        return 'Passenger Shuttle'


class FreeGenericCraft(CarriedCraft):
    cost: float = 0.0
    requires_pilot: bool = False
    render_in_spec: bool = False

    def __init__(self, docking_space: int | None = None, **data):
        if docking_space is not None and 'shipping_size' not in data:
            data['shipping_size'] = docking_space
        super().__init__(**data)

    def build_item(self) -> str | None:
        return f'Docking Space ({self.shipping_size:g} tons)'


class DockingClamp(ShipPart):
    _specs = {
        'I': dict(tons=1.0, cost=500_000.0),
        'II': dict(tons=5.0, cost=1_000_000.0),
        'III': dict(tons=10.0, cost=2_000_000.0),
        'IV': dict(tons=20.0, cost=4_000_000.0),
        'V': dict(tons=50.0, cost=8_000_000.0),
    }
    kind: str

    def build_item(self) -> str | None:
        return f'Docking Clamp, Type {self.kind}'

    def compute_tons(self) -> float:
        return float(self._specs[self.kind]['tons'])

    def compute_cost(self) -> float:
        return float(self._specs[self.kind]['cost'])


class InternalDockingSpace(ShipPart):
    craft: CarriedCraft

    def build_item(self) -> str | None:
        if not self.craft.render_in_spec:
            return self.craft.build_item()
        return f'Internal Docking Space: {self.craft.build_item()}'

    def compute_tons(self) -> float:
        return float(math.ceil(self.craft.shipping_size * 1.1))

    def compute_cost(self) -> float:
        return self.compute_tons() * 250_000.0


class FullHangar(ShipPart):
    craft: CarriedCraft

    def build_item(self) -> str | None:
        if not self.craft.render_in_spec:
            return f'Full Hangar ({self.craft.shipping_size:g} tons)'
        return f'Full Hangar: {self.craft.build_item()}'

    def compute_tons(self) -> float:
        return float(math.ceil(self.craft.shipping_size * 2.0))

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0


class CraftSection(CeresModel):
    full_hangars: list[FullHangar] = Field(default_factory=list)
    docking_clamps: list[DockingClamp] = Field(default_factory=list)
    docking_space: InternalDockingSpace | None = None
    auxiliary_docking_spaces: list[InternalDockingSpace] = Field(default_factory=list)

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = [*self.full_hangars, *self.docking_clamps]
        if self.docking_space is not None:
            parts.append(self.docking_space)
        parts.extend(self.auxiliary_docking_spaces)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        craft_rows: list[SpecRow] = []
        for part in self._all_parts():
            spec.add_row(ship._spec_row_for_part(SpecSection.CRAFT, part))
            if isinstance(part, DockingClamp):
                continue
            craft = part.craft
            if not craft.render_in_spec:
                continue
            craft_rows.append(
                SpecRow(
                    section=SpecSection.CRAFT,
                    item=craft.build_item() or craft.__class__.__name__,
                    cost=craft.cost,
                )
            )
        for row in craft_rows:
            spec.add_row(row)
