"""Reference ship case based on refs/BeagleLaboratoryShip.txt.

Purpose:
- provide a laboratory-ship reference case that extends the lab-station cases
  with jump drive, weapons, biosphere, hot tubs, and mixed internal/external
  carried-craft fittings

Source handling for this test case:
- supported: hull, drives, power plant, jump fuel, operation fuel, fuel
  processor, bridge, computer, included software, jump control, improved
  sensors, sensor station, beam-laser turrets, docking clamps, docking space,
  air/raft, advanced probe drones, biosphere, laboratories, physical library,
  medical bay, workshop, standard staterooms, common area, hot tubs, wet bar,
  low berths, cargo airlock, fuel/cargo container, and explicit crew
- deliberate interpretation:
  - the clamp-borne `Pinnace` is treated as maintained and transported
    external displacement, so drive and jump-fuel sizing use `455t`
- still excluded from the modeled reference case:
  - software packages `Mentor/1` and `Research Assist/1` (`TCS-004`)
  - `Planetology/1` is modeled as `Expert(rating=1, skill='Space Sciences (Planetology)')`
  - source crew is carried over explicitly; `Pinnace Pilot` is treated as an
    additional `Pilot`, and `Sensop` as `SENSOR OPERATOR`
  - `Ship's Mechanic` is treated as the `MAINTENANCE` crew role
"""

import pytest

from ceres.gear.software import Expert
from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import (
    Computer,
    ComputerSection,
)
from ceres.make.ship.crafts import CraftSection, DockingClamp, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import (
    Astrogator,
    Engineer,
    Gunner,
    Maintenance,
    Medic,
    Officer,
    Pilot,
    SensorOperator,
    ShipCrew,
    Steward,
)
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
from ceres.make.ship.weapons import MountWeapon, Turret, WeaponsSection


def build_beagle_laboratory_ship() -> ship.Ship:
    return ship.Ship(
        ship_class='Beagle-class',
        ship_type='Laboratory Ship',
        tl=15,
        displacement=430,
        maintained_external_displacement=40,
        design_type=ship.ShipDesignType.STANDARD,
        passenger_vector={},
        hull=hull.Hull(
            configuration=hull.dispersed_structure,
            airlocks=[Airlock() for _ in range(4)],
        ),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=195)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=8),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge(small=True, holographic=True)),
        computer=ComputerSection(
            hardware=Computer(processing=10),
            software=[JumpControl(rating=2), Expert(rating=3, skill='Space Sciences (Planetology)')],
        ),
        sensors=SensorsSection(primary=ImprovedSensors(), sensor_stations=SensorStations(count=1)),
        weapons=WeaponsSection(
            turrets=[
                Turret(size='double', weapons=[MountWeapon(weapon='beam_laser'), MountWeapon(weapon='beam_laser')]),
                Turret(size='double', weapons=[MountWeapon(weapon='beam_laser'), MountWeapon(weapon='beam_laser')]),
            ],
        ),
        craft=CraftSection(
            docking_clamps=[
                DockingClamp(kind='II', craft=SpaceCraft.from_catalog('Pinnace')),
                DockingClamp(kind='I', craft=Vehicle.from_catalog('ATV')),
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
            cargo_airlocks=[CargoAirlock()],
            fuel_cargo_containers=[FuelCargoContainer(capacity=94)],
        ),
        crew=ShipCrew(
            roles=[
                *[Pilot()] * 2,
                Astrogator(),
                Engineer(),
                *[Gunner()] * 2,
                Maintenance(),
                Steward(),
                SensorOperator(),
                Medic(),
                *[Officer()] * 10,
            ]
        ),
    )


