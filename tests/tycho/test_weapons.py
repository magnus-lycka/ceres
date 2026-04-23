import pytest

from tycho import hull, ship
from tycho.base import ShipBase
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection
from tycho.drives import DriveSection, FusionPlantTL12, MDrive, PowerSection
from tycho.parts import Advanced, EnergyEfficient, HighTechnology, SizeReduction, VeryAdvanced
from tycho.weapons import (
    Barbette,
    Bay,
    FixedMount,
    HighYield,
    LongRange,
    MissileStorage,
    MountWeapon,
    PointDefenseBattery,
    Turret,
    VeryHighYield,
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
    w = MountWeapon(weapon='pulse_laser', customisation=Advanced(EnergyEfficient))
    assert w.cost_modifier == pytest.approx(1.10)


def test_pulse_laser_very_high_yield_cost_modifier():
    # Very Advanced: 2 advantages, +25% cost
    w = MountWeapon(weapon='pulse_laser', customisation=VeryAdvanced(VeryHighYield))
    assert w.cost_modifier == pytest.approx(1.25)


def test_pulse_laser_high_technology_cost_modifier():
    # High Technology: 3 advantages (very_high_yield=2 + energy_efficient=1), +50% cost
    w = MountWeapon(weapon='pulse_laser', customisation=HighTechnology(VeryHighYield, EnergyEfficient))
    assert w.cost_modifier == pytest.approx(1.50)


# --- FixedMount ---


def test_fixed_firmpoint_base_cost():
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser')])
    fp.bind(DummyOwner(12, 6))
    # mount MCr0.1 + weapon MCr1 * 1.0 = 1,100,000
    assert float(fp.cost) == pytest.approx(1_100_000)


def test_fixed_firmpoint_high_technology_cost():
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser', customisation=HighTechnology(VeryHighYield, EnergyEfficient))])
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
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser', customisation=HighTechnology(VeryHighYield, EnergyEfficient))])
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
            MountWeapon(weapon='pulse_laser', customisation=Advanced(EnergyEfficient)),
        ]
    )
    fp.bind(DummyOwner(12, 100))
    assert float(fp.cost) == pytest.approx(100_000 + 1_000_000 + 1_100_000)
    assert float(fp.power) == 5


def test_mount_weapon_build_item_is_base_name_only():
    w = MountWeapon(weapon='pulse_laser', customisation=HighTechnology(VeryHighYield, EnergyEfficient))
    assert w.build_item() == 'Pulse Laser'


def test_mount_weapon_no_upgrades_has_no_customisation_note():
    w = MountWeapon(weapon='pulse_laser')
    assert w.customisation_note() is None


def test_mount_weapon_high_technology_customisation_note():
    w = MountWeapon(weapon='pulse_laser', customisation=HighTechnology(VeryHighYield, EnergyEfficient))
    note = w.customisation_note()
    assert note is not None
    assert note.category.value == 'info'
    assert note.message == 'High Technology: Very High Yield, Energy Efficient'


def test_mount_weapon_advanced_customisation_note():
    w = MountWeapon(weapon='pulse_laser', customisation=Advanced(EnergyEfficient))
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'Advanced: Energy Efficient'


def test_mount_weapon_very_advanced_customisation_note():
    w = MountWeapon(weapon='pulse_laser', customisation=VeryAdvanced(VeryHighYield))
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'Very Advanced: Very High Yield'


def test_mount_weapon_advanced_high_yield_customisation_note():
    w = MountWeapon(weapon='pulse_laser', customisation=Advanced(HighYield))
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'Advanced: High Yield'


def test_mount_weapon_long_range_customisation_note():
    w = MountWeapon(weapon='pulse_laser', customisation=VeryAdvanced(LongRange))
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'Very Advanced: Long Range'


def test_mount_weapon_long_range_is_allowed():
    w = MountWeapon(weapon='pulse_laser', customisation=VeryAdvanced(LongRange))
    assert ('error', 'Modification not allowed for MountWeapon: Long Range') not in [
        (note.category.value, note.message) for note in w.notes
    ]
    assert w.cost_modifier == pytest.approx(1.25)


