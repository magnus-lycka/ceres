"""Reference ship case based on refs/BeagleLaboratoryShip.txt.

Purpose:
- provide a laboratory-ship reference case that extends the lab-station cases
  with jump drive, weapons, biosphere, hot tubs, and mixed internal/external
  carried-craft fittings

Source handling for this test case:
- supported: hull, drives, power plant, jump fuel, operation fuel, fuel
  processor, bridge, computer, included software, jump control, improved
  sensors, sensor station, beam-laser and missile-rack/sandcaster turrets,
  missile and sandcaster ammunition storage, docking clamps, docking space,
  air/raft, advanced probe drones, biosphere, laboratories, physical library,
  medical bay, workshop, standard staterooms, common area, hot tubs, wet bar,
  low berths, cargo airlock, fuel/cargo container, and explicit crew
- supported: the sheet's `J-2, 8 Weeks of Operation` fuel total now matches the
  core-rule calculation of 80 tons jump fuel plus 4 tons operation fuel
- still excluded from the modeled reference case:
  - software packages `Mentor/1`, `Planetology/1`, and `Research Assist/1`
  - carried craft rows for `Pinnace` and `ATV`
  - `Ship's Mechanic`
- deliberate interpretation:
  - source crew is carried over explicitly; `Pinnace Pilot` is treated as an
    additional `Pilot`, and `Sensop` as `SENSOR OPERATOR`
"""

import pytest

from tycho import hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection, JumpControl
from tycho.crafts import AirRaft, CraftSection, DockingClamp, InternalDockingSpace
from tycho.crew import (
    Astrogator,
    Engineer,
    Gunner,
    Medic,
    Officer,
    Pilot,
    SensorOperator,
    ShipCrew,
    Steward,
)
from tycho.drives import DriveSection, FusionPlantTL12, JDrive, MDrive, PowerSection
from tycho.habitation import HabitationSection, HotTub, LowBerth, Stateroom
from tycho.sensors import ImprovedSensors, SensorStations, SensorsSection
from tycho.storage import CargoAirlock, CargoSection, FuelCargoContainer, FuelProcessor, FuelSection, JumpFuel, OperationFuel
from tycho.systems import AdvancedProbeDrones, Biosphere, CommonArea, Laboratory, LibraryFacility, MedicalBay, SystemsSection, WetBar, Workshop
from tycho.weapons import MissileStorage, MountWeapon, SandcasterCanisterStorage, Turret, WeaponsSection


def build_beagle_laboratory_ship() -> ship.Ship:
    return ship.Ship(
        ship_class='Beagle-class',
        ship_type='Laboratory Ship',
        tl=12,
        displacement=400,
        design_type=ship.ShipDesignType.STANDARD,
        passenger_vector={},
        hull=hull.Hull(configuration=hull.dispersed_structure),
        drives=DriveSection(m_drive=MDrive(2), j_drive=JDrive(2)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=180)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=8),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge(small=True, holographic=True)),
        computer=ComputerSection(hardware=Computer(10), software=[JumpControl(2)]),
        sensors=SensorsSection(primary=ImprovedSensors(), sensor_stations=SensorStations(count=1)),
        weapons=WeaponsSection(
            turrets=[
                Turret(size='double', weapons=[MountWeapon(weapon='beam_laser'), MountWeapon(weapon='beam_laser')]),
                Turret(size='double', weapons=[MountWeapon(weapon='missile_rack'), MountWeapon(weapon='sandcaster')]),
            ],
            missile_storage=MissileStorage(count=12),
            sandcaster_canister_storage=SandcasterCanisterStorage(count=20),
        ),
        craft=CraftSection(
            docking_clamps=[DockingClamp(kind='II'), DockingClamp(kind='I')],
            docking_space=InternalDockingSpace(craft=AirRaft()),
        ),
        systems=SystemsSection(
            probe_drones=AdvancedProbeDrones(count=10),
            biosphere=Biosphere(tons=2.0),
            laboratories=[Laboratory()] * 10,
            library=LibraryFacility(),
            medical_bay=MedicalBay(),
            workshop=Workshop(),
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            common_area=CommonArea(tons=10.0),
            hot_tubs=[HotTub(users=1)] * 4,
            wet_bar=WetBar(),
            low_berths=[LowBerth()] * 6,
        ),
        cargo=CargoSection(
            cargo_airlocks=[CargoAirlock()],
            fuel_cargo_containers=[FuelCargoContainer(capacity=80)],
        ),
        crew=ShipCrew(
            roles=[
                *[Pilot()] * 2,
                Astrogator(),
                Engineer(),
                *[Gunner()] * 2,
                Steward(),
                SensorOperator(),
                Medic(),
                *[Officer()] * 10,
            ]
        ),
    )


