"""Reference ship case based on refs/tycho/Suleiman.md.

Purpose:
- provide a compact source-derived scout/courier baseline
- exercise standard TL12 Streamlined/J-2/M-2/Fusion-60 design rules
- keep one explicit case where we follow Ceres for derived crew and fuel
  expenses rather than an internally inconsistent source export

Source handling for this test case:
- supported: hull, armour, drives, power plant, fuel tankage, bridge,
  computer, sensors, turret, docking space, air/raft, probe drones,
  workshop, staterooms, cargo, production cost, discounted purchase price
- ignored for test-case modelling:
  - battle-load figures (`TCS-002`)
  - income / profit rows (`TCS-003`)
- deliberate interpretation:
  - crew follows Ceres rules rather than the source crew row, because the
    source lists three crew while also fitting a double turret that requires
    a gunner
  - fuel expense follows the current Ceres operating-cost model, including
    purchased operation fuel, rather than the source's jump-fuel-only total
- source inconsistency:
  - the source life-support total fits four crew plus four middle passengers
    even though the source crew row lists only three crew
- model interpretation rather than dedicated installed rows:
  - stores and spares (`RIS-001`)
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive2, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import CargoSection, FuelProcessor, FuelSection, JumpFuel, OperationFuel
from ceres.make.ship.systems import Airlock, ProbeDrones, SystemsSection, Workshop
from ceres.make.ship.weapons import DoubleTurret, WeaponsSection

_expected = SimpleNamespace(
    ship_class='Suleiman',
    ship_type='Scout/Courier',
    tl=12,
    displacement=100,
    hull_cost_mcr=6.0,  # Streamlined Hull: 6,000,000
    hull_points=40,
    armour_description='Crystaliron',
    armour_protection=4,
    armour_tons=6.0,
    armour_cost_mcr=1.2,  # Crystaliron: 1,200,000
    m_drive_level=2,
    m_drive_tons=2.0,
    m_drive_cost_mcr=4.0,
    m_drive_power=20,
    j_drive_level=2,
    j_drive_tons=10.0,
    j_drive_cost_mcr=15.0,
    j_drive_power=20,
    plant_output=60,
    plant_tons=4.0,
    plant_cost_mcr=4.0,
    jump_fuel_parsecs=2,
    jump_fuel_tons=20.0,
    op_fuel_weeks=12,
    op_fuel_tons=1.2,  # ref: 1.20 tons; Ceres gives 2.0 per RIS-007
    fuel_processor_tons=2.0,
    fuel_processor_cost_cr=100_000,
    fuel_processor_power=2,
    bridge_tons=10.0,
    bridge_cost_cr=500_000,
    computer_processing=5,
    computer_cost_cr=45_000,  # Computer/5 bis
    software_packages=[
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000.0),
    ],
    sensor_tons=2.0,
    sensor_cost_cr=4_100_000,
    sensor_power=2,
    docking_space_shipping_size=4,
    docking_space_tons=5.0,
    docking_space_cost_cr=1_250_000,
    docking_space_power=0,
    stateroom_count=4,
    stateroom_tons_total=16.0,
    stateroom_cost_total_cr=2_000_000,
    airlock_count=1,
    airlock_tons=0.0,
    airlock_cost=0.0,
    probe_drones_count=10,
    probe_drones_tons=2.0,
    probe_drones_cost_cr=1_000_000,
    probe_drones_power=0,
    workshop_tons=6.0,
    workshop_cost_cr=900_000,
    workshop_power=0,
    cargo_tons=12.0,
    available_power=60,
    power_basic=20,  # Basic/Hull 20 PP
    power_maneuver=20,
    power_jump=20,
    power_fuel=2,
    power_sensors=2,
    power_weapon=1,
    total_power=45,  # Ceres total_power_load (excludes jump from running total?)
    production_cost_mcr=41.045,  # Design Cost: 41,045,000
    sales_price_mcr=36.9405,  # Discount Cost: 36,940,500
    crew=[
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
        ('GUNNER', 1, 2_000),
    ],
    expected_errors=[],
    expected_warnings=[],
    expected_crew_infos=[],
    expected_crew_warnings=[],
    spec_rows={
        'Streamlined Hull': 'Hull',
        'Basic Ship Systems': 'Hull',
        'Crystaliron, Armour: 4': 'Hull',
        'Fusion (TL 12), Power 60': 'Power',
        'M-Drive 2': 'Propulsion',
        'Military Grade Sensors': 'Sensors',
        'Airlock (2 tons)': 'Hull',
        'J-2, 20 weeks of operation': 'Fuel',
        'Fuel Scoops': 'Fuel',
        'Air/Raft': 'Craft',
        'Jump Control/2': 'Computer',
        'Staterooms': 'Habitation',
        'Probe Drones': 'Systems',
    },
    sensor_note_messages=[
        'Passive optical and thermal sensors, Radar, Lidar, Jammers, EMCON',
        'DM +0 to Electronics (comms) and Electronics (sensors) checks',
    ],
    spec_fuel_tank_tons=22.0,
    spec_air_raft_cost=250_000,
    spec_jump_control_cost=200_000,
    spec_expenses=[
        ('Production Cost', 41_045_000.0),
        ('Sales Price New', 36_940_500.0),
        ('Mortgage', 153_918.75),
        ('Maintenance', 3_078.0),
        ('Life Support Facilities', 4_000.0),
        ('Life Support People', 8_000.0),
        ('Fuel', 4_066.6666666666665),
        ('Crew Salaries', 17_000.0),
        ('Total Expenses', 190_063.41666666666),
    ],
    spec_crew=[
        ('PILOT', None, 6_000),
        ('ASTROGATOR', None, 5_000),
        ('ENGINEER', None, 4_000),
        ('GUNNER', None, 2_000),
    ],
    spec_passengers=[('MIDDLE', 4)],
)

# Ceres gives op_fuel_tons=2.0 per RIS-007 (rounds up to whole dTon for ≥100t ships), not 1.2 as in ref
_expected.op_fuel_tons = 2.0


def build_suleiman() -> ship.Ship:
    """Build the Suleiman reference case from refs/tycho/Suleiman.md."""
    return ship.Ship(
        ship_class='Suleiman',
        ship_type='Scout/Courier',
        tl=12,
        displacement=100,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            armour=armour.CrystalironArmour(protection=4),
            airlocks=[Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=60)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(bis=True), software=[JumpControl(rating=2)]),
        sensors=SensorsSection(primary=MilitarySensors()),
        weapons=WeaponsSection(turrets=[DoubleTurret()]),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))]),
        habitation=HabitationSection(staterooms=[Stateroom()] * 4),
        systems=SystemsSection(internal_systems=[Workshop()], drones=[ProbeDrones(count=10)]),
    )


def test_suleiman_matches_first_modeled_reference_slice():
    suleiman = build_suleiman()

    armour_part = suleiman.hull.armour
    assert suleiman.drives is not None
    m_drive = suleiman.drives.m_drive
    jump_drive = suleiman.drives.j_drive
    assert suleiman.power is not None
    fusion_plant = suleiman.power.plant
    assert suleiman.fuel is not None
    jump_fuel = suleiman.fuel.jump_fuel
    operation_fuel = suleiman.fuel.operation_fuel
    fuel_processor = suleiman.fuel.fuel_processor
    assert suleiman.command is not None
    bridge = suleiman.command.bridge
    sensors = suleiman.sensors.primary
    assert suleiman.craft is not None
    docking_space = suleiman.craft.internal_housing[0]
    assert suleiman.habitation is not None
    staterooms = suleiman.habitation.staterooms
    airlocks = suleiman.hull.airlocks
    assert suleiman.systems is not None
    probe_drones = suleiman.systems.drones[0]
    workshop = suleiman.systems.workshops[0]

    assert suleiman.tl == _expected.tl
    assert suleiman.displacement == _expected.displacement

    assert armour_part is not None
    assert armour_part.description == _expected.armour_description
    assert armour_part.protection == _expected.armour_protection
    assert armour_part.tons == pytest.approx(_expected.armour_tons)
    assert armour_part.cost == _expected.armour_cost_mcr * 1_000_000

    assert m_drive is not None
    assert m_drive.level == _expected.m_drive_level
    assert m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert m_drive.cost == _expected.m_drive_cost_mcr * 1_000_000
    assert m_drive.power == _expected.m_drive_power

    assert jump_drive is not None
    assert jump_drive.level == _expected.j_drive_level
    assert jump_drive.tons == pytest.approx(_expected.j_drive_tons)
    assert jump_drive.cost == _expected.j_drive_cost_mcr * 1_000_000
    assert jump_drive.power == _expected.j_drive_power

    assert fusion_plant is not None
    assert fusion_plant.output == _expected.plant_output
    assert fusion_plant.tons == pytest.approx(_expected.plant_tons)
    assert fusion_plant.cost == _expected.plant_cost_mcr * 1_000_000

    assert jump_fuel is not None
    assert jump_fuel.parsecs == _expected.jump_fuel_parsecs
    assert jump_fuel.tons == pytest.approx(_expected.jump_fuel_tons)

    assert operation_fuel is not None
    assert operation_fuel.weeks == _expected.op_fuel_weeks
    assert operation_fuel.tons == pytest.approx(_expected.op_fuel_tons)

    assert fuel_processor is not None
    assert fuel_processor.tons == pytest.approx(_expected.fuel_processor_tons)
    assert fuel_processor.cost == _expected.fuel_processor_cost_cr
    assert fuel_processor.power == _expected.fuel_processor_power

    assert bridge is not None
    assert bridge.tons == pytest.approx(_expected.bridge_tons)
    assert bridge.cost == _expected.bridge_cost_cr

    assert suleiman.computer is not None
    assert suleiman.computer.hardware is not None
    assert suleiman.computer.hardware.processing == _expected.computer_processing
    assert suleiman.computer.hardware.can_run_jump_control(10)
    assert suleiman.computer.hardware.cost == _expected.computer_cost_cr
    assert [(package.description, package.cost) for package in suleiman.computer.software_packages] == (
        _expected.software_packages
    )

    assert sensors is not None
    assert sensors.tons == pytest.approx(_expected.sensor_tons)
    assert sensors.cost == _expected.sensor_cost_cr
    assert sensors.power == _expected.sensor_power

    assert docking_space is not None
    assert docking_space.craft.shipping_size == _expected.docking_space_shipping_size
    assert docking_space.tons == pytest.approx(_expected.docking_space_tons)
    assert docking_space.cost == _expected.docking_space_cost_cr
    assert docking_space.power == _expected.docking_space_power

    assert staterooms is not None
    assert len(staterooms) == _expected.stateroom_count
    assert sum(room.tons for room in staterooms) == pytest.approx(_expected.stateroom_tons_total)
    assert sum(room.cost for room in staterooms) == _expected.stateroom_cost_total_cr

    assert len(airlocks) == _expected.airlock_count
    assert airlocks[0].tons == pytest.approx(_expected.airlock_tons)
    assert airlocks[0].cost == _expected.airlock_cost

    assert probe_drones is not None
    assert isinstance(probe_drones, ProbeDrones)
    assert probe_drones.count == _expected.probe_drones_count
    assert probe_drones.tons == pytest.approx(_expected.probe_drones_tons)
    assert probe_drones.cost == _expected.probe_drones_cost_cr
    assert probe_drones.power == _expected.probe_drones_power

    assert workshop is not None
    assert workshop.tons == pytest.approx(_expected.workshop_tons)
    assert workshop.cost == _expected.workshop_cost_cr
    assert workshop.power == _expected.workshop_power

    assert CargoSection.cargo_tons_for_ship(suleiman) == pytest.approx(_expected.cargo_tons)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in suleiman.crew.grouped_roles] == (
        _expected.crew
    )

    assert suleiman.hull_cost == _expected.hull_cost_mcr * 1_000_000
    assert suleiman.production_cost == _expected.production_cost_mcr * 1_000_000
    assert suleiman.sales_price_new == _expected.sales_price_mcr * 1_000_000

    assert suleiman.available_power == _expected.available_power
    assert suleiman.basic_hull_power_load == _expected.power_basic
    assert suleiman.maneuver_power_load == _expected.power_maneuver
    assert suleiman.jump_power_load == _expected.power_jump
    assert suleiman.fuel_power_load == _expected.power_fuel
    assert suleiman.sensor_power_load == _expected.power_sensors
    assert suleiman.weapon_power_load == _expected.power_weapon
    assert suleiman.total_power_load == _expected.total_power
    assert suleiman.notes.errors == _expected.expected_errors
    assert suleiman.notes.warnings == _expected.expected_warnings
    assert suleiman.crew.notes.infos == _expected.expected_crew_infos
    assert suleiman.crew.notes.warnings == _expected.expected_crew_warnings


def test_suleiman_spec_structure():
    suleiman = build_suleiman()
    spec = suleiman.build_spec()

    assert spec.ship_class == _expected.ship_class
    assert spec.ship_type == _expected.ship_type
    assert spec.tl == _expected.tl
    assert spec.hull_points == _expected.hull_points

    hull_row = spec.row('Streamlined Hull')
    assert hull_row.section == _expected.spec_rows['Streamlined Hull']
    assert hull_row.tons == _expected.displacement
    assert hull_row.cost == _expected.hull_cost_mcr * 1_000_000
    assert hull_row.emphasize_tons is True

    basic = spec.row('Basic Ship Systems')
    assert basic.section == _expected.spec_rows['Basic Ship Systems']
    assert basic.power == float(_expected.power_basic)

    armour = spec.row('Crystaliron, Armour: 4')
    assert armour.section == _expected.spec_rows['Crystaliron, Armour: 4']
    assert armour.tons == pytest.approx(_expected.armour_tons)
    assert armour.cost == _expected.armour_cost_mcr * 1_000_000

    fusion = spec.row('Fusion (TL 12), Power 60')
    assert fusion.section == _expected.spec_rows['Fusion (TL 12), Power 60']
    assert fusion.tons == pytest.approx(_expected.plant_tons)
    assert fusion.power == float(_expected.plant_output)
    assert fusion.emphasize_power is True

    mdrive = spec.row('M-Drive 2')
    assert mdrive.section == _expected.spec_rows['M-Drive 2']
    assert mdrive.power == float(-_expected.m_drive_power)

    sensors = spec.row('Military Grade Sensors')
    assert sensors.section == _expected.spec_rows['Military Grade Sensors']
    assert [note.message for note in sensors.notes] == _expected.sensor_note_messages

    airlock = spec.row('Airlock (2 tons)')
    assert airlock.section == _expected.spec_rows['Airlock (2 tons)']
    assert airlock.tons is None

    fuel_tank = spec.row('J-2, 20 weeks of operation', section='Fuel')
    assert fuel_tank.section == _expected.spec_rows['J-2, 20 weeks of operation']
    assert fuel_tank.tons == pytest.approx(_expected.spec_fuel_tank_tons)

    fuel_scoops = spec.row('Fuel Scoops')
    assert fuel_scoops.section == _expected.spec_rows['Fuel Scoops']

    air_raft = spec.row('Air/Raft')
    assert air_raft.section == _expected.spec_rows['Air/Raft']
    assert air_raft.cost == _expected.spec_air_raft_cost

    jc2 = spec.row('Jump Control/2')
    assert jc2.section == _expected.spec_rows['Jump Control/2']
    assert jc2.cost == _expected.spec_jump_control_cost

    staterooms = spec.row('Staterooms')
    assert staterooms.section == _expected.spec_rows['Staterooms']
    assert staterooms.quantity == _expected.stateroom_count

    probe_drones = spec.row('Probe Drones')
    assert probe_drones.section == _expected.spec_rows['Probe Drones']
    assert probe_drones.quantity == _expected.probe_drones_count

    assert [(expense.label, expense.amount) for expense in spec.expenses] == _expected.spec_expenses
    assert [(crew.role, crew.quantity, crew.salary) for crew in spec.crew] == _expected.spec_crew
    assert [(passenger.kind, passenger.quantity) for passenger in spec.passengers] == _expected.spec_passengers
