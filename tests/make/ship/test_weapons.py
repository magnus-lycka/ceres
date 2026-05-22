import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, Computer20, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive1, PowerSection
from ceres.make.ship.parts import Advanced, Budget, EnergyEfficient, HighTechnology, SizeReduction, VeryAdvanced
from ceres.make.ship.view import collapsed_main_rows
from ceres.make.ship.weapons import (
    Accurate,
    BeamLaser,
    DoubleTurret,
    EasyToRepair,
    FixedMount,
    FusionCarronade,
    GaussPointDefenseBattery3,
    GeneralPurposeMassDriverBay,
    HighYield,
    Inaccurate,
    IntenseFocus,
    LargeHullcutterBay,
    LargeMesonGunBay,
    LargeTorpedoBay,
    LaserPointDefenseBattery2,
    LongRange,
    MassDriverSpinalMount,
    MediumMissileBay,
    MediumParticleBeamBay,
    MesonSpinalMount,
    MissileRack,
    MissileStorage,
    ParticleAcceleratorSpinalMount,
    ParticleBarbette,
    PlasmaBarbette,
    PlasmaCarronade,
    PulseLaser,
    PulseLaserBarbette,
    QuadTurret,
    RailgunSpinalMount,
    Resilient,
    Sandcaster,
    SandcasterCanisterStorage,
    SingleTurret,
    SmallFusionGunBay,
    SmallMissileBay,
    TorpedoBarbette,
    TorpedoInterceptorCluster,
    TorpedoStorage,
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


def test_torpedo_storage_uses_three_torpedoes_per_ton():
    storage = TorpedoStorage(count=7_200)

    assert storage.build_item() == 'Torpedo Storage (7200)'
    assert storage.tons == pytest.approx(2_400)
    assert storage.cost == 0.0
    assert storage.power == 0.0


def test_particle_accelerator_spinal_mount_values_scale_by_base_size_multiple():
    spinal_mount = ParticleAcceleratorSpinalMount(size_multiple=2)
    spinal_mount.bind(DummyOwner(11, 50_000))

    assert spinal_mount.build_item() == 'Particle Accelerator Spinal Mount'
    assert spinal_mount.tons == pytest.approx(7_000.0)
    assert spinal_mount.cost == pytest.approx(2_000_000_000.0)
    assert spinal_mount.power == pytest.approx(2_000.0)
    assert spinal_mount.hardpoints_required == 70
    assert spinal_mount.crew_required_military == 70
    assert 'Damage: 16D × 1,000' in spinal_mount.notes.infos


@pytest.mark.parametrize(
    ('spinal_cls', 'tl', 'base_tons', 'base_power', 'base_cost', 'base_damage', 'max_tons'),
    [
        (MassDriverSpinalMount, 10, 5_000.0, 250.0, 1_500_000_000.0, 4, 100_000.0),
        (MesonSpinalMount, 12, 7_500.0, 1_000.0, 2_000_000_000.0, 6, 75_000.0),
        (ParticleAcceleratorSpinalMount, 11, 3_500.0, 1_000.0, 1_000_000_000.0, 8, 28_000.0),
        (RailgunSpinalMount, 10, 3_500.0, 500.0, 500_000_000.0, 4, 21_000.0),
    ],
)
def test_spinal_mount_hg_table_values(spinal_cls, tl, base_tons, base_power, base_cost, base_damage, max_tons):
    spinal_mount = spinal_cls()
    spinal_mount.bind(DummyOwner(tl, 200_000))

    assert spinal_mount.tl == tl
    assert spinal_mount.tons == pytest.approx(base_tons)
    assert spinal_mount.power == pytest.approx(base_power)
    assert spinal_mount.cost == pytest.approx(base_cost)
    assert spinal_mount.max_tons == pytest.approx(max_tons)
    assert spinal_mount.hardpoints_required == pytest.approx(base_tons / 100)
    assert spinal_mount.crew_required_military == pytest.approx(base_tons / 100)
    assert f'Damage: {base_damage}D × 1,000' in spinal_mount.notes.infos


def test_particle_accelerator_spinal_mount_appears_in_weapon_spec_rows():
    my_ship = ship.Ship(
        tl=11,
        displacement=50_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        weapons=WeaponsSection(spinal_mounts=[ParticleAcceleratorSpinalMount(size_multiple=2)]),
    )

    spec = my_ship.build_spec()

    row = spec.row('Particle Accelerator Spinal Mount', section='Weapons')
    assert row.tons == pytest.approx(7_000.0)
    assert row.cost == pytest.approx(2_000_000_000.0)
    assert row.power == pytest.approx(-2_000.0)


@pytest.mark.parametrize(
    ('tl_improvement', 'tons', 'cost'),
    [
        (1, 6_750.0, 2_200_000_000.0),
        (2, 6_375.0, 2_400_000_000.0),
        (3, 6_000.0, 2_600_000_000.0),
    ],
)
def test_meson_spinal_mount_tl_improvement_values(tl_improvement, tons, cost):
    spinal_mount = MesonSpinalMount(tl_improvement=tl_improvement)
    spinal_mount.bind(DummyOwner(12 + tl_improvement, 100_000))

    assert spinal_mount.build_item() == f'Meson Spinal Mount (TL{12 + tl_improvement})'
    assert spinal_mount.tons == pytest.approx(tons)
    assert spinal_mount.cost == pytest.approx(cost)
    assert spinal_mount.power == pytest.approx(1_000.0)


def test_spinal_mount_tl_improvement_requires_corresponding_ship_tl():
    spinal_mount = MesonSpinalMount(tl_improvement=3)
    spinal_mount.bind(DummyOwner(14, 100_000))

    assert 'Requires TL15, ship is TL14' in spinal_mount.notes.errors


def test_spinal_mount_item_includes_tl_improvement_but_not_base_size_multiple():
    spinal_mount = MesonSpinalMount(tl_improvement=3, size_multiple=2)
    spinal_mount.bind(DummyOwner(15, 100_000))

    assert spinal_mount.build_item() == 'Meson Spinal Mount (TL15)'
    assert spinal_mount.tons == pytest.approx(12_000.0)
    assert spinal_mount.cost == pytest.approx(5_200_000_000.0)


def test_mass_driver_spinal_mount_ammunition_cargo():
    cargo_hold = MassDriverSpinalMount.ammunition_cargo(attacks=3)

    assert cargo_hold.build_item() == 'Mass Driver Spinal Mount Ammunition (3 attacks) (Cargo Hold)'
    assert cargo_hold.tons == pytest.approx(150.0)
    assert cargo_hold.cost == pytest.approx(1_500_000.0)


def test_mass_driver_spinal_mount_ammunition_requires_positive_attacks():
    with pytest.raises(ValueError, match='at least one attack'):
        MassDriverSpinalMount.ammunition_cargo(attacks=0)


def test_railgun_spinal_mount_extra_rounds_cargo():
    cargo_hold = RailgunSpinalMount.extra_rounds_cargo(rounds=6)

    assert cargo_hold.build_item() == 'Railgun Spinal Mount Extra Rounds (6 rounds) (Cargo Hold)'
    assert cargo_hold.tons == pytest.approx(120.0)
    assert cargo_hold.cost == pytest.approx(1_200_000.0)


def test_railgun_spinal_mount_extra_rounds_requires_positive_rounds():
    with pytest.raises(ValueError, match='at least one extra round'):
        RailgunSpinalMount.extra_rounds_cargo(rounds=0)


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


def test_pop_up_fixed_mount_adds_tons_cost_tl_and_note():
    mount = FixedMount(pop_up=True, weapons=[PulseLaser()])
    mount.bind(DummyOwner(10, 100))

    assert mount.tons == pytest.approx(1.0)
    assert mount.cost == pytest.approx(2_100_000.0)
    assert mount.power == pytest.approx(3.0)
    assert mount.notes.infos == ['Pop-up mounting: concealed until deployed']


def test_pop_up_fixed_mount_requires_tl10():
    mount = FixedMount(pop_up=True, weapons=[PulseLaser()])
    mount.bind(DummyOwner(9, 100))

    assert 'Requires TL10, ship is TL9' in mount.notes.errors


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


def test_mount_weapon_accurate_is_allowed_and_noted():
    w = PulseLaser(customisation=VeryAdvanced(modifications=[Accurate]))

    assert 'Modification not allowed for MountWeapon: Accurate' not in w.notes.errors
    note = w.customisation_note()
    assert note is not None
    assert note.message == 'Very Advanced: Accurate'
    assert w.notes.infos == ['Accurate weapons gain DM+1 to attack rolls']


def test_mount_weapon_easy_to_repair_and_resilient_are_allowed_and_noted():
    w = BeamLaser(customisation=VeryAdvanced(modifications=[EasyToRepair, Resilient]))

    assert 'Modification not allowed for MountWeapon: Easy to Repair' not in w.notes.errors
    assert 'Modification not allowed for MountWeapon: Resilient' not in w.notes.errors
    assert w.notes.infos == [
        'Easy to Repair weapons grant DM+1 to repair attempts',
        'Resilient weapons reduce weapon critical hit Severity by -1',
    ]


def test_mount_weapon_inaccurate_is_allowed_as_disadvantage():
    w = PulseLaser(customisation=Budget(modifications=[Inaccurate]))

    assert 'Modification not allowed for MountWeapon: Inaccurate' not in w.notes.errors
    assert w.notes.infos == ['Inaccurate weapons suffer DM-1 to attack rolls']
    assert w.cost_modifier == pytest.approx(0.75)


def test_mount_weapon_intense_focus_is_allowed_for_lasers_and_noted():
    w = PulseLaser(customisation=VeryAdvanced(modifications=[IntenseFocus]))

    assert 'Intense Focus is only applicable for laser and particle weapons' not in w.notes.errors
    assert w.notes.infos == ['Intense Focus weapons gain AP+2']


def test_mount_weapon_intense_focus_rejects_missile_rack():
    w = MissileRack(customisation=VeryAdvanced(modifications=[IntenseFocus]))

    assert 'Intense Focus is only applicable for laser and particle weapons' in w.notes.errors


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


def test_pop_up_turret_adds_tons_cost_and_note():
    turret = SingleTurret(pop_up=True, weapons=[PulseLaser()])
    turret.bind(DummyOwner(10, 100))

    assert turret.tons == pytest.approx(2.0)
    assert turret.cost == pytest.approx(2_200_000.0)
    assert turret.power == pytest.approx(5.0)
    assert turret.notes.contents == ['Pulse Laser']
    assert turret.notes.infos == ['Pop-up mounting: concealed until deployed']


def test_pop_up_turret_appears_in_ship_spec():
    turret = SingleTurret(pop_up=True, weapons=[PulseLaser()])
    my_ship = ship.Ship(
        tl=10,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        weapons=WeaponsSection(turrets=[turret]),
    )

    row = my_ship.build_spec().row('Single Turret', section='Weapons')
    assert row.tons == pytest.approx(2.0)
    assert row.cost == pytest.approx(2_200_000.0)
    assert row.power == pytest.approx(-5.0)
    assert row.notes.contents == ['Pulse Laser']
    assert row.notes.infos == ['Pop-up mounting: concealed until deployed']


def test_different_triple_turrets_do_not_collapse_in_spec_or_report_rows():
    my_ship = ship.Ship(
        tl=12,
        displacement=300,
        hull=hull.Hull(configuration=hull.standard_hull),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        weapons=WeaponsSection(
            turrets=[
                TripleTurret(weapons=[PulseLaser(), PulseLaser(), PulseLaser()]),
                TripleTurret(weapons=[MissileRack(), MissileRack(), Sandcaster()]),
            ],
        ),
    )

    spec = my_ship.build_spec()
    weapon_rows = [r for r in spec.rows_for_section('Weapons') if r.item == 'Triple Turret']
    assert len(weapon_rows) == 2
    assert [row.quantity for row in weapon_rows] == [None, None]
    assert [row.notes.contents for row in weapon_rows] == [
        ['Pulse Laser × 3'],
        ['Missile Rack × 2', 'Sandcaster'],
    ]

    report_rows = [r for r in collapsed_main_rows(spec) if r.section == 'Weapons' and r.item == 'Triple Turret']
    assert len(report_rows) == 2
    assert [row.quantity for row in report_rows] == [None, None]


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


def test_general_purpose_mass_driver_bay_values_and_notes():
    bay = GeneralPurposeMassDriverBay()
    bay.bind(DummyOwner(8, 1_000))

    assert bay.build_item() == 'Small General-Purpose Mass Driver Bay'
    assert bay.tons == pytest.approx(50.0)
    assert bay.cost == pytest.approx(4_000_000.0)
    assert bay.power == pytest.approx(10.0)
    assert bay.hardpoints_required == 1
    assert bay.crew_required_military == 1
    assert bay.notes.infos == [
        'Can launch 50 tons; DM-4 to attack rolls against manoeuvring targets',
    ]


def test_general_purpose_mass_driver_bay_extra_capacity_values():
    bay = GeneralPurposeMassDriverBay(extra_launch_capacity=3)
    bay.bind(DummyOwner(8, 1_000))

    assert bay.tons == pytest.approx(56.0)
    assert bay.cost == pytest.approx(4_225_000.0)
    assert bay.power == pytest.approx(19.0)
    assert bay.launch_capacity == pytest.approx(53.0)
    assert bay.notes.infos == [
        'Can launch 53 tons; DM-4 to attack rolls against manoeuvring targets',
    ]


def test_general_purpose_mass_driver_bay_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=8,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        weapons=WeaponsSection(bays=[GeneralPurposeMassDriverBay(extra_launch_capacity=3)]),
    )

    row = my_ship.build_spec().row('Small General-Purpose Mass Driver Bay', section='Weapons')
    assert row.tons == pytest.approx(56.0)
    assert row.cost == pytest.approx(4_225_000.0)
    assert row.power == pytest.approx(-19.0)


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


