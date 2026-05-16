"""Spinward Extents Acrux-class Heavy Cruiser source snapshot.

The source image header says `Acrux Heavy Cruiser`, while the class ribbon says
`Class: Heavy Scout`. The latter is retained here as a source value but treated
as a likely layout/copy error until a text source confirms otherwise.

This is a capstone validation case that is intentionally being made buildable
one subsystem at a time. It exercises several systems that are not fully
modelled yet, including command bridges at capital-ship scale and large craft
berthing.
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import ComputerSection, Core50, Core60
from ceres.make.ship.crafts import CraftSection, EmptyOccupant, FullHangar, InternalDockingSpace
from ceres.make.ship.drives import DriveSection, FusionPlantTL8, JDrive2, MDrive5, PowerSection
from ceres.make.ship.habitation import Barracks, Brig, HabitationSection, HighStateroom, LowBerth, Stateroom
from ceres.make.ship.parts import HighTechnology, SizeReduction, VeryAdvanced
from ceres.make.ship.sensors import ExtendedArrays, MilitarySensors, SensorsSection
from ceres.make.ship.software import (
    AdvancedFireControl,
    AntiHijack,
    AutoRepair,
    BattleSystem,
    ElectronicWarfare,
    Evade,
    LaunchSolution,
    VirtualCrew,
)
from ceres.make.ship.spec import SpecSection
from ceres.make.ship.storage import (
    CargoCrane,
    CargoHold,
    CargoSection,
    FuelProcessor,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import (
    Armoury,
    BriefingRoom,
    CommonArea,
    MedicalBay,
    RepairDrones,
    SystemsSection,
    TrainingFacility,
    UNREPSystem,
    Workshop,
)
from ceres.make.ship.weapons import (
    BeamLaser,
    LargeMissileBay,
    LargeTorpedoBay,
    LaserPointDefenseBattery1,
    LongRange,
    MediumParticleBeamBay,
    MissileStorage,
    ParticleAcceleratorSpinalMount,
    ParticleBarbette,
    PlasmaBarbette,
    PulseLaser,
    Sandcaster,
    SandcasterCanisterStorage,
    TorpedoStorage,
    TripleTurret,
    WeaponsSection,
)

_expected = SimpleNamespace(
    source='Spinward Extents',
    ship_class='Acrux',
    ship_type='Heavy Cruiser',
    source_class_ribbon='Heavy Scout',
    source_class_ribbon_note='Likely source layout/copy error; title and caption say Acrux Heavy Cruiser.',
    tl=11,
    displacement=50_000,
    hull_description='50,000 tons, Close Structure, Reinforced, Radiation Shielding',
    hull_cost_mcr=4_625.0,
    hull_points=30_250,
    running_cost_maintenance_mcr=2.102215,
    purchase_cost_mcr=25_226.575,
    rows=(
        SimpleNamespace(section='Hull', item='50,000 tons, Close Structure, Reinforced', tons=None, cost_mcr=3375.0),
        SimpleNamespace(section='Hull', item='Radiation Shielding', tons=None, cost_mcr=1250.0),
        SimpleNamespace(section='Armour', item='Crystaliron, Armour 11', tons=6875.0, cost_mcr=1856.25),
        SimpleNamespace(section='M-Drive', item='Thrust 5', tons=2500.0, cost_mcr=5000.0),
        SimpleNamespace(section='J-Drive', item='Jump 2', tons=2505.0, cost_mcr=3757.5),
        SimpleNamespace(
            section='Power Plant', item='Fusion (TL8) (size reduction x3), Power: 52,500', tons=3676.0, cost_mcr=2756.25
        ),
        SimpleNamespace(section='Fuel Tanks', item='J-2, 8 weeks of operation', tons=10735.0, cost_mcr=None),
        SimpleNamespace(section='Bridge', item='Holographic Controls', tons=60.0, cost_mcr=312.5),
        SimpleNamespace(section='Bridge', item='Command, Holographic Controls', tons=80.0, cost_mcr=468.75),
        SimpleNamespace(section='Computer', item='Core/60 (primary)', tons=None, cost_mcr=75.0),
        SimpleNamespace(section='Computer', item='Core/50 (backup)', tons=None, cost_mcr=60.0),
        SimpleNamespace(section='Sensors', item='Military Grade x2', tons=4.0, cost_mcr=8.2),
        SimpleNamespace(section='Sensors', item='Distributed Arrays x2', tons=8.0, cost_mcr=16.4),
        SimpleNamespace(section='Sensors', item='Improved Signal Processing x2', tons=2.0, cost_mcr=8.0),
        SimpleNamespace(section='Weapons', item='Particle Accelerator Spinal Mount', tons=7000.0, cost_mcr=2000.0),
        SimpleNamespace(
            section='Weapons', item='Large Missile Bays (size reduction x3) x5', tons=1750.0, cost_mcr=937.5
        ),
        SimpleNamespace(
            section='Weapons', item='Large Torpedo Bays (size reduction x2) x5', tons=2000.0, cost_mcr=187.5
        ),
        SimpleNamespace(section='Weapons', item='Medium Particle Beam Bays x10', tons=1000.0, cost_mcr=400.0),
        SimpleNamespace(section='Weapons', item='Particle Barbettes x50', tons=250.0, cost_mcr=400.0),
        SimpleNamespace(section='Weapons', item='Plasma Barbettes x40', tons=200.0, cost_mcr=200.0),
        SimpleNamespace(
            section='Weapons', item='Triple Turrets (long range pulse lasers) x120', tons=120.0, cost_mcr=570.0
        ),
        SimpleNamespace(section='Weapons', item='Triple Turrets (beam lasers) x90', tons=90.0, cost_mcr=225.0),
        SimpleNamespace(section='Weapons', item='Triple Turrets (sandcasters) x60', tons=60.0, cost_mcr=105.0),
        SimpleNamespace(section='Weapons', item='Point Defence Batteries (type I) x10', tons=200.0, cost_mcr=50.0),
        SimpleNamespace(section='Ammunition', item='Missile Storage (28,800 missiles)', tons=2400.0, cost_mcr=None),
        SimpleNamespace(section='Ammunition', item='Torpedo Storage (7,200 torpedoes)', tons=2400.0, cost_mcr=None),
        SimpleNamespace(section='Ammunition', item='Sandcaster Storage (4,800 canisters)', tons=240.0, cost_mcr=None),
        SimpleNamespace(section='Systems', item='Fuel Scoops', tons=None, cost_mcr=1.0),
        SimpleNamespace(section='Systems', item='Fuel Processor (5,000 tons/day)', tons=250.0, cost_mcr=12.5),
        SimpleNamespace(section='Systems', item='Emergency Power', tons=367.5, cost_mcr=275.625),
        SimpleNamespace(section='Systems', item='Repair Drones', tons=500.0, cost_mcr=100.0),
        SimpleNamespace(section='Systems', item='Barracks (150 troops)', tons=300.0, cost_mcr=15.0),
        SimpleNamespace(section='Systems', item='Brigs x4', tons=16.0, cost_mcr=1.0),
        SimpleNamespace(section='Systems', item='Armoury', tons=50.0, cost_mcr=12.5),
        SimpleNamespace(section='Systems', item='Briefing Rooms x4', tons=16.0, cost_mcr=2.0),
        SimpleNamespace(section='Systems', item='Cargo Crane', tons=4.0, cost_mcr=4.0),
        SimpleNamespace(section='Systems', item='Medical Bays x6', tons=24.0, cost_mcr=12.0),
        SimpleNamespace(section='Systems', item='Training Facilities (50 personnel)', tons=100.0, cost_mcr=20.0),
        SimpleNamespace(section='Systems', item='UNREP System (500 tons/hour)', tons=25.0, cost_mcr=12.5),
        SimpleNamespace(section='Systems', item='Workshops x17', tons=102.0, cost_mcr=15.3),
        SimpleNamespace(section='Craft', item='Docking Space (1080 tons)', tons=1188.0, cost_mcr=297.0),
        SimpleNamespace(section='Craft', item='Full Hangar (360 tons)', tons=720.0, cost_mcr=144.0),
        SimpleNamespace(section='Staterooms', item='Standard x272', tons=1088.0, cost_mcr=136.0),
        SimpleNamespace(section='Staterooms', item='High x4', tons=24.0, cost_mcr=3.2),
        SimpleNamespace(section='Staterooms', item='Additional Crew (standard) x65', tons=260.0, cost_mcr=32.5),
        SimpleNamespace(section='Staterooms', item='Additional Crew (high) x5', tons=30.0, cost_mcr=4.0),
        SimpleNamespace(section='Staterooms', item='Low Berths x20', tons=10.0, cost_mcr=1.0),
        SimpleNamespace(section='Software', item='Manoeuvre/0', tons=None, cost_mcr=None),
        SimpleNamespace(section='Software', item='Library', tons=None, cost_mcr=None),
        SimpleNamespace(section='Software', item='Intellect', tons=None, cost_mcr=1.0),
        SimpleNamespace(section='Software', item='Auto-Repair/1', tons=None, cost_mcr=5.0),
        SimpleNamespace(section='Software', item='Evade/2', tons=None, cost_mcr=2.0),
        SimpleNamespace(section='Software', item='Advanced Fire Control/1', tons=None, cost_mcr=12.0),
        SimpleNamespace(section='Software', item='Anti-Hijack/1', tons=None, cost_mcr=6.0),
        SimpleNamespace(section='Software', item='Battle System/1', tons=None, cost_mcr=18.0),
        SimpleNamespace(section='Software', item='Electronic Warfare/1', tons=None, cost_mcr=15.0),
        SimpleNamespace(section='Software', item='Launch Solution/2', tons=None, cost_mcr=12.0),
        SimpleNamespace(section='Software', item='Virtual Crew/0', tons=None, cost_mcr=1.0),
        SimpleNamespace(section='Common Areas', item='Common Areas', tons=346.0, cost_mcr=34.6),
        SimpleNamespace(section='Cargo', item='Cargo', tons=424.5, cost_mcr=None),
    ),
    crew=(
        'Captain',
        'Officers x41',
        'Pilots x3',
        'Astrogator',
        'Medics x6',
        'Maintenance x33',
        'Engineers x83',
        "Ship's Troops x150",
        'Administrators x16',
        'Gunners x277',
    ),
    power_requirements=SimpleNamespace(
        basic_ship_systems=10_000,
        manoeuvre_drive=25_000,
        jump_drive=10_000,
        sensors=10,
        weapons=6_945,
    ),
    expected_errors=[],
    expected_warnings=[],
    unimplemented_reasons=(),
)

# Not yet implemented in Ceres.
_expected.unimplemented_reasons = ('command bridge source row is not the same part as the Ceres CommandBridge system',)
_expected.expected_current_ship_errors = []
_expected.expected_spec_errors = [
    'Requires TL12, ship is TL11',
]
_expected.expected_spec_warnings = [
    'No Jump Control software',
    'Recommended common area is 350.50 tons',
    'Cargo is below recommended 100-day stores capacity of 500 tons',
]


def _source_row(section: str, item: str):
    return next(row for row in _expected.rows if row.section == section and row.item == item)


def _ship_row(spec, section: str, item: str):
    section_map = {
        'Ammunition': SpecSection.WEAPONS,
        'Armour': SpecSection.HULL,
        'Common Areas': SpecSection.HABITATION,
        'Fuel Tanks': SpecSection.FUEL,
        'Bridge': SpecSection.COMMAND,
        'J-Drive': SpecSection.JUMP,
        'M-Drive': SpecSection.PROPULSION,
        'Power Plant': SpecSection.POWER,
        'Software': SpecSection.COMPUTER,
        'Staterooms': SpecSection.HABITATION,
    }
    return spec.row(item, section=section_map.get(section, section))


def _source_sum(*rows: tuple[str, str]):
    tons = 0.0
    cost_mcr = 0.0
    for section, item in rows:
        row = _source_row(section, item)
        if row.tons is not None:
            tons += row.tons
        if row.cost_mcr is not None:
            cost_mcr += row.cost_mcr
    return SimpleNamespace(tons=tons, cost_mcr=cost_mcr)


def _assert_row_matches_source(spec, *, source_section: str, source_item: str, ship_section: str, ship_item: str):
    source = _source_row(source_section, source_item)
    row = _ship_row(spec, ship_section, ship_item)
    if source.tons is not None:
        assert row.tons == pytest.approx(source.tons)
    if source.cost_mcr is not None:
        assert row.cost == pytest.approx(source.cost_mcr * 1_000_000)


def _size_reduction(steps: int):
    if steps == 2:
        return VeryAdvanced(modifications=[SizeReduction, SizeReduction])
    if steps == 3:
        return HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction])
    raise ValueError(f'Acrux only uses size reduction x2/x3, got x{steps}')


def build_acrux_heavy_cruiser():
    pulse_long_range = VeryAdvanced(modifications=[LongRange])
    # The Spinward Extents source rows apply the close-structure hull cost but
    # do not apply the HG close-structure armour volume modifier to armour tons.
    close_reinforced = hull.close_structure.model_copy(update={'reinforced': True, 'armour_volume_modifier': 1.0})
    fusion_plant = FusionPlantTL8(output=52_500, customisation=_size_reduction(3))

    return ship.Ship(
        ship_class=_expected.ship_class,
        ship_type=_expected.ship_type,
        military=True,
        tl=_expected.tl,
        displacement=_expected.displacement,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(
            configuration=close_reinforced,
            armour=armour.CrystalironArmour(protection=11),
            radiation_shielding=True,
        ),
        drives=DriveSection(m_drive=MDrive5(), j_drive=JDrive2()),
        power=PowerSection(plant=fusion_plant),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=8),
            fuel_processor=FuelProcessor(tons=250),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Core60(),
            backup_hardware=Core50(),
            software=[
                AutoRepair(rating=1),
                Evade(rating=2),
                AdvancedFireControl(rating=1),
                AntiHijack(rating=1),
                BattleSystem(rating=1),
                ElectronicWarfare(rating=1),
                LaunchSolution(rating=2),
                VirtualCrew(rating=0),
            ],
        ),
        sensors=SensorsSection(primary=MilitarySensors(), extended_arrays=ExtendedArrays()),
        weapons=WeaponsSection(
            spinal_mounts=[ParticleAcceleratorSpinalMount(size_multiple=2)],
            bays=[
                *[LargeMissileBay(customisation=_size_reduction(3)) for _ in range(5)],
                *[LargeTorpedoBay(customisation=_size_reduction(2)) for _ in range(5)],
                *[MediumParticleBeamBay() for _ in range(10)],
            ],
            barbettes=[
                *[ParticleBarbette() for _ in range(50)],
                *[PlasmaBarbette() for _ in range(40)],
            ],
            turrets=[
                *[
                    TripleTurret(
                        weapons=[
                            PulseLaser(customisation=pulse_long_range),
                            PulseLaser(customisation=pulse_long_range),
                            PulseLaser(customisation=pulse_long_range),
                        ]
                    )
                    for _ in range(120)
                ],
                *[TripleTurret(weapons=[BeamLaser(), BeamLaser(), BeamLaser()]) for _ in range(90)],
                *[TripleTurret(weapons=[Sandcaster(), Sandcaster(), Sandcaster()]) for _ in range(60)],
            ],
            point_defense_batteries=[LaserPointDefenseBattery1() for _ in range(10)],
            missile_storage=MissileStorage(count=28_800),
            torpedo_storage=TorpedoStorage(count=7_200),
            sandcaster_canister_storage=SandcasterCanisterStorage(count=4_800),
        ),
        craft=CraftSection(
            internal_housing=[
                InternalDockingSpace(craft=EmptyOccupant(docking_space=1080)),
                FullHangar(craft=EmptyOccupant(docking_space=360)),
            ]
        ),
        habitation=HabitationSection(
            staterooms=[*[Stateroom() for _ in range(337)], *[HighStateroom() for _ in range(9)]],
            low_berths=[LowBerth() for _ in range(20)],
            brigs=[Brig() for _ in range(4)],
            barracks=[Barracks(tons=300, occupants='150 troops')],
            common_area=CommonArea(tons=346),
        ),
        systems=SystemsSection(
            internal_systems=[
                *[Armoury() for _ in range(50)],
                *[BriefingRoom() for _ in range(4)],
                *[MedicalBay() for _ in range(6)],
                TrainingFacility(trainees=50),
                UNREPSystem(tons=25),
                *[Workshop() for _ in range(17)],
            ],
            drones=[RepairDrones()],
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=428.5, crane=CargoCrane())]),
    )


def test_acrux_heavy_cruiser_source_snapshot():
    assert _expected.source == 'Spinward Extents'
    assert _expected.ship_class == 'Acrux'
    assert _expected.ship_type == 'Heavy Cruiser'
    assert _expected.source_class_ribbon == 'Heavy Scout'
    assert _expected.tl == 11
    assert _expected.displacement == 50_000
    assert _expected.hull_points == 30_250
    assert _expected.expected_errors == []
    assert _expected.expected_warnings == []


def test_acrux_heavy_cruiser_builds_with_current_supported_parts():
    acrux = build_acrux_heavy_cruiser()

    assert acrux.ship_class == _expected.ship_class
    assert acrux.ship_type == _expected.ship_type
    assert acrux.tl == _expected.tl
    assert acrux.displacement == _expected.displacement


def test_acrux_heavy_cruiser_has_no_unexpected_ship_notes():
    acrux = build_acrux_heavy_cruiser()

    assert acrux.notes.errors == _expected.expected_current_ship_errors
    assert acrux.notes.warnings == _expected.expected_warnings


def test_acrux_heavy_cruiser_has_no_unexpected_spec_warnings():
    spec = build_acrux_heavy_cruiser().build_spec()

    errors = [note.message for row in spec.rows for note in row.notes if note.category == 'error']
    warnings = [note.message for row in spec.rows for note in row.notes if note.category == 'warning']

    assert errors == _expected.expected_spec_errors
    assert warnings == _expected.expected_spec_warnings


def test_acrux_heavy_cruiser_supported_spec_rows_match_source():
    spec = build_acrux_heavy_cruiser().build_spec()

    for section, item in [
        ('Armour', 'Crystaliron, Armour: 11'),
        ('M-Drive', 'M-Drive 5'),
        ('J-Drive', 'Jump 2'),
        ('Fuel Tanks', 'J-2, 8 weeks of operation'),
        ('Fuel Tanks', 'Fuel Processor (5000 tons/day)'),
        ('Bridge', 'Holographic Controls'),
        ('Computer', 'Core/60'),
        ('Computer', 'Backup Core/50'),
        ('Weapons', 'Particle Accelerator Spinal Mount'),
        ('Weapons', 'Medium Particle Beam Bay (Damage × 20 after armour)'),
        ('Systems', 'Repair Drones'),
        ('Systems', 'Armoury'),
        ('Systems', 'Briefing Room'),
        ('Systems', 'Medical Bay'),
        ('Systems', 'Training Facility: 50-person capacity'),
        ('Systems', 'UNREP System (500 tons/hour)'),
        ('Systems', 'Workshop'),
        ('Craft', 'Docking Space (1080 tons)'),
        ('Craft', 'Full Hangar (360 tons)'),
        ('Staterooms', 'Barracks (150 troops)'),
        ('Staterooms', 'Brigs'),
        ('Habitation', 'Common Area'),
        ('Weapons', 'Point Defence Laser Battery Type I'),
        ('Ammunition', 'Missile Storage (28800)'),
        ('Ammunition', 'Torpedo Storage (7200)'),
        ('Ammunition', 'Sandcaster Canister Storage (4800)'),
        ('Cargo', 'Cargo Hold'),
        ('Cargo', 'Cargo Crane'),
    ]:
        assert _ship_row(spec, section, item).item == item


def test_acrux_heavy_cruiser_key_source_values_that_match_current_ceres():
    spec = build_acrux_heavy_cruiser().build_spec()

    for source_section, source_item, ship_section, ship_item in [
        ('Hull', 'Radiation Shielding', 'Hull', 'Radiation Shielding: Reduce Rads by 1,000'),
        ('M-Drive', 'Thrust 5', 'M-Drive', 'M-Drive 5'),
        ('J-Drive', 'Jump 2', 'J-Drive', 'Jump 2'),
        ('Systems', 'Fuel Processor (5,000 tons/day)', 'Fuel Tanks', 'Fuel Processor (5000 tons/day)'),
        ('Bridge', 'Holographic Controls', 'Bridge', 'Holographic Controls'),
        ('Computer', 'Core/60 (primary)', 'Computer', 'Core/60'),
        ('Computer', 'Core/50 (backup)', 'Computer', 'Backup Core/50'),
        ('Software', 'Auto-Repair/1', 'Software', 'Auto-Repair/1'),
        ('Software', 'Evade/2', 'Software', 'Evade/2'),
        ('Software', 'Advanced Fire Control/1', 'Software', 'Advanced Fire Control/1'),
        ('Software', 'Anti-Hijack/1', 'Software', 'Anti-Hijack/1'),
        ('Software', 'Battle System/1', 'Software', 'Battle System/1'),
        ('Software', 'Electronic Warfare/1', 'Software', 'Electronic Warfare/1'),
        ('Software', 'Launch Solution/2', 'Software', 'Launch Solution/2'),
        ('Software', 'Virtual Crew/0', 'Software', 'Virtual Crew/0'),
        ('Systems', 'Repair Drones', 'Systems', 'Repair Drones'),
        ('Systems', 'Barracks (150 troops)', 'Staterooms', 'Barracks (150 troops)'),
        ('Systems', 'Armoury', 'Systems', 'Armoury'),
        ('Systems', 'Brigs x4', 'Staterooms', 'Brigs'),
        ('Systems', 'Briefing Rooms x4', 'Systems', 'Briefing Room'),
        ('Systems', 'Cargo Crane', 'Cargo', 'Cargo Crane'),
        ('Systems', 'Medical Bays x6', 'Systems', 'Medical Bay'),
        ('Systems', 'Training Facilities (50 personnel)', 'Systems', 'Training Facility: 50-person capacity'),
        ('Systems', 'UNREP System (500 tons/hour)', 'Systems', 'UNREP System (500 tons/hour)'),
        ('Systems', 'Workshops x17', 'Systems', 'Workshop'),
        ('Craft', 'Docking Space (1080 tons)', 'Craft', 'Docking Space (1080 tons)'),
        ('Craft', 'Full Hangar (360 tons)', 'Craft', 'Full Hangar (360 tons)'),
        ('Staterooms', 'Low Berths x20', 'Staterooms', 'Low Berths'),
        ('Common Areas', 'Common Areas', 'Common Areas', 'Common Area'),
        ('Cargo', 'Cargo', 'Cargo', 'Cargo Hold'),
    ]:
        _assert_row_matches_source(
            spec,
            source_section=source_section,
            source_item=source_item,
            ship_section=ship_section,
            ship_item=ship_item,
        )

    source_fuel = _source_row('Fuel Tanks', 'J-2, 8 weeks of operation')
    fuel_row = _ship_row(spec, 'Fuel Tanks', 'J-2, 8 weeks of operation')
    assert fuel_row.tons == pytest.approx(source_fuel.tons)

    # The source armour tonnage is consistent across Spinward Extents examples,
    # but its cost factor is not yet traced to an HG rule.
    source_armour = _source_row('Armour', 'Crystaliron, Armour 11')
    armour_row = _ship_row(spec, 'Armour', 'Crystaliron, Armour: 11')
    assert armour_row.tons == pytest.approx(source_armour.tons)

    standard_staterooms = _source_sum(
        ('Staterooms', 'Standard x272'),
        ('Staterooms', 'Additional Crew (standard) x65'),
    )
    stateroom_row = _ship_row(spec, 'Staterooms', 'Staterooms')
    assert stateroom_row.quantity == 337
    assert stateroom_row.tons == pytest.approx(standard_staterooms.tons)
    assert stateroom_row.cost == pytest.approx(standard_staterooms.cost_mcr * 1_000_000)

    high_staterooms = _source_sum(
        ('Staterooms', 'High x4'),
        ('Staterooms', 'Additional Crew (high) x5'),
    )
    high_stateroom_row = _ship_row(spec, 'Staterooms', 'High Staterooms')
    assert high_stateroom_row.quantity == 9
    assert high_stateroom_row.tons == pytest.approx(high_staterooms.tons)
    assert high_stateroom_row.cost == pytest.approx(high_staterooms.cost_mcr * 1_000_000)


def test_acrux_heavy_cruiser_supported_weapon_tonnage_matches_source():
    spec = build_acrux_heavy_cruiser().build_spec()

    source_spinal_mount = _source_row('Weapons', 'Particle Accelerator Spinal Mount')
    spinal_mount = _ship_row(spec, 'Weapons', 'Particle Accelerator Spinal Mount')
    assert spinal_mount.tons == pytest.approx(source_spinal_mount.tons)
    assert spinal_mount.cost == pytest.approx(source_spinal_mount.cost_mcr * 1_000_000)

    source_large_missiles = _source_row('Weapons', 'Large Missile Bays (size reduction x3) x5')
    large_missiles = _ship_row(spec, 'Weapons', 'Large Missile Bay (120 missiles per salvo)')
    assert large_missiles.quantity == 5
    assert large_missiles.tons == pytest.approx(source_large_missiles.tons)

    source_large_torpedoes = _source_row('Weapons', 'Large Torpedo Bays (size reduction x2) x5')
    large_torpedoes = _ship_row(spec, 'Weapons', 'Large Torpedo Bay (30 torpedoes per salvo)')
    assert large_torpedoes.quantity == 5
    assert large_torpedoes.tons == pytest.approx(source_large_torpedoes.tons)

    source_particle_barbettes = _source_row('Weapons', 'Particle Barbettes x50')
    particle_barbettes = _ship_row(spec, 'Weapons', 'Particle Barbette (Damage × 3 after armour)')
    assert particle_barbettes.quantity == 50
    assert particle_barbettes.tons == pytest.approx(source_particle_barbettes.tons)

    source_plasma_barbettes = _source_row('Weapons', 'Plasma Barbettes x40')
    plasma_barbettes = _ship_row(spec, 'Weapons', 'Plasma Barbette (Damage × 3 after armour)')
    assert plasma_barbettes.quantity == 40
    assert plasma_barbettes.tons == pytest.approx(source_plasma_barbettes.tons)

    source_particle_bays = _source_row('Weapons', 'Medium Particle Beam Bays x10')
    particle_bays = _ship_row(spec, 'Weapons', 'Medium Particle Beam Bay (Damage × 20 after armour)')
    assert particle_bays.quantity == 10
    assert particle_bays.tons == pytest.approx(source_particle_bays.tons)
    assert particle_bays.cost == pytest.approx(source_particle_bays.cost_mcr * 1_000_000)

    source_pulse_turrets = _source_row('Weapons', 'Triple Turrets (long range pulse lasers) x120')
    pulse_turrets = spec.rows_matching('Triple Turret')[0]
    assert pulse_turrets.quantity == 120
    assert pulse_turrets.tons == pytest.approx(source_pulse_turrets.tons)
    assert pulse_turrets.cost == pytest.approx(source_pulse_turrets.cost_mcr * 1_000_000)

    source_beam_turrets = _source_row('Weapons', 'Triple Turrets (beam lasers) x90')
    beam_turrets = spec.rows_matching('Triple Turret')[1]
    assert beam_turrets.quantity == 90
    assert beam_turrets.tons == pytest.approx(source_beam_turrets.tons)
    assert beam_turrets.cost == pytest.approx(source_beam_turrets.cost_mcr * 1_000_000)

    source_sand_turrets = _source_row('Weapons', 'Triple Turrets (sandcasters) x60')
    sand_turrets = spec.rows_matching('Triple Turret')[2]
    assert sand_turrets.quantity == 60
    assert sand_turrets.tons == pytest.approx(source_sand_turrets.tons)
    assert sand_turrets.cost == pytest.approx(source_sand_turrets.cost_mcr * 1_000_000)

    source_point_defence = _source_row('Weapons', 'Point Defence Batteries (type I) x10')
    point_defence = _ship_row(spec, 'Weapons', 'Point Defence Laser Battery Type I')
    assert point_defence.quantity == 10
    assert point_defence.tons == pytest.approx(source_point_defence.tons)
    assert point_defence.cost == pytest.approx(source_point_defence.cost_mcr * 1_000_000)

    source_missile_storage = _source_row('Ammunition', 'Missile Storage (28,800 missiles)')
    missile_storage = _ship_row(spec, 'Ammunition', 'Missile Storage (28800)')
    assert missile_storage.tons == pytest.approx(source_missile_storage.tons)

    source_torpedo_storage = _source_row('Ammunition', 'Torpedo Storage (7,200 torpedoes)')
    torpedo_storage = _ship_row(spec, 'Ammunition', 'Torpedo Storage (7200)')
    assert torpedo_storage.tons == pytest.approx(source_torpedo_storage.tons)

    source_sandcaster_storage = _source_row('Ammunition', 'Sandcaster Storage (4,800 canisters)')
    sandcaster_storage = _ship_row(spec, 'Ammunition', 'Sandcaster Canister Storage (4800)')
    assert sandcaster_storage.tons == pytest.approx(source_sandcaster_storage.tons)
