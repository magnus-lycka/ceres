"""Unit tests for weapons/section.py — WeaponsSection mount validation."""

from ceres.make.ship.base import ShipBase
from ceres.make.ship.weapons.bays import SmallMissileBay
from ceres.make.ship.weapons.mounts import SingleTurret, TripleTurret
from ceres.make.ship.weapons.point_defense import LaserPointDefenseBattery2
from ceres.make.ship.weapons.section import WeaponsSection


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


class TestWeaponsSection:
    def test_empty_section_has_no_turrets(self):
        section = WeaponsSection()
        assert section.turrets == []

    def test_section_holds_mixed_mount_types(self):
        section = WeaponsSection(turrets=[SingleTurret(), TripleTurret()])
        assert len(section.turrets) == 2

    def test_small_craft_pd_battery_generates_error(self):
        ship = _Ship(displacement=99)
        battery = LaserPointDefenseBattery2()
        section = WeaponsSection(point_defense_batteries=[battery])
        section.validate_mounting(ship)
        assert 'Point defense batteries cannot be mounted on small craft firmpoints' in battery.notes.errors

    def test_large_ship_pd_battery_has_no_error(self):
        ship = _Ship(displacement=400)
        battery = LaserPointDefenseBattery2()
        section = WeaponsSection(point_defense_batteries=[battery])
        section.validate_mounting(ship)
        assert 'Point defense batteries cannot be mounted on small craft firmpoints' not in battery.notes.errors

    def test_small_craft_bay_generates_error(self):
        ship = _Ship(displacement=99)
        bay = SmallMissileBay()
        section = WeaponsSection(bays=[bay])
        section.validate_mounting(ship)
        assert 'Bays cannot be mounted on small craft firmpoints' in bay.notes.errors
