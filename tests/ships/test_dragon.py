import pytest

from ceres import armour, hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import AutoRepair1, Computer25, ComputerSection, Evade1, FireControl2
from ceres.drives import DriveSection, FusionPlantTL12, MDrive7, PowerSection
from ceres.habitation import HabitationSection, Staterooms
from ceres.hull import ImprovedStealth
from ceres.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ExtendedArrays,
    ImprovedSensors,
    SensorsSection,
    SensorStations,
)
from ceres.storage import CargoSection, FuelSection, OperationFuel
from ceres.systems import Airlock, CommonArea, MedicalBay, RepairDrones, SystemsSection, Workshop
from ceres.weapons import Barbette, Bay, MissileStorage, WeaponsSection

from ._markdown_output import write_markdown_output


def build_dragon() -> ship.Ship:
    """
    Modeled subset of refs/dragon.txt.

    Not yet modeled from the reference:
    - armored bulkheads
    - backup computer
    - armored weapons / advanced size reduction
    - point defense battery
    - crew armory, biosphere, training facility
    - stores and spares
    - armored missile storage
    """

    return ship.Ship(
        ship_class='Dragon',
        ship_type='System Defense Boat',
        military=True,
        tl=13,
        displacement=400,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull.model_copy(
                update={'description': 'Streamlined-Needle Hull', 'reinforced': True},
            ),
            stealth=ImprovedStealth(),
            radiation_shielding=True,
            armour=armour.CrystalironArmour(protection=13),
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive7(armored=True)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=450)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16)),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Computer25(fib=True),
            software=[AutoRepair1(), FireControl2(), Evade1()],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(),
            countermeasures=CountermeasuresSuite(),
            signal_processing=EnhancedSignalProcessing(),
            extended_arrays=ExtendedArrays(),
            sensor_stations=SensorStations(count=2),
        ),
        weapons=WeaponsSection(
            barbettes=[Barbette(weapon='particle'), Barbette(weapon='particle')],
            bays=[Bay(size='small', weapon='missile')],
            missile_storage=MissileStorage(count=480),
        ),
        systems=SystemsSection(
            repair_drones=RepairDrones(),
            medical_bay=MedicalBay(),
            workshop=Workshop(),
        ),
        habitation=HabitationSection(
            staterooms=Staterooms(count=10),
            common_area=CommonArea(tons=10.0),
        ),
    )