def test_mount_weapon_high_yield_is_allowed():
    w = MountWeapon(weapon='pulse_laser', customisation=Advanced(HighYield))
    assert ('error', 'Modification not allowed for MountWeapon: High Yield') not in [
        (note.category.value, note.message) for note in w.notes
    ]
    assert w.cost_modifier == pytest.approx(1.10)


def test_mount_weapon_high_yield_not_applicable_for_missile_rack():
    w = MountWeapon(weapon='missile_rack', customisation=Advanced(HighYield))
    assert ('error', 'High Yield is not applicable for Missile Rack') in [
        (note.category.value, note.message) for note in w.notes
    ]


def test_fixed_mount_single_weapon_notes_include_customisation_note():
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser', customisation=HighTechnology(VeryHighYield, EnergyEfficient))])
    assert [(note.category.value, note.message) for note in fp.notes] == [
        ('item', 'Pulse Laser'),
        ('info', 'High Technology: Very High Yield, Energy Efficient'),
    ]


def test_fixed_firmpoint_with_multiple_weapons_reports_fixed_mount_item():
    fp = FixedMount(weapons=[MountWeapon(weapon='pulse_laser'), MountWeapon(weapon='pulse_laser')])
    assert [(note.category.value, note.message) for note in fp.notes] == [
        ('item', 'Fixed Mount'),
        ('info', 'Weapon: Pulse Laser × 2'),
    ]


def test_triple_turret_groups_identical_customised_weapons_in_notes():
    turret = Turret(
        size='triple',
        weapons=[
            MountWeapon(weapon='pulse_laser', customisation=HighTechnology(LongRange, HighYield)),
            MountWeapon(weapon='pulse_laser', customisation=HighTechnology(LongRange, HighYield)),
            MountWeapon(weapon='pulse_laser', customisation=HighTechnology(LongRange, HighYield)),
        ],
    )
    assert [(note.category.value, note.message) for note in turret.notes] == [
        ('item', 'Triple Turret'),
        ('info', 'Weapon: Pulse Laser × 3'),
        ('info', 'High Technology: Long Range, High Yield'),
    ]


def test_reused_weapon_and_turret_references_render_like_distinct_identical_objects():
    laser = MountWeapon(weapon='pulse_laser', customisation=HighTechnology(LongRange, HighYield))
    turret = Turret(size='triple', weapons=[laser, laser, laser])
    my_ship = ship.Ship(
        tl=15,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=50)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(20)),
        weapons=WeaponsSection(turrets=[turret, turret]),
    )

    spec = my_ship.build_spec()
    turret_row = spec.row('Triple Turret', section='Weapons')
    assert turret_row.quantity == 2
    assert turret_row.tons == pytest.approx(2.0)
    assert turret_row.cost == pytest.approx(11_000_000.0)
    assert [(note.category.value, note.message) for note in turret_row.notes] == [
        ('info', 'Weapon: Pulse Laser × 3'),
        ('info', 'High Technology: Long Range, High Yield'),
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
    assert barbette.build_item() == 'Barbette (Damage × 3 after armour)'
    assert barbette.tons == pytest.approx(5.0)
    assert barbette.cost == pytest.approx(8_000_000)


def test_particle_barbette_very_high_yield_values():
    barbette = Barbette(weapon='particle', customisation=VeryAdvanced(VeryHighYield))
    barbette.bind(DummyOwner(13, 400))
    assert barbette.build_item() == 'Barbette (Damage × 3 after armour)'
    assert barbette.tons == pytest.approx(5.0)
    assert barbette.cost == pytest.approx(10_000_000)
    assert barbette.power == pytest.approx(15.0)


def test_small_missile_bay_values():
    bay = Bay(size='small', weapon='missile')
    bay.bind(DummyOwner(12, 1_000))
    assert bay.tons == 50.0
    assert bay.cost == 12_000_000
    assert bay.power == 5.0
    assert bay.hardpoints_required == 1


def test_small_missile_bay_size_reduction_values():
    bay = Bay(size='small', weapon='missile', customisation=Advanced(SizeReduction))
    bay.bind(DummyOwner(13, 1_000))
    assert bay.build_item() == 'Small Bay (12 missiles per salvo)'
    assert bay.tons == pytest.approx(45.0)
    assert bay.cost == pytest.approx(13_200_000)


def test_small_missile_bay_three_size_reduction_steps_values():
    bay = Bay(size='small', weapon='missile', customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction))
    bay.bind(DummyOwner(13, 1_000))
    assert bay.build_item() == 'Small Bay (12 missiles per salvo)'
    assert bay.tons == pytest.approx(35.0)
    assert bay.cost == pytest.approx(18_000_000)


