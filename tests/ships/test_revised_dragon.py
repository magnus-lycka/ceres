"""Reference ship case based on refs/tycho/revised_dragon.txt.

Purpose:
- preserve a source-derived revised military Dragon variant
- exercise customisations beyond the baseline Dragon, including budget drives,
  very-high-yield barbettes, energy-efficient point defence, and modest
  habitation upgrades
- keep one explicit case where the source crew manifest is preserved verbatim
  and any role mismatches are surfaced as notes

Source handling for this test case:
- supported: hull, stealth, radiation shielding, armour, drives, power, fuel,
  bridge, computer, sensors, weapons, systems, habitation, production cost,
  discounted purchase price
- ignored for test-case modelling:
  - battle-load figures (`TCS-002`)
  - income / profit rows (`TCS-003`)
- normalized when mapping into Ceres:
  - source armored-bulkhead rows are represented as protected parts plus
    separate Hull bulkhead entries (`TCS-001`)
- deliberate interpretation:
  - the source crew manifest is preserved verbatim as explicit `ship.crew.roles` data
  - Ceres surfaces crew-rule mismatches as info/warning notes instead of
    silently normalizing the crew
  - point-defence batteries do not require dedicated gunners
- source inconsistency:
  - the source life-support total does not fit the source crew count
- model interpretation rather than dedicated installed rows:
  - stores and spares (`RI-001`)
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer20, Computer25, ComputerSection
from ceres.make.ship.crew import (
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
from ceres.make.ship.habitation import AdvancedEntertainmentSystem, HabitationSection, Stateroom
from ceres.make.ship.hull import ImprovedStealth
from ceres.make.ship.parts import (
    Advanced,
    Budget,
    EnergyEfficient,
    HighTechnology,
    IncreasedSize,
    SizeReduction,
    VeryAdvanced,
)
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
    VeryHighYield,
    WeaponsSection,
)

# Values taken from refs/tycho/revised_dragon.txt unless noted.
# Bulkhead tonnages/costs are derived from Ceres TCS-001 normalization: the
# source groups protected parts and bulkheads together in a single row, while
# Ceres records the protected part at its unprotected size and lists the
# bulkhead separately.
_expected = SimpleNamespace(
    hull_points=176,  # ref: Streamlined-Needle, Reinforced — Hull: 176
    hull_cost_mcr=36.0,  # ref: 36,000,000
    # ref: "M-Drive: 7 Budget-Increased Size, Armored 38.50 / 42,700,000" —
    # Ceres splits 3.5-ton / 700,000 bulkhead; drive itself 35.0 tons / 42,000,000
    m_drive_tons=35.0,
    m_drive_cost_mcr=42.0,
    # ref: "Fusion TL 12 Output: 482 Budget-Increased Size 40.17 / 24,100,000"
    plant_tons=40.1666666667,  # ref: 40.17
    plant_cost_mcr=24.1,  # ref: 24,100,000
    # ref: "16 Weeks of Operation 16.07" — Ceres rounds up to 17.0
    operation_fuel_tons=17.0,  # ref: 16.07; Ceres rounds up
    # Armoured bulkhead parts listed in order Ceres yields them (TCS-001)
    bulkhead_tons=[3.5, 4.0166666667, 1.6066666667, 2.0, 0.3, 0.2, 0.2, 0.6, 0.2, 0.5, 0.5, 3.5, 2.0, 3.4],
    bulkhead_costs=[
        700_000,
        803_333.3333,
        321_333.3333,
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
        680_000,
    ],
    # ref: "Armored Missile Storage (408) 37.40 / 680,000" —
    # Ceres splits 3.4-ton bulkhead; storage itself 34.0 tons / 0
    missile_storage_tons=34.0,
    missile_storage_cost=0.0,
    # ref: "1x 0.76 Ton Cargo Bay" + "Stores and Spares 4.48" = 5.24 total;
    # Ceres treats stores as guidance (RI-001); remaining usable tonnage gives 4.31
    cargo_tons=4.31,  # ref: ~5.24; Ceres gives 4.31 (fuel tons rounding + RI-001)
    production_cost_mcr=292.8551666667,  # ref: 292,855,166.67
    sales_price_mcr=263.56965,  # ref: 263,569,650.00
    available_power=482.0,  # ref: Available: 482 PP
    power_basic=80.0,  # ref: Basic/Hull 80 PP
    power_maneuver=280.0,  # ref: Maneuver 280 PP
    power_sensors=15.0,  # ref: Sensors 15 PP
    power_weapons=50.0,  # ref: Weapons 50 PP
    total_power=426.0,  # ref: Maximum Load 426 PP
)


def build_revised_dragon() -> ship.Ship:
    """Build the revised Dragon reference case from refs/tycho/revised_dragon.txt."""

    return ship.Ship(
        ship_class='Dragon',
        ship_type='System Defense Boat, Revised',
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
        drives=DriveSection(
            m_drive=MDrive7(customisation=Budget(modifications=[IncreasedSize]), armoured_bulkhead=True)
        ),
        power=PowerSection(
            plant=FusionPlantTL12(
                output=482,
                customisation=Budget(modifications=[IncreasedSize]),
                armoured_bulkhead=True,
            )
        ),
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
                ParticleBarbette(customisation=VeryAdvanced(modifications=[VeryHighYield]), armoured_bulkhead=True),
                ParticleBarbette(customisation=VeryAdvanced(modifications=[VeryHighYield]), armoured_bulkhead=True),
            ],
            bays=[
                SmallMissileBay(
                    customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                )
            ],
            point_defense_batteries=[
                LaserPointDefenseBattery2(
                    customisation=Advanced(modifications=[EnergyEfficient]),
                    armoured_bulkhead=True,
                )
            ],
            missile_storage=MissileStorage(count=408, armoured_bulkhead=True),
        ),
        systems=SystemsSection(
            internal_systems=[Armoury(), MedicalBay(), TrainingFacility(trainees=2), Workshop()],
            drones=[RepairDrones()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            common_area=CommonArea(tons=10.0),
            entertainment=AdvancedEntertainmentSystem(cost=500),
        ),
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 3,
                *[Engineer()] * 3,
                Maintenance(),
                Medic(),
                *[Gunner()] * 5,
                *[SensorOperator()] * 3,
                *[Officer()] * 2,
            ]
        ),
    )


def test_revised_dragon_modeled_subset_matches_current_model():
    dragon = build_revised_dragon()

    assert dragon.hull_points == _expected.hull_points
    assert dragon.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert [bulkhead.tons for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(_expected.bulkhead_tons)
    assert [bulkhead.cost for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(_expected.bulkhead_costs)

    assert dragon.drives is not None
    assert dragon.drives.m_drive is not None
    assert dragon.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert dragon.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)

    assert dragon.power is not None
    assert dragon.power.plant is not None
    assert dragon.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert dragon.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)

    assert dragon.fuel is not None
    assert dragon.fuel.operation_fuel is not None
    assert dragon.fuel.operation_fuel.tons == pytest.approx(_expected.operation_fuel_tons)

    assert dragon.weapons is not None
    assert len(dragon.weapons.barbettes) == 2
    assert dragon.weapons.barbettes[0].build_item() == 'Particle Barbette (Damage × 3 after armour)'
    assert dragon.weapons.missile_storage is not None
    assert dragon.weapons.missile_storage.tons == pytest.approx(_expected.missile_storage_tons)
    assert dragon.weapons.missile_storage.cost == pytest.approx(_expected.missile_storage_cost)

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(_expected.cargo_tons)
    assert dragon.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert dragon.sales_price_new == pytest.approx(_expected.sales_price_mcr * 1_000_000)


def test_revised_dragon_power_and_crew_for_current_subset():
    dragon = build_revised_dragon()

    assert dragon.available_power == pytest.approx(_expected.available_power)
    assert dragon.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert dragon.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert dragon.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert dragon.weapon_power_load == pytest.approx(_expected.power_weapons)
    assert dragon.total_power_load == pytest.approx(_expected.total_power)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in dragon.crew.grouped_roles] == [
        ('CAPTAIN', 1, 10_000),
        ('PILOT', 3, 6_000),
        ('ENGINEER', 3, 4_000),
        ('MAINTENANCE', 1, 1_000),
        ('MEDIC', 1, 4_000),
        ('GUNNER', 5, 2_000),
        ('SENSOR OPERATOR', 3, 4_000),
        ('OFFICER', 2, 5_000),
    ]
    crew_infos = dragon.crew.notes.infos
    assert 'MAINTENANCE above recommended count: 1 > 0' in crew_infos
    assert 'OFFICER above recommended count: 2 > 1' in crew_infos
