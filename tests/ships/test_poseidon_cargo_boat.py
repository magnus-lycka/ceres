import pytest

from ceres import hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import Computer5, ComputerSection
from ceres.drives import DriveSection, FusionPlantTL8, FusionPlantTL12, MDrive3, PowerSection
from ceres.habitation import HabitationSection, Staterooms
from ceres.storage import CargoSection, FuelSection, OperationFuel
from ceres.systems import Aerofins, Airlock, CommonArea

from ._markdown_output import write_markdown_output

POSEIDON_TLS = [9, 10, 12]
POSEIDON_HULL = hull.streamlined_hull.model_copy(
    update={'light': True, 'description': 'Light Streamlined Hull'},
)


def build_poseidon_cargo_boat(tl: int) -> ship.Ship:
    fusion_plant = FusionPlantTL8(output=50) if tl < 12 else FusionPlantTL12(output=50)
    return ship.Ship(
        ship_class='Poseidon',
        ship_type='Cargo Boat',
        tl=tl,
        displacement=100,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(configuration=POSEIDON_HULL, airlocks=[Airlock()], aerofins=Aerofins()),
        drives=DriveSection(m_drive=MDrive3()),
        power=PowerSection(fusion_plant=fusion_plant),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=Staterooms(count=1), common_area=CommonArea(tons=1.0)),
    )


@pytest.mark.parametrize('tl', POSEIDON_TLS)
def test_poseidon_cargo_boat_generates_markdown_for_visual_comparison(tl: int):
    cargo_boat = build_poseidon_cargo_boat(tl)
    table = cargo_boat.markdown_table()
    write_markdown_output(f'test_poseidon_100t_tl{tl}', table)

    assert f'## *Poseidon* Cargo Boat | TL{tl} | Hull 36' in table
    assert '| Hull | Light Streamlined Hull | **100.00** |  | 4500.00 |' in table
    assert '|  | Basic Ship Systems |  | 20.00 |  |' in table
    assert '| Command | Smaller Bridge | 6.00 |  | 250.00 |' in table
    assert '|  | • DM -1 to Pilot checks |  |  |  |' in table
    assert '| Sensors | Basic |  |  |  |' in table
    assert '|  | • Radar, Lidar; DM -4 |  |  |  |' in table
    assert 'Common Area | 1.00 |  | 100.00 |' in table
    assert '|  | Airlock |  |  |  |' in table
    assert 'Aerofins | 5.00 |  | 500.00 |' in table
    assert '|  | • DM +2 to Pilot checks in atmosphere |  |  |  |' in table
    if tl < 10:
        assert f'|  | **ERROR:** Requires TL10, ship is TL{tl} |  |  |  |' in table


@pytest.mark.parametrize('tl', [10, 12])
def test_poseidon_cargo_boat_small_bridge_is_overcompensated_in_atmosphere(tl: int):
    cargo_boat = build_poseidon_cargo_boat(tl)

    assert cargo_boat.command is not None
    assert cargo_boat.command.bridge is not None
    assert cargo_boat.hull.aerofins is not None
    assert cargo_boat.command.bridge.operations_dm == -1
    assert cargo_boat.hull.aerofins.atmospheric_pilot_dm == 2
    assert cargo_boat.command.bridge.operations_dm + cargo_boat.hull.aerofins.atmospheric_pilot_dm == 1


def test_poseidon_tl12_variant_trades_cost_for_cargo_with_better_power_plant():
    tl10 = build_poseidon_cargo_boat(10)
    tl12 = build_poseidon_cargo_boat(12)

    assert tl10.power is not None
    assert tl12.power is not None
    assert tl10.power.fusion_plant is not None
    assert tl12.power.fusion_plant is not None
    assert isinstance(tl10.power.fusion_plant, FusionPlantTL8)
    assert isinstance(tl12.power.fusion_plant, FusionPlantTL12)
    assert CargoSection.cargo_tons_for_ship(tl12) > CargoSection.cargo_tons_for_ship(tl10)
    assert tl12.production_cost > tl10.production_cost


@pytest.mark.parametrize('tl', [8, 9])
def test_poseidon_below_tl10_puts_error_on_mdrive(tl: int):
    cargo_boat = build_poseidon_cargo_boat(tl)
    assert cargo_boat.drives is not None
    assert cargo_boat.drives.m_drive is not None
    assert ('error', f'Requires TL10, ship is TL{tl}') in [
        (note.category.value, note.message) for note in cargo_boat.drives.m_drive.notes
    ]


def test_poseidon_100_tons_gets_free_airlock():
    poseidon_100 = build_poseidon_cargo_boat(12)
    assert poseidon_100.hull.airlocks[0].tons == 0.0
    assert poseidon_100.hull.airlocks[0].cost == 0.0


def test_ship_with_bridge_and_no_airlock_adds_error():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=POSEIDON_HULL),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=Staterooms(count=1)),
    )
    assert ('error', 'No airlock installed') in [(note.category.value, note.message) for note in my_ship.notes]
    assert my_ship.habitation is not None
    assert ('warning', 'Recommended common area is 1.00 tons') in [
        (note.category.value, note.message) for note in my_ship.habitation.notes
    ]


def test_markdown_table_renders_inline_error_on_missing_airlock():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        ship_class='Poseidon',
        ship_type='Cargo Boat',
        hull=hull.Hull(configuration=POSEIDON_HULL),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=Staterooms(count=1)),
    )
    table = my_ship.markdown_table()
    write_markdown_output('test_poseidon_missing_airlock', table)
    assert '|  | **ERROR:** No airlock installed |  |  |  |' in table


def test_ship_with_staterooms_and_no_common_area_adds_warning():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=POSEIDON_HULL, airlocks=[Airlock()]),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=Staterooms(count=1)),
    )
    assert my_ship.habitation is not None
    assert ('warning', 'Recommended common area is 1.00 tons') in [
        (note.category.value, note.message) for note in my_ship.habitation.notes
    ]


def test_markdown_table_renders_inline_warning_on_missing_common_area():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        ship_class='Poseidon',
        ship_type='Cargo Boat',
        hull=hull.Hull(configuration=POSEIDON_HULL, airlocks=[Airlock()]),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=Staterooms(count=1)),
    )
    table = my_ship.markdown_table()
    write_markdown_output('test_poseidon_missing_common_area', table)
    assert '|  | *WARNING:* Recommended common area is 1.00 tons |  |  |  |' in table
