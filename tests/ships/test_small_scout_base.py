"""Reference ship case based on refs/SmallScoutBase.txt.

Purpose:
- provide a large scout-base / space-station reference slice
- exercise light dispersed hulls, thrust-0 manoeuvre drives, full hangars,
  large explicit station crews, and large-scale habitation

Source handling for this test case:
- supported: light dispersed-structure hull, thrust-0 manoeuvre drive, TL12
  fusion plant, operation fuel, fuel processors, small bridge, computer and
  included software, full hangars, explicit airlocks, armoury, briefing room,
  physical library, medical bay, mining drones, probe drones, repair drones,
  training facility, standard staterooms, brig, common area, advanced
  entertainment system, swimming pool, theatre, and explicit crew
- source mismatch retained:
  - the sheet lists `HULL: 3,200`
  - Tycho follows the current light-hull and dispersed-structure modifiers,
    which yield 3,240 hull points
  - the sheet lists `12 Weeks of Operation` as 51 tons
  - Tycho follows the normal operation-fuel rule for this plant, which yields
    50 tons
- still excluded from the modeled reference case:
  - improved solar panels
  - additional fuel tankage
  - the advanced / long-range / mail-array sensor suite
  - all weapon rows
  - chart room
  - grappling arm
  - meteoric assault / support systems
  - vault
  - workshops x10
  - gaming space
- deliberate interpretation:
  - source crew is carried over explicitly; `Passenger Shuttle Pilots x10` are
    represented as ten additional `PILOT` roles tied to the ten modeled
    passenger shuttles
"""

import pytest

from tycho import hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection
from tycho.crafts import CraftSection, FreeGenericCraft, FullHangar, PassengerShuttle
from tycho.crew import (
    Administrator,
    Engineer,
    GeneralCrew,
    Gunner,
    Maintenance,
    Medic,
    Officer,
    Pilot,
    SensorOperator,
    ShipCrew,
)
from tycho.drives import DriveSection, FusionPlantTL12, MDrive, PowerSection
from tycho.habitation import AdvancedEntertainmentSystem, Brig, HabitationSection, Stateroom
from tycho.sensors import BasicSensors, SensorsSection
from tycho.storage import FuelProcessor, FuelSection, OperationFuel
from tycho.systems import (
    Airlock,
    Armoury,
    BriefingRoom,
    CommonArea,
    LibraryFacility,
    MedicalBay,
    MiningDrones,
    ProbeDrones,
    RepairDrones,
    SwimmingPool,
    SystemsSection,
    Theatre,
    TrainingFacility,
)


def build_small_scout_base() -> ship.Ship:
    light_dispersed = hull.dispersed_structure.model_copy(
        update={'light': True, 'description': 'Light Dispersed Structure Hull'}
    )
    return ship.Ship(
        ship_class='Small Scout Base',
        tl=12,
        displacement=10_000,
        design_type=ship.ShipDesignType.STANDARD,
        passenger_vector={},
        crew=ShipCrew(
            roles=[
                *[Engineer()] * 5,
                *[GeneralCrew()] * 250,
                *[Maintenance()] * 9,
                *[Gunner()] * 4,
                *[Administrator()] * 4,
                SensorOperator(),
                *[Pilot()] * 10,
                *[Medic()] * 2,
                *[Officer()] * 14,
            ]
        ),
        hull=hull.Hull(configuration=light_dispersed, airlocks=[Airlock() for _ in range(10)]),
        drives=DriveSection(m_drive=MDrive(0)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=2_500)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=5),
        ),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer(20)),
        sensors=SensorsSection(primary=BasicSensors()),
        craft=CraftSection(
            full_hangars=[
                *[FullHangar(craft=PassengerShuttle())] * 10,
                FullHangar(craft=FreeGenericCraft(docking_space=95)),
            ]
        ),
        systems=SystemsSection(
            armoury=Armoury(),
            briefing_room=BriefingRoom(),
            library=LibraryFacility(),
            medical_bay=MedicalBay(),
            mining_drones=MiningDrones(count=10),
            probe_drones=ProbeDrones(count=100),
            repair_drones=RepairDrones(),
            training_facility=TrainingFacility(trainees=1),
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 1_250,
            brig=Brig(),
            common_area=CommonArea(tons=1_250.0),
            entertainment=AdvancedEntertainmentSystem(cost=10_000),
            swimming_pool=SwimmingPool(tons=4.0),
            theatres=[Theatre(tons=8.0)],
        ),
    )


