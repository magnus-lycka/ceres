from ceres import armour
from ceres.base import NoteCategory, ShipBase


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement, armour_volume_modifier=1.0):
        super().__init__(tl=tl, displacement=displacement)
        self._armour_volume_modifier = armour_volume_modifier

    @property
    def armour_volume_modifier(self) -> float:
        return self._armour_volume_modifier


def error_messages(part) -> list[str]:
    return [note.message for note in part.notes if note.category is NoteCategory.ERROR]


def test_armour_recomputes_cost_from_input():
    my_armour = armour.TitaniumSteelArmour.model_validate({'tl': 7, 'protection': 2, 'cost': 5})
    my_armour.bind(DummyOwner(7, 100))
    assert my_armour.cost == 50_000 * my_armour.tons


def test_armour_recomputes_tons_from_input():
    my_armour = armour.TitaniumSteelArmour.model_validate({'tl': 7, 'protection': 2, 'tons': 500})
    my_armour.bind(DummyOwner(7, 100))
    assert my_armour.tons == 100 * 2 * 0.025


def test_titanium_steel_armour_too_low_tl_adds_error_note():
    a = armour.TitaniumSteelArmour(tl=6, protection=2)
    a.bind(DummyOwner(7, 99))
    assert any('TL' in msg for msg in error_messages(a))


def test_titanium_steel_armour():
    my_armour = armour.TitaniumSteelArmour(tl=7, protection=2)
    my_armour.bind(DummyOwner(7, 100))
    assert my_armour.description == 'Titanium Steel'
    assert my_armour.tons == 100 * 2 * 0.025
    assert my_armour.cost == 50_000 * my_armour.tons
    assert my_armour.protection == 2


def test_titanium_steel_armour_4ton():
    armour4 = armour.TitaniumSteelArmour(tl=7, protection=2)
    armour4.bind(DummyOwner(7, 4))
    assert armour4.tons == 0.0
    assert 'Displacement must be at least 5 tons for armour.' in error_messages(armour4)


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
    a_ok = armour.TitaniumSteelArmour(tl=7, protection=7)
    a_ok.bind(DummyOwner(99, 999))
    assert not error_messages(a_ok)

    a_bad = armour.TitaniumSteelArmour(tl=7, protection=8)
    a_bad.bind(DummyOwner(99, 999))
    assert error_messages(a_bad)


def test_max_protection_titanium_steel_tl8():
    a_ok = armour.TitaniumSteelArmour(tl=8, protection=8)
    a_ok.bind(DummyOwner(99, 999))
    assert not error_messages(a_ok)

    a_bad = armour.TitaniumSteelArmour(tl=8, protection=9)
    a_bad.bind(DummyOwner(99, 999))
    assert error_messages(a_bad)


def test_max_protection_titanium_steel_tl15():
    a_ok = armour.TitaniumSteelArmour(tl=15, protection=9)
    a_ok.bind(DummyOwner(99, 999))
    assert not error_messages(a_ok)

    a_bad = armour.TitaniumSteelArmour(tl=15, protection=10)
    a_bad.bind(DummyOwner(99, 999))
    assert error_messages(a_bad)


def test_crystaliron_armour_too_low_tl_adds_error_note():
    a = armour.CrystalironArmour(tl=9, protection=2)
    a.bind(DummyOwner(15, 555))
    assert any('TL' in msg for msg in error_messages(a))


def test_crystaliron_armour():
    my_armour = armour.CrystalironArmour(tl=10, protection=2)
    my_armour.bind(DummyOwner(10, 100))
    assert my_armour.description == 'Crystaliron'
    assert my_armour.tons == 100 * 2 * 0.0125
    assert my_armour.cost == 200_000 * my_armour.tons
    assert my_armour.protection == 2


def test_max_protection_crystaliron_armour():
    for tl in range(10, 16):
        max_prot = min(tl, 13)

        a_ok = armour.CrystalironArmour(tl=tl, protection=max_prot)
        a_ok.bind(DummyOwner(tl, 999))
        assert not error_messages(a_ok)

        a_bad = armour.CrystalironArmour(tl=tl, protection=max_prot + 1)
        a_bad.bind(DummyOwner(tl, 999))
        assert error_messages(a_bad)


def test_bonded_superdense_armour_too_low_tl_adds_error_note():
    a = armour.BondedSuperdenseArmour(tl=13, protection=2)
    a.bind(DummyOwner(13, 999))
    assert any('TL' in msg for msg in error_messages(a))


def test_bonded_superdense_armour():
    my_armour = armour.BondedSuperdenseArmour(tl=14, protection=2)
    my_armour.bind(DummyOwner(14, 100))
    assert my_armour.description == 'Bonded Superdense'
    assert my_armour.tons == 100 * 2 * 0.008
    assert my_armour.cost == 500_000 * my_armour.tons
    assert my_armour.protection == 2


def test_max_protection_bonded_superdense_armour():
    for tl in range(14, 16):
        max_prot = tl

        a_ok = armour.BondedSuperdenseArmour(tl=tl, protection=max_prot)
        a_ok.bind(DummyOwner(tl, 999))
        assert not error_messages(a_ok)

        a_bad = armour.BondedSuperdenseArmour(tl=tl, protection=max_prot + 1)
        a_bad.bind(DummyOwner(tl, 999))
        assert error_messages(a_bad)


def test_molecular_bonded_armour_too_low_tl_adds_error_note():
    a = armour.MolecularBondedArmour(tl=15, protection=2)
    a.bind(DummyOwner(15, 999))
    assert any('TL' in msg for msg in error_messages(a))


def test_molecular_bonded_armour():
    my_armour = armour.MolecularBondedArmour(tl=16, protection=2)
    my_armour.bind(DummyOwner(16, 100))
    assert my_armour.description == 'Molecular Bonded'
    assert my_armour.tons == 100 * 2 * 0.005
    assert my_armour.cost == 1_500_000 * my_armour.tons
    assert my_armour.protection == 2


def test_max_protection_molecular_bonded_armour():
    for tl in range(16, 20):
        max_prot = tl + 4

        a_ok = armour.MolecularBondedArmour(tl=tl, protection=max_prot)
        a_ok.bind(DummyOwner(tl, 999))
        assert not error_messages(a_ok)

        a_bad = armour.MolecularBondedArmour(tl=tl, protection=max_prot + 1)
        a_bad.bind(DummyOwner(tl, 999))
        assert error_messages(a_bad)
