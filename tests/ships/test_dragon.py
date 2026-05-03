"""Reference ship case based on refs/dragon.txt.

Purpose:
- preserve a source-derived military baseline for the Dragon line
- exercise reinforced streamlined TL13 SDB modelling with bulkheads, sensors,
  bays, barbettes, point defence, and military crew rules
- keep one explicit example of source-to-model normalization where the source
  export groups some protected items and bulkheads differently from Ceres

Source handling for this test case:
- supported: hull, stealth, radiation shielding, armour, drives, power, fuel,
  bridge, computer, sensors, weapons, systems, common area, production cost,
  discounted purchase price
- ignored for test-case modelling:
  - battle-load figures (`TCS-002`)
  - income / profit rows (`TCS-003`)
- normalized when mapping into Ceres:
  - source armored-bulkhead rows are represented as protected parts plus
    separate Hull bulkhead entries (`TCS-001`)
- deliberate interpretation:
  - the source crew manifest is preserved verbatim as explicit `ship.crew.roles` data
  - Ceres surfaces crew-rule mismatches as warnings instead of silently
    normalizing the crew
  - point-defence batteries do not require dedicated gunners
- source inconsistency:
  - the source life-support total does not fit the source crew count
- model interpretation rather than dedicated installed rows:
  - stores and spares (`RI-001`)
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import AutoRepair, Computer, ComputerSection, Evade, FireControl
from ceres.make.ship.crew import (
    Astrogator,
    Captain,
    Engineer,
    Gunner,
    Maintenance,
    Medic,
    Officer,
    Pilot,
    SensorOperator,
    ShipCrew,
)
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.hull import ImprovedStealth
from ceres.make.ship.parts import HighTechnology, SizeReduction
from ceres.make.ship.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ExtendedArrays,
    ImprovedSensors,
    SensorsSection,
    SensorStations,
)
from ceres.make.ship.storage import CargoSection, FuelSection, OperationFuel
from ceres.make.ship.systems import (
    Airlock,
    Armoury,
    Biosphere,
    CommonArea,
    MedicalBay,
    RepairDrones,
    SystemsSection,
    TrainingFacility,
    Workshop,
)
from ceres.make.ship.weapons import Barbette, Bay, MissileStorage, PointDefenseBattery, WeaponsSection


def build_dragon() -> ship.Ship:
    """
    Build the Dragon reference case from refs/dragon.txt.

    Source aspects intentionally not carried over verbatim:
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
        drives=DriveSection(m_drive=MDrive(level=7, armoured_bulkhead=True)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=450, armoured_bulkhead=True)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16, armoured_bulkhead=True)),
        command=CommandSection(bridge=Bridge(holographic=True, armoured_bulkhead=True)),
        computer=ComputerSection(
            hardware=Computer(score=25, fib=True),
            backup_hardware=Computer(score=20, fib=True),
            software=[AutoRepair(rating=1), FireControl(rating=2), Evade(rating=1)],
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
                    customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                )
            ],
            point_defense_batteries=[PointDefenseBattery(kind='laser', rating=2, armoured_bulkhead=True)],
            missile_storage=MissileStorage(count=480, armoured_bulkhead=True),
        ),
        systems=SystemsSection(
            internal_systems=[
                Armoury(),
                Biosphere(tons=4.0),
                MedicalBay(),
                TrainingFacility(trainees=2),
                Workshop(),
            ],
            drones=[RepairDrones()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            common_area=CommonArea(tons=10.0),
        ),
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 3,
                Astrogator(),
                *[Engineer()] * 2,
                Maintenance(),
                Medic(),
                *[Gunner()] * 6,
                *[SensorOperator()] * 3,
                Officer(),
            ]
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
    assert dragon.weapons.barbettes[0].build_item() == 'Barbette (Damage × 3 after armour)'
    assert dragon.weapons.barbettes[0].tons == pytest.approx(5.0)
    assert len(dragon.weapons.bays) == 1
    assert dragon.weapons.bays[0].build_item() == 'Small Bay (12 missiles per salvo)'
    assert dragon.weapons.bays[0].tons == pytest.approx(35.0)
    assert dragon.weapons.bays[0].cost == pytest.approx(18_000_000)
    assert len(dragon.weapons.point_defense_batteries) == 1
    assert dragon.weapons.point_defense_batteries[0].build_item() == 'Point Defence Laser Battery Type II'
    assert dragon.weapons.point_defense_batteries[0].tons == pytest.approx(20.0)
    assert dragon.weapons.point_defense_batteries[0].cost == pytest.approx(10_000_000)
    assert dragon.weapons.missile_storage is not None
    assert dragon.weapons.missile_storage.tons == pytest.approx(40.0)
    assert dragon.weapons.missile_storage.cost == pytest.approx(0.0)

    assert dragon.systems is not None
    assert len(dragon.systems.armouries) == 1
    assert dragon.systems.armouries[0].tons == pytest.approx(1.0)
    assert dragon.systems.biosphere is not None
    assert dragon.systems.biosphere.tons == pytest.approx(4.0)
    assert len(dragon.systems.drones) == 1
    assert dragon.systems.drones[0].tons == pytest.approx(4.0)
    assert dragon.systems.medical_bay is not None
    assert dragon.systems.training_facility is not None
    assert dragon.systems.workshop is not None

    assert dragon.habitation is not None
    assert dragon.habitation.staterooms is not None
    assert sum(room.tons for room in dragon.habitation.staterooms) == pytest.approx(40.0)
    assert dragon.habitation.common_area is not None
    assert dragon.habitation.common_area.tons == pytest.approx(10.0)

    # The source export includes a stores/spares row in cargo. Ceres treats that
    # as guidance (RI-001) rather than as a separately installed design item.
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

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in dragon.crew.grouped_roles] == [
        ('CAPTAIN', 1, 10_000),
        ('PILOT', 3, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 2, 4_000),
        ('MAINTENANCE', 1, 1_000),
        ('MEDIC', 1, 4_000),
        ('GUNNER', 6, 2_000),
        ('SENSOR OPERATOR', 3, 4_000),
        ('OFFICER', 1, 5_000),
    ]
    assert dragon.expenses.life_support == pytest.approx(29_000.0)
    assert dragon.expenses.crew_salaries == pytest.approx(75_000.0)
    assert ('info', 'ASTROGATOR above recommended count: 1 > 0') in [
        (note.category.value, note.message) for note in dragon.crew.notes
    ]
    assert ('info', 'MAINTENANCE above recommended count: 1 > 0') in [
        (note.category.value, note.message) for note in dragon.crew.notes
    ]
    assert ('info', 'GUNNER above recommended count: 6 > 5') in [
        (note.category.value, note.message) for note in dragon.crew.notes
    ]


def test_armoured_bulkhead_protected_parts_have_individual_notes():
    dragon = build_dragon()
    assert dragon.drives is not None and dragon.drives.m_drive is not None
    all_notes = [(n.category.value, n.message) for n in dragon.drives.m_drive.notes]
    assert ('info', 'Armoured bulkhead, see Hull section.') in all_notes
