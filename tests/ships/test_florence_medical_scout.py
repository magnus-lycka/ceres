import pytest

from tycho import hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer15, ComputerSection, JumpControl3
from tycho.crafts import AirRaft, CraftSection, InternalDockingSpace, SlowPinnace
from tycho.drives import DriveSection, FusionPlantTL12, JumpDrive3, MDrive2, PowerSection
from tycho.habitation import HabitationSection, LowBerths, Staterooms
from tycho.sensors import LifeScannerAnalysisSuite, MilitarySensors, SensorsSection
from tycho.storage import FuelProcessor, FuelScoops, FuelSection, JumpFuel, OperationFuel
from tycho.systems import BriefingRoom, CommonArea, Laboratory, MedicalBays, SystemsSection
from tycho.weapons import Turret, WeaponsSection

from ._markdown_output import write_markdown_output


def build_florence_medical_scout() -> ship.Ship:
    return ship.Ship(
        ship_class='Florence',
        ship_type='Medical Scout',
        military=False,
        tl=14,
        displacement=400,
        design_type=ship.ShipDesignType.CUSTOM,
        crew_vector={
            'CAPTAIN': 1,
            'PILOT': 2,
            'ASTROGATOR': 1,
            'ENGINEER': 2,
            'MAINTENANCE': 1,
            'MEDIC': 6,
        },
        passenger_vector={},
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive2(), jump_drive=JumpDrive3()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=300)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=3),
            operation_fuel=OperationFuel(weeks=12),
            fuel_scoops=FuelScoops(),
            fuel_processor=FuelProcessor(tons=3),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer15(), software=[JumpControl3()]),
        sensors=SensorsSection(primary=MilitarySensors(), life_scanner_analysis_suite=LifeScannerAnalysisSuite()),
        weapons=WeaponsSection(turrets=[Turret(size='double')]),
        craft=CraftSection(
            docking_space=InternalDockingSpace(craft=SlowPinnace()),
            auxiliary_docking_spaces=[
                InternalDockingSpace(craft=AirRaft()),
                InternalDockingSpace(craft=AirRaft()),
            ],
        ),
        systems=SystemsSection(
            medical_bays=MedicalBays(count=6),
            laboratory=Laboratory(),
            briefing_room=BriefingRoom(),
        ),
        habitation=HabitationSection(
            staterooms=Staterooms(count=8),
            low_berths=LowBerths(count=20),
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
    assert scout.drives.jump_drive is not None
    assert scout.drives.jump_drive.tons == pytest.approx(35.0)
    assert scout.drives.jump_drive.cost == pytest.approx(52_500_000)

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
    assert scout.systems.medical_bays is not None
    assert scout.systems.medical_bays.tons == pytest.approx(24.0)
    assert scout.systems.medical_bays.cost == pytest.approx(12_000_000)
    assert scout.systems.medical_bays.power == pytest.approx(6.0)
    assert scout.systems.laboratory is not None
    assert scout.systems.briefing_room is not None

    assert scout.habitation is not None
    assert scout.habitation.staterooms is not None
    assert scout.habitation.staterooms.tons == pytest.approx(32.0)
    assert scout.habitation.low_berths is not None
    assert scout.habitation.low_berths.tons == pytest.approx(10.0)
    assert scout.habitation.low_berths.power == pytest.approx(2.0)
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


def test_florence_medical_scout_markdown_output():
    scout = build_florence_medical_scout()
    table = scout.markdown_table()
    write_markdown_output('test_florence_medical_scout', table)

    assert '## *Florence* Medical Scout | TL14 | Hull 160' in table
    assert '| Hull | Standard Hull | **400.00** |  | 20000.00 |' in table
    assert '| Propulsion | M-Drive 2 | 8.00 | 80.00 | 16000.00 |' in table
    assert '| Jump | Jump 3 | 35.00 | 120.00 | 52500.00 |' in table
    assert '| Power | Fusion (TL 12) | 20.00 | **300.00** | 20000.00 |' in table
    assert '| Fuel | J-3, 12 weeks of operation | 126.00 |  |  |' in table
    assert '|  | Fuel Scoops |  |  | 1000.00 |' in table
    assert '|  | Fuel Processor (60 tons/day) | 3.00 | 3.00 | 150.00 |' in table
    assert '| Computer | Computer/15 |  |  | 2000.00 |' in table
    assert '|  | Jump Control/3 |  |  | 300.00 |' in table
    assert '| Sensors | Military Grade | 2.00 | 2.00 | 4100.00 |' in table
    assert '|  | Life Scanner Analysis Suite | 1.00 | 1.00 | 4000.00 |' in table
    assert '| Weapons | Double Turret | 1.00 | 1.00 | 500.00 |' in table
    assert '| Craft | Internal Docking Space: Slow Pinnace | 44.00 |  | 11000.00 |' in table
    assert '|  | Slow Pinnace |  |  | 6630.00 |' in table
    assert table.count('Internal Docking Space: Air/Raft') == 2
    assert table.count('|  | Air/Raft |  |  | 250.00 |') == 2
    assert '| Systems | Medical Bays | 24.00 | 6.00 | 12000.00 |' in table
    assert '|  | Laboratory | 4.00 |  | 1000.00 |' in table
    assert '|  | Briefing Room | 4.00 |  | 500.00 |' in table
    assert '| Habitation | Staterooms × 8 | 32.00 |  | 4000.00 |' in table
    assert '|  | Low Berths × 20 | 10.00 | 2.00 | 1000.00 |' in table
    assert '|  | Common Area | 32.00 |  | 3200.00 |' in table
    assert 'stores and spares' not in table
    assert 'No airlock installed' not in table
