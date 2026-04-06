import pytest

from ceres import armour, ship
from ceres.bridge import Bridge
from ceres.computer import Computer5, Computer10, JumpControl1, JumpControl2, JumpControl3
from ceres.crafts import AirRaft, InternalDockingSpace
from ceres.drives import FuelProcessor, FusionPlantTL12, JumpDrive2, JumpFuel, MDrive2, OperationFuel
from ceres.habitation import Staterooms
from ceres.sensors import MilitarySensors
from ceres.systems import Airlock, ProbeDrones, Workshop
from ceres.weapons import DoubleTurret

from ._markdown_output import write_markdown_output


def build_suleiman() -> ship.Ship:
    return ship.Ship(
        ship_class='Suleiman',
        ship_type='Scout/Courier',
        tl=12,
        displacement=100,
        design_type=ship.ShipDesignType.STANDARD,
        hull=ship.Hull(
            configuration=ship.streamlined_hull,
            armour=armour.CrystalironArmour(tl=12, protection=4),
        ),
        m_drive=MDrive2(),
        jump_drive=JumpDrive2(),
        fusion_plant=FusionPlantTL12(output=60),
        jump_fuel=JumpFuel(parsecs=2),
        operation_fuel=OperationFuel(weeks=12),
        fuel_processor=FuelProcessor(tons=2),
        bridge=Bridge(),
        computer=Computer5(bis=True),
        software=[JumpControl2()],
        sensors=MilitarySensors(),
        turrets=[DoubleTurret()],
        docking_space=InternalDockingSpace(craft=AirRaft()),
        staterooms=Staterooms(count=4),
        airlocks=[Airlock()],
        probe_drones=ProbeDrones(count=10),
        workshop=Workshop(),
    )


def test_suleiman_matches_first_modeled_reference_slice():
    suleiman = build_suleiman()

    armour_part = suleiman.hull.armour
    m_drive = suleiman.m_drive
    jump_drive = suleiman.jump_drive
    fusion_plant = suleiman.fusion_plant
    jump_fuel = suleiman.jump_fuel
    operation_fuel = suleiman.operation_fuel
    fuel_processor = suleiman.fuel_processor
    bridge = suleiman.bridge
    sensors = suleiman.sensors
    docking_space = suleiman.docking_space
    staterooms = suleiman.staterooms
    airlocks = suleiman.airlocks
    probe_drones = suleiman.probe_drones
    workshop = suleiman.workshop

    assert suleiman.tl == 12
    assert suleiman.displacement == 100

    assert armour_part is not None
    assert armour_part.description == 'Crystaliron'
    assert armour_part.protection == 4
    assert armour_part.tons == pytest.approx(6.0)
    assert armour_part.cost == 1_200_000

    assert m_drive is not None
    assert m_drive.rating == 2
    assert m_drive.tons == pytest.approx(2.0)
    assert m_drive.cost == 4_000_000
    assert m_drive.power == 20

    assert jump_drive is not None
    assert jump_drive.rating == 2
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
    assert operation_fuel.tons == pytest.approx(1.2)

    assert fuel_processor is not None
    assert fuel_processor.tons == pytest.approx(2.0)
    assert fuel_processor.cost == 100_000
    assert fuel_processor.power == 2

    assert bridge is not None
    assert bridge.tons == pytest.approx(10.0)
    assert bridge.cost == 500_000

    assert suleiman.computer is not None
    assert suleiman.computer.processing == 5
    assert suleiman.computer.jump_control_processing == 10
    assert suleiman.computer.cost == 45_000
    assert [(package.description, package.cost) for package in suleiman.software_packages] == [
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
    assert staterooms.count == 4
    assert staterooms.tons == pytest.approx(16.0)
    assert staterooms.cost == 2_000_000

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

    assert suleiman.cargo == pytest.approx(12.8)

    assert [(role.role, role.count, role.monthly_salary) for role in suleiman.crew_roles] == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
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
        hull=ship.Hull(configuration=ship.streamlined_hull),
        jump_drive=JumpDrive2(),
        computer=Computer5(bis=True),
    )
    assert my_ship.jump_drive is not None
    assert [(note.category.value, note.message) for note in my_ship.jump_drive.notes] == [
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

    fusion = spec.row('Fusion (TL 12)')
    assert fusion.section == 'Power'
    assert fusion.tons == pytest.approx(4.0)
    assert fusion.power == 60.0
    assert fusion.emphasize_power is True

    mdrive = spec.row('M-Drive 2')
    assert mdrive.section == 'Propulsion'
    assert mdrive.power == -20.0

    sensors = spec.row('Military Grade')
    assert sensors.section == 'Sensors'
    assert any('Jammers' in n.message for n in sensors.notes)

    airlock = spec.row('Airlock')
    assert airlock.section == 'Hull'
    assert airlock.tons is None

    fuel_tank = spec.row('J-2, 12 weeks of operation', section='Fuel')
    assert fuel_tank.section == 'Fuel'
    assert fuel_tank.tons == pytest.approx(21.2)

    fuel_scoops = spec.row('Fuel Scoops')
    assert fuel_scoops.section == 'Fuel'

    air_raft = spec.row('Air/Raft')
    assert air_raft.section == 'Craft'
    assert air_raft.cost == 250_000

    jc2 = spec.row('Jump Control/2')
    assert jc2.section == 'Computer'
    assert jc2.cost == 200_000

    assert spec.expenses[1].label == 'Sales Price New'
    assert spec.expenses[1].amount == 36_940_500
    assert any(e.label == 'Life Support' and e.amount == 12_000 for e in spec.expenses)
    assert any(e.label == 'Fuel' and e.amount == 4_000 for e in spec.expenses)
    assert any(e.label == 'Crew Salaries' and e.amount == 15_000 for e in spec.expenses)

    assert any(c.role == 'ENGINEER' and c.salary == 4_000 for c in spec.crew)


def test_suleiman_markdown_output():
    suleiman = build_suleiman()
    table = suleiman.markdown_table()
    write_markdown_output('test_suleiman', table)


def test_markdown_table_renders_inline_warning_on_jump_drive_row():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        jump_drive=JumpDrive2(),
        computer=Computer5(bis=True),
    )
    table = my_ship.markdown_table()
    write_markdown_output('test_suleiman_missing_jump_control', table)
    assert '|  | *WARNING:* No Jump Control software |  |  |  |' in table


