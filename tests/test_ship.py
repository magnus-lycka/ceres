import pytest
from pydantic import ValidationError

from ceres import armour, ship


def test_ship_initial():
    my_ship = ship.Ship(
        tl=15, displacement=300, hull=ship.Hull(configuration=ship.sphere)
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
        ship.Ship.model_validate(dict(tl=15, hull_configuration=ship.sphere))


def test_ship_needs_tech_level():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(hull_configuration=ship.sphere, displacement=100))


def test_ship_initial_bulky():
    my_ship = ship.Ship(
        tl=15, displacement=100, hull=ship.Hull(configuration=ship.buffered_planetoid)
    )
    assert my_ship.cargo == 65


def test_ship_with_armour():
    my_ship = ship.Ship(
        tl=12,
        hull=ship.Hull(
            configuration=ship.standard_hull,
            armour=armour.CrystalironArmour(protection=4, tl=12),
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


# def test_ship_heat_shielding():
#     tons =  555
#     my_ship = ship.Ship(
#         tl=9,
#         hull_configuration=ship.standard_hull,
#         displacement=tons,
#     )
#     base_cost = my_ship.cost()
#     my_ship.
