from ceres import ship
from ceres.base import ShipBase
from ceres.systems import Airlock, AirRaft, InternalDockingSpace, ProbeDrones, Workshop


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_workshop_tons():
    w = Workshop()
    w.bind(DummyOwner(12, 100))
    assert w.tons == 6.0


def test_workshop_cost():
    w = Workshop()
    w.bind(DummyOwner(12, 100))
    assert w.cost == 900_000


def test_workshop_power_zero():
    w = Workshop()
    w.bind(DummyOwner(12, 100))
    assert w.power == 0


def test_probe_drones_tons():
    p = ProbeDrones(count=10)
    p.bind(DummyOwner(12, 100))
    assert p.tons == 2.0


def test_probe_drones_cost():
    p = ProbeDrones(count=10)
    p.bind(DummyOwner(12, 100))
    assert p.cost == 1_000_000


def test_probe_drones_power_zero():
    p = ProbeDrones(count=10)
    p.bind(DummyOwner(12, 100))
    assert p.power == 0


def test_air_raft_cost():
    a = AirRaft()
    assert a.shipping_size == 4
    assert a.cost == 250_000


def test_internal_docking_space_for_air_raft():
    d = InternalDockingSpace(craft=AirRaft())
    d.bind(DummyOwner(12, 100))
    assert d.tons == 5.0
    assert d.cost == 1_250_000
    assert d.power == 0


def test_airlock_is_free_on_100_ton_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        airlocks=[Airlock()],
    )
    airlock = my_ship.airlocks[0]
    assert airlock.tons == 0.0
    assert airlock.cost == 0.0


def test_airlock_costs_tonnage_and_money_on_99_ton_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        airlocks=[Airlock()],
    )
    airlock = my_ship.airlocks[0]
    assert airlock.tons == 2.0
    assert airlock.cost == 200_000.0
