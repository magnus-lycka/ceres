"""Reference ship case based on refs/tycho/dragon.txt.

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
  - stores and spares (`RIS-001`)
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer20, Computer25, ComputerSection
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
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive7, PowerSection
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
from ceres.make.ship.software import (
    AutoRepair,
    Evade,
    FireControl,
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
from ceres.make.ship.weapons import (
    LaserPointDefenseBattery2,
    MissileStorage,
    ParticleBarbette,
    SmallMissileBay,
    WeaponsSection,
)

# Values taken from refs/tycho/dragon.txt unless noted.
# Bulkhead tonnages/costs are derived from Ceres TCS-001 normalization: the
# source groups protected parts and bulkheads together in a single row, while
# Ceres records the protected part at its unprotected size and lists the
# bulkhead separately.
_expected = SimpleNamespace(
    tl=13,
    displacement=400,
    hull_points=176,  # Streamlined-Needle, Reinforced; ref: "Hull: 176"
    hull_cost_mcr=36.0,  # ref: 36,000,000
    stealth_cost_mcr=40.0,  # ref: 40,000,000
    armour_tons=78.0,  # ref: Crystaliron 13; 78.00 tons
    armour_cost_mcr=15.6,  # ref: 15,600,000
    # ref row: "M-Drive: 7, Armored 30.80 / 56,560,000" — Ceres splits the
    # 2.8 ton armoured bulkhead out; drive itself is 28.0 tons / 56,000,000
    m_drive_tons=28.0,
    m_drive_cost_mcr=56.0,
    m_drive_power=280.0,
    plant_tons=30.0,  # ref: Fusion TL 12 Output: 450 — 30.00 tons
    plant_cost_mcr=30.0,  # ref: 30,000,000
    operation_fuel_tons=12.0,  # ref: 16 Weeks of Operation — 12.00 tons
    bridge_tons=20.0,  # ref: Standard Bridge — 20.00 tons
    bridge_cost_mcr=2.5,  # ref: 2,000,000 bridge + 500,000 holographic controls
    computer_cost_mcr=15.0,  # ref: Comp/25/fib — 15,000,000
    computer_backup_cost_mcr=7.5,  # ref: B/U Comp/20/fib — 7,500,000
    # Sensors — ref groups sensor bulkhead as "Armored Bulkhead 1.30 / 260,000"
    # and sensor stations as "2x Additional Armored Sensor Stations 2.20 / 1,040,000".
    # Ceres splits each sensor component's bulkhead individually (TCS-001).
    sensors_primary_tons=3.0,
    sensors_primary_cost_mcr=4.3,
    sensors_countermeasures_tons=2.0,
    sensors_countermeasures_cost_mcr=4.0,
    sensors_signal_processing_tons=2.0,
    sensors_signal_processing_cost_mcr=8.0,
    sensors_extended_arrays_tons=6.0,
    sensors_extended_arrays_cost_mcr=8.6,
    sensors_stations_tons=2.0,
    sensors_stations_cost_mcr=1.0,
    # Weapons — ref groups armoured barbettes as "2x ... 11.00 / 16,200,000";
    # Ceres splits bulkheads out so each barbette is 5.0 tons / 8,000,000 MCr
    # with 0.5-ton / 100,000 Cr bulkhead listed separately.
    barbette_tons=5.0,
    # ref: "1x Small Bay: Missile Bay (S), Armored ... 38.50 / 18,700,000" —
    # Ceres splits 3.5-ton bulkhead; bay itself 35.0 tons / 18,000,000
    bay_tons=35.0,
    bay_cost_mcr=18.0,
    # ref: "1x Point Defense Battery: Type II -L, Armored 22.00 / 10,400,000" —
    # Ceres splits 2.0-ton bulkhead; battery itself 20.0 tons / 10,000,000
    point_defense_tons=20.0,
    point_defense_cost_mcr=10.0,
    # ref: "Armored Missile Storage (480) 44.00 / 800,000" —
    # Ceres splits 4.0-ton bulkhead; storage itself 40.0 tons / 0
    missile_storage_tons=40.0,
    missile_storage_cost=0.0,
    # Armoured bulkhead parts listed in order Ceres yields them (TCS-001):
    # m_drive, plant, fuel, bridge, sensor_primary, sensor_countermeasures,
    # sensor_signal, sensor_stations, sensor_extended_arrays,
    # barbette×2, bay, point_defense, missile_storage
    bulkhead_tons=[2.8, 3.0, 1.2, 2.0, 0.3, 0.2, 0.2, 0.6, 0.2, 0.5, 0.5, 3.5, 2.0, 4.0],
    bulkhead_costs=[
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
    ],
    repair_drones_tons=4.0,
    staterooms_total_tons=40.0,
    common_area_tons=10.0,
    # ref shows "1x 13.52 Ton Cargo Bay" + "Stores and Spares 4.48" = 18.00
    # Ceres treats stores as guidance (RIS-001) not a separate install; total
    # remaining tonnage is asserted as 18.00 to match the published total
    cargo_tons=18.0,
    production_cost_mcr=308.25,  # ref: 308,250,000
    sales_price_mcr=277.425,  # ref: Discount Cost: 277,425,000
    available_power=450.0,  # ref: Available: 450 PP
    power_basic=80.0,  # ref: Basic/Hull 80 PP
    power_maneuver=280.0,  # ref: Maneuver 280 PP
    power_sensors=15.0,  # ref: Sensors 15 PP
    power_weapons=55.0,  # ref: Weapons 55 PP
    total_power=435.0,  # ref: Maximum Load 435
    # ref: Life Support 22,000 — source inconsistency noted in docstring;
    # Ceres calculates 29,000 based on stateroom occupancy rules
    life_support=22_000.0,  # ref value; Ceres gives 29,000 (see docstring)
    crew_salaries=75_000.0,  # ref: Crew Salaries 75,000
)
# Ceres calculates life support from stateroom occupancy, giving 29,000
# (source inconsistency: ref shows 22,000 which does not match crew count)
_expected.life_support = 29_000.0


def build_dragon() -> ship.Ship:
    """
    Build the Dragon reference case from refs/tycho/dragon.txt.

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
        drives=DriveSection(m_drive=MDrive7(armoured_bulkhead=True)),
        power=PowerSection(plant=FusionPlantTL12(output=450, armoured_bulkhead=True)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16, armoured_bulkhead=True)),
        command=CommandSection(bridge=Bridge(holographic=True, armoured_bulkhead=True)),
        computer=ComputerSection(
            hardware=Computer25(fib=True),
            backup_hardware=Computer20(fib=True),
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
                ParticleBarbette(armoured_bulkhead=True),
                ParticleBarbette(armoured_bulkhead=True),
            ],
            bays=[
                SmallMissileBay(
                    customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                )
            ],
            point_defense_batteries=[LaserPointDefenseBattery2(armoured_bulkhead=True)],
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

    assert dragon.tl == _expected.tl
    assert dragon.displacement == _expected.displacement
    assert dragon.hull_points == _expected.hull_points
    assert dragon.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)

    assert dragon.hull.stealth is not None
    assert dragon.hull.stealth.cost == pytest.approx(_expected.stealth_cost_mcr * 1_000_000)
    assert dragon.hull.radiation_shielding is True

    armour_part = dragon.hull.armour
    assert armour_part is not None
    assert armour_part.tons == pytest.approx(_expected.armour_tons)
    assert armour_part.cost == pytest.approx(_expected.armour_cost_mcr * 1_000_000)
    assert [bulkhead.tons for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(_expected.bulkhead_tons)
    assert [bulkhead.cost for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(_expected.bulkhead_costs)

    assert len(dragon.hull.airlocks) == 4
    assert all(airlock.tons == 0.0 for airlock in dragon.hull.airlocks)

    assert dragon.drives is not None
    assert dragon.drives.m_drive is not None
    assert dragon.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert dragon.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert dragon.drives.m_drive.power == pytest.approx(_expected.m_drive_power)

    assert dragon.power is not None
    assert dragon.power.plant is not None
    assert dragon.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert dragon.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)

    assert dragon.fuel is not None
    assert dragon.fuel.operation_fuel is not None
    assert dragon.fuel.operation_fuel.tons == pytest.approx(_expected.operation_fuel_tons)
    assert dragon.fuel.fuel_scoops is not None
    assert dragon.fuel.fuel_scoops.cost == 0.0

    assert dragon.command is not None
    assert dragon.command.bridge is not None
    assert dragon.command.bridge.tons == pytest.approx(_expected.bridge_tons)
    assert dragon.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)

    assert dragon.computer is not None
    assert dragon.computer.hardware is not None
    assert dragon.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)
    assert dragon.computer.hardware.build_item() == 'Computer/25/fib'
    assert dragon.computer.backup_hardware is not None
    assert dragon.computer.backup_hardware.cost == pytest.approx(_expected.computer_backup_cost_mcr * 1_000_000)
    assert dragon.computer.backup_hardware.build_item() == 'Computer/20/fib'

    assert dragon.sensors.primary.tons == pytest.approx(_expected.sensors_primary_tons)
    assert dragon.sensors.primary.cost == pytest.approx(_expected.sensors_primary_cost_mcr * 1_000_000)
    assert dragon.sensors.countermeasures is not None
    assert dragon.sensors.countermeasures.tons == pytest.approx(_expected.sensors_countermeasures_tons)
    assert dragon.sensors.countermeasures.cost == pytest.approx(_expected.sensors_countermeasures_cost_mcr * 1_000_000)
    assert dragon.sensors.signal_processing is not None
    assert dragon.sensors.signal_processing.tons == pytest.approx(_expected.sensors_signal_processing_tons)
    assert dragon.sensors.signal_processing.cost == pytest.approx(
        _expected.sensors_signal_processing_cost_mcr * 1_000_000
    )
    assert dragon.sensors.extended_arrays is not None
    assert dragon.sensors.extended_arrays.tons == pytest.approx(_expected.sensors_extended_arrays_tons)
    assert dragon.sensors.extended_arrays.cost == pytest.approx(_expected.sensors_extended_arrays_cost_mcr * 1_000_000)
    assert dragon.sensors.sensor_stations is not None
    assert dragon.sensors.sensor_stations.build_item() == 'Sensor Stations'
    assert dragon.sensors.sensor_stations.tons == pytest.approx(_expected.sensors_stations_tons)
    assert dragon.sensors.sensor_stations.cost == pytest.approx(_expected.sensors_stations_cost_mcr * 1_000_000)

    assert dragon.weapons is not None
    assert len(dragon.weapons.barbettes) == 2
    assert dragon.weapons.barbettes[0].build_item() == 'Particle Barbette (Damage × 3 after armour)'
    assert dragon.weapons.barbettes[0].tons == pytest.approx(_expected.barbette_tons)
    assert len(dragon.weapons.bays) == 1
    assert dragon.weapons.bays[0].build_item() == 'Small Missile Bay (12 missiles per salvo)'
    assert dragon.weapons.bays[0].tons == pytest.approx(_expected.bay_tons)
    assert dragon.weapons.bays[0].cost == pytest.approx(_expected.bay_cost_mcr * 1_000_000)
    assert len(dragon.weapons.point_defense_batteries) == 1
    assert dragon.weapons.point_defense_batteries[0].build_item() == 'Point Defence Laser Battery Type II'
    assert dragon.weapons.point_defense_batteries[0].tons == pytest.approx(_expected.point_defense_tons)
    assert dragon.weapons.point_defense_batteries[0].cost == pytest.approx(_expected.point_defense_cost_mcr * 1_000_000)
    assert dragon.weapons.missile_storage is not None
    assert dragon.weapons.missile_storage.tons == pytest.approx(_expected.missile_storage_tons)
    assert dragon.weapons.missile_storage.cost == pytest.approx(_expected.missile_storage_cost)

    assert dragon.systems is not None
    assert len(dragon.systems.armouries) == 1
    assert dragon.systems.armouries[0].tons == pytest.approx(1.0)
    assert dragon.systems.biospheres[0] is not None
    assert dragon.systems.biospheres[0].tons == pytest.approx(4.0)
    assert len(dragon.systems.drones) == 1
    assert dragon.systems.drones[0].tons == pytest.approx(_expected.repair_drones_tons)
    assert dragon.systems.medical_bays[0] is not None
    assert dragon.systems.training_facilities[0] is not None
    assert dragon.systems.workshops[0] is not None

    assert dragon.habitation is not None
    assert dragon.habitation.staterooms is not None
    assert sum(room.tons for room in dragon.habitation.staterooms) == pytest.approx(_expected.staterooms_total_tons)
    assert dragon.habitation.common_area is not None
    assert dragon.habitation.common_area.tons == pytest.approx(_expected.common_area_tons)

    # The source export includes a stores/spares row in cargo. Ceres treats that
    # as guidance (RIS-001) rather than as a separately installed design item.
    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(_expected.cargo_tons)
    assert dragon.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert dragon.sales_price_new == pytest.approx(_expected.sales_price_mcr * 1_000_000)


def test_dragon_power_and_crew_for_current_subset():
    dragon = build_dragon()

    assert dragon.available_power == pytest.approx(_expected.available_power)
    assert dragon.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert dragon.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert dragon.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert dragon.weapon_power_load == pytest.approx(_expected.power_weapons)
    assert dragon.total_power_load == pytest.approx(_expected.total_power)

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
    assert dragon.expenses.life_support == pytest.approx(_expected.life_support)
    assert dragon.expenses.crew_salaries == pytest.approx(_expected.crew_salaries)
    crew_infos = dragon.crew.notes.infos
    assert 'ASTROGATOR above recommended count: 1 > 0' in crew_infos
    assert 'MAINTENANCE above recommended count: 1 > 0' in crew_infos
    assert 'GUNNER above recommended count: 6 > 5' in crew_infos


def test_armoured_bulkhead_protected_parts_have_individual_notes():
    dragon = build_dragon()
    assert dragon.drives is not None and dragon.drives.m_drive is not None
    assert 'Armoured bulkhead, see Hull section.' in dragon.drives.m_drive.notes.infos
