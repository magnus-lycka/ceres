import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.crafts import CraftSection, DockingClamp, SpaceCraft
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive2, PowerSection, RDrive16
from ceres.make.ship.spec import SpecSection
from ceres.make.ship.storage import (
    CargoAirlock,
    CargoCrane,
    CargoHold,
    CargoNet,
    CargoScoop,
    CargoSection,
    Collector,
    ConcealedCompartment,
    ExternalCargoMount,
    FuelCargoContainer,
    FuelProcessor,
    FuelRefinery,
    FuelScoops,
    FuelSection,
    FuelTankCompartment,
    InterplanetaryJumpNet,
    InterstellarJumpNet,
    JumpFuel,
    LoadingBeltTL7,
    LoadingBeltTL12,
    MetalHydrideStorage,
    OperationFuel,
    Ramscoop,
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


@pytest.mark.parametrize(
    ('tl', 'output_per_ton', 'power_per_ton', 'crew_per_tons', 'cost_per_ton'),
    [
        (7, 10.0, 2.0, 50.0, 100_000.0),
        (10, 12.0, 1.0, 100.0, 250_000.0),
        (13, 15.0, 1.0, 500.0, 500_000.0),
    ],
)
def test_fuel_refinery_values(tl, output_per_ton, power_per_ton, crew_per_tons, cost_per_ton):
    refinery = FuelRefinery(tl=tl, tons=10)
    refinery.bind(DummyOwner(tl, 200))

    assert refinery.output_per_day == pytest.approx(10 * output_per_ton)
    assert refinery.power == pytest.approx(10 * power_per_ton)
    assert refinery.crew_requirement == pytest.approx(10 / crew_per_tons)
    assert refinery.cost == pytest.approx(10 * cost_per_ton)
    assert refinery.build_item() == f'Fuel Refinery ({10 * output_per_ton:g} tons/day)'


def test_fuel_refinery_values_are_property_backed_design_fields():
    refinery = FuelRefinery.model_validate({'tl': 10, 'tons': 10, 'cost': 99, 'power': 99})
    refinery.bind(DummyOwner(10, 200))
    dump = refinery.model_dump()

    assert refinery.tons == pytest.approx(10.0)
    assert refinery.output_per_day == pytest.approx(120.0)
    assert refinery.cost == pytest.approx(2_500_000.0)
    assert refinery.power == pytest.approx(10.0)
    assert dump['tons'] == pytest.approx(10.0)
    assert 'cost' not in dump
    assert 'power' not in dump


def test_fuel_refinery_appears_as_fuel_spec_row():
    my_ship = ship.Ship(
        tl=10,
        displacement=400,
        hull=hull.Hull(configuration=hull.dispersed_structure),
        fuel=FuelSection(fuel_refinery=FuelRefinery(tl=10, tons=10)),
    )
    row = my_ship.build_spec().row('Fuel Refinery (120 tons/day)', section=SpecSection.FUEL)
    assert row.tons == pytest.approx(10.0)
    assert row.power == pytest.approx(-10.0)
    assert row.cost == pytest.approx(2_500_000.0)
    assert row.notes.infos == ['Requires 1 crew per 100 tons']


def test_fuel_power_load_includes_processor_and_refinery():
    my_ship = ship.Ship(
        tl=10,
        displacement=400,
        hull=hull.Hull(configuration=hull.dispersed_structure),
        fuel=FuelSection(fuel_processor=FuelProcessor(tons=2), fuel_refinery=FuelRefinery(tl=10, tons=10)),
    )
    assert my_ship.fuel_power_load == pytest.approx(12.0)


def test_ramscoop_values_use_minimum_size():
    ramscoop = Ramscoop()
    ramscoop.bind(DummyOwner(12, 200))

    assert ramscoop.tons == pytest.approx(10.0)
    assert ramscoop.cost == pytest.approx(2_500_000.0)
    assert ramscoop.power == pytest.approx(0.0)
    assert ramscoop.collection_per_week == pytest.approx(50.0)
    assert ramscoop.build_item() == 'Ramscoop (50 tons/week)'


def test_ramscoop_values_use_one_percent_plus_five_and_extra_tons():
    ramscoop = Ramscoop(extra_tons=5)
    ramscoop.bind(DummyOwner(12, 1_000))

    assert ramscoop.tons == pytest.approx(20.0)
    assert ramscoop.cost == pytest.approx(5_000_000.0)
    assert ramscoop.collection_per_week == pytest.approx(100.0)


def test_ramscoop_values_are_computed_properties_not_serialized_fields():
    ramscoop = Ramscoop.model_validate({'extra_tons': 5, 'tons': 99, 'cost': 99, 'power': 99})
    ramscoop.bind(DummyOwner(12, 1_000))
    dump = ramscoop.model_dump()

    assert ramscoop.tons == pytest.approx(20.0)
    assert ramscoop.cost == pytest.approx(5_000_000.0)
    assert ramscoop.power == pytest.approx(0.0)
    assert dump['extra_tons'] == pytest.approx(5.0)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_ramscoop_appears_as_fuel_spec_row_and_rejects_streamlined_hull():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        fuel=FuelSection(ramscoop=Ramscoop()),
    )
    row = my_ship.build_spec().row('Ramscoop (50 tons/week)', section=SpecSection.FUEL)
    assert row.tons == pytest.approx(10.0)
    assert row.cost == pytest.approx(2_500_000.0)
    assert row.notes.infos == [
        'Collects 5 tons of hydrogen per week per ton of ramscoop',
        'Does not require fuel scoops or fuel processors',
    ]
    assert 'Ramscoops prevent atmospheric re-entry and cannot be installed on streamlined hulls' in row.notes.errors


