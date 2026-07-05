"""Unit tests for weapons/section.py — WeaponsSection mount validation."""

from ceres.make.ship.base import ShipBase
from ceres.make.ship.spec import ShipSpec, SpecRow, SpecSection
from ceres.make.ship.weapons.barbettes import BeamLaserBarbette
from ceres.make.ship.weapons.bays import PlasmaCarronade, SmallMissileBay
from ceres.make.ship.weapons.common import BeamLaser
from ceres.make.ship.weapons.magazines import MissileStorage, SandcasterCanisterStorage, TorpedoStorage
from ceres.make.ship.weapons.mounts import FixedMount, SingleTurret, TripleTurret
from ceres.make.ship.weapons.point_defense import LaserPointDefenseBattery2
from ceres.make.ship.weapons.section import WeaponsSection
from ceres.make.ship.weapons.spinal import MassDriverSpinalMount


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


class _SpecShip:
    def _grouped_spec_rows(self, section, parts):
        return [SpecRow(section=section, item=f'group:{type(part).__name__}') for part in parts]

    def _spec_row_for_part(self, section, part):
        return SpecRow(section=section, item=f'part:{type(part).__name__}')


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

    def test_is_small_craft_uses_100_ton_boundary(self):
        assert WeaponsSection.is_small_craft(_Ship(displacement=99))
        assert not WeaponsSection.is_small_craft(_Ship(displacement=100))

    def test_mount_capacity_uses_small_craft_and_ship_boundaries(self):
        assert WeaponsSection.mount_capacity(_Ship(displacement=34)) == 1
        assert WeaponsSection.mount_capacity(_Ship(displacement=35)) == 2
        assert WeaponsSection.mount_capacity(_Ship(displacement=70)) == 2
        assert WeaponsSection.mount_capacity(_Ship(displacement=71)) == 3
        assert WeaponsSection.mount_capacity(_Ship(displacement=400)) == 4

    def test_excess_small_craft_mounts_report_firmpoint_overflow_on_last_parts(self):
        ship = _Ship(displacement=34)
        first_turret = SingleTurret()
        second_turret = SingleTurret()
        section = WeaponsSection(turrets=[first_turret, second_turret])

        section.validate_mounting(ship)

        message = 'Exceeds available firmpoints: 2 mounts installed, capacity is 1'
        assert message not in first_turret.notes.errors
        assert message in second_turret.notes.errors

    def test_excess_ship_mounts_report_hardpoint_overflow_on_last_parts(self):
        ship = _Ship(displacement=100)
        first_turret = SingleTurret()
        second_turret = SingleTurret()
        section = WeaponsSection(turrets=[first_turret, second_turret])

        section.validate_mounting(ship)

        message = 'Exceeds available hardpoints: 2 mounts installed, capacity is 1'
        assert message not in first_turret.notes.errors
        assert message in second_turret.notes.errors

    def test_small_craft_rejects_double_or_larger_turrets(self):
        ship = _Ship(displacement=99)
        turret = TripleTurret()
        section = WeaponsSection(turrets=[turret])

        section.validate_mounting(ship)

        assert 'Small craft may only upgrade one firmpoint to a single turret' in turret.notes.errors

    def test_fixed_mount_capacity_is_one_weapon_on_small_craft(self):
        ship = _Ship(displacement=99)
        fixed_mount = FixedMount(weapons=[BeamLaser(), BeamLaser()])
        section = WeaponsSection(fixed_mounts=[fixed_mount])

        section.validate_mounting(ship)

        assert 'Fixed mount can carry at most 1 weapon on this ship' in fixed_mount.notes.errors

    def test_fixed_mount_capacity_is_three_weapons_on_ships(self):
        ship = _Ship(displacement=400)
        fixed_mount = FixedMount(weapons=[BeamLaser(), BeamLaser(), BeamLaser(), BeamLaser()])
        section = WeaponsSection(fixed_mounts=[fixed_mount])

        section.validate_mounting(ship)

        assert 'Fixed mount can carry at most 3 weapons on this ship' in fixed_mount.notes.errors

    def test_fixed_mount_within_capacity_has_no_capacity_error(self):
        ship = _Ship(displacement=400)
        fixed_mount = FixedMount(weapons=[BeamLaser(), BeamLaser(), BeamLaser()])
        section = WeaponsSection(fixed_mounts=[fixed_mount])

        section.validate_mounting(ship)

        assert 'Fixed mount can carry at most 3 weapons on this ship' not in fixed_mount.notes.errors

    def test_all_parts_returns_mounts_and_optional_storage_in_display_order(self):
        turret = SingleTurret()
        fixed_mount = FixedMount()
        carronade = PlasmaCarronade()
        barbette = BeamLaserBarbette()
        spinal_mount = MassDriverSpinalMount()
        bay = SmallMissileBay()
        battery = LaserPointDefenseBattery2()
        missile_storage = MissileStorage(count=12)
        torpedo_storage = TorpedoStorage(count=3)
        sand_storage = SandcasterCanisterStorage(count=20)
        section = WeaponsSection(
            turrets=[turret],
            fixed_mounts=[fixed_mount],
            carronades=[carronade],
            barbettes=[barbette],
            spinal_mounts=[spinal_mount],
            bays=[bay],
            point_defense_batteries=[battery],
            missile_storage=missile_storage,
            torpedo_storage=torpedo_storage,
            sandcaster_canister_storage=sand_storage,
        )

        assert section._all_parts() == [
            turret,
            fixed_mount,
            carronade,
            barbette,
            spinal_mount,
            bay,
            battery,
            missile_storage,
            torpedo_storage,
            sand_storage,
        ]

    def test_all_parts_omits_absent_storage(self):
        turret = SingleTurret()
        section = WeaponsSection(turrets=[turret])

        assert section._all_parts() == [turret]

    def test_add_spec_rows_adds_grouped_mounts_then_individual_storage_rows(self):
        spec = ShipSpec()
        section = WeaponsSection(
            turrets=[SingleTurret()],
            fixed_mounts=[FixedMount()],
            carronades=[PlasmaCarronade()],
            barbettes=[BeamLaserBarbette()],
            spinal_mounts=[MassDriverSpinalMount()],
            bays=[SmallMissileBay()],
            point_defense_batteries=[LaserPointDefenseBattery2()],
            missile_storage=MissileStorage(count=12),
            torpedo_storage=TorpedoStorage(count=3),
            sandcaster_canister_storage=SandcasterCanisterStorage(count=20),
        )

        section.add_spec_rows(_SpecShip(), spec)

        assert [row.section for row in spec.rows] == [SpecSection.WEAPONS] * 10
        assert [row.item for row in spec.rows] == [
            'group:SingleTurret',
            'group:FixedMount',
            'group:PlasmaCarronade',
            'group:BeamLaserBarbette',
            'group:MassDriverSpinalMount',
            'group:SmallMissileBay',
            'group:LaserPointDefenseBattery2',
            'part:MissileStorage',
            'part:TorpedoStorage',
            'part:SandcasterCanisterStorage',
        ]

    def test_add_spec_rows_omits_absent_storage_rows(self):
        spec = ShipSpec()
        section = WeaponsSection(turrets=[SingleTurret()])

        section.add_spec_rows(_SpecShip(), spec)

        assert [row.item for row in spec.rows] == ['group:SingleTurret']
