import pytest

from tycho import armour, hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import AutoRepair, Computer, ComputerSection, Evade, FireControl
from tycho.drives import DriveSection, FusionPlantTL12, MDrive, PowerSection
from tycho.habitation import AdvancedEntertainmentSystem, HabitationSection, Staterooms
from tycho.hull import ImprovedStealth
from tycho.parts import Advanced, Budget, EnergyEfficient, HighTechnology, IncreasedSize, SizeReduction, VeryAdvanced
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
from tycho.weapons import Barbette, Bay, MissileStorage, PointDefenseBattery, VeryHighYield, WeaponsSection


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
                update={'reinforced': True},
            ),
            stealth=ImprovedStealth(),
            radiation_shielding=True,
            armour=armour.CrystalironArmour(protection=13),
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive(7, customisation=Budget(IncreasedSize), armoured_bulkhead=True)),
        power=PowerSection(
            fusion_plant=FusionPlantTL12(
                output=482,
                customisation=Budget(IncreasedSize),
                armoured_bulkhead=True,
            )
        ),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16, armoured_bulkhead=True)),
        command=CommandSection(bridge=Bridge(holographic=True, armoured_bulkhead=True)),
        computer=ComputerSection(
            hardware=Computer(25, fib=True),
            backup_hardware=Computer(20, fib=True),
            software=[AutoRepair(1), FireControl(2), Evade(1)],
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
                Barbette(weapon='particle', customisation=VeryAdvanced(VeryHighYield), armoured_bulkhead=True),
                Barbette(weapon='particle', customisation=VeryAdvanced(VeryHighYield), armoured_bulkhead=True),
            ],
            bays=[
                Bay(
                    size='small',
                    weapon='missile',
                    customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction),
                    armoured_bulkhead=True,
                )
            ],
            point_defense_batteries=[
                PointDefenseBattery(kind='laser', rating=2, customisation=Advanced(EnergyEfficient), armoured_bulkhead=True)
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
    assert dragon.weapons.barbettes[0].build_item() == 'Particle Barbette'
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
