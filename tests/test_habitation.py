import pytest

from ceres.base import ShipBase
from ceres.habitation import LowBerths, Staterooms


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


def test_low_berths_tons():
    lb = LowBerths(count=20)
    lb.bind(DummyOwner(12, 200))
    assert lb.tons == pytest.approx(10.0)


def test_low_berths_cost():
    lb = LowBerths(count=20)
    lb.bind(DummyOwner(12, 200))
    assert lb.cost == 1_000_000


def test_low_berths_power():
    assert LowBerths(count=20).compute_power() == 2  # ceil(20/10)
    assert LowBerths(count=1).compute_power() == 1   # ceil(1/10)
    assert LowBerths(count=10).compute_power() == 1
    assert LowBerths(count=11).compute_power() == 2
