"""Reference ship case based on refs/tycho/BeagleLaboratoryShip.txt.

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
  - software packages `Mentor/1` and `Research Assist/1` have no HG 2022 equivalent (see RIS-008)
  - `Planetology/1` is modeled as `Expert(rating=3, skill='Space Science (Planetology)')`
"""

from types import SimpleNamespace

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

_expected = SimpleNamespace(
    hull_cost_mcr=10.0,  # ref: 400t Dispersed Structure; Ceres uses 360t → MCr9
    hull_points=129.0,  # Ceres 360t dispersed (ref would be 144 for 400t)
    m_drive_tons=8.0,
    m_drive_cost_mcr=16.0,
    m_drive_power=80.0,
    j_drive_tons=25.0,
    j_drive_cost_mcr=37.5,
    j_drive_power=80.0,
    plant_tons=12.0,
    plant_cost_mcr=12.0,
    available_power=180.0,
    total_power=171.0,
    remaining_usable_tonnage=1.0,
    jump_fuel_tons=80.0,  # ref shows combined 84t (J-2 + 8 weeks); Ceres splits: 80 jump + 3 op
    operation_fuel_tons=3.0,  # Ceres value; ref groups with jump fuel
    fuel_processor_tons=2.0,
    fuel_processor_cost_mcr=0.1,
    bridge_tons=10.0,
    bridge_cost_mcr=1.25,
    computer_cost_mcr=0.16,
    software_packages=[
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000.0),
        ('Expert (Space Science (Planetology))/3', 20_000.0),
    ],
    sensors_tons=3.0,
    sensors_cost_mcr=4.3,
    sensors_power=3.0,
    sensor_station_tons=1.0,
    sensor_station_cost_mcr=0.5,
    turret_0_cost_mcr=1.5,
    turret_1_cost_mcr=1.5,
    turret_0_power=9.0,
    turret_1_power=1.0,
    missile_storage_tons=1.0,
    missile_storage_cost_mcr=0.0,
    sandcaster_storage_tons=1.0,
    sandcaster_storage_cost_mcr=0.0,
    craft_tons=[5.0, 1.0, 5.0],
    craft_costs_mcr=[1.0, 0.5, 1.25],
    pinnace_cost_mcr=9.68,
    atv_cost_mcr=0.155,
    probe_drones_tons=2.0,
    probe_drones_cost_mcr=1.6,
    biosphere_tons=2.0,
    biosphere_cost_mcr=0.4,
    biosphere_power=2.0,
    lab_count=10,
    labs_total_tons=40.0,
    labs_total_cost_mcr=10.0,
    library_tons=4.0,
    library_cost_mcr=4.0,
    medical_bay_tons=4.0,
    medical_bay_cost_mcr=2.0,
    workshop_tons=6.0,
    workshop_cost_mcr=0.9,
    staterooms_total_tons=40.0,
    staterooms_total_cost_mcr=5.0,
    common_area_tons=10.0,
    common_area_cost_mcr=1.0,
    hot_tubs_total_tons=1.0,
    hot_tubs_total_cost=12_000.0,
    wet_bar_cost=2_000.0,
    low_berths_total_tons=3.0,
    low_berths_total_cost=300_000.0,
    low_berths_total_power=1.0,
    cargo_airlock_tons=2.0,  # ref; Ceres uses size=4 → 4 tons, MCr0.4
    cargo_airlock_cost_mcr=0.2,  # ref; Ceres: MCr0.4
    fuel_cargo_container_tons=84.0,  # ref: 84t (80 capacity + 4 overhead)
    fuel_cargo_container_cost_mcr=0.4,
    crew=[
        ('PILOT', 2),
        ('ASTROGATOR', 1),
        ('ENGINEER', 2),
        ('GUNNER', 2),
        ('SENSOR OPERATOR', 2),
        ('MEDIC', 1),
    ],
    # ref total MCr128.709 / purchase MCr115.838; Ceres differs due to 360t hull,
    # excluded Ship's Mechanic, and included Expert software
    production_cost_mcr=128.709,
    sales_price_mcr=115.838,
)
# Ceres 360t hull (MCr9 vs ref MCr10), no Ship's Mechanic (-MCr0.05), adds Expert (+MCr0.02)
_expected.hull_cost_mcr = 9.0
_expected.production_cost_mcr = 122.879
_expected.sales_price_mcr = 110.5911
# Ceres cargo airlock size=4 → 4 tons, MCr0.4
_expected.cargo_airlock_tons = 4.0
_expected.cargo_airlock_cost_mcr = 0.4


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

    assert ship_.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert ship_.hull_points == pytest.approx(_expected.hull_points)

    assert ship_.drives is not None
    assert ship_.drives.m_drive is not None
    assert ship_.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert ship_.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert ship_.drives.m_drive.power == pytest.approx(_expected.m_drive_power)
    assert ship_.drives.j_drive is not None
    assert ship_.drives.j_drive.tons == pytest.approx(_expected.j_drive_tons)
    assert ship_.drives.j_drive.cost == pytest.approx(_expected.j_drive_cost_mcr * 1_000_000)
    assert ship_.drives.j_drive.power == pytest.approx(_expected.j_drive_power)

    assert ship_.power is not None
    assert ship_.power.plant is not None
    assert ship_.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert ship_.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)
    assert ship_.available_power == pytest.approx(_expected.available_power)
    assert ship_.total_power_load == pytest.approx(_expected.total_power)
    assert ship_.remaining_usable_tonnage() == pytest.approx(_expected.remaining_usable_tonnage)
    assert 'Capacity 12.00 less than max use' not in ship_.notes.warnings

    assert ship_.fuel is not None
    assert ship_.fuel.jump_fuel is not None
    assert ship_.fuel.jump_fuel.tons == pytest.approx(_expected.jump_fuel_tons)
    assert ship_.fuel.operation_fuel is not None
    assert ship_.fuel.operation_fuel.tons == pytest.approx(_expected.operation_fuel_tons)
    assert ship_.fuel.fuel_processor is not None
    assert ship_.fuel.fuel_processor.tons == pytest.approx(_expected.fuel_processor_tons)
    assert ship_.fuel.fuel_processor.cost == pytest.approx(_expected.fuel_processor_cost_mcr * 1_000_000)

    assert ship_.command is not None
    assert ship_.command.bridge is not None
    assert ship_.command.bridge.tons == pytest.approx(_expected.bridge_tons)
    assert ship_.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)

    assert ship_.computer is not None
    assert ship_.computer.hardware is not None
    assert ship_.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)
    assert [(package.description, package.cost) for package in ship_.computer.software_packages] == (
        _expected.software_packages
    )

    assert ship_.sensors.primary.tons == pytest.approx(_expected.sensors_tons)
    assert ship_.sensors.primary.cost == pytest.approx(_expected.sensors_cost_mcr * 1_000_000)
    assert ship_.sensors.primary.power == pytest.approx(_expected.sensors_power)
    assert ship_.sensors.sensor_stations is not None
    assert ship_.sensors.sensor_stations.tons == pytest.approx(_expected.sensor_station_tons)
    assert ship_.sensors.sensor_stations.cost == pytest.approx(_expected.sensor_station_cost_mcr * 1_000_000)

    assert ship_.weapons is not None
    assert len(ship_.weapons.turrets) == 2
    assert ship_.weapons.turrets[0].cost == pytest.approx(_expected.turret_0_cost_mcr * 1_000_000)
    assert ship_.weapons.turrets[1].cost == pytest.approx(_expected.turret_1_cost_mcr * 1_000_000)
    assert ship_.weapons.turrets[0].power == pytest.approx(_expected.turret_0_power)
    assert ship_.weapons.turrets[1].power == pytest.approx(_expected.turret_1_power)
    assert ship_.weapons.missile_storage is not None
    assert ship_.weapons.missile_storage.tons == pytest.approx(_expected.missile_storage_tons)
    assert ship_.weapons.missile_storage.cost == pytest.approx(_expected.missile_storage_cost_mcr * 1_000_000)
    assert ship_.weapons.sandcaster_canister_storage is not None
    assert ship_.weapons.sandcaster_canister_storage.tons == pytest.approx(_expected.sandcaster_storage_tons)
    assert ship_.weapons.sandcaster_canister_storage.cost == pytest.approx(
        _expected.sandcaster_storage_cost_mcr * 1_000_000
    )

    assert ship_.craft is not None
    assert [part.build_item() for part in ship_.craft._all_parts()] == [
        'Docking Clamp, Type II',
        'Docking Clamp, Type I',
        'Internal Docking Space: Air/Raft',
    ]
    assert [part.tons for part in ship_.craft._all_parts()] == pytest.approx(_expected.craft_tons)
    assert [part.cost for part in ship_.craft._all_parts()] == pytest.approx(
        [c * 1_000_000 for c in _expected.craft_costs_mcr]
    )
    assert ship_.craft.docking_clamps[0].craft is not None
    assert ship_.craft.docking_clamps[0].craft.cost == pytest.approx(_expected.pinnace_cost_mcr * 1_000_000)
    assert ship_.craft.docking_clamps[1].craft is not None
    assert ship_.craft.docking_clamps[1].craft.cost == pytest.approx(_expected.atv_cost_mcr * 1_000_000)

    assert ship_.systems is not None
    assert len(ship_.systems.drones) == 1
    assert ship_.systems.drones[0].tons == pytest.approx(_expected.probe_drones_tons)
    assert ship_.systems.drones[0].cost == pytest.approx(_expected.probe_drones_cost_mcr * 1_000_000)
    assert ship_.systems.biospheres[0] is not None
    assert ship_.systems.biospheres[0].tons == pytest.approx(_expected.biosphere_tons)
    assert ship_.systems.biospheres[0].cost == pytest.approx(_expected.biosphere_cost_mcr * 1_000_000)
    assert ship_.systems.biospheres[0].power == pytest.approx(_expected.biosphere_power)
    assert len(ship_.systems.laboratories) == _expected.lab_count
    assert sum(lab.tons for lab in ship_.systems.laboratories) == pytest.approx(_expected.labs_total_tons)
    assert sum(lab.cost for lab in ship_.systems.laboratories) == pytest.approx(
        _expected.labs_total_cost_mcr * 1_000_000
    )
    assert ship_.systems.libraries[0] is not None
    assert ship_.systems.libraries[0].tons == pytest.approx(_expected.library_tons)
    assert ship_.systems.libraries[0].cost == pytest.approx(_expected.library_cost_mcr * 1_000_000)
    assert ship_.systems.medical_bays[0] is not None
    assert ship_.systems.medical_bays[0].tons == pytest.approx(_expected.medical_bay_tons)
    assert ship_.systems.medical_bays[0].cost == pytest.approx(_expected.medical_bay_cost_mcr * 1_000_000)
    assert ship_.systems.workshops[0] is not None
    assert ship_.systems.workshops[0].tons == pytest.approx(_expected.workshop_tons)
    assert ship_.systems.workshops[0].cost == pytest.approx(_expected.workshop_cost_mcr * 1_000_000)

    assert ship_.habitation is not None
    assert sum(room.tons for room in ship_.habitation.staterooms) == pytest.approx(_expected.staterooms_total_tons)
    assert sum(room.cost for room in ship_.habitation.staterooms) == pytest.approx(
        _expected.staterooms_total_cost_mcr * 1_000_000
    )
    assert ship_.habitation.common_area is not None
    assert ship_.habitation.common_area.tons == pytest.approx(_expected.common_area_tons)
    assert ship_.habitation.common_area.cost == pytest.approx(_expected.common_area_cost_mcr * 1_000_000)
    assert len(ship_.habitation.hot_tubs) == 4
    assert sum(tub.tons for tub in ship_.habitation.hot_tubs) == pytest.approx(_expected.hot_tubs_total_tons)
    assert sum(tub.cost for tub in ship_.habitation.hot_tubs) == pytest.approx(_expected.hot_tubs_total_cost)
    assert ship_.habitation.wet_bar is not None
    assert ship_.habitation.wet_bar.cost == pytest.approx(_expected.wet_bar_cost)
    assert sum(berth.tons for berth in ship_.habitation.low_berths) == pytest.approx(_expected.low_berths_total_tons)
    assert sum(berth.cost for berth in ship_.habitation.low_berths) == pytest.approx(_expected.low_berths_total_cost)
    assert sum(berth.power for berth in ship_.habitation.low_berths) == pytest.approx(_expected.low_berths_total_power)

    assert ship_.cargo is not None
    assert len(ship_.cargo.cargo_airlocks) == 1
    assert ship_.cargo.cargo_airlocks[0].tons == pytest.approx(_expected.cargo_airlock_tons)
    assert ship_.cargo.cargo_airlocks[0].cost == pytest.approx(_expected.cargo_airlock_cost_mcr * 1_000_000)
    assert len(ship_.cargo.fuel_cargo_containers) == 1
    assert ship_.cargo.fuel_cargo_containers[0].tons == pytest.approx(_expected.fuel_cargo_container_tons)
    assert ship_.cargo.fuel_cargo_containers[0].cost == pytest.approx(
        _expected.fuel_cargo_container_cost_mcr * 1_000_000
    )

    assert [(role.role, quantity) for role, quantity in ship_.crew.grouped_roles] == _expected.crew
    assert ship_.crew.notes.warnings == []

    assert ship_.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert ship_.sales_price_new == pytest.approx(_expected.sales_price_mcr * 1_000_000)


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
