"""Unit tests for weapons/spinal.py — spinal mount TL validation and ammunition helpers."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.weapons.spinal import (
    MassDriverSpinalMount,
    MesonSpinalMount,
    RailgunSpinalMount,
)


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=200_000):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=200_000):
    part.bind(_Ship(tl, displacement))
    return part


class TestSpinalMountTlValidation:
    def test_tl_improvement_requires_matching_ship_tl(self):
        mount = MesonSpinalMount(tl_improvement=3)
        _bind(mount, tl=14)
        assert 'Requires TL15, ship is TL14' in mount.notes.errors

    def test_tl_improvement_3_at_correct_tl_has_no_error(self):
        mount = MesonSpinalMount(tl_improvement=3)
        _bind(mount, tl=15)
        assert 'Requires TL15' not in '\n'.join(mount.notes.errors)


class TestSpinalMountItem:
    def test_tl_improvement_appears_in_build_item(self):
        mount = MesonSpinalMount(tl_improvement=3, size_multiple=2)
        _bind(mount, tl=15)
        assert mount.build_item() == 'Meson Spinal Mount (TL15)'

    def test_size_multiple_does_not_appear_in_build_item(self):
        mount = MesonSpinalMount(size_multiple=2)
        _bind(mount, tl=12)
        item = mount.build_item()
        assert item is not None
        assert 'size' not in item.lower()
        assert '2' not in item


class TestSpinalMountAmmunition:
    def test_mass_driver_ammo_cargo_requires_positive_attacks(self):
        with pytest.raises(ValueError, match='at least one attack'):
            MassDriverSpinalMount.ammunition_cargo(attacks=0)

    def test_mass_driver_ammo_cargo_tonnage(self):
        cargo = MassDriverSpinalMount.ammunition_cargo(attacks=3)
        assert cargo.tons == pytest.approx(150.0)

    def test_railgun_extra_rounds_requires_positive_rounds(self):
        with pytest.raises(ValueError, match='at least one extra round'):
            RailgunSpinalMount.extra_rounds_cargo(rounds=0)

    def test_railgun_extra_rounds_tonnage(self):
        cargo = RailgunSpinalMount.extra_rounds_cargo(rounds=6)
        assert cargo.tons == pytest.approx(120.0)
