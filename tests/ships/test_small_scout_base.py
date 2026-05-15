"""Reference ship case based on refs/tycho/SmallScoutBase.txt.

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

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
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

_expected = SimpleNamespace(
    hull_cost_mcr=187.5,  # 10000t Light Dispersed Structure
    hull_points=3_200.0,  # ref sheet; Ceres gives 3240 per light+dispersed modifiers
    airlocks_count=24,  # Ceres variant adds extra airlocks; ref shows x10 (20 tons)
    m_drive_tons=50.0,
    m_drive_cost_mcr=100.0,
    m_drive_power=250.0,
    plant_tons=166.6666666667,
    plant_cost_mcr=166.666666667,
    available_power=2_500.0,
    operation_fuel_tons=50.0,  # ref shows 51 tons (includes 1t from improved solar panel fuel?)
    fuel_processor_tons=5.0,
    fuel_processor_cost_mcr=0.25,
    fuel_processor_power=5.0,
    bridge_tons=40.0,
    bridge_cost_mcr=25.0,
    computer_cost_mcr=5.0,
    software_packages=[('Library', 0.0), ('Manoeuvre/0', 0.0), ('Intellect', 0.0)],
    turrets_total_tons=5.0,
    turrets_total_cost_mcr=21.0,
    turrets_total_power=74.0,
    craft_count=15,  # Ceres variant: 10 Passenger Shuttle + 2 Ship's Boat + 3 G/Carrier
    craft_total_tons=2_071.0,
    craft_total_housing_cost_mcr=416.75,
    craft_total_carried_cost_mcr=192.95,
    armoury_tons=1.0,
    armoury_cost_mcr=0.25,
    briefing_room_tons=4.0,
    briefing_room_cost_mcr=0.5,
    library_tons=4.0,
    library_cost_mcr=4.0,
    medical_bay_count=2,
    medical_bays_total_tons=8.0,
    medical_bays_total_cost_mcr=4.0,
    drone_mining_tons=20.0,
    drone_mining_cost_mcr=2.0,
    drone_probe_tons=20.0,
    drone_probe_cost_mcr=10.0,
    drone_repair_tons=100.0,
    drone_repair_cost_mcr=20.0,
    training_facility_tons=8.0,
    training_facility_cost_mcr=1.6,
    staterooms_count=1_250,
    staterooms_total_tons=5_000.0,
    staterooms_total_cost_mcr=625.0,
    brig_tons=4.0,
    brig_cost_mcr=0.25,
    common_area_tons=1_250.0,
    common_area_cost_mcr=125.0,
    entertainment_cost=10_000.0,
    swimming_pool_tons=4.0,
    swimming_pool_cost_mcr=0.08,
    theatre_tons=8.0,
    theatre_cost_mcr=0.8,
    power_basic=2_000.0,
    power_maneuver=250.0,
    power_sensors=0.0,
    power_weapons=74.0,
    power_fuel=5.0,
    total_power=2_331.0,
    crew=[
        ('ENGINEER', 6),
        ('GENERAL CREW', 250),
        ('MAINTENANCE', 9),
        ('GUNNER', 5),  # ref shows 4; Ceres raises to 5 to cover all modeled turrets
        ('ADMINISTRATOR', 4),
        ('SENSOR OPERATOR', 1),
        ('PILOT', 13),  # ref shows Passenger Shuttle Pilots x10; Ceres adds 2 Ship's Boat + 1 extra
        ('MEDIC', 2),
        ('OFFICER', 14),
    ],
)
# Ceres light+dispersed modifier gives 3240, not 3200 as on the ref sheet
_expected.hull_points = 3_240.0


def build_small_scout_base() -> ship.Ship:
    light_dispersed = hull.dispersed_structure.model_copy(
        update={'light': True, 'description': 'Light Dispersed Structure Hull'}
    )
    return ship.Ship(
        ship_class='Small Scout Base',
        tl=12,
        displacement=10_000,
        design_type=ship.ShipDesignType.STANDARD,
        occupants=[],
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
        power=PowerSection(plant=FusionPlantTL12(output=2_500)),
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

    assert base.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert base.hull_points == pytest.approx(_expected.hull_points)
    assert base.hull.airlocks is not None
    assert len(base.hull.airlocks) == _expected.airlocks_count
    assert all(airlock.tons == 0.0 for airlock in base.hull.airlocks)
    assert 'Installed airlocks below minimum recommendation: 24 < 20' not in base.notes.warnings

    assert base.drives is not None
    assert base.drives.m_drive is not None
    assert base.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert base.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert base.drives.m_drive.power == pytest.approx(_expected.m_drive_power)

    assert base.power is not None
    assert base.power.plant is not None
    assert base.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert base.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)
    assert base.available_power == pytest.approx(_expected.available_power)

    assert base.fuel is not None
    assert base.fuel.operation_fuel is not None
    assert base.fuel.operation_fuel.tons == pytest.approx(_expected.operation_fuel_tons)
    assert base.fuel.fuel_processor is not None
    assert base.fuel.fuel_processor.tons == pytest.approx(_expected.fuel_processor_tons)
    assert base.fuel.fuel_processor.cost == pytest.approx(_expected.fuel_processor_cost_mcr * 1_000_000)
    assert base.fuel.fuel_processor.power == pytest.approx(_expected.fuel_processor_power)

    assert base.command is not None
    assert base.command.bridge is not None
    assert base.command.bridge.tons == pytest.approx(_expected.bridge_tons)
    assert base.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)

    assert base.computer is not None
    assert base.computer.hardware is not None
    assert base.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)
    assert [(package.description, package.cost) for package in base.computer.software_packages] == (
        _expected.software_packages
    )

    assert base.weapons is not None
    assert len(base.weapons.turrets) == 5
    assert sum(turret.tons for turret in base.weapons.turrets) == pytest.approx(_expected.turrets_total_tons)
    assert sum(turret.cost for turret in base.weapons.turrets) == pytest.approx(
        _expected.turrets_total_cost_mcr * 1_000_000
    )
    assert sum(turret.power for turret in base.weapons.turrets) == pytest.approx(_expected.turrets_total_power)

    assert base.craft is not None
    assert len(base.craft.internal_housing) == _expected.craft_count
    assert sum(housing.tons for housing in base.craft.internal_housing) == pytest.approx(_expected.craft_total_tons)
    assert sum(housing.cost for housing in base.craft.internal_housing) == pytest.approx(
        _expected.craft_total_housing_cost_mcr * 1_000_000
    )
    assert sum(housing.craft.cost for housing in base.craft.internal_housing) == pytest.approx(
        _expected.craft_total_carried_cost_mcr * 1_000_000
    )

    assert base.systems is not None
    assert len(base.systems.armouries) == 1
    assert base.systems.armouries[0].tons == pytest.approx(_expected.armoury_tons)
    assert base.systems.armouries[0].cost == pytest.approx(_expected.armoury_cost_mcr * 1_000_000)
    assert base.systems.briefing_room is not None
    assert base.systems.briefing_room.tons == pytest.approx(_expected.briefing_room_tons)
    assert base.systems.briefing_room.cost == pytest.approx(_expected.briefing_room_cost_mcr * 1_000_000)
    assert base.systems.library is not None
    assert base.systems.library.tons == pytest.approx(_expected.library_tons)
    assert base.systems.library.cost == pytest.approx(_expected.library_cost_mcr * 1_000_000)
    assert len(base.systems.medical_bays) == _expected.medical_bay_count
    assert sum(bay.tons for bay in base.systems.medical_bays) == pytest.approx(_expected.medical_bays_total_tons)
    assert sum(bay.cost for bay in base.systems.medical_bays) == pytest.approx(
        _expected.medical_bays_total_cost_mcr * 1_000_000
    )
    assert len(base.systems.drones) == 3
    assert base.systems.drones[0].tons == pytest.approx(_expected.drone_mining_tons)
    assert base.systems.drones[0].cost == pytest.approx(_expected.drone_mining_cost_mcr * 1_000_000)
    assert base.systems.drones[1].tons == pytest.approx(_expected.drone_probe_tons)
    assert base.systems.drones[1].cost == pytest.approx(_expected.drone_probe_cost_mcr * 1_000_000)
    assert base.systems.drones[2].tons == pytest.approx(_expected.drone_repair_tons)
    assert base.systems.drones[2].cost == pytest.approx(_expected.drone_repair_cost_mcr * 1_000_000)
    assert base.systems.training_facility is not None
    assert base.systems.training_facility.tons == pytest.approx(_expected.training_facility_tons)
    assert base.systems.training_facility.cost == pytest.approx(_expected.training_facility_cost_mcr * 1_000_000)

    assert base.habitation is not None
    assert len(base.habitation.staterooms) == _expected.staterooms_count
    assert sum(room.tons for room in base.habitation.staterooms) == pytest.approx(_expected.staterooms_total_tons)
    assert sum(room.cost for room in base.habitation.staterooms) == pytest.approx(
        _expected.staterooms_total_cost_mcr * 1_000_000
    )
    assert base.habitation.brig is not None
    assert base.habitation.brig.tons == pytest.approx(_expected.brig_tons)
    assert base.habitation.brig.cost == pytest.approx(_expected.brig_cost_mcr * 1_000_000)
    assert base.habitation.common_area is not None
    assert base.habitation.common_area.tons == pytest.approx(_expected.common_area_tons)
    assert base.habitation.common_area.cost == pytest.approx(_expected.common_area_cost_mcr * 1_000_000)
    assert base.habitation.entertainment is not None
    assert base.habitation.entertainment.cost == pytest.approx(_expected.entertainment_cost)
    assert base.habitation.swimming_pool is not None
    assert base.habitation.swimming_pool.tons == pytest.approx(_expected.swimming_pool_tons)
    assert base.habitation.swimming_pool.cost == pytest.approx(_expected.swimming_pool_cost_mcr * 1_000_000)
    assert len(base.habitation.theatres) == 1
    assert base.habitation.theatres[0].tons == pytest.approx(_expected.theatre_tons)
    assert base.habitation.theatres[0].cost == pytest.approx(_expected.theatre_cost_mcr * 1_000_000)

    assert base.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert base.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert base.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert base.weapon_power_load == pytest.approx(_expected.power_weapons)
    assert base.fuel_power_load == pytest.approx(_expected.power_fuel)
    assert base.total_power_load == pytest.approx(_expected.total_power)

    assert _expected.crew == [(role.role, quantity) for role, quantity in base.crew.grouped_roles]

    notes = base.crew.notes
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
    assert beam_turret_rows[0].notes.contents == ['Beam Laser × 4']
    assert beam_turret_rows[1].quantity is None
    assert beam_turret_rows[1].cost == pytest.approx(5_000_000.0)
    assert beam_turret_rows[1].notes.contents == ['Missile Rack × 4']
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
