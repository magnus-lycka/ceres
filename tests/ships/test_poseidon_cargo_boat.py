import pytest

from tycho import hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection
from tycho.drives import DriveSection, FusionPlantTL8, FusionPlantTL12, MDrive, PowerSection
from tycho.habitation import HabitationSection, Stateroom
from tycho.storage import CargoSection, FuelSection, OperationFuel
from tycho.systems import Aerofins, Airlock, CommonArea


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
        drives=DriveSection(m_drive=MDrive(3)),
        power=PowerSection(fusion_plant=fusion_plant),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer(5)),
        habitation=HabitationSection(staterooms=[Stateroom()], common_area=CommonArea(tons=1.0)),
    )



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


@pytest.mark.parametrize('tl', [9])
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
        computer=ComputerSection(hardware=Computer(5)),
        habitation=HabitationSection(staterooms=[Stateroom()]),
    )
    assert ('error', 'No airlock installed') in [(note.category.value, note.message) for note in my_ship.notes]
    assert my_ship.habitation is not None
    assert ('warning', 'Recommended common area is 1.00 tons') in [
        (note.category.value, note.message) for note in my_ship.habitation.notes
    ]


def test_ship_with_staterooms_and_no_common_area_adds_warning():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=POSEIDON_HULL, airlocks=[Airlock()]),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer(5)),
        habitation=HabitationSection(staterooms=[Stateroom()]),
    )
    assert my_ship.habitation is not None
    assert ('warning', 'Recommended common area is 1.00 tons') in [
        (note.category.value, note.message) for note in my_ship.habitation.notes
    ]
