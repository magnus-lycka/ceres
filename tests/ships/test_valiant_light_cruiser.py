"""High Guard Valiant-class Light Cruiser source snapshot."""

from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import ComputerSection, Core100
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, SpaceCraft
from ceres.make.ship.drives import DecreasedFuel, DriveSection, FusionPlantTL15, JDrive4, MDrive5, PowerSection
from ceres.make.ship.habitation import HabitationSection, HighStateroom, Stateroom
from ceres.make.ship.parts import Advanced, HighTechnology, SizeReduction
from ceres.make.ship.screens import NuclearDamper, ScreensSection
from ceres.make.ship.sensors import (
    AdvancedSensors,
    EnhancedSignalProcessing,
    ExtendedArrays,
    MilitaryCountermeasuresSuite,
    SensorsSection,
)
from ceres.make.ship.software import (
    AdvancedFireControl,
    AntiHijack,
    BattleSystem,
    BroadSpectrumEW,
    ElectronicWarfare,
    LaunchSolution,
    PointDefence,
)
from ceres.make.ship.spec import SpecSection
from ceres.make.ship.storage import (
    CargoHold,
    CargoSection,
    FuelProcessor,
    FuelScoops,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import (
    Armoury,
    BriefingRoom,
    CommandBridge,
    CommonArea,
    MedicalBay,
    SystemsSection,
    Workshop,
)
from ceres.make.ship.weapons import (
    BeamLaser,
    LaserPointDefenseBattery2,
    MediumRepulsorBay,
    MesonSpinalMount,
    MissileRack,
    MissileStorage,
    Sandcaster,
    SandcasterCanisterStorage,
    TripleTurret,
    WeaponsSection,
)

_expected = SimpleNamespace(
    source='High Guard',
    ship_class='Valiant',
    ship_type='Light Cruiser',
    tl=15,
    displacement=30_000,
    hull_points=16_500,
    running_cost_maintenance_mcr=1.556925,
    purchase_cost_mcr=18_683.1,
    table_total_cost_mcr=20_759.0,
    rows=(
        SimpleNamespace(section='Hull', item='30,000 tons, Standard', tons=None, cost_mcr=1_500.0),
        SimpleNamespace(section='Hull', item='Reinforced', tons=None, cost_mcr=750.0),
        SimpleNamespace(section='Armour', item='Bonded Superdense: 15', tons=3_600.0, cost_mcr=1_800.0),
        SimpleNamespace(section='Armour', item='Radiation Shielding', tons=None, cost_mcr=750.0),
        SimpleNamespace(section='M-Drive', item='Thrust 5 (size reduction x3)', tons=1_050.0, cost_mcr=4_500.0),
        SimpleNamespace(section='J-Drive', item='Jump 4 (decreased fuel)', tons=3_005.0, cost_mcr=4_958.25),
        SimpleNamespace(section='Power Plant', item='Fusion (TL15), Power 24,000', tons=1_200.0, cost_mcr=2_400.0),
        SimpleNamespace(section='Fuel Tanks', item='J-4, 8 weeks of operation', tons=11_640.0, cost_mcr=None),
        SimpleNamespace(section='Bridge', item='Holographic Controls', tons=60.0, cost_mcr=187.5),
        SimpleNamespace(section='Bridge', item='Command Bridge', tons=40.0, cost_mcr=30.0),
        SimpleNamespace(section='Computer', item='Core/100fib', tons=None, cost_mcr=195.0),
        SimpleNamespace(section='Sensors', item='Advanced', tons=5.0, cost_mcr=5.3),
        SimpleNamespace(section='Sensors', item='Distributed Arrays', tons=10.0, cost_mcr=10.6),
        SimpleNamespace(section='Sensors', item='Enhanced Signal Processing', tons=2.0, cost_mcr=8.0),
        SimpleNamespace(section='Sensors', item='Military Countermeasures Suite', tons=15.0, cost_mcr=28.0),
        SimpleNamespace(section='Weapons', item='Meson Spinal Mount (TL15)', tons=6_000.0, cost_mcr=2_600.0),
        SimpleNamespace(section='Weapons', item='Medium Repulsor Bay', tons=100.0, cost_mcr=60.0),
        SimpleNamespace(section='Weapons', item='Triple Turrets (missile racks) x160', tons=160.0, cost_mcr=520.0),
        SimpleNamespace(section='Weapons', item='Triple Turrets (beam lasers) x50', tons=50.0, cost_mcr=187.5),
        SimpleNamespace(section='Weapons', item='Triple Turrets (sandcasters) x25', tons=25.0, cost_mcr=43.75),
        SimpleNamespace(section='Weapons', item='Point Defence Laser Batteries (Type II) x4', tons=80.0, cost_mcr=40.0),
        SimpleNamespace(section='Ammunition', item='Missile Storage (9,600 missiles)', tons=800.0, cost_mcr=None),
        SimpleNamespace(
            section='Ammunition', item='Sandcaster Canister Storage (1,320 canisters)', tons=66.0, cost_mcr=None
        ),
        SimpleNamespace(section='Screens', item='Nuclear Dampers (size reduction x3) x9', tons=63.0, cost_mcr=135.0),
        SimpleNamespace(section='Craft', item='Docking Spaces (50 tons) x5', tons=275.0, cost_mcr=68.75),
        SimpleNamespace(section='Craft', item='Modular Cutters x5', tons=None, cost_mcr=59.65),
        SimpleNamespace(section='Systems', item='Armoury', tons=18.0, cost_mcr=4.5),
        SimpleNamespace(section='Systems', item='Briefing Rooms x2', tons=8.0, cost_mcr=1.0),
        SimpleNamespace(section='Systems', item='Fuel Processor (1,000 tons/day)', tons=50.0, cost_mcr=2.5),
        SimpleNamespace(section='Systems', item='Fuel Scoops', tons=None, cost_mcr=1.0),
        SimpleNamespace(section='Systems', item='Medical Bays x4', tons=16.0, cost_mcr=8.0),
        SimpleNamespace(section='Systems', item='Workshops x2', tons=12.0, cost_mcr=1.8),
        SimpleNamespace(section='Staterooms', item='High', tons=6.0, cost_mcr=0.8),
        SimpleNamespace(section='Staterooms', item='Standard x265', tons=1_060.0, cost_mcr=132.5),
        SimpleNamespace(section='Software', item='Advanced Fire Control/2', tons=None, cost_mcr=15.0),
        SimpleNamespace(section='Software', item='Anti-Hijack/3', tons=None, cost_mcr=10.0),
        SimpleNamespace(section='Software', item='Battle System/2', tons=None, cost_mcr=24.0),
        SimpleNamespace(section='Software', item='Broad Spectrum EW', tons=None, cost_mcr=14.0),
        SimpleNamespace(section='Software', item='Electronic Warfare/1', tons=None, cost_mcr=15.0),
        SimpleNamespace(section='Software', item='Intellect', tons=None, cost_mcr=None),
        SimpleNamespace(section='Software', item='Launch Solution/3', tons=None, cost_mcr=16.0),
        SimpleNamespace(section='Software', item='Library', tons=None, cost_mcr=None),
        SimpleNamespace(section='Software', item='Manoeuvre', tons=None, cost_mcr=None),
        SimpleNamespace(section='Software', item='Point Defence/2', tons=None, cost_mcr=12.0),
        SimpleNamespace(section='Common Areas', item='Common Areas', tons=267.0, cost_mcr=26.7),
        SimpleNamespace(section='Cargo', item='Cargo', tons=317.0, cost_mcr=None),
    ),
    power_requirements=SimpleNamespace(
        basic_ship_systems=6_000,
        manoeuvre_drive=15_000,
        jump_drive=12_000,
        sensors=22,
        weapons=2_015,
        screens=180,
        fuel_processor=50,
    ),
    expected_errors=[],
    expected_warnings=[],
    unimplemented_reasons=(),
)

# Not yet implemented in Ceres.
_expected.unimplemented_reasons = (
    'Triple Turrets (beam lasers) cost does not match the current Ceres beam-laser turret model',
    'Source purchase cost, table total, and row total disagree with each other',
    'Source crew and running cost manifests are recorded in the source but not asserted here yet',
    'Source lists Jump Control/4 at zero cost; Ceres omits it because JC is hardware-integrated in Core computers',
)


def _source_row(section: str, item: str):
    return next(row for row in _expected.rows if row.section == section and row.item == item)


def _ship_row(spec, section: str, item: str):
    section_map = {
        'Ammunition': SpecSection.WEAPONS,
        'Armour': SpecSection.HULL,
        'Bridge': SpecSection.COMMAND,
        'Common Areas': SpecSection.HABITATION,
        'Fuel Tanks': SpecSection.FUEL,
        'J-Drive': SpecSection.JUMP,
        'M-Drive': SpecSection.PROPULSION,
        'Power Plant': SpecSection.POWER,
        'Screens': SpecSection.SCREENS,
        ('Bridge', 'Command Bridge'): SpecSection.SYSTEMS,
        ('Systems', 'Fuel Processor (1,000 tons/day)'): SpecSection.FUEL,
        ('Systems', 'Fuel Scoops'): SpecSection.FUEL,
        'Software': SpecSection.COMPUTER,
        'Staterooms': SpecSection.HABITATION,
    }
    item_map = {
        ('Armour', 'Bonded Superdense: 15'): 'Bonded Superdense, Armour: 15',
        ('Armour', 'Radiation Shielding'): 'Radiation Shielding: Reduce Rads by 1,000',
        ('M-Drive', 'Thrust 5 (size reduction x3)'): 'M-Drive 5',
        ('J-Drive', 'Jump 4 (decreased fuel)'): 'Jump 4',
        ('Power Plant', 'Fusion (TL15), Power 24,000'): 'Fusion (TL 15), Power 24000',
        ('Fuel Tanks', 'J-4, 8 weeks of operation'): 'J-4, 8 weeks of operation',
        ('Bridge', 'Command Bridge'): 'Command Bridge',
        ('Computer', 'Core/100fib'): 'Core/100/fib',
        ('Sensors', 'Advanced'): 'Advanced Sensors',
        ('Sensors', 'Distributed Arrays'): 'Extended Arrays',
        ('Sensors', 'Military Countermeasures Suite'): 'Military Countermeasures Suite',
        ('Weapons', 'Medium Repulsor Bay'): 'Medium Repulsor Bay (Damage × 20 after armour)',
        ('Weapons', 'Triple Turrets (missile racks) x160'): 'Triple Turret',
        ('Weapons', 'Triple Turrets (beam lasers) x50'): 'Triple Turret',
        ('Weapons', 'Triple Turrets (sandcasters) x25'): 'Triple Turret',
        ('Weapons', 'Point Defence Laser Batteries (Type II) x4'): 'Point Defence Laser Battery Type II',
        ('Ammunition', 'Missile Storage (9,600 missiles)'): 'Missile Storage (9600)',
        ('Ammunition', 'Sandcaster Canister Storage (1,320 canisters)'): 'Sandcaster Canister Storage (1320)',
        ('Screens', 'Nuclear Dampers (size reduction x3) x9'): 'Nuclear Damper',
        ('Craft', 'Docking Spaces (50 tons) x5'): 'Docking Space (50 tons)',
        ('Craft', 'Modular Cutters x5'): 'Internal Docking Space: Modular Cutter',
        ('Systems', 'Briefing Rooms x2'): 'Briefing Room',
        ('Systems', 'Fuel Processor (1,000 tons/day)'): 'Fuel Processor (1000 tons/day)',
        ('Systems', 'Medical Bays x4'): 'Medical Bay',
        ('Systems', 'Workshops x2'): 'Workshop',
        ('Staterooms', 'High'): 'High Stateroom',
        ('Staterooms', 'Standard x265'): 'Staterooms',
        ('Software', 'Manoeuvre'): 'Manoeuvre/0',
        ('Common Areas', 'Common Areas'): 'Common Area',
        ('Cargo', 'Cargo'): 'Cargo Hold',
    }
    target_item = item_map.get((section, item), item)
    target_section = section_map.get((section, item), section_map.get(section, section))
    quantity_map = {
        ('Weapons', 'Triple Turrets (missile racks) x160'): 160,
        ('Weapons', 'Triple Turrets (beam lasers) x50'): 50,
        ('Weapons', 'Triple Turrets (sandcasters) x25'): 25,
    }
    if (section, item) in quantity_map:
        for row in spec.rows_for_section(target_section):
            if row.item == target_item and row.quantity == quantity_map[(section, item)]:
                return row
        raise KeyError(f'No spec row with item={target_item!r} and quantity={quantity_map[(section, item)]}')
    return spec.row(target_item, section=target_section)


def _summed_ship_rows(spec, section: str, item: str) -> SimpleNamespace:
    if item == 'Modular Cutters x5':
        rows = [row for row in spec.rows_for_section(SpecSection.CRAFT) if row.item == 'Modular Cutter']
    elif item == 'Docking Spaces (50 tons) x5':
        rows = [
            row
            for row in spec.rows_for_section(SpecSection.CRAFT)
            if row.item == 'Internal Docking Space: Modular Cutter'
        ]
    else:
        rows = [_ship_row(spec, section, item)]
    return SimpleNamespace(
        tons=sum(row.tons or 0.0 for row in rows) if any(row.tons is not None for row in rows) else None,
        cost=sum(row.cost or 0.0 for row in rows) if any(row.cost is not None for row in rows) else None,
    )


def _size_reduction(steps: int):
    if steps == 3:
        return HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction])
    raise ValueError(f'Valiant only uses size reduction x3, got x{steps}')


