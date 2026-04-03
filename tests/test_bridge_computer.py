import pytest

from ceres.base import ShipBase
from ceres.bridge import Cockpit
from ceres.computer import Computer5, Computer10, Computer15, Core40


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
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert c.minimum_tl == 7
    assert c.ship_tl == 12
    assert c.effective_tl == 12
    assert c.processing == 5
    assert c.jump_control_processing == 5
    assert float(c.cost) == 30_000


def test_computer_10_cost():
    c = Computer10()
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 160_000


def test_computer_15_cost():
    c = Computer15()
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 2_000_000


def test_computer_tons_zero():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert float(c.tons) == 0


def test_computer_power_zero():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert c.power == 0


def test_computer_5_min_tl():
    # Computer/5 needs TL7; TL6 ship should fail
    with pytest.raises(ValueError):
        c = Computer5()
        c.bind(DummyOwner(6, 100))


def test_computer_recomputes_cost_from_input():
    c = Computer5.model_validate({'cost': 999})
    c.bind(DummyOwner(12, 6))
    assert c.cost == 30_000


def test_computer_bis_increases_cost_and_jump_control_processing():
    c = Computer5(bis=True)
    c.bind(DummyOwner(12, 6))
    assert c.processing == 5
    assert c.jump_control_processing == 10
    assert c.cost == 45_000


def test_computer_fib_increases_cost():
    c = Computer5(fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 45_000


def test_computer_bis_and_fib_double_cost():
    c = Computer5(bis=True, fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 60_000


def test_core_40_hardware():
    c = Core40()
    c.bind(DummyOwner(12, 100))
    assert c.minimum_tl == 9
    assert c.processing == 40
    assert c.jump_control_processing == 40
    assert c.cost == 45_000_000
