import pytest

from ceres.base import ShipBase
from ceres.habitation import Staterooms


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_staterooms_tons():
    s = Staterooms(count=4)
    s.bind(DummyOwner(12, 100))
    assert s.tons == pytest.approx(16.0)


def test_staterooms_cost():
    s = Staterooms(count=4)
    s.bind(DummyOwner(12, 100))
    assert s.cost == 2_000_000


def test_staterooms_power_zero():
    s = Staterooms(count=4)
    s.bind(DummyOwner(12, 100))
    assert s.power == 0


def test_staterooms_life_support_uses_full_occupancy():
    s = Staterooms(count=4)
    s.bind(DummyOwner(12, 100))
    assert s.occupancy == 8
    assert s.life_support_cost == 12_000