def test_dragon_modeled_subset_matches_current_model():
    dragon = build_dragon()

    assert dragon.tl == 13
    assert dragon.displacement == 400
    assert dragon.hull_points == 176
    assert dragon.hull_cost == pytest.approx(36_000_000)

    assert dragon.hull.stealth is not None
    assert dragon.hull.stealth.cost == pytest.approx(40_000_000)
    assert dragon.hull.radiation_shielding is True

    armour_part = dragon.hull.armour
    assert armour_part is not None
    assert armour_part.tons == pytest.approx(78.0)
    assert armour_part.cost == pytest.approx(15_600_000)

    assert len(dragon.hull.airlocks) == 4
    assert all(airlock.tons == 0.0 for airlock in dragon.hull.airlocks)

    assert dragon.drives is not None
    assert dragon.drives.m_drive is not None
    assert dragon.drives.m_drive.tons == pytest.approx(30.8)
    assert dragon.drives.m_drive.cost == pytest.approx(56_560_000)
    assert dragon.drives.m_drive.power == pytest.approx(280.0)

    assert dragon.power is not None
    assert dragon.power.fusion_plant is not None
    assert dragon.power.fusion_plant.tons == pytest.approx(30.0)
    assert dragon.power.fusion_plant.cost == pytest.approx(30_000_000)

    assert dragon.fuel is not None
    assert dragon.fuel.operation_fuel is not None
    assert dragon.fuel.operation_fuel.tons == pytest.approx(12.0)
    assert dragon.fuel.fuel_scoops is not None
    assert dragon.fuel.fuel_scoops.cost == 0.0

    assert dragon.command is not None
    assert dragon.command.bridge is not None
    assert dragon.command.bridge.tons == pytest.approx(20.0)
    assert dragon.command.bridge.cost == pytest.approx(2_500_000)

    assert dragon.computer is not None
    assert dragon.computer.hardware is not None
    assert dragon.computer.hardware.cost == pytest.approx(15_000_000)
    assert dragon.computer.hardware.build_item() == 'Computer/25/fib'

    assert dragon.sensors.primary.tons == pytest.approx(3.0)
    assert dragon.sensors.primary.cost == pytest.approx(4_300_000)
    assert dragon.sensors.countermeasures is not None
    assert dragon.sensors.countermeasures.tons == pytest.approx(2.0)
    assert dragon.sensors.countermeasures.cost == pytest.approx(4_000_000)
    assert dragon.sensors.signal_processing is not None
    assert dragon.sensors.signal_processing.tons == pytest.approx(2.0)
    assert dragon.sensors.signal_processing.cost == pytest.approx(8_000_000)
    assert dragon.sensors.extended_arrays is not None
    assert dragon.sensors.extended_arrays.tons == pytest.approx(6.0)
    assert dragon.sensors.extended_arrays.cost == pytest.approx(8_600_000)
    assert dragon.sensors.sensor_stations is not None
    assert dragon.sensors.sensor_stations.tons == pytest.approx(2.0)
    assert dragon.sensors.sensor_stations.cost == pytest.approx(1_000_000)

    assert dragon.weapons is not None
    assert len(dragon.weapons.barbettes) == 2
    assert dragon.weapons.barbettes[0].build_item() == 'Particle Barbette'
    assert dragon.weapons.barbettes[0].tons == pytest.approx(5.0)
    assert len(dragon.weapons.bays) == 1
    assert dragon.weapons.bays[0].build_item() == 'Small Missile Bay'
    assert dragon.weapons.bays[0].tons == pytest.approx(50.0)
    assert dragon.weapons.missile_storage is not None
    assert dragon.weapons.missile_storage.tons == pytest.approx(40.0)

    assert dragon.systems is not None
    assert dragon.systems.repair_drones is not None
    assert dragon.systems.repair_drones.tons == pytest.approx(4.0)
    assert dragon.systems.medical_bay is not None
    assert dragon.systems.workshop is not None

    assert dragon.habitation is not None
    assert dragon.habitation.staterooms is not None
    assert dragon.habitation.staterooms.tons == pytest.approx(40.0)
    assert dragon.habitation.common_area is not None
    assert dragon.habitation.common_area.tons == pytest.approx(10.0)

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(50.2)
    assert dragon.production_cost == pytest.approx(269_260_000)
    assert dragon.sales_price_new == pytest.approx(242_334_000)


def test_dragon_power_and_crew_for_current_subset():
    dragon = build_dragon()

    assert dragon.available_power == pytest.approx(450.0)
    assert dragon.basic_hull_power_load == pytest.approx(80.0)
    assert dragon.maneuver_power_load == pytest.approx(280.0)
    assert dragon.sensor_power_load == pytest.approx(13.0)
    assert dragon.weapon_power_load == pytest.approx(35.0)
    assert dragon.total_power_load == pytest.approx(409.0)

    assert [(role.role, role.count, role.monthly_salary) for role in dragon.crew_roles] == [
        ('PILOT', 3, 6_000),
        ('ENGINEER', 2, 4_000),
        ('GUNNER', 5, 2_000),
        ('SENSOR OPERATOR', 3, 4_000),
        ('OFFICER', 1, 5_000),
    ]


def test_dragon_markdown_output():
    dragon = build_dragon()
    table = dragon.markdown_table()
    write_markdown_output('test_dragon', table)

    assert '## *Dragon* System Defense Boat | TL13 | Hull 176' in table
    assert '| Hull | Streamlined-Needle Hull | **400.00** |  | 36000.00 |' in table
    assert '|  | Improved Stealth |  |  | 40000.00 |' in table
    assert '| Propulsion | M-Drive 7 (Armored) | 30.80 | 280.00 | 56560.00 |' in table
    assert '| Power | Fusion (TL 12) | 30.00 | **450.00** | 30000.00 |' in table
    assert '| Fuel | 16 weeks of operation | 12.00 |  |  |' in table
    assert '|  | Enhanced Signal Processing | 2.00 | 2.00 | 8000.00 |' in table
    assert '|  | Extended Arrays | 6.00 | 6.00 | 8600.00 |' in table
    assert '|  | Sensor Stations × 2 | 2.00 |  | 1000.00 |' in table
    assert '| Weapons | Particle Barbette × 2 | 10.00 | 30.00 | 16000.00 |' in table
    assert '|  | Small Missile Bay | 50.00 | 5.00 | 12000.00 |' in table
