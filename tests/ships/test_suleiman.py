import pytest

from ceres import armour, ship
from ceres.bridge import Bridge
from ceres.computer import Computer5
from ceres.drives import FuelProcessor, FusionPlantTL12, JumpDrive2, JumpFuel, MDrive2, OperationFuel
from ceres.habitation import Staterooms
from ceres.sensors import MilitaryGradeSensors
from ceres.weapons import DoubleTurret


def build_suleiman() -> ship.Ship:
    return ship.Ship(
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
        sensors=MilitaryGradeSensors(),
        turrets=[DoubleTurret()],
        staterooms=Staterooms(count=4),
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
    staterooms = suleiman.staterooms

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

    assert sensors is not None
    assert sensors.tons == pytest.approx(2.0)
    assert sensors.cost == 4_100_000
    assert sensors.power == 2

    assert staterooms is not None
    assert staterooms.count == 4
    assert staterooms.tons == pytest.approx(16.0)
    assert staterooms.cost == 2_000_000

    assert [(role.role, role.count, role.monthly_salary) for role in suleiman.crew_roles] == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
    ]
    assert suleiman.total_crew == 3
    assert suleiman.crew_salary_cost == 15_000
    assert suleiman.life_support_cost == 12_000

    assert suleiman.hull_cost == 6_000_000

    assert suleiman.available_power == 60
    assert suleiman.basic_hull_power_load == 20
    assert suleiman.maneuver_power_load == 20
    assert suleiman.jump_power_load == 20
    assert suleiman.fuel_power_load == 2
    assert suleiman.sensor_power_load == 2
    assert suleiman.weapon_power_load == 1
    assert suleiman.total_power_load == 45
