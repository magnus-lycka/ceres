from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Cockpit, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive6, PowerSection
from ceres.make.ship.parts import EnergyEfficient, HighTechnology
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.storage import FuelSection, OperationFuel
from ceres.make.ship.weapons import FixedMount, PulseLaser, VeryHighYield, WeaponsSection

_expected = SimpleNamespace(
    tl=12,
    displacement=6,
    hull_cost=270_000,
    armour_tons=2.16,
    armour_cost=432_000,
    stealth_tons=0.12,
    stealth_cost=240_000,
    m_drive_tons=0.36,
    m_drive_cost=720_000,
    power_plant_tons=8 / 15,
    power_plant_cost=533_333,
    operation_fuel_tons=0.1,
    cockpit_tons=1.5,
    cockpit_cost=12_500,
    computer_processing=5,
    computer_cost=30_000,
    sensor_tons=1,
    sensor_cost=3_000_000,
    weapon_mount_tons=0,
    weapon_mount_cost=1_600_000,
    weapon_mount_info_notes=['High Technology: Very High Yield, Energy Efficient'],
    available_power=8,
    power_basic=1,  # Tycho normal-load stat block
    power_maneuver=4,
    power_sensors=1,
    power_weapons=2,
    total_power=8,  # Tycho normal-load stat block
    crew=[('PILOT', 1, 6_000)],
    expected_errors=[],
    expected_warnings=[],
)
# Tycho tool uses floor; ceil(6 * 0.2) = 2 per RIS-013
_expected.power_basic = 2
_expected.total_power = 9


def build_ultralight_fighter() -> ship.Ship:
    return ship.Ship(
        ship_class='Botfly',
        military=True,
        ship_type='Ultralight Fighter',
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull.model_copy(
                update={'light': True, 'description': 'Light Streamlined Hull'},
            ),
            armour=armour.CrystalironArmour(protection=6),
            stealth=hull.BasicStealth(),
        ),
        drives=DriveSection(m_drive=MDrive6()),
        power=PowerSection(plant=FusionPlantTL12(output=8)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=1)),
        command=CommandSection(cockpit=Cockpit(holographic=True)),
        computer=ComputerSection(hardware=Computer5()),
        sensors=SensorsSection(primary=CivilianSensors()),
        weapons=WeaponsSection(
            fixed_mounts=[
                FixedMount(
                    weapons=[
                        PulseLaser(
                            customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]),
                        )
                    ]
                ),
            ],
        ),
    )


def test_ultralight_fighter_part_values():
    fighter = build_ultralight_fighter()

    assert fighter.tl == _expected.tl
    assert fighter.displacement == _expected.displacement

    a = fighter.hull.armour
    assert a is not None
    assert float(a.tons) == pytest.approx(_expected.armour_tons)
    assert int(a.cost) == _expected.armour_cost

    s = fighter.hull.stealth
    assert s is not None
    assert float(s.tons) == pytest.approx(_expected.stealth_tons)
    assert int(s.cost) == _expected.stealth_cost

    assert fighter.drives is not None
    m = fighter.drives.m_drive
    assert m is not None
    assert float(m.tons) == pytest.approx(_expected.m_drive_tons)
    assert int(m.cost) == _expected.m_drive_cost
    assert int(m.power) == _expected.power_maneuver

    assert fighter.power is not None
    fp = fighter.power.plant
    assert fp is not None
    assert float(fp.tons) == pytest.approx(_expected.power_plant_tons)
    assert int(fp.cost) == _expected.power_plant_cost

    assert fighter.fuel is not None
    assert fighter.fuel.operation_fuel is not None
    assert float(fighter.fuel.operation_fuel.tons) == pytest.approx(_expected.operation_fuel_tons)

    assert fighter.command is not None
    assert fighter.command.cockpit is not None
    assert float(fighter.command.cockpit.tons) == pytest.approx(_expected.cockpit_tons)
    assert int(fighter.command.cockpit.cost) == _expected.cockpit_cost

    assert fighter.computer is not None
    assert fighter.computer.hardware is not None
    assert fighter.computer.hardware.processing == _expected.computer_processing
    assert int(fighter.computer.hardware.cost) == _expected.computer_cost

    assert fighter.sensors is not None
    assert float(fighter.sensors.primary.tons) == pytest.approx(_expected.sensor_tons)
    assert int(fighter.sensors.primary.cost) == _expected.sensor_cost

    assert fighter.weapons is not None
    weapon_mount = fighter.weapons.fixed_mounts[0]
    assert float(weapon_mount.tons) == pytest.approx(_expected.weapon_mount_tons)
    assert int(weapon_mount.cost) == _expected.weapon_mount_cost
    assert int(weapon_mount.power) == _expected.power_weapons

    assert fighter.hull_cost == _expected.hull_cost
    assert fighter.available_power == _expected.available_power
    assert fighter.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert fighter.maneuver_power_load == _expected.power_maneuver
    assert fighter.sensor_power_load == _expected.power_sensors
    assert fighter.weapon_power_load == _expected.power_weapons
    assert fighter.total_power_load == pytest.approx(_expected.total_power)

    crew = [(role.role, quantity, role.monthly_salary) for role, quantity in fighter.crew.grouped_roles]
    assert crew == _expected.crew
    assert fighter.notes.errors == _expected.expected_errors
    assert fighter.notes.warnings == _expected.expected_warnings


def test_ultralight_fighter_pulse_laser_has_customisation_note():
    fighter = build_ultralight_fighter()
    assert fighter.weapons is not None
    mount = fighter.weapons.fixed_mounts[0]
    assert mount.notes.infos == _expected.weapon_mount_info_notes
