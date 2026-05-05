"""Reference ship case based on refs/SmallScoutBase.txt.

Purpose:
- provide a large scout-base / space-station reference slice
- exercise light dispersed hulls, thrust-0 manoeuvre drives, full hangars,
  large explicit station crews, and large-scale habitation

Source handling for this test case:
- supported: light dispersed-structure hull, thrust-0 manoeuvre drive, TL12
  fusion plant, operation fuel, fuel processors, small bridge, computer and
  included software, quad turrets with beam lasers and missile racks, full
  hangars, explicit airlocks, armoury, briefing room, physical library,
  medical bay, mining drones, probe drones, repair drones, training facility,
  standard staterooms, brig, common area, advanced entertainment system,
  swimming pool, theatre, and explicit crew
- source mismatch retained:
  - the sheet lists `HULL: 3,200`
  - Ceres follows the current light-hull and dispersed-structure modifiers,
    which yield 3,240 hull points
- still excluded from the modeled reference case:
  - improved solar panels
  - additional fuel tankage
  - the advanced / long-range / mail-array sensor suite
  - chart room
  - grappling arm
  - meteoric assault / support systems
  - vault
  - workshops x10
  - gaming space
- deliberate interpretation:
  - this Ceres variant models additional carried craft beyond the sheet:
    `Ship's Boat x2` in full hangars and `G/Carrier x3` in internal docking
    spaces, so the explicit pilot count is raised accordingly
  - this Ceres variant also raises source `Gunners x4` to `Gunners x5` so the
    explicit crew covers all five modeled turrets
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import NoteList
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer20, ComputerSection
from ceres.make.ship.crafts import CraftSection, FullHangar, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import (
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
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive0, PowerSection
from ceres.make.ship.habitation import AdvancedEntertainmentSystem, Brig, HabitationSection, Stateroom
from ceres.make.ship.sensors import BasicSensors, SensorsSection
from ceres.make.ship.storage import FuelProcessor, FuelSection, OperationFuel
from ceres.make.ship.systems import (
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
from ceres.make.ship.weapons import BeamLaser, MissileRack, QuadTurret, WeaponsSection


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
                *[Engineer()] * 6,
                *[GeneralCrew()] * 250,
                *[Maintenance()] * 9,
                *[Gunner()] * 5,
                *[Administrator()] * 4,
                SensorOperator(),
                *[Pilot()] * 13,
                *[Medic()] * 2,
                *[Officer()] * 14,
            ]
        ),
        hull=hull.Hull(configuration=light_dispersed, airlocks=[Airlock() for _ in range(24)]),
        drives=DriveSection(m_drive=MDrive0()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=2_500)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=5),
        ),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer20()),
        sensors=SensorsSection(primary=BasicSensors()),
        weapons=WeaponsSection(
            turrets=[
                *[
                    QuadTurret(
                        weapons=[BeamLaser()] * 4,
                    )
                ]
                * 4,
                QuadTurret(
                    weapons=[MissileRack()] * 4,
                ),
            ]
        ),
        craft=CraftSection(
            internal_housing=[
                *[FullHangar(craft=SpaceCraft.from_catalog('Passenger Shuttle'))] * 10,
                *[FullHangar(craft=SpaceCraft.from_catalog("Ship's Boat"))] * 2,
                *[InternalDockingSpace(craft=Vehicle.from_catalog('G/Carrier'))] * 3,
            ]
        ),
        systems=SystemsSection(
            internal_systems=[
                Armoury(),
                BriefingRoom(),
                LibraryFacility(),
                MedicalBay(),
                MedicalBay(),
                TrainingFacility(trainees=4),
            ],
            drones=[MiningDrones(count=10), ProbeDrones(count=100), RepairDrones()],
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
    assert len(base.hull.airlocks) == 24
    assert all(airlock.tons == 0.0 for airlock in base.hull.airlocks)
    assert 'Installed airlocks below minimum recommendation: 24 < 20' not in NoteList(base.notes).warnings

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

    assert base.weapons is not None
    assert len(base.weapons.turrets) == 5
    assert sum(turret.tons for turret in base.weapons.turrets) == pytest.approx(5.0)
    assert sum(turret.cost for turret in base.weapons.turrets) == pytest.approx(21_000_000.0)
    assert sum(turret.power for turret in base.weapons.turrets) == pytest.approx(74.0)

    assert base.craft is not None
    assert len(base.craft.internal_housing) == 15
    assert sum(housing.tons for housing in base.craft.internal_housing) == pytest.approx(2_071.0)
    assert sum(housing.cost for housing in base.craft.internal_housing) == pytest.approx(416_750_000.0)
    assert sum(housing.craft.cost for housing in base.craft.internal_housing) == pytest.approx(192_950_000.0)

    assert base.systems is not None
    assert len(base.systems.armouries) == 1
    assert base.systems.armouries[0].tons == pytest.approx(1.0)
    assert base.systems.armouries[0].cost == pytest.approx(250_000.0)
    assert base.systems.briefing_room is not None
    assert base.systems.briefing_room.tons == pytest.approx(4.0)
    assert base.systems.briefing_room.cost == pytest.approx(500_000.0)
    assert base.systems.library is not None
    assert base.systems.library.tons == pytest.approx(4.0)
    assert base.systems.library.cost == pytest.approx(4_000_000.0)
    assert len(base.systems.medical_bays) == 2
    assert sum(bay.tons for bay in base.systems.medical_bays) == pytest.approx(8.0)
    assert sum(bay.cost for bay in base.systems.medical_bays) == pytest.approx(4_000_000.0)
    assert len(base.systems.drones) == 3
    assert base.systems.drones[0].tons == pytest.approx(20.0)
    assert base.systems.drones[0].cost == pytest.approx(2_000_000.0)
    assert base.systems.drones[1].tons == pytest.approx(20.0)
    assert base.systems.drones[1].cost == pytest.approx(10_000_000.0)
    assert base.systems.drones[2].tons == pytest.approx(100.0)
    assert base.systems.drones[2].cost == pytest.approx(20_000_000.0)
    assert base.systems.training_facility is not None
    assert base.systems.training_facility.tons == pytest.approx(8.0)
    assert base.systems.training_facility.cost == pytest.approx(1_600_000.0)

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
    assert base.weapon_power_load == pytest.approx(74.0)
    assert base.fuel_power_load == pytest.approx(5.0)
    assert base.total_power_load == pytest.approx(2_331.0)

    assert [
        ('ENGINEER', 6),
        ('GENERAL CREW', 250),
        ('MAINTENANCE', 9),
        ('GUNNER', 5),
        ('ADMINISTRATOR', 4),
        ('SENSOR OPERATOR', 1),
        ('PILOT', 13),
        ('MEDIC', 2),
        ('OFFICER', 14),
    ] == [(role.role, quantity) for role, quantity in base.crew.grouped_roles]

    notes = NoteList(base.crew.notes)
    assert 'ENGINEER below recommended count: 5 < 6' not in notes.warnings
    assert 'GUNNER below recommended count: 4 < 5' not in notes.warnings
    assert 'MEDIC above recommended count: 2 > 0' not in notes.infos
    assert 'PILOT below recommended count: 12 < 13' not in notes.warnings


def test_small_scout_base_spec_structure():
    base = build_small_scout_base()
    spec = base.build_spec()

    assert spec.row('Light Dispersed Structure Hull').section == 'Hull'
    assert spec.row('Airlock (2 tons)', section='Hull').quantity == 24
    assert spec.row('M-Drive 0').section == 'Propulsion'
    assert spec.row('12 weeks of operation').section == 'Fuel'
    assert spec.row('Fuel Processor (100 tons/day)').section == 'Fuel'
    assert spec.row('Smaller Bridge').section == 'Command'
    assert spec.row('Computer/20').section == 'Computer'
    beam_turret_rows = spec.rows_matching('Quad Turret')
    assert len(beam_turret_rows) == 2
    assert beam_turret_rows[0].quantity == 4
    assert beam_turret_rows[0].cost == pytest.approx(16_000_000.0)
    assert NoteList(beam_turret_rows[0].notes).contents == ['Beam Laser × 4']
    assert beam_turret_rows[1].quantity is None
    assert beam_turret_rows[1].cost == pytest.approx(5_000_000.0)
    assert NoteList(beam_turret_rows[1].notes).contents == ['Missile Rack × 4']
    assert len(spec.rows_matching('Full Hangar: Passenger Shuttle')) == 10
    assert len(spec.rows_matching('Passenger Shuttle')) == 10
    assert len(spec.rows_matching("Full Hangar: Ship's Boat")) == 2
    assert len(spec.rows_matching("Ship's Boat")) == 2
    assert len(spec.rows_matching('Internal Docking Space: G/Carrier')) == 3
    assert len(spec.rows_matching('G/Carrier')) == 3
    assert spec.row('Armoury').section == 'Systems'
    assert spec.row('Briefing Room').section == 'Systems'
    assert spec.row('Library', section='Systems').section == 'Systems'
    assert spec.row('Medical Bay').section == 'Systems'
    assert spec.row('Medical Bay').quantity == 2
    assert spec.row('Mining Drones').quantity == 10
    assert spec.row('Probe Drones').quantity == 100
    assert spec.row('Repair Drones').section == 'Systems'
    assert spec.row('Training Facility: 4-person capacity').section == 'Systems'
    assert spec.row('Staterooms').quantity == 1_250
    assert spec.row('Brig').section == 'Habitation'
    assert spec.row('Common Area').section == 'Habitation'
    assert spec.row('Advanced Entertainment System').section == 'Habitation'
    assert spec.row('Swimming Pool').section == 'Habitation'
    assert spec.row('Theatre').section == 'Habitation'
