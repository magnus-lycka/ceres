import pytest
from ceres.report.tycho_pdf import _build_typst_source

from tycho import hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection, FireControl
from tycho.drives import DriveSection, FusionPlantTL12, MDrive, PowerSection, RDrive
from tycho.habitation import CabinSpace, HabitationSection
from tycho.sensors import MilitarySensors, SensorsSection
from tycho.storage import FuelScoops, FuelSection, OperationFuel, ReactionFuel
from tycho.systems import Aerofins
from tycho.weapons import FixedMount, MountWeapon, WeaponsSection



def build_gothta_ambush_fighter() -> ship.Ship:
    return ship.Ship(
        ship_class='Gothta',
        ship_type='Ambush Fighter',
        military=True,
        tl=12,
        displacement=20,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            pressure_hull=True,
            airlocks=[],
            aerofins=Aerofins(),
        ),
        drives=DriveSection(
            m_drive=MDrive(6),
            r_drive=RDrive(4, high_burn_thruster=True),
        ),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=30)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=2),
            reaction_fuel=ReactionFuel(minutes=60),
            fuel_scoops=FuelScoops(free=True),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5), software=[FireControl(1)]),
        sensors=SensorsSection(primary=MilitarySensors()),
        weapons=WeaponsSection(
            fixed_mounts=[FixedMount(weapons=[MountWeapon(weapon='pulse_laser')])],
        ),
        habitation=HabitationSection(cabin_space=CabinSpace(tons=1.5)),
    )


def test_gothta_ambush_fighter_matches_current_subset():
    fighter = build_gothta_ambush_fighter()

    assert fighter.hull_cost == pytest.approx(12_000_000)
    assert fighter.hull_points == 8
    assert fighter.hull.pressure_hull_tons(fighter.displacement) == pytest.approx(5.0)

    assert fighter.drives is not None
    assert fighter.drives.m_drive is not None
    assert fighter.drives.m_drive.tons == pytest.approx(1.2)
    assert fighter.drives.m_drive.cost == pytest.approx(2_400_000)
    assert fighter.drives.r_drive is not None
    assert fighter.drives.r_drive.tons == pytest.approx(1.6)
    assert fighter.drives.r_drive.cost == pytest.approx(320_000)
    assert fighter.drives.r_drive.build_item() == 'High-Burn Thruster, Thrust 4'

    assert fighter.power is not None
    assert fighter.power.fusion_plant is not None
    assert fighter.power.fusion_plant.tons == pytest.approx(2.0)
    assert fighter.power.fusion_plant.cost == pytest.approx(2_000_000)

    assert fighter.fuel is not None
    assert fighter.fuel.operation_fuel is not None
    assert fighter.fuel.operation_fuel.tons == pytest.approx(0.1)
    assert fighter.fuel.reaction_fuel is not None
    assert fighter.fuel.reaction_fuel.tons == pytest.approx(2.0)

    assert fighter.command is not None
    assert fighter.command.bridge is not None
    assert fighter.command.bridge.tons == pytest.approx(3.0)
    assert fighter.command.bridge.cost == pytest.approx(500_000)

    assert fighter.computer is not None
    assert fighter.computer.hardware is not None
    assert fighter.computer.hardware.cost == pytest.approx(30_000)

    assert fighter.sensors.primary.tons == pytest.approx(2.0)
    assert fighter.sensors.primary.cost == pytest.approx(4_100_000)

    assert fighter.weapons is not None
    assert fighter.weapons.fixed_mounts[0].cost == pytest.approx(1_100_000)
    assert fighter.weapons.fixed_mounts[0].power == pytest.approx(3.0)

    assert fighter.habitation is not None
    assert fighter.habitation.cabin_space is not None
    assert fighter.habitation.cabin_space.tons == pytest.approx(1.5)
    assert fighter.habitation.cabin_space.cost == pytest.approx(75_000)

    assert fighter.available_power == pytest.approx(30.0)
    assert fighter.basic_hull_power_load == pytest.approx(4.0)
    assert fighter.maneuver_power_load == pytest.approx(12.0)
    assert fighter.sensor_power_load == pytest.approx(2.0)
    assert fighter.weapon_power_load == pytest.approx(3.0)
    assert fighter.total_power_load == pytest.approx(21.0)
    assert fighter.production_cost == pytest.approx(24_625_000)
    assert fighter.sales_price_new == pytest.approx(24_625_000)
    assert fighter.expenses.maintenance == pytest.approx(2052.0)
    assert [(role.role, quantity, role.monthly_salary) for role, quantity in fighter.crew.grouped_roles] == [
        ('PILOT', 1, 6_000),
    ]


def test_gothta_pdf_places_ship_error_below_main_table():
    fighter = build_gothta_ambush_fighter()
    src = _build_typst_source(fighter.build_spec(), page_size='a4')
    assert 'Error: No airlock installed' in src
    assert 'Cargo' in src
    assert src.index('Cargo') < src.index('Error: No airlock installed')


def test_gothta_has_no_crew_notes():
    fighter = build_gothta_ambush_fighter()
    spec = fighter.build_spec()
    assert spec.crew_notes == []
