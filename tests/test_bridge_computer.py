import pytest

from ceres.base import ShipBase
from ceres.bridge import Cockpit
from ceres.computer import Computer


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


# --- Cockpit ---


def test_cockpit_tons():
    c = Cockpit()
    c.bind(DummyOwner(12, 6))
    assert float(c.tons) == 1.5


def test_cockpit_cost():
    c = Cockpit()
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 10_000


def test_cockpit_holographic_cost():
    c = Cockpit(holographic=True)
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 12_500


def test_cockpit_power_zero():
    c = Cockpit()
    c.bind(DummyOwner(12, 6))
    assert c.power == 0


def test_cockpit_recomputes_tons_from_input():
    c = Cockpit.model_validate({'tons': 999})
    c.bind(DummyOwner(12, 6))
    assert c.tons == 1.5


def test_cockpit_recomputes_cost_from_input():
    c = Cockpit.model_validate({'cost': 999})
    c.bind(DummyOwner(12, 6))
    assert c.cost == 10_000


# --- Computer ---


def test_computer_5_cost():
    c = Computer(rating=5)
    c.bind(DummyOwner(12, 6))
    assert c.minimum_tl == 7
    assert c.ship_tl == 12
    assert c.effective_tl == 12
    assert float(c.cost) == 30_000


def test_computer_10_cost():
    c = Computer(rating=10)
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 160_000


def test_computer_15_cost():
    c = Computer(rating=15)
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 2_000_000


def test_computer_tons_zero():
    c = Computer(rating=5)
    c.bind(DummyOwner(12, 6))
    assert float(c.tons) == 0


def test_computer_power_zero():
    c = Computer(rating=5)
    c.bind(DummyOwner(12, 6))
    assert c.power == 0


def test_computer_5_min_tl():
    # Computer/5 needs TL7; TL6 ship should fail
    with pytest.raises(ValueError):
        c = Computer(rating=5)
        c.bind(DummyOwner(6, 100))


def test_computer_recomputes_cost_from_input():
    c = Computer.model_validate({'rating': 5, 'cost': 999})
    c.bind(DummyOwner(12, 6))
    assert c.cost == 30_000
