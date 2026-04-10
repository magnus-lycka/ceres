import pytest

from ceres import armour, hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import AutoRepair1, Computer20, ComputerSection, Core40, Evade1, FireControl2
from ceres.drives import DriveSection, FusionPlantTL12, MDrive7, PowerSection
from ceres.habitation import HabitationSection, Staterooms
from ceres.hull import ImprovedStealth
from ceres.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ExtendedArrays,
    ImprovedSensors,
    SensorsSection,
)
from ceres.storage import CargoSection, FuelProcessor, FuelSection, OperationFuel
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
            armoured_bulkheads=[
                hull.ArmouredBulkhead(protected_tonnage=26.16, protected_item='Power Plant'),
                hull.ArmouredBulkhead(protected_tonnage=10.46, protected_item='Operation Fuel'),
                hull.ArmouredBulkhead(protected_tonnage=20.0, protected_item='Bridge'),
            ],
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive7(armored=True)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=436)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=16),
            fuel_processor=FuelProcessor(tons=20),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Core40(fib=True),
            backup_hardware=Computer20(fib=True),
            software=[AutoRepair1(), FireControl2(), Evade1()],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(),
            countermeasures=CountermeasuresSuite(),
            signal_processing=EnhancedSignalProcessing(),
            extended_arrays=ExtendedArrays(),
        ),
        weapons=WeaponsSection(
            barbettes=[
                Barbette(weapon='particle', armored=True, size_reduction=True),
                Barbette(weapon='particle', armored=True, size_reduction=True),
            ],
            bays=[Bay(size='small', weapon='missile', armored=True, size_reduction=True)],
            point_defense_batteries=[PointDefenseBattery(kind='laser', rating=2, armored=True, size_reduction=True)],
            missile_storage=ArmoredMissileStorage(count=720),
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


def test_alt_dragon_modeled_subset_is_currently_overloaded():
    dragon = build_alt_dragon()

    assert dragon.power is not None
    assert dragon.power.fusion_plant is not None
    assert dragon.power.fusion_plant.tons == pytest.approx(29.0666666667)
    assert dragon.power.fusion_plant.cost == pytest.approx(29_066_666.6667)

    assert dragon.fuel is not None
    assert dragon.fuel.operation_fuel is not None
    assert dragon.fuel.operation_fuel.tons == pytest.approx(11.63)
    assert dragon.fuel.fuel_processor is not None
    assert dragon.fuel.fuel_processor.build_item() == 'Fuel Processor (20 tons/day)'
    assert dragon.fuel.fuel_processor.tons == pytest.approx(20.0)

    assert dragon.computer is not None
    assert dragon.computer.hardware is not None
    assert dragon.computer.hardware.build_item() == 'Core/40/fib'
    assert dragon.computer.hardware.cost == pytest.approx(67_500_000)

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(-26.3586666667)
    assert [(note.category.value, note.message) for note in dragon.notes] == [
        ('error', 'Hull overloaded by 26.36 tons'),
    ]

    assert dragon.production_cost == pytest.approx(347_749_066.6667)
    assert dragon.sales_price_new == pytest.approx(312_974_160.0)
    assert dragon.available_power == pytest.approx(436.0)
    assert dragon.total_power_load == pytest.approx(453.0)


def test_alt_dragon_markdown_output():
    dragon = build_alt_dragon()
    table = dragon.markdown_table()
    write_markdown_output('test_alt_dragon', table)

    assert '## *Dragon* System Defense Boat, Alternate | TL13 | Hull 176' in table
    assert '| Power | Fusion (TL 12) | 29.07 | **436.00** | 29066.67 |' in table
    assert '|  | Fuel Processor (20 tons/day) | 20.00 | 20.00 | 1000.00 |' in table
    assert '| Computer | Core/40/fib |  |  | 67500.00 |' in table
    assert '| Weapons | Particle Barbette, Armored, Adv - Size Reduction × 2 | 9.90 | 30.00 | 17780.00 |' in table
    assert '|  | Point Defense Battery: Type II-L, Armored, Adv - Size Reduction | 19.80 | 20.00 | 11360.00 |' in table
    assert '|  | Magazine Armored Missile Storage (720) | 66.00 |  | 1200.00 |' in table
    assert '| Cargo | Cargo Hold | -26.36 |  |  |' in table
    assert '|  | *WARNING:* Cargo is below recommended 100-day stores capacity of 4.00 tons |  |  |  |' in table
    assert '|  | **ERROR:** Hull overloaded by 26.36 tons |  |  |  |' in table
