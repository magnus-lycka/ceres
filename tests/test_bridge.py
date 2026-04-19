import pytest

from tycho.base import ShipBase
from tycho.bridge import Bridge, Cockpit, CommandSection


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


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


def test_bridge_100_tons_standard_size_and_cost():
    b = Bridge()
    b.bind(DummyOwner(12, 100))
    assert b.tons == 10.0
    assert b.cost == 500_000
    assert b.operations_dm == 0


def test_bridge_100_tons_small_bridge_uses_previous_size_band():
    b = Bridge(small=True)
    b.bind(DummyOwner(12, 100))
    assert b.tons == 6.0
    assert b.cost == 250_000
    assert b.operations_dm == -1


def test_small_bridges():
    for size, weight in [
        (51, 3),
        (99, 3),
        (100, 6),
        (200, 6),
        (201, 10),
        (1000, 10),
        (1001, 20),
        (2000, 20),
        (2001, 40),
        (100_000, 40),
        (100_001, 60),
        (200_000, 60),
        (200_001, 80),
    ]:
        b = Bridge(small=True)
        b.bind(DummyOwner(12, size))
        assert b.tons == weight
        assert b.cost == ((size - 1) // 100 + 1) * 250_000


def test_bridge_holographic_cost():
    b = Bridge(holographic=True)
    b.bind(DummyOwner(12, 200))
    assert b.cost == pytest.approx(1_250_000)


def test_bridge_holographic_build_item():
    b = Bridge(holographic=True)
    b.bind(DummyOwner(12, 200))
    assert b.build_item() == 'Bridge (Holographic)'


def test_normal_bridges():
    for size, weight in [
        (50, 3),
        (51, 6),
        (99, 6),
        (100, 10),
        (200, 10),
        (201, 20),
        (1000, 20),
        (1001, 40),
        (2000, 40),
        (2001, 60),
        (100_000, 60),
        (100_001, 80),
        (200_000, 80),
        (200_001, 100),
    ]:
        b = Bridge()
        b.bind(DummyOwner(12, size))
        assert b.tons == weight
        assert b.cost == ((size - 1) // 100 + 1) * 500_000


def test_command_section_all_parts():
    command = CommandSection(bridge=Bridge(), cockpit=Cockpit())
    assert [type(part) for part in command._all_parts()] == [Bridge, Cockpit]
