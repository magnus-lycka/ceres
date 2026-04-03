from pydantic import ValidationError
import pytest

from ceres import armour
from ceres.base import ShipBase


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement, armour_volume_modifier=1.0):
        super().__init__(tl=tl, displacement=displacement)
        self._armour_volume_modifier = armour_volume_modifier

    @property
    def armour_volume_modifier(self) -> float:
        return self._armour_volume_modifier


def test_cannot_set_cost_for_armour():
    with pytest.raises(ValidationError):
        armour.TitaniumSteelArmour.model_validate({'tl': 7, 'protection': 2, 'cost': 5})


def test_cannot_set_tons_for_armour():
    with pytest.raises(ValidationError):
        armour.TitaniumSteelArmour.model_validate({'tl': 7, 'protection': 2, 'tons': 500})


def test_titanium_steel_armour_too_low_tl():
    with pytest.raises(ValueError):
        a = armour.TitaniumSteelArmour(tl=6, protection=2)
        a.bind(DummyOwner(7, 99))


def test_titanium_steel_armour():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2)
    my_armour.bind(DummyOwner(7, 100))
    assert my_armour.tons == 100 * 2 * 0.025
    assert my_armour.cost == 50_000 * my_armour.tons
    assert my_armour.protection == 2


def test_titanium_steel_armour_4ton():
    with pytest.raises(ValueError):
        armour4 = armour.TitaniumSteelArmour(tl=7, protection=2)
        armour4.bind(DummyOwner(7, 4))
        armour4.calculate_tons()


def test_titanium_steel_armour_5_15ton():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2)
    my_armour.bind(DummyOwner(7, 5))
    assert my_armour.tons == 5 * 2 * 0.025 * 4
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2)
    my_armour.bind(DummyOwner(7, 15))
    assert my_armour.tons == 15 * 2 * 0.025 * 4


def test_titanium_steel_armour_16_25ton():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2)
    my_armour.bind(DummyOwner(7, 16))
    assert my_armour.tons == 16 * 2 * 0.025 * 3
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2)
    my_armour.bind(DummyOwner(7, 25))
    assert my_armour.tons == 25 * 2 * 0.025 * 3


def test_titanium_steel_armour_26_99ton():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2)
    my_armour.bind(DummyOwner(7, 26))
    assert my_armour.tons == 26 * 2 * 0.025 * 2
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2)
    my_armour.bind(DummyOwner(7, 99))
    assert my_armour.tons == 99 * 2 * 0.025 * 2


def test_max_protection_titanium_steel_tl7():
    armour.TitaniumSteelArmour(tl=7, protection=7)
    with pytest.raises(ValueError):
        a = armour.TitaniumSteelArmour(tl=7, protection=8)
        a.bind(DummyOwner(99, 999))


def test_max_protection_titanium_steel_tl8():
    armour.TitaniumSteelArmour(tl=8, protection=8)
    with pytest.raises(ValueError):
        a = armour.TitaniumSteelArmour(tl=8, protection=9)
        a.bind(DummyOwner(99, 999))


def test_max_protection_titanium_steel_tl15():
    armour.TitaniumSteelArmour(tl=15, protection=9)
    with pytest.raises(ValueError):
        a = armour.TitaniumSteelArmour(tl=15, protection=10)
        a.bind(DummyOwner(99, 999))


def test_crystaliron_armour_too_low_tl():
    with pytest.raises(ValueError):
        a = armour.CrystalironArmour(tl=9, protection=2)
        a.bind(DummyOwner(15, 555))


def test_crystaliron_armour():
    my_armour = armour.CrystalironArmour(tl=10, protection=2)
    my_armour.bind(DummyOwner(10, 100))
    assert my_armour.tons == 100 * 2 * 0.0125
    assert my_armour.cost == 200_000 * my_armour.tons
    assert my_armour.protection == 2


def test_max_protection_crystaliron_armour():
    for tl in range(10, 16):
        max_prot = min(tl, 13)
        armour.CrystalironArmour(tl=tl, protection=max_prot)
        with pytest.raises(ValueError):
            a = armour.CrystalironArmour(tl=tl, protection=max_prot + 1)
            a.bind(DummyOwner(tl, 999))


def test_bonded_superdense_armour_too_low_tl():
    with pytest.raises(ValueError):
        a = armour.BondedSuperdenseArmour(tl=13, protection=2)
        a.bind(DummyOwner(13, 999))


def test_bonded_superdense_armour():
    my_armour = armour.BondedSuperdenseArmour(tl=14, protection=2)
    my_armour.bind(DummyOwner(14, 100))
    assert my_armour.tons == 100 * 2 * 0.008
    assert my_armour.cost == 500_000 * my_armour.tons
    assert my_armour.protection == 2


def test_max_protection_bonded_superdense_armour():
    for tl in range(14, 16):
        max_prot = tl
        armour.BondedSuperdenseArmour(tl=tl, protection=max_prot)
        with pytest.raises(ValueError):
            a = armour.BondedSuperdenseArmour(tl=tl, protection=max_prot + 1)
            a.bind(DummyOwner(tl, 999))


def test_molecular_bonded_armour_too_low_tl():
    with pytest.raises(ValueError):
        a1 = armour.MolecularBondedArmour(tl=15, protection=2)
        a1.bind(DummyOwner(15, 999))


def test_molecular_bonded_armour():
    my_armour = armour.MolecularBondedArmour(tl=16, protection=2)
    my_armour.bind(DummyOwner(16, 100))
    assert my_armour.tons == 100 * 2 * 0.005
    assert my_armour.cost == 1_500_000 * my_armour.tons
    assert my_armour.protection == 2


def test_max_protection_molecular_bonded_armour():
    for tl in range(16, 20):
        max_prot = tl + 4
        armour.MolecularBondedArmour(tl=tl, protection=max_prot)
        with pytest.raises(ValueError):
            a = armour.MolecularBondedArmour(tl=tl, protection=max_prot + 1)
            a.bind(DummyOwner(tl, 999))
