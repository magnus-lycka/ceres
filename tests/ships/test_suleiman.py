"""Reference ship case based on refs/Suleiman.md.

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
  - stores and spares (`RI-001`)
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer, ComputerSection, JumpControl
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive, MDrive, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
from ceres.make.ship.storage import CargoSection, FuelProcessor, FuelSection, JumpFuel, OperationFuel
from ceres.make.ship.systems import Airlock, ProbeDrones, SystemsSection, Workshop
from ceres.make.ship.weapons import Turret, WeaponsSection
from ceres.report import render_ship_html

from ._output import write_html_output, write_json_output


def build_suleiman() -> ship.Ship:
    """Build the Suleiman reference case from refs/Suleiman.md."""
    return ship.Ship(
        ship_class='Suleiman',
        ship_type='Scout/Courier',
        tl=12,
        displacement=100,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            armour=armour.CrystalironArmour(tl=12, protection=4),
            airlocks=[Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive(2), j_drive=JDrive(2)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=60)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5, bis=True), software=[JumpControl(2)]),
        sensors=SensorsSection(primary=MilitarySensors()),
        weapons=WeaponsSection(turrets=[Turret(size='double')]),
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
    fusion_plant = suleiman.power.fusion_plant
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
    workshop = suleiman.systems.workshop

    assert suleiman.tl == 12
    assert suleiman.displacement == 100

    assert armour_part is not None
    assert armour_part.description == 'Crystaliron'
    assert armour_part.protection == 4
    assert armour_part.tons == pytest.approx(6.0)
    assert armour_part.cost == 1_200_000

    assert m_drive is not None
    assert m_drive.level == 2
    assert m_drive.tons == pytest.approx(2.0)
    assert m_drive.cost == 4_000_000
    assert m_drive.power == 20

    assert jump_drive is not None
    assert jump_drive.level == 2
    assert jump_drive.tons == pytest.approx(10.0)
    assert jump_drive.cost == 15_000_000
    assert jump_drive.power == 20

    assert fusion_plant is not None
    assert fusion_plant.output == 60
    assert fusion_plant.tons == pytest.approx(4.0)
    assert fusion_plant.cost == 4_000_000

    assert jump_fuel is not None
    assert jump_fuel.parsecs == 2
    assert jump_fuel.tons == pytest.approx(20.0)

    assert operation_fuel is not None
    assert operation_fuel.weeks == 12
    assert operation_fuel.tons == pytest.approx(2.0)

    assert fuel_processor is not None
    assert fuel_processor.tons == pytest.approx(2.0)
    assert fuel_processor.cost == 100_000
    assert fuel_processor.power == 2

    assert bridge is not None
    assert bridge.tons == pytest.approx(10.0)
    assert bridge.cost == 500_000

    assert suleiman.computer is not None
    assert suleiman.computer.hardware is not None
    assert suleiman.computer.hardware.processing == 5
    assert suleiman.computer.hardware.jump_control_processing == 10
    assert suleiman.computer.hardware.cost == 45_000
    assert [(package.description, package.cost) for package in suleiman.computer.software_packages.values()] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000),
    ]

    assert sensors is not None
    assert sensors.tons == pytest.approx(2.0)
    assert sensors.cost == 4_100_000
    assert sensors.power == 2

    assert docking_space is not None
    assert docking_space.craft.shipping_size == 4
    assert docking_space.tons == pytest.approx(5.0)
    assert docking_space.cost == 1_250_000
    assert docking_space.power == 0

    assert staterooms is not None
    assert len(staterooms) == 4
    assert sum(room.tons for room in staterooms) == pytest.approx(16.0)
    assert sum(room.cost for room in staterooms) == 2_000_000

    assert len(airlocks) == 1
    assert airlocks[0].tons == pytest.approx(0.0)
    assert airlocks[0].cost == 0.0

    assert probe_drones is not None
    assert probe_drones.count == 10
    assert probe_drones.tons == pytest.approx(2.0)
    assert probe_drones.cost == 1_000_000
    assert probe_drones.power == 0

    assert workshop is not None
    assert workshop.tons == pytest.approx(6.0)
    assert workshop.cost == 900_000
    assert workshop.power == 0

    assert CargoSection.cargo_tons_for_ship(suleiman) == pytest.approx(12.0)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in suleiman.crew.grouped_roles] == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
        ('GUNNER', 1, 2_000),
    ]

    assert suleiman.hull_cost == 6_000_000
    assert suleiman.production_cost == 41_045_000
    assert suleiman.sales_price_new == 36_940_500

    assert suleiman.available_power == 60
    assert suleiman.basic_hull_power_load == 20
    assert suleiman.maneuver_power_load == 20
    assert suleiman.jump_power_load == 20
    assert suleiman.fuel_power_load == 2
    assert suleiman.sensor_power_load == 2
    assert suleiman.weapon_power_load == 1
    assert suleiman.total_power_load == 45


def test_jump_drive_2_without_jump_control_2_adds_local_note():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(j_drive=JDrive(2)),
        computer=ComputerSection(hardware=Computer(5, bis=True)),
    )
    assert my_ship.drives is not None
    assert my_ship.drives.j_drive is not None
    assert [(note.category.value, note.message) for note in my_ship.drives.j_drive.notes] == [
        ('item', 'Jump 2'),
        ('warning', 'No Jump Control software'),
    ]


def test_suleiman_spec_structure():
    suleiman = build_suleiman()
    spec = suleiman.build_spec()

    assert spec.ship_class == 'Suleiman'
    assert spec.ship_type == 'Scout/Courier'
    assert spec.tl == 12
    assert spec.hull_points == 40

    hull_row = spec.row('Streamlined Hull')
    assert hull_row.section == 'Hull'
    assert hull_row.tons == 100.0
    assert hull_row.cost == 6_000_000
    assert hull_row.emphasize_tons is True

    basic = spec.row('Basic Ship Systems')
    assert basic.section == 'Hull'
    assert basic.power == 20.0

    armour = spec.row('Crystaliron, Armour: 4')
    assert armour.section == 'Hull'
    assert armour.tons == pytest.approx(6.0)
    assert armour.cost == 1_200_000

    fusion = spec.row('Fusion (TL 12), Power 60')
    assert fusion.section == 'Power'
    assert fusion.tons == pytest.approx(4.0)
    assert fusion.power == 60.0
    assert fusion.emphasize_power is True

    mdrive = spec.row('M-Drive 2')
    assert mdrive.section == 'Propulsion'
    assert mdrive.power == -20.0

    sensors = spec.row('Military Grade Sensors')
    assert sensors.section == 'Sensors'
    assert any('Jammers' in n.message for n in sensors.notes)

    airlock = spec.row('Airlock (2 tons)')
    assert airlock.section == 'Hull'
    assert airlock.tons is None

    fuel_tank = spec.row('J-2, 20 weeks of operation', section='Fuel')
    assert fuel_tank.section == 'Fuel'
    assert fuel_tank.tons == pytest.approx(22.0)

    fuel_scoops = spec.row('Fuel Scoops')
    assert fuel_scoops.section == 'Fuel'

    air_raft = spec.row('Air/Raft')
    assert air_raft.section == 'Craft'
    assert air_raft.cost == 250_000

    jc2 = spec.row('Jump Control/2')
    assert jc2.section == 'Computer'
    assert jc2.cost == 200_000

    staterooms = spec.row('Staterooms')
    assert staterooms.section == 'Habitation'
    assert staterooms.quantity == 4

    probe_drones = spec.row('Probe Drones')
    assert probe_drones.section == 'Systems'
    assert probe_drones.quantity == 10

    assert spec.expenses[1].label == 'Sales Price New'
    assert spec.expenses[1].amount == 36_940_500
    assert any(e.label == 'Life Support Facilities' and e.amount == 4_000 for e in spec.expenses)
    assert any(e.label == 'Life Support People' and e.amount == 8_000 for e in spec.expenses)
    assert any(e.label == 'Fuel' and e.amount == pytest.approx(4_066.6666666667) for e in spec.expenses)
    assert any(e.label == 'Crew Salaries' and e.amount == 17_000 for e in spec.expenses)

    assert any(c.role == 'ENGINEER' and c.quantity is None and c.salary == 4_000 for c in spec.crew)
    assert any(c.role == 'GUNNER' and c.quantity is None and c.salary == 2_000 for c in spec.crew)
    assert any(c.role == 'PILOT' and c.quantity is None and c.salary == 6_000 for c in spec.crew)
    assert any(p.kind == 'MIDDLE' and p.quantity == 4 for p in spec.passengers)


@pytest.mark.generated_output
def test_suleiman_report_html_output():
    suleiman = build_suleiman()
    html = render_ship_html(suleiman)
    write_html_output('test_suleiman', html)
    write_json_output('test_suleiman', suleiman)

    assert '<title>Suleiman</title>' in html
    assert '<p class="banner-meta">Scout/Courier | TL12 | Hull 40</p>' in html
    assert '<header class="sidebar-card-title">Crew</header>' in html
    assert '<header class="sidebar-card-title">Power</header>' in html
    assert '<header class="sidebar-card-title">Costs</header>' in html
    assert '<th class="num">Cost (MCr)</th>' in html
    assert '<td>Military Grade Sensors</td>' in html
    assert '<td class="item-cell">J-2, 20 weeks of operation</td>' in html
    assert '<td>Fusion (TL 12), Power 60</td><td class="num power-positive">60.00</td>' in html
    assert '<td>Basic Ship Systems</td><td class="num">20.00</td>' in html
    assert 'MIDDLE × 2' not in html
    assert 'Life Support People' in html
    assert 'Scout/Courier | TL12 | Hull 40' in html
    assert '<p class="eyebrow">' not in html


def test_jump_drive_with_lower_jump_control_warns_on_drive():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(j_drive=JDrive(2)),
        computer=ComputerSection(hardware=Computer(5, bis=True), software=[JumpControl(1)]),
    )
    assert my_ship.drives is not None
    assert my_ship.drives.j_drive is not None
    assert [(note.category.value, note.message) for note in my_ship.drives.j_drive.notes] == [
        ('item', 'Jump 2'),
        ('warning', 'Limited to Jump 1 by control software'),
    ]


def test_jump_control_without_jump_drive_warns_on_software():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        computer=ComputerSection(hardware=Computer(5, bis=True), software=[JumpControl(2)]),
    )
    assert my_ship.computer is not None
    explicit_jump_control = my_ship.computer.software_packages[JumpControl]
    assert [(note.category.value, note.message) for note in explicit_jump_control.notes] == [
        ('item', 'Jump Control/2'),
        ('warning', 'No jump drive installed'),
    ]


def test_jump_control_with_higher_rating_than_drive_warns_on_software():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(j_drive=JDrive(2)),
        computer=ComputerSection(hardware=Computer(10, bis=True), software=[JumpControl(3)]),
    )
    assert my_ship.computer is not None
    explicit_jump_control = my_ship.computer.software_packages[JumpControl]
    assert [(note.category.value, note.message) for note in explicit_jump_control.notes] == [
        ('item', 'Jump Control/3'),
        ('warning', 'Limited to Jump 2 by drive capacity'),
    ]


def test_higher_jump_control_replaces_lower_one():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(j_drive=JDrive(2)),
        computer=ComputerSection(hardware=Computer(10, bis=True), software=[JumpControl(2), JumpControl(3)]),
    )

    assert my_ship.computer is not None
    assert [package.description for package in my_ship.computer.software_packages.values()] == [
        'Library',
        'Manoeuvre/0',
        'Intellect',
        'Jump Control/3',
    ]

    jump_control = my_ship.computer.software_packages[JumpControl]
    assert ('warning', 'Redundant Jump Control/2 added') in [
        (note.category.value, note.message) for note in jump_control.notes
    ]