def test_medium_particle_beam_bay_high_yield_and_two_size_reductions_values():
    bay = Bay(size='medium', weapon='particle_beam', customisation=HighTechnology(HighYield, SizeReduction, SizeReduction))
    bay.bind(DummyOwner(15, 1_000))
    assert bay.tons == pytest.approx(80.0)
    assert bay.cost == pytest.approx(60_000_000.0)
    assert ('error', 'Modification not allowed for Bay: High Yield') not in [
        (note.category.value, note.message) for note in bay.notes
    ]


def test_medium_missile_bay_high_yield_not_applicable():
    bay = Bay(size='medium', weapon='missile', customisation=Advanced(HighYield))
    bay.bind(DummyOwner(10, 1_000))
    assert ('error', 'High Yield is not applicable for Medium Bay (24 missiles per salvo)') in [
        (note.category.value, note.message) for note in bay.notes
    ]


def test_high_technology_medium_particle_beam_bay_requires_tl15_not_tl18():
    bay = Bay(size='medium', weapon='particle_beam', customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction))
    bay.bind(DummyOwner(15, 450))
    assert bay.minimum_tl == 12
    assert bay.effective_tl == 15
    assert ('error', 'Requires TL18, ship is TL15') not in [
        (note.category.value, note.message) for note in bay.notes
    ]


def test_high_technology_medium_particle_beam_bay_errors_at_tl14():
    bay = Bay(size='medium', weapon='particle_beam', customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction))
    bay.bind(DummyOwner(14, 450))
    assert ('error', 'Requires TL15, ship is TL14') in [
        (note.category.value, note.message) for note in bay.notes
    ]


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
    assert battery.build_item() == 'Point Defence Laser Battery Type II'
    assert battery.tons == pytest.approx(20.0)
    assert battery.cost == pytest.approx(10_000_000)


def test_type_ii_laser_point_defense_battery_energy_efficient_values():
    battery = PointDefenseBattery(kind='laser', rating=2, customisation=Advanced(EnergyEfficient))
    battery.bind(DummyOwner(13, 1_000))
    assert battery.build_item() == 'Point Defence Laser Battery Type II'
    assert battery.tons == pytest.approx(20.0)
    assert battery.cost == pytest.approx(11_000_000.0)
    assert battery.power == pytest.approx(15.0)


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
        weapons=[MountWeapon(weapon='pulse_laser'), MountWeapon(weapon='pulse_laser', customisation=Advanced(EnergyEfficient))]
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


# ---------------------------------------------------------------------------
# Customisation labels as notes
# ---------------------------------------------------------------------------

def test_barbette_with_very_high_yield_item_is_base_name_only():
    barbette = Barbette(weapon='particle', customisation=VeryAdvanced(VeryHighYield))
    barbette.bind(DummyOwner(13, 400))
    assert barbette.build_item() == 'Barbette (Damage × 3 after armour)'


def test_barbette_with_very_high_yield_has_customisation_note():
    barbette = Barbette(weapon='particle', customisation=VeryAdvanced(VeryHighYield))
    barbette.bind(DummyOwner(13, 400))
    info_notes = [n.message for n in barbette.notes if n.category.value == 'info']
    assert 'Weapon: Particle' in info_notes
    assert 'Very Advanced: Very High Yield' in info_notes
    assert 'Damage × 3 after armour' not in info_notes


def test_bay_with_size_reduction_item_is_base_name_only():
    bay = Bay(size='small', weapon='missile', customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction))
    bay.bind(DummyOwner(13, 1_000))
    assert bay.build_item() == 'Small Bay (12 missiles per salvo)'