def test_small_scout_base_matches_supported_slice():
    base = build_small_scout_base()

    assert base.hull_cost == pytest.approx(187_500_000.0)
    assert base.hull_points == pytest.approx(3_240.0)
    assert base.hull.airlocks is not None
    assert len(base.hull.airlocks) == 10
    assert all(airlock.tons == 0.0 for airlock in base.hull.airlocks)
    assert ('warning', 'Installed airlocks below minimum recommendation: 10 < 20') in [
        (note.category.value, note.message) for note in base.notes
    ]

    assert base.drives is not None
    assert base.drives.m_drive is not None
    assert base.drives.m_drive.tons == pytest.approx(50.0)
    assert base.drives.m_drive.cost == pytest.approx(100_000_000.0)
    assert base.drives.m_drive.power == pytest.approx(250.0)

    assert base.power is not None
    assert base.power.fusion_plant is not None
    assert base.power.fusion_plant.tons == pytest.approx(166.6666666667)
    assert base.power.fusion_plant.cost == pytest.approx(166_666_666.6667)
    assert base.available_power == pytest.approx(2_500.0)

    assert base.fuel is not None
    assert base.fuel.operation_fuel is not None
    assert base.fuel.operation_fuel.tons == pytest.approx(50.0)
    assert base.fuel.fuel_processor is not None
    assert base.fuel.fuel_processor.tons == pytest.approx(5.0)
    assert base.fuel.fuel_processor.cost == pytest.approx(250_000.0)
    assert base.fuel.fuel_processor.power == pytest.approx(5.0)

    assert base.command is not None
    assert base.command.bridge is not None
    assert base.command.bridge.tons == pytest.approx(40.0)
    assert base.command.bridge.cost == pytest.approx(25_000_000.0)

    assert base.computer is not None
    assert base.computer.hardware is not None
    assert base.computer.hardware.cost == pytest.approx(5_000_000.0)
    assert [(package.description, package.cost) for package in base.computer.software_packages.values()] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
    ]

    assert base.craft is not None
    assert len(base.craft.full_hangars) == 11
    assert sum(hangar.tons for hangar in base.craft.full_hangars) == pytest.approx(2_090.0)
    assert sum(hangar.cost for hangar in base.craft.full_hangars) == pytest.approx(418_000_000.0)
    assert sum(hangar.craft.cost for hangar in base.craft.full_hangars) == pytest.approx(143_050_000.0)

    assert base.systems is not None
    assert base.systems.armoury is not None
    assert base.systems.armoury.tons == pytest.approx(1.0)
    assert base.systems.armoury.cost == pytest.approx(250_000.0)
    assert base.systems.briefing_room is not None
    assert base.systems.briefing_room.tons == pytest.approx(4.0)
    assert base.systems.briefing_room.cost == pytest.approx(500_000.0)
    assert base.systems.library is not None
    assert base.systems.library.tons == pytest.approx(4.0)
    assert base.systems.library.cost == pytest.approx(4_000_000.0)
    assert base.systems.medical_bay is not None
    assert base.systems.medical_bay.tons == pytest.approx(4.0)
    assert base.systems.medical_bay.cost == pytest.approx(2_000_000.0)
    assert base.systems.mining_drones is not None
    assert base.systems.mining_drones.tons == pytest.approx(20.0)
    assert base.systems.mining_drones.cost == pytest.approx(2_000_000.0)
    assert base.systems.probe_drones is not None
    assert base.systems.probe_drones.tons == pytest.approx(20.0)
    assert base.systems.probe_drones.cost == pytest.approx(10_000_000.0)
    assert base.systems.repair_drones is not None
    assert base.systems.repair_drones.tons == pytest.approx(100.0)
    assert base.systems.repair_drones.cost == pytest.approx(20_000_000.0)
    assert base.systems.training_facility is not None
    assert base.systems.training_facility.tons == pytest.approx(2.0)
    assert base.systems.training_facility.cost == pytest.approx(400_000.0)

    assert base.habitation is not None
    assert len(base.habitation.staterooms) == 1_250
    assert sum(room.tons for room in base.habitation.staterooms) == pytest.approx(5_000.0)
    assert sum(room.cost for room in base.habitation.staterooms) == pytest.approx(625_000_000.0)
    assert base.habitation.brig is not None
    assert base.habitation.brig.tons == pytest.approx(4.0)
    assert base.habitation.brig.cost == pytest.approx(250_000.0)
    assert base.habitation.common_area is not None
    assert base.habitation.common_area.tons == pytest.approx(1_250.0)
    assert base.habitation.common_area.cost == pytest.approx(125_000_000.0)
    assert base.habitation.entertainment is not None
    assert base.habitation.entertainment.cost == pytest.approx(10_000.0)
    assert base.habitation.swimming_pool is not None
    assert base.habitation.swimming_pool.tons == pytest.approx(4.0)
    assert base.habitation.swimming_pool.cost == pytest.approx(80_000.0)
    assert len(base.habitation.theatres) == 1
    assert base.habitation.theatres[0].tons == pytest.approx(8.0)
    assert base.habitation.theatres[0].cost == pytest.approx(800_000.0)

    assert base.basic_hull_power_load == pytest.approx(2_000.0)
    assert base.maneuver_power_load == pytest.approx(250.0)
    assert base.sensor_power_load == pytest.approx(0.0)
    assert base.fuel_power_load == pytest.approx(5.0)
    assert base.total_power_load == pytest.approx(2_256.0)

    assert [
        ('ENGINEER', 5),
        ('GENERAL CREW', 250),
        ('MAINTENANCE', 9),
        ('GUNNER', 4),
        ('ADMINISTRATOR', 4),
        ('SENSOR OPERATOR', 1),
        ('PILOT', 10),
        ('MEDIC', 2),
        ('OFFICER', 14),
    ] == [
        (role.role, quantity) for role, quantity in base.crew.grouped_roles
    ]


