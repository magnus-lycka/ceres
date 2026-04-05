from typing import ClassVar

from ceres import parts
from ceres.base import ShipBase


class DummyShip(ShipBase):
    def __init__(self, tl=14, displacement=100):
        super().__init__(tl=tl, displacement=displacement)


class FixedPart(parts.ShipPart):
    minimum_tl: ClassVar[int] = 9


class HighTlPart(parts.ShipPart):
    minimum_tl: ClassVar[int] = 15


def test_base_part():
    part = FixedPart.model_validate({'cost': 1, 'power': 3.14, 'tons': 4.44})
    owner = DummyShip()
    part.bind(owner)
    assert part.cost == 1
    assert part.minimum_tl == 9
    assert part.ship_tl == 14
    assert part.effective_tl == 14
    assert part.power == 3.14
    assert part.tons == 4.44


def test_part_rejects_ship_below_minimum_tl():
    part = HighTlPart.model_validate({'cost': 1, 'power': 0, 'tons': 0})
    part.bind(DummyShip(tl=14))
    assert [('error', 'Requires TL15, ship is TL14')] == [(note.category.value, note.message) for note in part.notes]
