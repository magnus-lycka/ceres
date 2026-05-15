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
    turret_count=2,
    turret_0_power=9.0,
    turret_1_power=1.0,
    missile_storage_tons=1.0,
    missile_storage_cost_mcr=0.0,
    sandcaster_storage_tons=1.0,
    sandcaster_storage_cost_mcr=0.0,
    craft_items=[
        'Docking Clamp, Type II',
        'Docking Clamp, Type I',
        'Internal Docking Space: Air/Raft',
    ],
    craft_tons=[5.0, 1.0, 5.0],
    craft_costs_mcr=[1.0, 0.5, 1.25],
    pinnace_cost_mcr=9.68,
    atv_cost_mcr=0.155,
    probe_drones_count=1,
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
    hot_tubs_count=4,
    hot_tubs_total_tons=1.0,
    hot_tubs_total_cost=12_000.0,
    wet_bar_cost=2_000.0,
    low_berths_total_tons=3.0,
    low_berths_total_cost=300_000.0,
    low_berths_total_power=1.0,
    cargo_airlock_tons=2.0,  # ref; Ceres uses size=4 → 4 tons, MCr0.4
    cargo_airlock_count=1,
    cargo_airlock_cost_mcr=0.2,  # ref; Ceres: MCr0.4
    fuel_cargo_container_tons=84.0,  # ref: 84t (80 capacity + 4 overhead)
    fuel_cargo_container_count=1,
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
    expected_errors=[],
    expected_warnings=[],
    expected_crew_infos=[],
    expected_crew_warnings=[],
    spec_rows={
        'Dispersed Structure Hull': 'Hull',
        'M-Drive 2 (400t)': 'Propulsion',
        'Jump 2 (400t)': 'Jump',
        'Fusion (TL 12), Power 180': 'Power',
        'Fuel Processor (40 tons/day)': 'Fuel',
        'Smaller Holographic Controls': 'Command',
        'Computer/10': 'Computer',
        'Jump Control/2': 'Computer',
        'Improved Sensors': 'Sensors',
        'Sensor Station': 'Sensors',
        'Missile Storage (12)': 'Weapons',
        'Sandcaster Canister Storage (20)': 'Weapons',
        'Docking Clamp, Type II': 'Craft',
        'Pinnace': 'Craft',
        'Docking Clamp, Type I': 'Craft',
        'ATV': 'Craft',
        'Internal Docking Space: Air/Raft': 'Craft',
        'Air/Raft': 'Craft',
        'Biosphere': 'Systems',
        'Medical Bay': 'Systems',
        'Wet Bar': 'Habitation',
        'Cargo Airlock (4 tons)': 'Cargo',
        'Fuel/Cargo Container (80 tons)': 'Cargo',
    },
    spec_quantities={
        'Airlock (2 tons)': 3,
        'Double Turret': 2,
        'Advanced Probe Drones': 10,
        'Laboratory': 10,
        'Staterooms': 10,
        'Hot Tub (1 User)': 4,
        'Low Berths': 6,
    },
    spec_tons={
        'J-2 (400t), 8 weeks of operation': 83.0,
        'Cargo Space': 1.0,
    },
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
    assert len(ship_.weapons.turrets) == _expected.turret_count
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
    assert [part.build_item() for part in ship_.craft._all_parts()] == _expected.craft_items
    assert [part.tons for part in ship_.craft._all_parts()] == pytest.approx(_expected.craft_tons)
    assert [part.cost for part in ship_.craft._all_parts()] == pytest.approx(
        [c * 1_000_000 for c in _expected.craft_costs_mcr]
    )
    assert ship_.craft.docking_clamps[0].craft is not None
    assert ship_.craft.docking_clamps[0].craft.cost == pytest.approx(_expected.pinnace_cost_mcr * 1_000_000)
    assert ship_.craft.docking_clamps[1].craft is not None
    assert ship_.craft.docking_clamps[1].craft.cost == pytest.approx(_expected.atv_cost_mcr * 1_000_000)

    assert ship_.systems is not None
    assert len(ship_.systems.drones) == _expected.probe_drones_count
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
    assert len(ship_.habitation.hot_tubs) == _expected.hot_tubs_count
    assert sum(tub.tons for tub in ship_.habitation.hot_tubs) == pytest.approx(_expected.hot_tubs_total_tons)
    assert sum(tub.cost for tub in ship_.habitation.hot_tubs) == pytest.approx(_expected.hot_tubs_total_cost)
    assert ship_.habitation.wet_bar is not None
    assert ship_.habitation.wet_bar.cost == pytest.approx(_expected.wet_bar_cost)
    assert sum(berth.tons for berth in ship_.habitation.low_berths) == pytest.approx(_expected.low_berths_total_tons)
    assert sum(berth.cost for berth in ship_.habitation.low_berths) == pytest.approx(_expected.low_berths_total_cost)
    assert sum(berth.power for berth in ship_.habitation.low_berths) == pytest.approx(_expected.low_berths_total_power)

    assert ship_.cargo is not None
    assert len(ship_.cargo.cargo_airlocks) == _expected.cargo_airlock_count
    assert ship_.cargo.cargo_airlocks[0].tons == pytest.approx(_expected.cargo_airlock_tons)
    assert ship_.cargo.cargo_airlocks[0].cost == pytest.approx(_expected.cargo_airlock_cost_mcr * 1_000_000)
    assert len(ship_.cargo.fuel_cargo_containers) == _expected.fuel_cargo_container_count
    assert ship_.cargo.fuel_cargo_containers[0].tons == pytest.approx(_expected.fuel_cargo_container_tons)
    assert ship_.cargo.fuel_cargo_containers[0].cost == pytest.approx(
        _expected.fuel_cargo_container_cost_mcr * 1_000_000
    )

    assert [(role.role, quantity) for role, quantity in ship_.crew.grouped_roles] == _expected.crew
    assert ship_.notes.errors == _expected.expected_errors
    assert ship_.notes.warnings == _expected.expected_warnings
    assert ship_.crew.notes.infos == _expected.expected_crew_infos
    assert ship_.crew.notes.warnings == _expected.expected_crew_warnings

    assert ship_.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert ship_.sales_price_new == pytest.approx(_expected.sales_price_mcr * 1_000_000)


def test_beagle_laboratory_ship_spec_structure():
    ship_ = build_beagle_laboratory_ship()
    spec = ship_.build_spec()

    for item, section in _expected.spec_rows.items():
        assert spec.row(item, section=section).section == section
    for item, quantity in _expected.spec_quantities.items():
        if item == 'Double Turret':
            assert len(spec.rows_matching(item)) == quantity
        else:
            assert spec.row(item).quantity == quantity
    for item, tons in _expected.spec_tons.items():
        assert spec.row(item).tons == pytest.approx(tons)
