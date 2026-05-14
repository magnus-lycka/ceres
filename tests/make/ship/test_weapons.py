import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, Computer20, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive1, PowerSection
from ceres.make.ship.parts import Advanced, EnergyEfficient, HighTechnology, SizeReduction, VeryAdvanced
from ceres.make.ship.weapons import (
    BeamLaser,
    DoubleTurret,
    FixedMount,
    GaussPointDefenseBattery3,
    HighYield,
    LargeMesonGunBay,
    LargeTorpedoBay,
    LaserPointDefenseBattery2,
    LongRange,
    MediumMissileBay,
    MediumParticleBeamBay,
    MissileRack,
    MissileStorage,
    ParticleBarbette,
    PulseLaser,
    PulseLaserBarbette,
    QuadTurret,
    Sandcaster,
    SandcasterCanisterStorage,
    SingleTurret,
    SmallFusionGunBay,
    SmallMissileBay,
    TorpedoBarbette,
    TripleTurret,
    VeryHighYield,
    WeaponsSection,
    _size_reduction_steps,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_size_reduction_steps_true_counts_as_one():
    assert _size_reduction_steps(True) == 1


# --- MountWeapon ---


def test_pulse_laser_base_cost():
    w = PulseLaser()
    assert w.base_cost == 1_000_000


def test_pulse_laser_base_power():
    w = PulseLaser()
    assert w.base_power == 4


def test_sandcaster_base_values():
    w = Sandcaster()
    assert w.base_cost == 250_000
    assert w.base_power == 0
    assert w.build_item() == 'Sandcaster'


def test_pulse_laser_no_upgrades_cost_modifier():
    w = PulseLaser()
    assert w.cost_modifier == pytest.approx(1.0)


def test_pulse_laser_energy_efficient_cost_modifier():
    # Advanced: 1 advantage, +10% cost
    w = PulseLaser(customisation=Advanced(modifications=[EnergyEfficient]))
    assert w.cost_modifier == pytest.approx(1.10)


def test_pulse_laser_very_high_yield_cost_modifier():
    # Very Advanced: 2 advantages, +25% cost
    w = PulseLaser(customisation=VeryAdvanced(modifications=[VeryHighYield]))
    assert w.cost_modifier == pytest.approx(1.25)


def test_pulse_laser_high_technology_cost_modifier():
    # High Technology: 3 advantages (very_high_yield=2 + energy_efficient=1), +50% cost
    w = PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))
    assert w.cost_modifier == pytest.approx(1.50)


# --- FixedMount ---


def test_fixed_firmpoint_base_cost():
    fp = FixedMount(weapons=[PulseLaser()])
    fp.bind(DummyOwner(12, 6))
    # mount MCr0.1 + weapon MCr1 * 1.0 = 1,100,000
    assert float(fp.cost) == pytest.approx(1_100_000)


def test_fixed_firmpoint_high_technology_cost():
    fp = FixedMount(weapons=[PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))])
    fp.bind(DummyOwner(12, 6))
    # mount 100,000 + weapon 1,000,000 * 1.5 = 1,600,000
    assert float(fp.cost) == pytest.approx(1_600_000)


def test_fixed_firmpoint_tons_zero():
    fp = FixedMount(weapons=[PulseLaser()])
    fp.bind(DummyOwner(12, 6))
    assert float(fp.tons) == 0


def test_fixed_firmpoint_base_power():
    # Firmpoint reduces by 25%: floor(4 * 0.75) = 3
    fp = FixedMount(weapons=[PulseLaser()])
    fp.bind(DummyOwner(12, 6))
    assert float(fp.power) == 3


def test_fixed_firmpoint_energy_efficient_power():
    # Firmpoint -25% * energy_efficient -25%: floor(4 * 0.75 * 0.75) = floor(2.25) = 2
    fp = FixedMount(weapons=[PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))])
    fp.bind(DummyOwner(12, 6))
    assert float(fp.power) == 2


def test_fixed_firmpoint_recomputes_cost_from_input():
    fp = FixedMount.model_validate({'weapons': [{'weapon_type': 'pulse_laser'}], 'cost': 999})
    fp.bind(DummyOwner(12, 6))
    assert fp.cost == pytest.approx(1_100_000)


