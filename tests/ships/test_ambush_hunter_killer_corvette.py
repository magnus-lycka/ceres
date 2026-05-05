import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.armour import BondedSuperdenseArmour
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer30, ComputerSection
from ceres.make.ship.drives import (
    DecreasedFuel,
    DriveSection,
    FusionPlantTL12,
    JDrive2,
    MDrive6,
    PowerSection,
)
from ceres.make.ship.habitation import HabitationSection, HighStateroom, Stateroom
from ceres.make.ship.parts import EnergyEfficient, HighTechnology, SizeReduction, VeryAdvanced
from ceres.make.ship.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ImprovedSensors,
    SensorsSection,
    SensorStations,
)
from ceres.make.ship.software import (
    AdvancedFireControl,
    AntiHijack,
    BroadSpectrumEW,
    ElectronicWarfare,
    JumpControl,
    VirtualGunner,
)
from ceres.make.ship.storage import FuelProcessor, FuelSection, OperationFuel
from ceres.make.ship.systems import Airlock, Armoury, BriefingRoom, CommonArea, MedicalBay, RepairDrones, SystemsSection
from ceres.make.ship.weapons import Bay, HighYield, LongRange, MountWeapon, Turret, WeaponsSection


def build_ambush_hunter_killer_corvette() -> ship.Ship:
    """
    Modeled subset of the Ambush-class Hunter-Killer Corvette reference.

    Not yet modeled from the reference:
    - reinforced hull as its own separate cost row
    - the exact reference crew panel
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
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(
            m_drive=MDrive6(customisation=VeryAdvanced(modifications=[SizeReduction, EnergyEfficient])),
            j_drive=JDrive2(customisation=VeryAdvanced(modifications=[DecreasedFuel, DecreasedFuel])),
        ),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=500, armoured_bulkhead=True)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=16),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(
            hardware=Computer30(),
            software=[
                JumpControl(rating=2),
                AdvancedFireControl(rating=1),
                AntiHijack(rating=1),
                BroadSpectrumEW(),
                ElectronicWarfare(rating=1),
                VirtualGunner(rating=1),
            ],
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
                    customisation=HighTechnology(modifications=[HighYield, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                ),
                Bay(
                    size='medium',
                    weapon='particle_beam',
                    customisation=HighTechnology(modifications=[HighYield, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                ),
            ],
            turrets=[
                Turret(
                    size='triple',
                    weapons=[
                        MountWeapon(
                            weapon='pulse_laser', customisation=HighTechnology(modifications=[LongRange, HighYield])
                        ),
                        MountWeapon(
                            weapon='pulse_laser', customisation=HighTechnology(modifications=[LongRange, HighYield])
                        ),
                        MountWeapon(
                            weapon='pulse_laser', customisation=HighTechnology(modifications=[LongRange, HighYield])
                        ),
                    ],
                ),
                Turret(
                    size='triple',
                    weapons=[
                        MountWeapon(
                            weapon='pulse_laser', customisation=HighTechnology(modifications=[LongRange, HighYield])
                        ),
                        MountWeapon(
                            weapon='pulse_laser', customisation=HighTechnology(modifications=[LongRange, HighYield])
                        ),
                        MountWeapon(
                            weapon='pulse_laser', customisation=HighTechnology(modifications=[LongRange, HighYield])
                        ),
                    ],
                ),
            ],
        ),
        systems=SystemsSection(
            drones=[RepairDrones()],
            internal_systems=[Armoury(), BriefingRoom(), MedicalBay()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 8 + [HighStateroom()],
            common_area=CommonArea(tons=12),
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
    assert corvette.drives.j_drive is not None
    assert corvette.drives.j_drive.tons == pytest.approx(27.5)
    assert corvette.drives.j_drive.cost == pytest.approx(51_562_500.0)

    assert corvette.power is not None
    assert corvette.power.fusion_plant is not None
    assert corvette.power.fusion_plant.tons == pytest.approx(33.3333333333)
    assert corvette.power.fusion_plant.cost == pytest.approx(33_333_333.3333)

    assert corvette.fuel is not None
    assert corvette.fuel.operation_fuel is not None
    assert corvette.fuel.operation_fuel.tons == pytest.approx(14.0)
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
    software_packages = {package.description: package.cost for package in corvette.computer.software_packages.values()}
    assert software_packages == {
        'Library': 0.0,
        'Manoeuvre/0': 0.0,
        'Intellect': 0.0,
        'Jump Control/2': 200_000.0,
        'Advanced Fire Control/1': 12_000_000.0,
        'Anti-Hijack/1': 6_000_000.0,
        'Broad Spectrum EW': 14_000_000.0,
        'Electronic Warfare/1': 15_000_000.0,
        'Virtual Gunner/1': 5_000_000.0,
    }

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
    assert corvette.weapons.bays[0].tons == pytest.approx(80.0)
    assert corvette.weapons.bays[0].cost == pytest.approx(60_000_000.0)
    assert corvette.weapons.turrets[0].tons == pytest.approx(1.0)
    assert corvette.weapons.turrets[0].cost == pytest.approx(5_500_000.0)

    bulkheads = corvette.armoured_bulkhead_parts()
    assert len(bulkheads) == 3
    assert sum(part.tons for part in bulkheads) == pytest.approx(19.3333333333)
    assert sum(part.cost for part in bulkheads) == pytest.approx(3_866_666.6667)

    assert corvette.systems is not None
    assert len(corvette.systems.armouries) == 1
    assert corvette.systems.armouries[0].tons == pytest.approx(1.0)
    assert corvette.systems.armouries[0].cost == pytest.approx(250_000.0)
    assert len(corvette.systems.drones) == 1
    assert corvette.systems.drones[0].tons == pytest.approx(4.5)
    assert corvette.systems.drones[0].cost == pytest.approx(900_000.0)
    assert corvette.systems.briefing_room is not None
    assert corvette.systems.medical_bay is not None
    assert corvette.systems.medical_bay.tons == pytest.approx(4.0)
    assert corvette.systems.medical_bay.cost == pytest.approx(2_000_000.0)
    assert corvette.systems.medical_bay.power == pytest.approx(1.0)

    assert corvette.habitation is not None
    assert corvette.habitation.staterooms is not None
    standard_rooms = [room for room in corvette.habitation.staterooms if type(room) is Stateroom]
    high_rooms = [room for room in corvette.habitation.staterooms if isinstance(room, HighStateroom)]
    assert sum(room.tons for room in standard_rooms) == pytest.approx(32.0)
    assert sum(room.cost for room in standard_rooms) == pytest.approx(4_000_000.0)
    assert sum(room.tons for room in high_rooms) == pytest.approx(6.0)
    assert sum(room.cost for room in high_rooms) == pytest.approx(800_000.0)
    assert corvette.habitation.common_area is not None
    assert corvette.habitation.common_area.tons == pytest.approx(12.0)
    assert corvette.habitation.common_area.cost == pytest.approx(1_200_000.0)

    assert corvette.available_power == pytest.approx(500.0)
    assert corvette.basic_hull_power_load == pytest.approx(90.0)
    assert corvette.maneuver_power_load == pytest.approx(202.5)
    assert corvette.jump_power_load == pytest.approx(90.0)
    assert corvette.sensor_power_load == pytest.approx(6.0)
    assert corvette.weapon_power_load == pytest.approx(126.0)
    assert corvette.fuel_power_load == pytest.approx(2.0)
    assert corvette.total_power_load == pytest.approx(427.5)

    assert corvette.remaining_usable_tonnage() == pytest.approx(6.2333333333)
    assert corvette.production_cost == pytest.approx(448_812_500.0)
    assert corvette.sales_price_new == pytest.approx(448_812_500.0)
    assert corvette.expenses.maintenance == pytest.approx(37_401.0)

    spec = corvette.build_spec()
    turret_row = spec.row('Triple Turret', section='Weapons')
    assert turret_row.quantity == 2
    assert [(note.category.value, note.message) for note in turret_row.notes] == [
        ('info', 'Weapon: Pulse Laser × 3'),
        ('info', 'High Technology: Long Range, High Yield'),
    ]

    assert [(role.role, quantity) for role, quantity in corvette.crew.grouped_roles] == [
        ('CAPTAIN', 1),
        ('PILOT', 3),
        ('ASTROGATOR', 1),
        ('ENGINEER', 3),
        ('GUNNER', 8),
        ('SENSOR OPERATOR', 3),
        ('MEDIC', 1),
        ('OFFICER', 2),
    ]

    assert not any(
        note.category.value == 'error' and note.message.startswith('Hull overloaded by ') for note in corvette.notes
    )
