"""Reference ship case: Strandbell System Defense Boat.

Source: refs/tycho/sdb.md (Tycho design tool output for a 200-ton TL-15 SDB).

Purpose:
- exercise a 200-ton military standard reinforced hull with Crystaliron armour
- confirm M-Drive 9, Fusion TL12 power plant, and sensor suite behaviour
- validate turret costs and power, missile storage, and crew composition
- serve as a multi-component integration reference for military ships

Source handling:
- supported: hull, armour, m-drive, fusion plant, operation fuel, fuel
  processor, fuel scoops, bridge, computer/35, software packages, improved
  sensors, countermeasures suite, triple turrets (beam + missile), missile
  storage, repair drones, medical bay, staterooms, common area, airlocks,
  cargo, and production cost
- not modelled: armored bulkheads listed separately in the ref for M-Drive
  (1.60t, MCr0.32), bridge (1.0t, MCr0.2), and sensors (0.5t, MCr0.1); stores
  and spares (2.0t)

Known deviations from the Tycho stat block:
- m_drive_tons: ref shows 19.80t for "M-Drive 9, Armored" (includes armored
  bulkhead tonnage); Ceres models un-armored MDrive9 at 18.0t — the armored
  bulkhead is a separate component not in the build function (RI: "we no
  longer model a pseudo-armored M-drive")
- m_drive_cost: ref shows MCr36.36 (includes armored bulkhead cost of
  MCr0.32 and MCr0.04 rounding); Ceres gives MCr36.0 for the bare drive
- op_fuel_tons: ref shows 4.80t for 12 weeks; Ceres gives 5.0t per RIS-007
  (standard rounding)
- cargo_tons: ref shows 13.8t; Ceres gives 20.5t — the difference comes from
  not modelling the armored M-drive bulkheads and stores/spares
- production_cost: ref total is MCr147.13; Ceres gives MCr140.9 — reflects
  the above omissions (armored bulkheads and stores)
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer35, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive9, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import CountermeasuresSuite, ImprovedSensors, SensorsSection
from ceres.make.ship.software import (
    AutoRepair,
    Evade,
    FireControl,
)
from ceres.make.ship.storage import CargoSection, FuelProcessor, FuelScoops, FuelSection, OperationFuel
from ceres.make.ship.systems import Airlock, CommonArea, MedicalBay, RepairDrones, SystemsSection
from ceres.make.ship.weapons import BeamLaser, MissileRack, MissileStorage, TripleTurret, WeaponsSection

_expected = SimpleNamespace(
    # Hull
    hull_points=88,
    hull_cost_mcr=15.0,
    # Armour: Crystaliron 13 — agrees with ref
    armour_protection=13,
    armour_tons=32.5,
    armour_cost_mcr=6.5,
    # M-Drive: ref shows "M-Drive 9, Armored" at 19.80t, MCr36.36 (includes
    # armored bulkhead of 1.60t, MCr0.32 + MCr0.04 rounding). Ceres models
    # the un-armored MDrive9 at 18.0t, MCr36.0.
    m_drive_tons_ref=19.80,
    m_drive_cost_mcr_ref=36.36,
    m_drive_tons=18.0,
    m_drive_cost_mcr=36.0,
    m_drive_power=180,
    # Fusion plant TL12, output 240 — agrees with ref
    plant_output=240,
    plant_tons=16.0,
    plant_cost_mcr=16.0,
    # Fuel: ref shows 4.80t for 12 weeks; Ceres gives 5.0t per RIS-007
    op_fuel_weeks=12,
    op_fuel_tons_ref=4.80,
    op_fuel_tons=5.0,
    fuel_processor_tons=1.0,
    fuel_processor_cost_mcr=0.05,
    fuel_scoops_cost_mcr=1.0,
    # Sensors — Ceres agrees with ref tonnage and cost
    sensors_tons=3.0,
    sensors_cost_mcr=4.3,
    sensors_power=3.0,
    countermeasures_tons=2.0,
    countermeasures_cost_mcr=4.0,
    countermeasures_power=1.0,
    # Turrets — agrees with ref
    beam_turret_cost_mcr=2.5,
    beam_turret_power=13.0,  # 1 mount + 3 × 4 beam lasers
    missile_turret_cost_mcr=3.25,
    missile_turret_power=1.0,  # 1 mount only; missiles draw no power
    # Missile storage — agrees with ref
    missile_count=240,
    missile_storage_tons=20.0,
    missile_storage_cost=0,
    # Systems
    repair_drones_tons=2.0,
    repair_drones_cost_mcr=0.4,
    airlock_tons=0.0,  # 2 free airlocks for a 200-ton hull
    stateroom_count=15,
    staterooms_total_tons=60.0,
    common_area_tons=4.0,
    medical_bay_tons=4.0,
    # Power — Ceres agrees with ref available and basic/maneuver loads
    available_power=240,
    basic_hull_power=40.0,
    maneuver_power=180.0,
    total_power=240.0,
    # Cargo: ref 13.8t; Ceres 20.5t (armored M-drive bulkheads and stores
    # not modelled)
    cargo_tons_ref=13.8,
    cargo_tons=20.5,
    # Production cost: ref MCr147.13; Ceres MCr140.9 (omitted bulkheads +
    # stores)
    production_cost_mcr_ref=147.13,
    production_cost_mcr=140.9,
)

STRANDBELL_HULL = hull.standard_hull.model_copy(
    update={'reinforced': True, 'description': 'Standard Reinforced Hull'},
)


def build_strandbell() -> ship.Ship:
    return ship.Ship(
        ship_class='Strandbell',
        ship_type='System Defense Boat',
        military=True,
        tl=15,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=STRANDBELL_HULL,
            armour=armour.CrystalironArmour(protection=13),
            airlocks=[Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive9()),
        power=PowerSection(plant=FusionPlantTL12(output=240)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=1),
            fuel_scoops=FuelScoops(),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(
            hardware=Computer35(), software=[AutoRepair(rating=1), FireControl(rating=2), Evade(rating=2)]
        ),
        sensors=SensorsSection(primary=ImprovedSensors(), countermeasures=CountermeasuresSuite()),
        weapons=WeaponsSection(
            turrets=[
                TripleTurret(
                    weapons=[
                        BeamLaser(),
                        BeamLaser(),
                        BeamLaser(),
                    ],
                ),
                TripleTurret(
                    weapons=[
                        MissileRack(),
                        MissileRack(),
                        MissileRack(),
                    ],
                ),
            ],
            missile_storage=MissileStorage(count=240),
        ),
        systems=SystemsSection(internal_systems=[MedicalBay()], drones=[RepairDrones()]),
        habitation=HabitationSection(staterooms=[Stateroom()] * 15, common_area=CommonArea(tons=4.0)),
    )


def test_strandbell_hull():
    sdb = build_strandbell()
    assert sdb.hull_points == _expected.hull_points
    assert sdb.hull_cost == _expected.hull_cost_mcr * 1_000_000


def test_strandbell_armour():
    sdb = build_strandbell()
    a = sdb.hull.armour
    assert a is not None
    assert a.protection == _expected.armour_protection
    assert a.tons == pytest.approx(_expected.armour_tons)
    assert a.cost == pytest.approx(_expected.armour_cost_mcr * 1_000_000)


def test_strandbell_armored_m_drive():
    sdb = build_strandbell()
    assert sdb.drives is not None
    assert sdb.drives.m_drive is not None
    assert sdb.drives.m_drive.tons == pytest.approx(_expected.m_drive_tons)
    assert sdb.drives.m_drive.cost == pytest.approx(_expected.m_drive_cost_mcr * 1_000_000)
    assert sdb.drives.m_drive.power == pytest.approx(_expected.m_drive_power)


def test_strandbell_fusion_plant():
    sdb = build_strandbell()
    assert sdb.power is not None
    fp = sdb.power.plant
    assert fp is not None
    assert fp.output == _expected.plant_output
    assert fp.tons == pytest.approx(_expected.plant_tons)
    assert fp.cost == pytest.approx(_expected.plant_cost_mcr * 1_000_000)


def test_strandbell_fuel():
    sdb = build_strandbell()
    assert sdb.fuel is not None
    assert sdb.fuel.operation_fuel is not None
    assert sdb.fuel.operation_fuel.tons == pytest.approx(_expected.op_fuel_tons)
    assert sdb.fuel.fuel_processor is not None
    assert sdb.fuel.fuel_processor.tons == pytest.approx(_expected.fuel_processor_tons)
    assert sdb.fuel.fuel_processor.cost == pytest.approx(_expected.fuel_processor_cost_mcr * 1_000_000)
    assert sdb.fuel.fuel_scoops is not None
    assert sdb.fuel.fuel_scoops.cost == pytest.approx(_expected.fuel_scoops_cost_mcr * 1_000_000)


def test_strandbell_sensors():
    sdb = build_strandbell()
    assert sdb.sensors.primary.tons == pytest.approx(_expected.sensors_tons)
    assert sdb.sensors.primary.cost == pytest.approx(_expected.sensors_cost_mcr * 1_000_000)
    assert sdb.sensors.primary.power == pytest.approx(_expected.sensors_power)
    assert sdb.sensors.countermeasures is not None
    assert sdb.sensors.countermeasures.tons == pytest.approx(_expected.countermeasures_tons)
    assert sdb.sensors.countermeasures.cost == pytest.approx(_expected.countermeasures_cost_mcr * 1_000_000)
    assert sdb.sensors.countermeasures.power == pytest.approx(_expected.countermeasures_power)


def test_strandbell_turrets():
    sdb = build_strandbell()
    assert sdb.weapons is not None
    assert len(sdb.weapons.turrets) == 2
    beam_turret = sdb.weapons.turrets[0]
    missile_turret = sdb.weapons.turrets[1]
    assert beam_turret.cost == pytest.approx(_expected.beam_turret_cost_mcr * 1_000_000)
    assert beam_turret.power == pytest.approx(_expected.beam_turret_power)  # 1 mount + 3 × 4 beam
    assert missile_turret.cost == pytest.approx(_expected.missile_turret_cost_mcr * 1_000_000)
    assert missile_turret.power == pytest.approx(_expected.missile_turret_power)  # 1 mount + 3 × 0 missiles


def test_strandbell_missile_storage():
    sdb = build_strandbell()
    assert sdb.weapons is not None
    assert sdb.weapons.missile_storage is not None
    assert sdb.weapons.missile_storage.count == _expected.missile_count
    assert sdb.weapons.missile_storage.tons == pytest.approx(_expected.missile_storage_tons)
    assert sdb.weapons.missile_storage.cost == _expected.missile_storage_cost


def test_strandbell_systems():
    sdb = build_strandbell()
    assert sdb.systems is not None
    assert len(sdb.systems.drones) == 1
    assert sdb.systems.drones[0].tons == pytest.approx(_expected.repair_drones_tons)
    assert sdb.systems.drones[0].cost == pytest.approx(_expected.repair_drones_cost_mcr * 1_000_000)
    assert len(sdb.hull.airlocks) == 2
    assert sdb.hull.airlocks[0].tons == _expected.airlock_tons  # 2 free for 200t
    assert sdb.hull.airlocks[1].tons == _expected.airlock_tons
    assert sdb.systems.medical_bays[0] is not None
    assert sdb.habitation is not None
    assert sdb.habitation.staterooms is not None
    assert len(sdb.habitation.staterooms) == _expected.stateroom_count
    assert sum(room.tons for room in sdb.habitation.staterooms) == pytest.approx(_expected.staterooms_total_tons)
    assert sdb.habitation.common_area is not None
    assert sdb.habitation.common_area.tons == pytest.approx(_expected.common_area_tons)


def test_strandbell_power():
    sdb = build_strandbell()
    assert sdb.available_power == _expected.available_power
    assert sdb.basic_hull_power_load == pytest.approx(_expected.basic_hull_power)
    assert sdb.maneuver_power_load == pytest.approx(_expected.maneuver_power)
    # sensors(3) + countermeasures(1) + beam turret(13) + missile turret(1) + medical(1) + fuel processor(1) = 20
    assert sdb.total_power_load == pytest.approx(_expected.total_power)


def test_strandbell_cargo():
    # Ref: 13.8t cargo + 2.0t stores + 3.1t armored bulkheads = 18.9t.
    # We still do not model stores for Strandbell, and we no longer model a
    # pseudo-armored M-drive, so cargo lands higher.
    sdb = build_strandbell()
    assert CargoSection.cargo_tons_for_ship(sdb) == pytest.approx(_expected.cargo_tons, abs=0.01)


def test_strandbell_cost():
    # Ref design cost 147.13MCr includes armored bulkheads (0.62MCr) and
    # stores/spares we don't model.
    sdb = build_strandbell()
    assert sdb.production_cost == pytest.approx(_expected.production_cost_mcr * 1_000_000)


def test_strandbell_software():
    sdb = build_strandbell()
    assert sdb.computer is not None
    packages = [(p.description, p.cost) for p in sdb.computer.software_packages]
    assert ('Library', 0.0) in packages
    assert ('Manoeuvre/0', 0.0) in packages
    assert ('Intellect', 0.0) in packages
    assert ('Auto-Repair/1', 5_000_000) in packages
    assert ('Fire Control/2', 4_000_000) in packages
    assert ('Evade/2', 2_000_000) in packages


def test_strandbell_spec_structure():
    sdb = build_strandbell()
    spec = sdb.build_spec()

    assert spec.ship_class == 'Strandbell'
    assert spec.ship_type == 'System Defense Boat'
    assert spec.tl == 15
    assert spec.hull_points == 88

    assert spec.row('Standard Reinforced Hull').section == 'Hull'
    assert spec.row('Crystaliron, Armour: 13').section == 'Hull'
    assert spec.row('M-Drive 9').section == 'Propulsion'
    assert spec.row('Fusion (TL 12), Power 240').section == 'Power'
    assert spec.row('Fuel Scoops').section == 'Fuel'
    assert spec.row('Standard Bridge').section == 'Command'
    assert spec.row('Computer/35').section == 'Computer'
    assert spec.row('Auto-Repair/1').section == 'Computer'
    assert spec.row('Fire Control/2').section == 'Computer'
    assert spec.row('Evade/2').section == 'Computer'
    assert spec.row('Improved Sensors').section == 'Sensors'
    assert spec.row('Countermeasures Suite').section == 'Sensors'
    assert spec.row('Triple Turret', section='Weapons').section == 'Weapons'
    assert spec.row('Missile Storage (240)').section == 'Weapons'
    assert spec.row('Medical Bay').section == 'Systems'
    assert spec.row('Repair Drones').section == 'Systems'
    stateroom_row = spec.row('Staterooms', section='Habitation')
    assert stateroom_row.section == 'Habitation'
    assert stateroom_row.quantity == 15
    assert spec.row('Common Area').section == 'Habitation'
    airlock_row = spec.row('Airlock (2 tons)', section='Hull')
    assert airlock_row.section == 'Hull'
    assert airlock_row.quantity == 2


def test_strandbell_uses_military_crew_rules():
    sdb = build_strandbell()
    assert [(role.role, quantity, role.monthly_salary) for role, quantity in sdb.crew.grouped_roles] == [
        ('CAPTAIN', 1, 10_000),
        ('PILOT', 3, 6_000),
        ('ENGINEER', 1, 4_000),
        ('GUNNER', 4, 2_000),
        ('SENSOR OPERATOR', 3, 4_000),
        ('MEDIC', 1, 4_000),
        ('OFFICER', 1, 5_000),
    ]