def test_beagle_laboratory_ship_matches_supported_slice():
    ship_ = build_beagle_laboratory_ship()

    assert ship_.hull_cost == pytest.approx(10_750_000.0)
    assert ship_.hull_points == pytest.approx(154.0)

    assert ship_.drives is not None
    assert ship_.drives.m_drive is not None
    assert ship_.drives.m_drive.tons == pytest.approx(9.4)
    assert ship_.drives.m_drive.cost == pytest.approx(18_800_000.0)
    assert ship_.drives.m_drive.power == pytest.approx(94.0)
    assert ship_.drives.j_drive is not None
    assert ship_.drives.j_drive.tons == pytest.approx(28.5)
    assert ship_.drives.j_drive.cost == pytest.approx(42_750_000.0)
    assert ship_.drives.j_drive.power == pytest.approx(94.0)

    assert ship_.power is not None
    assert ship_.power.fusion_plant is not None
    assert ship_.power.fusion_plant.tons == pytest.approx(13.0)
    assert ship_.power.fusion_plant.cost == pytest.approx(13_000_000.0)
    assert ship_.available_power == pytest.approx(195.0)
    assert ship_.total_power_load == pytest.approx(207.0)
    assert ship_.remaining_usable_tonnage() == pytest.approx(0.1)
    assert ('error', 'Hull overloaded by 1.90 tons') not in [
        (note.category.value, note.message) for note in ship_.notes
    ]
    assert ('warning', 'Capacity 12.00 less than max use') not in [
        (note.category.value, note.message) for note in ship_.notes
    ]

    assert ship_.fuel is not None
    assert ship_.fuel.jump_fuel is not None
    assert ship_.fuel.jump_fuel.tons == pytest.approx(94.0)
    assert ship_.fuel.operation_fuel is not None
    assert ship_.fuel.operation_fuel.tons == pytest.approx(3.0)
    assert ship_.fuel.fuel_processor is not None
    assert ship_.fuel.fuel_processor.tons == pytest.approx(2.0)
    assert ship_.fuel.fuel_processor.cost == pytest.approx(100_000.0)

    assert ship_.command is not None
    assert ship_.command.bridge is not None
    assert ship_.command.bridge.tons == pytest.approx(10.0)
    assert ship_.command.bridge.cost == pytest.approx(1_562_500.0)

    assert ship_.computer is not None
    assert ship_.computer.hardware is not None
    assert ship_.computer.hardware.cost == pytest.approx(160_000.0)
    assert [(package.description, package.cost) for package in ship_.computer.software_packages.values()] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000.0),
        ('Expert (Space Sciences (Planetology))/3', 20_000.0),
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
    assert ship_.weapons.turrets[1].power == pytest.approx(9.0)
    assert ship_.weapons.missile_storage is None
    assert ship_.weapons.sandcaster_canister_storage is None

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
    assert ship_.cargo.cargo_airlocks[0].tons == pytest.approx(2.0)
    assert ship_.cargo.cargo_airlocks[0].cost == pytest.approx(200_000.0)
    assert len(ship_.cargo.fuel_cargo_containers) == 1
    assert ship_.cargo.fuel_cargo_containers[0].tons == pytest.approx(99.0)
    assert ship_.cargo.fuel_cargo_containers[0].cost == pytest.approx(470_000.0)

    assert [(role.role, quantity) for role, quantity in ship_.crew.grouped_roles] == [
        ('PILOT', 2),
        ('ASTROGATOR', 1),
        ('ENGINEER', 1),
        ('GUNNER', 2),
        ('MAINTENANCE', 1),
        ('STEWARD', 1),
        ('SENSOR OPERATOR', 1),
        ('MEDIC', 1),
        ('OFFICER', 10),
    ]
    assert ('warning', 'ENGINEER below recommended count: 1 < 2') in [
        (note.category.value, note.message) for note in ship_.crew.notes
    ]
    assert ('info', 'MAINTENANCE above recommended count: 1 > 0') in [
        (note.category.value, note.message) for note in ship_.crew.notes
    ]
    assert ('warning', 'SENSOR OPERATOR below recommended count: 1 < 2') in [
        (note.category.value, note.message) for note in ship_.crew.notes
    ]
    assert ('info', 'OFFICER above recommended count: 10 > 0') in [
        (note.category.value, note.message) for note in ship_.crew.notes
    ]
    assert ('info', 'STEWARD above recommended count: 1 > 0') in [
        (note.category.value, note.message) for note in ship_.crew.notes
    ]


def test_beagle_laboratory_ship_spec_structure():
    ship_ = build_beagle_laboratory_ship()
    spec = ship_.build_spec()

    assert spec.row('Dispersed Structure Hull').section == 'Hull'
    assert spec.row('Airlock (2 tons)').quantity == 4
    assert spec.row('M-Drive 2 (470t)').section == 'Propulsion'
    assert spec.row('Jump 2 (470t)').section == 'Jump'
    assert spec.row('Fusion (TL 12), Power 195').section == 'Power'
    assert ('warning', 'Capacity 12.00 less than max use') in [
        (note.category.value, note.message) for note in spec.row('Fusion (TL 12), Power 195', section='Power').notes
    ]
    assert spec.row('J-2 (470t), 8 weeks of operation').tons == pytest.approx(97.0)
    assert spec.row('Fuel Processor (40 tons/day)').section == 'Fuel'
    assert spec.row('Smaller Holographic Controls').section == 'Command'
    assert spec.row('Computer/10').section == 'Computer'
    assert spec.row('Jump Control/2').section == 'Computer'
    assert spec.row('Improved Sensors').section == 'Sensors'
    assert spec.row('Sensor Station').section == 'Sensors'
    assert spec.row('Double Turret').quantity == 2
    with pytest.raises(KeyError):
        spec.row('Missile Storage (12)')
    with pytest.raises(KeyError):
        spec.row('Sandcaster Canister Storage (20)')
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
    assert spec.row('Cargo Airlock (2 tons)').section == 'Cargo'
    assert spec.row('Fuel/Cargo Container (94 tons)').section == 'Cargo'
    assert spec.row('Cargo Space').tons == pytest.approx(0.1)


def test_beagle_expert_software_roundtrip():
    ship_ = build_beagle_laboratory_ship()
    loaded = ship.Ship.model_validate_json(ship_.model_dump_json())
    assert loaded.computer is not None
    packages = loaded.computer.software_packages
    expert = next((p for p in packages.values() if isinstance(p, Expert)), None)
    assert expert is not None
    assert expert.rating == 3
    assert expert.skill == 'Space Sciences (Planetology)'
    assert expert.description == 'Expert (Space Sciences (Planetology))/3'
    assert expert.cost == pytest.approx(20_000.0)
