"""Reference ship case based on refs/BeagleLaboratoryShip.txt.

Purpose:
- provide a laboratory-ship reference case that extends the lab-station cases
  with jump drive, weapons, biosphere, hot tubs, and mixed internal/external
  carried-craft fittings

Source handling for this test case:
- supported: hull, drives, power plant, jump fuel, operation fuel, fuel
  processor, bridge, computer, included software, jump control, improved
  sensors, sensor station, turrets, docking clamps, docking space,
  air/raft, advanced probe drones, biosphere, laboratories, physical library,
  medical bay, workshop, standard staterooms, common area, hot tubs, wet bar,
  low berths, cargo airlock, and fuel/cargo container
- crew is rules-derived (`ShipCrew()`) rather than copied from the source
- deliberate interpretation:
  - the clamp-borne `Pinnace` is treated as maintained and transported
    external displacement, so drive and jump-fuel sizing use `455t`
- still excluded from the modeled reference case:
  - software packages `Mentor/1` and `Research Assist/1` (`TCS-004`)
  - `Planetology/1` is modeled as `Expert(rating=3, skill='Space Science (Planetology)')`
"""

import pytest

from ceres.gear.software import Expert
from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer10, ComputerSection
from ceres.make.ship.crafts import CraftSection, DockingClamp, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive2, PowerSection
from ceres.make.ship.habitation import HabitationSection, HotTub, LowBerth, Stateroom
from ceres.make.ship.sensors import ImprovedSensors, SensorsSection, SensorStations
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import (
    CargoAirlock,
    CargoSection,
    FuelCargoContainer,
    FuelProcessor,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import (
    AdvancedProbeDrones,
    Airlock,
    Biosphere,
    CommonArea,
    Laboratory,
    LibraryFacility,
    MedicalBay,
    SystemsSection,
    WetBar,
    Workshop,
)
from ceres.make.ship.weapons import (
    BeamLaser,
    DoubleTurret,
    MissileRack,
    MissileStorage,
    Sandcaster,
    SandcasterCanisterStorage,
    WeaponsSection,
)


def build_beagle_laboratory_ship() -> ship.Ship:
    return ship.Ship(
        ship_class='Beagle-class',
        ship_type='Laboratory Ship',
        tl=15,
        displacement=360,
        design_type=ship.ShipDesignType.STANDARD,
        occupants=[],
        hull=hull.Hull(
            configuration=hull.dispersed_structure,
            airlocks=[Airlock() for _ in range(3)],
        ),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=180)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=8),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge(small=True, holographic=True)),
        computer=ComputerSection(
            hardware=Computer10(),
            software=[JumpControl(rating=2), Expert(rating=3, skill='Space Science (Planetology)')],
        ),
        sensors=SensorsSection(primary=ImprovedSensors(), sensor_stations=SensorStations(count=1)),
        weapons=WeaponsSection(
            turrets=[
                DoubleTurret(weapons=[BeamLaser(), BeamLaser()]),
                DoubleTurret(weapons=[MissileRack(), Sandcaster()]),
            ],
            missile_storage=MissileStorage(count=12),
            sandcaster_canister_storage=SandcasterCanisterStorage(count=20),
        ),
        craft=CraftSection(
            docking_clamps=[
                DockingClamp(craft=SpaceCraft.from_catalog('Pinnace'), transported=True, maintained=True),
                DockingClamp(craft=Vehicle.from_catalog('ATV'), transported=False, maintained=False),
            ],
            internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))],
        ),
        systems=SystemsSection(
            drones=[AdvancedProbeDrones(count=10)],
            internal_systems=[
                Biosphere(tons=2.0),
                *[Laboratory()] * 10,
                LibraryFacility(),
                MedicalBay(),
                Workshop(),
            ],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            common_area=CommonArea(tons=10.0),
            hot_tubs=[HotTub(users=1)] * 4,
            wet_bar=WetBar(),
            low_berths=[LowBerth()] * 6,
        ),
        cargo=CargoSection(
            cargo_airlocks=[CargoAirlock(size=4.0)],
            fuel_cargo_containers=[FuelCargoContainer(capacity=80)],
        ),
        crew=ShipCrew(),
    )


