import pytest

from tycho import hull, ship
from tycho.armour import BondedSuperdenseArmour
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection, FireControl, JumpControl
from tycho.drives import DecreasedFuel, DriveSection, FusionPlantTL12, JumpDrive2, MDrive6, PowerSection
from tycho.habitation import HabitationSection, Staterooms
from tycho.parts import EnergyEfficient, HighTechnology, SizeReduction, VeryAdvanced
from tycho.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ImprovedSensors,
    SensorsSection,
    SensorStations,
)
from tycho.storage import FuelProcessor, FuelSection, JumpFuel, OperationFuel
from tycho.systems import Airlock, BriefingRoom, CommonArea, CrewArmory, MedicalBay, RepairDrones, SystemsSection
from tycho.weapons import Bay, LongRange, MountWeapon, Turret, WeaponsSection


def build_ambush_hunter_killer_corvette() -> ship.Ship:
    """
    Modeled subset of the Ambush-class Hunter-Killer Corvette reference.

    Not yet modeled from the reference:
    - reinforced hull as its own separate cost row
    - the specific medium-bay/high-yield export combination
    - the full advanced EW / anti-hijack / advanced fire-control software stack
    - high staterooms
    - the exact reference crew panel
    - the exact low cargo remainder from the sheet
    """

    return ship.Ship(
        ship_class='Ambush-Class',
        ship_type='Hunter-Killer Corvette',
        military=True,
        tl=15,
        displacement=450,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(
            configuration=hull.close_structure.model_copy(
                update={'reinforced': True, 'description': 'Close Structure Hull, Reinforced'},
            ),
            armour=BondedSuperdenseArmour(protection=12),
            airlocks=[Airlock(), Airlock()],
        ),
        drives=DriveSection(
            m_drive=MDrive6(customisation=VeryAdvanced(SizeReduction, EnergyEfficient)),
            jump_drive=JumpDrive2(customisation=VeryAdvanced(DecreasedFuel, DecreasedFuel)),
        ),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=500, armoured_bulkhead=True)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=16),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(
            hardware=Computer(30),
            software=[JumpControl(2), FireControl(1)],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(),
            countermeasures=CountermeasuresSuite(),
            signal_processing=EnhancedSignalProcessing(),
            sensor_stations=SensorStations(count=2),
        ),
        weapons=WeaponsSection(
            bays=[
                Bay(
                    size='medium',
                    weapon='particle_beam',
                    customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction),
                    armoured_bulkhead=True,
                ),
                Bay(
                    size='medium',
                    weapon='particle_beam',
                    customisation=HighTechnology(SizeReduction, SizeReduction, SizeReduction),
                    armoured_bulkhead=True,
                ),
            ],
            turrets=[
                Turret(
                    size='triple',
                    weapons=[
                        MountWeapon(weapon='pulse_laser', customisation=VeryAdvanced(LongRange)),
                        MountWeapon(weapon='pulse_laser'),
                        MountWeapon(weapon='pulse_laser'),
                    ],
                ),
                Turret(
                    size='triple',
                    weapons=[
                        MountWeapon(weapon='pulse_laser', customisation=VeryAdvanced(LongRange)),
                        MountWeapon(weapon='pulse_laser'),
                        MountWeapon(weapon='pulse_laser'),
                    ],
                ),
            ],
        ),
        systems=SystemsSection(
            crew_armory=CrewArmory(capacity=25),
            repair_drones=RepairDrones(),
            briefing_room=BriefingRoom(),
            medical_bay=MedicalBay(),
        ),
        habitation=HabitationSection(
            staterooms=Staterooms(count=8),
            common_area=CommonArea(tons=17),
        ),
    )