def test_metal_hydride_storage_doubles_fuel_tankage_and_adds_cost():
    my_ship = ship.Ship(
        tl=9,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=1),
            metal_hydride_storage=MetalHydrideStorage(),
        ),
    )

    fuel_row = my_ship.build_spec().row('J-1, metal hydride storage', section=SpecSection.FUEL)
    assert my_ship.fuel is not None
    assert my_ship.fuel.jump_fuel is not None
    assert my_ship.fuel.metal_hydride_storage is not None
    assert my_ship.fuel.jump_fuel.tons == pytest.approx(10.0)
    assert my_ship.fuel.metal_hydride_storage.tons == pytest.approx(10.0)
    assert fuel_row.tons == pytest.approx(20.0)
    assert fuel_row.cost == pytest.approx(4_000_000.0)
    assert fuel_row.notes.infos == [
        'Replaces normal liquid hydrogen fuel tankage; consumes twice the stored fuel volume',
        'Fuel leak loss reduced to 25% of indicated amount, minimum 1 ton',
    ]


def test_metal_hydride_storage_requires_tl9():
    my_ship = ship.Ship(
        tl=8,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=1),
            metal_hydride_storage=MetalHydrideStorage(),
        ),
    )

    assert my_ship.fuel is not None
    assert my_ship.fuel.metal_hydride_storage is not None
    assert 'Requires TL9, ship is TL8' in my_ship.fuel.metal_hydride_storage.notes.errors


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


def test_cargo_crane_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=150, crane=CargoCrane())]),
    )

    crane_row = my_ship.build_spec().row('Cargo Crane', section=SpecSection.CARGO)
    assert crane_row.tons == pytest.approx(3.0)
    assert crane_row.cost == pytest.approx(3_000_000.0)


def test_auto_sized_cargo_hold_consumes_remaining_displacement_without_extra_residual_row():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(
            cargo_airlocks=[CargoAirlock()],
            cargo_holds=[CargoHold(crane=CargoCrane())],
        ),
    )

    cargo_rows = my_ship.build_spec().rows_for_section(SpecSection.CARGO)
    assert [(row.item, row.tons) for row in cargo_rows] == [
        ('Cargo Airlock (2 tons)', 2.0),
        ('Cargo Hold', pytest.approx(194.5)),
        ('Cargo Crane', pytest.approx(3.5)),
    ]


