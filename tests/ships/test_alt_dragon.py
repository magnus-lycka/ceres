import pytest

from ceres import armour, hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import AutoRepair1, Computer20, ComputerSection, Core40, Evade1, FireControl2
from ceres.drives import DriveSection, EmergencyPowerSystem, FusionPlantTL12, MDrive7, PowerSection
from ceres.habitation import AdvancedEntertainmentSystem, CabinSpace, HabitationSection, Staterooms
from ceres.hull import ImprovedStealth
from ceres.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ImprovedSensors,
    RapidDeploymentExtendedArrays,
    SensorsSection,
)
from ceres.storage import CargoSection, FuelProcessor, FuelSection, OperationFuel
from ceres.systems import (
    Airlock,
    BasicAutodoc,
    Biosphere,
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


def build_alt_dragon() -> ship.Ship:
    """
    Modeled subset of refs/alt_dragon.txt.

    Not yet modeled from the reference:
    - budget-increased-size M-drive
    - reduced-size fusion plant
    - emergency power system
    - retro computers
    - rapid deployment extended arrays
    - basic autodoc
    - cabin-space / mixed stateroom accommodation layout
    - advanced entertainment system
    """

    fusion_plant = FusionPlantTL12(output=436, size_reduction=True, armoured_bulkhead=True)

    return ship.Ship(
        ship_class='Dragon',
        ship_type='System Defense Boat, Alternate',
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
            armoured_bulkheads=[],
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive7(budget=True, increased_size=True, armoured_bulkhead=True)),
        power=PowerSection(
            fusion_plant=fusion_plant,
            emergency_power_system=EmergencyPowerSystem.from_fusion_plant(fusion_plant),
        ),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=16, armoured_bulkhead=True),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge(holographic=True, armoured_bulkhead=True)),
        computer=ComputerSection(
            hardware=Core40(fib=True, retro=True),
            backup_hardware=Computer20(fib=True, retro=True),
            software=[AutoRepair1(), FireControl2(), Evade1()],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(),
            countermeasures=CountermeasuresSuite(),
            signal_processing=EnhancedSignalProcessing(),
            extended_arrays=RapidDeploymentExtendedArrays(),
        ),
        weapons=WeaponsSection(
            barbettes=[
                Barbette(weapon='particle', size_reduction=True, armoured_bulkhead=True),
                Barbette(weapon='particle', size_reduction=True, armoured_bulkhead=True),
            ],
            bays=[Bay(size='small', weapon='missile', size_reduction=3, armoured_bulkhead=True)],
            point_defense_batteries=[
                PointDefenseBattery(kind='laser', rating=2, size_reduction=True, armoured_bulkhead=True)
            ],
            missile_storage=MissileStorage(count=720, armoured_bulkhead=True),
        ),
        systems=SystemsSection(
            crew_armory=CrewArmory(capacity=25),
            biosphere=Biosphere(tons=4.0),
            repair_drones=RepairDrones(),
            medical_bay=MedicalBay(autodoc=BasicAutodoc()),
            training_facility=TrainingFacility(trainees=2),
            workshop=Workshop(),
        ),
        habitation=HabitationSection(
            staterooms=Staterooms(count=4),
            cabin_space=CabinSpace(tons=15.0),
            common_area=CommonArea(tons=10.0),
            entertainment=AdvancedEntertainmentSystem(quality='adequate'),
        ),
    )


def test_alt_dragon_modeled_subset_tracks_current_model():
    dragon = build_alt_dragon()

    assert dragon.power is not None
    assert dragon.power.fusion_plant is not None
    assert dragon.power.fusion_plant.tons == pytest.approx(26.16)
    assert dragon.power.fusion_plant.cost == pytest.approx(31_973_333.3333)
    assert dragon.power.emergency_power_system is not None
    assert dragon.power.emergency_power_system.tons == pytest.approx(2.616)
    assert dragon.power.emergency_power_system.cost == pytest.approx(3_197_333.3333)

    assert dragon.fuel is not None
    assert dragon.fuel.operation_fuel is not None
    assert dragon.fuel.operation_fuel.tons == pytest.approx(10.47)
    assert dragon.fuel.fuel_processor is not None
    assert dragon.fuel.fuel_processor.build_item() == 'Fuel Processor (20 tons/day)'
    assert dragon.fuel.fuel_processor.tons == pytest.approx(1.0)

    assert dragon.computer is not None
    assert dragon.computer.hardware is not None
    assert dragon.computer.hardware.build_item() == 'Core/40/fib, (Retro*)'
    assert dragon.computer.hardware.cost == pytest.approx(4_218_750.0)

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(6.3916)
    assert dragon.notes == []

    assert dragon.production_cost == pytest.approx(293_063_146.6667)
    assert dragon.sales_price_new == pytest.approx(263_756_832.0)
    assert dragon.available_power == pytest.approx(436.0)
    assert dragon.sensor_power_load == pytest.approx(15.0)
    assert dragon.total_power_load == pytest.approx(436.0)


def test_alt_dragon_markdown_output():
    dragon = build_alt_dragon()
    table = dragon.markdown_table()
    write_markdown_output('test_alt_dragon', table)

    assert '## *Dragon* System Defense Boat, Alternate | TL13 | Hull 176' in table
    assert '|  | Radiation Shielding: Reduce Rads by 1,000 |  |  | 10000.00 |' in table
    assert '| Power | Fusion (TL 12), Adv - Size Reduction | 26.16 | **436.00** | 31973.33 |' in table
    assert '|  | Emergency Power System | 2.62 |  | 3197.33 |' in table
    assert '|  | Fuel Processor (20 tons/day) | 1.00 | 1.00 | 50.00 |' in table
    assert '| Computer | Core/40/fib, (Retro*) |  |  | 4218.75 |' in table
    assert '|  | Armoured Bulkheads | 21.36 |  | 4272.48 |' in table
    assert (
        '|  | • M-Drive, Power Plant, Operation Fuel, Bridge, Particle Barbette, Adv - Size Reduction × 2, '
        'Small Missile Bay, Adv - Size Reduction × 3, '
        'Point Defense Battery: Type II-L, '
        'Adv - Size Reduction, Missile Storage (720) |  |  |  |'
    ) in table
    assert '| Weapons | Particle Barbette, Adv - Size Reduction × 2 | 9.00 | 30.00 | 17600.00 |' in table
    assert '|  | Small Missile Bay, Adv - Size Reduction × 3 | 35.00 | 5.00 | 18000.00 |' in table
    assert '|  | Point Defense Battery: Type II-L, Adv - Size Reduction | 18.00 | 20.00 | 11000.00 |' in table
    assert '|  | Missile Storage (720) | 60.00 |  |  |' in table
    assert '| Habitation | Staterooms × 4 | 16.00 |  | 2000.00 |' in table
    assert '|  | Cabin Space | 15.00 |  | 750.00 |' in table
    assert '| Cargo | Cargo Hold | 6.39 |  |  |' in table
    assert '|  | **ERROR:**' not in table