def _decreased_fuel():
    return Advanced(modifications=[DecreasedFuel])


def build_valiant_light_cruiser():
    """Note: High Guard Valiant source snapshot is mostly modelled.

    Still missing for a complete Valiant: source crew/running-cost validation,
    investigation of the beam laser turret source cost, and a policy for the
    source's mutually inconsistent purchase/table/row totals.
    """
    reinforced_hull = hull.standard_hull.model_copy(update={'reinforced': True})
    modular_cutter = SpaceCraft.from_catalog('Modular Cutter')

    return ship.Ship(
        ship_class=_expected.ship_class,
        ship_type=_expected.ship_type,
        military=True,
        tl=_expected.tl,
        displacement=_expected.displacement,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(
            configuration=reinforced_hull,
            armour=armour.BondedSuperdenseArmour(protection=15),
            radiation_shielding=True,
        ),
        drives=DriveSection(
            m_drive=MDrive5(customisation=_size_reduction(3)), j_drive=JDrive4(customisation=_decreased_fuel())
        ),
        power=PowerSection(plant=FusionPlantTL15(output=24_000)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=4),
            operation_fuel=OperationFuel(weeks=8),
            fuel_scoops=FuelScoops(),
            fuel_processor=FuelProcessor(tons=50.0),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Core100(fib=True),
            software=[
                AdvancedFireControl(rating=2),
                AntiHijack(rating=3),
                BattleSystem(rating=2),
                BroadSpectrumEW(),
                ElectronicWarfare(rating=1),
                LaunchSolution(rating=3),
                PointDefence(rating=2),
            ],
        ),
        sensors=SensorsSection(
            primary=AdvancedSensors(),
            extended_arrays=ExtendedArrays(),
            signal_processing=EnhancedSignalProcessing(),
            countermeasures=MilitaryCountermeasuresSuite(),
        ),
        weapons=WeaponsSection(
            spinal_mounts=[MesonSpinalMount(tl_improvement=3)],
            bays=[MediumRepulsorBay()],
            turrets=[
                *[TripleTurret(weapons=[MissileRack(), MissileRack(), MissileRack()]) for _ in range(160)],
                *[TripleTurret(weapons=[BeamLaser(), BeamLaser(), BeamLaser()]) for _ in range(50)],
                *[TripleTurret(weapons=[Sandcaster(), Sandcaster(), Sandcaster()]) for _ in range(25)],
            ],
            point_defense_batteries=[LaserPointDefenseBattery2() for _ in range(4)],
            missile_storage=MissileStorage(count=9_600),
            sandcaster_canister_storage=SandcasterCanisterStorage(count=1_320),
        ),
        screens=ScreensSection(
            screens=[NuclearDamper(customisation=_size_reduction(3)) for _ in range(9)],
        ),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=modular_cutter) for _ in range(5)]),
        systems=SystemsSection(
            internal_systems=[
                *[CommandBridge()],
                *[Armoury() for _ in range(18)],
                *[BriefingRoom() for _ in range(2)],
                *[MedicalBay() for _ in range(4)],
                *[Workshop() for _ in range(2)],
            ]
        ),
        habitation=HabitationSection(
            staterooms=[HighStateroom(), *[Stateroom() for _ in range(265)]],
            common_area=CommonArea(tons=267.0),
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=317.0)]),
    )


