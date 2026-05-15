"""Reference ship case based on refs/tycho/PinnaceWith20TonFuelCapacity.txt.

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

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crew import Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive5, PowerSection
from ceres.make.ship.habitation import CabinSpace, HabitationSection
from ceres.make.ship.sensors import BasicSensors, SensorsSection
from ceres.make.ship.storage import CargoSection, FuelCargoContainer, FuelSection, OperationFuel
from ceres.make.ship.systems import Airlock, SystemsSection

_expected = SimpleNamespace(
    tl=12,
    displacement=40,
    hull_cost_mcr=2.4,  # 40 tons Streamlined: 2,400,000
    hull_points=16,
    m_drive_tons=2.0,  # Thrust 5 on 40t hull
    m_drive_cost_mcr=4.0,
    m_drive_power=20,
    plant_tons=2.0,  # Fusion (TL 12), Power 30
    plant_cost_mcr=2.0,
    available_power=30.0,
    op_fuel_tons=1.0,  # ref: 1 ton; Ceres gives 0.2 per RI-007 (small-craft rounding)
    bridge_tons=3.0,
    bridge_cost_mcr=0.5,
    computer_cost_mcr=0.03,  # Computer/5: 0.03
    sensor_tons=0.0,  # Basic sensors: 0 tons
    sensor_cost_cr=0.0,
    sensor_power=0.0,
    airlock_tons=2.0,  # explicitly purchased airlock
    airlock_cost_cr=200_000,
    cabin_tons=9.0,  # Cabin Space x6
    cabin_cost_cr=450_000,
    cabin_passenger_capacity=6,
    fuel_cargo_container_tons=21.0,  # 20t capacity + 1t structure
    fuel_cargo_container_cost_cr=100_000,
    cargo_tons=20.8,  # remaining usable tonnage
    power_basic=8.0,  # ceil(40 * 0.2) = 8 per RI-013
    power_maneuver=20.0,
    total_power=28.0,  # basic(8) + maneuver(20)
    production_cost_mcr=9.68,  # Total Cost: MCr9.68
    sales_price_mcr=8.712,  # Purchase Cost: MCr8.712
    maintenance_cr=726,  # Maintenance Cost: Cr726/month
)

# Ceres gives op_fuel_tons=0.2 per RI-007 (small craft: round up to 0.1 dTon)
_expected.op_fuel_tons = 0.2


def build_pinnace_with_20_ton_fuel_capacity() -> ship.Ship:
    return ship.Ship(
        ship_class='Pinnace',
        ship_type='with 20 ton fuel capacity',
        tl=12,
        displacement=40,
        design_type=ship.ShipDesignType.STANDARD,
        occupants=[],
        crew=ShipCrew(roles=[Pilot()]),
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
        drives=DriveSection(m_drive=MDrive5()),
        power=PowerSection(plant=FusionPlantTL12(output=30)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=4)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        sensors=SensorsSection(primary=BasicSensors()),
        systems=SystemsSection(),
        habitation=HabitationSection(cabin_space=CabinSpace(tons=9)),
        cargo=CargoSection(fuel_cargo_containers=[FuelCargoContainer(capacity=20)]),
    )


def test_pinnace_with_20_ton_fuel_capacity_matches_reference_sheet():
    pinnace = build_pinnace_with_20_ton_fuel_capacity()

    assert pinnace.tl == _expected.tl
    assert pinnace.displacement == _expected.displacement
    assert pinnace.hull_cost == pytest.approx(_expected.hull_cost_mcr * 1_000_000)
    assert pinnace.hull_points == pytest.approx(_expected.hull_points)

    assert pinnace.drives is not None
    assert pinnace.drives.m_drive is not None
    assert pinnace.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert pinnace.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert pinnace.drives.m_drive.power == pytest.approx(_expected.m_drive_power)

    assert pinnace.power is not None
    assert pinnace.power.plant is not None
    assert pinnace.power.plant.tons == pytest.approx(_expected.plant_tons)
    assert pinnace.power.plant.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)
    assert pinnace.available_power == pytest.approx(_expected.available_power)

    assert pinnace.fuel is not None
    assert pinnace.fuel.operation_fuel is not None
    assert pinnace.fuel.operation_fuel.tons == pytest.approx(_expected.op_fuel_tons)
    assert pinnace.fuel.fuel_scoops is not None
    assert pinnace.fuel.fuel_scoops.cost == pytest.approx(0.0)

    assert pinnace.command is not None
    assert pinnace.command.bridge is not None
    assert pinnace.command.bridge.tons == pytest.approx(_expected.bridge_tons)
    assert pinnace.command.bridge.cost == pytest.approx(_expected.bridge_cost_mcr * 1_000_000)

    assert pinnace.computer is not None
    assert pinnace.computer.hardware is not None
    assert pinnace.computer.hardware.cost == pytest.approx(_expected.computer_cost_mcr * 1_000_000)
    assert [(package.description, package.cost) for package in pinnace.computer.software_packages] == [
        ('Library', 0.0),
        ('Manoeuvre/0', 0.0),
        ('Intellect', 0.0),
    ]

    assert pinnace.sensors.primary.tons == pytest.approx(_expected.sensor_tons)
    assert pinnace.sensors.primary.cost == pytest.approx(_expected.sensor_cost_cr)
    assert pinnace.sensors.primary.power == pytest.approx(_expected.sensor_power)

    assert len(pinnace.hull.airlocks or []) == 1
    assert pinnace.hull.airlocks[0].tons == pytest.approx(_expected.airlock_tons)
    assert pinnace.hull.airlocks[0].cost == pytest.approx(_expected.airlock_cost_cr)

    assert pinnace.habitation is not None
    assert pinnace.habitation.cabin_space is not None
    assert pinnace.habitation.cabin_space.tons == pytest.approx(_expected.cabin_tons)
    assert pinnace.habitation.cabin_space.cost == pytest.approx(_expected.cabin_cost_cr)
    assert pinnace.habitation.cabin_space.passenger_capacity == _expected.cabin_passenger_capacity

    assert pinnace.cargo is not None
    assert len(pinnace.cargo.fuel_cargo_containers) == 1
    assert pinnace.cargo.fuel_cargo_containers[0].tons == pytest.approx(_expected.fuel_cargo_container_tons)
    assert pinnace.cargo.fuel_cargo_containers[0].cost == pytest.approx(_expected.fuel_cargo_container_cost_cr)
    assert CargoSection.cargo_tons_for_ship(pinnace) == pytest.approx(_expected.cargo_tons)

    assert pinnace.basic_hull_power_load == pytest.approx(_expected.power_basic)
    assert pinnace.maneuver_power_load == pytest.approx(_expected.power_maneuver)
    assert pinnace.total_power_load == pytest.approx(_expected.total_power)

    assert pinnace.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)
    assert pinnace.sales_price_new == pytest.approx(_expected.sales_price_mcr * 1_000_000)
    assert pinnace.expenses.maintenance == pytest.approx(_expected.maintenance_cr)

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
