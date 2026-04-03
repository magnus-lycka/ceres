import pytest
from pydantic import ValidationError
from ceres.bridge import Cockpit
from ceres.computer import Computer


class DummyOwner:
    def __init__(self, tl, displacement):
        self.tl = tl
        self.displacement = displacement


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
    assert float(c.power) == 0


def test_cockpit_cannot_set_tons():
    with pytest.raises(ValidationError):
        Cockpit(tons=999)


def test_cockpit_cannot_set_cost():
    with pytest.raises(ValidationError):
        Cockpit(cost=999)


# --- Computer ---

def test_computer_5_cost():
    c = Computer(rating=5)
    c.bind(DummyOwner(12, 6))
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
    assert float(c.power) == 0


def test_computer_5_min_tl():
    # Computer/5 needs TL7; TL6 ship should fail
    with pytest.raises(ValueError):
        c = Computer(rating=5)
        c.bind(DummyOwner(6, 100))


def test_computer_cannot_set_cost():
    with pytest.raises(ValidationError):
        Computer(rating=5, cost=999)