def test_large_hullcutter_bay_values_and_notes():
    bay = LargeHullcutterBay()
    bay.bind(DummyOwner(16, 10_000))

    assert bay.build_item() == 'Large Hullcutter Bay'
    assert bay.tons == pytest.approx(500.0)
    assert bay.cost == pytest.approx(110_000_000.0)
    assert bay.power == pytest.approx(100.0)
    assert bay.hardpoints_required == 5
    assert bay.notes.infos == [
        'Reductor: target armour is reduced by -1 per damage die before damage is applied',
    ]


def test_large_hullcutter_bay_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=16,
        displacement=10_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        weapons=WeaponsSection(bays=[LargeHullcutterBay()]),
    )

    row = my_ship.build_spec().row('Large Hullcutter Bay', section='Weapons')
    assert row.tons == pytest.approx(500.0)
    assert row.cost == pytest.approx(110_000_000.0)
    assert row.power == pytest.approx(-100.0)


def test_type_ii_laser_point_defense_battery_values():
    battery = LaserPointDefenseBattery2()
    battery.bind(DummyOwner(12, 1_000))
    assert battery.tons == 20.0
    assert battery.cost == 10_000_000
    assert battery.power == 20.0
    assert battery.hardpoints_required == 1


def test_torpedo_interceptor_cluster_values_and_notes():
    cluster = TorpedoInterceptorCluster()
    cluster.bind(DummyOwner(10, 1_000))

    assert cluster.build_item() == 'Torpedo-Interceptor Cluster'
    assert cluster.tons == pytest.approx(1.0)
    assert cluster.cost == pytest.approx(1_000_000.0)
    assert cluster.power == pytest.approx(1.0)
    assert cluster.hardpoints_required == 1
    assert cluster.notes.infos == [
        'One-shot system; must be replaced dockside after firing',
        'Four interceptors; each kills one missile on 6+ or torpedo on 8+',
    ]


