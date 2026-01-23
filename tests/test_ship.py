import pytest
from pydantic import ValidationError
from ceres import ship


def test_ship_initial():
    my_ship = ship.Ship(tl=15, displacement=300, hull_configuration=ship.sphere)
    assert my_ship.tl == 15
    assert my_ship.displacement == 300
    assert my_ship.hull == 120
    assert my_ship.cargo == 300


def test_ship_needs_hull():
    with pytest.raises(ValidationError):
        my_ship = ship.Ship(tl=15, displacement=100)


def test_ship_needs_displacement():
    with pytest.raises(ValidationError):
        my_ship = ship.Ship(tl=15, hull_configuration=ship.sphere)


def test_ship_needs_tech_level():
    with pytest.raises(ValidationError):
        my_ship = ship.Ship(hull_configuration=ship.sphere, displacement=100)


def test_ship_initial_bulky():
    my_ship = ship.Ship(tl=15, displacement=100, hull_configuration=ship.buffered_planetoid)
    assert my_ship.cargo == 65
