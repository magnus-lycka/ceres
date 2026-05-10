import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.crafts import CraftSection, DockingClamp, SpaceCraft
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, PowerSection, RDrive16
from ceres.make.ship.spec import SpecSection
from ceres.make.ship.storage import (
    CargoAirlock,
    CargoCrane,
    CargoHold,
    CargoSection,
    FuelCargoContainer,
    FuelProcessor,
    FuelScoops,
    FuelSection,
    JumpFuel,
    OperationFuel,
    ReactionFuel,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement, **kwargs):
        super().__init__(tl=tl, displacement=displacement, **kwargs)

    def remaining_usable_tonnage(self) -> float:
        return float(self.displacement)


@pytest.mark.parametrize(
    ('part', 'expected_tons', 'expected_cost', 'expected_power'),
    [
        (FuelScoops(), 0.0, 1_000_000.0, 0.0),
        (FuelScoops(free=True), 0.0, 0.0, 0.0),
        (CargoAirlock(size=3.0), 3.0, 300_000.0, 0.0),
        (FuelCargoContainer(capacity=30.0), 32.0, 150_000.0, 0.0),
    ],
)
def test_converted_storage_values_are_computed_properties_not_serialized_fields(
    part, expected_tons, expected_cost, expected_power
):
    part.bind(DummyOwner(12, 200))
    dump = part.model_dump()

    assert part.tons == pytest.approx(expected_tons)
    assert part.cost == pytest.approx(expected_cost)
    assert part.power == pytest.approx(expected_power)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


@pytest.mark.parametrize(
    ('part_cls', 'data', 'expected_tons', 'expected_cost', 'expected_power'),
    [
        (FuelScoops, {}, 0.0, 1_000_000.0, 0.0),
        (FuelScoops, {'free': True}, 0.0, 0.0, 0.0),
        (CargoAirlock, {'size': 3.0}, 3.0, 300_000.0, 0.0),
        (FuelCargoContainer, {'capacity': 30.0}, 32.0, 150_000.0, 0.0),
    ],
)
def test_converted_storage_values_ignore_stale_numeric_inputs(
    part_cls, data, expected_tons, expected_cost, expected_power
):
    part = part_cls.model_validate({'tons': 99, 'cost': 99, 'power': 99, **data})
    part.bind(DummyOwner(12, 200))

    assert part.tons == pytest.approx(expected_tons)
    assert part.cost == pytest.approx(expected_cost)
    assert part.power == pytest.approx(expected_power)


def test_fuel_processor_values_are_property_backed_design_fields():
    processor = FuelProcessor.model_validate({'tons': 2.0, 'cost': 99, 'power': 99})
    processor.bind(DummyOwner(12, 200))
    dump = processor.model_dump()

    assert processor.tons == pytest.approx(2.0)
    assert processor.cost == pytest.approx(100_000.0)
    assert processor.power == pytest.approx(2.0)
    assert dump['tons'] == pytest.approx(2.0)
    assert 'cost' not in dump
    assert 'power' not in dump


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
    assert float(fuel.tons) == pytest.approx(0.1)


def test_operation_fuel_cost_zero():
    _, fuel = _make_ship_with_plant()
    assert fuel is not None
    assert fuel.cost == 0


def test_operation_fuel_power_zero():
    _, fuel = _make_ship_with_plant()
    assert fuel is not None
    assert fuel.power == 0


def test_operation_fuel_values_are_computed_properties_not_serialized_fields():
    _, fuel = _make_ship_with_plant()
    assert fuel is not None
    dump = fuel.model_dump()

    assert fuel.tons == pytest.approx(0.1)
    assert fuel.cost == pytest.approx(0.0)
    assert fuel.power == pytest.approx(0.0)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_operation_fuel_ignores_stale_numeric_inputs():
    fuel = OperationFuel.model_validate({'weeks': 1, 'tons': 99, 'cost': 99, 'power': 99})
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=8)),
        fuel=FuelSection(operation_fuel=fuel),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.operation_fuel is not None
    assert my_ship.fuel.operation_fuel.tons == pytest.approx(0.1)
    assert my_ship.fuel.operation_fuel.cost == pytest.approx(0.0)
    assert my_ship.fuel.operation_fuel.power == pytest.approx(0.0)


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
    assert 'Ship must have a FusionPlant to compute OperationFuel' in my_ship.fuel.operation_fuel.notes.errors


def test_jump_fuel_uses_performance_displacement_for_external_transport_load():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.dispersed_structure),
        drives=DriveSection(j_drive=JDrive2()),
        fuel=FuelSection(jump_fuel=JumpFuel(parsecs=2)),
        craft=CraftSection(docking_clamps=[DockingClamp(craft=SpaceCraft.from_catalog('Pinnace'), transported=True)]),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.jump_fuel is not None
    assert my_ship.fuel.jump_fuel.tons == pytest.approx(88.0)


def test_jump_fuel_values_are_computed_properties_not_serialized_fields():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.dispersed_structure),
        drives=DriveSection(j_drive=JDrive2()),
        fuel=FuelSection(jump_fuel=JumpFuel.model_validate({'parsecs': 2, 'tons': 99, 'cost': 99, 'power': 99})),
        craft=CraftSection(docking_clamps=[DockingClamp(craft=SpaceCraft.from_catalog('Pinnace'), transported=True)]),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.jump_fuel is not None
    dump = my_ship.fuel.jump_fuel.model_dump()

    assert my_ship.fuel.jump_fuel.tons == pytest.approx(88.0)
    assert my_ship.fuel.jump_fuel.cost == pytest.approx(0.0)
    assert my_ship.fuel.jump_fuel.power == pytest.approx(0.0)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_reaction_fuel_values_are_computed_properties_not_serialized_fields():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(r_drive=RDrive16()),
        fuel=FuelSection(
            reaction_fuel=ReactionFuel.model_validate({'minutes': 60, 'tons': 99, 'cost': 99, 'power': 99})
        ),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.reaction_fuel is not None
    dump = my_ship.fuel.reaction_fuel.model_dump()

    assert my_ship.fuel.reaction_fuel.tons == pytest.approx(80.0)
    assert my_ship.fuel.reaction_fuel.cost == pytest.approx(0.0)
    assert my_ship.fuel.reaction_fuel.power == pytest.approx(0.0)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_military_cargo_note_shows_maximum_stores_for_100_days():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        military=True,
        hull=hull.Hull(configuration=hull.standard_hull),
    )
    cargo_row = my_ship.build_spec().rows_for_section(SpecSection.CARGO)[-1]
    assert '2 tons needed per 100 days of stores and spares' in cargo_row.notes.infos


def test_military_cargo_warning_if_below_recommended_stores_capacity():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        military=True,
        hull=hull.Hull(configuration=hull.standard_hull),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=1.0)]),
    )
    cargo_row = my_ship.build_spec().rows_for_section(SpecSection.CARGO)[-1]
    assert 'Cargo is below recommended 100-day stores capacity of 2 tons' in cargo_row.notes.warnings


def test_spec_always_shows_residual_cargo_space_even_with_explicit_cargo_parts():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(
            cargo_airlocks=[CargoAirlock()],
            fuel_cargo_containers=[FuelCargoContainer(capacity=30)],
        ),
    )

    cargo_rows = my_ship.build_spec().rows_for_section(SpecSection.CARGO)
    assert [(row.item, row.tons) for row in cargo_rows] == [
        ('Cargo Airlock (2 tons)', 2.0),
        ('Fuel/Cargo Container (30 tons)', 32),
        ('Cargo Space', pytest.approx(166.0)),
    ]