def test_torpedo_interceptor_cluster_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=10,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        weapons=WeaponsSection(point_defense_batteries=[TorpedoInterceptorCluster()]),
    )

    row = my_ship.build_spec().row('Torpedo-Interceptor Cluster', section='Weapons')
    assert row.tons == pytest.approx(1.0)
    assert row.cost == pytest.approx(1_000_000.0)
    assert row.power == pytest.approx(-1.0)


def test_plasma_carronade_values_and_notes():
    carronade = PlasmaCarronade()
    carronade.bind(DummyOwner(10, 1_000))

    assert carronade.build_item() == 'Plasma Carronade'
    assert carronade.tons == pytest.approx(4.0)
    assert carronade.cost == pytest.approx(10_000_000.0)
    assert carronade.power == pytest.approx(35.0)
    assert carronade.hardpoints_required == 4
    assert carronade.notes.infos == [
        'Damage: 12D; Weak trait doubles target armour against damage',
    ]


def test_fusion_carronade_values_and_notes():
    carronade = FusionCarronade()
    carronade.bind(DummyOwner(12, 1_000))

    assert carronade.build_item() == 'Fusion Carronade'
    assert carronade.tons == pytest.approx(4.0)
    assert carronade.cost == pytest.approx(12_000_000.0)
    assert carronade.power == pytest.approx(45.0)
    assert carronade.hardpoints_required == 4
    assert carronade.notes.infos == [
        'Damage: 16D; Radiation, Weak trait doubles target armour against damage',
    ]


