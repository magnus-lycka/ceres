from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive6, PowerSection, RDrive4
from ceres.make.ship.habitation import CabinSpace, HabitationSection
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
from ceres.make.ship.software import FireControl
from ceres.make.ship.storage import FuelScoops, FuelSection, OperationFuel, ReactionFuel
from ceres.make.ship.systems import Aerofins
from ceres.make.ship.weapons import FixedMount, PulseLaser, WeaponsSection

_expected = SimpleNamespace(
    tl=12,
    displacement=20,
    hull_cost_mcr=12.0,
    hull_points=8,
    pressure_hull_tons=5.0,
    m_drive_tons=1.2,
    m_drive_cost_mcr=2.4,
    r_drive_tons=1.6,
    r_drive_cost_mcr=0.32,
    r_drive_item='High-Burn Thruster, Thrust 4',
    plant_tons=2.0,
    plant_cost_mcr=2.0,
    operation_fuel_tons=0.1,
    reaction_fuel_tons=2.0,
    bridge_tons=3.0,
    bridge_cost_mcr=0.5,
    computer_cost_mcr=0.03,
    sensor_tons=2.0,
    sensor_cost_mcr=4.1,
    fixed_mount_cost_mcr=1.1,
    fixed_mount_power=3.0,
    cabin_space_tons=1.5,
    cabin_space_cost_mcr=0.075,
    available_power=30.0,
    power_basic=4.0,
    power_maneuver=12.0,
    power_sensors=2.0,
    power_weapons=3.0,
    total_power=21.0,
    production_cost_mcr=24.625,
    sales_price_mcr=24.625,
    maintenance_cr=2052.0,
    crew=[('PILOT', 1, 6_000)],
    expected_errors=['No airlock installed'],
    expected_warnings=[],
    expected_crew_infos=[],
    expected_crew_warnings=[],
)


def build_gothta_ambush_fighter() -> ship.Ship:
    return ship.Ship(
        ship_class='Gothta',
        ship_type='Ambush Fighter',
        military=True,
        tl=_expected.tl,
        displacement=_expected.displacement,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            pressure_hull=True,
            airlocks=[],
            aerofins=Aerofins(),
        ),
        drives=DriveSection(
            m_drive=MDrive6(),
            r_drive=RDrive4(high_burn_thruster=True),
        ),
        power=PowerSection(plant=FusionPlantTL12(output=30)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=2),
            reaction_fuel=ReactionFuel(minutes=60),
            fuel_scoops=FuelScoops(free=True),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(), software=[FireControl(rating=1)]),
        sensors=SensorsSection(primary=MilitarySensors()),
        weapons=WeaponsSection(
            fixed_mounts=[FixedMount(weapons=[PulseLaser()])],
        ),
        habitation=HabitationSection(cabin_space=CabinSpace(tons=1.5)),
    )


def test_gothta_ambush_fighter_matches_current_subset():
    fighter = build_gothta_ambush_fighter()

    assert fighter.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert fighter.hull_points == _expected.hull_points
    assert fighter.hull.pressure_hull_tons(fighter.displacement) == pytest.approx(_expected.pressure_hull_tons)

    assert fighter.drives is not None
    assert fighter.drives.m_drive is not None
    assert fighter.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert fighter.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert fighter.drives.r_drive is not None
    assert fighter.drives.r_drive.tons == pytest.approx(_expected.r_drive_tons)
    assert fighter.drives.r_drive.cost == pytest.approx(_expected.r_drive_cost_mcr * 1_000_000)
    assert fighter.drives.r_drive.build_item() == _expected.r_drive_item

    assert fighter.power is not None
    assert fighter.power.plant is not None
    assert fighter.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert fighter.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)

    assert fighter.fuel is not None
    assert fighter.fuel.operation_fuel is not None
    assert fighter.fuel.operation_fuel.tons == pytest.approx(_expected.operation_fuel_tons)
    assert fighter.fuel.reaction_fuel is not None
    assert fighter.fuel.reaction_fuel.tons == pytest.approx(_expected.reaction_fuel_tons)

    assert fighter.command is not None
    assert fighter.command.bridge is not None
    assert fighter.command.bridge.tons == pytest.approx(_expected.bridge_tons)
    assert fighter.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)

    assert fighter.computer is not None
    assert fighter.computer.hardware is not None
    assert fighter.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)

    assert fighter.sensors.primary.tons == pytest.approx(_expected.sensor_tons)
    assert fighter.sensors.primary.cost == pytest.approx(_expected.sensor_cost_mcr * 1_000_000)

    assert fighter.weapons is not None
    assert fighter.weapons.fixed_mounts[0].cost == pytest.approx(_expected.fixed_mount_cost_mcr * 1_000_000)
    assert fighter.weapons.fixed_mounts[0].power == pytest.approx(_expected.fixed_mount_power)

    assert fighter.habitation is not None
    assert fighter.habitation.cabin_space is not None
    assert fighter.habitation.cabin_space.tons == pytest.approx(_expected.cabin_space_tons)
    assert fighter.habitation.cabin_space.cost == pytest.approx(_expected.cabin_space_cost_mcr * 1_000_000)

    assert fighter.available_power == pytest.approx(_expected.available_power)
    assert fighter.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert fighter.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert fighter.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert fighter.weapon_power_load == pytest.approx(_expected.power_weapons)
    assert fighter.total_power_load == pytest.approx(_expected.total_power)
    assert fighter.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert fighter.sales_price_new == pytest.approx(_expected.sales_price_mcr * 1_000_000)
    assert fighter.expenses.maintenance == pytest.approx(_expected.maintenance_cr)
    crew = [(role.role, quantity, role.monthly_salary) for role, quantity in fighter.crew.grouped_roles]
    assert crew == _expected.crew
    assert fighter.notes.errors == _expected.expected_errors
    assert fighter.notes.warnings == _expected.expected_warnings


def test_gothta_has_no_crew_notes():
    fighter = build_gothta_ambush_fighter()
    spec = fighter.build_spec()
    assert spec.crew_notes.infos == _expected.expected_crew_infos
    assert spec.crew_notes.warnings == _expected.expected_crew_warnings
