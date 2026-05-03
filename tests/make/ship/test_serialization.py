"""Roundtrip serialization tests using Pydantic's native model_dump_json / model_validate_json."""

import json

import pytest

from ceres.make.ship import armour, hull
from ceres.make.ship.bridge import Cockpit, CommandSection
from ceres.make.ship.computer import Computer, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive, PowerSection
from ceres.make.ship.hull import BasicStealth, Hull
from ceres.make.ship.parts import EnergyEfficient, HighTechnology
from ceres.make.ship.sensors import BasicSensors, CivilianSensors, SensorsSection
from ceres.make.ship.ship import Ship
from ceres.make.ship.storage import CargoSection, FuelSection, OperationFuel
from ceres.make.ship.systems import Airlock, Armoury, Biosphere, SystemsSection, TrainingFacility
from ceres.make.ship.weapons import FixedMount, MountWeapon, VeryHighYield, WeaponsSection
from tests.ships.test_dragon import build_dragon
from tests.ships.test_revised_beowulf import build_revised_beowulf
from tests.ships.test_revised_dragon import build_revised_dragon

# Minimal ship for structural tests
bare = Ship(tl=12, displacement=6, hull=Hull(configuration=hull.standard_hull))

# Full ship matching the ultralight fighter spec
ultralight = Ship(
    tl=12,
    displacement=6,
    hull=Hull(
        configuration=hull.streamlined_hull,
        armour=armour.CrystalironArmour(tl=12, protection=6),
        stealth=BasicStealth(),
    ),
    drives=DriveSection(m_drive=MDrive(level=6)),
    power=PowerSection(fusion_plant=FusionPlantTL12(output=8)),
    fuel=FuelSection(operation_fuel=OperationFuel(weeks=1)),
    command=CommandSection(cockpit=Cockpit(holographic=True)),
    computer=ComputerSection(hardware=Computer(score=5)),
    sensors=SensorsSection(primary=CivilianSensors()),
    craft=CraftSection(internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))]),
    weapons=WeaponsSection(
        fixed_mounts=[
            FixedMount(
                weapons=[
                    MountWeapon(
                        weapon='pulse_laser',
                        customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]),
                    )
                ]
            )
        ],
    ),
)


# ---------------------------------------------------------------------------
# JSON output is valid and contains expected structure
# ---------------------------------------------------------------------------


def test_dump_produces_valid_json():
    assert json.loads(ultralight.model_dump_json())


def test_dump_bare_ship_contains_tl_and_displacement():
    data = json.loads(bare.model_dump_json())
    assert data['tl'] == 12
    assert data['displacement'] == 6
    assert 'crew' in data


def test_dump_omits_empty_hull_armoured_bulkheads():
    data = json.loads(bare.model_dump_json())
    assert 'armoured_bulkheads' not in data['hull']


def test_dump_armour_in_hull():
    data = json.loads(ultralight.model_dump_json())
    assert data['hull']['armour']['description'] == 'Crystaliron'
    assert data['hull']['armour']['protection'] == 6
    assert data['hull']['armour']['tl'] == 12


def test_dump_no_armour_is_null():
    data = json.loads(bare.model_dump_json())
    assert data['hull'].get('armour') is None


def test_dump_stealth_in_hull():
    data = json.loads(ultralight.model_dump_json())
    assert data['hull']['stealth']['description'] == 'Basic Stealth'


def test_dump_no_stealth_is_null():
    data = json.loads(bare.model_dump_json())
    assert data['hull'].get('stealth') is None


def test_dump_m_drive_present():
    data = json.loads(ultralight.model_dump_json())
    assert data['drives']['m_drive']['cost'] == 720_000
    assert data['drives']['m_drive']['power'] == 4
    assert data['drives']['m_drive']['tons'] == pytest.approx(0.36)


def test_dump_weapon_in_fixed_mounts():
    data = json.loads(ultralight.model_dump_json())
    fp = data['weapons']['fixed_mounts'][0]
    assert fp['weapons'][0]['weapon'] == 'pulse_laser'
    assert fp['weapons'][0]['customisation']['grade'] == 'HIGH_TECHNOLOGY'
    assert [m['name'] for m in fp['weapons'][0]['customisation']['modifications']] == [
        'Very High Yield',
        'Energy Efficient',
    ]


