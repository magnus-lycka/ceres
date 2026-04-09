import math

from .base import CeresModel
from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection


class CarriedCraft(CeresModel):
    shipping_size: int
    cost: float
    model_config = {'frozen': True}

    def build_item(self) -> str | None:
        return self.__class__.__name__


class AirRaft(CarriedCraft):
    shipping_size: int = 4
    cost: float = 250_000.0

    def build_item(self) -> str | None:
        return 'Air/Raft'


class InternalDockingSpace(ShipPart):
    craft: AirRaft

    def build_item(self) -> str | None:
        return f'Internal Docking Space: {self.craft.build_item()}'

    def compute_tons(self) -> float:
        return float(math.ceil(self.craft.shipping_size * 1.1))

    def compute_cost(self) -> float:
        return self.compute_tons() * 250_000.0


class CraftSection(CeresModel):
    docking_space: InternalDockingSpace | None = None

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        if self.docking_space is not None:
            parts.append(self.docking_space)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.docking_space is None:
            return
        spec.add_row(ship._spec_row_for_part(SpecSection.CRAFT, self.docking_space))
        craft = self.docking_space.craft
        spec.add_row(
            SpecRow(
                section=SpecSection.CRAFT,
                item=craft.build_item() or craft.__class__.__name__,
                cost=craft.cost,
            )
        )