def test_jump_drive_with_lower_jump_control_warns_on_drive():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        jump_drive=JumpDrive2(),
        computer=Computer5(bis=True),
        software=[JumpControl1()],
    )
    assert my_ship.jump_drive is not None
    assert [(note.category.value, note.message) for note in my_ship.jump_drive.notes] == [
        ('item', 'Jump 2'),
        ('warning', 'Limited to Jump 1 by control software'),
    ]


def test_jump_control_without_jump_drive_warns_on_software():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        computer=Computer5(bis=True),
        software=[JumpControl2()],
    )
    explicit_jump_control = my_ship.software[0]
    assert [(note.category.value, note.message) for note in explicit_jump_control.notes] == [
        ('item', 'Jump Control/2'),
        ('warning', 'No jump drive installed'),
    ]


def test_jump_control_with_higher_rating_than_drive_warns_on_software():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        jump_drive=JumpDrive2(),
        computer=Computer10(bis=True),
        software=[JumpControl3()],
    )
    explicit_jump_control = my_ship.software[0]
    assert [(note.category.value, note.message) for note in explicit_jump_control.notes] == [
        ('item', 'Jump Control/3'),
        ('warning', 'Limited to Jump 2 by drive capacity'),
    ]


def test_markdown_table_renders_inline_warning_on_high_jump_control_row():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        jump_drive=JumpDrive2(),
        computer=Computer10(bis=True),
        software=[JumpControl3()],
    )
    table = my_ship.markdown_table()
    write_markdown_output('test_suleiman_high_jump_control', table)
    assert '|  | *WARNING:* Limited to Jump 2 by drive capacity |  |  |  |' in table


def test_markdown_table_renders_inline_warning_on_missing_jump_drive_row():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        computer=Computer5(bis=True),
        software=[JumpControl2()],
    )
    table = my_ship.markdown_table()
    write_markdown_output('test_suleiman_missing_jump_drive', table)
    assert '|  | *WARNING:* No jump drive installed |  |  |  |' in table