def test_dump_ship_crew_contains_vector_and_notes():
    source_ship = build_dragon()
    data = json.loads(source_ship.model_dump_json())
    assert any(role['role'] == 'ASTROGATOR' and role['level'] == 1 for role in data['crew']['roles'])
    assert any(note['message'] == 'ASTROGATOR above recommended count: 1 > 0' for note in data['crew']['notes'])


# ---------------------------------------------------------------------------
# Roundtrip: model_dump_json → model_validate_json
# ---------------------------------------------------------------------------


def _roundtrip(s: Ship) -> Ship:
    return Ship.model_validate_json(s.model_dump_json())


def test_roundtrip_bare_ship():
    loaded = _roundtrip(bare)
    assert loaded.tl == bare.tl
    assert loaded.displacement == bare.displacement


def test_roundtrip_hull_configuration():
    loaded = _roundtrip(ultralight)
    assert loaded.hull.configuration == ultralight.hull.configuration


def test_roundtrip_armour_type_and_protection():
    loaded = _roundtrip(ultralight)
    orig = ultralight.hull.armour
    rt = loaded.hull.armour
    assert orig is not None
    assert rt is not None
    assert type(rt) is type(orig)
    assert rt.protection == orig.protection


def test_roundtrip_no_armour():
    loaded = _roundtrip(bare)
    assert loaded.hull.armour is None


def test_roundtrip_stealth():
    loaded = _roundtrip(ultralight)
    assert isinstance(loaded.hull.stealth, BasicStealth)


def test_roundtrip_no_stealth():
    loaded = _roundtrip(bare)
    assert loaded.hull.stealth is None


def test_roundtrip_m_drive_attributes():
    loaded = _roundtrip(ultralight)
    assert loaded.drives is not None
    assert ultralight.drives is not None
    assert loaded.drives.m_drive is not None
    assert ultralight.drives.m_drive is not None
    assert type(loaded.drives.m_drive) is type(ultralight.drives.m_drive)
    assert loaded.drives.m_drive.level == ultralight.drives.m_drive.level


def test_roundtrip_recomputes_derived_part_values():
    data = json.loads(ultralight.model_dump_json())
    data['drives']['m_drive']['cost'] = 1
    data['drives']['m_drive']['power'] = 999
    data['drives']['m_drive']['tons'] = 999
    loaded = Ship.model_validate_json(json.dumps(data))
    assert loaded.drives is not None
    assert loaded.drives.m_drive is not None
    assert loaded.drives.m_drive.cost == 720_000
    assert loaded.drives.m_drive.power == 4
    assert loaded.drives.m_drive.tons == pytest.approx(0.36)


def test_roundtrip_fusion_plant_attributes():
    loaded = _roundtrip(ultralight)
    assert loaded.power is not None
    assert ultralight.power is not None
    assert loaded.power.fusion_plant is not None
    assert ultralight.power.fusion_plant is not None
    assert loaded.power.fusion_plant.fusion_tl == ultralight.power.fusion_plant.fusion_tl
    assert loaded.power.fusion_plant.output == ultralight.power.fusion_plant.output


def test_roundtrip_cockpit():
    loaded = _roundtrip(ultralight)
    assert loaded.command is not None
    assert ultralight.command is not None
    assert loaded.command.cockpit is not None
    assert ultralight.command.cockpit is not None
    assert loaded.command.cockpit.holographic == ultralight.command.cockpit.holographic


def test_roundtrip_computer():
    loaded = _roundtrip(ultralight)
    assert loaded.computer is not None
    assert ultralight.computer is not None
    assert loaded.computer.hardware is not None
    assert ultralight.computer.hardware is not None
    assert type(loaded.computer.hardware) is type(ultralight.computer.hardware)
    assert loaded.computer.hardware.processing == ultralight.computer.hardware.processing


def test_roundtrip_backup_computer():
    ship_with_backup = Ship(
        tl=13,
        displacement=100,
        hull=Hull(configuration=hull.standard_hull),
        computer=ComputerSection(hardware=Computer(score=25), backup_hardware=Computer(score=20, fib=True)),
    )
    loaded = _roundtrip(ship_with_backup)
    assert loaded.computer is not None
    assert loaded.computer.backup_hardware is not None
    assert isinstance(loaded.computer.backup_hardware, Computer)
    assert loaded.computer.backup_hardware.score == 20
    assert loaded.computer.backup_hardware.fib is True


def test_roundtrip_sensors():
    loaded = _roundtrip(ultralight)
    assert isinstance(loaded.sensors.primary, CivilianSensors)