def test_fixed_firmpoint_recomputes_tons_from_input():
    fp = FixedMount.model_validate({'weapons': [{'weapon_type': 'pulse_laser'}], 'tons': 999})
    fp.bind(DummyOwner(12, 6))
    assert fp.tons == 0


def test_fixed_mount_values_are_computed_properties_not_serialized_fields():
    fp = FixedMount.model_validate(
        {'weapons': [{'weapon_type': 'pulse_laser'}], 'tons': 999, 'cost': 999, 'power': 999}
    )
    fp.bind(DummyOwner(12, 6))
    assert fp.tons == pytest.approx(0.0)
    assert fp.cost == pytest.approx(1_100_000)
    assert fp.power == pytest.approx(3.0)
    dump = fp.model_dump()
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_sandcaster_canister_storage_values():
    storage = SandcasterCanisterStorage(count=20)
    storage.bind(DummyOwner(12, 400))
    assert storage.tons == pytest.approx(1.0)
    assert storage.cost == 0.0
    assert storage.build_item() == 'Sandcaster Canister Storage (20)'


def test_fixed_firmpoint_can_carry_multiple_weapons_on_larger_ship():
    fp = FixedMount(
        weapons=[
            PulseLaser(),
            PulseLaser(customisation=Advanced(modifications=[EnergyEfficient])),
        ]
    )
    fp.bind(DummyOwner(12, 100))
    assert float(fp.cost) == pytest.approx(100_000 + 1_000_000 + 1_100_000)
    assert float(fp.power) == 5


def test_mount_weapon_build_item_is_base_name_only():
    w = PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))
    assert w.build_item() == 'Pulse Laser'


def test_mount_weapon_no_upgrades_has_no_customisation_note():
    w = PulseLaser()
    assert w.customisation_note() is None


def test_mount_weapon_high_technology_customisation_note():
    w = PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'High Technology: Very High Yield, Energy Efficient'


def test_mount_weapon_advanced_customisation_note():
    w = PulseLaser(customisation=Advanced(modifications=[EnergyEfficient]))
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'Advanced: Energy Efficient'


def test_mount_weapon_very_advanced_customisation_note():
    w = PulseLaser(customisation=VeryAdvanced(modifications=[VeryHighYield]))
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'Very Advanced: Very High Yield'


def test_mount_weapon_advanced_high_yield_customisation_note():
    w = PulseLaser(customisation=Advanced(modifications=[HighYield]))
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'Advanced: High Yield'


def test_mount_weapon_long_range_customisation_note():
    w = PulseLaser(customisation=VeryAdvanced(modifications=[LongRange]))
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'Very Advanced: Long Range'


def test_mount_weapon_long_range_is_allowed():
    w = PulseLaser(customisation=VeryAdvanced(modifications=[LongRange]))
    assert 'Modification not allowed for MountWeapon: Long Range' not in w.notes.errors
    assert w.cost_modifier == pytest.approx(1.25)


def test_mount_weapon_high_yield_is_allowed():
    w = PulseLaser(customisation=Advanced(modifications=[HighYield]))
    assert 'Modification not allowed for MountWeapon: High Yield' not in w.notes.errors
    assert w.cost_modifier == pytest.approx(1.10)


def test_mount_weapon_high_yield_not_applicable_for_missile_rack():
    w = MissileRack(customisation=Advanced(modifications=[HighYield]))
    assert 'High Yield is not applicable for Missile Rack' in w.notes.errors


def test_mount_weapon_rejects_disallowed_modification():
    w = PulseLaser(customisation=Advanced(modifications=[SizeReduction]))
    assert 'Modification not allowed for MountWeapon: Size Reduction' in w.notes.errors


def test_fixed_mount_single_weapon_notes_include_customisation_note():
    fp = FixedMount(weapons=[PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))])
    notes = fp.notes
    assert notes.items == ['Pulse Laser']
    assert notes.infos == ['High Technology: Very High Yield, Energy Efficient']


def test_fixed_firmpoint_with_multiple_weapons_reports_fixed_mount_item():
    fp = FixedMount(weapons=[PulseLaser(), PulseLaser()])
    notes = fp.notes
    assert notes.items == ['Fixed Mount']
    assert notes.contents == ['Pulse Laser × 2']


