"""Reference ship case based on refs/tycho/KingKayLuxuryLiner.csv.

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
    (`RIS-006`)
- still excluded from the modeled reference case:
  - `Gaming Space`
  - cargo, total cost, purchase cost, maintenance cost, and crew/life-support
    totals, because the excluded rows above materially affect them
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, Computer10, ComputerSection
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
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive1, PowerSection
from ceres.make.ship.habitation import HabitationSection, HighStateroom, LowBerth, LuxuryStateroom, Stateroom
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.software import JumpControl
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

_expected = SimpleNamespace(
    tl=12,
    displacement=5_000,
    hull_cost_mcr=200.0,  # 5000t Close Structure
    hull_points=2_000.0,
    airlocks_count=10,  # included free airlocks for 5000t hull
    m_drive_tons=50.0,
    m_drive_cost_mcr=100.0,
    m_drive_power=500.0,
    j_drive_tons=255.0,
    j_drive_cost_mcr=382.5,
    j_drive_power=1_000.0,
    plant_tons=134.0,
    plant_cost_mcr=134.0,
    available_power=2_010.0,
    jump_fuel_tons=1_000.0,
    operation_fuel_tons=27.0,  # ref shows J-2 + 8 weeks combined 1028t; Ceres: 1000 + 27 = 1027 (1t gap)
    bridge_tons=60.0,
    bridge_cost_mcr=31.25,
    computer_cost_mcr=0.16,
    backup_computer_cost_mcr=0.045,
    software_packages=[
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000.0),
    ],
    sensors_tons=1.0,
    sensors_cost_mcr=3.0,
    docking_spaces_tons=[77.0, 77.0, 278.0],
    docking_spaces_costs_mcr=[19.25, 19.25, 69.5],
    medical_bay_tons=4.0,
    medical_bay_cost_mcr=2.0,
    medical_bay_power=1.0,
    commercial_zone_tons=240.0,
    commercial_zone_cost_mcr=48.0,
    commercial_zone_power=1.0,
    standard_staterooms_tons=320.0,
    standard_staterooms_cost_mcr=40.0,
    high_staterooms_tons=1_152.0,
    high_staterooms_cost_mcr=153.6,
    luxury_staterooms_tons=80.0,
    luxury_staterooms_cost_mcr=12.0,
    common_area_tons=388.0,
    common_area_cost_mcr=38.8,
    swimming_pool_tons=60.0,
    swimming_pool_cost_mcr=1.2,
    theatres_tons=[100.0, 100.0, 100.0],
    theatres_costs_mcr=[10.0, 10.0, 10.0],
    wet_bar_cost=2_000.0,
    low_berths_total_tons=9.0,
    low_berths_total_cost_mcr=0.9,
    low_berths_total_power=2.0,
    crew=[
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
    ],
    crew_salaries_mcr=0.387,
    power_basic=1_000.0,
    total_power=2_005.0,
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
        drives=DriveSection(m_drive=MDrive1(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=2_010)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=8),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Computer10(),
            backup_hardware=Computer5(bis=True),
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
    assert liner.tl == _expected.tl
    assert liner.displacement == _expected.displacement

    assert liner.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert liner.hull_points == pytest.approx(_expected.hull_points)
    assert liner.hull.airlocks is not None
    assert len(liner.hull.airlocks) == _expected.airlocks_count
    assert all(airlock.tons == 0.0 for airlock in liner.hull.airlocks)

    assert liner.drives is not None
    assert liner.drives.m_drive is not None
    assert liner.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert liner.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert liner.drives.m_drive.power == pytest.approx(_expected.m_drive_power)

    assert liner.drives.j_drive is not None
    assert liner.drives.j_drive.tons == pytest.approx(_expected.j_drive_tons)
    assert liner.drives.j_drive.cost == pytest.approx(_expected.j_drive_cost_mcr * 1_000_000)
    assert liner.drives.j_drive.power == pytest.approx(_expected.j_drive_power)

    assert liner.power is not None
    assert liner.power.plant is not None
    assert liner.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert liner.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)
    assert liner.available_power == pytest.approx(_expected.available_power)

    assert liner.fuel is not None
    assert liner.fuel.jump_fuel is not None
    assert liner.fuel.jump_fuel.tons == pytest.approx(_expected.jump_fuel_tons)
    assert liner.fuel.operation_fuel is not None
    assert liner.fuel.operation_fuel.tons == pytest.approx(_expected.operation_fuel_tons)

    assert liner.command is not None
    assert liner.command.bridge is not None
    assert liner.command.bridge.tons == pytest.approx(_expected.bridge_tons)
    assert liner.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)

    assert liner.computer is not None
    assert liner.computer.hardware is not None
    assert liner.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)
    assert liner.computer.backup_hardware is not None
    assert liner.computer.backup_hardware.cost == pytest.approx(_expected.backup_computer_cost_mcr * 1_000_000)
    assert [(package.description, package.cost) for package in liner.computer.software_packages] == (
        _expected.software_packages
    )
    assert not any(
        note.message.startswith('Redundant ') for package in liner.computer.software_packages for note in package.notes
    )

    assert liner.sensors.primary.tons == pytest.approx(_expected.sensors_tons)
    assert liner.sensors.primary.cost == pytest.approx(_expected.sensors_cost_mcr * 1_000_000)

    assert liner.craft is not None
    docking_spaces = liner.craft._all_parts()
    assert [space.tons for space in docking_spaces] == pytest.approx(_expected.docking_spaces_tons)
    assert [space.cost for space in docking_spaces] == pytest.approx(
        [c * 1_000_000 for c in _expected.docking_spaces_costs_mcr]
    )

    assert liner.systems is not None
    assert liner.systems.medical_bays[0] is not None
    assert liner.systems.medical_bays[0].tons == pytest.approx(_expected.medical_bay_tons)
    assert liner.systems.medical_bays[0].cost == pytest.approx(_expected.medical_bay_cost_mcr * 1_000_000)
    assert liner.systems.medical_bays[0].power == pytest.approx(_expected.medical_bay_power)
    assert liner.systems.commercial_zones[0] is not None
    assert liner.systems.commercial_zones[0].tons == pytest.approx(_expected.commercial_zone_tons)
    assert liner.systems.commercial_zones[0].cost == pytest.approx(_expected.commercial_zone_cost_mcr * 1_000_000)
    assert liner.systems.commercial_zones[0].power == pytest.approx(_expected.commercial_zone_power)

    assert liner.habitation is not None
    assert liner.habitation.staterooms is not None
    standard_rooms = [room for room in liner.habitation.staterooms if type(room) is Stateroom]
    high_rooms = [room for room in liner.habitation.staterooms if isinstance(room, HighStateroom)]
    luxury_rooms = [room for room in liner.habitation.staterooms if isinstance(room, LuxuryStateroom)]
    assert sum(room.tons for room in standard_rooms) == pytest.approx(_expected.standard_staterooms_tons)
    assert sum(room.cost for room in standard_rooms) == pytest.approx(
        _expected.standard_staterooms_cost_mcr * 1_000_000
    )
    assert sum(room.tons for room in high_rooms) == pytest.approx(_expected.high_staterooms_tons)
    assert sum(room.cost for room in high_rooms) == pytest.approx(_expected.high_staterooms_cost_mcr * 1_000_000)
    assert sum(room.tons for room in luxury_rooms) == pytest.approx(_expected.luxury_staterooms_tons)
    assert sum(room.cost for room in luxury_rooms) == pytest.approx(_expected.luxury_staterooms_cost_mcr * 1_000_000)
    assert liner.habitation.common_area is not None
    assert liner.habitation.common_area.tons == pytest.approx(_expected.common_area_tons)
    assert liner.habitation.common_area.cost == pytest.approx(_expected.common_area_cost_mcr * 1_000_000)
    assert liner.habitation.swimming_pool is not None
    assert liner.habitation.swimming_pool.tons == pytest.approx(_expected.swimming_pool_tons)
    assert liner.habitation.swimming_pool.cost == pytest.approx(_expected.swimming_pool_cost_mcr * 1_000_000)
    assert [theatre.tons for theatre in liner.habitation.theatres] == pytest.approx(_expected.theatres_tons)
    assert [theatre.cost for theatre in liner.habitation.theatres] == pytest.approx(
        [c * 1_000_000 for c in _expected.theatres_costs_mcr]
    )
    assert liner.habitation.wet_bar is not None
    assert liner.habitation.wet_bar.cost == pytest.approx(_expected.wet_bar_cost)
    assert liner.habitation.low_berths is not None
    assert sum(berth.tons for berth in liner.habitation.low_berths) == pytest.approx(_expected.low_berths_total_tons)
    assert sum(berth.cost for berth in liner.habitation.low_berths) == pytest.approx(
        _expected.low_berths_total_cost_mcr * 1_000_000
    )
    assert sum(berth.power for berth in liner.habitation.low_berths) == pytest.approx(_expected.low_berths_total_power)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in liner.crew.grouped_roles] == (
        _expected.crew
    )
    assert liner.expenses.crew_salaries == pytest.approx(_expected.crew_salaries_mcr * 1_000_000)

    assert liner.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert liner.total_power_load == pytest.approx(_expected.total_power)
    assert not liner.notes.errors


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
