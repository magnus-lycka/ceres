import pytest

from tycho import hull, ship
from tycho.base import ShipBase
from tycho.drives import FusionPlantTL12, PowerSection
from tycho.spec import SpecSection
from tycho.storage import (
    CargoAirlock,
    CargoCrane,
    CargoHold,
    CargoSection,
    FuelCargoContainer,
    FuelSection,
    OperationFuel,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)

    def remaining_usable_tonnage(self) -> float:
        return float(self.displacement)


def test_cargo_crane_tons_up_to_150():
    c = CargoCrane()
    assert c.tons_for_space(67) == pytest.approx(3.0)


def test_cargo_crane_tons_exactly_150():
    c = CargoCrane()
    assert c.tons_for_space(150) == pytest.approx(3.0)


def test_cargo_crane_tons_over_150():
    c = CargoCrane()
    assert c.tons_for_space(151) == pytest.approx(3.5)


def test_cargo_crane_cost():
    c = CargoCrane()
    assert c.cost_for_space(150) == pytest.approx(3_000_000)


def test_cargo_hold_usable_tons_subtracts_crane():
    hold = CargoHold(tons=150, crane=CargoCrane())
    owner = DummyOwner(12, 200)
    assert hold.total_tons(owner) == pytest.approx(150)
    assert hold.crane_tons(owner) == pytest.approx(3.0)
    assert hold.usable_tons(owner) == pytest.approx(147.0)


def test_cargo_airlock_has_fixed_tons_and_cost():
    airlock = CargoAirlock()
    owner = DummyOwner(12, 200)
    airlock.bind(owner)
    assert airlock.tons == pytest.approx(2.0)
    assert airlock.cost == pytest.approx(200_000.0)


def test_fuel_cargo_container_rounds_up_tons_from_capacity():
    container = FuelCargoContainer(capacity=30)
    owner = DummyOwner(12, 200)
    container.bind(owner)
    assert container.tons == pytest.approx(32.0)
    assert container.cost == pytest.approx(150_000.0)
    assert container.cargo_capacity == pytest.approx(30.0)


def test_fuel_cargo_container_adds_cargo_capacity_without_cargo_hold():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(fuel_cargo_containers=[FuelCargoContainer(capacity=30)]),
    )
    assert CargoSection.cargo_tons_for_ship(my_ship) == pytest.approx(198.0)


def _make_ship_with_plant():
    fuel = OperationFuel(weeks=1)
    s = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=8)),
        fuel=FuelSection(operation_fuel=fuel),
    )
    assert s.fuel is not None
    return s, s.fuel.operation_fuel


def test_operation_fuel_1_week_tons():
    _, fuel = _make_ship_with_plant()
    assert fuel is not None
    assert float(fuel.tons) == pytest.approx(0.02)


def test_operation_fuel_cost_zero():
    _, fuel = _make_ship_with_plant()
    assert fuel is not None
    assert fuel.cost == 0


def test_operation_fuel_power_zero():
    _, fuel = _make_ship_with_plant()
    assert fuel is not None
    assert fuel.power == 0


def test_operation_fuel_requires_plant():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=1)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.operation_fuel is not None
    assert my_ship.fuel.operation_fuel.tons == 0.0
    assert ('error', 'Ship must have a FusionPlant to compute OperationFuel') in [
        (note.category.value, note.message) for note in my_ship.fuel.operation_fuel.notes
    ]


def test_military_cargo_note_shows_maximum_stores_for_100_days():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        military=True,
        hull=hull.Hull(configuration=hull.standard_hull),
    )
    cargo_row = my_ship.build_spec().rows_for_section(SpecSection.CARGO)[-1]
    assert ('info', '2 tons needed per 100 days of stores and spares') in [
        (note.category.value, note.message) for note in cargo_row.notes
    ]


def test_military_cargo_warning_if_below_recommended_stores_capacity():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        military=True,
        hull=hull.Hull(configuration=hull.standard_hull),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=1.0)]),
    )
    cargo_row = my_ship.build_spec().rows_for_section(SpecSection.CARGO)[-1]
    assert ('warning', 'Cargo is below recommended 100-day stores capacity of 2 tons') in [
        (note.category.value, note.message) for note in cargo_row.notes
    ]