def test_triple_turret_groups_identical_customised_weapons_in_notes():
    turret = TripleTurret(
        weapons=[
            PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield])),
            PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield])),
            PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield])),
        ],
    )
    notes = turret.notes
    assert notes.items == ['Triple Turret']
    assert notes.contents == ['Pulse Laser × 3']
    assert notes.infos == ['High Technology: Long Range, High Yield']


def test_reused_weapon_and_turret_references_render_like_distinct_identical_objects():
    laser = PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield]))
    turret = TripleTurret(weapons=[laser, laser, laser])
    my_ship = ship.Ship(
        tl=15,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FusionPlantTL12(output=50)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer20()),
        weapons=WeaponsSection(turrets=[turret, turret]),
    )

    spec = my_ship.build_spec()
    turret_row = spec.row('Triple Turret', section='Weapons')
    assert turret_row.quantity == 2
    assert turret_row.tons == pytest.approx(2.0)
    assert turret_row.cost == pytest.approx(11_000_000.0)
    notes = turret_row.notes
    assert notes.contents == ['Pulse Laser × 3']
    assert notes.infos == ['High Technology: Long Range, High Yield']


def test_pulse_laser_barbette_values():
    barbette = PulseLaserBarbette()
    barbette.bind(DummyOwner(12, 200))
    assert barbette.tons == 5.0
    assert barbette.cost == 6_000_000
    assert barbette.power == 12.0


def test_particle_barbette_values():
    barbette = ParticleBarbette()
    barbette.bind(DummyOwner(13, 400))
    assert barbette.build_item() == 'Particle Barbette (Damage × 3 after armour)'
    assert barbette.tons == pytest.approx(5.0)
    assert barbette.cost == pytest.approx(8_000_000)


def test_torpedo_barbette_has_no_damage_multiple_in_item():
    barbette = TorpedoBarbette()
    barbette.bind(DummyOwner(12, 400))
    assert barbette.build_item() == 'Torpedo Barbette'
    assert barbette.crew_required_commercial == 1
    assert barbette.crew_required_military == 2


def test_particle_barbette_very_high_yield_values():
    barbette = ParticleBarbette(customisation=VeryAdvanced(modifications=[VeryHighYield]))
    barbette.bind(DummyOwner(13, 400))
    assert barbette.build_item() == 'Particle Barbette (Damage × 3 after armour)'
    assert barbette.tons == pytest.approx(5.0)
    assert barbette.cost == pytest.approx(10_000_000)
    assert barbette.power == pytest.approx(15.0)


def test_barbette_values_are_computed_properties_not_serialized_fields():
    barbette = ParticleBarbette.model_validate({'tons': 999, 'cost': 999, 'power': 999})
    barbette.bind(DummyOwner(13, 400))
    assert barbette.tons == pytest.approx(5.0)
    assert barbette.cost == pytest.approx(8_000_000)
    assert barbette.power == pytest.approx(15.0)
    dump = barbette.model_dump()
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_small_missile_bay_values():
    bay = SmallMissileBay()
    bay.bind(DummyOwner(12, 1_000))
    assert bay.tons == 50.0
    assert bay.cost == 12_000_000
    assert bay.power == 5.0
    assert bay.hardpoints_required == 1


def test_small_missile_bay_size_reduction_values():
    bay = SmallMissileBay(customisation=Advanced(modifications=[SizeReduction]))
    bay.bind(DummyOwner(13, 1_000))
    assert bay.build_item() == 'Small Missile Bay (12 missiles per salvo)'
    assert bay.tons == pytest.approx(45.0)
    assert bay.cost == pytest.approx(13_200_000)


def test_small_missile_bay_three_size_reduction_steps_values():
    bay = SmallMissileBay(
        customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
    )
    bay.bind(DummyOwner(13, 1_000))
    assert bay.build_item() == 'Small Missile Bay (12 missiles per salvo)'
    assert bay.tons == pytest.approx(35.0)
    assert bay.cost == pytest.approx(18_000_000)


def test_medium_particle_beam_bay_high_yield_and_two_size_reductions_values():
    bay = MediumParticleBeamBay(
        customisation=HighTechnology(modifications=[HighYield, SizeReduction, SizeReduction]),
    )
    bay.bind(DummyOwner(15, 1_000))
    assert bay.tons == pytest.approx(80.0)
    assert bay.cost == pytest.approx(60_000_000.0)
    assert 'Modification not allowed for Bay: High Yield' not in bay.notes.errors


