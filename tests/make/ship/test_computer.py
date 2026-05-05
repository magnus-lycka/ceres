import pytest

from ceres.gear.software import Intellect
from ceres.make.ship.base import ShipBase
from ceres.make.ship.computer import (
    Computer,
    Core,
)
from ceres.make.ship.software import Library, Manoeuvre


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_computer_5_cost():
    c = Computer(processing=5)
    c.bind(DummyOwner(12, 6))
    assert c.tl == 7
    assert c.assembly_tl == 12
    assert c.processing == 5
    assert c.jump_control_processing == 5
    assert float(c.cost) == 30_000


def test_computer_10_cost():
    c = Computer(processing=10)
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 160_000


def test_computer_15_cost():
    c = Computer(processing=15)
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 2_000_000


def test_computer_rejects_invalid_processing():
    with pytest.raises(ValueError, match='Unsupported Computer processing 23'):
        Computer(processing=23)


def test_computer_tons_zero():
    c = Computer(processing=5)
    c.bind(DummyOwner(12, 6))
    assert float(c.tons) == 0


def test_computer_power_zero():
    c = Computer(processing=5)
    c.bind(DummyOwner(12, 6))
    assert c.power == 0


def test_computer_5_min_tl():
    c = Computer(processing=5)
    c.bind(DummyOwner(6, 100))
    assert ('error', 'Requires TL7, ship is TL6') in [(note.category.value, note.message) for note in c.notes]


def test_computer_recomputes_cost_from_input():
    c = Computer.model_validate({'kind': 'computer', 'processing': 5, 'cost': 999})
    c.bind(DummyOwner(12, 6))
    assert c.cost == 30_000


def test_computer_bis_increases_cost_and_jump_control_processing():
    c = Computer(processing=5, bis=True)
    c.bind(DummyOwner(12, 6))
    assert c.processing == 5
    assert c.jump_control_processing == 10
    assert c.cost == 45_000


def test_computer_fib_increases_cost():
    c = Computer(processing=5, fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 45_000


def test_computer_bis_and_fib_double_cost():
    c = Computer(processing=5, bis=True, fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 60_000


def test_core_40_hardware():
    c = Core(processing=40)
    c.bind(DummyOwner(12, 100))
    assert c.tl == 9
    assert c.processing == 40
    assert c.jump_control_processing == 40
    assert c.cost == 45_000_000


def test_core_40_fib_hardware():
    c = Core(processing=40, fib=True)
    c.bind(DummyOwner(13, 100))
    assert c.build_item() == 'Core/40/fib'
    assert c.cost == pytest.approx(67_500_000.0)


def test_included_software_packages():
    c = Computer(processing=5)
    c.bind(DummyOwner(12, 100))
    assert [type(package) for package in c.included_software] == [Library, Manoeuvre, Intellect]
    assert [package.cost for package in c.included_software] == [0.0, 0.0, 0.0]
