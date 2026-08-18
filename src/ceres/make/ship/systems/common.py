from typing import ClassVar

from pydantic import ConfigDict, Field

from ..installable import not_installable
from ..parts import ShipPartBase


@not_installable
class _ZeroPowerSystemPart(ShipPartBase):
    power: ClassVar[float]

    @property
    def power(self) -> float:
        return 0.0


@not_installable
class _ExplicitTonsSystemPart(ShipPartBase):
    tons: ClassVar[float]
    base_tons: float = Field(0.0, alias='tons')
    model_config = ConfigDict(frozen=True, populate_by_name=True, serialize_by_alias=True)

    @property
    def tons(self) -> float:
        return self.base_tons
