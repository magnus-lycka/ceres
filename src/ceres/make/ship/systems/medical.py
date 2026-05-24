from typing import ClassVar, Literal

from ceres.shared import CeresModel

from ..parts import ShipPart
from .common import _ExplicitTonsSystemPart


class BasicAutodoc(CeresModel):
    description: Literal['Basic Autodoc'] = 'Basic Autodoc'

    @property
    def cost(self) -> float:
        return 100_000.0


class MedicalBay(ShipPart):
    system_type: Literal['MEDICAL_BAY'] = 'MEDICAL_BAY'
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    autodoc: BasicAutodoc | None = None

    def item_description(self) -> str:
        if self.autodoc is not None:
            return 'Medical Bay, Basic Autodoc'
        return 'Medical Bay'

    @property
    def tons(self) -> float:
        return 4.0

    @property
    def cost(self) -> float:
        cost = 2_000_000.0
        if self.autodoc is not None:
            cost += self.autodoc.cost
        return cost

    @property
    def power(self) -> float:
        return 1.0


class Biosphere(_ExplicitTonsSystemPart):
    system_type: Literal['BIOSPHERE'] = 'BIOSPHERE'
    description: Literal['Biosphere'] = 'Biosphere'
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0

    @property
    def power(self) -> float:
        return self.tons
