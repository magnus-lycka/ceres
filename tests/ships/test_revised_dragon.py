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
from ceres.weapons import ArmoredMissileStorage, Barbette, Bay, PointDefenseBattery, WeaponsSection

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
            armoured_bulkheads=[
                hull.ArmouredBulkhead(protected_tonnage=40.17, protected_item='Power Plant'),
                hull.ArmouredBulkhead(protected_tonnage=16.07, protected_item='Operation Fuel'),
                hull.ArmouredBulkhead(protected_tonnage=20.0, protected_item='Bridge'),
                hull.ArmouredBulkhead(protected_tonnage=13.0, protected_item='Sensors'),
            ],
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive7(armored=True)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=482)),
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
            missile_storage=ArmoredMissileStorage(count=408),
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
    assert [bulkhead.tons for bulkhead in dragon.hull.armoured_bulkheads] == pytest.approx([4.017, 1.607, 2.0, 1.3])
    assert [bulkhead.cost for bulkhead in dragon.hull.armoured_bulkheads] == pytest.approx(
        [803_400, 321_400, 400_000, 260_000]
    )

    assert dragon.drives is not None
    assert dragon.drives.m_drive is not None
    assert dragon.drives.m_drive.tons == pytest.approx(30.8)

    assert dragon.power is not None
    assert dragon.power.fusion_plant is not None
    assert dragon.power.fusion_plant.tons == pytest.approx(32.1333333333)
    assert dragon.power.fusion_plant.cost == pytest.approx(32_133_333.3333)

    assert dragon.fuel is not None
    assert dragon.fuel.operation_fuel is not None
    assert dragon.fuel.operation_fuel.tons == pytest.approx(12.86)

    assert dragon.weapons is not None
    assert len(dragon.weapons.barbettes) == 2
    assert dragon.weapons.barbettes[0].build_item() == 'Particle Barbette, Armored'
    assert dragon.weapons.missile_storage is not None
    assert dragon.weapons.missile_storage.tons == pytest.approx(37.4)
    assert dragon.weapons.missile_storage.cost == pytest.approx(680_000)

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(13.1826666667)
    assert dragon.production_cost == pytest.approx(295_148_133.3333)
    assert dragon.sales_price_new == pytest.approx(265_633_320.0)


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

    assert '## *Dragon* System Defense Boat, Revised | TL13 | Hull 176' in table
    assert '|  | Armoured Bulkhead for Power Plant | 4.02 |  | 803.40 |' in table
    assert '| Power | Fusion (TL 12) | 32.13 | **482.00** | 32133.33 |' in table
    assert '| Fuel | 16 weeks of operation | 12.86 |  |  |' in table
    assert '|  | Additional Armored Sensor Stations × 2 | 2.20 |  | 1040.00 |' in table
    assert '| Weapons | Particle Barbette, Armored × 2 | 11.00 | 30.00 | 16200.00 |' in table
    assert '|  | Magazine Armored Missile Storage (408) | 37.40 |  | 680.00 |' in table
    assert '| Cargo | Cargo Hold | 13.18 |  |  |' in table
    assert '|  | • 4.00 tons needed per 100 days of stores and spares |  |  |  |' in table
    assert 'Cargo is below recommended 100-day stores capacity' not in table
