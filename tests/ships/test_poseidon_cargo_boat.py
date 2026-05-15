from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL8, FusionPlantTL12, MDrive3, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.storage import CargoSection, FuelSection, OperationFuel
from ceres.make.ship.systems import Aerofins, Airlock, CommonArea

POSEIDON_TLS = [9, 10, 12]
POSEIDON_HULL = hull.streamlined_hull.model_copy(
    update={'light': True, 'description': 'Light Streamlined Hull'},
)

_expected = SimpleNamespace(
    tl10=10,
    tl12=12,
    bridge_operations_dm=-1,
    aerofins_atmospheric_pilot_dm=2,
    net_atmospheric_dm=1,
    tl10_plant_type=FusionPlantTL8,
    tl12_plant_type=FusionPlantTL12,
    tl10_cargo_tons=74.0,
    tl12_cargo_tons=75.6666666667,
    tl10_production_cost=14_380_000.0,
    tl12_production_cost=15_213_333.333333334,
    expected_errors=[],
    expected_warnings=[],
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
        power=PowerSection(plant=fusion_plant),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=[Stateroom()], common_area=CommonArea(tons=1.0)),
    )


@pytest.mark.parametrize('tl', [10, 12])
def test_poseidon_cargo_boat_small_bridge_is_overcompensated_in_atmosphere(tl: int):
    cargo_boat = build_poseidon_cargo_boat(tl)

    assert cargo_boat.command is not None
    assert cargo_boat.command.bridge is not None
    assert cargo_boat.hull.aerofins is not None
    assert cargo_boat.command.bridge.operations_dm == _expected.bridge_operations_dm
    assert cargo_boat.hull.aerofins.atmospheric_pilot_dm == _expected.aerofins_atmospheric_pilot_dm
    assert (
        cargo_boat.command.bridge.operations_dm + cargo_boat.hull.aerofins.atmospheric_pilot_dm
        == _expected.net_atmospheric_dm
    )
    assert cargo_boat.notes.errors == _expected.expected_errors
    assert cargo_boat.notes.warnings == _expected.expected_warnings


def test_poseidon_tl12_variant_trades_cost_for_cargo_with_better_power_plant():
    tl10 = build_poseidon_cargo_boat(_expected.tl10)
    tl12 = build_poseidon_cargo_boat(_expected.tl12)

    assert tl10.power is not None
    assert tl12.power is not None
    assert tl10.power.plant is not None
    assert tl12.power.plant is not None
    assert isinstance(tl10.power.plant, _expected.tl10_plant_type)
    assert isinstance(tl12.power.plant, _expected.tl12_plant_type)
    assert CargoSection.cargo_tons_for_ship(tl10) == pytest.approx(_expected.tl10_cargo_tons)
    assert CargoSection.cargo_tons_for_ship(tl12) == pytest.approx(_expected.tl12_cargo_tons)
    assert tl10.production_cost == pytest.approx(_expected.tl10_production_cost)
    assert tl12.production_cost == pytest.approx(_expected.tl12_production_cost)


@pytest.mark.parametrize('tl', [9])
def test_poseidon_below_tl10_puts_error_on_mdrive(tl: int):
    cargo_boat = build_poseidon_cargo_boat(tl)
    assert cargo_boat.drives is not None
    assert cargo_boat.drives.m_drive is not None
    assert f'Requires TL10, ship is TL{tl}' in cargo_boat.drives.m_drive.notes.errors
