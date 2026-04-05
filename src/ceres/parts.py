from typing import Any, ClassVar

from pydantic import PrivateAttr

from .base import CeresModel, ShipBase


class ShipPart(CeresModel):
    cost: float = 0.0
    power: float = 0.0
    tons: float = 0.0
    minimum_tl: ClassVar[int] = 0
    _owner: ShipBase | None = PrivateAttr(default=None)
    model_config = {'frozen': True}

    def compute_cost(self) -> float:
        return self.cost

    def compute_power(self) -> float:
        return self.power

    def compute_tons(self) -> float:
        return self.tons

    def _refresh_field(self, field_name: str, compute_method_name: str) -> None:
        compute_method = getattr(type(self), compute_method_name)
        base_method = getattr(ShipPart, compute_method_name)
        if compute_method is base_method:
            return
        value = getattr(self, compute_method_name)()
        object.__setattr__(self, field_name, value)

    def refresh_derived_values(self) -> None:
        self._refresh_field('cost', 'compute_cost')
        self._refresh_field('power', 'compute_power')
        self._refresh_field('tons', 'compute_tons')

    def model_post_init(self, __context: Any) -> None:
        self.clear_notes()

    def bind(self, owner: ShipBase) -> None:
        self._owner = owner
        self.clear_notes()
        self.validate_tl()
        self.refresh_derived_values()

    @property
    def owner(self) -> ShipBase:
        if self._owner is None:
            raise RuntimeError(f'{self.__class__.__name__} not bound to a Ship')
        return self._owner

    @property
    def ship_tl(self) -> int:
        return self.owner.tl

    @property
    def effective_tl(self) -> int:
        return self.ship_tl

    def validate_tl(self) -> None:
        if self.ship_tl < self.minimum_tl:
            self.error(
                f'Requires TL{self.minimum_tl}, ship is TL{self.ship_tl}',
            )
