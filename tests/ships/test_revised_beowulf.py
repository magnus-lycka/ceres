"""Reference ship case based on refs/tycho/RevisedBowulf.md.

Purpose:
- exercise a lighter revised Beowulf variant against the same baseline rules as
  the standard Beowulf
- preserve one explicit example of a source case that includes export-specific
  rows and assumptions beyond the current Ceres model

Source handling for this test case:
- supported: light streamlined hull, armour, drives, budget/increased-size
  fusion plant, habitation, workshop, medical bay, cargo hold, crew manifest,
  planned passenger manifest, entertainment cost, production cost,
  discounted purchase price, crew salaries
- ignored for test-case modelling:
  - battle-load figures (`TCS-002`)
  - income / profit rows (`TCS-003`)
- still excluded from the modeled reference case:
  - cost-reduction labels on drives, for which we have found no support in our
    current documented rules sources
  - advanced low berth pricing/details
  - the source life-support total is Cr1000 higher than the current core-rule
    formula for the same manifest: Ceres computes Cr10000 facilities plus
    Cr20000 for four crew and 16 middle passengers. The source also lists 20
    low-passage berths, but no planned low passengers; if all were occupied,
    the rules would add Cr2000, not Cr1000.
  - the source fuel-expense total is slightly lower than Ceres now that
    operation fuel follows the book rule of a 1-ton minimum four-week baseline
- deliberate interpretation:
  - Ceres warns that the installed medical bay calls for a medic, even though
    the source export lists only four crew
- model interpretation rather than dedicated installed rows:
  - passenger luggage / baggage storage (`RIS-002`)
  - stores and spares (`RIS-001`)
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crew import Astrogator, Engineer, Pilot, ShipCrew, Steward
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive1, MDrive1, PowerSection
from ceres.make.ship.habitation import AdvancedEntertainmentSystem, HabitationSection, LowBerth, Stateroom
from ceres.make.ship.occupants import MiddlePassage
from ceres.make.ship.parts import Budget, IncreasedSize
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
from ceres.make.ship.systems import Airlock, CommonArea, MedicalBay, SystemsSection, Workshop

_expected = SimpleNamespace(
    tl=12,
    displacement=200,
    hull_cost_mcr=9.0,  # Light Streamlined Hull: 9,000,000
    hull_points=72,  # Light hull: 72
    armour_tons=6.0,
    armour_cost_mcr=1.2,  # Crystaliron: 1,200,000
    m_drive_tons=2.0,
    m_drive_cost_mcr=3.2,  # ref: 3,200,000 (Cost Reduction 3); Ceres uses 4,000,000 (no cost-reduction rule)
    j_drive_tons=10.0,
    j_drive_cost_mcr=10.5,  # ref: 10,500,000 (Cost Reduction 3); Ceres uses 15,000,000 (no cost-reduction rule)
    plant_tons=5.4166666667,  # Budget+IncreasedSize: 5.42 tons (ref)
    plant_cost_mcr=3.25,  # Budget+IncreasedSize: 3,250,000
    jump_fuel_tons=20.0,
    op_fuel_tons=0.54,  # ref: 0.54 tons; Ceres gives 1.0 per RIS-007 (1-ton minimum)
    fuel_processor_tons=1.0,
    fuel_processor_cost_cr=50_000,
    bridge_tons=10.0,
    bridge_cost_mcr=1.25,  # Standard Bridge 1,000,000 + Holographic Controls 250,000
    low_berth_tons_total=10.0,
    low_berth_cost_total_mcr=1.0,  # ref shows 1,800,000 for Advanced Low Berths; Ceres models standard at 1,000,000
    entertainment_cost_cr=5_000,
    available_power=65.0,
    power_basic=40.0,  # Basic/Hull 40 PP
    power_jump=20.0,
    power_maneuver=20.0,
    power_sensors=1.0,
    power_fuel=1.0,
    total_power=65.0,  # 40+20+20+1+1+2 (low_berths)+1 (medical bay) = 85; ref max load 87
    cargo_tons=64.5,  # ref: 67.50 Ton Cargo Bay (Ceres remainder given other components)
    production_cost_mcr=46.285,  # ref: 46,285,000; Ceres gives 49,785,000 (drive cost difference)
    sales_price_mcr=41.6565,  # ref: 41,656,500; Ceres gives 44,806,500 (drive cost difference)
    maintenance_cr=3_471,  # ref: 3,471; Ceres gives 3,734 (production cost difference)
    life_support_cr=31_000,  # ref: 31,000; Ceres gives 30,000 (4 crew + 16 middle pax)
    crew_salaries_cr=17_000,
    fuel_expense_cr=4_054.17,  # ref: 4,054.17; Ceres gives 4,100 (op fuel 1-ton minimum)
)

# Ceres gives op_fuel_tons=1.0 per RIS-007 (1-ton minimum), not 0.54 as in ref
_expected.op_fuel_tons = 1.0
# Ceres does not model cost-reduction drives; m_drive and j_drive use standard pricing
_expected.m_drive_cost_mcr = 4.0
_expected.j_drive_cost_mcr = 15.0
# Ceres gives production_cost and sales_price based on standard drive costs
_expected.production_cost_mcr = 49_785_000 / 1_000_000
_expected.sales_price_mcr = 44_806_500 / 1_000_000
# Ceres gives maintenance based on its production cost
_expected.maintenance_cr = 3_734.0
# Ceres gives life_support=30_000 (4 crew + 16 middle pax), not 31_000 as in ref
_expected.life_support_cr = 30_000.0
# Ceres gives fuel_expense=4_100 due to 1-ton op fuel minimum per RIS-007
_expected.fuel_expense_cr = 4_100.0


def build_revised_beowulf() -> ship.Ship:
    """
    Build the Revised Beowulf reference case from refs/tycho/RevisedBowulf.md.

    Excluded from this reference mapping:
    - cost reduction on M-drive and jump drive
    - advanced low berth pricing/details
    - the reference expense assumptions for life support and purchased fuel
    """

    return ship.Ship(
        ship_class='Beowulf',
        ship_type='Free Trader, Revised',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull.model_copy(
                update={'light': True, 'description': 'Light Streamlined Hull'},
            ),
            armour=armour.CrystalironArmour(protection=2),
            airlocks=[Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive1(), j_drive=JDrive1()),
        power=PowerSection(plant=FusionPlantTL12(output=65, customisation=Budget(modifications=[IncreasedSize]))),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=1),
            operation_fuel=OperationFuel(weeks=4),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(hardware=Computer5(), software=[JumpControl(rating=1)]),
        sensors=SensorsSection(primary=CivilianSensors()),
        systems=SystemsSection(internal_systems=[MedicalBay(), Workshop()]),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            low_berths=[LowBerth()] * 20,
            common_area=CommonArea(tons=10.0),
            entertainment=AdvancedEntertainmentSystem(cost=5_000),
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=67.5, crane=CargoCrane())]),
        crew=ShipCrew(roles=[Pilot(), Astrogator(), Engineer(), Steward()]),
        occupants=[MiddlePassage()] * 16,
    )


def test_revised_beowulf_matches_current_modeled_subset():
    beowulf = build_revised_beowulf()

    assert beowulf.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert beowulf.hull_points == _expected.hull_points

    assert beowulf.drives is not None
    assert beowulf.drives.m_drive is not None
    assert beowulf.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert beowulf.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)

    assert beowulf.drives.j_drive is not None
    assert beowulf.drives.j_drive.tons == pytest.approx(_expected.j_drive_tons)
    assert beowulf.drives.j_drive.cost == pytest.approx(_expected.j_drive_cost_mcr * 1_000_000)

    assert beowulf.power is not None
    assert beowulf.power.plant is not None
    assert beowulf.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert beowulf.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)

    assert beowulf.fuel is not None
    assert beowulf.fuel.jump_fuel is not None
    assert beowulf.fuel.jump_fuel.tons == pytest.approx(_expected.jump_fuel_tons)
    assert beowulf.fuel.operation_fuel is not None
    assert beowulf.fuel.operation_fuel.tons == pytest.approx(_expected.op_fuel_tons)
    assert beowulf.fuel.fuel_processor is not None
    assert beowulf.fuel.fuel_processor.tons == pytest.approx(_expected.fuel_processor_tons)
    assert beowulf.fuel.fuel_processor.cost == pytest.approx(_expected.fuel_processor_cost_cr)

    assert beowulf.command is not None
    assert beowulf.command.bridge is not None
    assert beowulf.command.bridge.tons == pytest.approx(_expected.bridge_tons)
    assert beowulf.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)

    assert beowulf.habitation is not None
    assert beowulf.habitation.low_berths is not None
    assert sum(berth.tons for berth in beowulf.habitation.low_berths) == pytest.approx(_expected.low_berth_tons_total)
    assert sum(berth.cost for berth in beowulf.habitation.low_berths) == pytest.approx(
        _expected.low_berth_cost_total_mcr * 1_000_000
    )
    assert beowulf.habitation.entertainment is not None
    assert beowulf.habitation.entertainment.cost == pytest.approx(_expected.entertainment_cost_cr)

    assert beowulf.available_power == pytest.approx(_expected.available_power)
    assert beowulf.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert beowulf.jump_power_load == pytest.approx(_expected.power_jump)
    assert beowulf.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert beowulf.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert beowulf.weapon_power_load == pytest.approx(0.0)
    assert beowulf.fuel_power_load == pytest.approx(_expected.power_fuel)
    assert beowulf.total_power_load == pytest.approx(_expected.total_power)

    # Source export also includes passenger luggage/storage and supplies rows.
    # Those are treated via RIS-002 and RIS-001 rather than as dedicated design
    # components in this reference case.
    assert CargoSection.cargo_tons_for_ship(beowulf) == pytest.approx(_expected.cargo_tons)
    assert beowulf.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert beowulf.sales_price_new == pytest.approx(_expected.sales_price_mcr * 1_000_000)
    assert beowulf.expenses.maintenance == pytest.approx(_expected.maintenance_cr)
    assert beowulf.expenses.life_support_facilities == pytest.approx(10_000.0)
    assert beowulf.expenses.life_support_people == pytest.approx(20_000.0)
    assert beowulf.expenses.life_support == pytest.approx(_expected.life_support_cr)
    assert beowulf.expenses.crew_salaries == pytest.approx(_expected.crew_salaries_cr)
    assert beowulf.expenses.fuel == pytest.approx(_expected.fuel_expense_cr)
    assert [(role.role, quantity, role.monthly_salary) for role, quantity in beowulf.crew.grouped_roles] == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
        ('STEWARD', 1, 2_000),
    ]
    assert 'MEDIC below recommended count: 0 < 1' in beowulf.crew.notes.warnings
