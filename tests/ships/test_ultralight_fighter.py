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
    available_power=8,
    power_basic=1,  # Tycho normal-load stat block
    power_maneuver=4,
    power_sensors=1,
    power_weapons=2,
    total_power=8,  # Tycho normal-load stat block
)
# Tycho tool uses floor; ceil(6 * 0.2) = 2 per RI-013
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

    assert fighter.tl == 12
    assert fighter.displacement == 6

    a = fighter.hull.armour
    assert a is not None
    assert float(a.tons) == pytest.approx(2.16)
    assert int(a.cost) == 432_000

    s = fighter.hull.stealth
    assert s is not None
    assert float(s.tons) == pytest.approx(0.12)
    assert int(s.cost) == 240_000

    assert fighter.drives is not None
    m = fighter.drives.m_drive
    assert m is not None
    assert float(m.tons) == pytest.approx(0.36)
    assert int(m.cost) == 720_000
    assert int(m.power) == 4

    assert fighter.power is not None
    fp = fighter.power.plant
    assert fp is not None
    assert float(fp.tons) == pytest.approx(8 / 15)
    assert int(fp.cost) == 533_333

    assert fighter.fuel is not None
    assert fighter.fuel.operation_fuel is not None
    assert float(fighter.fuel.operation_fuel.tons) == pytest.approx(0.1)

    assert fighter.command is not None
    assert fighter.command.cockpit is not None
    assert float(fighter.command.cockpit.tons) == pytest.approx(1.5)
    assert int(fighter.command.cockpit.cost) == 12_500

    assert fighter.computer is not None
    assert fighter.computer.hardware is not None
    assert fighter.computer.hardware.processing == 5
    assert int(fighter.computer.hardware.cost) == 30_000

    assert fighter.sensors is not None
    assert float(fighter.sensors.primary.tons) == pytest.approx(1)
    assert int(fighter.sensors.primary.cost) == 3_000_000

    assert fighter.weapons is not None
    weapon_mount = fighter.weapons.fixed_mounts[0]
    assert float(weapon_mount.tons) == pytest.approx(0)
    assert int(weapon_mount.cost) == 1_600_000
    assert int(weapon_mount.power) == 2

    assert fighter.hull_cost == _expected.hull_cost
    assert fighter.available_power == _expected.available_power
    assert fighter.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert fighter.maneuver_power_load == _expected.power_maneuver
    assert fighter.sensor_power_load == _expected.power_sensors
    assert fighter.weapon_power_load == _expected.power_weapons
    assert fighter.total_power_load == pytest.approx(_expected.total_power)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in fighter.crew.grouped_roles] == [
        ('PILOT', 1, 6_000),
    ]


def test_ultralight_fighter_pulse_laser_has_customisation_note():
    fighter = build_ultralight_fighter()
    assert fighter.weapons is not None
    mount = fighter.weapons.fixed_mounts[0]
    note_messages = mount.notes.infos
    assert 'High Technology: Very High Yield, Energy Efficient' in note_messages