@pytest.fixture(scope='module')
def valiant_light_cruiser():
    return build_valiant_light_cruiser()


@pytest.fixture(scope='module')
def valiant_spec(valiant_light_cruiser):
    return valiant_light_cruiser.build_spec()


def test_valiant_source_snapshot_metadata(valiant_light_cruiser):
    assert _expected.source == 'High Guard'
    assert valiant_light_cruiser.ship_class == _expected.ship_class
    assert valiant_light_cruiser.ship_type == _expected.ship_type
    assert valiant_light_cruiser.tl == _expected.tl
    assert valiant_light_cruiser.displacement == _expected.displacement
    assert valiant_light_cruiser.hull_points == pytest.approx(_expected.hull_points)


@pytest.mark.parametrize(
    ('section', 'item'),
    [
        (row.section, row.item)
        for row in _expected.rows
        if row.item
        not in {
            '30,000 tons, Standard',
            'Reinforced',
            'Triple Turrets (beam lasers) x50',
        }
    ],
)
def test_valiant_rows_match_source(valiant_spec, section: str, item: str):
    source_row = _source_row(section, item)
    ship_row = _summed_ship_rows(valiant_spec, section, item)

    if source_row.tons is None or source_row.tons == 0:
        assert ship_row.tons in {None, 0.0}
    else:
        assert ship_row.tons == pytest.approx(source_row.tons)
    if source_row.cost_mcr is None:
        assert ship_row.cost is None
    else:
        assert ship_row.cost == pytest.approx(source_row.cost_mcr * 1_000_000)