@pytest.mark.parametrize(
    ('belt', 'expected_tl', 'expected_cost', 'expected_power', 'expected_replaced_crew'),
    [
        (LoadingBeltTL7(), 7, 3_000.0, 0.0, 10),
        (LoadingBeltTL12(), 12, 10_000.0, 1.0, 25),
    ],
)
def test_loading_belt_values(belt, expected_tl, expected_cost, expected_power, expected_replaced_crew):
    assert belt.tl == expected_tl
    assert belt.tons == pytest.approx(1.0)
    assert belt.cost == pytest.approx(expected_cost)
    assert belt.power == pytest.approx(expected_power)
    assert belt.replaced_loading_crew == expected_replaced_crew


def test_loading_belt_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(loading_belts=[LoadingBeltTL12()]),
    )

    row = my_ship.build_spec().row('Loading Belt (TL12)', section=SpecSection.CARGO)
    assert row.tons == pytest.approx(1.0)
    assert row.cost == pytest.approx(10_000.0)
    assert row.power == pytest.approx(-1.0)


def test_loading_belt_requires_matching_ship_tl():
    my_ship = ship.Ship(
        tl=9,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(loading_belts=[LoadingBeltTL12()]),
    )

    assert my_ship.cargo is not None
    loading_belt = my_ship.cargo.loading_belts[0]
    assert 'Requires TL12, ship is TL9' in loading_belt.notes.errors


def test_cargo_scoop_values_and_notes():
    scoop = CargoScoop()

    assert scoop.tons == pytest.approx(2.0)
    assert scoop.cost == pytest.approx(500_000.0)
    assert scoop.power == pytest.approx(0.0)
    assert scoop.notes.infos == [
        'Picks up floating cargo at one ton per round',
        'Pilot check required; ship takes damage equal to negative Effect on failure',
    ]


def test_cargo_scoop_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(cargo_scoops=[CargoScoop()]),
    )

    row = my_ship.build_spec().row('Cargo Scoop', section=SpecSection.CARGO)
    assert row.tons == pytest.approx(2.0)
    assert row.cost == pytest.approx(500_000.0)


def test_cargo_net_values_and_notes():
    net = CargoNet()

    assert net.tons == pytest.approx(5.0)
    assert net.cost == pytest.approx(1_000_000.0)
    assert net.power == pytest.approx(0.0)
    assert net.notes.infos == [
        'Tow drones extend a retrieval net',
        'Ship cannot jump while cargo net is deployed',
    ]


def test_cargo_net_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(cargo_nets=[CargoNet()]),
    )

    row = my_ship.build_spec().row('Cargo Net', section=SpecSection.CARGO)
    assert row.tons == pytest.approx(5.0)
    assert row.cost == pytest.approx(1_000_000.0)


def test_concealed_compartment_values_and_notes():
    compartment = ConcealedCompartment(tons=5)

    assert compartment.tons == pytest.approx(5.0)
    assert compartment.cost == pytest.approx(100_000.0)
    assert compartment.power == pytest.approx(0.0)
    assert compartment.sensors_dm == -2
    assert compartment.investigate_dm == -4
    assert compartment.notes.infos == [
        'Hidden space shielded against sensors',
        'DM-2 to Electronics (sensors) checks and DM-4 to Investigate checks',
    ]


def test_concealed_compartment_rejects_more_than_5_percent_of_ship_tonnage():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        cargo=CargoSection(concealed_compartments=[ConcealedCompartment(tons=5.1)]),
    )

    assert my_ship.cargo is not None
    compartment = my_ship.cargo.concealed_compartments[0]
    assert 'Concealed compartment exceeds 5% of ship tonnage: 5.1 > 5.0' in compartment.notes.errors


def test_concealed_compartment_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        cargo=CargoSection(concealed_compartments=[ConcealedCompartment(tons=5)]),
    )

    row = my_ship.build_spec().row('Concealed Compartment', section=SpecSection.CARGO)
    assert row.tons == pytest.approx(5.0)
    assert row.cost == pytest.approx(100_000.0)


def test_fuel_tank_compartment_values_and_notes():
    compartment = FuelTankCompartment(tons=5)

    assert compartment.tons == pytest.approx(5.0)
    assert compartment.cost == pytest.approx(20_000.0)
    assert compartment.power == pytest.approx(0.0)
    assert compartment.sensors_dm == -4
    assert compartment.investigate_dm == -6
    assert compartment.notes.infos == [
        'Officially counts as fuel tankage; Ceres counts it as real cargo volume (RIS-018)',
        'Can only be accessed when fuel tank is at least three-quarters empty',
        'DM-4 to Electronics (sensors) checks and DM-6 to Investigate checks',
    ]


