import pytest

from tycho import hull, ship
from tycho.base import ShipBase
from tycho.crafts import AirRaft, CraftSection, DockingClamp, FreeGenericCraft, FullHangar, InternalDockingSpace


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


def test_craft_section_all_parts():
    section = CraftSection(docking_space=InternalDockingSpace(craft=AirRaft()))

    assert len(section._all_parts()) == 1
    assert isinstance(section._all_parts()[0], InternalDockingSpace)


def test_empty_docking_space_renders_without_invented_craft_row():
    my_ship = ship.Ship(
        tl=12,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        craft=CraftSection(docking_space=InternalDockingSpace(craft=FreeGenericCraft(docking_space=70))),
    )
    spec = my_ship.build_spec()

    assert [row.item for row in spec.rows_for_section('Craft')] == ['Docking Space (70 tons)']


def test_docking_clamp_type_ii_values():
    clamp = DockingClamp(kind='II')
    clamp.bind(DummyOwner(12, 400))
    assert clamp.tons == 5.0
    assert clamp.cost == 1_000_000.0
    assert clamp.build_item() == 'Docking Clamp, Type II'


def test_full_hangar_with_free_generic_craft_values():
    hangar = FullHangar(craft=FreeGenericCraft(docking_space=95))
    hangar.bind(DummyOwner(12, 10_000))
    assert hangar.tons == pytest.approx(190.0)
    assert hangar.cost == pytest.approx(38_000_000.0)
    assert hangar.build_item() == 'Full Hangar (95 tons)'