def test_bay_with_size_reduction_has_customisation_note():
    bay = Bay(size='small', weapon='missile', customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction))
    bay.bind(DummyOwner(13, 1_000))
    info_notes = [n.message for n in bay.notes if n.category.value == 'info']
    assert 'Weapon: Missile' in info_notes
    assert 'Magazine: 144 missiles (12 full salvos)' in info_notes
    assert 'High Technology: Size Reduction × 3' in info_notes
    assert 'Damage × 10 after armour' not in info_notes


def test_small_energy_bay_has_damage_multiple_note():
    bay = Bay(size='small', weapon='fusion_gun')
    bay.bind(DummyOwner(12, 1_000))
    assert bay.build_item() == 'Small Bay (Damage × 10 after armour)'
    info_notes = [n.message for n in bay.notes if n.category.value == 'info']
    assert 'Weapon: Fusion Gun' in info_notes
    assert 'Damage × 10 after armour' not in info_notes


def test_medium_energy_bay_has_damage_multiple_note():
    bay = Bay(size='medium', weapon='particle_beam')
    bay.bind(DummyOwner(12, 1_000))
    assert bay.build_item() == 'Medium Bay (Damage × 20 after armour)'
    info_notes = [n.message for n in bay.notes if n.category.value == 'info']
    assert 'Weapon: Particle Beam' in info_notes
    assert 'Damage × 20 after armour' not in info_notes


def test_large_energy_bay_has_damage_multiple_note():
    bay = Bay(size='large', weapon='meson_gun')
    bay.bind(DummyOwner(13, 1_000))
    assert bay.build_item() == 'Large Bay (Damage × 100 after armour)'
    info_notes = [n.message for n in bay.notes if n.category.value == 'info']
    assert 'Weapon: Meson Gun' in info_notes
    assert 'Damage × 100 after armour' not in info_notes


def test_medium_missile_bay_has_salvo_summary_note():
    bay = Bay(size='medium', weapon='missile')
    bay.bind(DummyOwner(12, 1_000))
    assert bay.build_item() == 'Medium Bay (24 missiles per salvo)'
    info_notes = [n.message for n in bay.notes if n.category.value == 'info']
    assert 'Weapon: Missile' in info_notes
    assert 'Magazine: 288 missiles (12 full salvos)' in info_notes


def test_large_torpedo_bay_has_salvo_summary_note():
    bay = Bay(size='large', weapon='torpedo')
    bay.bind(DummyOwner(12, 1_000))
    assert bay.build_item() == 'Large Bay (30 torpedoes per salvo)'
    info_notes = [n.message for n in bay.notes if n.category.value == 'info']
    assert 'Weapon: Torpedo' in info_notes
    assert 'Magazine: 360 torpedoes (12 full salvos)' in info_notes


def test_battery_with_energy_efficient_item_is_base_name_only():
    battery = PointDefenseBattery(kind='laser', rating=2, customisation=Advanced(EnergyEfficient))
    battery.bind(DummyOwner(13, 1_000))
    assert battery.build_item() == 'Point Defence Laser Battery Type II'


def test_battery_with_energy_efficient_has_customisation_note():
    battery = PointDefenseBattery(kind='laser', rating=2, customisation=Advanced(EnergyEfficient))
    battery.bind(DummyOwner(13, 1_000))
    info_notes = [n.message for n in battery.notes if n.category.value == 'info']
    assert 'Advanced: Energy Efficient' in info_notes


def test_grouped_parts_with_same_note_show_note_once(tmp_path):
    from tycho import hull, ship
    from tycho.bridge import Bridge, CommandSection
    from tycho.computer import Computer, ComputerSection
    my_ship = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        weapons=WeaponsSection(
            barbettes=[
                Barbette(weapon='particle', armoured_bulkhead=True),
                Barbette(weapon='particle', armoured_bulkhead=True),
            ],
        ),
    )
    spec = my_ship.build_spec()
    barbette_rows = [r for r in spec.rows if 'Barbette' in r.item]
    assert barbette_rows
    row = barbette_rows[0]
    ab_notes = [n for n in row.notes if 'Armoured bulkhead' in n.message]
    assert len(ab_notes) == 1, 'Duplicate armoured-bulkhead note should be deduplicated'
