"""Reference ship case based on refs/KingKayLuxuryLiner.csv.

Purpose:
- provide a large source-derived commercial liner reference slice
- exercise close-structure hulls, large TL12 jump/fusion hardware, holographic
  bridge controls, luxury/high/standard accommodation, and large docking spaces
- keep one explicit example of a source sheet that exceeds current Ceres
  support in several non-trivial areas

Source handling for this test case:
- supported: hull, drives, power plant, fuel tankage, bridge, computer,
  software, civilian sensors, medical bay, standard/high/luxury staterooms,
  common area, commercial zone, swimming pool, theatre, wet bar, low berths,
  docking-space tonnage/cost, and the explicit crew manifest
- deliberate source normalization:
  - the CSV lists bundled computer software rows such as `Library`,
    `Manoeuvre`, and `Intellect` explicitly
  - Ceres treats those as included software provided by the primary computer,
    so only the separately costed `Jump Control/2` is added explicitly in this
    reference case
- current model limitation:
  - Ceres models empty docking spaces through a placeholder occupant object,
    but suppresses any separate carried-craft row in the spec
- deliberate interpretation:
  - source-listed `Marines` on this liner are treated as shipboard security
    staff rather than as proof that the vessel should use military ship rules
    (`RI-006`)
- still excluded from the modeled reference case:
  - `Gaming Space`
  - cargo, total cost, purchase cost, maintenance cost, and crew/life-support
    totals, because the excluded rows above materially affect them
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer, ComputerSection, JumpControl
from ceres.make.ship.crafts import CraftSection, EmptyOccupant, InternalDockingSpace
from ceres.make.ship.crew import (
    Administrator,
    Astrogator,
    Captain,
    Engineer,
    GeneralCrew,
    Maintenance,
    Marine,
    Medic,
    Officer,
    Pilot,
    ShipCrew,
    Steward,
)
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive, MDrive, PowerSection
from ceres.make.ship.habitation import HabitationSection, HighStateroom, LowBerth, LuxuryStateroom, Stateroom
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.storage import FuelSection, JumpFuel, OperationFuel
from ceres.make.ship.systems import (
    CommercialZone,
    CommonArea,
    MedicalBay,
    SwimmingPool,
    SystemsSection,
    Theatre,
    WetBar,
)


def build_king_kay() -> ship.Ship:
    """Build the modeled King Kay reference slice from refs/KingKayLuxuryLiner.csv."""
    return ship.Ship(
        ship_class='King Kay',
        ship_type='Luxury Liner',
        tl=12,
        displacement=5_000,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(configuration=hull.close_structure),
        drives=DriveSection(m_drive=MDrive(level=1), j_drive=JDrive(level=2)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=2_010)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=8),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Computer(score=10),
            backup_hardware=Computer(score=5, bis=True),
            software=[JumpControl(rating=2)],
        ),
        sensors=SensorsSection(primary=CivilianSensors()),
        craft=CraftSection(
            internal_housing=[
                InternalDockingSpace(craft=EmptyOccupant(docking_space=70)),
                InternalDockingSpace(craft=EmptyOccupant(docking_space=70)),
                InternalDockingSpace(craft=EmptyOccupant(docking_space=252)),
            ]
        ),
        systems=SystemsSection(
            internal_systems=[MedicalBay(), CommercialZone(tons=240)],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 80 + [HighStateroom()] * 192 + [LuxuryStateroom()] * 8,
            common_area=CommonArea(tons=388),
            swimming_pool=SwimmingPool(tons=60),
            theatres=[Theatre(tons=100), Theatre(tons=100), Theatre(tons=100)],
            wet_bar=WetBar(),
            low_berths=[LowBerth()] * 18,
        ),
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 3,
                Astrogator(),
                *[Engineer()] * 16,
                *[GeneralCrew()] * 55,
                *[Maintenance()] * 5,
                *[Steward()] * 65,
                *[Administrator()] * 10,
                *[Medic()] * 5,
                *[Officer()] * 11,
                *[Marine()] * 10,
            ]
        ),
    )


def test_king_kay_matches_supported_reference_slice():
    liner = build_king_kay()

    assert liner.ship_class == 'King Kay'
    assert liner.ship_type == 'Luxury Liner'
    assert liner.tl == 12
    assert liner.displacement == 5_000

    assert liner.hull_cost == pytest.approx(200_000_000.0)
    assert liner.hull_points == pytest.approx(2_000.0)
    assert liner.hull.airlocks is not None
    assert len(liner.hull.airlocks) == 10
    assert all(airlock.tons == 0.0 for airlock in liner.hull.airlocks)

    assert liner.drives is not None
    assert liner.drives.m_drive is not None
    assert liner.drives.m_drive.tons == pytest.approx(50.0)
    assert liner.drives.m_drive.cost == pytest.approx(100_000_000.0)
    assert liner.drives.m_drive.power == pytest.approx(500.0)

    assert liner.drives.j_drive is not None
    assert liner.drives.j_drive.tons == pytest.approx(255.0)
    assert liner.drives.j_drive.cost == pytest.approx(382_500_000.0)
    assert liner.drives.j_drive.power == pytest.approx(1_000.0)

    assert liner.power is not None
    assert liner.power.fusion_plant is not None
    assert liner.power.fusion_plant.tons == pytest.approx(134.0)
    assert liner.power.fusion_plant.cost == pytest.approx(134_000_000.0)
    assert liner.available_power == pytest.approx(2_010.0)

    assert liner.fuel is not None
    assert liner.fuel.jump_fuel is not None
    assert liner.fuel.jump_fuel.tons == pytest.approx(1_000.0)
    assert liner.fuel.operation_fuel is not None
    assert liner.fuel.operation_fuel.tons == pytest.approx(27.0)

    assert liner.command is not None
    assert liner.command.bridge is not None
    assert liner.command.bridge.tons == pytest.approx(60.0)
    assert liner.command.bridge.cost == pytest.approx(31_250_000.0)

    assert liner.computer is not None
    assert liner.computer.hardware is not None
    assert liner.computer.hardware.cost == pytest.approx(160_000.0)
    assert liner.computer.backup_hardware is not None
    assert liner.computer.backup_hardware.cost == pytest.approx(45_000.0)
    assert [(package.description, package.cost) for package in liner.computer.software_packages.values()] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000.0),
    ]
    assert not any(
        note.message.startswith('Redundant ')
        for package in liner.computer.software_packages.values()
        for note in package.notes
    )

    assert liner.sensors.primary.tons == pytest.approx(1.0)
    assert liner.sensors.primary.cost == pytest.approx(3_000_000.0)

    assert liner.craft is not None
    docking_spaces = liner.craft._all_parts()
    assert [space.tons for space in docking_spaces] == pytest.approx([77.0, 77.0, 278.0])
    assert [space.cost for space in docking_spaces] == pytest.approx([19_250_000.0, 19_250_000.0, 69_500_000.0])

    assert liner.systems is not None
    assert liner.systems.medical_bay is not None
    assert liner.systems.medical_bay.tons == pytest.approx(4.0)
    assert liner.systems.medical_bay.cost == pytest.approx(2_000_000.0)
    assert liner.systems.medical_bay.power == pytest.approx(1.0)
    assert liner.systems.commercial_zone is not None
    assert liner.systems.commercial_zone.tons == pytest.approx(240.0)
    assert liner.systems.commercial_zone.cost == pytest.approx(48_000_000.0)
    assert liner.systems.commercial_zone.power == pytest.approx(1.0)

    assert liner.habitation is not None
    assert liner.habitation.staterooms is not None
    standard_rooms = [room for room in liner.habitation.staterooms if type(room) is Stateroom]
    high_rooms = [room for room in liner.habitation.staterooms if isinstance(room, HighStateroom)]
    luxury_rooms = [room for room in liner.habitation.staterooms if isinstance(room, LuxuryStateroom)]
    assert sum(room.tons for room in standard_rooms) == pytest.approx(320.0)
    assert sum(room.cost for room in standard_rooms) == pytest.approx(40_000_000.0)
    assert sum(room.tons for room in high_rooms) == pytest.approx(1_152.0)
    assert sum(room.cost for room in high_rooms) == pytest.approx(153_600_000.0)
    assert sum(room.tons for room in luxury_rooms) == pytest.approx(80.0)
    assert sum(room.cost for room in luxury_rooms) == pytest.approx(12_000_000.0)
    assert liner.habitation.common_area is not None
    assert liner.habitation.common_area.tons == pytest.approx(388.0)
    assert liner.habitation.common_area.cost == pytest.approx(38_800_000.0)
    assert liner.habitation.swimming_pool is not None
    assert liner.habitation.swimming_pool.tons == pytest.approx(60.0)
    assert liner.habitation.swimming_pool.cost == pytest.approx(1_200_000.0)
    assert [theatre.tons for theatre in liner.habitation.theatres] == pytest.approx([100.0, 100.0, 100.0])
    assert [theatre.cost for theatre in liner.habitation.theatres] == pytest.approx(
        [10_000_000.0, 10_000_000.0, 10_000_000.0]
    )
    assert liner.habitation.wet_bar is not None
    assert liner.habitation.wet_bar.cost == pytest.approx(2_000.0)
    assert liner.habitation.low_berths is not None
    assert sum(berth.tons for berth in liner.habitation.low_berths) == pytest.approx(9.0)
    assert sum(berth.cost for berth in liner.habitation.low_berths) == pytest.approx(900_000.0)
    assert sum(berth.power for berth in liner.habitation.low_berths) == pytest.approx(2.0)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in liner.crew.grouped_roles] == [
        ('CAPTAIN', 1, 10_000),
        ('PILOT', 3, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 16, 4_000),
        ('GENERAL CREW', 55, 1_000),
        ('MAINTENANCE', 5, 1_000),
        ('STEWARD', 65, 2_000),
        ('ADMINISTRATOR', 10, 1_500),
        ('MEDIC', 5, 4_000),
        ('OFFICER', 11, 5_000),
        ('MARINE', 10, 1_000),
    ]
    assert liner.expenses.crew_salaries == pytest.approx(387_000.0)

    assert liner.basic_hull_power_load == pytest.approx(1_000.0)
    assert liner.total_power_load == pytest.approx(2_005.0)
    assert not any(note.category.value == 'error' for note in liner.notes)


def test_king_kay_spec_contains_supported_liner_rows():
    spec = build_king_kay().build_spec()

    assert spec.ship_class == 'King Kay'
    assert spec.ship_type == 'Luxury Liner'
    assert spec.tl == 12
    assert spec.hull_points == pytest.approx(2_000.0)

    assert spec.row('Close Structure Hull').section == 'Hull'
    assert spec.row('Holographic Controls').section == 'Command'
    assert spec.row('Computer/10').section == 'Computer'
    assert spec.row('Backup Computer/5/bis').section == 'Computer'
    assert spec.row('Civilian Grade Sensors').section == 'Sensors'
    assert spec.row('Commercial Zone').section == 'Systems'
    assert spec.row('Swimming Pool').section == 'Habitation'
    assert spec.row('Theatre').quantity == 3
    assert spec.row('Wet Bar').section == 'Habitation'
    assert len(spec.rows_matching('Docking Space (70 tons)')) == 2
    assert spec.row('Docking Space (252 tons)').section == 'Craft'
    assert spec.row('Medical Bay').section == 'Systems'
    assert spec.row('Luxury Staterooms').quantity == 8
    assert spec.row('High Staterooms').quantity == 192
    assert spec.row('Staterooms').quantity == 80
    assert spec.row('Common Area').section == 'Habitation'
    assert not any('Passenger Tender' in row.item for row in spec.rows_for_section('Craft'))