def test_medium_missile_bay_high_yield_not_applicable():
    bay = MediumMissileBay(customisation=Advanced(modifications=[HighYield]))
    bay.bind(DummyOwner(10, 1_000))
    assert 'High Yield is not applicable for Medium Missile Bay (24 missiles per salvo)' in bay.notes.errors


def test_high_technology_medium_particle_beam_bay_requires_tl15_not_tl18():
    bay = MediumParticleBeamBay(
        customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
    )
    bay.bind(DummyOwner(15, 450))
    assert bay.tl == 12
    assert 'Requires TL18, ship is TL15' not in bay.notes.errors


def test_high_technology_medium_particle_beam_bay_errors_at_tl14():
    bay = MediumParticleBeamBay(
        customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
    )
    bay.bind(DummyOwner(14, 450))
    assert 'Requires TL15, ship is TL14' in bay.notes.errors


def test_large_torpedo_bay_uses_five_hardpoints():
    bay = LargeTorpedoBay()
    bay.bind(DummyOwner(12, 10_000))
    assert bay.tons == 500.0
    assert bay.cost == 10_000_000
    assert bay.power == 10.0
    assert bay.hardpoints_required == 5


def test_type_ii_laser_point_defense_battery_values():
    battery = LaserPointDefenseBattery2()
    battery.bind(DummyOwner(12, 1_000))
    assert battery.tons == 20.0
    assert battery.cost == 10_000_000
    assert battery.power == 20.0
    assert battery.hardpoints_required == 1


def test_type_ii_laser_point_defense_battery_item_values():
    battery = LaserPointDefenseBattery2()
    battery.bind(DummyOwner(12, 1_000))
    assert battery.build_item() == 'Point Defence Laser Battery Type II'
    assert battery.tons == pytest.approx(20.0)
    assert battery.cost == pytest.approx(10_000_000)


def test_type_ii_laser_point_defense_battery_energy_efficient_values():
    battery = LaserPointDefenseBattery2(customisation=Advanced(modifications=[EnergyEfficient]))
    battery.bind(DummyOwner(13, 1_000))
    assert battery.build_item() == 'Point Defence Laser Battery Type II'
    assert battery.tons == pytest.approx(20.0)
    assert battery.cost == pytest.approx(11_000_000.0)
    assert battery.power == pytest.approx(15.0)


@pytest.mark.parametrize(
    'part, expected_tons, expected_cost, expected_power',
    [
        (MissileStorage.model_validate({'count': 24, 'tons': 999, 'cost': 999, 'power': 999}), 2.0, 0.0, 0.0),
        (
            SandcasterCanisterStorage.model_validate({'count': 20, 'tons': 999, 'cost': 999, 'power': 999}),
            1.0,
            0.0,
            0.0,
        ),
        (DoubleTurret.model_validate({'tons': 999, 'cost': 999, 'power': 999}), 1.0, 500_000.0, 1.0),
        (
            SmallMissileBay.model_validate({'tons': 999, 'cost': 999, 'power': 999}),
            50.0,
            12_000_000.0,
            5.0,
        ),
        (
            LaserPointDefenseBattery2.model_validate({'tons': 999, 'cost': 999, 'power': 999}),
            20.0,
            10_000_000.0,
            20.0,
        ),
    ],
)
def test_weapon_part_values_are_computed_properties_not_serialized_fields(
    part,
    expected_tons,
    expected_cost,
    expected_power,
):
    part.bind(DummyOwner(13, 1_000))
    assert part.tons == pytest.approx(expected_tons)
    assert part.cost == pytest.approx(expected_cost)
    assert part.power == pytest.approx(expected_power)
    dump = part.model_dump()
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


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
        weapons=WeaponsSection(point_defense_batteries=[LaserPointDefenseBattery2()]),
    )

    assert my_ship.weapons is not None
    assert any(
        note.message == 'Point defense batteries cannot be mounted on small craft firmpoints'
        for note in my_ship.weapons.point_defense_batteries[0].notes
    )


def test_double_turret_cost_and_power_include_weapons():
    turret = DoubleTurret(
        weapons=[
            PulseLaser(),
            PulseLaser(customisation=Advanced(modifications=[EnergyEfficient])),
        ],
    )
    turret.bind(DummyOwner(12, 100))
    assert turret.cost == pytest.approx(500_000 + 1_000_000 + 1_100_000)
    assert turret.power == pytest.approx(1 + 4 + 3)


