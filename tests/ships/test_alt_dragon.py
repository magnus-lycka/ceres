import pytest
from stuart import render_ship_html

from tycho import armour, hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import AutoRepair, Computer, ComputerSection, Core, Evade, FireControl
from tycho.drives import DriveSection, EmergencyPowerSystem, FusionPlantTL12, MDrive7, PowerSection
from tycho.habitation import AdvancedEntertainmentSystem, CabinSpace, HabitationSection, Staterooms
from tycho.hull import ImprovedStealth
from tycho.parts import Advanced, Budget, HighTechnology, IncreasedSize, SizeReduction
from tycho.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ImprovedSensors,
    RapidDeploymentExtendedArrays,
    SensorsSection,
)
from tycho.storage import CargoSection, FuelProcessor, FuelSection, OperationFuel
from tycho.systems import (
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
from tycho.weapons import Barbette, Bay, MissileStorage, PointDefenseBattery, WeaponsSection

from ._output import write_html_output


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

    fusion_plant = FusionPlantTL12(output=436, customisation=Advanced(SizeReduction), armoured_bulkhead=True)

    return ship.Ship(
        ship_class='Dragon',
        ship_type='System Defense Boat, Alternate',
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
            armoured_bulkheads=[],
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive7(customisation=Budget(IncreasedSize), armoured_bulkhead=True)),
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
            hardware=Core(40, fib=True),
            backup_hardware=Computer(20, fib=True),
            software=[AutoRepair(1), FireControl(2), Evade(1)],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(),
            countermeasures=CountermeasuresSuite(),
            signal_processing=EnhancedSignalProcessing(),
            extended_arrays=RapidDeploymentExtendedArrays(),
        ),
        weapons=WeaponsSection(
            barbettes=[
                Barbette(weapon='particle', customisation=Advanced(SizeReduction), armoured_bulkhead=True),
                Barbette(weapon='particle', customisation=Advanced(SizeReduction), armoured_bulkhead=True),
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
                PointDefenseBattery(kind='laser', rating=2, customisation=Advanced(SizeReduction), armoured_bulkhead=True)
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
    assert dragon.computer.hardware.build_item() == 'Core/40/fib'
    assert dragon.computer.hardware.cost == pytest.approx(67_500_000.0)

    assert CargoSection.cargo_tons_for_ship(dragon) == pytest.approx(6.3916)
    assert dragon.notes == []

    assert dragon.production_cost == pytest.approx(360_094_396.6667)
    assert dragon.sales_price_new == pytest.approx(324_084_957.0)
    assert dragon.available_power == pytest.approx(436.0)
    assert dragon.sensor_power_load == pytest.approx(15.0)
    assert dragon.total_power_load == pytest.approx(436.0)


def test_alt_dragon_has_no_errors():
    dragon = build_alt_dragon()
    all_notes = [(n.category.value, n.message) for n in dragon.notes]
    assert not any(cat == 'error' for cat, _ in all_notes)


def test_alt_dragon_stuart_html_output():
    dragon = build_alt_dragon()
    html = render_ship_html(dragon)
    write_html_output('test_alt_dragon', html)

    assert '<title>Dragon</title>' in html
    assert '<p class="banner-meta">System Defense Boat, Alternate | TL13 | Hull 176</p>' in html
    assert '<header class="sidebar-card-title">Crew</header>' in html
    assert '<header class="sidebar-card-title">Power</header>' in html
    assert '<header class="sidebar-card-title">Costs</header>' in html
    assert 'Radiation Shielding: Reduce Rads by 1,000' in html
    assert 'Small Missile Bay' in html
    assert 'High Technology: Size Reduction × 3' in html
    assert 'Life Support Facilities' in html
    assert 'Armoured Bulkheads<ul class="item-notes">' in html
    assert 'Critical hit severity reduced by 1 if critical hit severity &gt;1' in html
    assert 'Improved Sensors' in html
    assert '<p class="eyebrow">' not in html
