import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.crafts import (
    CraftSection,
    DockingClamp,
    EmptyOccupant,
    FullHangar,
    InternalDockingSpace,
    SpaceCraft,
    Vehicle,
)
from ceres.make.ship.view import collapsed_main_rows


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_air_raft_cost():
    a = Vehicle.from_catalog('Air/Raft')
    assert a.kind == 'Air/Raft'
    assert a.tl == 8
    assert a.shipping_size == 4
    assert a.cost == 250_000
    assert not hasattr(a, 'engineering_tonnage')
    assert not hasattr(a, 'crew')
    assert a.requires_pilot is False


def test_internal_docking_space_for_air_raft():
    d = InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))
    d.bind(DummyOwner(12, 100))
    assert d.tons == 5.0
    assert d.cost == 1_250_000
    assert d.power == 0


def test_craft_section_all_parts():
    section = CraftSection(internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))])

    assert len(section._all_parts()) == 1
    assert isinstance(section._all_parts()[0], InternalDockingSpace)


def test_empty_docking_space_renders_without_invented_craft_row():
    my_ship = ship.Ship(
        tl=12,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=EmptyOccupant(docking_space=70))]),
    )
    spec = my_ship.build_spec()

    assert [row.item for row in spec.rows_for_section('Craft')] == ['Docking Space (70 tons)']


def test_docking_clamp_type_ii_values():
    clamp = DockingClamp(kind='II')
    clamp.bind(DummyOwner(12, 400))
    assert clamp.tons == 5.0
    assert clamp.cost == 1_000_000.0
    assert clamp.build_item() == 'Docking Clamp, Type II'


def test_docking_clamp_can_carry_spacecraft_without_changing_clamp_values():
    clamp = DockingClamp(kind='II', craft=SpaceCraft.from_catalog('Pinnace'))
    clamp.bind(DummyOwner(12, 400))
    assert clamp.tons == 5.0
    assert clamp.cost == 1_000_000.0
    assert clamp.craft is not None
    assert clamp.craft.build_item() == 'Pinnace'


def test_full_hangar_with_empty_occupant_values():
    hangar = FullHangar(craft=EmptyOccupant(docking_space=95))
    hangar.bind(DummyOwner(12, 10_000))
    assert hangar.tons == pytest.approx(190.0)
    assert hangar.cost == pytest.approx(38_000_000.0)
    assert hangar.build_item() == 'Full Hangar (95 tons)'


def test_passenger_shuttle_values():
    shuttle = SpaceCraft.from_catalog('Passenger Shuttle')
    assert shuttle.tl == 9
    assert shuttle.shipping_size == 95
    assert shuttle.cost == 14_305_000.0
    assert shuttle.engineering_tonnage == pytest.approx(3.95)
    assert shuttle.crew == 1
    assert shuttle.requires_pilot is True
    assert shuttle.build_item() == 'Passenger Shuttle'


def test_catalog_craft_metadata_for_other_examples():
    assert Vehicle.from_catalog('ATV').build_item() == 'ATV'
    assert SpaceCraft.from_catalog('Slow Pinnace').engineering_tonnage == pytest.approx(3.2)


def test_freeform_carried_spacecraft_can_be_owned_already():
    craft = SpaceCraft(
        kind='Owned Pinnace',
        tl=12,
        shipping_size=40,
        cost=0.0,
        engineering_tonnage=4.0,
        crew=1,
    )

    assert craft.build_item() == 'Owned Pinnace'
    assert craft.cost == 0.0
    assert craft.requires_pilot is True


def test_owned_spacecraft_still_drives_docking_space_tonnage():
    docking_space = InternalDockingSpace(
        craft=SpaceCraft(
            kind='Owned Pinnace',
            tl=12,
            shipping_size=40,
            cost=0.0,
            engineering_tonnage=4.0,
            crew=1,
        )
    )
    docking_space.bind(DummyOwner(12, 1_000))

    assert docking_space.tons == 44.0
    assert docking_space.cost == 11_000_000.0


def test_freeform_carried_spacecraft_roundtrips_with_metadata():
    my_ship = ship.Ship(
        tl=12,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        craft=CraftSection(
            internal_housing=[
                InternalDockingSpace(
                    craft=SpaceCraft(
                        kind='Owned Pinnace',
                        tl=12,
                        shipping_size=40,
                        cost=0.0,
                        engineering_tonnage=4.0,
                        crew=1,
                    )
                )
            ]
        ),
    )

    loaded = ship.Ship.model_validate_json(my_ship.model_dump_json())
    assert loaded.craft is not None
    assert len(loaded.craft.internal_housing) == 1
    assert loaded.craft.internal_housing[0].craft.kind == 'Owned Pinnace'
    assert loaded.craft.internal_housing[0].craft.cost == 0.0
    assert loaded.craft.internal_housing[0].craft.engineering_tonnage == pytest.approx(4.0)


def test_craft_rows_stay_next_to_their_housing_rows():
    my_ship = ship.Ship(
        tl=12,
        displacement=10_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        craft=CraftSection(
            internal_housing=[
                *[FullHangar(craft=SpaceCraft.from_catalog('Passenger Shuttle'))] * 10,
                *[FullHangar(craft=SpaceCraft.from_catalog("Ship's Boat"))] * 2,
                *[InternalDockingSpace(craft=Vehicle.from_catalog('G/Carrier'))] * 3,
            ],
        ),
    )

    items = [row.item for row in my_ship.build_spec().rows_for_section('Craft')]
    assert items[:6] == [
        'Full Hangar: Passenger Shuttle',
        'Passenger Shuttle',
        'Full Hangar: Passenger Shuttle',
        'Passenger Shuttle',
        'Full Hangar: Passenger Shuttle',
        'Passenger Shuttle',
    ]

    collapsed_items = [row.item for row in collapsed_main_rows(my_ship.build_spec()) if row.section == 'Craft']
    assert collapsed_items == [
        'Full Hangar: Passenger Shuttle',
        'Passenger Shuttle',
        "Full Hangar: Ship's Boat",
        "Ship's Boat",
        'Internal Docking Space: G/Carrier',
        'G/Carrier',
    ]

    collapsed_quantities = [row.quantity for row in collapsed_main_rows(my_ship.build_spec()) if row.section == 'Craft']
    assert collapsed_quantities == [10, 10, 2, 2, 3, 3]


def test_docking_clamp_craft_row_renders_after_clamp_row():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        craft=CraftSection(
            docking_clamps=[
                DockingClamp(kind='II', craft=SpaceCraft.from_catalog('Pinnace')),
                DockingClamp(kind='I', craft=Vehicle.from_catalog('ATV')),
            ]
        ),
    )

    items = [row.item for row in my_ship.build_spec().rows_for_section('Craft')]
    assert items == [
        'Docking Clamp, Type II',
        'Pinnace',
        'Docking Clamp, Type I',
        'ATV',
    ]