def test_small_scout_base_spec_structure():
    base = build_small_scout_base()
    spec = base.build_spec()

    assert spec.row('Light Dispersed Structure Hull').section == 'Hull'
    assert spec.row('Airlock (2 tons)', section='Hull').quantity == 10
    assert spec.row('M-Drive 0').section == 'Propulsion'
    assert spec.row('12 weeks of operation').section == 'Fuel'
    assert spec.row('Fuel Processor (100 tons/day)').section == 'Fuel'
    assert spec.row('Smaller Bridge').section == 'Command'
    assert spec.row('Computer/20').section == 'Computer'
    assert len(spec.rows_matching('Full Hangar: Passenger Shuttle')) == 10
    assert len(spec.rows_matching('Full Hangar (95 tons)')) == 1
    assert len(spec.rows_matching('Passenger Shuttle')) == 10
    assert spec.row('Armoury').section == 'Systems'
    assert spec.row('Briefing Room').section == 'Systems'
    assert spec.row('Library', section='Systems').section == 'Systems'
    assert spec.row('Medical Bay').section == 'Systems'
    assert spec.row('Mining Drones').quantity == 10
    assert spec.row('Probe Drones').quantity == 100
    assert spec.row('Repair Drones').section == 'Systems'
    assert spec.row('Training Facility: 1-person capacity').section == 'Systems'
    assert spec.row('Staterooms').quantity == 1_250
    assert spec.row('Brig').section == 'Habitation'
    assert spec.row('Common Area').section == 'Habitation'
    assert spec.row('Advanced Entertainment System').section == 'Habitation'
    assert spec.row('Swimming Pool').section == 'Habitation'
    assert spec.row('Theatre').section == 'Habitation'