def test_fuel_tank_compartment_appears_as_cargo_with_official_fuel_note():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(plant=FusionPlantTL12(output=60)),
        cargo=CargoSection(fuel_tank_compartments=[FuelTankCompartment(tons=10)]),
    )

    row = my_ship.build_spec().row('Fuel Tank Compartment', section=SpecSection.CARGO)
    assert row.tons == pytest.approx(10.0)
    assert row.cost == pytest.approx(40_000.0)
    assert row.notes.infos == [
        'Officially counts as fuel tankage; Ceres counts it as real cargo volume (RIS-018)',
        'Can only be accessed when fuel tank is at least three-quarters empty',
        'DM-4 to Electronics (sensors) checks and DM-6 to Investigate checks',
        'Would overstate official operation endurance by 100 weeks',
    ]


def test_external_cargo_mount_values_and_notes():
    mount = ExternalCargoMount(capacity=40)

    assert mount.tons == pytest.approx(0.0)
    assert mount.cost == pytest.approx(40_000.0)
    assert mount.power == pytest.approx(0.0)
    assert mount.performance_displacement_contribution == pytest.approx(40.0)
    assert mount.notes.infos == ['Ship is effectively unstreamlined while external cargo is mounted']


def test_external_cargo_mount_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        cargo=CargoSection(external_cargo_mounts=[ExternalCargoMount(capacity=40)]),
    )

    row = my_ship.build_spec().row('External Cargo Mount (40 tons)', section=SpecSection.CARGO)
    assert row.cost == pytest.approx(40_000.0)


def test_external_cargo_mount_rejects_streamlined_hulls():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(external_cargo_mounts=[ExternalCargoMount(capacity=40)]),
    )

    assert my_ship.cargo is not None
    mount = my_ship.cargo.external_cargo_mounts[0]
    assert 'External cargo mount cannot be installed on streamlined hulls' in mount.notes.errors


def test_external_cargo_mount_rejects_dispersed_structure_hulls():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.dispersed_structure),
        cargo=CargoSection(external_cargo_mounts=[ExternalCargoMount(capacity=40)]),
    )

    assert my_ship.cargo is not None
    mount = my_ship.cargo.external_cargo_mounts[0]
    assert 'External cargo mount cannot be installed on dispersed structure hulls' in mount.notes.errors


def test_external_cargo_mount_contributes_to_performance_displacement():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive2()),
        cargo=CargoSection(external_cargo_mounts=[ExternalCargoMount(capacity=40)]),
    )

    assert my_ship.performance_displacement == pytest.approx(440.0)
    assert my_ship.drives is not None
    assert my_ship.drives.m_drive is not None
    assert my_ship.drives.m_drive.build_item() == 'M-Drive 2 (440t)'
    assert my_ship.drives.m_drive.tons == pytest.approx(8.8)
    assert my_ship.drives.m_drive.power == pytest.approx(88.0)


@pytest.mark.parametrize(
    ('jump_net', 'expected_tl', 'expected_tons', 'expected_cost'),
    [
        (InterplanetaryJumpNet(capacity=100), 8, 1.0, 100_000.0),
        (InterplanetaryJumpNet(capacity=101), 8, 2.0, 200_000.0),
        (InterstellarJumpNet(capacity=100), 10, 1.0, 300_000.0),
        (InterstellarJumpNet(capacity=101), 10, 2.0, 600_000.0),
    ],
)
def test_jump_net_values(jump_net, expected_tl, expected_tons, expected_cost):
    assert jump_net.tl == expected_tl
    assert jump_net.tons == pytest.approx(expected_tons)
    assert jump_net.cost == pytest.approx(expected_cost)
    assert jump_net.power == pytest.approx(0.0)
    assert jump_net.performance_displacement_contribution == pytest.approx(jump_net.capacity)


