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

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer, ComputerSection, JumpControl
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.make.ship.crew import Astrogator, Engineer, Gunner, Medic, Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL15, JDrive, MDrive, PowerSection
from ceres.make.ship.habitation import HabitationSection, LowBerth, Stateroom
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
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
from ceres.make.ship.weapons import MountWeapon, Turret, WeaponsSection


def build_dolphin_extended_scout_courier() -> ship.Ship:
    return ship.Ship(
        ship_class='Dolphin Class',
        ship_type='Extended Scout Courier',
        tl=15,
        displacement=150,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            armour=armour.CrystalironArmour(tl=15, protection=4),
        ),
        drives=DriveSection(m_drive=MDrive(level=2), j_drive=JDrive(level=2)),
        power=PowerSection(fusion_plant=FusionPlantTL15(output=70)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=16),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(processing=10), software=[JumpControl(rating=2)]),
        sensors=SensorsSection(primary=MilitarySensors()),
        weapons=WeaponsSection(
            turrets=[
                Turret(
                    size='triple',
                    weapons=[
                        MountWeapon(weapon='pulse_laser'),
                        MountWeapon(weapon='pulse_laser'),
                        MountWeapon(weapon='pulse_laser'),
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

    assert dolphin.tl == 15
    assert dolphin.displacement == 150
    assert dolphin.hull_cost == pytest.approx(9_000_000.0)
    assert dolphin.hull_points == pytest.approx(60.0)

    assert dolphin.hull.armour is not None
    assert dolphin.hull.armour.tons == pytest.approx(9.0)
    assert dolphin.hull.armour.cost == pytest.approx(1_800_000.0)

    assert dolphin.drives is not None
    assert dolphin.drives.m_drive is not None
    assert dolphin.drives.m_drive.tons == pytest.approx(3.0)
    assert dolphin.drives.m_drive.cost == pytest.approx(6_000_000.0)
    assert dolphin.drives.m_drive.power == pytest.approx(30.0)
    assert dolphin.drives.j_drive is not None
    assert dolphin.drives.j_drive.tons == pytest.approx(12.5)
    assert dolphin.drives.j_drive.cost == pytest.approx(18_750_000.0)
    assert dolphin.drives.j_drive.power == pytest.approx(30.0)

    assert dolphin.power is not None
    assert dolphin.power.fusion_plant is not None
    assert dolphin.power.fusion_plant.tons == pytest.approx(3.5)
    assert dolphin.power.fusion_plant.cost == pytest.approx(7_000_000.0)
    assert dolphin.available_power == pytest.approx(70.0)

    assert dolphin.fuel is not None
    assert dolphin.fuel.jump_fuel is not None
    assert dolphin.fuel.jump_fuel.tons == pytest.approx(30.0)
    assert dolphin.fuel.operation_fuel is not None
    assert dolphin.fuel.operation_fuel.tons == pytest.approx(2.0)
    assert dolphin.fuel.fuel_scoops is not None
    assert dolphin.fuel.fuel_scoops.cost == pytest.approx(0.0)
    assert dolphin.fuel.fuel_processor is not None
    assert dolphin.fuel.fuel_processor.tons == pytest.approx(2.0)
    assert dolphin.fuel.fuel_processor.cost == pytest.approx(100_000.0)

    assert dolphin.command is not None
    assert dolphin.command.bridge is not None
    assert dolphin.command.bridge.tons == pytest.approx(10.0)
    assert dolphin.command.bridge.cost == pytest.approx(1_000_000.0)

    assert dolphin.computer is not None
    assert dolphin.computer.hardware is not None
    assert dolphin.computer.hardware.cost == pytest.approx(160_000.0)
    assert [(package.description, package.cost) for package in dolphin.computer.software_packages.values()] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
        ('Jump Control/2', 200_000.0),
    ]

    assert dolphin.sensors.primary.tons == pytest.approx(2.0)
    assert dolphin.sensors.primary.cost == pytest.approx(4_100_000.0)
    assert dolphin.sensors.primary.power == pytest.approx(2.0)

    assert dolphin.weapons is not None
    assert len(dolphin.weapons.turrets) == 1
    assert dolphin.weapons.turrets[0].tons == pytest.approx(1.0)
    assert dolphin.weapons.turrets[0].cost == pytest.approx(4_000_000.0)
    assert dolphin.weapons.turrets[0].power == pytest.approx(13.0)

    assert dolphin.craft is not None
    assert len(dolphin.craft.internal_housing) == 1
    assert dolphin.craft.internal_housing[0].tons == pytest.approx(5.0)
    assert dolphin.craft.internal_housing[0].cost == pytest.approx(1_250_000.0)
    assert dolphin.craft.internal_housing[0].craft.cost == pytest.approx(250_000.0)

    assert dolphin.systems is not None
    assert dolphin.systems.medical_bay is not None
    assert dolphin.systems.medical_bay.tons == pytest.approx(4.0)
    assert dolphin.systems.medical_bay.cost == pytest.approx(2_000_000.0)
    assert len(dolphin.systems.drones) == 1
    assert dolphin.systems.drones[0].tons == pytest.approx(2.0)
    assert dolphin.systems.drones[0].cost == pytest.approx(1_000_000.0)
    assert dolphin.systems.workshop is not None
    assert dolphin.systems.workshop.tons == pytest.approx(6.0)
    assert dolphin.systems.workshop.cost == pytest.approx(900_000.0)

    assert dolphin.habitation is not None
    assert sum(room.tons for room in dolphin.habitation.staterooms) == pytest.approx(16.0)
    assert sum(room.cost for room in dolphin.habitation.staterooms) == pytest.approx(2_000_000.0)
    assert dolphin.habitation.common_area is not None
    assert dolphin.habitation.common_area.tons == pytest.approx(4.0)
    assert dolphin.habitation.common_area.cost == pytest.approx(400_000.0)
    assert sum(berth.tons for berth in dolphin.habitation.low_berths) == pytest.approx(2.0)
    assert sum(berth.cost for berth in dolphin.habitation.low_berths) == pytest.approx(200_000.0)
    assert sum(berth.power for berth in dolphin.habitation.low_berths) == pytest.approx(1.0)

    assert dolphin.cargo is not None
    assert len(dolphin.cargo.cargo_airlocks) == 1
    assert dolphin.cargo.cargo_airlocks[0].tons == pytest.approx(2.0)
    assert dolphin.cargo.cargo_airlocks[0].cost == pytest.approx(200_000.0)
    assert len(dolphin.cargo.fuel_cargo_containers) == 1
    assert dolphin.cargo.fuel_cargo_containers[0].tons == pytest.approx(32.0)
    assert dolphin.cargo.fuel_cargo_containers[0].cost == pytest.approx(150_000.0)
    assert CargoSection.cargo_tons_for_ship(dolphin) == pytest.approx(32.0)

    assert len(dolphin.hull.airlocks or []) == 1
    assert dolphin.hull.airlocks[0].tons == pytest.approx(0.0)
    assert dolphin.hull.airlocks[0].cost == pytest.approx(0.0)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in dolphin.crew.grouped_roles] == [
        ('PILOT', 1, 6_000),
        ('ASTROGATOR', 1, 5_000),
        ('ENGINEER', 1, 4_000),
        ('GUNNER', 1, 2_000),
        ('MEDIC', 1, 4_000),
    ]

    assert dolphin.basic_hull_power_load == pytest.approx(30.0)
    assert dolphin.maneuver_power_load == pytest.approx(30.0)
    assert dolphin.jump_power_load == pytest.approx(30.0)
    assert dolphin.sensor_power_load == pytest.approx(2.0)
    assert dolphin.weapon_power_load == pytest.approx(13.0)
    assert dolphin.fuel_power_load == pytest.approx(2.0)
    assert dolphin.total_power_load == pytest.approx(79.0)

    assert dolphin.production_cost == pytest.approx(60_460_000.0)
    assert dolphin.sales_price_new == pytest.approx(54_414_000.0)
    assert dolphin.expenses.maintenance == pytest.approx(4_534.0)
    assert ('warning', 'Capacity 9.00 less than max use') not in [
        (note.category.value, note.message) for note in dolphin.notes
    ]


def test_dolphin_extended_scout_courier_spec_structure():
    spec = build_dolphin_extended_scout_courier().build_spec()

    assert spec.ship_class == 'Dolphin Class'
    assert spec.ship_type == 'Extended Scout Courier'
    assert spec.tl == 15
    assert spec.hull_points == pytest.approx(60.0)

    assert spec.row('Streamlined Hull').section == 'Hull'
    assert spec.row('Crystaliron, Armour: 4').section == 'Hull'
    assert spec.row('M-Drive 2').section == 'Propulsion'
    assert spec.row('Jump 2').section == 'Jump'
    assert ('warning', 'Capacity 9.00 less than max use') in [
        (note.category.value, note.message) for note in spec.row('Fusion (TL 15), Power 70', section='Power').notes
    ]
    assert spec.row('Fusion (TL 15), Power 70').section == 'Power'
    assert spec.row('J-2, 20 weeks of operation').section == 'Fuel'
    assert spec.row('Fuel Scoops').section == 'Fuel'
    assert spec.row('Fuel Processor (40 tons/day)').section == 'Fuel'
    assert spec.row('Computer/10').section == 'Computer'
    assert spec.row('Jump Control/2').section == 'Computer'
    assert spec.row('Military Grade Sensors').section == 'Sensors'
    assert spec.row('Triple Turret').section == 'Weapons'
    assert spec.row('Internal Docking Space: Air/Raft').section == 'Craft'
    assert spec.row('Air/Raft').section == 'Craft'
    assert spec.row('Medical Bay').section == 'Systems'
    assert spec.row('Probe Drones').quantity == 10
    assert spec.row('Workshop').section == 'Systems'
    assert spec.row('Staterooms').quantity == 4
    assert spec.row('Common Area').section == 'Habitation'
    assert spec.row('Low Berths').quantity == 4
    assert spec.row('Cargo Airlock (2 tons)').section == 'Cargo'
    assert spec.row('Fuel/Cargo Container (30 tons)').section == 'Cargo'
    assert spec.row('Cargo Space').tons == pytest.approx(2.0)
