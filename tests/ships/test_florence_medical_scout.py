"""Reference ship case: Florence-class Medical Scout.

Source: Mongoose Traveller 2e (screenshot of official stat block).

Purpose:
- exercise a 400-ton standard hull with J-3/M-2/FusionTL12 configuration
- verify Military sensors + Life Scanner Analysis Suite
- verify Medical Bays x6, Laboratory, Briefing Room
- verify slow pinnace + air/raft x2 docking spaces
- verify power accounting for medical and low-berth loads

Known deviations from stat block:
- none identified; all asserted values agree with the published stat block
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer15, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import Astrogator, Captain, Engineer, Maintenance, Medic, Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive3, MDrive2, PowerSection
from ceres.make.ship.habitation import HabitationSection, LowBerth, Stateroom
from ceres.make.ship.sensors import LifeScannerAnalysisSuite, MilitarySensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import FuelProcessor, FuelScoops, FuelSection, JumpFuel, OperationFuel
from ceres.make.ship.systems import BriefingRoom, CommonArea, Laboratory, MedicalBay, SystemsSection
from ceres.make.ship.weapons import DoubleTurret, WeaponsSection

_expected = SimpleNamespace(
    tl=14,
    displacement=400,
    hull_cost_mcr=20,  # 400 tons, Standard
    hull_points=160,
    m_drive_tons=8,  # Thrust 2
    m_drive_cost_mcr=16,
    j_drive_tons=35,  # Jump 3
    j_drive_cost_mcr=52.5,
    plant_tons=20,  # Fusion (TL12), Power 300
    plant_cost_mcr=20,
    jump_fuel_tons=120,  # J-3: 400 × 0.3
    op_fuel_tons=6,  # 12 weeks; stat block shows 127 total (120 jump + ~7 op+pinnace)
    fuel_processor_tons=3,  # 60 tons/day
    fuel_processor_cost_mcr=0.15,
    fuel_scoops_cost_mcr=1,
    computer_cost_mcr=2,  # Computer/15
    primary_sensor_tons=2,  # Military Grade
    primary_sensor_cost_mcr=4.1,
    life_scanner_tons=1,
    life_scanner_cost_mcr=4,
    turret_tons=1,  # Double Turret (empty)
    turret_cost_mcr=0.5,
    craft_count=3,
    pinnace_docking_tons=44,  # Docking Space (40 tons): 40 × 1.1
    airraft_docking_tons=5,  # Docking Space (4 tons): 4 × 1.25
    medical_bay_count=6,
    laboratory_count=1,
    medical_bay_tons_total=24,  # 6 × 4
    medical_bay_cost_total_mcr=12,  # 6 × MCr2
    medical_bay_power_total=6,  # 6 × 1
    stateroom_tons_total=32,  # Standard x8: 8 × 4
    low_berth_tons_total=10,  # x20: 20 × 0.5
    low_berth_power_total=2,  # 20 × 0.1
    common_area_tons=32,
    available_power=300,
    power_basic=80,  # ceil(400 × 0.2) per RIS-013
    power_maneuver=80,  # Thrust 2 × 400 × 0.1
    power_jump=120,  # Jump 3 × 400 × 0.1
    power_sensors=3,  # Military Grade
    power_fuel_processor=3,
    power_medical=6,
    power_weapons=1,
    power_low_berths=2,
    total_power=215,  # basic + max(maneuver, jump) + sensors + fuel_proc + medical + weapons + low_berths
    production_cost_mcr=164.88,
    maintenance_cr=13_740,
    expected_errors=[],
    expected_warnings=[],
    expected_crew_infos=[
        'CAPTAIN above recommended count: 1 > 0',
        'MAINTENANCE above recommended count: 1 > 0',
        'MEDIC above recommended count: 6 > 1',
    ],
    expected_crew_warnings=['GUNNER below recommended count: 0 < 1'],
)


def build_florence_medical_scout() -> ship.Ship:
    return ship.Ship(
        ship_class='Florence',
        ship_type='Medical Scout',
        military=False,
        tl=_expected.tl,
        displacement=_expected.displacement,
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
        occupants=[],
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive3()),
        power=PowerSection(plant=FusionPlantTL12(output=300)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=3),
            operation_fuel=OperationFuel(weeks=12),
            fuel_scoops=FuelScoops(),
            fuel_processor=FuelProcessor(tons=3),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer15(), software=[JumpControl(rating=3)]),
        sensors=SensorsSection(primary=MilitarySensors(), life_scanner_analysis_suite=LifeScannerAnalysisSuite()),
        weapons=WeaponsSection(turrets=[DoubleTurret()]),
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

    assert scout.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert scout.hull_points == _expected.hull_points
    assert 'No airlock installed' not in scout.notes.errors
    assert scout.drives is not None
    assert scout.drives.m_drive is not None
    assert scout.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert scout.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert scout.drives.j_drive is not None
    assert scout.drives.j_drive.tons == pytest.approx(_expected.j_drive_tons)
    assert scout.drives.j_drive.cost == pytest.approx(_expected.j_drive_cost_mcr * 1_000_000)

    assert scout.power is not None
    assert scout.power.plant is not None
    assert scout.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert scout.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)

    assert scout.fuel is not None
    assert scout.fuel.jump_fuel is not None
    assert scout.fuel.jump_fuel.tons == pytest.approx(_expected.jump_fuel_tons)
    assert scout.fuel.operation_fuel is not None
    assert scout.fuel.operation_fuel.tons == pytest.approx(_expected.op_fuel_tons)
    assert scout.fuel.fuel_processor is not None
    assert scout.fuel.fuel_processor.tons == pytest.approx(_expected.fuel_processor_tons)
    assert scout.fuel.fuel_processor.cost == pytest.approx(_expected.fuel_processor_cost_mcr * 1_000_000)
    assert scout.fuel.fuel_scoops is not None
    assert scout.fuel.fuel_scoops.cost == pytest.approx(_expected.fuel_scoops_cost_mcr * 1_000_000)

    assert scout.computer is not None
    assert scout.computer.hardware is not None
    assert scout.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)

    assert scout.sensors.primary.tons == pytest.approx(_expected.primary_sensor_tons)
    assert scout.sensors.primary.cost == pytest.approx(_expected.primary_sensor_cost_mcr * 1_000_000)
    assert scout.sensors.life_scanner_analysis_suite is not None
    assert scout.sensors.life_scanner_analysis_suite.tons == pytest.approx(_expected.life_scanner_tons)
    assert scout.sensors.life_scanner_analysis_suite.cost == pytest.approx(_expected.life_scanner_cost_mcr * 1_000_000)

    assert scout.weapons is not None
    assert scout.weapons.turrets[0].tons == pytest.approx(_expected.turret_tons)
    assert scout.weapons.turrets[0].cost == pytest.approx(_expected.turret_cost_mcr * 1_000_000)

    assert scout.craft is not None
    assert len(scout.craft._all_parts()) == _expected.craft_count
    assert scout.craft._all_parts()[0].tons == pytest.approx(_expected.pinnace_docking_tons)
    assert scout.craft._all_parts()[1].tons == pytest.approx(_expected.airraft_docking_tons)
    assert scout.craft._all_parts()[2].tons == pytest.approx(_expected.airraft_docking_tons)

    assert scout.systems is not None
    assert len(scout.systems.medical_bays) == _expected.medical_bay_count
    assert sum(bay.tons for bay in scout.systems.medical_bays) == pytest.approx(_expected.medical_bay_tons_total)
    assert sum(bay.cost for bay in scout.systems.medical_bays) == pytest.approx(
        _expected.medical_bay_cost_total_mcr * 1_000_000
    )
    assert sum(bay.power for bay in scout.systems.medical_bays) == pytest.approx(_expected.medical_bay_power_total)
    assert len(scout.systems.laboratories) == _expected.laboratory_count
    assert scout.systems.briefing_rooms[0] is not None

    assert scout.habitation is not None
    assert scout.habitation.staterooms is not None
    assert sum(room.tons for room in scout.habitation.staterooms) == pytest.approx(_expected.stateroom_tons_total)
    assert scout.habitation.low_berths is not None
    assert sum(berth.tons for berth in scout.habitation.low_berths) == pytest.approx(_expected.low_berth_tons_total)
    assert sum(berth.power for berth in scout.habitation.low_berths) == pytest.approx(_expected.low_berth_power_total)
    assert scout.habitation.common_area is not None
    assert scout.habitation.common_area.tons == pytest.approx(_expected.common_area_tons)

    assert scout.available_power == pytest.approx(_expected.available_power)
    assert scout.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert scout.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert scout.jump_power_load == pytest.approx(_expected.power_jump)
    assert scout.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert scout.weapon_power_load == pytest.approx(_expected.power_weapons)
    assert scout.fuel_power_load == pytest.approx(_expected.power_fuel_processor)
    assert scout.total_power_load == pytest.approx(_expected.total_power)

    assert scout.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert scout.sales_price_new == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert scout.expenses.maintenance == pytest.approx(_expected.maintenance_cr)
    assert scout.notes.errors == _expected.expected_errors
    assert scout.notes.warnings == _expected.expected_warnings
    assert scout.crew.notes.infos == _expected.expected_crew_infos
    assert scout.crew.notes.warnings == _expected.expected_crew_warnings
