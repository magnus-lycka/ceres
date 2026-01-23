import pytest
from pydantic import ValidationError
from ceres import armour


def test_cannot_set_cost_for_armour():
    with pytest.raises(ValidationError):
        my_armour = armour._Armour(tl=7, protection=2, displacement=100, cost=5)


def test_cannot_set_tons_for_armour():
    with pytest.raises(ValidationError):
        my_armour = armour._Armour(tl=7, protection=2, displacement=100, tons=500)


def test_cannot_set_power_for_armour():
    with pytest.raises(ValidationError):
        my_armour = armour._Armour(tl=7, protection=2, displacement=100, power=5)


def test_titanium_steel_armour_too_low_tl():
    with pytest.raises(ValidationError):
        my_armour = armour.TitaniumSteelArmour(tl=6)


def test_titanium_steel_armour():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2, displacement=100)
    assert my_armour.cost == 50000 * 2 * 100
    assert my_armour.tons == 100 * 2 * 0.025
    assert my_armour.protection == 2


def test_titanium_steel_armour_4ton():
    with pytest.raises(ValidationError):
        my_armour = armour.TitaniumSteelArmour(tl=7, protection=2, displacement=4)


