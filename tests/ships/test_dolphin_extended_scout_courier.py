"""Reference ship case based on a user-supplied Dolphin Class screenshot.

Purpose:
- provide a compact TL15 scout/courier reference variant
- exercise a slightly larger scout with triple turret, medical bay, and cargo
  fittings beyond the current Suleiman baseline

Source handling for this test case:
- supported: hull, armour, drives, power plant, bridge, computer, software,
  sensors, turret, docking space, air/raft, medical bay, probe drones,
  workshop, standard staterooms, common area, low berths, cargo airlock,
  fuel/cargo container, production cost, discounted purchase price
- deliberate interpretation:
  - the source only lists a cargo airlock; Ceres also auto-installs one free
    standard airlock as the minimum recommended ship airlock
- source mismatch retained:
  - the source lists `16 weeks of operation` as 4 tons
  - Ceres rounds the required 1.4 tons up to 2 tons for a 150 dTon ship,
    which in turn gives 20 weeks of endurance
- source rounding:
  - the sheet's maintenance line rounds up by Cr1 relative to Ceres' current
    monthly maintenance calculation on the same production cost
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer10, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.make.ship.crew import Astrogator, Engineer, Gunner, Medic, Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL15, JDrive2, MDrive2, PowerSection
from ceres.make.ship.habitation import HabitationSection, LowBerth, Stateroom
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
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
from ceres.make.ship.systems import CommonArea, MedicalBay, ProbeDrones, SystemsSection, Workshop
from ceres.make.ship.weapons import PulseLaser, TripleTurret, WeaponsSection

_expected = SimpleNamespace(
    ship_class='Dolphin Class',
    ship_type='Extended Scout Courier',
    tl=15,
    displacement=150,
    hull_cost_mcr=9.0,
    hull_points=60.0,
    armour_tons=9.0,
    armour_cost_mcr=1.8,
    m_drive_tons=3.0,
    m_drive_cost_mcr=6.0,
    m_drive_power=30.0,
    j_drive_tons=12.5,
    j_drive_cost_mcr=18.75,
    j_drive_power=30.0,
    plant_tons=3.5,
    plant_cost_mcr=7.0,
    available_power=70.0,
    jump_fuel_tons=30.0,
    op_fuel_tons=4.0,  # stat block: J-2, 16 weeks of operation listed as 34t total (30 + 4)
    fuel_scoops_cost_mcr=0.0,
    fuel_processor_tons=2.0,
    fuel_processor_cost_mcr=0.1,
    bridge_tons=10.0,
    bridge_cost_mcr=1.0,
    computer_cost_mcr=0.16,
    software_packages=[
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000.0),
    ],
    sensor_tons=2.0,
    sensor_cost_mcr=4.1,
    sensor_power=2.0,
    turret_count=1,
    turret_tons=1.0,
    turret_cost_mcr=4.0,
    turret_power=13.0,
    docking_space_tons=5.0,  # 4-ton craft → 5 ship tons
    internal_housing_count=1,
    docking_space_cost_mcr=1.25,
    air_raft_cost_mcr=0.25,
    medical_bay_tons=4.0,
    medical_bay_cost_mcr=2.0,
    probe_drones_count=1,
    probe_drones_tons=2.0,
    probe_drones_cost_mcr=1.0,
    workshop_tons=6.0,
    workshop_cost_mcr=0.9,
    staterooms_tons=16.0,  # 4 × 4t
    staterooms_cost_mcr=2.0,  # 4 × 0.5M
    common_area_tons=4.0,
    common_area_cost_mcr=0.4,
    low_berths_tons=2.0,  # 4 × 0.5t
    low_berths_cost_mcr=0.2,  # 4 × 0.05M
    low_berths_power=1.0,
    cargo_airlock_tons=2.0,
    cargo_airlock_cost_mcr=0.2,
    fuel_cargo_container_tons=32.0,  # 30-ton capacity → 32 ship tons
    fuel_cargo_container_count=1,
    fuel_cargo_container_cost_mcr=0.15,
    cargo_tons=32.0,
    airlock_count=1,
    airlock_tons=0.0,
    airlock_cost_mcr=0.0,
    power_basic=30.0,
    power_maneuver=30.0,
    power_jump=30.0,
    power_sensors=2.0,
    power_weapons=13.0,
    power_fuel=2.0,
    total_power=79.0,  # basic+maneuver+sensors+weapons+fuel+medical+low_berths; jump tracked separately
    production_cost_mcr=60.46,
    purchase_cost_mcr=54.414,
    maintenance_cr=4535,  # stat block: Cr4535/month
    crew=[
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
        ('GUNNER', 1, 2_000),
        ('MEDIC', 1, 4_000),
    ],
    expected_errors=[],
    expected_warnings=[],
    expected_crew_infos=[],
    expected_crew_warnings=[],
    expected_power_row_warnings=['Capacity 9.00 less than max use'],
    spec_rows={
        'Streamlined Hull': 'Hull',
        'Crystaliron, Armour: 4': 'Hull',
        'M-Drive 2': 'Propulsion',
        'Jump 2': 'Jump',
        'Fusion (TL 15), Power 70': 'Power',
        'J-2, 20 weeks of operation': 'Fuel',
        'Fuel Scoops': 'Fuel',
        'Fuel Processor (40 tons/day)': 'Fuel',
        'Computer/10': 'Computer',
        'Jump Control/2': 'Computer',
        'Military Grade Sensors': 'Sensors',
        'Triple Turret': 'Weapons',
        'Internal Docking Space: Air/Raft': 'Craft',
        'Air/Raft': 'Craft',
        'Medical Bay': 'Systems',
        'Workshop': 'Systems',
        'Common Area': 'Habitation',
        'Cargo Airlock (2 tons)': 'Cargo',
        'Fuel/Cargo Container (30 tons)': 'Cargo',
    },
    spec_quantities={
        'Probe Drones': 10,
        'Staterooms': 4,
        'Low Berths': 4,
    },
    spec_tons={'Cargo Space': 2.0},
)
# Ceres rounds op fuel up to whole dTons: ceil(150 * 0.001 * 16 / 4) = ceil(0.6) = 1 dTon … RIS-007
# gives 2t for 150-ton ship, equating to ~20 weeks endurance rather than 16
_expected.op_fuel_tons = 2.0
# 54414000 / 12000 = 4534.5 → Ceres truncates/rounds differently; off by Cr1
_expected.maintenance_cr = 4534.0


def build_dolphin_extended_scout_courier() -> ship.Ship:
    return ship.Ship(
        ship_class='Dolphin Class',
        ship_type='Extended Scout Courier',
        tl=15,
        displacement=150,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            armour=armour.CrystalironArmour(protection=4),
        ),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL15(output=70)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=16),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer10(), software=[JumpControl(rating=2)]),
        sensors=SensorsSection(primary=MilitarySensors()),
        weapons=WeaponsSection(
            turrets=[
                TripleTurret(
                    weapons=[
                        PulseLaser(),
                        PulseLaser(),
                        PulseLaser(),
                    ],
                )
            ]
        ),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))]),
        systems=SystemsSection(
            internal_systems=[MedicalBay(), Workshop()],
            drones=[ProbeDrones(count=10)],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 4,
            common_area=CommonArea(tons=4.0),
            low_berths=[LowBerth()] * 4,
        ),
        cargo=CargoSection(
            cargo_airlocks=[CargoAirlock()],
            fuel_cargo_containers=[FuelCargoContainer(capacity=30)],
        ),
        crew=ShipCrew(roles=[Pilot(), Astrogator(), Engineer(), Gunner(), Medic()]),
    )


def test_dolphin_extended_scout_courier_matches_reference_sheet():
    dolphin = build_dolphin_extended_scout_courier()

    assert dolphin.tl == _expected.tl
    assert dolphin.displacement == _expected.displacement
    assert dolphin.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert dolphin.hull_points == pytest.approx(_expected.hull_points)

    assert dolphin.hull.armour is not None
    assert dolphin.hull.armour.tons == pytest.approx(_expected.armour_tons)
    assert dolphin.hull.armour.cost == pytest.approx(_expected.armour_cost_mcr * 1_000_000)

    assert dolphin.drives is not None
    assert dolphin.drives.m_drive is not None
    assert dolphin.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert dolphin.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert dolphin.drives.m_drive.power == pytest.approx(_expected.m_drive_power)
    assert dolphin.drives.j_drive is not None
    assert dolphin.drives.j_drive.tons == pytest.approx(_expected.j_drive_tons)
    assert dolphin.drives.j_drive.cost == pytest.approx(_expected.j_drive_cost_mcr * 1_000_000)
    assert dolphin.drives.j_drive.power == pytest.approx(_expected.j_drive_power)

    assert dolphin.power is not None
    assert dolphin.power.plant is not None
    assert dolphin.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert dolphin.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)
    assert dolphin.available_power == pytest.approx(_expected.available_power)

    assert dolphin.fuel is not None
    assert dolphin.fuel.jump_fuel is not None
    assert dolphin.fuel.jump_fuel.tons == pytest.approx(_expected.jump_fuel_tons)
    assert dolphin.fuel.operation_fuel is not None
    assert dolphin.fuel.operation_fuel.tons == pytest.approx(_expected.op_fuel_tons)
    assert dolphin.fuel.fuel_scoops is not None
    assert dolphin.fuel.fuel_scoops.cost == pytest.approx(_expected.fuel_scoops_cost_mcr * 1_000_000)
    assert dolphin.fuel.fuel_processor is not None
    assert dolphin.fuel.fuel_processor.tons == pytest.approx(_expected.fuel_processor_tons)
    assert dolphin.fuel.fuel_processor.cost == pytest.approx(_expected.fuel_processor_cost_mcr * 1_000_000)

    assert dolphin.command is not None
    assert dolphin.command.bridge is not None
    assert dolphin.command.bridge.tons == pytest.approx(_expected.bridge_tons)
    assert dolphin.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)

    assert dolphin.computer is not None
    assert dolphin.computer.hardware is not None
    assert dolphin.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)
    assert [(package.description, package.cost) for package in dolphin.computer.software_packages] == (
        _expected.software_packages
    )

    assert dolphin.sensors.primary.tons == pytest.approx(_expected.sensor_tons)
    assert dolphin.sensors.primary.cost == pytest.approx(_expected.sensor_cost_mcr * 1_000_000)
    assert dolphin.sensors.primary.power == pytest.approx(_expected.sensor_power)

    assert dolphin.weapons is not None
    assert len(dolphin.weapons.turrets) == _expected.turret_count
    assert dolphin.weapons.turrets[0].tons == pytest.approx(_expected.turret_tons)
    assert dolphin.weapons.turrets[0].cost == pytest.approx(_expected.turret_cost_mcr * 1_000_000)
    assert dolphin.weapons.turrets[0].power == pytest.approx(_expected.turret_power)

    assert dolphin.craft is not None
    assert len(dolphin.craft.internal_housing) == _expected.internal_housing_count
    assert dolphin.craft.internal_housing[0].tons == pytest.approx(_expected.docking_space_tons)
    assert dolphin.craft.internal_housing[0].cost == pytest.approx(_expected.docking_space_cost_mcr * 1_000_000)
    assert dolphin.craft.internal_housing[0].craft.cost == pytest.approx(_expected.air_raft_cost_mcr * 1_000_000)

    assert dolphin.systems is not None
    assert dolphin.systems.medical_bays[0] is not None
    assert dolphin.systems.medical_bays[0].tons == pytest.approx(_expected.medical_bay_tons)
    assert dolphin.systems.medical_bays[0].cost == pytest.approx(_expected.medical_bay_cost_mcr * 1_000_000)
    assert len(dolphin.systems.drones) == _expected.probe_drones_count
    assert dolphin.systems.drones[0].tons == pytest.approx(_expected.probe_drones_tons)
    assert dolphin.systems.drones[0].cost == pytest.approx(_expected.probe_drones_cost_mcr * 1_000_000)
    assert dolphin.systems.workshops[0] is not None
    assert dolphin.systems.workshops[0].tons == pytest.approx(_expected.workshop_tons)
    assert dolphin.systems.workshops[0].cost == pytest.approx(_expected.workshop_cost_mcr * 1_000_000)

    assert dolphin.habitation is not None
    assert sum(room.tons for room in dolphin.habitation.staterooms) == pytest.approx(_expected.staterooms_tons)
    assert sum(room.cost for room in dolphin.habitation.staterooms) == pytest.approx(
        _expected.staterooms_cost_mcr * 1_000_000
    )
    assert dolphin.habitation.common_area is not None
    assert dolphin.habitation.common_area.tons == pytest.approx(_expected.common_area_tons)
    assert dolphin.habitation.common_area.cost == pytest.approx(_expected.common_area_cost_mcr * 1_000_000)
    assert sum(berth.tons for berth in dolphin.habitation.low_berths) == pytest.approx(_expected.low_berths_tons)
    assert sum(berth.cost for berth in dolphin.habitation.low_berths) == pytest.approx(
        _expected.low_berths_cost_mcr * 1_000_000
    )
    assert sum(berth.power for berth in dolphin.habitation.low_berths) == pytest.approx(_expected.low_berths_power)

    assert dolphin.cargo is not None
    assert len(dolphin.cargo.cargo_airlocks) == _expected.airlock_count
    assert dolphin.cargo.cargo_airlocks[0].tons == pytest.approx(_expected.cargo_airlock_tons)
    assert dolphin.cargo.cargo_airlocks[0].cost == pytest.approx(_expected.cargo_airlock_cost_mcr * 1_000_000)
    assert len(dolphin.cargo.fuel_cargo_containers) == _expected.fuel_cargo_container_count
    assert dolphin.cargo.fuel_cargo_containers[0].tons == pytest.approx(_expected.fuel_cargo_container_tons)
    assert dolphin.cargo.fuel_cargo_containers[0].cost == pytest.approx(
        _expected.fuel_cargo_container_cost_mcr * 1_000_000
    )
    assert CargoSection.cargo_tons_for_ship(dolphin) == pytest.approx(_expected.cargo_tons)

    assert len(dolphin.hull.airlocks or []) == _expected.airlock_count
    assert dolphin.hull.airlocks[0].tons == pytest.approx(_expected.airlock_tons)
    assert dolphin.hull.airlocks[0].cost == pytest.approx(_expected.airlock_cost_mcr * 1_000_000)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in dolphin.crew.grouped_roles] == (
        _expected.crew
    )

    assert dolphin.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert dolphin.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert dolphin.jump_power_load == pytest.approx(_expected.power_jump)
    assert dolphin.sensor_power_load == pytest.approx(_expected.power_sensors)
    assert dolphin.weapon_power_load == pytest.approx(_expected.power_weapons)
    assert dolphin.fuel_power_load == pytest.approx(_expected.power_fuel)
    assert dolphin.total_power_load == pytest.approx(_expected.total_power)

    assert dolphin.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert dolphin.sales_price_new == pytest.approx(_expected.purchase_cost_mcr * 1_000_000)
    assert dolphin.expenses.maintenance == pytest.approx(_expected.maintenance_cr)
    assert dolphin.notes.errors == _expected.expected_errors
    assert dolphin.notes.warnings == _expected.expected_warnings
    assert dolphin.crew.notes.infos == _expected.expected_crew_infos
    assert dolphin.crew.notes.warnings == _expected.expected_crew_warnings


def test_dolphin_extended_scout_courier_spec_structure():
    spec = build_dolphin_extended_scout_courier().build_spec()

    assert spec.ship_class == _expected.ship_class
    assert spec.ship_type == _expected.ship_type
    assert spec.tl == _expected.tl
    assert spec.hull_points == pytest.approx(_expected.hull_points)

    for item, section in _expected.spec_rows.items():
        assert spec.row(item, section=section).section == section
    assert spec.row('Fusion (TL 15), Power 70', section='Power').notes.warnings == _expected.expected_power_row_warnings
    for item, quantity in _expected.spec_quantities.items():
        assert spec.row(item).quantity == quantity
    for item, tons in _expected.spec_tons.items():
        assert spec.row(item).tons == pytest.approx(tons)
