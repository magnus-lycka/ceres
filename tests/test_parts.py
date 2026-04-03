from typing import ClassVar

import pytest

from ceres import parts


class DummyShip:
    def __init__(self, tl=14):
        self.tl = tl
        self.displacement = 100


class FixedPart(parts.ShipPart):
    minimum_tl: ClassVar[int] = 9


class HighTlPart(parts.ShipPart):
    minimum_tl: ClassVar[int] = 15


def test_base_part():
    part = FixedPart(cost=1, power=3.14, tons=4.44)
    owner = DummyShip()
    part.bind(owner)
    assert part.cost == 1
    assert part.minimum_tl == 9
    assert part.ship_tl == 14
    assert part.effective_tl == 14
    assert part.power == 3.14
    assert part.tons == 4.44


def test_part_rejects_ship_below_minimum_tl():
    with pytest.raises(ValueError):
        HighTlPart(cost=1, power=0, tons=0).bind(DummyShip(tl=14))