def test_quad_turret_cost_and_power_include_weapons():
    turret = QuadTurret(
        weapons=[
            BeamLaser(),
            BeamLaser(),
            BeamLaser(),
            BeamLaser(),
        ],
    )
    turret.bind(DummyOwner(12, 100))
    assert turret.cost == pytest.approx(2_000_000 + 4 * 500_000)
    assert turret.power == pytest.approx(2 + 4 * 4)


def test_double_turret_errors_if_it_mounts_too_many_weapons():
    turret = DoubleTurret(
        weapons=[
            PulseLaser(),
            PulseLaser(),
            PulseLaser(),
        ],
    )
    assert 'Turret can mount at most 2 weapons' in turret.notes.errors


def test_single_turret_is_allowed_on_small_craft():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(turrets=[SingleTurret()]),
    )

    assert my_ship.weapons is not None
    notes = my_ship.weapons.turrets[0].notes
    assert notes.items == ['Single Turret']
    assert notes.infos == ['No weapons in turret']


def test_small_craft_fixed_mount_cannot_carry_more_than_one_weapon():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(
            fixed_mounts=[FixedMount(weapons=[PulseLaser(), PulseLaser()])],
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
        weapons=WeaponsSection(bays=[SmallMissileBay()]),
    )

    assert my_ship.weapons is not None
    assert any(
        note.message == 'Bays cannot be mounted on small craft firmpoints' for note in my_ship.weapons.bays[0].notes
    )


def test_small_craft_cannot_mount_double_turret():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(turrets=[DoubleTurret()]),
    )

    assert my_ship.weapons is not None
    notes = my_ship.weapons.turrets[0].notes
    assert notes.items == ['Double Turret']
    assert notes.infos == ['No weapons in turret']
    assert notes.errors == ['Small craft may only upgrade one firmpoint to a single turret']


def test_small_craft_cannot_mount_triple_turret():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(turrets=[TripleTurret()]),
    )

    assert my_ship.weapons is not None
    notes = my_ship.weapons.turrets[0].notes
    assert notes.items == ['Triple Turret']
    assert notes.infos == ['No weapons in turret']
    assert notes.errors == ['Small craft may only upgrade one firmpoint to a single turret']


def test_weapon_mounts_cannot_exceed_hardpoints():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(
            turrets=[DoubleTurret()],
            fixed_mounts=[FixedMount(weapons=[PulseLaser()])],
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
                FixedMount(weapons=[PulseLaser()]),
                FixedMount(weapons=[PulseLaser()]),
            ],
        ),
    )

    assert my_ship.weapons is not None
    overflow_part = my_ship.weapons.fixed_mounts[1]
    assert any(
        note.message == 'Exceeds available firmpoints: 2 mounts installed, capacity is 1'
        for note in overflow_part.notes
    )


def test_small_craft_mount_capacity_boundaries():
    assert WeaponsSection.mount_capacity(DummyOwner(12, 34)) == 1
    assert WeaponsSection.mount_capacity(DummyOwner(12, 35)) == 2
    assert WeaponsSection.mount_capacity(DummyOwner(12, 70)) == 2
    assert WeaponsSection.mount_capacity(DummyOwner(12, 71)) == 3


def test_bays_count_against_hardpoint_capacity():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        weapons=WeaponsSection(bays=[LargeTorpedoBay()]),
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
    barbette = ParticleBarbette(customisation=VeryAdvanced(modifications=[VeryHighYield]))
    barbette.bind(DummyOwner(13, 400))
    assert barbette.build_item() == 'Particle Barbette (Damage × 3 after armour)'


def test_barbette_with_very_high_yield_has_customisation_note():
    barbette = ParticleBarbette(customisation=VeryAdvanced(modifications=[VeryHighYield]))
    barbette.bind(DummyOwner(13, 400))
    info_notes = barbette.notes.infos
    assert 'Very Advanced: Very High Yield' in info_notes
    assert 'Damage × 3 after armour' not in info_notes


