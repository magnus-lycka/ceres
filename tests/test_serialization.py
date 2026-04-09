"""Roundtrip serialization tests using Pydantic's native model_dump_json / model_validate_json."""

import json

import pytest

from ceres import armour, hull
from ceres.bridge import Cockpit, CommandSection
from ceres.computer import Computer5, ComputerSection
from ceres.crafts import AirRaft, CraftSection, InternalDockingSpace
from ceres.drives import DriveSection, FusionPlantTL12, MDrive6, PowerSection
from ceres.hull import BasicStealth, Hull
from ceres.sensors import BasicSensors, CivilianSensors, SensorsSection
from ceres.ship import Ship
from ceres.storage import FuelSection, OperationFuel
from ceres.systems import Airlock
from ceres.weapons import FixedFirmpoint, PulseLaser, WeaponsSection

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
    drives=DriveSection(m_drive=MDrive6()),
    power=PowerSection(fusion_plant=FusionPlantTL12(output=8)),
    fuel=FuelSection(operation_fuel=OperationFuel(weeks=1)),
    command=CommandSection(cockpit=Cockpit(holographic=True)),
    computer=ComputerSection(hardware=Computer5()),
    sensors=SensorsSection(primary=CivilianSensors()),
    craft=CraftSection(docking_space=InternalDockingSpace(craft=AirRaft())),
    weapons=WeaponsSection(
        fixed_firmpoints=[FixedFirmpoint(weapon=PulseLaser(very_high_yield=True, energy_efficient=True))],
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


def test_dump_weapon_in_fixed_firmpoints():
    data = json.loads(ultralight.model_dump_json())
    fp = data['weapons']['fixed_firmpoints'][0]
    assert fp['weapon']['very_high_yield'] is True
    assert fp['weapon']['energy_efficient'] is True


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
    assert loaded.drives.m_drive.rating == ultralight.drives.m_drive.rating


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
    orig_fp = ultralight.weapons.fixed_firmpoints[0]
    rt_fp = loaded.weapons.fixed_firmpoints[0]
    assert rt_fp.weapon.very_high_yield == orig_fp.weapon.very_high_yield
    assert rt_fp.weapon.energy_efficient == orig_fp.weapon.energy_efficient


def test_roundtrip_cargo():
    loaded = _roundtrip(ultralight)
    assert float(loaded.cargo_tons) == pytest.approx(float(ultralight.cargo_tons))


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
