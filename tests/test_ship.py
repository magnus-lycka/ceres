from pydantic import ValidationError
import pytest

from ceres import armour, ship
from ceres.bridge import Cockpit
from ceres.drives import FusionPlantTL12, MDrive
from ceres.sensors import CivilianGradeSensors
from ceres.weapons import FixedFirmpoint, PulseLaser


def test_ship_initial():
    my_ship = ship.Ship(
        tl=15,
        displacement=300,
        hull=ship.Hull(configuration=ship.sphere),
    )
    assert my_ship.tl == 15
    assert my_ship.displacement == 300
    assert my_ship.hull.configuration.points(300) == 120
    assert my_ship.cargo == 300


def test_ship_needs_hull():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(tl=15, displacement=100))


def test_ship_needs_displacement():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(tl=15, hull=ship.Hull(configuration=ship.sphere)))


def test_ship_needs_tech_level():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(hull=ship.Hull(configuration=ship.sphere), displacement=100))


def test_ship_initial_bulky():
    my_ship = ship.Ship(
        tl=15,
        displacement=100,
        hull=ship.Hull(configuration=ship.buffered_planetoid),
    )
    assert my_ship.cargo == 65


def test_ship_with_armour():
    my_ship = ship.Ship(
        tl=12,
        hull=ship.Hull(
            configuration=ship.standard_hull,
            crystaliron_armour=armour.CrystalironArmour(protection=4, tl=12),
        ),
        displacement=100,
    )
    assert my_ship.cargo == 100 - (100 * 4 * 0.0125)


def test_ship_not_selfhealing():
    my_ship = ship.Ship(
        tl=8,
        hull=ship.Hull(configuration=ship.standard_hull),
        displacement=100,
    )
    assert not my_ship.self_sealing


def test_ship_selfhealing():
    my_ship = ship.Ship(
        tl=9,
        hull=ship.Hull(configuration=ship.standard_hull),
        displacement=100,
    )
    assert my_ship.self_sealing


def test_ship_hull_cost():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.streamlined_hull.model_copy(update={'light': True})),
    )
    assert my_ship.hull_cost == 270_000


def test_ship_design_cost_custom_has_no_multiplier():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=ship.Hull(configuration=ship.streamlined_hull.model_copy(update={'light': True})),
        civilian_sensors=CivilianGradeSensors(),
    )
    assert my_ship.design_cost == 3_270_000
    assert my_ship.discount_cost == 3_270_000


def test_ship_design_cost_standard_gets_discount():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.STANDARD,
        hull=ship.Hull(configuration=ship.streamlined_hull.model_copy(update={'light': True})),
        civilian_sensors=CivilianGradeSensors(),
    )
    assert my_ship.discount_cost == 2_943_000


def test_ship_design_cost_new_gets_markup():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.NEW,
        hull=ship.Hull(configuration=ship.streamlined_hull.model_copy(update={'light': True})),
        civilian_sensors=CivilianGradeSensors(),
    )
    assert my_ship.discount_cost == 3_302_700


def test_ship_available_power_without_plant_is_zero():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
    )
    assert my_ship.available_power == 0


def test_ship_available_power_with_plant_uses_output():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
        fusion_plant=FusionPlantTL12(output=8),
    )
    assert my_ship.available_power == 8


def test_ship_total_power_load_includes_basic_and_active_systems():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
        m_drive=MDrive(rating=6),
        cockpit=Cockpit(),
        civilian_sensors=CivilianGradeSensors(),
        fixed_firmpoints=[FixedFirmpoint(weapon=PulseLaser(very_high_yield=True, energy_efficient=True))],
    )
    assert my_ship.total_power_load == 8


def test_ship_power_margin():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
        fusion_plant=FusionPlantTL12(output=8),
        m_drive=MDrive(rating=6),
        cockpit=Cockpit(),
        civilian_sensors=CivilianGradeSensors(),
        fixed_firmpoints=[FixedFirmpoint(weapon=PulseLaser(very_high_yield=True, energy_efficient=True))],
    )
    assert my_ship.power_margin == 0
