import pytest

from ceres import hull, ship
from ceres.base import ShipBase
from ceres.weapons import (
    Barbette,
    Bay,
    FixedMount,
    MissileStorage,
    MountWeapon,
    PointDefenseBattery,
    Turret,
    WeaponsSection,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


# --- MountWeapon ---


def test_pulse_laser_base_cost():
    w = MountWeapon(weapon='pulse_laser')
    assert w.base_cost == 1_000_000


def test_pulse_laser_base_power():
    w = MountWeapon(weapon='pulse_laser')
    assert w.base_power == 4


def test_pulse_laser_no_upgrades_cost_modifier():
    w = MountWeapon(weapon='pulse_laser')
    assert w.cost_modifier == pytest.approx(1.0)


def test_pulse_laser_energy_efficient_cost_modifier():
    # Advanced: 1 advantage, +10% cost
    w = MountWeapon(weapon='pulse_laser', energy_efficient=True)
    assert w.cost_modifier == pytest.approx(1.10)


def test_pulse_laser_very_high_yield_cost_modifier():
    # Very Advanced: 2 advantages, +25% cost
    w = MountWeapon(weapon='pulse_laser', very_high_yield=True)
    assert w.cost_modifier == pytest.approx(1.25)


def test_pulse_laser_high_technology_cost_modifier():
    # High Technology: 3 advantages (very_high_yield=2 + energy_efficient=1), +50% cost
    w = MountWeapon(weapon='pulse_laser', very_high_yield=True, energy_efficient=True)
    assert w.cost_modifier == pytest.approx(1.50)


# --- FixedMount ---


def test_fixed_firmpoint_base_cost():
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser')])
    fp.bind(DummyOwner(12, 6))
    # mount MCr0.1 + weapon MCr1 * 1.0 = 1,100,000
    assert float(fp.cost) == pytest.approx(1_100_000)


def test_fixed_firmpoint_high_technology_cost():
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser', very_high_yield=True, energy_efficient=True)])
    fp.bind(DummyOwner(12, 6))
    # mount 100,000 + weapon 1,000,000 * 1.5 = 1,600,000
    assert float(fp.cost) == pytest.approx(1_600_000)


def test_fixed_firmpoint_tons_zero():
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser')])
    fp.bind(DummyOwner(12, 6))
    assert float(fp.tons) == 0


def test_fixed_firmpoint_base_power():
    # Firmpoint reduces by 25%: floor(4 * 0.75) = 3
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser')])
    fp.bind(DummyOwner(12, 6))
    assert float(fp.power) == 3


def test_fixed_firmpoint_energy_efficient_power():
    # Firmpoint -25% * energy_efficient -25%: floor(4 * 0.75 * 0.75) = floor(2.25) = 2
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser', very_high_yield=True, energy_efficient=True)])
    fp.bind(DummyOwner(12, 6))
    assert float(fp.power) == 2


def test_fixed_firmpoint_recomputes_cost_from_input():
    fp = FixedMount.model_validate({'weapons': [{'weapon': 'pulse_laser'}], 'cost': 999})
    fp.bind(DummyOwner(12, 6))
    assert fp.cost == pytest.approx(1_100_000)


def test_fixed_firmpoint_recomputes_tons_from_input():
    fp = FixedMount.model_validate({'weapons': [{'weapon': 'pulse_laser'}], 'tons': 999})
    fp.bind(DummyOwner(12, 6))
    assert fp.tons == 0


def test_fixed_firmpoint_can_carry_multiple_weapons_on_larger_ship():
    fp = FixedMount(
        weapons=[
            MountWeapon(weapon='pulse_laser'),
            MountWeapon(weapon='pulse_laser', energy_efficient=True),
        ]
    )
    fp.bind(DummyOwner(12, 100))
    assert float(fp.cost) == pytest.approx(100_000 + 1_000_000 + 1_100_000)
    assert float(fp.power) == 5


def test_fixed_firmpoint_with_multiple_weapons_reports_fixed_mount_item():
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser'), MountWeapon(weapon='pulse_laser')])
    assert [(note.category.value, note.message) for note in fp.notes] == [
        ('item', 'Fixed Mount'),
        ('info', 'Pulse Laser'),
        ('info', 'Pulse Laser'),
    ]


def test_pulse_laser_barbette_values():
    barbette = Barbette(weapon='pulse_laser')
    barbette.bind(DummyOwner(12, 200))
    assert barbette.tons == 5.0
    assert barbette.cost == 6_000_000
    assert barbette.power == 12.0


def test_particle_barbette_values():
    barbette = Barbette(weapon='particle')
    barbette.bind(DummyOwner(13, 400))
    assert barbette.build_item() == 'Particle Barbette'
    assert barbette.tons == pytest.approx(5.0)
    assert barbette.cost == pytest.approx(8_000_000)


def test_small_missile_bay_values():
    bay = Bay(size='small', weapon='missile')
    bay.bind(DummyOwner(12, 1_000))
    assert bay.tons == 50.0
    assert bay.cost == 12_000_000
    assert bay.power == 5.0
    assert bay.hardpoints_required == 1


def test_small_missile_bay_size_reduction_values():
    bay = Bay(size='small', weapon='missile', size_reduction=True)
    bay.bind(DummyOwner(13, 1_000))
    assert bay.build_item() == 'Small Missile Bay, Adv - Size Reduction'
    assert bay.tons == pytest.approx(45.0)
    assert bay.cost == pytest.approx(13_200_000)


def test_large_torpedo_bay_uses_five_hardpoints():
    bay = Bay(size='large', weapon='torpedo')
    bay.bind(DummyOwner(12, 10_000))
    assert bay.tons == 500.0
    assert bay.cost == 10_000_000
    assert bay.power == 10.0
    assert bay.hardpoints_required == 5


def test_type_ii_laser_point_defense_battery_values():
    battery = PointDefenseBattery(kind='laser', rating=2)
    battery.bind(DummyOwner(12, 1_000))
    assert battery.tons == 20.0
    assert battery.cost == 10_000_000
    assert battery.power == 20.0
    assert battery.hardpoints_required == 1


def test_type_ii_laser_point_defense_battery_item_values():
    battery = PointDefenseBattery(kind='laser', rating=2)
    battery.bind(DummyOwner(12, 1_000))
    assert battery.build_item() == 'Point Defense Battery: Type II-L'
    assert battery.tons == pytest.approx(20.0)
    assert battery.cost == pytest.approx(10_000_000)


def test_missile_storage_can_generate_armoured_bulkhead():
    storage = MissileStorage(count=480, armoured_bulkhead=True)
    storage.bind(DummyOwner(13, 400))
    assert storage.tons == pytest.approx(40.0)
    assert storage.cost == pytest.approx(0.0)
    assert storage.armoured_bulkhead_part is not None
    assert storage.armoured_bulkhead_part.tons == pytest.approx(4.0)
    assert storage.armoured_bulkhead_part.cost == pytest.approx(800_000)


def test_point_defense_battery_cannot_be_mounted_on_small_craft():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(point_defense_batteries=[PointDefenseBattery(kind='laser', rating=2)]),
    )

    assert my_ship.weapons is not None
    assert any(
        note.message == 'Point defense batteries cannot be mounted on small craft firmpoints'
        for note in my_ship.weapons.point_defense_batteries[0].notes
    )