def test_beagle_laboratory_ship_matches_supported_slice():
    ship_ = build_beagle_laboratory_ship()

    assert ship_.hull_cost == pytest.approx(9_000_000.0)
    assert ship_.hull_points == pytest.approx(129.0)

    assert ship_.drives is not None
    assert ship_.drives.m_drive is not None
    assert ship_.drives.m_drive.tons == pytest.approx(8.0)
    assert ship_.drives.m_drive.cost == pytest.approx(16_000_000.0)
    assert ship_.drives.m_drive.power == pytest.approx(80.0)
    assert ship_.drives.j_drive is not None
    assert ship_.drives.j_drive.tons == pytest.approx(25.0)
    assert ship_.drives.j_drive.cost == pytest.approx(37_500_000.0)
    assert ship_.drives.j_drive.power == pytest.approx(80.0)

    assert ship_.power is not None
    assert ship_.power.plant is not None
    assert ship_.power.plant.tons == pytest.approx(12.0)
    assert ship_.power.plant.cost == pytest.approx(12_000_000.0)
    assert ship_.available_power == pytest.approx(180.0)
    assert ship_.total_power_load == pytest.approx(171.0)
    assert ship_.remaining_usable_tonnage() == pytest.approx(1.0)
    assert 'Capacity 12.00 less than max use' not in ship_.notes.warnings

    assert ship_.fuel is not None
    assert ship_.fuel.jump_fuel is not None
    assert ship_.fuel.jump_fuel.tons == pytest.approx(80.0)
    assert ship_.fuel.operation_fuel is not None
    assert ship_.fuel.operation_fuel.tons == pytest.approx(3.0)
    assert ship_.fuel.fuel_processor is not None
    assert ship_.fuel.fuel_processor.tons == pytest.approx(2.0)
    assert ship_.fuel.fuel_processor.cost == pytest.approx(100_000.0)

    assert ship_.command is not None
    assert ship_.command.bridge is not None
    assert ship_.command.bridge.tons == pytest.approx(10.0)
    assert ship_.command.bridge.cost == pytest.approx(1_250_000.0)

    assert ship_.computer is not None
    assert ship_.computer.hardware is not None
    assert ship_.computer.hardware.cost == pytest.approx(160_000.0)
    assert [(package.description, package.cost) for package in ship_.computer.software_packages] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000.0),
        ('Expert (Space Science (Planetology))/3', 20_000.0),
    ]

    assert ship_.sensors.primary.tons == pytest.approx(3.0)
    assert ship_.sensors.primary.cost == pytest.approx(4_300_000.0)
    assert ship_.sensors.primary.power == pytest.approx(3.0)
    assert ship_.sensors.sensor_stations is not None
    assert ship_.sensors.sensor_stations.tons == pytest.approx(1.0)
    assert ship_.sensors.sensor_stations.cost == pytest.approx(500_000.0)

    assert ship_.weapons is not None
    assert len(ship_.weapons.turrets) == 2
    assert ship_.weapons.turrets[0].cost == pytest.approx(1_500_000.0)
    assert ship_.weapons.turrets[1].cost == pytest.approx(1_500_000.0)
    assert ship_.weapons.turrets[0].power == pytest.approx(9.0)
    assert ship_.weapons.turrets[1].power == pytest.approx(1.0)
    assert ship_.weapons.missile_storage is not None
    assert ship_.weapons.missile_storage.tons == pytest.approx(1.0)
    assert ship_.weapons.missile_storage.cost == pytest.approx(0.0)
    assert ship_.weapons.sandcaster_canister_storage is not None
    assert ship_.weapons.sandcaster_canister_storage.tons == pytest.approx(1.0)
    assert ship_.weapons.sandcaster_canister_storage.cost == pytest.approx(0.0)

    assert ship_.craft is not None
    assert [part.build_item() for part in ship_.craft._all_parts()] == [
        'Docking Clamp, Type II',
        'Docking Clamp, Type I',
        'Internal Docking Space: Air/Raft',
    ]
    assert [part.tons for part in ship_.craft._all_parts()] == pytest.approx([5.0, 1.0, 5.0])
    assert [part.cost for part in ship_.craft._all_parts()] == pytest.approx([1_000_000.0, 500_000.0, 1_250_000.0])
    assert ship_.craft.docking_clamps[0].craft is not None
    assert ship_.craft.docking_clamps[0].craft.cost == pytest.approx(9_680_000.0)
    assert ship_.craft.docking_clamps[1].craft is not None
    assert ship_.craft.docking_clamps[1].craft.cost == pytest.approx(155_000.0)

    assert ship_.systems is not None
    assert len(ship_.systems.drones) == 1
    assert ship_.systems.drones[0].tons == pytest.approx(2.0)
    assert ship_.systems.drones[0].cost == pytest.approx(1_600_000.0)
    assert ship_.systems.biosphere is not None
    assert ship_.systems.biosphere.tons == pytest.approx(2.0)
    assert ship_.systems.biosphere.cost == pytest.approx(400_000.0)
    assert ship_.systems.biosphere.power == pytest.approx(2.0)
    assert len(ship_.systems.laboratories) == 10
    assert sum(lab.tons for lab in ship_.systems.laboratories) == pytest.approx(40.0)
    assert sum(lab.cost for lab in ship_.systems.laboratories) == pytest.approx(10_000_000.0)
    assert ship_.systems.library is not None
    assert ship_.systems.library.tons == pytest.approx(4.0)
    assert ship_.systems.library.cost == pytest.approx(4_000_000.0)
    assert ship_.systems.medical_bay is not None
    assert ship_.systems.medical_bay.tons == pytest.approx(4.0)
    assert ship_.systems.medical_bay.cost == pytest.approx(2_000_000.0)
    assert ship_.systems.workshop is not None
    assert ship_.systems.workshop.tons == pytest.approx(6.0)
    assert ship_.systems.workshop.cost == pytest.approx(900_000.0)

    assert ship_.habitation is not None
    assert sum(room.tons for room in ship_.habitation.staterooms) == pytest.approx(40.0)
    assert sum(room.cost for room in ship_.habitation.staterooms) == pytest.approx(5_000_000.0)
    assert ship_.habitation.common_area is not None
    assert ship_.habitation.common_area.tons == pytest.approx(10.0)
    assert ship_.habitation.common_area.cost == pytest.approx(1_000_000.0)
    assert len(ship_.habitation.hot_tubs) == 4
    assert sum(tub.tons for tub in ship_.habitation.hot_tubs) == pytest.approx(1.0)
    assert sum(tub.cost for tub in ship_.habitation.hot_tubs) == pytest.approx(12_000.0)
    assert ship_.habitation.wet_bar is not None
    assert ship_.habitation.wet_bar.cost == pytest.approx(2_000.0)
    assert sum(berth.tons for berth in ship_.habitation.low_berths) == pytest.approx(3.0)
    assert sum(berth.cost for berth in ship_.habitation.low_berths) == pytest.approx(300_000.0)
    assert sum(berth.power for berth in ship_.habitation.low_berths) == pytest.approx(1.0)

    assert ship_.cargo is not None
    assert len(ship_.cargo.cargo_airlocks) == 1
    assert ship_.cargo.cargo_airlocks[0].tons == pytest.approx(4.0)
    assert ship_.cargo.cargo_airlocks[0].cost == pytest.approx(400_000.0)
    assert len(ship_.cargo.fuel_cargo_containers) == 1
    assert ship_.cargo.fuel_cargo_containers[0].tons == pytest.approx(84.0)
    assert ship_.cargo.fuel_cargo_containers[0].cost == pytest.approx(400_000.0)

    assert [(role.role, quantity) for role, quantity in ship_.crew.grouped_roles] == [
        ('PILOT', 2),
        ('ASTROGATOR', 1),
        ('ENGINEER', 2),
        ('GUNNER', 2),
        ('SENSOR OPERATOR', 2),
        ('MEDIC', 1),
    ]
    assert ship_.crew.notes.warnings == []

    # Source total MCr 123.909 / purchase MCr 111.518 (Mentor/1 and Research Assist/1 excluded).
    # Remaining gap: source uses 400t hull (MCr 10 vs our MCr 9, also 4 vs 3 free airlocks),
    # includes Ship's Mechanic (MCr 0.05), and omits Expert software we include (MCr 0.02).
    assert ship_.production_cost == pytest.approx(122_879_000.0)
    assert ship_.sales_price_new == pytest.approx(110_591_100.0)


