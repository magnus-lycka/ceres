"""Roundtrip serialization tests using Pydantic's native model_dump_json / model_validate_json."""
import json
import pytest

from ceres import armour, ship
from ceres.bridge import Cockpit
from ceres.computer import Computer
from ceres.drives import FusionPlantTL12, MDrive, OperationFuel
from ceres.sensors import CivilianGradeSensors
from ceres.ship import BasicStealth, Ship, Hull
from ceres.weapons import FixedFirmpoint, PulseLaser


# Minimal ship for structural tests
bare = Ship(tl=12, displacement=6, hull=Hull(configuration=ship.standard_hull))

# Full ship matching the ultralight fighter spec
ultralight = Ship(
    tl=12,
    displacement=6,
    hull=Hull(
        configuration=ship.streamlined_hull,
        crystaliron_armour=armour.CrystalironArmour(tl=12, protection=6),
        basic_stealth=BasicStealth(),
    ),
    m_drive=MDrive(rating=6, budget=True, increased_size=True),
    fusion_plant=FusionPlantTL12(output=8, budget=True, increased_size=True),
    operation_fuel=OperationFuel(weeks=1),
    cockpit=Cockpit(holographic=True),
    computer=Computer(rating=5),
    civilian_sensors=CivilianGradeSensors(),
    fixed_firmpoints=[FixedFirmpoint(weapon=PulseLaser(very_high_yield=True, energy_efficient=True))],
)


# ---------------------------------------------------------------------------
# JSON output is valid and contains expected structure
# ---------------------------------------------------------------------------

def test_dump_produces_valid_json():
    assert json.loads(ultralight.model_dump_json())


def test_dump_bare_ship_contains_tl_and_displacement():
    data = json.loads(bare.model_dump_json())
    assert data["tl"] == 12
    assert data["displacement"] == 6


def test_dump_armour_in_hull():
    data = json.loads(ultralight.model_dump_json())
    assert data["hull"]["crystaliron_armour"]["protection"] == 6
    assert data["hull"]["crystaliron_armour"]["tl"] == 12


def test_dump_no_armour_is_null():
    data = json.loads(bare.model_dump_json())
    assert data["hull"].get("crystaliron_armour") is None


def test_dump_stealth_in_hull():
    data = json.loads(ultralight.model_dump_json())
    assert data["hull"]["basic_stealth"] is not None


def test_dump_no_stealth_is_null():
    data = json.loads(bare.model_dump_json())
    assert data["hull"].get("basic_stealth") is None


def test_dump_m_drive_present():
    data = json.loads(ultralight.model_dump_json())
    assert data["m_drive"]["rating"] == 6
    assert data["m_drive"]["budget"] is True
    assert data["m_drive"]["increased_size"] is True


def test_dump_weapon_in_fixed_firmpoints():
    data = json.loads(ultralight.model_dump_json())
    fp = data["fixed_firmpoints"][0]
    assert fp["weapon"]["very_high_yield"] is True
    assert fp["weapon"]["energy_efficient"] is True


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
    orig = ultralight.hull.crystaliron_armour
    rt = loaded.hull.crystaliron_armour
    assert rt is not None
    assert type(rt) is type(orig)
    assert rt.protection == orig.protection


def test_roundtrip_no_armour():
    loaded = _roundtrip(bare)
    assert loaded.hull.crystaliron_armour is None
    assert loaded.hull.titanium_steel_armour is None


def test_roundtrip_stealth():
    loaded = _roundtrip(ultralight)
    assert isinstance(loaded.hull.basic_stealth, BasicStealth)


def test_roundtrip_no_stealth():
    loaded = _roundtrip(bare)
    assert loaded.hull.basic_stealth is None


def test_roundtrip_m_drive_attributes():
    loaded = _roundtrip(ultralight)
    assert loaded.m_drive.rating == ultralight.m_drive.rating
    assert loaded.m_drive.budget == ultralight.m_drive.budget
    assert loaded.m_drive.increased_size == ultralight.m_drive.increased_size


def test_roundtrip_fusion_plant_attributes():
    loaded = _roundtrip(ultralight)
    assert loaded.fusion_plant.fusion_tl == ultralight.fusion_plant.fusion_tl
    assert loaded.fusion_plant.output == ultralight.fusion_plant.output
    assert loaded.fusion_plant.budget == ultralight.fusion_plant.budget


def test_roundtrip_cockpit():
    loaded = _roundtrip(ultralight)
    assert loaded.cockpit.holographic == ultralight.cockpit.holographic


def test_roundtrip_computer():
    loaded = _roundtrip(ultralight)
    assert loaded.computer.rating == ultralight.computer.rating


def test_roundtrip_sensors():
    loaded = _roundtrip(ultralight)
    assert isinstance(loaded.civilian_sensors, CivilianGradeSensors)


def test_roundtrip_weapon_attributes():
    loaded = _roundtrip(ultralight)
    orig_fp = ultralight.fixed_firmpoints[0]
    rt_fp = loaded.fixed_firmpoints[0]
    assert rt_fp.weapon.very_high_yield == orig_fp.weapon.very_high_yield
    assert rt_fp.weapon.energy_efficient == orig_fp.weapon.energy_efficient


def test_roundtrip_cargo():
    loaded = _roundtrip(ultralight)
    assert float(loaded.cargo) == pytest.approx(float(ultralight.cargo))


def test_roundtrip_no_parts():
    loaded = _roundtrip(bare)
    assert loaded.m_drive is None
    assert loaded.fusion_plant is None
    assert loaded.cockpit is None
    assert loaded.fixed_firmpoints == []
