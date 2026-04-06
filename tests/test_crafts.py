from ceres.base import ShipBase
from ceres.crafts import AirRaft, InternalDockingSpace


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


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
