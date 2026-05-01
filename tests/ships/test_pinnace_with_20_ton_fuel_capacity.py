"""Reference ship case based on refs/PinnaceWith20TonFuelCapacity.txt.

Purpose:
- provide a compact small-craft reference case with a large fuel/cargo
  container and explicit purchased airlock

Source handling for this test case:
- supported: hull, manoeuvre drive, power plant, operation fuel, fuel scoops,
  bridge, computer, included software, basic sensors, explicit airlock, cabin
  space, fuel/cargo container, production cost, discounted purchase price, and
  maintenance cost
- deliberate interpretation:
  - the airlock is modeled as an explicitly purchased airlock on a small craft;
    it is not treated as a free included airlock
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer, ComputerSection
from ceres.make.ship.crew import Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive, PowerSection
from ceres.make.ship.habitation import CabinSpace, HabitationSection
from ceres.make.ship.sensors import BasicSensors, SensorsSection
from ceres.make.ship.storage import CargoSection, FuelCargoContainer, FuelSection, OperationFuel
from ceres.make.ship.systems import Airlock, SystemsSection


def build_pinnace_with_20_ton_fuel_capacity() -> ship.Ship:
    return ship.Ship(
        ship_class='Pinnace',
        ship_type='with 20 ton fuel capacity',
        tl=12,
        displacement=40,
        design_type=ship.ShipDesignType.STANDARD,
        passenger_vector={},
        crew=ShipCrew(roles=[Pilot()]),
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
        drives=DriveSection(m_drive=MDrive(5)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=30)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=4)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        sensors=SensorsSection(primary=BasicSensors()),
        systems=SystemsSection(),
        habitation=HabitationSection(cabin_space=CabinSpace(tons=9)),
        cargo=CargoSection(fuel_cargo_containers=[FuelCargoContainer(capacity=20)]),
    )


def test_pinnace_with_20_ton_fuel_capacity_matches_reference_sheet():
    pinnace = build_pinnace_with_20_ton_fuel_capacity()

    assert pinnace.tl == 12
    assert pinnace.displacement == 40
    assert pinnace.hull_cost == pytest.approx(2_400_000.0)
    assert pinnace.hull_points == pytest.approx(16.0)

    assert pinnace.drives is not None
    assert pinnace.drives.m_drive is not None
    assert pinnace.drives.m_drive.tons == pytest.approx(2.0)
    assert pinnace.drives.m_drive.cost == pytest.approx(4_000_000.0)
    assert pinnace.drives.m_drive.power == pytest.approx(20.0)

    assert pinnace.power is not None
    assert pinnace.power.fusion_plant is not None
    assert pinnace.power.fusion_plant.tons == pytest.approx(2.0)
    assert pinnace.power.fusion_plant.cost == pytest.approx(2_000_000.0)
    assert pinnace.available_power == pytest.approx(30.0)

    assert pinnace.fuel is not None
    assert pinnace.fuel.operation_fuel is not None
    assert pinnace.fuel.operation_fuel.tons == pytest.approx(0.2)
    assert pinnace.fuel.fuel_scoops is not None
    assert pinnace.fuel.fuel_scoops.cost == pytest.approx(0.0)

    assert pinnace.command is not None
    assert pinnace.command.bridge is not None
    assert pinnace.command.bridge.tons == pytest.approx(3.0)
    assert pinnace.command.bridge.cost == pytest.approx(500_000.0)

    assert pinnace.computer is not None
    assert pinnace.computer.hardware is not None
    assert pinnace.computer.hardware.cost == pytest.approx(30_000.0)
    assert [(package.description, package.cost) for package in pinnace.computer.software_packages.values()] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
    ]

    assert pinnace.sensors.primary.tons == pytest.approx(0.0)
    assert pinnace.sensors.primary.cost == pytest.approx(0.0)
    assert pinnace.sensors.primary.power == pytest.approx(0.0)

    assert len(pinnace.hull.airlocks or []) == 1
    assert pinnace.hull.airlocks[0].tons == pytest.approx(2.0)
    assert pinnace.hull.airlocks[0].cost == pytest.approx(200_000.0)

    assert pinnace.habitation is not None
    assert pinnace.habitation.cabin_space is not None
    assert pinnace.habitation.cabin_space.tons == pytest.approx(9.0)
    assert pinnace.habitation.cabin_space.cost == pytest.approx(450_000.0)
    assert pinnace.habitation.cabin_space.passenger_capacity == 6

    assert pinnace.cargo is not None
    assert len(pinnace.cargo.fuel_cargo_containers) == 1
    assert pinnace.cargo.fuel_cargo_containers[0].tons == pytest.approx(21.0)
    assert pinnace.cargo.fuel_cargo_containers[0].cost == pytest.approx(100_000.0)
    assert CargoSection.cargo_tons_for_ship(pinnace) == pytest.approx(20.8)

    assert pinnace.basic_hull_power_load == pytest.approx(8.0)
    assert pinnace.maneuver_power_load == pytest.approx(20.0)
    assert pinnace.total_power_load == pytest.approx(28.0)

    assert pinnace.production_cost == pytest.approx(9_680_000.0)
    assert pinnace.sales_price_new == pytest.approx(8_712_000.0)
    assert pinnace.expenses.maintenance == pytest.approx(726.0)

    assert [(role.role, quantity, role.monthly_salary) for role, quantity in pinnace.crew.grouped_roles] == [
        ('PILOT', 1, 6_000),
    ]


def test_pinnace_with_20_ton_fuel_capacity_spec_structure():
    pinnace = build_pinnace_with_20_ton_fuel_capacity()
    spec = pinnace.build_spec()

    assert spec.row('Streamlined Hull').section == 'Hull'
    assert spec.row('Airlock (2 tons)').section == 'Hull'
    assert spec.row('M-Drive 5').section == 'Propulsion'
    assert spec.row('Fusion (TL 12), Power 30').section == 'Power'
    assert spec.row('4 weeks of operation').section == 'Fuel'
    assert spec.row('Fuel Scoops').section == 'Fuel'
    assert spec.row('Standard Bridge').section == 'Command'
    assert spec.row('Computer/5').section == 'Computer'
    assert spec.row('Cabin Space').section == 'Habitation'
    assert spec.row('Fuel/Cargo Container (20 tons)').section == 'Cargo'