def test_interplanetary_jump_net_notes():
    jump_net = InterplanetaryJumpNet(capacity=100)

    assert jump_net.notes.infos == [
        'Ship is effectively unstreamlined while jump net is deployed',
        'Cannot perform jump while interplanetary jump net is deployed',
    ]


def test_interstellar_jump_net_notes():
    jump_net = InterstellarJumpNet(capacity=100)

    assert jump_net.notes.infos == ['Ship is effectively unstreamlined while jump net is deployed']


def test_jump_net_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        cargo=CargoSection(jump_nets=[InterstellarJumpNet(capacity=150)]),
    )

    row = my_ship.build_spec().row('Interstellar Jump Net (150 tons)', section=SpecSection.CARGO)
    assert row.tons == pytest.approx(2.0)
    assert row.cost == pytest.approx(600_000.0)


def test_jump_net_contributes_to_performance_displacement():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive2()),
        cargo=CargoSection(jump_nets=[InterstellarJumpNet(capacity=40)]),
    )

    assert my_ship.performance_displacement == pytest.approx(440.0)
    assert my_ship.drives is not None
    assert my_ship.drives.m_drive is not None
    assert my_ship.drives.m_drive.build_item() == 'M-Drive 2 (440t)'
    assert my_ship.drives.m_drive.tons == pytest.approx(8.8)
    assert my_ship.drives.m_drive.power == pytest.approx(88.0)


def test_cargo_hold_display_label_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=20, display_label='Specimen Hold')]),
    )

    cargo_row = my_ship.build_spec().row('Specimen Hold (Cargo Hold)', section=SpecSection.CARGO)
    assert cargo_row.tons == pytest.approx(20.0)


def test_cargo_hold_cost_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=50, cost=500_000, display_label='Ammunition Locker')]),
    )

    cargo_row = my_ship.build_spec().row('Ammunition Locker (Cargo Hold)', section=SpecSection.CARGO)
    assert cargo_row.tons == pytest.approx(50.0)
    assert cargo_row.cost == pytest.approx(500_000.0)


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
        power=PowerSection(plant=FusionPlantTL12(output=8)),
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
        power=PowerSection(plant=FusionPlantTL12(output=8)),
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
    assert 'Ship must have a power plant to compute OperationFuel' in my_ship.fuel.operation_fuel.notes.errors


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


def test_collector_values():
    collector = Collector(parsecs=2)
    collector.bind(DummyOwner(14, 400))
    assert collector.tl == 14
    assert collector.tons == pytest.approx(13.0)
    assert collector.cost == pytest.approx(6_500_000.0)
    assert collector.power == pytest.approx(0.0)
    assert collector.build_item() == 'Collector (J-2)'


def test_collector_values_are_computed_properties_not_serialized_fields():
    collector = Collector.model_validate({'parsecs': 2, 'tons': 99, 'cost': 99, 'power': 99})
    collector.bind(DummyOwner(14, 400))
    dump = collector.model_dump()

    assert collector.tons == pytest.approx(13.0)
    assert collector.cost == pytest.approx(6_500_000.0)
    assert collector.power == pytest.approx(0.0)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_collector_appears_as_fuel_spec_row():
    my_ship = ship.Ship(
        tl=14,
        displacement=400,
        hull=hull.Hull(configuration=hull.dispersed_structure),
        fuel=FuelSection(collector=Collector(parsecs=2)),
    )
    row = my_ship.build_spec().row('Collector (J-2)', section=SpecSection.FUEL)
    assert row.tons == pytest.approx(13.0)
    assert row.cost == pytest.approx(6_500_000.0)
    assert row.notes.infos == ['Collects and stores interstellar hydrogen for jump fuel']


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


def test_spec_always_shows_residual_cargo_hold_even_with_explicit_cargo_parts():
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
        ('Cargo Hold', pytest.approx(166.0)),
    ]


def test_spec_does_not_show_zero_ton_residual_cargo_hold():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=200.0)]),
    )

    cargo_rows = my_ship.build_spec().rows_for_section(SpecSection.CARGO)
    assert [(row.item, row.tons) for row in cargo_rows] == [('Cargo Hold', pytest.approx(200.0))]
