import pytest

from ceres import armour, hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import AutoRepair1, Computer20, Computer25, ComputerSection, Evade1, FireControl2
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
from ceres.systems import (
    Airlock,
    Biosphere,
    CommonArea,
    CrewArmory,
    MedicalBay,
    RepairDrones,
    SystemsSection,
    TrainingFacility,
    Workshop,
)
from ceres.weapons import ArmoredMissileStorage, Barbette, Bay, PointDefenseBattery, WeaponsSection

from ._markdown_output import write_markdown_output


def build_dragon() -> ship.Ship:
    """
    Modeled subset of refs/dragon.txt.

    Not yet modeled from the reference:
    - exact bay count/formatting from source export
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
            armoured_bulkheads=[
                hull.ArmouredBulkhead(protected_tonnage=30.0, protected_item='M-Drive'),
                hull.ArmouredBulkhead(protected_tonnage=12.0, protected_item='Operation Fuel'),
                hull.ArmouredBulkhead(protected_tonnage=20.0, protected_item='Bridge'),
                hull.ArmouredBulkhead(protected_tonnage=13.0, protected_item='Sensors'),
            ],
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive7(armored=True)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=450)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16)),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Computer25(fib=True),
            backup_hardware=Computer20(fib=True),
            software=[AutoRepair1(), FireControl2(), Evade1()],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(),
            countermeasures=CountermeasuresSuite(),
            signal_processing=EnhancedSignalProcessing(),
            extended_arrays=ExtendedArrays(),
            sensor_stations=SensorStations(count=2, armored=True),
        ),
        weapons=WeaponsSection(
            barbettes=[Barbette(weapon='particle', armored=True), Barbette(weapon='particle', armored=True)],
            bays=[Bay(size='small', weapon='missile', armored=True, size_reduction=True)],
            point_defense_batteries=[PointDefenseBattery(kind='laser', rating=2, armored=True)],
            missile_storage=ArmoredMissileStorage(count=480),
        ),
        systems=SystemsSection(
            crew_armory=CrewArmory(capacity=25),
            biosphere=Biosphere(tons=4.0),
            repair_drones=RepairDrones(),
            medical_bay=MedicalBay(),
            training_facility=TrainingFacility(trainees=2),
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
    assert [bulkhead.tons for bulkhead in dragon.hull.armoured_bulkheads] == pytest.approx([3.0, 1.2, 2.0, 1.3])
    assert [bulkhead.cost for bulkhead in dragon.hull.armoured_bulkheads] == pytest.approx(
        [600_000, 240_000, 400_000, 260_000]
    )

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
    assert dragon.computer.backup_hardware is not None
    assert dragon.computer.backup_hardware.cost == pytest.approx(7_500_000)
    assert dragon.computer.backup_hardware.build_item() == 'Computer/20/fib'

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
    assert dragon.sensors.sensor_stations.build_item() == 'Additional Armored Sensor Stations'
    assert dragon.sensors.sensor_stations.tons == pytest.approx(2.2)
    assert dragon.sensors.sensor_stations.cost == pytest.approx(1_040_000)

    assert dragon.weapons is not None
    assert len(dragon.weapons.barbettes) == 2
    assert dragon.weapons.barbettes[0].build_item() == 'Particle Barbette, Armored'
    assert dragon.weapons.barbettes[0].tons == pytest.approx(5.5)
    assert len(dragon.weapons.bays) == 1
    assert dragon.weapons.bays[0].build_item() == 'Small Missile Bay, Armored, Adv - Size Reduction'
    assert dragon.weapons.bays[0].tons == pytest.approx(49.5)
    assert len(dragon.weapons.point_defense_batteries) == 1
    assert dragon.weapons.point_defense_batteries[0].build_item() == 'Point Defense Battery: Type II-L, Armored'
    assert dragon.weapons.point_defense_batteries[0].tons == pytest.approx(22.0)
    assert dragon.weapons.missile_storage is not None
    assert dragon.weapons.missile_storage.tons == pytest.approx(44.0)
    assert dragon.weapons.missile_storage.cost == pytest.approx(800_000)

    assert dragon.systems is not None
    assert dragon.systems.crew_armory is not None
    assert dragon.systems.crew_armory.tons == pytest.approx(1.0)
    assert dragon.systems.biosphere is not None
    assert dragon.systems.biosphere.tons == pytest.approx(4.0)
    assert dragon.systems.repair_drones is not None
    assert dragon.systems.repair_drones.tons == pytest.approx(4.0)
    assert dragon.systems.medical_bay is not None
    assert dragon.systems.training_facility is not None
    assert dragon.systems.workshop is not None

    assert dragon.habitation is not None
    assert dragon.habitation.staterooms is not None
    assert dragon.habitation.staterooms.tons == pytest.approx(40.0)
    assert dragon.habitation.common_area is not None
    assert dragon.habitation.common_area.tons == pytest.approx(10.0)

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(7.0)
    assert dragon.production_cost == pytest.approx(293_650_000)
    assert dragon.sales_price_new == pytest.approx(264_285_000)


def test_dragon_power_and_crew_for_current_subset():
    dragon = build_dragon()

    assert dragon.available_power == pytest.approx(450.0)
    assert dragon.basic_hull_power_load == pytest.approx(80.0)
    assert dragon.maneuver_power_load == pytest.approx(280.0)
    assert dragon.sensor_power_load == pytest.approx(13.0)
    assert dragon.weapon_power_load == pytest.approx(55.0)
    assert dragon.total_power_load == pytest.approx(433.0)

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
    assert '|  | Armoured Bulkhead for M-Drive | 3.00 |  | 600.00 |' in table
    assert '|  | • Critical hit severity reduced by 1 if >1 |  |  |  |' in table
    assert '| Propulsion | M-Drive 7 (Armored) | 30.80 | 280.00 | 56560.00 |' in table
    assert '| Power | Fusion (TL 12) | 30.00 | **450.00** | 30000.00 |' in table
    assert '| Fuel | 16 weeks of operation | 12.00 |  |  |' in table
    assert '| Computer | Computer/25/fib |  |  | 15000.00 |' in table
    assert '|  | Backup Computer/20/fib |  |  | 7500.00 |' in table
    assert '|  | Enhanced Signal Processing | 2.00 | 2.00 | 8000.00 |' in table
    assert '|  | Extended Arrays | 6.00 | 6.00 | 8600.00 |' in table
    assert '|  | Additional Armored Sensor Stations × 2 | 2.20 |  | 1040.00 |' in table
    assert '| Weapons | Particle Barbette, Armored × 2 | 11.00 | 30.00 | 16200.00 |' in table
    assert '|  | Small Missile Bay, Armored, Adv - Size Reduction | 49.50 | 5.00 | 14100.00 |' in table
    assert '|  | Point Defense Battery: Type II-L, Armored | 22.00 | 20.00 | 10400.00 |' in table
    assert '| Systems | Crew Armory: Supports 25 Crew | 1.00 |  | 250.00 |' in table
    assert '|  | Biosphere | 4.00 | 4.00 | 800.00 |' in table
    assert '|  | Training Facility: 2-person capacity | 4.00 |  | 800.00 |' in table
    assert '|  | Magazine Armored Missile Storage (480) | 44.00 |  | 800.00 |' in table
    assert '|  | • 4.00 tons needed per 100 days of stores and spares |  |  |  |' in table
