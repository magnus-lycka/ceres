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
    CommonArea,
    CrewArmory,
    MedicalBay,
    RepairDrones,
    SystemsSection,
    TrainingFacility,
    Workshop,
)
from ceres.weapons import Barbette, Bay, MissileStorage, PointDefenseBattery, WeaponsSection

from ._markdown_output import write_markdown_output


def build_revised_dragon() -> ship.Ship:
    """
    Modeled subset of refs/revised_dragon.txt.

    Not yet modeled from the reference:
    - budget-increased-size M-drive
    - very high yield on particle barbettes
    - energy-efficient point defense battery
    - advanced entertainment system
    - exact crew interpretation from the reference export
    """

    return ship.Ship(
        ship_class='Dragon',
        ship_type='System Defense Boat, Revised',
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
        drives=DriveSection(m_drive=MDrive7()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=482, armoured_bulkhead=True)),
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
            bays=[Bay(size='small', weapon='missile', size_reduction=3, armoured_bulkhead=True)],
            point_defense_batteries=[PointDefenseBattery(kind='laser', rating=2, armoured_bulkhead=True)],
            missile_storage=MissileStorage(count=408, armoured_bulkhead=True),
        ),
        systems=SystemsSection(
            crew_armory=CrewArmory(capacity=25),
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


def test_revised_dragon_modeled_subset_matches_current_model():
    dragon = build_revised_dragon()

    assert dragon.hull_points == 176
    assert dragon.hull_cost == pytest.approx(36_000_000)
    assert [bulkhead.tons for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(
        [3.2133333333, 1.286, 2.0, 0.3, 0.2, 0.2, 0.6, 0.2, 0.5, 0.5, 3.5, 2.0, 3.4]
    )
    assert [bulkhead.cost for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(
        [
            642_666.6667,
            257_200,
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
        ]
    )

    assert dragon.drives is not None
    assert dragon.drives.m_drive is not None
    assert dragon.drives.m_drive.tons == pytest.approx(28.0)

    assert dragon.power is not None
    assert dragon.power.fusion_plant is not None
    assert dragon.power.fusion_plant.tons == pytest.approx(32.1333333333)
    assert dragon.power.fusion_plant.cost == pytest.approx(32_133_333.3333)

    assert dragon.fuel is not None
    assert dragon.fuel.operation_fuel is not None
    assert dragon.fuel.operation_fuel.tons == pytest.approx(12.86)

    assert dragon.weapons is not None
    assert len(dragon.weapons.barbettes) == 2
    assert dragon.weapons.barbettes[0].build_item() == 'Particle Barbette'
    assert dragon.weapons.missile_storage is not None
    assert dragon.weapons.missile_storage.tons == pytest.approx(34.0)
    assert dragon.weapons.missile_storage.cost == pytest.approx(0.0)

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(28.1073333333)
    assert dragon.production_cost == pytest.approx(308_963_200.0)
    assert dragon.sales_price_new == pytest.approx(278_066_880.0)


def test_revised_dragon_power_and_crew_for_current_subset():
    dragon = build_revised_dragon()

    assert dragon.available_power == pytest.approx(482.0)
    assert dragon.basic_hull_power_load == pytest.approx(80.0)
    assert dragon.maneuver_power_load == pytest.approx(280.0)
    assert dragon.sensor_power_load == pytest.approx(13.0)
    assert dragon.weapon_power_load == pytest.approx(55.0)
    assert dragon.total_power_load == pytest.approx(429.0)

    assert [(role.role, role.count, role.monthly_salary) for role in dragon.crew_roles] == [
        ('PILOT', 3, 6_000),
        ('ENGINEER', 2, 4_000),
        ('GUNNER', 5, 2_000),
        ('SENSOR OPERATOR', 3, 4_000),
        ('OFFICER', 1, 5_000),
    ]


def test_revised_dragon_markdown_output():
    dragon = build_revised_dragon()
    table = dragon.markdown_table()
    write_markdown_output('test_revised_dragon', table)
    bulkhead_note = (
        '|  | • Power Plant, Operation Fuel, Bridge, Improved, Countermeasures Suite, '
        'Enhanced Signal Processing, Extended Arrays, Sensor Stations, Particle Barbette, Particle Barbette, '
        'Small Missile Bay, '
        'Adv - Size Reduction x3, Point Defense Battery: Type II-L, Missile Storage (408) |  |  |  |'
    )

    assert '## *Dragon* System Defense Boat, Revised | TL13 | Hull 176' in table
    assert '|  | Radiation Shielding: Reduce Rads by 1,000 |  |  | 10000.00 |' in table
    assert '|  | Armoured Bulkheads | 17.90 |  | 3579.87 |' in table
    assert bulkhead_note in table
    assert '| Power | Fusion (TL 12) | 32.13 | **482.00** | 32133.33 |' in table
    assert '| Fuel | 16 weeks of operation | 12.86 |  |  |' in table
    assert '|  | Sensor Stations × 2 | 2.00 |  | 1000.00 |' in table
    assert '| Weapons | Particle Barbette × 2 | 10.00 | 30.00 | 16000.00 |' in table
    assert '|  | Missile Storage (408) | 34.00 |  |  |' in table
    assert '| Cargo | Cargo Hold | 28.11 |  |  |' in table
    assert '|  | • 4.00 tons needed per 100 days of stores and spares |  |  |  |' in table
    assert 'Cargo is below recommended 100-day stores capacity' not in table
