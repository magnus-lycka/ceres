"""Reference ship case based on refs/RevisedBowulf.md.

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
    formula for the same manifest
  - the source fuel-expense total is slightly lower than Ceres now that
    operation fuel follows the book rule of a 1-ton minimum four-week baseline
- deliberate interpretation:
  - Ceres warns that the installed medical bay calls for a medic, even though
    the source export lists only four crew
- model interpretation rather than dedicated installed rows:
  - passenger luggage / baggage storage (`RI-002`)
  - stores and spares (`RI-001`)
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer, ComputerSection, JumpControl
from ceres.make.ship.crew import Astrogator, Engineer, Pilot, ShipCrew, Steward
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive, MDrive, PowerSection
from ceres.make.ship.habitation import AdvancedEntertainmentSystem, HabitationSection, LowBerth, Stateroom
from ceres.make.ship.parts import Budget, IncreasedSize
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
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


def build_revised_beowulf() -> ship.Ship:
    """
    Build the Revised Beowulf reference case from refs/RevisedBowulf.md.

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
        drives=DriveSection(m_drive=MDrive(level=1), j_drive=JDrive(level=1)),
        power=PowerSection(
            fusion_plant=FusionPlantTL12(output=65, customisation=Budget(modifications=[IncreasedSize]))
        ),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=1),
            operation_fuel=OperationFuel(weeks=4),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(hardware=Computer(score=5), software=[JumpControl(rating=1)]),
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
        passenger_vector={'middle': 16},
    )


def test_revised_beowulf_matches_current_modeled_subset():
    beowulf = build_revised_beowulf()

    assert beowulf.hull_cost == pytest.approx(9_000_000)
    assert beowulf.hull_points == 72

    assert beowulf.drives is not None
    assert beowulf.drives.m_drive is not None
    assert beowulf.drives.m_drive.tons == pytest.approx(2.0)
    assert beowulf.drives.m_drive.cost == pytest.approx(4_000_000)

    assert beowulf.drives.j_drive is not None
    assert beowulf.drives.j_drive.tons == pytest.approx(10.0)
    assert beowulf.drives.j_drive.cost == pytest.approx(15_000_000)

    assert beowulf.power is not None
    assert beowulf.power.fusion_plant is not None
    assert beowulf.power.fusion_plant.tons == pytest.approx(5.4166666667)
    assert beowulf.power.fusion_plant.cost == pytest.approx(3_250_000)

    assert beowulf.fuel is not None
    assert beowulf.fuel.jump_fuel is not None
    assert beowulf.fuel.jump_fuel.tons == pytest.approx(20.0)
    assert beowulf.fuel.operation_fuel is not None
    assert beowulf.fuel.operation_fuel.tons == pytest.approx(1.0)
    assert beowulf.fuel.fuel_processor is not None
    assert beowulf.fuel.fuel_processor.tons == pytest.approx(1.0)
    assert beowulf.fuel.fuel_processor.cost == pytest.approx(50_000)

    assert beowulf.command is not None
    assert beowulf.command.bridge is not None
    assert beowulf.command.bridge.tons == pytest.approx(10.0)
    assert beowulf.command.bridge.cost == pytest.approx(1_250_000)

    assert beowulf.habitation is not None
    assert beowulf.habitation.low_berths is not None
    assert sum(berth.tons for berth in beowulf.habitation.low_berths) == pytest.approx(10.0)
    assert sum(berth.cost for berth in beowulf.habitation.low_berths) == pytest.approx(1_000_000)
    assert beowulf.habitation.entertainment is not None
    assert beowulf.habitation.entertainment.cost == pytest.approx(5_000.0)

    assert beowulf.available_power == pytest.approx(65.0)
    assert beowulf.basic_hull_power_load == pytest.approx(40.0)
    assert beowulf.jump_power_load == pytest.approx(20.0)
    assert beowulf.maneuver_power_load == pytest.approx(20.0)
    assert beowulf.sensor_power_load == pytest.approx(1.0)
    assert beowulf.weapon_power_load == pytest.approx(0.0)
    assert beowulf.fuel_power_load == pytest.approx(1.0)
    assert beowulf.total_power_load == pytest.approx(65.0)

    # Source export also includes passenger luggage/storage and supplies rows.
    # Those are treated via RI-002 and RI-001 rather than as dedicated design
    # components in this reference case.
    assert CargoSection.cargo_tons_for_ship(beowulf) == pytest.approx(64.5)
    assert beowulf.production_cost == pytest.approx(49_785_000.0)
    assert beowulf.sales_price_new == pytest.approx(44_806_500.0)
    assert beowulf.expenses.maintenance == pytest.approx(3734.0)
    assert beowulf.expenses.life_support == pytest.approx(30_000.0)
    assert beowulf.expenses.crew_salaries == pytest.approx(17_000.0)
    assert beowulf.expenses.fuel == pytest.approx(4_100.0)
    assert [(role.role, quantity, role.monthly_salary) for role, quantity in beowulf.crew.grouped_roles] == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
        ('STEWARD', 1, 2_000),
    ]
    assert ('warning', 'MEDIC below recommended count: 0 < 1') in [
        (note.category.value, note.message) for note in beowulf.crew.notes
    ]
