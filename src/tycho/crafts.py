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


class CraftSection(CeresModel):
    docking_space: InternalDockingSpace | None = None
    auxiliary_docking_spaces: list[InternalDockingSpace] = Field(default_factory=list)

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        if self.docking_space is not None:
            parts.append(self.docking_space)
        parts.extend(self.auxiliary_docking_spaces)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for docking_space in self._all_parts():
            spec.add_row(ship._spec_row_for_part(SpecSection.CRAFT, docking_space))
            craft = docking_space.craft
            if not craft.render_in_spec:
                continue
            spec.add_row(
                SpecRow(
                    section=SpecSection.CRAFT,
                    item=craft.build_item() or craft.__class__.__name__,
                    cost=craft.cost,
                )
            )