def test_bay_with_size_reduction_item_is_base_name_only():
    bay = SmallMissileBay(
        customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
    )
    bay.bind(DummyOwner(13, 1_000))
    assert bay.build_item() == 'Small Missile Bay (12 missiles per salvo)'


def test_bay_with_size_reduction_has_customisation_note():
    bay = SmallMissileBay(
        customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
    )
    bay.bind(DummyOwner(13, 1_000))
    info_notes = bay.notes.infos
    assert 'Magazine: 144 missiles (12 full salvos)' in info_notes
    assert 'High Technology: Size Reduction × 3' in info_notes
    assert 'Damage × 10 after armour' not in info_notes


def test_small_energy_bay_has_damage_multiple_note():
    bay = SmallFusionGunBay()
    bay.bind(DummyOwner(12, 1_000))
    assert bay.build_item() == 'Small Fusion Gun Bay (Damage × 10 after armour)'


def test_medium_energy_bay_has_damage_multiple_note():
    bay = MediumParticleBeamBay()
    bay.bind(DummyOwner(12, 1_000))
    assert bay.build_item() == 'Medium Particle Beam Bay (Damage × 20 after armour)'


def test_large_energy_bay_has_damage_multiple_note():
    bay = LargeMesonGunBay()
    bay.bind(DummyOwner(13, 1_000))
    assert bay.build_item() == 'Large Meson Gun Bay (Damage × 100 after armour)'


def test_medium_missile_bay_has_salvo_summary_note():
    bay = MediumMissileBay()
    bay.bind(DummyOwner(12, 1_000))
    assert bay.build_item() == 'Medium Missile Bay (24 missiles per salvo)'
    info_notes = bay.notes.infos
    assert 'Magazine: 288 missiles (12 full salvos)' in info_notes


def test_large_torpedo_bay_has_salvo_summary_note():
    bay = LargeTorpedoBay()
    bay.bind(DummyOwner(12, 1_000))
    assert bay.build_item() == 'Large Torpedo Bay (30 torpedoes per salvo)'
    info_notes = bay.notes.infos
    assert 'Magazine: 360 torpedoes (12 full salvos)' in info_notes
    assert bay.crew_required_commercial == 0


def test_battery_with_energy_efficient_item_is_base_name_only():
    battery = LaserPointDefenseBattery2(customisation=Advanced(modifications=[EnergyEfficient]))
    battery.bind(DummyOwner(13, 1_000))
    assert battery.build_item() == 'Point Defence Laser Battery Type II'


def test_battery_with_energy_efficient_has_customisation_note():
    battery = LaserPointDefenseBattery2(customisation=Advanced(modifications=[EnergyEfficient]))
    battery.bind(DummyOwner(13, 1_000))
    info_notes = battery.notes.infos
    assert 'Advanced: Energy Efficient' in info_notes


def test_gauss_point_defense_battery_notes_include_ammunition_requirement():
    battery = GaussPointDefenseBattery3()
    battery.bind(DummyOwner(13, 1_000))
    info_notes = battery.notes.infos
    assert 'Intercept +6D' in info_notes
    assert 'Requires ammunition storage to reload after 12 rounds' in info_notes


def test_grouped_parts_with_same_note_show_note_once(tmp_path):
    from ceres.make.ship import hull, ship
    from ceres.make.ship.bridge import Bridge, CommandSection
    from ceres.make.ship.computer import ComputerSection

    my_ship = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        weapons=WeaponsSection(
            barbettes=[
                ParticleBarbette(armoured_bulkhead=True),
                ParticleBarbette(armoured_bulkhead=True),
            ],
        ),
    )
    spec = my_ship.build_spec()
    barbette_rows = [r for r in spec.rows if 'Barbette' in r.item]
    assert barbette_rows
    row = barbette_rows[0]
    ab_notes = [n for n in row.notes if 'Armoured bulkhead' in n.message]
    assert len(ab_notes) == 1, 'Duplicate armoured-bulkhead note should be deduplicated'


def test_point_defense_battery_appears_in_weapon_spec_rows():
    my_ship = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        weapons=WeaponsSection(point_defense_batteries=[LaserPointDefenseBattery2()]),
    )
    spec = my_ship.build_spec()
    row = spec.row('Point Defence Laser Battery Type II', section='Weapons')
    assert row.tons == pytest.approx(20.0)
    assert row.cost == pytest.approx(10_000_000.0)