def test_beagle_laboratory_ship_spec_structure():
    ship_ = build_beagle_laboratory_ship()
    spec = ship_.build_spec()

    assert spec.row('Dispersed Structure Hull').section == 'Hull'
    assert spec.row('Airlock (2 tons)').quantity == 3
    assert spec.row('M-Drive 2 (400t)').section == 'Propulsion'
    assert spec.row('Jump 2 (400t)').section == 'Jump'
    assert spec.row('Fusion (TL 12), Power 180').section == 'Power'
    assert spec.row('J-2 (400t), 8 weeks of operation').tons == pytest.approx(83.0)
    assert spec.row('Fuel Processor (40 tons/day)').section == 'Fuel'
    assert spec.row('Smaller Holographic Controls').section == 'Command'
    assert spec.row('Computer/10').section == 'Computer'
    assert spec.row('Jump Control/2').section == 'Computer'
    assert spec.row('Improved Sensors').section == 'Sensors'
    assert spec.row('Sensor Station').section == 'Sensors'
    assert len(spec.rows_matching('Double Turret')) == 2
    assert spec.row('Missile Storage (12)').section == 'Weapons'
    assert spec.row('Sandcaster Canister Storage (20)').section == 'Weapons'
    assert spec.row('Docking Clamp, Type II').section == 'Craft'
    assert spec.row('Pinnace').section == 'Craft'
    assert spec.row('Docking Clamp, Type I').section == 'Craft'
    assert spec.row('ATV').section == 'Craft'
    assert spec.row('Internal Docking Space: Air/Raft').section == 'Craft'
    assert spec.row('Air/Raft').section == 'Craft'
    assert spec.row('Advanced Probe Drones').quantity == 10
    assert spec.row('Laboratory').quantity == 10
    assert spec.row('Biosphere').section == 'Systems'
    assert spec.row('Medical Bay').section == 'Systems'
    assert spec.row('Staterooms').quantity == 10
    assert spec.row('Hot Tub (1 User)').quantity == 4
    assert spec.row('Wet Bar').section == 'Habitation'
    assert spec.row('Low Berths').quantity == 6
    assert spec.row('Cargo Airlock (4 tons)').section == 'Cargo'
    assert spec.row('Fuel/Cargo Container (80 tons)').section == 'Cargo'
    assert spec.row('Cargo Space').tons == pytest.approx(1.0)


def test_beagle_expert_software_roundtrip():
    ship_ = build_beagle_laboratory_ship()
    loaded = ship.Ship.model_validate_json(ship_.model_dump_json())
    assert loaded.computer is not None
    packages = loaded.computer.software_packages
    expert = next((p for p in packages if isinstance(p, Expert)), None)
    assert expert is not None
    assert expert.rating == 3
    assert expert.skill == 'Space Science (Planetology)'
    assert expert.description == 'Expert (Space Science (Planetology))/3'
    assert expert.cost == pytest.approx(20_000.0)
