import pytest

from ceres import armour, hull, ship
from ceres.bridge import Cockpit, CommandSection
from ceres.computer import Computer5, ComputerSection
from ceres.drives import DriveSection, FusionPlantTL12, MDrive6, PowerSection
from ceres.sensors import CivilianSensors, SensorsSection
from ceres.storage import FuelSection, OperationFuel
from ceres.weapons import FixedFirmpoint, PulseLaser, WeaponsSection

from ._markdown_output import write_markdown_output


def build_ultralight_fighter() -> ship.Ship:
    return ship.Ship(
        ship_class='Botfly',
        ship_type='Ultralight Fighter',
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull.model_copy(
                update={'light': True, 'description': 'Light Streamlined Hull'},
            ),
            armour=armour.CrystalironArmour(tl=12, protection=6),
            stealth=hull.BasicStealth(),
        ),
        drives=DriveSection(m_drive=MDrive6()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=8)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=1)),
        command=CommandSection(cockpit=Cockpit(holographic=True)),
        computer=ComputerSection(hardware=Computer5()),
        sensors=SensorsSection(primary=CivilianSensors()),
        weapons=WeaponsSection(
            fixed_firmpoints=[
                FixedFirmpoint(weapon=PulseLaser(very_high_yield=True, energy_efficient=True)),
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
    fp = fighter.power.fusion_plant
    assert fp is not None
    assert float(fp.tons) == pytest.approx(8 / 15)
    assert int(fp.cost) == 533_333

    assert fighter.fuel is not None
    assert fighter.fuel.operation_fuel is not None
    assert float(fighter.fuel.operation_fuel.tons) == pytest.approx(0.02)

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
    weapon_mount = fighter.weapons.fixed_firmpoints[0]
    assert float(weapon_mount.tons) == pytest.approx(0)
    assert int(weapon_mount.cost) == 1_600_000
    assert int(weapon_mount.power) == 2

    assert fighter.hull_cost == 270_000
    assert fighter.available_power == 8
    assert fighter.basic_hull_power_load == pytest.approx(1.0)
    assert fighter.maneuver_power_load == 4
    assert fighter.sensor_power_load == 1
    assert fighter.weapon_power_load == 2
    assert fighter.total_power_load == pytest.approx(8.0)

    assert [(role.role, role.count, role.monthly_salary) for role in fighter.crew_roles] == [
        ('PILOT', 1, 6_000),
    ]


def test_ultralight_fighter_markdown_table():
    fighter = build_ultralight_fighter()
    table = fighter.markdown_table()
    write_markdown_output('test_ultralight_fighter', table)

    assert '## *Botfly* Ultralight Fighter | TL12 | Hull 2' in table
    assert '| Hull | Light Streamlined Hull | **6.00** |  | 270.00 |' in table
    assert '|  | Basic Ship Systems |  | 1.00 |  |' in table
    assert '|  | Crystaliron, Armour: 6 | 2.16 |  | 432.00 |' in table
    assert '| Propulsion | M-Drive 6 | 0.36 | 4.00 | 720.00 |' in table
    assert '| Power | Fusion (TL 12) | 0.53 | **8.00** | 533.33 |' in table
    assert '| Sensors | Civilian Grade | 1.00 | 1.00 | 3000.00 |' in table
    assert '| Fuel | 1 week of operation | 0.02 |  |  |' in table
    assert '|  | Manoeuvre/0 |  |  |  |' in table
