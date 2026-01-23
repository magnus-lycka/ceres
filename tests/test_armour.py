import pytest
from pydantic import ValidationError

from ceres import armour


def test_cannot_set_cost_for_armour():
    with pytest.raises(ValidationError):
        armour.Armour(tl=7, protection=2, displacement=100, cost=5)


def test_cannot_set_tons_for_armour():
    with pytest.raises(ValidationError):
        armour.Armour(tl=7, protection=2, displacement=100, tons=500)


def test_cannot_set_power_for_armour():
    with pytest.raises(ValidationError):
        armour.Armour(tl=7, protection=2, displacement=100, power=5)


def test_titanium_steel_armour_too_low_tl():
    with pytest.raises(ValidationError):
        armour.TitaniumSteelArmour(tl=6, protection=2, displacement=100)


def test_titanium_steel_armour():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2, displacement=100)
    assert my_armour.cost == 50000 * 2 * 100
    assert my_armour.tons == 100 * 2 * 0.025
    assert my_armour.protection == 2


def test_titanium_steel_armour_4ton():
    with pytest.raises(ValidationError):
        armour.TitaniumSteelArmour(tl=7, protection=2, displacement=4)


def test_titanium_steel_armour_5_15ton():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2, displacement=5)
    assert my_armour.tons == 5 * 2 * 0.025 * 4
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2, displacement=15)
    assert my_armour.tons == 15 * 2 * 0.025 * 4


def test_titanium_steel_armour_16_25ton():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2, displacement=16)
    assert my_armour.tons == 16 * 2 * 0.025 * 3
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2, displacement=25)
    assert my_armour.tons == 25 * 2 * 0.025 * 3


def test_titanium_steel_armour_26_99ton():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2, displacement=26)
    assert my_armour.tons == 26 * 2 * 0.025 * 2
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2, displacement=99)
    assert my_armour.tons == 99 * 2 * 0.025 * 2


def test_max_protection_titanium_steel_tl7():
    armour.TitaniumSteelArmour(tl=7, protection=7, displacement=100)
    with pytest.raises(ValidationError):
        armour.TitaniumSteelArmour(tl=7, protection=8, displacement=100)


def test_max_protection_titanium_steel_tl8():
    armour.TitaniumSteelArmour(tl=8, protection=8, displacement=100)
    with pytest.raises(ValidationError):
        armour.TitaniumSteelArmour(tl=8, protection=9, displacement=100)


def test_max_protection_titanium_steel_tl15():
    armour.TitaniumSteelArmour(tl=15, protection=9, displacement=100)
    with pytest.raises(ValidationError):
        armour.TitaniumSteelArmour(tl=15, protection=10, displacement=100)


def test_crystaliron_armour_too_low_tl():
    with pytest.raises(ValidationError):
        armour.CrystalironArmour(tl=9, protection=2, displacement=100)


def test_crystaliron_armour():
    my_armour = armour.CrystalironArmour(tl=10, protection=2, displacement=100)
    assert my_armour.cost == 200_000 * 2 * 100
    assert my_armour.tons == 100 * 2 * 0.0125
    assert my_armour.protection == 2


def test_max_protection_crystaliron_armour():
    for tl in range(10, 16):
        max_prot = min(tl, 13)
        armour.CrystalironArmour(tl=tl, protection=max_prot, displacement=100)
        with pytest.raises(ValidationError):
            armour.CrystalironArmour(tl=tl, protection=max_prot + 1, displacement=100)


def test_bonded_superdense_armour_too_low_tl():
    with pytest.raises(ValidationError):
        armour.BondedSuperdenseArmour(tl=13, protection=2, displacement=100)


def test_bonded_superdense_armour():
    my_armour = armour.BondedSuperdenseArmour(tl=14, protection=2, displacement=100)
    assert my_armour.cost == 500_000 * 2 * 100
    assert my_armour.tons == 100 * 2 * 0.008
    assert my_armour.protection == 2


def test_max_protection_bonded_superdense_armour():
    for tl in range(14, 16):
        max_prot = tl
        armour.BondedSuperdenseArmour(tl=tl, protection=max_prot, displacement=100)
        with pytest.raises(ValidationError):
            armour.BondedSuperdenseArmour(
                tl=tl, protection=max_prot + 1, displacement=100
            )


def test_molecular_bonded_armour_too_low_tl():
    with pytest.raises(ValidationError):
        armour.MolecularBondedArmour(tl=15, protection=2, displacement=100)


def test_molecular_bonded_armour():
    my_armour = armour.MolecularBondedArmour(tl=16, protection=2, displacement=100)
    assert my_armour.cost == 1_500_000 * 2 * 100
    assert my_armour.tons == 100 * 2 * 0.005
    assert my_armour.protection == 2


def test_max_protection_molecular_bonded_armour():
    for tl in range(16, 20):
        max_prot = tl
        armour.MolecularBondedArmour(tl=tl, protection=max_prot, displacement=100)
        with pytest.raises(ValidationError):
            armour.MolecularBondedArmour(
                tl=tl, protection=max_prot + 1, displacement=100
            )
