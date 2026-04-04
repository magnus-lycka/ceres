import pytest

from ceres import ship
from ceres.bridge import Bridge
from ceres.computer import Computer5
from ceres.drives import FusionPlantTL8, FusionPlantTL12, MDrive3, OperationFuel
from ceres.habitation import Staterooms
from ceres.systems import Aerofins, Airlock

from ._markdown_output import write_markdown_output


def build_poseidon_cargo_boat(tl: int, displacement: int = 99) -> ship.Ship:
    fusion_plant = FusionPlantTL8(output=50) if tl < 12 else FusionPlantTL12(output=50)
    return ship.Ship(
        ship_class='Poseidon',
        ship_type='Cargo Boat',
        tl=tl,
        displacement=displacement,
        design_type=ship.ShipDesignType.STANDARD,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        m_drive=MDrive3(),
        fusion_plant=fusion_plant,
        operation_fuel=OperationFuel(weeks=16),
        bridge=Bridge(small=True),
        computer=Computer5(),
        staterooms=Staterooms(count=1),
        airlocks=[Airlock()],
        aerofins=Aerofins(),
    )


@pytest.mark.parametrize(
    ('tl', 'displacement'),
    [(tl, displacement) for tl in [10, 11, 12, 13, 14, 15] for displacement in [99, 100]],
)
def test_poseidon_cargo_boat_generates_markdown_for_visual_comparison(tl: int, displacement: int):
    cargo_boat = build_poseidon_cargo_boat(tl, displacement)
    table = cargo_boat.markdown_table()
    write_markdown_output(f'test_poseidon_{displacement}t_tl{tl}', table)

    expected_hull = 39 if displacement == 99 else 40
    assert f'## *Poseidon* Cargo Boat | TL{tl} | Hull {expected_hull}' in table
    expected_bridge_tons = '3.00' if displacement == 99 else '6.00'
    assert f'| Bridge | Smaller Bridge | {expected_bridge_tons} |  | 250.00 |' in table
    assert '|  | • DM -1 to Pilot checks |  |  |  |' in table
    if displacement == 99:
        assert '|  | Airlock | 2.00 |  | 200.00 |' in table
        assert '| Systems | Aerofins | 4.95 |  | 495.00 |' in table
    else:
        assert '|  | Airlock | 0.00 |  | 0.00 |' in table
        assert '| Systems | Aerofins | 5.00 |  | 500.00 |' in table
    assert '|  | • DM +2 to Pilot checks in atmosphere |  |  |  |' in table


@pytest.mark.parametrize('tl', [10, 11, 12, 13, 14, 15])
def test_poseidon_cargo_boat_small_bridge_is_overcompensated_in_atmosphere(tl: int):
    cargo_boat = build_poseidon_cargo_boat(tl)

    assert cargo_boat.bridge is not None
    assert cargo_boat.aerofins is not None
    assert cargo_boat.bridge.operations_dm == -1
    assert cargo_boat.aerofins.atmospheric_pilot_dm == 2
    assert cargo_boat.bridge.operations_dm + cargo_boat.aerofins.atmospheric_pilot_dm == 1


def test_poseidon_tl12_variant_trades_cost_for_cargo_with_better_power_plant():
    tl10 = build_poseidon_cargo_boat(10)
    tl12 = build_poseidon_cargo_boat(12)

    assert tl10.fusion_plant is not None
    assert tl12.fusion_plant is not None
    assert isinstance(tl10.fusion_plant, FusionPlantTL8)
    assert isinstance(tl12.fusion_plant, FusionPlantTL12)
    assert tl12.cargo > tl10.cargo
    assert tl12.production_cost > tl10.production_cost


def test_poseidon_100_tons_gets_free_airlock_but_99_tons_still_has_more_cargo():
    poseidon_99 = build_poseidon_cargo_boat(12, 99)
    poseidon_100 = build_poseidon_cargo_boat(12, 100)

    assert poseidon_99.airlocks[0].tons == 2.0
    assert poseidon_99.airlocks[0].cost == 200_000.0
    assert poseidon_100.airlocks[0].tons == 0.0
    assert poseidon_100.airlocks[0].cost == 0.0
    assert poseidon_99.cargo > poseidon_100.cargo


def test_ship_with_bridge_and_no_airlock_adds_error():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        bridge=Bridge(small=True),
        computer=Computer5(),
        staterooms=Staterooms(count=1),
    )
    assert [(note.category.value, note.message) for note in my_ship.notes] == [
        ('error', 'No airlock installed'),
    ]


def test_markdown_table_renders_inline_error_on_missing_airlock():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        ship_class='Poseidon',
        ship_type='Cargo Boat',
        hull=ship.Hull(configuration=ship.streamlined_hull),
        bridge=Bridge(small=True),
        computer=Computer5(),
        staterooms=Staterooms(count=1),
    )
    table = my_ship.markdown_table()
    write_markdown_output('test_poseidon_missing_airlock', table)
    assert '|  | **ERROR:** No airlock installed |  |  |  |' in table
