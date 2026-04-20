import pytest

from tycho import armour, hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import AutoRepair1, Computer20, Computer25, ComputerSection, Evade1, FireControl2
from tycho.drives import DriveSection, FusionPlantTL12, MDrive7, PowerSection
from tycho.habitation import HabitationSection, Staterooms
from tycho.hull import ImprovedStealth
from tycho.parts import HighTechnology, SizeReduction
from tycho.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ExtendedArrays,
    ImprovedSensors,
    SensorsSection,
    SensorStations,
)
from tycho.storage import CargoSection, FuelSection, OperationFuel
from tycho.systems import (
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
from tycho.weapons import Barbette, Bay, MissileStorage, PointDefenseBattery, WeaponsSection


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
                update={'reinforced': True},
            ),
            stealth=ImprovedStealth(),
            radiation_shielding=True,
            armour=armour.CrystalironArmour(protection=13),
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive7(armoured_bulkhead=True)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=450, armoured_bulkhead=True)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16, armoured_bulkhead=True)),
        command=CommandSection(bridge=Bridge(holographic=True, armoured_bulkhead=True)),
        computer=ComputerSection(
            hardware=Computer25(fib=True),
            backup_hardware=Computer20(fib=True),
            software=[AutoRepair1(), FireControl2(), Evade1()],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(armoured_bulkhead=True),
            countermeasures=CountermeasuresSuite(armoured_bulkhead=True),
            signal_processing=EnhancedSignalProcessing(armoured_bulkhead=True),
            extended_arrays=ExtendedArrays(armoured_bulkhead=True),
            sensor_stations=SensorStations(count=2, armoured_bulkhead=True),
        ),
        weapons=WeaponsSection(
            barbettes=[
                Barbette(weapon='particle', armoured_bulkhead=True),
                Barbette(weapon='particle', armoured_bulkhead=True),
            ],
            bays=[
                Bay(
                    size='small',
                    weapon='missile',
                    customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction),
                    armoured_bulkhead=True,
                )
            ],
            point_defense_batteries=[PointDefenseBattery(kind='laser', rating=2, armoured_bulkhead=True)],
            missile_storage=MissileStorage(count=480, armoured_bulkhead=True),
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
    assert [bulkhead.tons for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(
        [2.8, 3.0, 1.2, 2.0, 0.3, 0.2, 0.2, 0.6, 0.2, 0.5, 0.5, 3.5, 2.0, 4.0]
    )
    assert [bulkhead.cost for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(
        [
            560_000,
            600_000,
            240_000,
            400_000,
            60_000,
            40_000,
            40_000,
            120_000,
            40_000,
            100_000,
            100_000,
            700_000,
            400_000,
            800_000,
        ]
    )

    assert len(dragon.hull.airlocks) == 4
    assert all(airlock.tons == 0.0 for airlock in dragon.hull.airlocks)

    assert dragon.drives is not None
    assert dragon.drives.m_drive is not None
    assert dragon.drives.m_drive.tons == pytest.approx(28.0)
    assert dragon.drives.m_drive.cost == pytest.approx(56_000_000)
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
    assert dragon.sensors.sensor_stations.build_item() == 'Sensor Stations'
    assert dragon.sensors.sensor_stations.tons == pytest.approx(2.0)
    assert dragon.sensors.sensor_stations.cost == pytest.approx(1_000_000)

    assert dragon.weapons is not None
    assert len(dragon.weapons.barbettes) == 2
    assert dragon.weapons.barbettes[0].build_item() == 'Particle Barbette'
    assert dragon.weapons.barbettes[0].tons == pytest.approx(5.0)
    assert len(dragon.weapons.bays) == 1
    assert dragon.weapons.bays[0].build_item() == 'Small Missile Bay'
    assert dragon.weapons.bays[0].tons == pytest.approx(35.0)
    assert dragon.weapons.bays[0].cost == pytest.approx(18_000_000)
    assert len(dragon.weapons.point_defense_batteries) == 1
    assert dragon.weapons.point_defense_batteries[0].build_item() == 'Point Defense Battery: Type II-L'
    assert dragon.weapons.point_defense_batteries[0].tons == pytest.approx(20.0)
    assert dragon.weapons.point_defense_batteries[0].cost == pytest.approx(10_000_000)
    assert dragon.weapons.missile_storage is not None
    assert dragon.weapons.missile_storage.tons == pytest.approx(40.0)
    assert dragon.weapons.missile_storage.cost == pytest.approx(0.0)

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

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(18.00)
    assert dragon.production_cost == pytest.approx(308_250_000)
    assert dragon.sales_price_new == pytest.approx(277_425_000)


def test_dragon_power_and_crew_for_current_subset():
    dragon = build_dragon()

    assert dragon.available_power == pytest.approx(450.0)
    assert dragon.basic_hull_power_load == pytest.approx(80.0)
    assert dragon.maneuver_power_load == pytest.approx(280.0)
    assert dragon.sensor_power_load == pytest.approx(15.0)
    assert dragon.weapon_power_load == pytest.approx(55.0)
    assert dragon.total_power_load == pytest.approx(435.0)

    assert [(role.role, role.count, role.monthly_salary) for role in dragon.crew_roles] == [
        ('CAPTAIN', 1, 10_000),
        ('PILOT', 3, 6_000),
        ('ENGINEER', 2, 4_000),
        ('MAINTENANCE', 1, 1_000),
        ('GUNNER', 5, 2_000),
        ('SENSOR OPERATOR', 3, 4_000),
        ('MEDIC', 1, 4_000),
        ('OFFICER', 1, 5_000),
    ]


def test_armoured_bulkhead_protected_parts_have_individual_notes():
    dragon = build_dragon()
    assert dragon.drives is not None
    all_notes = [(n.category.value, n.message) for n in dragon.drives.m_drive.notes]
    assert ('info', 'Armoured bulkhead, see Hull section.') in all_notes