def test_double_turret_cost_and_power_include_weapons():
    turret = Turret(
        size='double',
        weapons=[MountWeapon(weapon='pulse_laser'), MountWeapon(weapon='pulse_laser', energy_efficient=True)]
    )
    turret.bind(DummyOwner(12, 100))
    assert turret.cost == pytest.approx(500_000 + 1_000_000 + 1_100_000)
    assert turret.power == pytest.approx(1 + 4 + 3)


def test_single_turret_is_allowed_on_small_craft():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(turrets=[Turret(size='single')]),
    )

    assert my_ship.weapons is not None
    assert [(note.category.value, note.message) for note in my_ship.weapons.turrets[0].notes] == [
        ('item', 'Single Turret'),
        ('info', 'No weapons in turret'),
    ]


def test_small_craft_fixed_mount_cannot_carry_more_than_one_weapon():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(
            fixed_mounts=[FixedMount(weapons=[MountWeapon(weapon='pulse_laser'), MountWeapon(weapon='pulse_laser')])],
        ),
    )

    assert my_ship.weapons is not None
    assert any(
        note.message == 'Fixed mount can carry at most 1 weapon on this ship'
        for note in my_ship.weapons.fixed_mounts[0].notes
    )


def test_bay_cannot_be_mounted_on_small_craft():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(bays=[Bay(size='small', weapon='missile')]),
    )

    assert my_ship.weapons is not None
    assert any(
        note.message == 'Bays cannot be mounted on small craft firmpoints'
        for note in my_ship.weapons.bays[0].notes
    )


def test_small_craft_cannot_mount_double_turret():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(turrets=[Turret(size='double')]),
    )

    assert my_ship.weapons is not None
    assert [(note.category.value, note.message) for note in my_ship.weapons.turrets[0].notes] == [
        ('item', 'Double Turret'),
        ('info', 'No weapons in turret'),
        ('error', 'Small craft may only upgrade one firmpoint to a single turret'),
    ]


def test_small_craft_cannot_mount_triple_turret():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(turrets=[Turret(size='triple')]),
    )

    assert my_ship.weapons is not None
    assert [(note.category.value, note.message) for note in my_ship.weapons.turrets[0].notes] == [
        ('item', 'Triple Turret'),
        ('info', 'No weapons in turret'),
        ('error', 'Small craft may only upgrade one firmpoint to a single turret'),
    ]


def test_weapon_mounts_cannot_exceed_hardpoints():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(
            turrets=[Turret(size='double')],
            fixed_mounts=[FixedMount(weapons=[MountWeapon(weapon='pulse_laser')])],
        ),
    )

    assert my_ship.weapons is not None
    overflow_part = my_ship.weapons.turrets[0]
    assert any(
        note.message == 'Exceeds available hardpoints: 2 mounts installed, capacity is 1'
        for note in overflow_part.notes
    )


def test_weapon_mounts_cannot_exceed_firmpoints():
    my_ship = ship.Ship(
        tl=12,
        displacement=34,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(
            fixed_mounts=[
                FixedMount(weapons=[MountWeapon(weapon='pulse_laser')]),
                FixedMount(weapons=[MountWeapon(weapon='pulse_laser')]),
            ],
        ),
    )

    assert my_ship.weapons is not None
    overflow_part = my_ship.weapons.fixed_mounts[1]
    assert any(
        note.message == 'Exceeds available firmpoints: 2 mounts installed, capacity is 1'
        for note in overflow_part.notes
    )


def test_bays_count_against_hardpoint_capacity():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(bays=[Bay(size='large', weapon='torpedo')]),
    )

    assert my_ship.weapons is not None
    assert any(
        note.message == 'Exceeds available hardpoints: 5 mounts installed, capacity is 2'
        for note in my_ship.weapons.bays[0].notes
    )
