import pytest

from tycho import armour, hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import AutoRepair1, Computer20, Computer25, ComputerSection, Evade1, FireControl2
from tycho.drives import DriveSection, FusionPlantTL12, MDrive7, PowerSection
from tycho.habitation import AdvancedEntertainmentSystem, HabitationSection, Staterooms
from tycho.hull import ImprovedStealth
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
    CommonArea,
    CrewArmory,
    MedicalBay,
    RepairDrones,
    SystemsSection,
    TrainingFacility,
    Workshop,
)
from tycho.weapons import Barbette, Bay, MissileStorage, PointDefenseBattery, WeaponsSection

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
        drives=DriveSection(m_drive=MDrive7(budget=True, increased_size=True, armoured_bulkhead=True)),
        power=PowerSection(
            fusion_plant=FusionPlantTL12(
                output=482,
                budget=True,
                increased_size=True,
                armoured_bulkhead=True,
            )
        ),
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
                Barbette(weapon='particle', very_high_yield=True, armoured_bulkhead=True),
                Barbette(weapon='particle', very_high_yield=True, armoured_bulkhead=True),
            ],
            bays=[Bay(size='small', weapon='missile', size_reduction=3, armoured_bulkhead=True)],
            point_defense_batteries=[
                PointDefenseBattery(kind='laser', rating=2, energy_efficient=True, armoured_bulkhead=True)
            ],
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
            entertainment=AdvancedEntertainmentSystem(quality='cheap'),
        ),
    )


def test_revised_dragon_modeled_subset_matches_current_model():
    dragon = build_revised_dragon()

    assert dragon.hull_points == 176
    assert dragon.hull_cost == pytest.approx(36_000_000)
    assert [bulkhead.tons for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(
        [3.5, 4.0166666667, 1.6066666667, 2.0, 0.3, 0.2, 0.2, 0.6, 0.2, 0.5, 0.5, 3.5, 2.0, 3.4]
    )
    assert [bulkhead.cost for bulkhead in dragon.armoured_bulkhead_parts()] == pytest.approx(
        [
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
        ]
    )

    assert dragon.drives is not None
    assert dragon.drives.m_drive is not None
    assert dragon.drives.m_drive.tons == pytest.approx(35.0)
    assert dragon.drives.m_drive.cost == pytest.approx(42_000_000.0)

    assert dragon.power is not None
    assert dragon.power.fusion_plant is not None
    assert dragon.power.fusion_plant.tons == pytest.approx(40.1666666667)
    assert dragon.power.fusion_plant.cost == pytest.approx(24_100_000.0)

    assert dragon.fuel is not None
    assert dragon.fuel.operation_fuel is not None
    assert dragon.fuel.operation_fuel.tons == pytest.approx(16.07)

    assert dragon.weapons is not None
    assert len(dragon.weapons.barbettes) == 2
    assert dragon.weapons.barbettes[0].build_item() == 'Particle Barbette, VAdv - Very High Yield'
    assert dragon.weapons.missile_storage is not None
    assert dragon.weapons.missile_storage.tons == pytest.approx(34.0)
    assert dragon.weapons.missile_storage.cost == pytest.approx(0.0)

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(5.24)
    assert dragon.production_cost == pytest.approx(292_855_166.6667)
    assert dragon.sales_price_new == pytest.approx(263_569_650.0)


def test_revised_dragon_power_and_crew_for_current_subset():
    dragon = build_revised_dragon()

    assert dragon.available_power == pytest.approx(482.0)
    assert dragon.basic_hull_power_load == pytest.approx(80.0)
    assert dragon.maneuver_power_load == pytest.approx(280.0)
    assert dragon.sensor_power_load == pytest.approx(15.0)
    assert dragon.weapon_power_load == pytest.approx(50.0)
    assert dragon.total_power_load == pytest.approx(426.0)

    assert [(role.role, role.count, role.monthly_salary) for role in dragon.crew_roles] == [
        ('CAPTAIN', 1, 10_000),
        ('PILOT', 3, 6_000),
        ('ENGINEER', 3, 4_000),
        ('MAINTENANCE', 1, 1_000),
        ('GUNNER', 5, 2_000),
        ('SENSOR OPERATOR', 3, 4_000),
        ('MEDIC', 1, 4_000),
        ('OFFICER', 1, 5_000),
    ]


def test_revised_dragon_markdown_output():
    dragon = build_revised_dragon()
    table = dragon.markdown_table()
    write_markdown_output('test_revised_dragon', table)
    bulkhead_note = (
        '|  | • M-Drive, Power Plant, Operation Fuel, Bridge, Improved Sensors, Countermeasures Suite, '
        'Enhanced Signal Processing, Extended Arrays, Sensor Stations × 2, '
        'Particle Barbette, VAdv - Very High Yield × 2, Small Missile Bay, Adv - Size Reduction × 3, '
        'Point Defense Battery: Type II-L, Adv - Energy Efficient, Missile Storage (408) |  |  |  |'
    )

    assert '## *Dragon* System Defense Boat, Revised | TL13 | Hull 176' in table
    assert '|  | Radiation Shielding: Reduce Rads by 1,000 |  |  | 10000.00 |' in table
    assert '|  | Armoured Bulkheads | 22.52 |  | 4504.67 |' in table
    assert bulkhead_note in table
    assert '| Propulsion | M-Drive 7, Budget-Increased Size | 35.00 | 280.00 | 42000.00 |' in table
    assert '| Power | Fusion (TL 12), Budget-Increased Size | 40.17 | **482.00** | 24100.00 |' in table
    assert '| Fuel | 16 weeks of operation | 16.07 |  |  |' in table
    assert '|  | Sensor Stations × 2 | 2.00 |  | 1000.00 |' in table
    assert '|  | Extended Arrays | 6.00 | 9.00 | 8600.00 |' in table
    assert '| Weapons | Particle Barbette, VAdv - Very High Yield × 2 | 10.00 | 30.00 | 20000.00 |' in table
    assert '|  | Point Defense Battery: Type II-L, Adv - Energy Efficient | 20.00 | 15.00 | 11000.00 |' in table
    assert '|  | Missile Storage (408) | 34.00 |  |  |' in table
    assert '| Cargo | Cargo Hold | 5.24 |  |  |' in table
    assert '|  | • 4.00 tons needed per 100 days of stores and spares |  |  |  |' in table
    assert 'Cargo is below recommended 100-day stores capacity' not in table