def test_beagle_laboratory_ship_matches_supported_slice():
    ship_ = build_beagle_laboratory_ship()

    assert ship_.hull_cost == pytest.approx(10_000_000.0)
    assert ship_.hull_points == pytest.approx(144.0)

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
    assert ship_.power.fusion_plant is not None
    assert ship_.power.fusion_plant.tons == pytest.approx(12.0)
    assert ship_.power.fusion_plant.cost == pytest.approx(12_000_000.0)
    assert ship_.available_power == pytest.approx(180.0)

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
    assert [(package.description, package.cost) for package in ship_.computer.software_packages.values()] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000.0),
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
    assert ship_.weapons.missile_storage is not None
    assert ship_.weapons.missile_storage.tons == pytest.approx(1.0)
    assert ship_.weapons.sandcaster_canister_storage is not None
    assert ship_.weapons.sandcaster_canister_storage.tons == pytest.approx(1.0)

    assert ship_.craft is not None
    assert [part.build_item() for part in ship_.craft._all_parts()] == [
        'Docking Clamp, Type II',
        'Docking Clamp, Type I',
        'Internal Docking Space: Air/Raft',
    ]
    assert [part.tons for part in ship_.craft._all_parts()] == pytest.approx([5.0, 1.0, 5.0])
    assert [part.cost for part in ship_.craft._all_parts()] == pytest.approx([1_000_000.0, 500_000.0, 1_250_000.0])

    assert ship_.systems is not None
    assert ship_.systems.probe_drones is not None
    assert ship_.systems.probe_drones.tons == pytest.approx(2.0)
    assert ship_.systems.probe_drones.cost == pytest.approx(1_600_000.0)
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
    assert ship_.cargo.cargo_airlocks[0].tons == pytest.approx(2.0)
    assert ship_.cargo.cargo_airlocks[0].cost == pytest.approx(200_000.0)
    assert len(ship_.cargo.fuel_cargo_containers) == 1
    assert ship_.cargo.fuel_cargo_containers[0].tons == pytest.approx(84.0)
    assert ship_.cargo.fuel_cargo_containers[0].cost == pytest.approx(400_000.0)

    assert [(role.role, quantity) for role, quantity in ship_.crew.grouped_roles] == [
        ('PILOT', 2),
        ('ASTROGATOR', 1),
        ('ENGINEER', 1),
        ('GUNNER', 2),
        ('STEWARD', 1),
        ('SENSOR OPERATOR', 1),
        ('MEDIC', 1),
        ('OFFICER', 10),
    ]


def test_beagle_laboratory_ship_spec_structure():
    ship_ = build_beagle_laboratory_ship()
    spec = ship_.build_spec()

    assert spec.row('Dispersed Structure Hull').section == 'Hull'
    assert spec.row('M-Drive 2').section == 'Propulsion'
    assert spec.row('Jump 2').section == 'Jump'
    assert spec.row('Fusion (TL 12)').section == 'Power'
    assert spec.row('J-2, 8 weeks of operation').section == 'Fuel'
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
    assert spec.row('Docking Clamp, Type I').section == 'Craft'
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
    assert spec.row('Cargo Airlock (2 tons)').section == 'Cargo'
    assert spec.row('Fuel/Cargo Container (80 tons)').section == 'Cargo'
