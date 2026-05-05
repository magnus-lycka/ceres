"""Reference ship case based on refs/Beowulf.md.

Purpose:
- provide a compact source-derived commercial baseline ship
- exercise standard TL12 Streamlined/J-1/M-1/Fusion-75 design rules
- keep one explicit example of how we map Anderson-style export rows into Ceres

Source handling for this test case:
- supported: hull, armour, drives, power plant, fuel, bridge, computer,
  sensors, common area, staterooms, low berths, cargo crane, cargo hold,
  crew manifest, planned passenger manifest, production cost, discounted
  purchase price, crew salaries
- ignored for test-case modelling:
  - battle-load figures (`TCS-002`)
  - income / profit rows (`TCS-003`)
- still excluded from the modeled reference case:
  - the source life-support total is Cr1000 higher than the current core-rule
    formula for the same manifest
  - the source fuel-expense total is Cr50 lower than Ceres now that operation
    fuel follows the book rule of a 1-ton minimum four-week baseline
- model interpretation rather than dedicated installed rows:
  - stores and spares (`RI-001`)
  - passenger luggage / baggage storage (`RI-002`)
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import (
    Computer,
    ComputerSection,
)
from ceres.make.ship.crew import Astrogator, Engineer, Pilot, ShipCrew, Steward
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive, MDrive, PowerSection
from ceres.make.ship.habitation import HabitationSection, LowBerth, Stateroom
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import (
    CargoCrane,
    CargoHold,
    CargoSection,
    FuelProcessor,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import Airlock, CommonArea


def build_beowulf() -> ship.Ship:
    """Build the Beowulf reference case from refs/Beowulf.md."""
    return ship.Ship(
        ship_class='Beowulf',
        ship_type='Type A Free Trader',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            armour=armour.CrystalironArmour(protection=2),
            airlocks=[Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive(level=1), j_drive=JDrive(level=1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=75)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=1),
            operation_fuel=OperationFuel(weeks=4),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(processing=5), software=[JumpControl(rating=1)]),
        sensors=SensorsSection(primary=CivilianSensors()),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            low_berths=[LowBerth()] * 20,
            common_area=CommonArea(tons=10.0),
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(crane=CargoCrane())]),
        crew=ShipCrew(roles=[Pilot(), Astrogator(), Engineer(), Steward()]),
        passenger_vector={'middle': 16},
    )


def test_beowulf_hull():
    beowulf = build_beowulf()
    assert beowulf.hull_cost == 12_000_000
    assert beowulf.hull_points == 80


def test_beowulf_armour():
    beowulf = build_beowulf()
    a = beowulf.hull.armour
    assert a is not None
    assert a.tons == pytest.approx(6.0)
    assert a.cost == 1_200_000


def test_beowulf_drives():
    beowulf = build_beowulf()
    assert beowulf.drives is not None
    assert beowulf.drives.m_drive is not None
    assert beowulf.drives.m_drive.tons == pytest.approx(2.0)
    assert beowulf.drives.m_drive.cost == 4_000_000
    assert beowulf.drives.m_drive.power == 20

    assert beowulf.drives.j_drive is not None
    assert beowulf.drives.j_drive.tons == pytest.approx(10.0)
    assert beowulf.drives.j_drive.cost == 15_000_000
    assert beowulf.drives.j_drive.power == 20


def test_beowulf_fusion_plant():
    beowulf = build_beowulf()
    assert beowulf.power is not None
    fp = beowulf.power.fusion_plant
    assert fp is not None
    assert fp.output == 75
    assert fp.tons == pytest.approx(5.0)
    assert fp.cost == 5_000_000


def test_beowulf_fuel():
    beowulf = build_beowulf()
    assert beowulf.fuel is not None
    assert beowulf.fuel.jump_fuel is not None
    assert beowulf.fuel.jump_fuel.tons == pytest.approx(20.0)
    assert beowulf.fuel.operation_fuel is not None
    assert beowulf.fuel.operation_fuel.tons == pytest.approx(1.0)
    assert beowulf.fuel.fuel_processor is not None
    assert beowulf.fuel.fuel_processor.tons == pytest.approx(1.0)
    assert beowulf.fuel.fuel_processor.cost == 50_000


def test_beowulf_bridge():
    beowulf = build_beowulf()
    assert beowulf.command is not None
    b = beowulf.command.bridge
    assert b is not None
    assert b.tons == pytest.approx(10.0)
    assert b.cost == 1_000_000


def test_beowulf_staterooms():
    beowulf = build_beowulf()
    assert beowulf.habitation is not None
    assert beowulf.habitation.staterooms is not None
    assert len(beowulf.habitation.staterooms) == 10
    assert sum(room.tons for room in beowulf.habitation.staterooms) == pytest.approx(40.0)
    assert sum(room.cost for room in beowulf.habitation.staterooms) == 5_000_000

    assert beowulf.habitation.low_berths is not None
    assert len(beowulf.habitation.low_berths) == 20
    assert sum(berth.tons for berth in beowulf.habitation.low_berths) == pytest.approx(10.0)
    assert sum(berth.cost for berth in beowulf.habitation.low_berths) == 1_000_000
    assert sum(berth.power for berth in beowulf.habitation.low_berths) == 2


def test_beowulf_systems():
    beowulf = build_beowulf()
    assert beowulf.habitation is not None
    assert beowulf.habitation.common_area is not None
    assert beowulf.habitation.common_area.tons == pytest.approx(10.0)
    assert beowulf.fuel is not None
    assert beowulf.fuel.fuel_scoops is not None
    assert beowulf.fuel.fuel_scoops.cost == 0.0


def test_beowulf_airlocks_free():
    # 200t ship gets 2 free airlocks
    beowulf = build_beowulf()
    assert len(beowulf.hull.airlocks) == 2
    assert beowulf.hull.airlocks[0].tons == 0.0
    assert beowulf.hull.airlocks[1].tons == 0.0


def test_beowulf_cargo():
    # Source rows:
    # - Cargo Bay: 80.00
    # - Passenger Luggage Storage Area: 0.80 (RI-002)
    # - Supplies / Stores and Spares: 0.70 (RI-001)
    #
    # Ceres does not install luggage or stores/spares as separate design rows in
    # this case, but the resulting usable cargo capacity still lands at 81.5.
    beowulf = build_beowulf()
    assert CargoSection.cargo_tons_for_ship(beowulf) == pytest.approx(81.0, abs=0.01)


def test_beowulf_power():
    beowulf = build_beowulf()
    assert beowulf.available_power == 75
    assert beowulf.basic_hull_power_load == pytest.approx(40.0)
    assert beowulf.maneuver_power_load == 20
    assert beowulf.jump_power_load == 20
    # non-drive: sensors(1) + fuel_processor(1) + low_berths(2) = 4
    assert beowulf.total_power_load == pytest.approx(64.0)


def test_beowulf_production_cost():
    beowulf = build_beowulf()
    assert beowulf.production_cost == pytest.approx(51_380_000)
    assert beowulf.sales_price_new == pytest.approx(46_242_000)


def test_beowulf_crew_and_life_support_match_reference_manifest():
    beowulf = build_beowulf()

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in beowulf.crew.grouped_roles] == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
        ('STEWARD', 1, 2_000),
    ]
    assert beowulf.expenses.life_support == pytest.approx(30_000.0)
    assert beowulf.expenses.crew_salaries == pytest.approx(17_000.0)
    assert beowulf.expenses.fuel == pytest.approx(4_100.0)
    assert not beowulf.notes


def test_beowulf_spec_structure():
    beowulf = build_beowulf()
    spec = beowulf.build_spec()

    assert spec.ship_class == 'Beowulf'
    assert spec.ship_type == 'Type A Free Trader'
    assert spec.tl == 12
    assert spec.hull_points == 80

    assert spec.row('Streamlined Hull').section == 'Hull'
    assert spec.row('Standard Bridge').section == 'Command'
    assert spec.row('Jump 1').section == 'Jump'
    assert spec.row('M-Drive 1').section == 'Propulsion'
    assert spec.row('Fusion (TL 12), Power 75').section == 'Power'
    assert spec.row('J-1, 8 weeks of operation').section == 'Fuel'
    assert spec.row('Fuel Scoops').section == 'Fuel'
    airlock_row = spec.row('Airlock (2 tons)', section='Hull')
    assert airlock_row.section == 'Hull'
    assert airlock_row.quantity == 2
    stateroom_row = spec.row('Staterooms', section='Habitation')
    assert stateroom_row.section == 'Habitation'
    assert stateroom_row.quantity == 10
    low_berth_row = spec.row('Low Berths', section='Habitation')
    assert low_berth_row.section == 'Habitation'
    assert low_berth_row.quantity == 20
    assert spec.row('Common Area').section == 'Habitation'
    assert spec.row('Cargo Hold').section == 'Cargo'
    assert spec.row('Cargo Crane').section == 'Cargo'

    assert spec.expenses[0].label == 'Production Cost'
    assert spec.expenses[0].amount == pytest.approx(51_380_000)
    assert spec.expenses[1].amount == pytest.approx(46_242_000)
    assert [(crew.role, crew.quantity, crew.salary) for crew in spec.crew] == [
        ('PILOT', None, 6_000),
        ('ASTROGATOR', None, 5_000),
        ('ENGINEER', None, 4_000),
        ('STEWARD', None, 2_000),
    ]