def test_ambush_hunter_killer_corvette_matches_current_modeled_subset():
    corvette = build_ambush_hunter_killer_corvette()

    assert corvette.hull_cost == pytest.approx(27_000_000)
    assert corvette.hull_points == 198

    assert corvette.drives is not None
    assert corvette.drives.m_drive is not None
    assert corvette.drives.m_drive.tons == pytest.approx(24.3)
    assert corvette.drives.m_drive.cost == pytest.approx(67_500_000)
    assert corvette.drives.jump_drive is not None
    assert corvette.drives.jump_drive.tons == pytest.approx(27.5)
    assert corvette.drives.jump_drive.cost == pytest.approx(51_562_500.0)

    assert corvette.power is not None
    assert corvette.power.fusion_plant is not None
    assert corvette.power.fusion_plant.tons == pytest.approx(33.3333333333)
    assert corvette.power.fusion_plant.cost == pytest.approx(33_333_333.3333)

    assert corvette.fuel is not None
    assert corvette.fuel.jump_fuel is not None
    assert corvette.fuel.jump_fuel.tons == pytest.approx(81.0)
    assert corvette.fuel.operation_fuel is not None
    assert corvette.fuel.operation_fuel.tons == pytest.approx(13.34)
    assert corvette.fuel.fuel_processor is not None
    assert corvette.fuel.fuel_processor.tons == pytest.approx(2.0)
    assert corvette.fuel.fuel_processor.cost == pytest.approx(100_000.0)

    assert corvette.command is not None
    assert corvette.command.bridge is not None
    assert corvette.command.bridge.tons == pytest.approx(20.0)
    assert corvette.command.bridge.cost == pytest.approx(2_500_000.0)

    assert corvette.computer is not None
    assert corvette.computer.hardware is not None
    assert corvette.computer.hardware.cost == pytest.approx(20_000_000.0)

    assert corvette.hull.armour is not None
    assert corvette.hull.armour.tons == pytest.approx(64.8)
    assert corvette.hull.armour.cost == pytest.approx(32_400_000.0)

    assert corvette.sensors.primary.tons == pytest.approx(3.0)
    assert corvette.sensors.primary.cost == pytest.approx(4_300_000.0)
    assert corvette.sensors.countermeasures is not None
    assert corvette.sensors.countermeasures.tons == pytest.approx(2.0)
    assert corvette.sensors.countermeasures.cost == pytest.approx(4_000_000.0)
    assert corvette.sensors.signal_processing is not None
    assert corvette.sensors.signal_processing.tons == pytest.approx(2.0)
    assert corvette.sensors.signal_processing.cost == pytest.approx(8_000_000.0)
    assert corvette.sensors.sensor_stations is not None
    assert corvette.sensors.sensor_stations.tons == pytest.approx(2.0)
    assert corvette.sensors.sensor_stations.cost == pytest.approx(1_000_000.0)

    assert corvette.weapons is not None
    assert len(corvette.weapons.bays) == 2
    assert corvette.weapons.bays[0].tons == pytest.approx(70.0)
    assert corvette.weapons.bays[0].cost == pytest.approx(60_000_000.0)
    assert corvette.weapons.turrets[0].tons == pytest.approx(1.0)
    assert corvette.weapons.turrets[0].cost == pytest.approx(4_250_000.0)

    bulkheads = corvette.armoured_bulkhead_parts()
    assert len(bulkheads) == 3
    assert sum(part.tons for part in bulkheads) == pytest.approx(17.3333333333)
    assert sum(part.cost for part in bulkheads) == pytest.approx(3_466_666.6667)

    assert corvette.systems is not None
    assert corvette.systems.crew_armory is not None
    assert corvette.systems.crew_armory.tons == pytest.approx(1.0)
    assert corvette.systems.crew_armory.cost == pytest.approx(250_000.0)
    assert corvette.systems.repair_drones is not None
    assert corvette.systems.repair_drones.tons == pytest.approx(4.5)
    assert corvette.systems.repair_drones.cost == pytest.approx(900_000.0)
    assert corvette.systems.briefing_room is not None
    assert corvette.systems.medical_bay is not None
    assert corvette.systems.medical_bay.tons == pytest.approx(4.0)
    assert corvette.systems.medical_bay.cost == pytest.approx(2_000_000.0)
    assert corvette.systems.medical_bay.power == pytest.approx(1.0)

    assert corvette.habitation is not None
    assert corvette.habitation.staterooms is not None
    assert corvette.habitation.staterooms.tons == pytest.approx(32.0)
    assert corvette.habitation.staterooms.cost == pytest.approx(4_000_000.0)
    assert corvette.habitation.common_area is not None
    assert corvette.habitation.common_area.tons == pytest.approx(17.0)
    assert corvette.habitation.common_area.cost == pytest.approx(1_700_000.0)

    assert corvette.available_power == pytest.approx(500.0)
    assert corvette.basic_hull_power_load == pytest.approx(90.0)
    assert corvette.maneuver_power_load == pytest.approx(202.5)
    assert corvette.jump_power_load == pytest.approx(90.0)
    assert corvette.sensor_power_load == pytest.approx(6.0)
    assert corvette.weapon_power_load == pytest.approx(126.0)
    assert corvette.fuel_power_load == pytest.approx(2.0)
    assert corvette.total_power_load == pytest.approx(427.5)

    assert corvette.remaining_usable_tonnage() == pytest.approx(-47.1066666667)
    assert corvette.production_cost == pytest.approx(395_212_500.0)
    assert corvette.sales_price_new == pytest.approx(395_212_500.0)
    assert corvette.expenses.maintenance == pytest.approx(32_934.0)

    assert [(role.role, role.count) for role in corvette.crew_roles] == [
        ('CAPTAIN', 1),
        ('PILOT', 3),
        ('ASTROGATOR', 1),
        ('ENGINEER', 3),
        ('MAINTENANCE', 1),
        ('GUNNER', 8),
        ('SENSOR OPERATOR', 3),
        ('MEDIC', 1),
        ('OFFICER', 2),
    ]

    assert ('error', 'Hull overloaded by 47.11 tons') in [
        (note.category.value, note.message) for note in corvette.notes
    ]