def test_carronade_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        weapons=WeaponsSection(carronades=[FusionCarronade()]),
    )

    row = my_ship.build_spec().row('Fusion Carronade', section='Weapons')
    assert row.tons == pytest.approx(4.0)
    assert row.cost == pytest.approx(12_000_000.0)
    assert row.power == pytest.approx(-45.0)


def test_carronade_requires_four_hardpoints():
    my_ship = ship.Ship(
        tl=10,
        displacement=300,
        hull=hull.Hull(configuration=hull.standard_hull),
        weapons=WeaponsSection(carronades=[PlasmaCarronade()]),
    )

    assert my_ship.weapons is not None
    errors = my_ship.weapons.carronades[0].notes.errors
    assert 'Exceeds available hardpoints: 4 mounts installed, capacity is 3' in errors


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
            LargeHullcutterBay.model_validate({'tons': 999, 'cost': 999, 'power': 999}),
            500.0,
            110_000_000.0,
            100.0,
        ),
        (
            GeneralPurposeMassDriverBay.model_validate({'tons': 999, 'cost': 999, 'power': 999}),
            50.0,
            4_000_000.0,
            10.0,
        ),
        (
            LaserPointDefenseBattery2.model_validate({'tons': 999, 'cost': 999, 'power': 999}),
            20.0,
            10_000_000.0,
            20.0,
        ),
        (
            TorpedoInterceptorCluster.model_validate({'tons': 999, 'cost': 999, 'power': 999}),
            1.0,
            1_000_000.0,
            1.0,
        ),
        (PlasmaCarronade.model_validate({'tons': 999, 'cost': 999, 'power': 999}), 4.0, 10_000_000.0, 35.0),
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


def test_barbette_intense_focus_is_allowed_for_particle_weapons_and_noted():
    barbette = ParticleBarbette(customisation=VeryAdvanced(modifications=[IntenseFocus]))
    barbette.bind(DummyOwner(13, 400))

    assert 'Intense Focus is only applicable for laser and particle weapons' not in barbette.notes.errors
    assert 'Intense Focus weapons gain AP+2' in barbette.notes.infos


def test_barbette_intense_focus_rejects_plasma_weapons():
    barbette = PlasmaBarbette(customisation=VeryAdvanced(modifications=[IntenseFocus]))
    barbette.bind(DummyOwner(13, 400))

    assert 'Intense Focus is only applicable for laser and particle weapons' in barbette.notes.errors


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


def test_bay_intense_focus_is_allowed_for_particle_weapons_and_noted():
    bay = MediumParticleBeamBay(customisation=VeryAdvanced(modifications=[IntenseFocus]))
    bay.bind(DummyOwner(14, 1_000))

    assert 'Intense Focus is only applicable for laser and particle weapons' not in bay.notes.errors
    assert 'Intense Focus weapons gain AP+2' in bay.notes.infos


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