def test_valiant_hull_rows_match_source(valiant_light_cruiser):
    assert valiant_light_cruiser.hull.configuration.cost(_expected.displacement) == pytest.approx(
        (_source_row('Hull', '30,000 tons, Standard').cost_mcr + _source_row('Hull', 'Reinforced').cost_mcr) * 1_000_000
    )


def test_valiant_basic_power_requirements_match_source(valiant_light_cruiser):
    assert valiant_light_cruiser.basic_hull_power_load == _expected.power_requirements.basic_ship_systems
    assert valiant_light_cruiser.maneuver_power_load == _expected.power_requirements.manoeuvre_drive
    assert valiant_light_cruiser.jump_power_load == _expected.power_requirements.jump_drive
    assert valiant_light_cruiser.screens is not None
    assert sum(screen.power for screen in valiant_light_cruiser.screens.screens) == _expected.power_requirements.screens
    assert valiant_light_cruiser.fuel_power_load == _expected.power_requirements.fuel_processor


def test_valiant_has_no_unexpected_ship_errors_or_warnings(valiant_light_cruiser, valiant_spec):
    assert valiant_light_cruiser.notes.errors == _expected.expected_errors
    assert valiant_light_cruiser.notes.warnings == _expected.expected_warnings
    assert valiant_spec.ship_notes.errors == _expected.expected_errors
    assert valiant_spec.ship_notes.warnings == _expected.expected_warnings
