import pytest

from ceres import ship
from ceres.base import ShipBase
from ceres.systems import (
    Airlock,
    CargoCrane,
    CargoHold,
    CommonArea,
    FuelScoops,
    MedicalBay,
    ProbeDrones,
    Workshop,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)

    def cargo_space_for(self, hold) -> float:
        return float(self.displacement)


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


def test_common_area_cost():
    c = CommonArea(tons=1.0)
    c.bind(DummyOwner(12, 100))
    assert c.cost == 100_000


def test_common_area_power_zero():
    c = CommonArea(tons=1.0)
    c.bind(DummyOwner(12, 100))
    assert c.power == 0


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


def test_medical_bay_tons():
    m = MedicalBay()
    m.bind(DummyOwner(12, 200))
    assert m.tons == 4.0


def test_medical_bay_cost():
    m = MedicalBay()
    m.bind(DummyOwner(12, 200))
    assert m.cost == 2_000_000


def test_medical_bay_power():
    m = MedicalBay()
    m.bind(DummyOwner(12, 200))
    assert m.power == 1.0


def test_cargo_crane_tons_up_to_150():
    c = CargoCrane()
    assert c.tons_for_space(67) == pytest.approx(3.0)  # 2.5 + 0.5 * ceil(67/150) = 3.0


def test_cargo_crane_tons_exactly_150():
    c = CargoCrane()
    assert c.tons_for_space(150) == pytest.approx(3.0)


def test_cargo_crane_tons_over_150():
    c = CargoCrane()
    assert c.tons_for_space(151) == pytest.approx(3.5)  # 2.5 + 0.5 * ceil(151/150) = 3.5


def test_cargo_crane_cost():
    c = CargoCrane()
    assert c.cost_for_space(150) == pytest.approx(3_000_000)


def test_cargo_hold_usable_tons_subtracts_crane():
    hold = CargoHold(tons=150, crane=CargoCrane())
    owner = DummyOwner(12, 200)
    assert hold.total_tons(owner) == pytest.approx(150)
    assert hold.crane_tons(owner) == pytest.approx(3.0)
    assert hold.usable_tons(owner) == pytest.approx(147.0)


def test_fuel_scoops_auto_included_for_streamlined_hull():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
    )
    assert my_ship.fuel_scoops is not None


def test_fuel_scoops_free_with_streamlined_hull():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
    )
    assert my_ship.fuel_scoops is not None
    assert my_ship.fuel_scoops.tons == 0.0
    assert my_ship.fuel_scoops.cost == 0.0


def test_fuel_scoops_not_auto_included_for_standard_hull():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.standard_hull),
    )
    assert my_ship.fuel_scoops is None


def test_fuel_scoops_paid_when_added_to_standard_hull():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.standard_hull),
        fuel_scoops=FuelScoops(),
    )
    assert my_ship.fuel_scoops is not None
    assert my_ship.fuel_scoops.tons == 0.0
    assert my_ship.fuel_scoops.cost == 1_000_000.0


def test_fuel_scoops_explicit_on_streamlined_hull_still_free():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        fuel_scoops=FuelScoops(),
    )
    assert my_ship.fuel_scoops is not None
    assert my_ship.fuel_scoops.cost == 0.0


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