def test_roundtrip_basic_sensors():
    loaded = _roundtrip(bare)
    assert isinstance(loaded.sensors.primary, BasicSensors)


def test_roundtrip_weapon_attributes():
    loaded = _roundtrip(ultralight)
    assert ultralight.weapons is not None
    assert loaded.weapons is not None
    orig_fp = ultralight.weapons.fixed_mounts[0]
    rt_fp = loaded.weapons.fixed_mounts[0]
    assert rt_fp.weapons[0].weapon == orig_fp.weapons[0].weapon
    assert rt_fp.weapons[0].customisation == orig_fp.weapons[0].customisation


def test_roundtrip_cargo():
    loaded = _roundtrip(ultralight)
    loaded_cargo = float(CargoSection.cargo_tons_for_ship(loaded))
    original_cargo = float(CargoSection.cargo_tons_for_ship(ultralight))
    assert loaded_cargo == pytest.approx(original_cargo)


def test_roundtrip_no_parts():
    loaded = _roundtrip(bare)
    assert loaded.drives is None
    assert loaded.power is None
    assert loaded.command is None or loaded.command.cockpit is None
    assert loaded.weapons is None


def test_roundtrip_airlock():
    ship_with_airlock = Ship(
        tl=12,
        displacement=100,
        hull=Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
    )
    loaded = _roundtrip(ship_with_airlock)
    assert len(loaded.hull.airlocks) == 1
    assert loaded.hull.airlocks[0].tons == pytest.approx(0.0)
    assert loaded.hull.airlocks[0].cost == 0.0


def test_roundtrip_new_systems():
    ship_with_systems = Ship(
        tl=12,
        displacement=100,
        hull=Hull(configuration=hull.standard_hull),
        systems=SystemsSection(
            internal_systems=[Armoury(), Biosphere(tons=4.0), TrainingFacility(trainees=2)],
        ),
    )
    loaded = _roundtrip(ship_with_systems)
    assert loaded.systems is not None
    assert len(loaded.systems.armouries) == 1
    assert loaded.systems.armouries[0].tons == pytest.approx(1.0)
    assert loaded.systems.biosphere is not None
    assert loaded.systems.biosphere.tons == pytest.approx(4.0)
    assert loaded.systems.training_facility is not None
    assert loaded.systems.training_facility.trainees == 2


# ---------------------------------------------------------------------------
# Idempotency: roundtripping twice produces identical JSON
# ---------------------------------------------------------------------------


def _roundtrip_json(s: Ship) -> str:
    return Ship.model_validate_json(s.model_dump_json()).model_dump_json()


def test_roundtrip_is_idempotent_ultralight():
    j1 = _roundtrip_json(ultralight)
    j2 = _roundtrip_json(Ship.model_validate_json(j1))
    assert json.loads(j1) == json.loads(j2)


def test_roundtrip_is_idempotent_dragon():
    ship = build_dragon()
    j1 = _roundtrip_json(ship)
    j2 = _roundtrip_json(Ship.model_validate_json(j1))
    assert json.loads(j1) == json.loads(j2)


def test_roundtrip_is_idempotent_revised_dragon():
    ship = build_revised_dragon()
    j1 = _roundtrip_json(ship)
    j2 = _roundtrip_json(Ship.model_validate_json(j1))
    assert json.loads(j1) == json.loads(j2)


def test_roundtrip_is_idempotent_revised_beowulf():
    ship = build_revised_beowulf()
    j1 = _roundtrip_json(ship)
    j2 = _roundtrip_json(Ship.model_validate_json(j1))
    assert json.loads(j1) == json.loads(j2)


def test_roundtrip_dragon_production_cost():
    ship = build_dragon()
    loaded = _roundtrip(ship)
    assert loaded.production_cost == pytest.approx(ship.production_cost)


def test_roundtrip_dragon_part_notes_not_duplicated():
    ship = build_dragon()
    loaded = _roundtrip(ship)
    assert loaded.power is not None and ship.power is not None
    assert loaded.power.fusion_plant is not None and ship.power.fusion_plant is not None
    assert len(loaded.power.fusion_plant.notes) == len(ship.power.fusion_plant.notes)
    assert loaded.drives is not None and ship.drives is not None
    assert loaded.drives.m_drive is not None and ship.drives.m_drive is not None
    assert len(loaded.drives.m_drive.notes) == len(ship.drives.m_drive.notes)
