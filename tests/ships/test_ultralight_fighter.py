import pytest

from ceres import armour, ship
from ceres.bridge import Cockpit
from ceres.computer import Computer5
from ceres.drives import FusionPlantTL12, MDrive6, OperationFuel
from ceres.sensors import CivilianGradeSensors
from ceres.weapons import FixedFirmpoint, PulseLaser

from ._markdown_output import write_markdown_output


def build_ultralight_fighter() -> ship.Ship:
    return ship.Ship(
        ship_class='Botfly',
        ship_type='Ultralight Fighter',
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.STANDARD,
        hull=ship.Hull(
            configuration=ship.streamlined_hull.model_copy(
                update={'light': True, 'description': 'Light Streamlined Hull'},
            ),
            armour=armour.CrystalironArmour(tl=12, protection=6),
            stealth=ship.BasicStealth(),
        ),
        m_drive=MDrive6(budget=True, increased_size=True),
        fusion_plant=FusionPlantTL12(
            output=8,
            budget=True,
            increased_size=True,
        ),
        operation_fuel=OperationFuel(weeks=1),
        cockpit=Cockpit(holographic=True),
        computer=Computer5(),
        sensors=CivilianGradeSensors(),
        fixed_firmpoints=[
            FixedFirmpoint(
                weapon=PulseLaser(very_high_yield=True, energy_efficient=True),
            ),
        ],
    )


def test_ultralight_fighter_matches_modeled_reference_values():
    fighter = build_ultralight_fighter()
    armour_part = fighter.hull.armour
    stealth = fighter.hull.stealth
    m_drive = fighter.m_drive
    fusion_plant = fighter.fusion_plant
    operation_fuel = fighter.operation_fuel
    cockpit = fighter.cockpit
    computer = fighter.computer
    sensors = fighter.sensors
    weapon_mount = fighter.fixed_firmpoints[0]

    assert int(fighter.tl) == 12
    assert fighter.displacement == 6

    assert armour_part is not None
    assert float(armour_part.tons) == pytest.approx(2.16)
    assert int(armour_part.cost) == 432_000

    assert stealth is not None
    assert float(stealth.tons) == pytest.approx(0.12)
    assert int(stealth.cost) == 240_000

    assert m_drive is not None
    assert float(m_drive.tons) == pytest.approx(0.45)
    assert int(m_drive.cost) == 540_000
    assert int(m_drive.power) == 4

    assert fusion_plant is not None
    assert float(fusion_plant.tons) == pytest.approx(2 / 3)
    assert int(fusion_plant.cost) == 400_000

    assert operation_fuel is not None
    assert float(operation_fuel.tons) == pytest.approx(0.02)
    assert int(operation_fuel.cost) == 0

    assert cockpit is not None
    assert float(cockpit.tons) == pytest.approx(1.5)
    assert int(cockpit.cost) == 12_500

    assert computer is not None
    assert float(computer.tons) == pytest.approx(0)
    assert computer.processing == 5
    assert int(computer.cost) == 30_000
    assert [(package.name, package.tons, package.cost) for package in fighter.software_packages] == [
        ('Library', 0.0, 0.0),
        ('Maneuver/0', 0.0, 0.0),
        ('Intellect', 0.0, 0.0),
    ]

    assert sensors is not None
    assert float(sensors.tons) == pytest.approx(1)
    assert int(sensors.cost) == 3_000_000
    assert int(sensors.power) == 1

    assert float(weapon_mount.tons) == pytest.approx(0)
    assert int(weapon_mount.cost) == 1_600_000
    assert int(weapon_mount.power) == 2

    assert fighter.hull_cost == 270_000
    assert fighter.production_cost == 6_524_500
    assert fighter.sales_price_new == 5_872_050
    assert [(role.role, role.count, role.monthly_salary) for role in fighter.crew_roles] == [('PILOT', 1, 6_000)]
    assert fighter.available_power == 8
    assert fighter.basic_hull_power_load == 1
    assert fighter.maneuver_power_load == 4
    assert fighter.sensor_power_load == 1
    assert fighter.weapon_power_load == 2
    assert fighter.total_power_load == 8

    # The reference sheet rounds this to 0.09 tons.
    assert float(fighter.cargo) == pytest.approx(0.08333333333333393)


def test_ultralight_fighter_markdown_table_contains_core_rows():
    fighter = build_ultralight_fighter()
    table = fighter.markdown_table()
    write_markdown_output('test_ultralight_fighter', table)

    assert '## *Botfly* Ultralight Fighter | TL12 | Hull 2' in table
    assert '| Section | Item | Tons | Power | Cost (kCr) |' in table
    assert '| Hull | Light Streamlined Hull | 6.00 |  | 270.00 |' in table
    assert '| Armour | Crystaliron, Armour: 6 | 2.16 |  | 432.00 |' in table
    assert '| M-Drive | Thrust 6 Budget Increased Size | 0.45 | -4.00 | 540.00 |' in table
    assert '| Sensors | Civilian Grade | 1.00 | -1.00 | 3000.00 |' in table
    assert '|  | • Radar, Lidar; DM -2 |  |  |  |' in table
    assert '| Fuel | Operation 1 weeks | 0.02 |  | 0.00 |' in table
    assert '|  | Maneuver/0 |  |  | 0.00 |' in table
    assert '| Cargo | Cargo Hold | 0.08 |  | 0.00 |' in table
    assert '| Mortgage | 24466.88 |' in table
    assert '| Total Expenses | 30955.88 |' in table
