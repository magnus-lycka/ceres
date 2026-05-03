import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer, ComputerSection, JumpControl
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import Astrogator, Captain, Engineer, Maintenance, Medic, Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive, MDrive, PowerSection
from ceres.make.ship.habitation import HabitationSection, LowBerth, Stateroom
from ceres.make.ship.sensors import LifeScannerAnalysisSuite, MilitarySensors, SensorsSection
from ceres.make.ship.storage import FuelProcessor, FuelScoops, FuelSection, JumpFuel, OperationFuel
from ceres.make.ship.systems import BriefingRoom, CommonArea, Laboratory, MedicalBay, SystemsSection
from ceres.make.ship.weapons import Turret, WeaponsSection


def build_florence_medical_scout() -> ship.Ship:
    return ship.Ship(
        ship_class='Florence',
        ship_type='Medical Scout',
        military=False,
        tl=14,
        displacement=400,
        design_type=ship.ShipDesignType.CUSTOM,
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 2,
                Astrogator(),
                *[Engineer()] * 2,
                Maintenance(),
                *[Medic()] * 6,
            ]
        ),
        passenger_vector={},
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive(level=2), j_drive=JDrive(level=3)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=300)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=3),
            operation_fuel=OperationFuel(weeks=12),
            fuel_scoops=FuelScoops(),
            fuel_processor=FuelProcessor(tons=3),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(score=15), software=[JumpControl(rating=3)]),
        sensors=SensorsSection(primary=MilitarySensors(), life_scanner_analysis_suite=LifeScannerAnalysisSuite()),
        weapons=WeaponsSection(turrets=[Turret(size='double')]),
        craft=CraftSection(
            internal_housing=[
                InternalDockingSpace(craft=SpaceCraft.from_catalog('Slow Pinnace')),
                InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft')),
                InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft')),
            ],
        ),
        systems=SystemsSection(internal_systems=[*[MedicalBay() for _ in range(6)], Laboratory(), BriefingRoom()]),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 8,
            low_berths=[LowBerth()] * 20,
            common_area=CommonArea(tons=32),
        ),
    )


def test_florence_medical_scout_matches_current_subset():
    scout = build_florence_medical_scout()

    assert scout.hull_cost == pytest.approx(20_000_000)
    assert scout.hull_points == 160
    assert ('error', 'No airlock installed') not in [(note.category.value, note.message) for note in scout.notes]
    assert scout.drives is not None
    assert scout.drives.m_drive is not None
    assert scout.drives.m_drive.tons == pytest.approx(8.0)
    assert scout.drives.m_drive.cost == pytest.approx(16_000_000)
    assert scout.drives.j_drive is not None
    assert scout.drives.j_drive.tons == pytest.approx(35.0)
    assert scout.drives.j_drive.cost == pytest.approx(52_500_000)

    assert scout.power is not None
    assert scout.power.fusion_plant is not None
    assert scout.power.fusion_plant.tons == pytest.approx(20.0)
    assert scout.power.fusion_plant.cost == pytest.approx(20_000_000)

    assert scout.fuel is not None
    assert scout.fuel.jump_fuel is not None
    assert scout.fuel.jump_fuel.tons == pytest.approx(120.0)
    assert scout.fuel.operation_fuel is not None
    assert scout.fuel.operation_fuel.tons == pytest.approx(6.0)
    assert scout.fuel.fuel_processor is not None
    assert scout.fuel.fuel_processor.tons == pytest.approx(3.0)
    assert scout.fuel.fuel_processor.cost == pytest.approx(150_000)
    assert scout.fuel.fuel_scoops is not None
    assert scout.fuel.fuel_scoops.cost == pytest.approx(1_000_000)

    assert scout.computer is not None
    assert scout.computer.hardware is not None
    assert scout.computer.hardware.cost == pytest.approx(2_000_000)

    assert scout.sensors.primary.tons == pytest.approx(2.0)
    assert scout.sensors.primary.cost == pytest.approx(4_100_000)
    assert scout.sensors.life_scanner_analysis_suite is not None
    assert scout.sensors.life_scanner_analysis_suite.tons == pytest.approx(1.0)
    assert scout.sensors.life_scanner_analysis_suite.cost == pytest.approx(4_000_000)

    assert scout.weapons is not None
    assert scout.weapons.turrets[0].tons == pytest.approx(1.0)
    assert scout.weapons.turrets[0].cost == pytest.approx(500_000)

    assert scout.craft is not None
    assert len(scout.craft._all_parts()) == 3
    assert scout.craft._all_parts()[0].tons == pytest.approx(44.0)
    assert scout.craft._all_parts()[1].tons == pytest.approx(5.0)
    assert scout.craft._all_parts()[2].tons == pytest.approx(5.0)

    assert scout.systems is not None
    assert len(scout.systems.medical_bays) == 6
    assert sum(bay.tons for bay in scout.systems.medical_bays) == pytest.approx(24.0)
    assert sum(bay.cost for bay in scout.systems.medical_bays) == pytest.approx(12_000_000)
    assert sum(bay.power for bay in scout.systems.medical_bays) == pytest.approx(6.0)
    assert len(scout.systems.laboratories) == 1
    assert scout.systems.briefing_room is not None

    assert scout.habitation is not None
    assert scout.habitation.staterooms is not None
    assert sum(room.tons for room in scout.habitation.staterooms) == pytest.approx(32.0)
    assert scout.habitation.low_berths is not None
    assert sum(berth.tons for berth in scout.habitation.low_berths) == pytest.approx(10.0)
    assert sum(berth.power for berth in scout.habitation.low_berths) == pytest.approx(2.0)
    assert scout.habitation.common_area is not None
    assert scout.habitation.common_area.tons == pytest.approx(32.0)

    assert scout.available_power == pytest.approx(300.0)
    assert scout.basic_hull_power_load == pytest.approx(80.0)
    assert scout.maneuver_power_load == pytest.approx(80.0)
    assert scout.jump_power_load == pytest.approx(120.0)
    assert scout.sensor_power_load == pytest.approx(3.0)
    assert scout.weapon_power_load == pytest.approx(1.0)
    assert scout.fuel_power_load == pytest.approx(3.0)
    assert scout.total_power_load == pytest.approx(215.0)

    assert scout.production_cost == pytest.approx(164_880_000)
    assert scout.sales_price_new == pytest.approx(164_880_000)
    assert scout.expenses.maintenance == pytest.approx(13_740.0)
    assert ('error', 'No airlock installed') not in [(n.category.value, n.message) for n in scout.notes]
